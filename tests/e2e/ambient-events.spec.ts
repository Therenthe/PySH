import {test,expect,type Page} from '@playwright/test';

async function mountEvents(page:Page,night:boolean,language:string){
 await page.route('**/api/**',route=>{const path=new URL(route.request().url()).pathname;return route.fulfill({json:path==='/api/session'?{token:'fixture'}:path==='/api/state'?{preferences:{language,setupComplete:true,screensaverMinutes:0},network:{},bluetooth:{devices:[],prompts:[]},audio:{},player:{},weather:{}}:{ok:true}});});
 await page.goto('/');await expect(page.locator('.ambient-home')).toBeVisible();
 await page.evaluate(async night=>{
  const main=await (await fetch('/src/main.tsx')).text(),source=await(await fetch('/src/AmbientEvents.tsx')).text();
  const reactURL=source.match(/from\s+["']([^"']*\/react\.js[^"']*)["']/)![1],domURL=main.match(/from\s+["']([^"']*react-dom_client\.js[^"']*)["']/)![1];
  const reactModule=await import(reactURL),domModule=await import(domURL),events=await import('/src/AmbientEvents.tsx' as string),React=reactModule.default||reactModule,createRoot=domModule.createRoot||domModule.default.createRoot;
  document.body.innerHTML='<div id="ambient-audit" style="position:fixed;inset:0;background:linear-gradient(#071522,#172f39);overflow:hidden"></div><style>.ambient-moon{right:23px!important;top:85px!important}</style>';
  document.body.style.margin='0';const root=createRoot(document.getElementById('ambient-audit'));
  const {Moon}=await import('/src/Moon.tsx' as string);
  (window as any).eventGeometry=events;(window as any).renderEvents=(enabled=true,moonVisible=true,lunarDust=true)=>root.render(React.createElement(React.Fragment,null,night&&moonVisible?React.createElement(Moon,{now:new Date('2026-10-04T20:00:00Z')}):null,React.createElement(events.AmbientEvents,{enabled,night,moonVisible,lunarDust})));(window as any).renderEvents();
 },night);
 await expect(page.locator('.ambient-events')).toBeAttached();
}

test('aircraft and lunar dust geometries are bounded and variable',async({page},info)=>{
 await mountEvents(page,true,info.project.name.endsWith('ro')?'ro':'en');
 const result=await page.evaluate(()=>{
  const module=(window as any).eventGeometry,low=module.createAircraft(1,()=>0),high=module.createAircraft(2,()=>.999999),dustLow=module.createLunarDust(3,()=>0),dustHigh=module.createLunarDust(4,()=>.999999);
  return {low,high,dustLow,dustHigh};
 });
 expect(result.low.fromX).toBeLessThan(0);expect(result.low.toX).toBeGreaterThan(100);expect(result.high.fromX).toBeGreaterThan(100);expect(result.high.toX).toBeLessThan(0);
 for(const flight of [result.low,result.high]){expect(flight.fromY).toBeGreaterThanOrEqual(12);expect(flight.toY).toBeGreaterThanOrEqual(8);expect(flight.toY).toBeLessThanOrEqual(54);expect(Math.cos(flight.heading*Math.PI/180)*(flight.toX-flight.fromX)).toBeGreaterThan(0);expect(flight.duration).toBeGreaterThanOrEqual(24000);expect(flight.duration).toBeLessThanOrEqual(42000);}
 expect(result.low.duration).not.toBe(result.high.duration);expect(result.low.scale).not.toBe(result.high.scale);
 for(const dust of [result.dustLow,result.dustHigh]){expect(Math.hypot(dust.x-45,dust.y-45)+dust.radius*1.7).toBeLessThan(44);expect(dust.duration).toBeLessThanOrEqual(2700);}
});

for(const night of [false,true])test(`decorative events ${night?'night':'day'}: bounded, hidden/reduced-motion cleanup`,async({page},info)=>{
 test.setTimeout(60000);
 await page.addInitScript(()=>{crypto.getRandomValues=((array:Uint32Array)=>{array.fill(0);return array;}) as typeof crypto.getRandomValues;});
 await page.clock.install();await mountEvents(page,night,info.project.name.endsWith('ro')?'ro':'en');
 await page.clock.runFor(18020);await expect(page.locator('[data-ambient-event=aircraft]')).toHaveCount(1);
 await page.locator('.ambient-flight').evaluate(el=>{el.getAnimations().forEach(animation=>{animation.currentTime=12000;animation.pause();});});
 await page.screenshot({path:info.outputPath(`ambient-aircraft-${night?'night':'day'}.png`)});
 const rect=(await page.locator('.ambient-flight').boundingBox())!;expect(rect.x).toBeGreaterThan(300);expect(rect.x).toBeLessThan(500);
 await page.clock.runFor(47000);await expect(page.locator('[data-ambient-event=lunar-dust]')).toHaveCount(night?1:0);
 if(night){await page.locator('.ambient-lunar-event').evaluate(el=>el.getAnimations({subtree:true}).forEach(animation=>{animation.currentTime=500;animation.pause();}));await page.screenshot({path:info.outputPath('ambient-lunar-dust.png')});}
 for(let i=0;i<20;i++){await page.clock.runFor(10000);expect(await page.locator('[data-ambient-event]').count()).toBeLessThanOrEqual(2);}
 await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});document.dispatchEvent(new Event('visibilitychange'));});await expect(page.locator('[data-ambient-event]')).toHaveCount(0);await page.clock.runFor(300000);await expect(page.locator('[data-ambient-event]')).toHaveCount(0);
 await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,get:()=>false});document.dispatchEvent(new Event('visibilitychange'));});await page.clock.runFor(18020);await expect(page.locator('[data-ambient-event=aircraft]')).toHaveCount(1);
 await page.emulateMedia({reducedMotion:'reduce'});await expect(page.locator('[data-ambient-event]')).toHaveCount(0);await page.clock.runFor(300000);await expect(page.locator('[data-ambient-event]')).toHaveCount(0);
 await page.emulateMedia({reducedMotion:'no-preference'});await page.clock.runFor(18020);await expect(page.locator('[data-ambient-event=aircraft]')).toHaveCount(1);
 await page.evaluate(()=>(window as any).renderEvents(true,false));await page.clock.runFor(66000);await expect(page.locator('[data-ambient-event=lunar-dust]')).toHaveCount(0);
 await page.evaluate(()=>(window as any).renderEvents(true,true,false));await page.clock.runFor(66000);await expect(page.locator('[data-ambient-event=lunar-dust]')).toHaveCount(0);
 await page.evaluate(()=>(window as any).renderEvents(false));await expect(page.locator('[data-ambient-event]')).toHaveCount(0);
});
