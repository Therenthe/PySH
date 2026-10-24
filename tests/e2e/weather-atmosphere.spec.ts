import {test,expect} from '@playwright/test';

const cases=[
 {name:'clear unchanged',code:0,visibility:20000,cover:0,haze:'0.000',clouds:'none',stars:true},
 {name:'fog code eight kilometres sparse',code:45,visibility:8000,cover:10,haze:'0.000',clouds:'sparse',stars:true},
 {name:'fog code eight kilometres broken',code:45,visibility:8000,cover:60,haze:'0.000',clouds:'broken',stars:true},
 {name:'fog code eight kilometres overcast',code:45,visibility:8000,cover:100,haze:'0.000',clouds:'overcast',stars:false},
 {name:'very dense fog',code:45,visibility:100,cover:10,haze:'0.800',clouds:'sparse',stars:false},
 {name:'fog eight hundred metres',code:45,visibility:800,cover:10,haze:'0.302',clouds:'sparse',stars:true},
 {name:'missing measurements',code:45,visibility:undefined,cover:undefined,haze:'0.120',clouds:'unknown',stars:false},
 {name:'null measurements',code:45,visibility:null,cover:null,haze:'0.120',clouds:'unknown',stars:false},
 {name:'invalid measurements',code:45,visibility:'8000',cover:101,haze:'0.120',clouds:'unknown',stars:false},
 {name:'stale measurements',code:45,visibility:100,cover:100,haze:'0.000',clouds:'unknown',stars:false,stale:true},
 {name:'rain overrides conflicting cloud cover',code:63,visibility:8000,cover:0,haze:'0.000',clouds:'overcast',stars:false},
 {name:'snow overrides conflicting cloud cover',code:75,visibility:8000,cover:0,haze:'0.000',clouds:'overcast',stars:false},
] as const;

for(const theme of ['ink','night'])for(const scene of cases)test(`atmosphere ${theme}: ${scene.name}`,async({page},info)=>{
 const language=info.project.name.endsWith('ro')?'ro':'en',night=theme==='night',now=new Date(night?'2026-10-04T23:00:00Z':'2026-10-23T10:00:00Z');
 const state={preferences:{language,theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,timezone:'Europe/Bucharest',homeCards:['weather','forecast'],navigationCollapsed:true,location:{name:'București · Sector 5',latitude:44.4,longitude:26.1},favorites:[],shortcuts:[]},player:{state:'idle'},audio:{available:true,ready:true,outputs:[]},bluetooth:{available:true,powered:false,devices:[],prompts:[]},network:{available:true,state:'connected',devices:[],saved:[]},weather:{current:{weather_code:scene.code,is_day:night?0:1,temperature_c:13,visibility_m:scene.visibility,cloud_cover_pct:scene.cover},daily:[],updated_at:now.toISOString(),stale:'stale' in scene&&scene.stale}};
 await page.route('**/api/**',route=>route.fulfill({json:new URL(route.request().url()).pathname==='/api/state'?state:{token:'atmosphere-fixture'}}));
 await page.clock.install({time:now});await page.goto('/');
 const sky=page.locator('.ambient-sky');await expect(sky).toHaveAttribute('data-haze',scene.haze);await expect(sky).toHaveAttribute('data-sky-cover',scene.clouds);
 await expect(page.locator('[data-blender-star]')).toHaveCount(night&&scene.stars?170:0);
 await expect(page.locator(night?'.blender-sun':'.blender-moon')).toHaveCount(0);
 await expect(page.locator('.celestial-anchor')).toHaveCount(scene.stars?1:0);
 if(['none','unknown'].includes(scene.clouds))await expect(page.locator('.blender-clouds')).toHaveCount(0);
 else await expect(page.locator('.blender-clouds')).toHaveAttribute('data-cloud-cover',scene.clouds);
 if(scene.code===45){await expect(page.locator('.ambient-condition')).toHaveText(language==='ro'?'Ceață':'Fog');}
 if('stale' in scene)await expect(sky).toHaveClass(/sky-neutral/);
 if(scene.code===63||scene.code===75)await expect(page.locator('.scene-precipitation')).toHaveAttribute('data-precipitation',scene.code===63?'rain':'snow');
 await page.locator('.weather-heading').click();await expect(page.locator('.ambient-weather')).toHaveClass(/card-compact/);
 await page.locator('.weather-heading').click();await expect(page.locator('.ambient-weather')).not.toHaveClass(/card-compact/);
 await page.clock.runFor(16000);await page.locator('.weather-heading').click();
 const after=await page.locator('.ambient-weather').boundingBox();expect(after!.x).toBeGreaterThanOrEqual(0);expect(after!.x+after!.width).toBeLessThanOrEqual(800);expect(after!.y).toBeGreaterThanOrEqual(0);expect(after!.y+after!.height).toBeLessThanOrEqual(480);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=800&&document.documentElement.scrollHeight<=480)).toBeTruthy();
});

test('atmosphere polling updates measurements without moving cards or changing the reported condition',async({page})=>{
 const now=new Date('2026-10-04T23:00:00Z'),current={weather_code:45,is_day:0,temperature_c:13,visibility_m:100,cloud_cover_pct:100};
 const state={preferences:{language:'ro',theme:'night',setupComplete:true,nightEnabled:false,screensaverMinutes:0,homeCards:['weather'],timezone:'Europe/Bucharest',location:{name:'București · Sector 5',latitude:44.4,longitude:26.1}},weather:{current,updated_at:now.toISOString(),stale:false},network:{},bluetooth:{devices:[],prompts:[]},audio:{},player:{}};
 await page.route('**/api/**',route=>route.fulfill({json:new URL(route.request().url()).pathname==='/api/state'?state:{token:'polling-atmosphere'}}));await page.clock.install({time:now});await page.goto('/');
 await expect(page.locator('.ambient-sky')).toHaveAttribute('data-haze','0.800');await expect(page.locator('.ambient-home')).toHaveCSS('transform',/^(none|matrix\(1, 0, 0, 1, 0, 0\))$/);const initial=await page.locator('.ambient-weather').boundingBox();
 current.visibility_m=8000;current.cloud_cover_pct=10;await page.clock.runFor(3000);
 await expect(page.locator('.ambient-sky')).toHaveAttribute('data-haze','0.000');await expect(page.locator('[data-blender-star]')).toHaveCount(170);await expect(page.locator('.ambient-condition')).toHaveText('Ceață');
 await expect.poll(()=>page.locator('.ambient-weather').boundingBox()).toEqual(initial);
 await page.emulateMedia({reducedMotion:'reduce'});expect(await page.locator('.cloud-mass').first().evaluate(el=>getComputedStyle(el).animationName)).toBe('none');
});

test('atmosphere rejects unmeasured values and grades haze continuously without relabelling weather',async({page})=>{
 await page.route('**/atmosphere-model.html',route=>route.fulfill({contentType:'text/html',body:'<main>Atmosphere model test</main>'}));await page.goto('/atmosphere-model.html');
 const result=await page.evaluate(async()=>{
  const {sceneAtmosphere}=await import('/src/sceneAtmosphere.ts' as string);
  return {invalid:[undefined,null,-1,NaN,Infinity,'8000',true,{}].map(value=>sceneAtmosphere(45,false,value,value)),boundaries:[0,100,800,1000,4000,8000,20000].map(value=>sceneAtmosphere(45,false,value,10)),legacy:sceneAtmosphere(0,false,undefined,undefined),missing:sceneAtmosphere(null,false,0,0)};
 });
 expect(result.invalid.every(item=>item.haze===.12&&item.cloudCover==='unknown'&&!item.openSky)).toBeTruthy();
 expect(result.boundaries.map(item=>Number(item.haze.toFixed(3)))).toEqual([1,.8,.302,.16,.091,0,0]);
 expect(result.legacy).toMatchObject({haze:0,cloudCover:'none',openSky:true,transmission:1});
 expect(result.missing).toMatchObject({haze:0,cloudCover:'unknown',openSky:false,transmission:0});
});

for(const night of [false,true])for(const snow of [false,true])test(`precipitation native-size contrast ${night?'night':'day'} ${snow?'snow':'rain'}`,async({page},info)=>{
 const now=new Date(night?'2026-10-04T23:00:00Z':'2026-10-23T10:00:00Z'),state={preferences:{language:info.project.name.endsWith('ro')?'ro':'en',theme:night?'night':'ink',setupComplete:true,nightEnabled:false,screensaverMinutes:0,timezone:'Europe/Bucharest',homeCards:[],navigationCollapsed:true,location:{latitude:44.4,longitude:26.1},decorativeAircraft:false},weather:{current:{weather_code:snow?73:63,is_day:night?0:1,temperature_c:snow?-2:13,wind_kmh:8,visibility_m:8000,cloud_cover_pct:95},updated_at:now.toISOString(),stale:false},network:{},bluetooth:{devices:[],prompts:[]},audio:{},player:{}};
 await page.route('**/api/**',route=>route.fulfill({json:new URL(route.request().url()).pathname==='/api/state'?state:{token:'precipitation-contrast'}}));await page.clock.install({time:now});await page.goto('/');await expect(page.locator('.weather-particle')).toHaveCount(38);
 await page.locator('.ambient-sky img').evaluateAll(images=>Promise.all(images.map(image=>(image as HTMLImageElement).decode())));
 await page.evaluate(async snow=>{const image=new Image();image.src=`/ambient/${snow?'snowflake':'raindrop'}-v1.png`;await image.decode();},snow);
 await page.addStyleTag({content:'*{animation-play-state:paused!important;transition:none!important}'});
 const filter=await page.locator('.weather-particle').first().evaluate(el=>getComputedStyle(el).filter);
 expect(night?filter==='none':filter!=='none').toBeTruthy();
 const current=await page.screenshot({path:info.outputPath(`${night?'night':'day'}-${snow?'snow':'rain'}-contrast.png`)});
 const prior=await page.addStyleTag({content:'.weather-particle{filter:none!important}'});const unfiltered=await page.screenshot();await prior.evaluate(el=>el.remove());
 const hidden=await page.addStyleTag({content:'.scene-precipitation{visibility:hidden!important}'});const empty=await page.screenshot();await hidden.evaluate(el=>el.remove());
 const measured=await page.evaluate(async encoded=>{
  const pixels=async(value:string)=>{const image=new Image();image.src=`data:image/png;base64,${value}`;await image.decode();const canvas=document.createElement('canvas');canvas.width=800;canvas.height=480;const context=canvas.getContext('2d')!;context.drawImage(image,0,0);return context.getImageData(0,0,800,480).data;};
  const [current,prior,empty]=await Promise.all([pixels(encoded.current),pixels(encoded.prior),pixels(encoded.empty)]);let contrast=0,previous=0,changed=0;
  for(let y=80;y<280;y++)for(let x=0;x<800;x++){const index=(y*800+x)*4;for(let channel=0;channel<3;channel++){const actual=Math.abs(current[index+channel]-empty[index+channel]),before=Math.abs(prior[index+channel]-empty[index+channel]);contrast+=actual;previous+=before;if(actual>3)changed++;}}
  return {contrast,previous,changed};
 },{current:current.toString('base64'),prior:unfiltered.toString('base64'),empty:empty.toString('base64')});
 await info.attach('precipitation-contrast.json',{body:JSON.stringify({night,snow,...measured}),contentType:'application/json'});
 expect(measured.changed).toBeGreaterThan(15);if(night)expect(measured.contrast).toBe(measured.previous);else expect(measured.contrast).toBeGreaterThan(measured.previous*1.15);
});
