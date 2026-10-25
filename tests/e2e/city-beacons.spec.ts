import {test,expect,type Page} from '@playwright/test';

// Controlled loopback browser state. No hardware or real network is mutated.
async function fixture(page:Page,language:string,theme:string,day=false,code=45){
 const now=new Date(day?'2026-10-24T10:00:00Z':'2026-10-24T20:00:00Z');
 const state:any={preferences:{language,theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,visualizerStyle:'wave',timezone:'Europe/Bucharest',location:{name:'București · Sector5',latitude:44.4,longitude:26.1},homeCards:[],navigationCollapsed:true,navigationAutoHide:false,decorativeAircraft:false,decorativeLunarDust:false,favorites:[],shortcuts:[]},network:{available:true,state:'connected',active_type:'ethernet',devices:[]},bluetooth:{available:true,powered:true,devices:[{connected:true}],prompts:[]},audio:{available:true,ready:true,volume:20,mute:false,outputs:[]},player:{state:'playing',kind:'radio',url:'https://example.invalid/radio',station_name:'Radio Fixture',title:'Track'},weather:{stale:false,current:{weather_code:code,is_day:day?1:0,temperature_c:12,visibility_m:code===45?100:20000,cloud_cover_pct:code===0?0:100,wind_kmh:8},daily:[],updated_at:now.toISOString()}};
 const writes:any[]=[];
 await page.route('**/api/**',async route=>{const request=route.request(),path=new URL(request.url()).pathname;let json:any={ok:true};if(path==='/api/session')json={token:'city-beacon-isolated'};else if(path==='/api/state')json=state;else if(path==='/api/radio')json={stations:[]};else if(path==='/api/audio/visualization')json={available:true,status:'ready',waveform:Array(64).fill(.25),bars:Array(16).fill(.3),rms:.25,peak:.3,silent:false};else if(request.method()!=='GET')writes.push({path,body:request.postDataJSON()});await route.fulfill({json});});
 await page.clock.install({time:now});await page.goto('/');await expect(page.locator('.city-diorama')).toHaveAttribute('data-city-version','blender-v4');
 await page.locator('.city-diorama img').evaluateAll(nodes=>Promise.all(nodes.map(node=>(node as HTMLImageElement).decode())));
 return {state,writes};
}
async function motionSamples(page:Page,selector:string){
 return page.locator(selector).evaluate(node=>{const animation=node.getAnimations()[0];if(!animation)return [];const duration=Number(animation.effect!.getTiming().duration),delay=Number(animation.effect!.getTiming().delay);animation.pause();const samples=[0,.2,.4,.6,.8].map(fraction=>{animation.currentTime=delay+duration*fraction;const css=getComputedStyle(node);return{opacity:Number(css.opacity),transform:css.transform,duration};});animation.play();return samples;});
}

for(const theme of ['ink','night'])for(const scene of [{name:'day-fog',day:true,code:45},{name:'night-fog',day:false,code:45},{name:'night-clear',day:false,code:0},{name:'day-rain',day:true,code:63}])test(`city beacons ${theme} ${scene.name}: mounted readable status survives weather`,async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro')?'ro':'en',theme,scene.day,scene.code);
 const city=page.locator('.city-diorama');await expect(city).toHaveAttribute('data-bluetooth','connected');await expect(city).toHaveAttribute('data-radio-emitting','true');
 if(scene.name==='day-rain'){
  expect(await page.locator('.scene-precipitation').evaluate(node=>node.parentElement?.classList.contains('ambient-sky'))).toBe(true);
  expect(await page.locator('.scene-precipitation').evaluate(node=>Number(getComputedStyle(node).zIndex))).toBeGreaterThan(await city.evaluate(node=>Number(getComputedStyle(node).zIndex)));
 }
 await expect(page.locator('.city-architecture')).toHaveAttribute('src',`/ambient/gothic-city-${scene.day?'day':'night'}-unlit-v1.png`);
 const geometry=await page.locator('.city-radio-tower,.city-bluetooth').evaluateAll(nodes=>nodes.map(node=>{const r=node.getBoundingClientRect(),css=getComputedStyle(node);return{x:r.x,y:r.y,w:r.width,h:r.height,z:Number(css.zIndex)};}));
 expect(geometry).toHaveLength(2);expect(geometry.every(r=>r.w>=20&&r.h>=25&&r.x>=0&&r.y>=0&&r.x+r.w<=800&&r.y+r.h<=480)).toBe(true);
 await expect(city).toHaveAttribute('data-beacon-palette',!scene.day||theme==='night'?'night':'day');
 if(theme==='night'&&scene.day){
  // Manual Night must dim scenery without dimming real service indicators.
  // Their old common-ancestor filter passed state tests but erased the signs.
  await expect(page.locator('.ambient-sky')).toHaveCSS('filter','none');await expect(page.locator('.ambient-scenery')).toHaveCSS('filter','brightness(0.4)');await expect(city).toHaveCSS('opacity','1');await expect(page.locator('.city-scenery')).toHaveCSS('opacity','1');await expect(page.locator('.city-scenery')).toHaveCSS('filter','brightness(0.4)');
  const attenuation=await page.locator('.city-signal-core,.city-bluetooth-rune').evaluateAll(nodes=>nodes.map(node=>{const chain=[];for(let parent:Element|null=node;parent;parent=parent.parentElement){const style=getComputedStyle(parent);if(style.filter!=='none'||Number(style.opacity)<1)chain.push({className:parent.className,filter:style.filter,opacity:style.opacity});if(parent.classList.contains('ambient-sky'))break;}return chain;}));expect(attenuation).toEqual([[],[]]);
 }
 const assets=await page.locator('.city-radio-hardware,.city-bluetooth-hardware,.city-signal-core,.city-signal-ring').evaluateAll(nodes=>nodes.map(node=>{const image=node as HTMLImageElement;return{loaded:image.complete&&image.naturalWidth>0&&image.naturalHeight>0,src:image.getAttribute('src')};}));
 expect(assets).toHaveLength(9);expect(assets.every(asset=>asset.loaded&&(asset.src?.includes('/ambient/city-beacon-')||asset.src?.includes('/ambient/city-bluetooth-support-')))).toBe(true);await expect(page.locator('.city-bluetooth-rune')).toHaveCSS('background-size','3200% 100%');
 if(scene.code===45){const haze=Number(await page.locator('.ambient-sky').getAttribute('data-haze'));expect(haze).toBeGreaterThan(.75);const mistZ=await page.locator('.city-ground-mist').evaluate(node=>Number(getComputedStyle(node).zIndex));expect(geometry.every(r=>r.z>mistZ)).toBe(true);expect(Number(await page.locator('.city-ground-mist').evaluate(node=>getComputedStyle(node).opacity))).toBeGreaterThan(0);}
 for(const selector of ['.city-radio-emission .city-signal-ring[data-ring="1"]','.city-bluetooth-emission .city-signal-ring[data-ring="1"]']){const samples=await motionSamples(page,selector);expect(samples.length).toBeGreaterThan(1);expect(samples.every(s=>s.duration>=2000&&s.duration<=20000)).toBe(true);expect(new Set(samples.map(s=>s.opacity+':'+s.transform)).size).toBeGreaterThan(1);expect(samples.every(s=>s.opacity>=.39)).toBe(true);}
 for(const wrapper of ['.city-radio-emission','.city-bluetooth-emission']){await expect(page.locator(wrapper)).toHaveCSS('opacity','1');const delays=await page.locator(wrapper+' .city-signal-ring').evaluateAll(nodes=>nodes.map(node=>getComputedStyle(node).animationDelay));expect(new Set(delays).size).toBe(3);if(wrapper==='.city-radio-emission')await expect(page.locator(wrapper+' .city-signal-core')).toHaveCSS('opacity','1');else await expect(page.locator('.city-bluetooth-rune')).toHaveCSS('opacity','1');}
 expect(await page.evaluate(()=>document.documentElement.scrollWidth>800||document.documentElement.scrollHeight>480)).toBe(false);expect(f.writes).toEqual([]);
 await page.screenshot({path:info.outputPath(`${theme}-${scene.name}-beacons.png`)});
});

test('city beacon lifecycle: off, idle, connected and playback have truthful motion without mutations',async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro')?'ro':'en','night');const city=page.locator('.city-diorama');
 f.state.player.state='paused';f.state.bluetooth.devices=[];await page.clock.runFor(2700);await expect(city).toHaveAttribute('data-radio-emitting','false');await expect(page.locator('.city-radio-emitter')).toHaveCount(0);await expect(page.locator('.city-radio-hardware')).toBeVisible();await expect(city).toHaveAttribute('data-bluetooth','on');await expect(page.locator('.city-bluetooth-emission')).toHaveCSS('opacity','0');await expect(page.locator('.city-bluetooth-emission')).toHaveCSS('animation-name','none');
 await page.screenshot({path:info.outputPath('powered-idle-paused.png')});
 f.state.bluetooth.powered=false;await page.clock.runFor(2700);await expect(city).toHaveAttribute('data-bluetooth','off');await expect(page.locator('.city-bluetooth')).toHaveCount(0);
 f.state.bluetooth.powered=true;f.state.bluetooth.devices=[{connected:true}];f.state.player.state='playing';await page.clock.runFor(2700);await expect(city).toHaveAttribute('data-bluetooth','connected');await expect(page.locator('.city-radio-emission')).toBeVisible();
 await city.evaluate(node=>(node as HTMLElement).style.transform='translateY(900px)');await expect(city).toHaveAttribute('data-animate','false');for(const selector of ['.city-radio-emission .city-signal-ring','.city-bluetooth-emission .city-signal-ring'])for(const ring of await page.locator(selector).all())await expect(ring).toHaveCSS('animation-play-state','paused');
 await city.evaluate(node=>(node as HTMLElement).style.transform='none');await expect(city).toHaveAttribute('data-animate','true');
 await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'));});await expect(city).toHaveAttribute('data-animate','false');for(const selector of ['.city-radio-emission .city-signal-ring','.city-bluetooth-emission .city-signal-ring'])for(const ring of await page.locator(selector).all())await expect(ring).toHaveCSS('animation-play-state','paused');
 await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:false});document.dispatchEvent(new Event('visibilitychange'));});await expect(city).toHaveAttribute('data-animate','true');
 await page.emulateMedia({reducedMotion:'reduce'});for(const selector of ['.city-radio-emission .city-signal-ring','.city-bluetooth-emission .city-signal-ring'])for(const ring of await page.locator(selector).all()){await expect(ring).toHaveCSS('animation-name','none');expect(Number(await ring.evaluate(node=>getComputedStyle(node).opacity))).toBeGreaterThan(0);}
 await page.screenshot({path:info.outputPath('reduced-motion-status-static.png')});expect(f.writes).toEqual([]);
});
