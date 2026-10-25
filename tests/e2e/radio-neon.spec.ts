import {test,expect,type Page,type Locator} from '@playwright/test';
import {openSettingsSection} from './settings-navigation';

// Loopback-only controlled UAT: these samples are measured-output fixtures, not
// decorative audio, and all state mutations remain inside this browser test.
async function fixture(page:Page,language:string,theme:string,day=false){
 const now=new Date(day?'2026-10-24T10:00:00Z':'2026-10-24T20:00:00Z');
 const positions={weather:{x:.02,y:.02},forecast:{x:.04,y:.5},playback:{x:.03,y:.78},visualizer:{x:.06,y:.7,anchorX:'right',anchorY:'bottom'}};
 const state:any={preferences:{language,theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,visualizerStyle:'wave',visualizerSize:'compact',timezone:'Europe/Bucharest',location:{name:'București · Sector 5',latitude:44.4,longitude:26.1},homeCards:['weather','forecast','playback'],homePositions:positions,navigationCollapsed:true,navigationAutoHide:false,shortcuts:['radio','media'],decorativeAircraft:false},network:{available:true,state:'connected'},bluetooth:{available:true,powered:false,devices:[],prompts:[]},audio:{available:true,ready:true,volume:40,mute:false,outputs:[]},player:{state:'playing',kind:'radio',url:'https://example.invalid/radio',station_name:'Fixture Radio',title:'Artist · Track'},weather:{stale:false,current:{weather_code:0,is_day:day?1:0,temperature_c:16},daily:[],updated_at:now.toISOString()}};
 const sample:any={available:true,status:'ready',waveform:Array(64).fill(.1),bars:Array(16).fill(.1),rms:.1,peak:.2,silent:false};
 const actions:any[]=[];let reads=0;
 await page.route('**/api/**',async route=>{const req=route.request(),path=new URL(req.url()).pathname;let json:any={ok:true};if(path==='/api/session')json={token:'isolated-radio-neon-uat'};else if(path==='/api/state')json=state;else if(path==='/api/audio/visualization'){reads++;json=sample;}else if(path==='/api/radio')json={stations:[]};else if(req.method()!=='GET'){const body=req.postDataJSON();actions.push({path,body});if(path==='/api/preferences'){Object.assign(state.preferences,body);json=state.preferences;}if(path==='/api/player'){state.player.state=body.action==='pause'?'paused':'playing';}if(path==='/api/audio')Object.assign(state.audio,body);}await route.fulfill({json});});
 await page.clock.install({time:now});await page.goto('/');await expect(page.locator('.ambient-home')).toBeVisible();
 return {state,sample,actions,positions,reads:()=>reads};
}
const neon=(page:Page)=>page.locator('.city-radio-neon');
const button=(page:Page)=>page.locator('button.city-radio-entry');
const zones=(page:Page)=>neon(page).locator('[data-neon-zone]');
const opacities=(page:Page)=>zones(page).evaluateAll(nodes=>nodes.map(node=>Number((node as HTMLElement).style.opacity)));
async function advance(page:Page,ms=2700){await page.clock.runFor(ms);}
async function capture(page:Page,name:string){await page.screenshot({path:test.info().outputPath(name+'.png')});}
async function target(locator:Locator){const box=await locator.boundingBox();expect(box).not.toBeNull();expect(box!.width).toBeGreaterThanOrEqual(48);expect(box!.height).toBeGreaterThanOrEqual(48);expect(box!.x).toBeGreaterThanOrEqual(0);expect(box!.y).toBeGreaterThanOrEqual(0);expect(box!.x+box!.width).toBeLessThanOrEqual(800);expect(box!.y+box!.height).toBeLessThanOrEqual(480);}

for(const theme of ['ink','night'])for(const day of [false,true])test(`radio neon ${theme} actual-${day?'day':'night'}: eight Blender zones respond to genuine amplitude`,async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro')?'ro':'en',theme,day);
 await expect(neon(page)).toHaveAttribute('data-signal-status','ready');await expect(neon(page)).toHaveAttribute('data-neon-night',String(!day));await expect(neon(page)).toHaveAttribute('data-neon-palette',!day||theme==='night'?'night':'day');await expect(zones(page)).toHaveCount(8);
 await zones(page).evaluateAll(nodes=>Promise.all(nodes.map(node=>(node as HTMLImageElement).decode())));
 expect(await zones(page).evaluateAll(nodes=>nodes.every(node=>{const image=node as HTMLImageElement;return image.naturalWidth>0&&image.naturalHeight>0&&image.src.includes('/ambient/');}))).toBe(true);
 const low=await opacities(page);
 // Wait for this changed network sample and its rendered state. A long virtual
 // jump can run the900ms fetch deadline before mocked response-body delivery.
 const fresh=page.waitForResponse(async response=>{if(new URL(response.url()).pathname!=='/api/audio/visualization'||!response.ok())return false;const sample=await response.json().catch(()=>null);return sample?.available===true&&sample?.peak===.9&&sample?.bars?.[0]===.9;});
 f.sample.bars=Array.from({length:16},(_,i)=>i<8?.9:.4);f.sample.rms=.6;f.sample.peak=.9;await advance(page,200);await fresh;
 await expect(neon(page)).toHaveAttribute('data-signal-status','ready');await expect.poll(async()=>Math.max(...await opacities(page))).toBeGreaterThan(.8);
 const high=await opacities(page);expect(Math.max(...high)).toBeLessThanOrEqual(1);expect(Math.max(...high)).toBeGreaterThan(.8);expect(high.some((value,i)=>value>low[i]+.02)).toBe(true);expect(new Set(high.map(value=>value.toFixed(3))).size).toBeGreaterThan(1);
 expect(await zones(page).evaluateAll(nodes=>nodes.every(node=>getComputedStyle(node).animationName==='none'))).toBe(true);
 await expect(page.locator('.ambient-home .audio-visualizer')).toHaveCount(0);await expect(button(page)).toHaveAccessibleName(/Radio/);await target(button(page));await capture(page,`neon-${theme}-${day?'day':'night'}-measured`);expect(f.actions).toEqual([]);
});

for(const theme of ['ink','night'])test(`radio neon ${theme}: measured quiet-output day fog retains genuine PCM visibility`,async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro')?'ro':'en',theme,true);
 // Representative measured range from the device, with output volume3. This
 // controlled fixture changes no device audio or weather and invents no gain.
 f.state.audio.volume=3;Object.assign(f.state.weather.current,{weather_code:45,visibility_m:100,cloud_cover_pct:100});
 f.sample.bars=Array.from({length:16},(_,i)=>.24+i*.01);f.sample.rms=.2479;f.sample.peak=.672;
 await advance(page);await expect(neon(page)).toHaveAttribute('data-signal-status','ready');await expect(neon(page)).toHaveAttribute('data-neon-night','false');await expect(neon(page)).toHaveAttribute('data-neon-palette',theme==='night'?'night':'day');
 await expect.poll(async()=>Math.max(...await opacities(page))).toBeGreaterThan(.6);
 const values=await opacities(page);for(let i=0;i<8;i++)expect(values[i]).toBeCloseTo(Math.sqrt(f.sample.bars[i*2+1]),5);
 expect(Number(await page.locator('.ambient-sky').getAttribute('data-haze'))).toBeGreaterThan(.75);
 expect(await zones(page).evaluateAll((nodes,night)=>nodes.every(node=>(node as HTMLImageElement).src.includes(night?'/radio-neon-zone-':'/radio-neon-day-zone-')),theme==='night')).toBe(true);
 await advance(page,31000);await expect(page.locator('.app')).toHaveAttribute('data-home-phase','ambient');await capture(page,`measured-day-fog-${theme}`);expect(f.actions).toEqual([]);
});

for(const theme of ['ink','night'])test(`radio neon ${theme}: pause mute zero unavailable malformed silent never imply a party`,async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro')?'ro':'en',theme);
 await expect(neon(page)).toHaveAttribute('data-signal-status','ready');
 for(const [label,change,undo]of [
  ['pause',()=>f.state.player.state='paused',()=>f.state.player.state='playing'],
  ['mute',()=>f.state.audio.mute=true,()=>f.state.audio.mute=false],
  ['zero-volume',()=>f.state.audio.volume=0,()=>f.state.audio.volume=40],
  ['no-output',()=>f.state.audio.ready=false,()=>f.state.audio.ready=true],
 ]as const){change();await advance(page);await expect(neon(page)).toHaveAttribute('data-signal-status','inactive');expect((await opacities(page)).every(value=>value===0)).toBe(true);await capture(page,`neon-${theme}-${label}`);const reads=f.reads();await advance(page,500);expect(f.reads()-reads).toBeLessThanOrEqual(1);undo();await advance(page);await expect(neon(page)).toHaveAttribute('data-signal-status','ready');}
 f.sample.available=false;f.sample.status='unavailable';await advance(page,1100);await expect(neon(page)).toHaveAttribute('data-signal-status','unavailable');expect((await opacities(page)).every(value=>value===0)).toBe(true);await capture(page,`neon-${theme}-unavailable`);
 f.sample.available=true;f.sample.bars=[1];await advance(page,1100);await expect(neon(page)).toHaveAttribute('data-signal-status','unavailable');expect((await opacities(page)).every(value=>value===0)).toBe(true);
 f.sample.bars=Array(16).fill(0);f.sample.waveform=Array(64).fill(0);f.sample.rms=0;f.sample.peak=0;f.sample.silent=true;f.sample.status='ready';await advance(page,1100);expect((await opacities(page)).every(value=>value===0)).toBe(true);await capture(page,`neon-${theme}-silent`);expect(f.actions).toEqual([]);
});

test('radio neon lifecycle: one reader, hidden and offscreen stop, reduced motion downsamples',async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro')?'ro':'en','night');await expect(neon(page)).toHaveAttribute('data-signal-status','ready');
 await page.clock.resume();let before=f.reads();await page.waitForTimeout(1100);const active=f.reads()-before;expect(active).toBeGreaterThanOrEqual(5);expect(active).toBeLessThanOrEqual(13);
 const city=page.locator('.city-diorama');await city.evaluate(node=>(node as HTMLElement).style.transform='translateY(900px)');await expect(city).toHaveAttribute('data-animate','false');before=f.reads();await advance(page,1100);expect(f.reads()-before).toBeLessThanOrEqual(1);expect((await opacities(page)).every(value=>value===0)).toBe(true);
 await city.evaluate(node=>(node as HTMLElement).style.transform='none');await expect(city).toHaveAttribute('data-animate','true');await advance(page,1200);await expect(neon(page)).toHaveAttribute('data-signal-status','ready');
 await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'));});await expect(city).toHaveAttribute('data-animate','false');before=f.reads();await advance(page,1100);expect(f.reads()-before).toBeLessThanOrEqual(1);expect((await opacities(page)).every(value=>value===0)).toBe(true);
 await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:false});document.dispatchEvent(new Event('visibilitychange'));});await expect(city).toHaveAttribute('data-animate','true');await advance(page,1200);
 await page.emulateMedia({reducedMotion:'reduce'});await advance(page,1200);before=f.reads();await advance(page,2200);expect(f.reads()-before).toBeGreaterThanOrEqual(1);expect(f.reads()-before).toBeLessThanOrEqual(3);await capture(page,'neon-reduced-motion');
 await page.locator('.navigation-toggle').tap();await page.locator('.main-nav button').nth(2).tap();await expect(page.locator('.ambient-home')).toHaveCount(0);before=f.reads();await advance(page,1100);expect(f.reads()-before).toBeLessThanOrEqual(1);expect(f.actions.filter(action=>action.path!=='/api/preferences'||!('navigationCollapsed' in action.body))).toEqual([]);
});

test('radio building navigation keeps ambient wake and playback controls independent',async({page},info)=>{
 const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro?'ro':'en','night'),saved=JSON.stringify(f.positions);
 await page.route('**/ambient/radio-entry-*.webm',route=>route.abort());
 await advance(page,31000);await expect(page.locator('.app')).toHaveAttribute('data-home-phase','ambient');
 const box=(await button(page).boundingBox())!;await page.touchscreen.tap(box.x+box.width/2,box.y+box.height/2);await expect(page.locator('.app')).toHaveAttribute('data-home-phase','interactive');await expect(page.locator('.radio-city-entry')).toHaveCount(0);
 await page.getByRole('button',{name:ro?'Comenzi rapide':'Quick controls',exact:true}).tap();const quick=page.locator('.quick-controls-dialog');await expect(quick).toBeVisible();const pause=quick.getByRole('button',{name:ro?/^Pauz/:/^Pause$/});await expect(pause).toBeVisible();await expect(pause).toBeEnabled();await quick.getByRole('button',{name:ro?/nchide$/:/^Close$/}).tap();await expect(quick).toHaveCount(0);
 await button(page).tap();await expect(page.locator('.radio-page')).toBeVisible();await expect(page.locator('.radio-city-entry')).toHaveCount(0);
 expect(JSON.stringify(f.state.preferences.homePositions)).toBe(saved);expect(f.actions).toEqual([]);await capture(page,'radio-navigation-preserves-playback');
});

test('radio neon boundary: Off other styles local media hidden card and arrange retain saved visualizer anchor',async({page},info)=>{
 const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro?'ro':'en','night'),saved=JSON.stringify(f.positions);
 await expect(neon(page)).toBeVisible();f.state.preferences.visualizerStyle='bars';await advance(page);await expect(neon(page)).toHaveCount(0);await expect(page.locator('.ambient-home .audio-visualizer[data-signal-style=bars]')).toBeVisible();
 f.state.preferences.visualizerStyle='off';await advance(page);await expect(neon(page)).toHaveCount(0);await expect(page.locator('.ambient-home .audio-visualizer')).toHaveCount(0);
 f.state.preferences.visualizerStyle='wave';f.state.player.kind='audio';f.state.player.title='Fixture track';await advance(page);await expect(neon(page)).toHaveCount(0);await expect(page.locator('.ambient-home .audio-visualizer[data-signal-style=wave]')).toBeVisible();
 f.state.player.kind='radio';f.state.preferences.homeCards=['weather','forecast'];await advance(page);await expect(neon(page)).toBeVisible();await expect(page.locator('.ambient-dock')).toHaveCount(0);await expect(button(page)).toBeVisible();
 f.state.preferences.homeCards=['weather','forecast','playback'];await advance(page);await expect(neon(page)).toBeVisible();
 await page.locator('.navigation-toggle').tap();await page.locator('.main-nav button').nth(3).tap();await openSettingsSection(page,'home');await page.getByRole('button',{name:ro?'Aranjează Acasă':'Arrange Home',exact:true}).tap();await expect(page.locator('.ambient-home')).toHaveAttribute('data-layout-editing','true');await expect(neon(page)).toHaveCount(0);await expect(page.locator('[data-layout-handle=visualizer]')).toBeVisible();await expect(page.locator('.ambient-home .audio-visualizer[data-signal-style=wave]')).toBeVisible();await capture(page,'neon-arrange-legacy-anchor');
 await page.getByRole('button',{name:ro?'Gata':'Done',exact:true}).tap();await expect(page.locator('.ambient-home')).toHaveAttribute('data-layout-editing','false');await expect(neon(page)).toBeVisible();expect(JSON.stringify(f.state.preferences.homePositions)).toBe(saved);expect(f.actions.filter(action=>action.path==='/api/preferences'&&action.body.homePositions)).toHaveLength(1);expect(f.actions.find(action=>action.path==='/api/preferences'&&action.body.homePositions).body.homePositions).toEqual(f.positions);
});



test('radio building target contains facade for every size with rail open, retracted and after idle',async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro')?'ro':'en','night');await expect(neon(page)).toHaveAttribute('data-signal-status','ready');
 const aligned=async()=>{await expect(async()=>{await advance(page,120);const n=(await neon(page).boundingBox())!,b=(await button(page).boundingBox())!;expect(b.x).toBeLessThanOrEqual(n.x+1);expect(b.y).toBeLessThan(n.y);expect(b.x+b.width).toBeGreaterThanOrEqual(n.x+n.width-1);expect(b.y+b.height).toBeGreaterThan(n.y+n.height);await target(button(page));}).toPass({timeout:3000,intervals:[50,100,200]});};
 for(const size of ['compact','balanced','large']){f.state.preferences.visualizerSize=size;await advance(page);for(const rail of ['retracted','open']){
  if(await page.locator('.app').getAttribute('data-navigation')!==rail){await page.locator('.navigation-toggle').tap();await advance(page,400);}
  await expect(page.locator('.app')).toHaveAttribute('data-navigation',rail);await aligned();await capture(page,`entry-alignment-${size}-${rail}`);
 }}
 await page.locator('.navigation-toggle').blur();await advance(page,31000);await aligned();await capture(page,'entry-alignment-ambient');
});

for(const theme of ['ink','night'])test(`radio facade ${theme}: hidden playback card preserves measured colored neon`,async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro')?'ro':'en',theme);
 await expect(neon(page)).toHaveAttribute('data-signal-status','ready');
 f.state.preferences.homeCards=['weather','forecast'];await advance(page);
 await expect(page.locator('.ambient-dock')).toHaveCount(0);
 await expect(neon(page)).toHaveAttribute('data-signal-status','ready');await expect(zones(page)).toHaveCount(8);
 await zones(page).evaluateAll(nodes=>Promise.all(nodes.map(n=>(n as HTMLImageElement).decode())));
 expect((await opacities(page)).some(value=>value>0)).toBe(true);
 await advance(page,31000);await expect(page.locator('.app')).toHaveAttribute('data-home-phase','ambient');
 await expect(neon(page)).toBeVisible();await capture(page,`neon-hidden-card-${theme}`);
 expect(f.state.preferences.homeCards).toEqual(['weather','forecast']);expect(f.actions).toEqual([]);
});
