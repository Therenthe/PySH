import {test,expect,type Page,type Locator} from '@playwright/test';

// Isolated loopback UAT. These routes never touch the Pi, real preferences,
// transport or networks. Actual Blender playback is exercised separately from
// blocked-media failure/cancellation probes; synthetic events are labelled.
async function fixture(page:Page,language:string,theme:string,day=true){
 const now=new Date(day?'2026-10-24T10:00:00Z':'2026-10-24T20:00:00Z');
 const state:any={preferences:{language,theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,visualizerStyle:'wave',visualizerSize:'compact',timezone:'Europe/Bucharest',location:{name:'Bucure\u0219ti \u00b7 Sector 5',latitude:44.4,longitude:26.1},homeCards:['weather','forecast','playback'],homePositions:{weather:{x:0,y:0},forecast:{x:0,y:.38},playback:{x:0,y:0,anchorY:'bottom'}},navigationCollapsed:true,navigationAutoHide:false,decorativeAircraft:false,decorativeLunarDust:false,favorites:[],shortcuts:['radio','media']},network:{available:true,state:'connected',wireless_enabled:true,active_type:'ethernet',active_interface:'end0',devices:[{type:'ethernet',interface:'end0',state:'connected'},{type:'wifi',interface:'wlan0',state:'connected',signal:68}]},bluetooth:{available:true,powered:true,devices:[{connected:true}],prompts:[]},audio:{available:true,ready:true,volume:3,mute:false,outputs:[]},player:{state:'playing',kind:'radio',url:'https://example.invalid/radio',station_name:'Fixture Radio',title:'Artist \u00b7 Track'},weather:{stale:false,current:{weather_code:45,is_day:day?1:0,temperature_c:12,visibility_m:100,cloud_cover_pct:100,wind_kmh:8},daily:[],updated_at:now.toISOString()}};
 const writes:any[]=[];const errors:string[]=[];page.on('pageerror',error=>errors.push(String(error)));
 await page.route('**/api/**',async route=>{const req=route.request(),path=new URL(req.url()).pathname;let json:any={ok:true};if(path==='/api/session')json={token:'isolated-radio-city-entry'};else if(path==='/api/state')json=state;else if(path==='/api/radio')json={stations:[]};else if(path==='/api/audio/visualization')json={available:true,status:'ready',waveform:Array(64).fill(.25),bars:Array(16).fill(.4),rms:.25,peak:.65,silent:false};else if(req.method()!=='GET')writes.push({path,body:req.postDataJSON()});await route.fulfill({json});});
 await page.clock.install({time:now});await page.goto('/');await expect(page.locator('.ambient-home')).toBeVisible();
 return {state,writes,errors,saved:JSON.stringify({preferences:state.preferences,player:state.player,audio:state.audio})};
}
const entry=(page:Page)=>page.locator('button.city-radio-entry');
const dialog=(page:Page)=>page.locator('.radio-city-entry[role=dialog]');
const cancel=(page:Page,ro:boolean)=>dialog(page).getByRole('button',{name:ro?'Anulează':'Cancel',exact:true});
const skip=(page:Page,ro:boolean)=>dialog(page).getByRole('button',{name:ro?'Omite animația':'Skip animation',exact:true});
async function target(locator:Locator){const box=await locator.boundingBox();expect(box).not.toBeNull();expect(box!.width).toBeGreaterThanOrEqual(48);expect(box!.height).toBeGreaterThanOrEqual(48);expect(box!.x).toBeGreaterThanOrEqual(0);expect(box!.y).toBeGreaterThanOrEqual(0);expect(box!.x+box!.width).toBeLessThanOrEqual(800);expect(box!.y+box!.height).toBeLessThanOrEqual(480);}
async function capture(page:Page,name:string){await page.screenshot({path:test.info().outputPath(name+'.png')});expect(await page.evaluate(()=>document.documentElement.scrollWidth>800||document.documentElement.scrollHeight>480)).toBe(false);}
function stable(f:Awaited<ReturnType<typeof fixture>>){expect(f.writes).toEqual([]);expect(f.errors).toEqual([]);expect(JSON.stringify({preferences:f.state.preferences,player:f.state.player,audio:f.state.audio})).toBe(f.saved);}
async function holdClip(page:Page){let release!:()=>void;const held=new Promise<void>(resolve=>release=resolve);await page.route('**/ambient/radio-entry-*.webm',async route=>{await held;await route.continue().catch(()=>{});});return release;}
async function hidden(page:Page,value:boolean){await page.evaluate(value=>{Object.defineProperty(document,'hidden',{configurable:true,value});document.dispatchEvent(new Event('visibilitychange'));},value);}

for(const theme of ['ink','night'])test(`Radio building ${theme}: independent accessible entry, ambient wake and no other building navigation`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro?'ro':'en',theme);
 await expect(entry(page)).toHaveAccessibleName(ro?'Intră în Radio':'Enter Radio');await target(entry(page));
 f.state.player.state='idle';f.state.player.url='';f.state.preferences.visualizerStyle='off';f.state.preferences.homeCards=[];await page.clock.runFor(2700);await expect(entry(page)).toBeVisible();await target(entry(page));
 // Changes above are fixture setup, never writes from navigation.
 const saved=JSON.stringify({preferences:f.state.preferences,player:f.state.player,audio:f.state.audio});
 await page.clock.runFor(31000);await expect(page.locator('.app')).toHaveAttribute('data-home-phase','ambient');const box=(await entry(page).boundingBox())!;await page.touchscreen.tap(box.x+box.width/2,box.y+box.height/2);await expect(page.locator('.app')).toHaveAttribute('data-home-phase','interactive');await expect(dialog(page)).toHaveCount(0);await expect(page.locator('.radio-page')).toHaveCount(0);
 for(const selector of ['.city-bluetooth','.city-wifi']){const point=(await page.locator(selector).boundingBox())!;await page.touchscreen.tap(point.x+point.width/2,point.y+point.height/2);await expect(dialog(page)).toHaveCount(0);await expect(page.locator('.radio-page')).toHaveCount(0);}
 await capture(page,'independent-entry-after-wake');expect(f.writes).toEqual([]);expect(f.errors).toEqual([]);expect(JSON.stringify({preferences:f.state.preferences,player:f.state.player,audio:f.state.audio})).toBe(saved);
});

for(const theme of ['ink','night'])for(const day of [true,false])test(`Radio doorway ${theme} actual-${day?'day':'night'}: actual Blender clip completes into usable Radio`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro?'ro':'en',theme,day);await page.clock.resume();await entry(page).tap();await expect(dialog(page)).toBeVisible();await target(cancel(page,ro));await target(skip(page,ro));
 const video=dialog(page).locator('video');await expect(video).toHaveAttribute('src',`/ambient/radio-entry-${day?'day':'night'}-v1.webm`);await expect(dialog(page)).toHaveAttribute('data-phase','playing',{timeout:5000});await expect(page.locator('.main-area')).toHaveCSS('opacity','0');await expect(page.locator('.city-diorama')).toHaveCSS('opacity','0');await expect(page.locator('.ambient-sky')).toHaveCSS('opacity','1');expect(await page.locator('.ambient-sky').evaluate(node=>node.parentElement?.classList.contains('app')&&!node.closest('.main-area'))).toBe(true);
 expect(await video.evaluate(node=>{const v=node as HTMLVideoElement;return v.muted&&v.readyState>=2&&v.videoWidth>0&&v.videoHeight>0&&v.duration>0&&v.duration<=6;})).toBe(true);await capture(page,`doorway-${theme}-${day?'day':'night'}-playing`);
 await expect(page.locator('.radio-page')).toBeVisible({timeout:9000});await expect(dialog(page)).toHaveCount(0);await expect(page.locator('.station-list')).toBeVisible();await expect(page.locator('.radio-page .search-field')).toBeEnabled();await expect(page.locator('.radio-page .search-field')).toBeFocused();await capture(page,'radio-after-real-clip');await page.locator('.radio-page .search-field').tap();await expect(page.locator('.keyboard-card[role=dialog]')).toBeVisible();await page.locator('.keyboard-card').getByRole('button',{name:ro?'Închide':'Close',exact:true}).tap();await expect(page.locator('.radio-page')).toBeVisible();stable(f);
});

for(const theme of ['ink','night'])test(`Radio arrival ${theme}: navigation auto-hide pending preferences retains destination focus`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro?'ro':'en',theme);f.state.preferences.navigationAutoHide=true;await page.clock.runFor(2700);
 const saved=JSON.stringify({preferences:f.state.preferences,player:f.state.player,audio:f.state.audio});let release!:()=>void,started!:()=>void;const held=new Promise<void>(resolve=>release=resolve),requestStarted=new Promise<void>(resolve=>started=resolve);
 await page.route('**/api/preferences',async route=>{const request=route.request();expect(request.method()).toBe('PATCH');const body=request.postDataJSON();f.writes.push({path:'/api/preferences',body});Object.assign(f.state.preferences,body);started();await held;await route.fulfill({json:f.state.preferences});});
 await page.clock.resume();await entry(page).tap();await expect(dialog(page)).toHaveAttribute('data-phase','playing');await expect(page.locator('.radio-page')).toBeVisible({timeout:9000});await requestStarted;
 const search=page.locator('.radio-page .search-field');await expect(search).toBeDisabled();await page.waitForTimeout(350);await expect(search).not.toBeFocused();await capture(page,'radio-arrival-preferences-pending');release();
 await expect(search).toBeEnabled();await expect(search).toBeFocused();await page.keyboard.press('Enter');await expect(page.locator('.keyboard-card[role=dialog]')).toBeVisible();await page.keyboard.press('Escape');await expect(page.locator('.keyboard-card')).toHaveCount(0);await expect(search).toBeFocused();await capture(page,'radio-arrival-focus-after-preferences');
 expect(f.writes).toEqual([{path:'/api/preferences',body:{navigationCollapsed:true}}]);expect(f.errors).toEqual([]);expect(JSON.stringify({preferences:f.state.preferences,player:f.state.player,audio:f.state.audio})).toBe(saved);
});

for(const theme of ['ink','night'])test(`Radio entry ${theme}: cancel Escape skip and repeated input are bounded and preserve audio`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro'),release=await holdClip(page),f=await fixture(page,ro?'ro':'en',theme);
 await entry(page).tap();await expect(dialog(page)).toHaveAttribute('data-phase','loading');await expect(page.locator('.topbar')).toHaveCSS('opacity','0');await cancel(page,ro).tap();await expect(dialog(page)).toHaveCount(0);await expect(entry(page)).toBeFocused();
 await entry(page).focus();await page.keyboard.press('Enter');await expect(dialog(page)).toHaveCount(1);await page.keyboard.press('Escape');await expect(dialog(page)).toHaveCount(0);await entry(page).focus();await page.keyboard.press('Space');await expect(dialog(page)).toHaveCount(1);await cancel(page,ro).tap();await expect(dialog(page)).toHaveCount(0);
 // Deliberately repeated native DOM activations: only one entry may own completion.
 await entry(page).evaluate(node=>{(node as HTMLButtonElement).click();(node as HTMLButtonElement).click();});await expect(dialog(page)).toHaveCount(1);await target(cancel(page,ro));await target(skip(page,ro));await capture(page,'entry-loading-single-owner');await skip(page,ro).tap();await expect(page.locator('.radio-page')).toBeVisible();await page.clock.runFor(50);await expect(page.locator('.radio-page .search-field')).toBeFocused();release();await page.clock.runFor(3500);await expect(dialog(page)).toHaveCount(0);stable(f);
});

for(const mode of ['load-error','play-rejection','load-timeout'])test(`Radio entry ${mode}: usable fallback without playback or preference mutation`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro');let release=()=>{};
 if(mode==='load-error')await page.route('**/ambient/radio-entry-*.webm',route=>route.abort('failed'));
 if(mode==='play-rejection')await page.addInitScript(()=>{HTMLMediaElement.prototype.play=function(){return Promise.reject(new DOMException('Isolated playback rejection','NotAllowedError'));};});
 if(mode==='load-timeout')release=await holdClip(page);
 const f=await fixture(page,ro?'ro':'en','night');await entry(page).tap();if(mode==='load-timeout')await page.clock.runFor(3000);await expect(page.locator('.radio-page')).toBeVisible({timeout:5000});await expect(dialog(page)).toHaveCount(0);await page.clock.runFor(50);await expect(page.locator('.radio-page .search-field')).toBeFocused();release();await page.clock.runFor(1000);await capture(page,'entry-'+mode+'-fallback');stable(f);
});

test('Radio entry reduced motion and hidden cancellation never leave surprise navigation',async({page},info)=>{
 const ro=info.project.name.endsWith('ro'),release=await holdClip(page),f=await fixture(page,ro?'ro':'en','night');await entry(page).tap();await expect(dialog(page)).toBeVisible();await hidden(page,true);await expect(dialog(page)).toHaveCount(0);await page.clock.runFor(3500);await hidden(page,false);await expect(page.locator('.ambient-home')).toBeVisible();await expect(page.locator('.radio-page')).toHaveCount(0);
 await page.emulateMedia({reducedMotion:'reduce'});await entry(page).tap();await expect(dialog(page)).toHaveCount(0);await expect(page.locator('.radio-page')).toBeVisible();await page.clock.runFor(50);await expect(page.locator('.radio-page .search-field')).toBeFocused();release();await capture(page,'entry-reduced-motion-direct');stable(f);
});

test('Radio entry document unmount discards pending media completion',async({page},info)=>{
 const release=await holdClip(page),f=await fixture(page,info.project.name.endsWith('ro')?'ro':'en','ink');await entry(page).tap();await expect(dialog(page)).toBeVisible();await page.reload();await expect(page.locator('.ambient-home')).toBeVisible();release();await page.clock.runFor(3500);await expect(dialog(page)).toHaveCount(0);await expect(page.locator('.radio-page')).toHaveCount(0);stable(f);
});

for(const theme of ['ink','night'])test(`City service cues ${theme}: waves-only actual WiFi route and true3D BT lifecycle`,async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro')?'ro':'en',theme),city=page.locator('.city-diorama'),rune=page.locator('.city-bluetooth-rune');await expect(page.locator('.city-wifi-wave')).toHaveCount(3);await expect(page.locator('.city-wifi-hardware,.city-wifi-lamp')).toHaveCount(0);await expect(city).toHaveAttribute('data-wifi-active','false');
 expect(await page.locator('.city-wifi-wave').evaluateAll(nodes=>nodes.every(node=>Number(getComputedStyle(node).opacity)===0))).toBe(true);
 f.state.network.active_type='wifi';f.state.network.active_interface='wlan0';f.state.network.devices[0].state='disconnected';await page.clock.runFor(2700);await expect(city).toHaveAttribute('data-wifi-active','true');expect(await page.locator('.city-wifi-wave').evaluateAll(nodes=>nodes.every(node=>getComputedStyle(node).animationName!=='none'))).toBe(true);
 await expect(rune).toHaveAttribute('data-turning','false');let turning=false;for(let i=0;i<60;i++){await page.clock.runFor(500);if(await rune.getAttribute('data-turning')==='true'){turning=true;break;}}expect(turning).toBe(true);
 // Sample the CSS sprite timeline explicitly: the JS timer clock does not
 // prove that a compositor animation advanced between screenshots.
 const positions=await rune.evaluate(node=>{const animation=node.getAnimations()[0];if(!animation)return[];animation.pause();const duration=Number(animation.effect!.getTiming().duration);const samples=[0,.25,.5,.75].map(phase=>{animation.currentTime=duration*phase;return getComputedStyle(node).backgroundPosition;});animation.play();return samples;});expect(new Set(positions).size).toBeGreaterThan(2);await capture(page,'bt-true3d-turn-wifi-waves');
 await city.evaluate(node=>(node as HTMLElement).style.transform='translateY(900px)');await expect(city).toHaveAttribute('data-animate','false');await expect(rune).toHaveAttribute('data-turning','false');await city.evaluate(node=>(node as HTMLElement).style.transform='none');await hidden(page,true);await expect(rune).toHaveAttribute('data-turning','false');await hidden(page,false);await page.emulateMedia({reducedMotion:'reduce'});await page.clock.runFor(30000);await expect(rune).toHaveAttribute('data-turning','false');
 f.state.network.active_type=null;f.state.network.active_interface=null;f.state.network.devices[1].state='disconnected';await page.clock.runFor(2700);await expect(city).toHaveAttribute('data-wifi-active','false');expect(await page.locator('.city-wifi-wave').evaluateAll(nodes=>nodes.every(node=>Number(getComputedStyle(node).opacity)===0))).toBe(true);
 f.state.bluetooth.powered=false;await page.clock.runFor(2700);await expect(rune).toHaveCount(0);expect(f.writes).toEqual([]);expect(f.errors).toEqual([]);
});
