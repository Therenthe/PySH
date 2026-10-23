import {test,expect,type Page} from '@playwright/test';

async function fixture(page:Page,theme='night',language='en'){
 const now=new Date(theme==='night'?'2026-10-23T19:00:00Z':'2026-10-23T10:00:00Z');
 const state={preferences:{language,theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,timezone:'Europe/Bucharest',homeCards:[],favorites:[],location:{latitude:44.4,longitude:26.1}},network:{available:true,state:'connected',wireless_enabled:true,active_type:'wifi' as string|null,active_interface:'wlan0' as string|null,devices:[{type:'wifi',interface:'wlan0',state:'connected',signal:68}]},bluetooth:{available:true,powered:true,devices:[{connected:true}],prompts:[]},audio:{available:true,ready:true,outputs:[]},player:{state:'playing',kind:'radio'},weather:{current:{weather_code:0,is_day:theme==='night'?0:1,temperature_c:16},daily:[],updated_at:now.toISOString(),stale:false}};
 const mutations:string[]=[];
 await page.route('**/api/**',route=>{if(route.request().method()!=='GET')mutations.push(new URL(route.request().url()).pathname);return route.fulfill({json:new URL(route.request().url()).pathname==='/api/state'?state:{token:'city-motion-fixture'}})});
 await page.clock.install({time:now});await page.goto('/');await expect(page.locator('.city-diorama')).toHaveAttribute('data-animate','true');
 await page.locator('.city-architecture').evaluate(async node=>(node as HTMLImageElement).decode());
 return {state,mutations};
}

async function metroFrame(page:Page,time:number){
 return page.locator('.city-metro').evaluate((node,time)=>{
  const animation=node.getAnimations()[0];animation.pause();animation.currentTime=time+Number(animation.effect!.getTiming().delay);
  const style=getComputedStyle(node),matrix=new DOMMatrix(style.transform);
  return {x:node.getBoundingClientRect().x,opacity:Number(style.opacity),direction:matrix.a,duration:Number(animation.effect!.getTiming().duration),easing:animation.effect!.getTiming().easing};
 },time);
}

for(const theme of ['ink','night'])test(`quiet city ${theme}: constant metro crossings, bounded signals and static reduced-motion meaning`,async({page},info)=>{
 await fixture(page,theme,info.project.name.endsWith('ro')?'ro':'en');
 await expect(page.locator('.city-diorama')).toHaveAttribute('data-city-version','blender-v2');
 await expect(page.locator('.city-architecture')).toHaveAttribute('src',`/ambient/gothic-city-${theme==='night'?'night':'day'}-v2.png`);
 await expect(page.locator('.city-metro')).toHaveAttribute('src','/ambient/metro-v2.png');
 await expect(page.locator('.city-wifi-hardware')).toHaveAttribute('src',`/ambient/city-wifi-${theme==='night'?'night':'day'}-v1.png`);
 const frames=[];for(const time of [16000,19000,22000,62000,65000,68000])frames.push(await metroFrame(page,time));
 expect(frames[0]).toMatchObject({duration:100000,easing:'linear',direction:1,opacity:1});
 expect(frames[1].x-frames[0].x,JSON.stringify(frames)).toBeGreaterThan(0);
 expect(frames[1].x-frames[0].x).toBeCloseTo(frames[2].x-frames[1].x,1);
 expect(frames[3].direction).toBe(-1);
 expect(frames[4].x-frames[3].x).toBeLessThan(0);
 expect(frames[4].x-frames[3].x).toBeCloseTo(frames[5].x-frames[4].x,1);
 expect(Math.abs(frames[4].x-frames[3].x)).toBeCloseTo(frames[1].x-frames[0].x,1);
 const resting=await metroFrame(page,40000),track=(await page.locator('.city-metro-track').boundingBox())!;
 expect(resting.opacity).toBe(0);expect(resting.x).toBeGreaterThan(track.x+track.width);
 await metroFrame(page,16000);
 await expect(page.locator('.city-metro-track')).toHaveCSS('overflow','hidden');
 await expect(page.locator('.city-radio-emitter>i')).toHaveCount(2);
 await expect(page.locator('.city-radio-emitter>i').first()).toHaveCSS('animation-duration','6.8s');
 await expect(page.locator('.city-bluetooth.connected i')).toHaveCSS('animation-name','none');
 await page.screenshot({path:info.outputPath(`${theme}-metro-eastbound.png`)});
 await metroFrame(page,65000);
 await page.screenshot({path:info.outputPath(`${theme}-metro-westbound.png`)});
 await page.emulateMedia({reducedMotion:'reduce'});
 await expect(page.locator('.city-metro')).toHaveCSS('display','none');
 await expect(page.locator('.city-wifi-emission')).toHaveCSS('animation-name','none');
 await expect(page.locator('.city-wifi-emission')).toHaveCSS('opacity','0.72');
 await expect(page.locator('.city-radio-emitter>i').first()).toHaveCSS('opacity','0.5');
 await expect(page.locator('.city-bluetooth.connected i')).toBeVisible();
 await page.screenshot({path:info.outputPath(`${theme}-reduced-motion.png`)});
});

test('city pauses for offscreen or hidden independently, then resumes only when both allow',async({page})=>{
 await fixture(page);
 const city=page.locator('.city-diorama'),metro=page.locator('.city-metro');
 const hidden=(value:boolean)=>page.evaluate(value=>{Object.defineProperty(document,'hidden',{configurable:true,value});document.dispatchEvent(new Event('visibilitychange'));},value);
 await city.evaluate(node=>(node as HTMLElement).style.transform='translateY(800px)');
 await expect(city).toHaveAttribute('data-animate','false');await expect(metro).toHaveCSS('animation-play-state','paused');
 await hidden(true);await city.evaluate(node=>(node as HTMLElement).style.transform='none');
 await expect(city).toHaveAttribute('data-animate','false');
 await hidden(false);await expect(city).toHaveAttribute('data-animate','true');await expect(metro).toHaveCSS('animation-play-state','running');
 await hidden(true);await city.evaluate(node=>(node as HTMLElement).style.transform='translateY(800px)');
 await hidden(false);await expect(city).toHaveAttribute('data-animate','false');
 await city.evaluate(node=>(node as HTMLElement).style.transform='none');
 await expect(city).toHaveAttribute('data-animate','true');
});

test('city signal states follow actual route, playback and Bluetooth without mutation',async({page})=>{
 const {state,mutations}=await fixture(page);
 const city=page.locator('.city-diorama'),emission=page.locator('.city-wifi-emission');
 await expect(city).toHaveAttribute('data-wifi-active','true');await expect(emission).toHaveCSS('animation-name','city-wifi-transmission');
 state.network.active_type='ethernet';state.network.active_interface='end0';state.network.devices.push({type:'ethernet',interface:'end0',state:'connected',signal:0});
 state.player.state='paused';state.bluetooth.devices=[];
 await page.clock.runFor(2600);
 await expect(city).toHaveAttribute('data-wifi','connected');await expect(city).toHaveAttribute('data-wifi-active','false');await expect(emission).toHaveCSS('opacity','0');
 await expect(page.locator('.city-radio-emitter')).toHaveCount(0);await expect(city).toHaveAttribute('data-bluetooth','on');await expect(page.locator('.city-bluetooth i')).not.toBeVisible();
 state.network.devices[0].state='connecting';await page.clock.runFor(2600);
 await expect(city).toHaveAttribute('data-wifi','connecting');await expect(emission).toHaveCSS('animation-name','city-wifi-search');
 state.network.wireless_enabled=false;state.bluetooth.powered=false;await page.clock.runFor(2600);
 await expect(city).toHaveAttribute('data-wifi','off');await expect(emission).toHaveCSS('opacity','0');await expect(page.locator('.city-bluetooth')).toHaveCount(0);
 expect(mutations).toEqual([]);
});
