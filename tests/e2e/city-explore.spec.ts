import {test,expect,type Page} from '@playwright/test';
// Loopback-only controlled output/device fixtures, actual original Blender exports.
async function fixture(page:Page,ro:boolean,theme:string){
 const now=new Date(theme==='night'?'2026-10-24T18:00:00Z':'2026-10-24T10:00:00Z');
 const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,visualizerStyle:'wave',timezone:'Europe/Bucharest',location:{name:'București · Sector 5',latitude:44.4,longitude:26.1},homeCards:[],navigationCollapsed:true,navigationAutoHide:false,decorativeAircraft:false,decorativeLunarDust:false,favorites:[],shortcuts:[]},network:{available:true,state:'connected',wireless_enabled:true,active_type:'wifi',active_interface:'wlan0',devices:[{type:'wifi',interface:'wlan0',state:'connected',signal:68}]},bluetooth:{available:true,powered:true,devices:[{connected:true,name:'Fixture speaker'}],prompts:[]},audio:{available:true,ready:true,volume:3,mute:false,outputs:[]},player:{state:'playing',kind:'radio',url:'https://example.invalid/retained',station_name:'Retained station'},weather:{stale:false,current:{weather_code:0,is_day:theme==='night'?0:1,temperature_c:14},daily:[],updated_at:now.toISOString(),alerts:{state:'available',updated_at:now.toISOString(),alerts:[]}}};
 const writes:string[]=[],errors:string[]=[];page.on('pageerror',error=>errors.push(String(error)));
 await page.route('**/api/**',async route=>{const req=route.request(),path=new URL(req.url()).pathname;if(req.method()!=='GET')writes.push(path);if(path==='/api/preferences'&&req.method()==='PATCH'){Object.assign(state.preferences,req.postDataJSON());await route.fulfill({json:state.preferences});return;}const json=path==='/api/state'?state:path==='/api/session'?{token:'city-destinations-fixture'}:path==='/api/audio/visualization'?{available:true,status:'ready',waveform:Array(64).fill(.2),bars:Array(16).fill(.3),rms:.2,peak:.4,silent:false}:path==='/api/radio'?{stations:[]}:path==='/api/media'?{items:[],roots:[]}:{};await route.fulfill({json});});
 await page.clock.install({time:now});await page.goto('/');await expect(page.locator('.ambient-home')).toBeVisible();return {state,writes,errors};
}


const guide=(page:Page)=>page.locator('.city-wayfinding');
const toggle=(page:Page)=>page.locator('.city-explore-toggle');
const target=(page:Page,id:string)=>page.locator(`.city-wayfinding-sign[data-destination=${id}] button`);
const destinations=[['media','.media-page'],['audio','.settings-panel[data-settings-section=audio]'],['network','.settings-panel[data-settings-section=network]'],['settings','.settings-page'],['radio','.radio-page']] as const;
async function geometry(page:Page){
 const boxes=await page.locator('.city-wayfinding-target').evaluateAll(ns=>ns.map(n=>{const r=n.getBoundingClientRect();return{x:r.x,y:r.y,w:r.width,h:r.height,exposed:[[0,0],[-23,-23],[23,-23],[-23,23],[23,23]].every(([dx,dy])=>n.contains(document.elementFromPoint(r.x+r.width/2+dx,r.y+r.height/2+dy)))};}));
 expect(boxes).toHaveLength(5);
 // Chromium reports48px transformed targets as47.999984px at fractional positions.
 for(const b of boxes){expect(b.x).toBeGreaterThanOrEqual(-.001);expect(b.y).toBeGreaterThanOrEqual(57.999);expect(b.x+b.w).toBeLessThanOrEqual(800.001);expect(b.y+b.h).toBeLessThanOrEqual(480.001);expect(b.w).toBeGreaterThanOrEqual(47.999);expect(b.h).toBeGreaterThanOrEqual(47.999);expect(b.exposed).toBe(true);}
 for(let i=0;i<boxes.length;i++)for(let j=i+1;j<boxes.length;j++){const a=boxes[i],b=boxes[j];expect(a.x+a.w<=b.x||b.x+b.w<=a.x||a.y+a.h<=b.y||b.y+b.h<=a.y).toBe(true);}
 return boxes;
}
for(const theme of ['ink','night'])test(`Explore city ${theme}: five floating labels preserve state and remain discoverable`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme);f.state.preferences.homeCards=['weather','forecast','playback'];await page.clock.runFor(2700);const before=JSON.stringify(f.state);
 await expect(toggle(page)).toHaveAccessibleName(ro?'Explorează orașul':'Explore city');await toggle(page).tap();await expect(toggle(page)).toHaveAttribute('aria-pressed','true');await expect(guide(page)).toHaveAttribute('data-art-status','ready');
 await geometry(page);await expect(page.locator('.city-radio-neon')).toHaveAttribute('data-signal-status','ready');await expect(page.locator('.ambient-weather')).toBeHidden();await expect(page.locator('.ambient-forecast')).toBeHidden();await expect(page.locator('.ambient-dock')).toBeHidden();await page.screenshot({path:info.outputPath(`floating-${theme}.png`)});
 await page.clock.runFor(35000);await expect(page.locator('.app')).toHaveAttribute('data-home-phase','interactive');await expect(guide(page)).toHaveAttribute('data-state','open');
 await page.keyboard.press('Escape');await expect(guide(page)).toHaveCount(0);await expect(toggle(page)).toBeFocused();await expect(page.locator('.ambient-weather')).toBeVisible();expect(JSON.stringify(f.state)).toBe(before);expect(f.writes).toEqual([]);expect(f.errors).toEqual([]);
});
for(const theme of ['ink','night'])test(`Explore city ${theme}: ambient wake and temporary rail clearance do not change preferences`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme);await page.clock.runFor(31000);await expect(page.locator('.app')).toHaveAttribute('data-home-phase','ambient');await page.touchscreen.tap(200,30);await expect(page.locator('.app')).toHaveAttribute('data-home-phase','interactive');await expect(guide(page)).toHaveCount(0);
 await page.locator('.navigation-toggle').tap();await page.clock.runFor(500);f.writes.length=0;const before=JSON.stringify(f.state.preferences);await toggle(page).tap();await expect(guide(page)).toHaveAttribute('data-art-status','ready');await expect(page.locator('.app')).toHaveAttribute('data-navigation','retracted');await geometry(page);
 await page.screenshot({path:info.outputPath(`floating-${theme}-temporary-clearance.png`)});await toggle(page).tap();await expect(guide(page)).toHaveCount(0);expect(JSON.stringify(f.state.preferences)).toBe(before);expect(f.writes).toEqual([]);expect(f.errors).toEqual([]);
});
for(const theme of ['ink','night'])test(`Explore city ${theme}: every named 3D label enters its canonical destination`,async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro'),theme);await page.emulateMedia({reducedMotion:'reduce'});
 for(const [id,selector] of destinations){await page.goto('/');await toggle(page).tap();await expect(guide(page)).toHaveAttribute('data-art-status','ready');await target(page,id).tap();await expect(page.locator(selector)).toBeVisible();await expect(guide(page)).toHaveCount(0);}
 expect(f.writes).toEqual([]);expect(f.errors).toEqual([]);
});
for(const theme of ['ink','night'])test(`Explore city ${theme}: authored buoyancy, reversible opening and static reduced motion`,async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro'),theme);await toggle(page).tap();await expect(guide(page)).toHaveAttribute('data-art-status','ready');
 const carrier=page.locator('.city-wayfinding-sign').first();await expect.poll(()=>carrier.evaluate(n=>n.getAnimations().length)).toBe(1);
 // Actual authored trajectory is sampled at two points; the visible target moves
 // with its real 3D export instead of an unrelated decorative animation.
 const sample=async(ms:number)=>{await carrier.evaluate((n,ms)=>{const a=n.getAnimations()[0];a.pause();a.currentTime=ms;},ms);return target(page,'media').boundingBox();};
 const a=await sample(0),b=await sample(1000);expect(Math.abs(b!.y-a!.y)).toBeGreaterThan(.5);expect(Math.abs(b!.y-a!.y)).toBeLessThan(5);await geometry(page);await page.screenshot({path:info.outputPath(`floating-${theme}-buoyancy.png`)});
 await toggle(page).tap();await toggle(page).tap();await expect(guide(page)).toHaveAttribute('data-state','open');await expect(guide(page)).toHaveAttribute('data-art-status','ready');await geometry(page);
 await page.emulateMedia({reducedMotion:'reduce'});await expect.poll(()=>carrier.evaluate(n=>n.getAnimations({subtree:true}).length)).toBe(0);await page.screenshot({path:info.outputPath(`floating-${theme}-reduced.png`)});await toggle(page).tap();await expect(guide(page)).toHaveCount(0);expect(f.writes).toEqual([]);expect(f.errors).toEqual([]);
});
test('Explore city: failed artwork has a bounded usable fallback and closes cleanly',async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro'),'night');await page.route('**/ambient/city-wayfinding-*.png',r=>r.abort());await page.reload();await toggle(page).tap();await expect(page.locator('.city-wayfinding-fallback')).toBeVisible();await expect(page.locator('.city-wayfinding-fallback button')).toHaveCount(5);await page.screenshot({path:info.outputPath('floating-art-failure.png')});await toggle(page).tap();await expect(guide(page)).toHaveCount(0);expect(f.writes).toEqual([]);expect(f.errors).toEqual([]);
});

test('Explore city: returning to a visible page keeps the settled label pose',async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro'),'night');await toggle(page).tap();await expect(guide(page)).toHaveAttribute('data-art-status','ready');
 await expect.poll(()=>page.locator('.city-wayfinding-art').evaluateAll(ns=>ns.map(n=>n.getAnimations().length))).toEqual([1,1,1,1,1]);
 const settled=()=>page.locator('.city-wayfinding-art').evaluateAll(ns=>ns.every(n=>n.getAnimations().every(a=>Number(a.currentTime)>=Number(a.effect?.getComputedTiming().endTime)-.01)));
 await expect.poll(settled).toBe(true);
 // Synthetic visibility events exercise the React lifecycle; native tab behaviour is a separate gate.
 await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'));});
 await expect.poll(()=>page.locator('.city-wayfinding-art').evaluateAll(ns=>ns.every(n=>n.getAnimations().every(a=>a.playState==='paused')))).toBe(true);
 await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:false});document.dispatchEvent(new Event('visibilitychange'));});
 await expect.poll(()=>page.locator('.city-wayfinding-art').evaluateAll(ns=>ns.every(n=>n.getAnimations().every(a=>a.playState==='paused')))).toBe(true);expect(await settled()).toBe(true);
 await page.clock.runFor(200);await expect(page.locator('.city-radio-neon')).toHaveAttribute('data-signal-status','ready');await expect.poll(()=>page.locator('.city-radio-neon img').evaluateAll(ns=>ns.some(n=>Number(getComputedStyle(n).opacity)>0))).toBe(true);
 await page.screenshot({path:info.outputPath('floating-settled-after-visibility.png')});await toggle(page).tap();await expect(guide(page)).toHaveCount(0);expect(f.writes).toEqual([]);expect(f.errors).toEqual([]);
});

test('Explore city: late artwork cannot replace focused timeout fallback',async({page},info)=>{
 const pending:import('@playwright/test').Route[]=[];await page.route('**/ambient/city-wayfinding-*.png',route=>{pending.push(route);});
 const f=await fixture(page,info.project.name.endsWith('ro'),'night');await toggle(page).tap();await page.clock.runFor(2700);
 const fallback=page.locator('.city-wayfinding-fallback');await expect(fallback).toBeVisible();const first=fallback.locator('button').first();await first.focus();
 const responses=pending.map(route=>page.waitForResponse(response=>response.url()===route.request().url()));for(const route of pending)await route.continue();await Promise.all(responses);await page.clock.runFor(50);
 await expect(guide(page)).toHaveAttribute('data-art-status','error');await expect(first).toBeFocused();await page.screenshot({path:info.outputPath('floating-late-art-preserves-fallback.png')});await first.press('Enter');await expect(page.locator('.media-page')).toBeVisible();expect(f.writes).toEqual([]);expect(f.errors).toEqual([]);
});

test('Explore city: art palette changes preserve the focused destination',async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro'),'ink');await toggle(page).tap();await expect(guide(page)).toHaveAttribute('data-art-status','ready');await target(page,'media').focus();
 f.state.preferences.theme='night';await page.clock.runFor(2700);await expect(page.locator('.app')).toHaveAttribute('data-theme','night');await expect(guide(page)).toHaveAttribute('data-art-status','ready');await expect(target(page,'media')).toBeFocused();
 await page.screenshot({path:info.outputPath('floating-palette-preserves-destination-focus.png')});await page.keyboard.press('Escape');await expect(guide(page)).toHaveCount(0);await expect(toggle(page)).toBeFocused();expect(f.writes).toEqual([]);expect(f.errors).toEqual([]);
});

test('Explore city: a delayed palette cannot steal a newer control focus',async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro'),'ink');await toggle(page).tap();await expect(guide(page)).toHaveAttribute('data-art-status','ready');await target(page,'media').focus();
 const pending:import('@playwright/test').Route[]=[];await page.route('**/ambient/city-wayfinding-*-night-*.png',route=>{pending.push(route);});
 f.state.preferences.theme='night';await page.clock.runFor(2100);await expect(guide(page)).toHaveAttribute('data-art-status','loading');await toggle(page).focus();
 const responses=pending.map(route=>page.waitForResponse(response=>response.url()===route.request().url()));for(const route of pending)await route.continue();await Promise.all(responses);await expect(guide(page)).toHaveAttribute('data-art-status','ready');await expect(toggle(page)).toBeFocused();
 await page.screenshot({path:info.outputPath('floating-palette-keeps-newer-control-focus.png')});await toggle(page).tap();await expect(guide(page)).toHaveCount(0);expect(f.writes).toEqual([]);expect(f.errors).toEqual([]);
});

test('Explore city: pressing a floating name lights its artwork without a rectangular plate',async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro'),'night');await toggle(page).tap();await expect(guide(page)).toHaveAttribute('data-art-status','ready');const label=target(page,'media');
 await label.evaluate(n=>{for(const a of n.parentElement!.getAnimations())a.pause();});const box=await label.boundingBox();await page.mouse.move(box!.x+box!.width/2,box!.y+box!.height/2);await page.mouse.down();
 try{await expect(label).toHaveAttribute('data-pressed','true');await expect(label).toHaveCSS('box-shadow','none');await expect(page.locator('.city-wayfinding-sign[data-destination=media] .city-wayfinding-art')).toHaveCSS('filter','brightness(1.15)');await page.screenshot({path:info.outputPath('floating-name-pressed.png')});}finally{await page.mouse.up();}
 expect(f.writes).toEqual([]);expect(f.errors).toEqual([]);
});

test('Explore city: slow closed preload does not consume the open-time artwork budget',async({page},info)=>{
 const pending:import('@playwright/test').Route[]=[];await page.route('**/ambient/city-wayfinding-*.png',route=>{pending.push(route);});
 const f=await fixture(page,info.project.name.endsWith('ro'),'night');await expect.poll(()=>pending.length).toBe(5);await page.clock.runFor(3000);await expect(guide(page)).toHaveCount(0);
 const responses=pending.map(route=>page.waitForResponse(response=>response.url()===route.request().url()).then(response=>response.finished()));for(const route of pending)await route.continue();await Promise.all(responses);
 await toggle(page).tap();await expect(guide(page)).toHaveAttribute('data-art-status','ready');await geometry(page);await page.screenshot({path:info.outputPath('floating-slow-closed-preload-ready.png')});await page.keyboard.press('Escape');await expect(guide(page)).toHaveCount(0);expect(f.writes).toEqual([]);expect(f.errors).toEqual([]);
});
