import {test,expect,type Page} from '@playwright/test';

async function stage(page:Page,{time,condition='partly-cloudy',night=true,aircraft='airliner'}:{time:string;condition?:string;night?:boolean;aircraft?:string}){
 await page.route('**/api/**',route=>route.fulfill({json:new URL(route.request().url()).pathname==='/api/state'?{preferences:{language:'en',setupComplete:true,screensaverMinutes:0},network:{},bluetooth:{devices:[],prompts:[]},audio:{},player:{},weather:{}}:{token:'isolated-sky-fixture'}}));
 await page.goto('/');await expect(page.locator('.ambient-home')).toBeVisible();
 await page.evaluate(async config=>{
  const main=await(await fetch('/src/main.tsx')).text(),source=await(await fetch('/src/AmbientCelestial3D.tsx')).text();
  const reactURL=source.match(/from\s+["']([^"']*\/react\.js[^"']*)["']/)![1],domURL=main.match(/from\s+["']([^"']*react-dom_client\.js[^"']*)["']/)![1];
  const reactModule=await import(reactURL),domModule=await import(domURL),sky=await import('/src/AmbientCelestial3D.tsx' as string),city=await import('/src/CityDiorama.tsx' as string),weather=await import('/src/sceneWeather.ts' as string),ephemeris=await import('/src/CelestialMotion.ts' as string);
  const React=reactModule.default||reactModule,createRoot=domModule.createRoot||domModule.default.createRoot,now=new Date(config.time),celestial=ephemeris.getCelestialScene(now,44.4,26.1);
  document.body.innerHTML='<div id="blender-sky-stage" style="position:fixed;inset:0;overflow:hidden"></div>';
  const root=createRoot(document.getElementById('blender-sky-stage'));
  const skyChildren:any[]=[];
  if(config.night)skyChildren.push(React.createElement(sky.BlenderStars,{key:'stars'}));
  const body=config.night?celestial?.moon:celestial?.sun;
  if(body?.visible)skyChildren.push(React.createElement('div',{key:'body',className:'celestial-anchor','data-celestial-body':config.night?'moon':'sun',style:{left:`${body.x}%`,top:`${body.y}%`}},config.night?React.createElement(sky.BlenderMoon,{now}):React.createElement(sky.BlenderSun)));
  skyChildren.push(React.createElement(sky.BlenderClouds,{key:'clouds',night:config.night,condition:config.condition}));
  skyChildren.push(React.createElement(city.CityDiorama,{key:'city',night:config.night,weather:weather.sceneWeather(config.condition==='clear'?0:2,false,13,8,now,44.4),radioPlaying:true,bluetoothPowered:true,bluetoothConnected:true}));
  skyChildren.push(React.createElement('div',{key:'aircraft',style:{position:'absolute',left:'38%',top:'28%',zIndex:3}},React.createElement(sky.BlenderAircraft,{night:config.night,variant:config.aircraft,heading:0,scale:1})));
  root.render(React.createElement('div',{className:'app','data-theme':config.night?'night':'ink',style:{position:'absolute',inset:0,width:800,height:480}},React.createElement('div',{className:`ambient-sky ${config.night?'sky-night':'sky-day'} sky-${config.condition}`,style:{inset:0}},...skyChildren),React.createElement('div',{style:{position:'absolute',left:0,right:0,top:10,textAlign:'center',color:config.night?'#f4f7fb':'#23312f',fontSize:25,fontWeight:600}},now.toLocaleTimeString('ro-RO',{timeZone:'Europe/Bucharest',hour:'2-digit',minute:'2-digit'}))));
  (window as any).skyModule=sky;
 },{time,condition,night,aircraft});
 await expect(page.locator('.city-diorama')).toBeVisible();
 await page.locator('.blender-clouds img').evaluateAll(elements=>Promise.all(elements.map(element=>(element as HTMLImageElement).decode())));
 await page.locator('.blender-aircraft img').evaluateAll(elements=>Promise.all(elements.map(element=>(element as HTMLImageElement).decode())));
 await page.evaluate(async()=>{const image=new Image();image.src='/ambient/sky3d/moon-phases-blender-v1.png';await image.decode();});
}

for(const scene of [
 {name:'night-half-moon',time:'2026-10-04T23:00:00Z',night:true,condition:'partly-cloudy',aircraft:'airliner'},
 {name:'night-clear',time:'2026-10-04T23:00:00Z',night:true,condition:'clear',aircraft:'tv-helicopter'},
 {name:'night-waxing-moon',time:'2026-10-20T17:00:00Z',night:true,condition:'clear',aircraft:'airliner'},
 {name:'day-spring',time:'2026-04-14T10:00:00Z',night:false,condition:'partly-cloudy',aircraft:'airliner'},
 {name:'day-summer',time:'2026-07-14T10:00:00Z',night:false,condition:'mainly-clear',aircraft:'turboprop'},
 {name:'day-autumn',time:'2026-10-14T10:00:00Z',night:false,condition:'overcast',aircraft:'airliner'},
 {name:'night-winter',time:'2026-01-04T23:00:00Z',night:true,condition:'overcast',aircraft:'airliner'},
])test(`Blender sky fixture ${scene.name} preserves sparse geometry and loads genuine rendered assets`,async({page},info)=>{
 await stage(page,scene);
 await expect(page.locator('[data-blender-star]')).toHaveCount(scene.night?170:0);
 await expect(page.locator('.ambient-star-texture')).toHaveCount(0);
 await expect(page.locator('.blender-clouds')).toHaveCount(scene.condition==='clear'?0:1);
 await expect(page.locator('[data-aircraft-model=blender3d]')).toHaveCount(1);
 if(scene.name==='night-waxing-moon'){
  await expect(page.locator('.blender-moon')).toBeVisible();
  await expect(page.locator('.blender-moon')).toHaveAttribute('data-lunar-direction','waxing');
 }
 await page.screenshot({path:info.outputPath(`sky3d-${scene.name}.png`)});
 await page.emulateMedia({reducedMotion:'reduce'});
 const motion=await page.locator('.cloud-mass,.blender-star-glint,.blender-aircraft-light').evaluateAll(nodes=>nodes.map(node=>getComputedStyle(node).animationName));expect(motion.every(value=>value==='none')).toBeTruthy();
});

test('Blender Moon atlas preserves waxing/waning orientation and continuous illumination metadata',async({page})=>{
 await stage(page,{time:'2026-10-04T23:00:00Z',night:true,condition:'clear'});
 const mapping=await page.evaluate(()=>{
  const frame=(window as any).skyModule.moonAtlasFrame;let worst=0;
  for(let index=0;index<=10000;index++){const illumination=index/10000;for(const waxing of [true,false]){const selected=frame(illumination,waxing);const rendered=(1-Math.cos(selected/128*Math.PI*2))/2;worst=Math.max(worst,Math.abs(illumination-rendered));}}
  return {newMoon:frame(0,true),waxingHalf:frame(.5,true),full:frame(1,true),waningHalf:frame(.5,false),worst};
 });
 expect(mapping).toMatchObject({newMoon:0,waxingHalf:32,full:64,waningHalf:96});expect(mapping.worst).toBeLessThan(.01228);
 await expect(page.locator('.blender-moon')).toHaveAttribute('data-moon-surface','blender-nasa-svs');
});

test('Blender Sun has limb depth and a smooth quiet alpha perimeter',async({page})=>{
 await stage(page,{time:'2026-07-14T10:00:00Z',night:false,condition:'clear'});
 const pixels=await page.evaluate(async()=>{
  const image=new Image();image.src='/ambient/sky3d/sun-blender-v1.png';await image.decode();
  const canvas=document.createElement('canvas');canvas.width=image.width;canvas.height=image.height;
  const context=canvas.getContext('2d')!;context.drawImage(image,0,0);const data=context.getImageData(0,0,image.width,image.height).data;
  const sample=(x:number,y:number)=>Array.from(data.slice((y*image.width+x)*4,(y*image.width+x)*4+4));
  // A192px raster is centred between pixels95 and96; compare opposite centres.
  const rings=Array.from({length:12},(_,index)=>[sample(171+index,96)[3],sample(20-index,96)[3],sample(96,171+index)[3],sample(96,20-index)[3]]);
  return {center:sample(96,96),limb:sample(164,96),corner:sample(0,0),rings};
 });
 expect(pixels.center[3]).toBe(255);expect(pixels.corner[3]).toBe(0);
 expect(pixels.center.slice(0,3).reduce((a,b)=>a+b,0)).toBeGreaterThan(pixels.limb.slice(0,3).reduce((a,b)=>a+b,0)+15);
 for(const ring of pixels.rings)expect(Math.max(...ring)-Math.min(...ring)).toBeLessThan(45);
 const outer=pixels.rings.at(-1)!;expect(Math.max(...outer)).toBeLessThan(12);
});

for(const scenario of [
 {name:'night-clear',time:'2026-10-04T23:00:00Z',code:0,theme:'night'},
 {name:'night-clouds',time:'2026-10-04T23:00:00Z',code:2,theme:'night'},
 {name:'day-clouds',time:'2026-04-14T10:00:00Z',code:2,theme:'ink'},
])test(`integrated Home sky ${scenario.name} keeps Blender imagery after all styles load`,async({page},info)=>{
 const now=new Date(scenario.time),night=scenario.theme==='night';
 const state={preferences:{language:info.project.name.endsWith('ro')?'ro':'en',theme:scenario.theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,timezone:'Europe/Bucharest',homeCards:[],navigationCollapsed:true,location:{name:'București · Sector 5',latitude:44.4,longitude:26.1},favorites:[],shortcuts:[]},player:{state:'idle'},audio:{available:true,ready:true,outputs:[]},bluetooth:{available:true,powered:false,devices:[],prompts:[]},network:{available:true,state:'connected',devices:[],saved:[]},weather:{current:{weather_code:scenario.code,is_day:night?0:1,temperature_c:13},daily:[],updated_at:now.toISOString(),stale:false}};
 await page.route('**/api/**',route=>route.fulfill({json:new URL(route.request().url()).pathname==='/api/state'?state:{token:'isolated-integrated-sky-fixture'}}));
 await page.clock.install({time:now});await page.goto('/');await expect(page.locator('.ambient-home')).toBeVisible();
 await page.clock.runFor(500);
 const body=page.locator(night?'.blender-moon':'.blender-sun');await expect(body).toBeVisible();
 await expect.poll(()=>body.evaluate(element=>getComputedStyle(element).backgroundImage)).toContain(night?'moon-phases-blender-v1.png':'sun-blender-v1.png');
 if(night){await expect(page.locator('.blender-sun')).toHaveCount(0);await expect(page.locator('[data-blender-star]')).toHaveCount(170);}else await expect(page.locator('.blender-moon')).toHaveCount(0);
 if(scenario.code===2){await expect(page.locator('.blender-clouds')).toBeVisible();await page.locator('.blender-clouds img').evaluateAll(elements=>Promise.all(elements.map(element=>(element as HTMLImageElement).decode())));}
 await page.evaluate(async()=>{for(const src of ['/ambient/sky3d/moon-phases-blender-v1.png','/ambient/sky3d/sun-blender-v1.png','/ambient/sky3d/star-glints-blender-v1.png']){const image=new Image();image.src=src;await image.decode();}});
 await page.screenshot({path:info.outputPath(`integrated-${scenario.name}.png`)});
});
