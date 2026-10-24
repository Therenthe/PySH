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
const button=(page:Page)=>page.locator('.city-radio-control');
const zones=(page:Page)=>neon(page).locator('[data-neon-zone]');
const opacities=(page:Page)=>zones(page).evaluateAll(nodes=>nodes.map(node=>Number((node as HTMLElement).style.opacity)));
async function advance(page:Page,ms=2700){await page.clock.runFor(ms);}
async function capture(page:Page,name:string){await page.screenshot({path:test.info().outputPath(name+'.png')});}
async function target(locator:Locator){const box=await locator.boundingBox();expect(box).not.toBeNull();expect(box!.width).toBeGreaterThanOrEqual(48);expect(box!.height).toBeGreaterThanOrEqual(48);expect(box!.x).toBeGreaterThanOrEqual(0);expect(box!.y).toBeGreaterThanOrEqual(0);expect(box!.x+box!.width).toBeLessThanOrEqual(800);expect(box!.y+box!.height).toBeLessThanOrEqual(480);}

for(const theme of ['ink','night'])for(const day of [false,true])test(`radio neon ${theme} actual-${day?'day':'night'}: eight Blender zones respond to genuine amplitude`,async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro')?'ro':'en',theme,day);
 await expect(neon(page)).toHaveAttribute('data-signal-status','ready');await expect(neon(page)).toHaveAttribute('data-neon-night',String(!day));await expect(zones(page)).toHaveCount(8);
 await zones(page).evaluateAll(nodes=>Promise.all(nodes.map(node=>(node as HTMLImageElement).decode())));
 expect(await zones(page).evaluateAll(nodes=>nodes.every(node=>{const image=node as HTMLImageElement;return image.naturalWidth>0&&image.naturalHeight>0&&image.src.includes('/ambient/');}))).toBe(true);
 const low=await opacities(page);
 // Wait for this changed network sample and its rendered state. A long virtual
 // jump can run the900ms fetch deadline before mocked response-body delivery.
 const fresh=page.waitForResponse(async response=>{if(new URL(response.url()).pathname!=='/api/audio/visualization'||!response.ok())return false;const sample=await response.json().catch(()=>null);return sample?.available===true&&sample?.peak===.9&&sample?.bars?.[0]===.9;});
 f.sample.bars=Array.from({length:16},(_,i)=>i<8?.9:.4);f.sample.rms=.6;f.sample.peak=.9;await advance(page,200);await fresh;
 await expect(neon(page)).toHaveAttribute('data-signal-status','ready');await expect.poll(async()=>Math.max(...await opacities(page))).toBeGreaterThan(day?.18:.8);
 const high=await opacities(page);expect(Math.max(...high)).toBeLessThanOrEqual(day?.22:1);if(!day)expect(Math.max(...high)).toBeGreaterThan(.8);expect(high.some((value,i)=>value>low[i]+.02)).toBe(true);expect(new Set(high.map(value=>value.toFixed(3))).size).toBeGreaterThan(1);
 expect(await zones(page).evaluateAll(nodes=>nodes.every(node=>getComputedStyle(node).animationName==='none'))).toBe(true);
 await expect(page.locator('.ambient-home .audio-visualizer')).toHaveCount(0);await expect(button(page)).toHaveAccessibleName(/Fixture Radio/);await target(button(page));await capture(page,`neon-${theme}-${day?'day':'night'}-measured`);expect(f.actions).toEqual([]);
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

test('radio neon controls: ambient first touch wakes, second expands, collapse returns focus and no transport or preference mutation',async({page},info)=>{
 const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro?'ro':'en','night'),saved=JSON.stringify(f.positions);
 await expect(button(page)).toBeVisible();await advance(page,31000);await expect(page.locator('.app')).toHaveAttribute('data-home-phase','ambient');await expect(page.locator('.ambient-dock')).toBeHidden();await capture(page,'neon-ambient');
 const b=(await button(page).boundingBox())!;await page.touchscreen.tap(b.x+b.width/2,b.y+b.height/2);await expect(page.locator('.app')).toHaveAttribute('data-home-phase','interactive');await expect(button(page)).toHaveAttribute('aria-expanded','false');expect(f.actions).toEqual([]);
 await button(page).tap();await expect(button(page)).toHaveAttribute('aria-expanded','true');await expect(page.locator('.playback-toggle')).toBeVisible();await capture(page,'neon-expanded-transport');
 await page.locator('.playback-expand').focus();await page.keyboard.press('Enter');await expect(button(page)).toHaveAttribute('aria-expanded','false');await expect(button(page)).toBeFocused();await page.keyboard.press('Enter');await expect(button(page)).toHaveAttribute('aria-expanded','true');await page.keyboard.press('Space');await expect(button(page)).toHaveAttribute('aria-expanded','false');
 expect(JSON.stringify(f.state.preferences.homePositions)).toBe(saved);expect(f.actions).toEqual([]);
});

test('radio neon boundary: Off other styles local media hidden card and arrange retain saved visualizer anchor',async({page},info)=>{
 const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro?'ro':'en','night'),saved=JSON.stringify(f.positions);
 await expect(neon(page)).toBeVisible();f.state.preferences.visualizerStyle='bars';await advance(page);await expect(neon(page)).toHaveCount(0);await expect(page.locator('.ambient-home .audio-visualizer[data-signal-style=bars]')).toBeVisible();
 f.state.preferences.visualizerStyle='off';await advance(page);await expect(neon(page)).toHaveCount(0);await expect(page.locator('.ambient-home .audio-visualizer')).toHaveCount(0);
 f.state.preferences.visualizerStyle='wave';f.state.player.kind='audio';f.state.player.title='Fixture track';await advance(page);await expect(neon(page)).toHaveCount(0);await expect(page.locator('.ambient-home .audio-visualizer[data-signal-style=wave]')).toBeVisible();
 f.state.player.kind='radio';f.state.preferences.homeCards=['weather','forecast'];await advance(page);await expect(neon(page)).toHaveCount(0);await expect(button(page)).toHaveCount(0);
 f.state.preferences.homeCards=['weather','forecast','playback'];await advance(page);await expect(neon(page)).toBeVisible();
 await page.locator('.navigation-toggle').tap();await page.locator('.main-nav button').nth(3).tap();await openSettingsSection(page,'home');await page.getByRole('button',{name:ro?'Aranjează Acasă':'Arrange Home',exact:true}).tap();await expect(page.locator('.ambient-home')).toHaveAttribute('data-layout-editing','true');await expect(neon(page)).toHaveCount(0);await expect(page.locator('[data-layout-handle=visualizer]')).toBeVisible();await expect(page.locator('.ambient-home .audio-visualizer[data-signal-style=wave]')).toBeVisible();await capture(page,'neon-arrange-legacy-anchor');
 await page.getByRole('button',{name:ro?'Gata':'Done',exact:true}).tap();await expect(page.locator('.ambient-home')).toHaveAttribute('data-layout-editing','false');await expect(neon(page)).toBeVisible();expect(JSON.stringify(f.state.preferences.homePositions)).toBe(saved);expect(f.actions.filter(action=>action.path==='/api/preferences'&&action.body.homePositions)).toHaveLength(1);expect(f.actions.find(action=>action.path==='/api/preferences'&&action.body.homePositions).body.homePositions).toEqual(f.positions);
});



test('radio neon control follows Blender crop for every size with rail open, retracted and after idle',async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro')?'ro':'en','night');await expect(neon(page)).toHaveAttribute('data-signal-status','ready');
 for(const size of ['compact','balanced','large']){
  f.state.preferences.visualizerSize=size;await advance(page);
  for(const rail of ['retracted','open']){
   if(await page.locator('.app').getAttribute('data-navigation')!==rail){await page.locator('.navigation-toggle').tap();await advance(page,400);}
   await expect(page.locator('.app')).toHaveAttribute('data-navigation',rail);
   const aligned=async()=>{const n=(await neon(page).boundingBox())!,b=(await button(page).boundingBox())!;return Math.max(Math.abs(n.x-b.x),Math.abs(n.y-b.y),Math.abs(n.width-b.width),Math.abs(n.height-b.height));};
   await expect.poll(aligned).toBeLessThan(1);await target(button(page));
   await advance(page,31000);await expect(page.locator('.app')).toHaveAttribute('data-home-phase','ambient');await test.info().attach('alignment-'+size+'-'+rail,{body:JSON.stringify({neon:await neon(page).boundingBox(),control:await button(page).boundingBox(),styles:await button(page).evaluate(el=>{const s=getComputedStyle(el);return {left:s.left,bottom:s.bottom,padding:s.padding,margin:s.margin,transform:s.transform};})}),contentType:'application/json'});await expect.poll(aligned).toBeLessThan(1);
   const b=(await button(page).boundingBox())!;await page.touchscreen.tap(b.x+b.width-5,b.y+5);await expect(page.locator('.app')).toHaveAttribute('data-home-phase','interactive');await expect(button(page)).toHaveAttribute('aria-expanded','false');await expect.poll(aligned).toBeLessThan(1);
   await page.touchscreen.tap(b.x+b.width-5,b.y+5);await expect(button(page)).toHaveAttribute('aria-expanded','true');await page.locator('.playback-expand').tap();await expect(button(page)).toHaveAttribute('aria-expanded','false');
   await capture(page,`neon-alignment-${size}-${rail}`);
  }
 }
});
