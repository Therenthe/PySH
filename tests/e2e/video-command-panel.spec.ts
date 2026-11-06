import {expect,test,type Locator,type Page,type TestInfo} from '@playwright/test';

// This media clock is a control/lifecycle double, not decoder or DRM evidence.
// API calls and pointer/keyboard inputs below exercise the production app.
type Kind='tv'|'local';
type Call={path:string;method:string;body:any};
async function mediaClock(page:Page){
 await page.route('**/node_modules/.vite/deps/hls__js.js*',route=>route.fulfill({contentType:'application/javascript',body:`export default class Hls {static Events={ERROR:'error',MANIFEST_PARSED:'manifest'};static isSupported(){return true;}events={};on(name,fn){this.events[name]=fn;}loadSource(){}attachMedia(){queueMicrotask(()=>this.events.manifest?.());}destroy(){}}`}));
 await page.addInitScript(()=>{
  const proto=HTMLMediaElement.prototype,owned=(v:HTMLMediaElement)=>!!v.closest('.iptv-live,.video-overlay'),states=new WeakMap<HTMLMediaElement,{paused:boolean;at:number;position:number}>();
  const counters={play:0,pause:0,seek:0};(window as any).videoCommandMedia=counters;
  const state=(v:HTMLMediaElement)=>{let s=states.get(v);if(!s){s={paused:true,at:performance.now(),position:0};states.set(v,s);}return s;};
  const position=(v:HTMLMediaElement)=>{const s=state(v);return s.position+(s.paused?0:(performance.now()-s.at)/1000);};
  for(const name of ['paused','currentTime','duration','readyState','ended'] as const){
   const native=Object.getOwnPropertyDescriptor(proto,name)!;
   Object.defineProperty(proto,name,{configurable:true,get(){if(!owned(this))return native.get!.call(this);return name==='paused'?state(this).paused:name==='currentTime'?position(this):name==='duration'?180:name==='readyState'?4:false;},...(name==='currentTime'?{set(value:number){if(!owned(this))return native.set!.call(this,value);counters.seek++;const s=state(this);s.position=value;s.at=performance.now();}}:{})});
  }
  const width=Object.getOwnPropertyDescriptor(HTMLVideoElement.prototype,'videoWidth')!;Object.defineProperty(HTMLVideoElement.prototype,'videoWidth',{configurable:true,get(){return owned(this)?1280:width.get!.call(this);}});
  const play=proto.play,pause=proto.pause;
  proto.play=function(){if(!owned(this))return play.call(this);const s=state(this);if(!s.paused)return Promise.resolve();s.paused=false;s.at=performance.now();counters.play++;this.dispatchEvent(new Event('play'));this.dispatchEvent(new Event('playing'));return Promise.resolve();};
  proto.pause=function(){if(!owned(this))return pause.call(this);const s=state(this);if(s.paused)return;s.position=position(this);s.paused=true;counters.pause++;this.dispatchEvent(new Event('pause'));};
 });
}
const clone=<T,>(v:T):T=>JSON.parse(JSON.stringify(v));
async function fixture(page:Page,ro:boolean,theme:string){
 await mediaClock(page);
 const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,navigationCollapsed:false,navigationAutoHide:false,timezone:'Europe/Bucharest',volume:40,screenBrightness:25,homeCards:[],shortcuts:[],visualizerStyle:'off'},network:{available:true,state:'connected'},bluetooth:{available:true,powered:true,devices:[],prompts:[]},audio:{available:true,ready:true,volume:40,mute:false,outputs:[{id:'speaker',description:'Fixture speaker',active:true}],output:'speaker'},player:{kind:'radio',state:'idle',url:''},weather:{},power:{standby:false,brightness:{available:true,value:25},timer:{},daily:{enabled:false,time:'23:00'}}};
 const calls:Call[]=[],saved={volume:40,brightness:25},control={holdClose:false,failClose:false};let closeRelease=()=>{},streamRelease=()=>{},sessionNumber=0;
 const streamGate=new Promise<void>(r=>streamRelease=r),identity='m1_'+'b'.repeat(64);
 await page.route('**/api/**',async route=>{
  const req=route.request(),path=new URL(req.url()).pathname,method=req.method(),body=req.postData()?req.postDataJSON():undefined;let json:any={ok:true};
  if(method!=='GET')calls.push({path,method,body});
  if(path==='/api/session')json={token:'video-command-fixture'};
  else if(path==='/api/state')json=clone(state);
  else if(path==='/api/audio'){
   if(body.volume!==undefined){state.audio.volume=body.volume;if(body.persist!==false)saved.volume=state.preferences.volume=body.volume;}
   if(body.mute!==undefined)state.audio.mute=body.mute;json=clone(state.audio);
  }
  else if(path==='/api/power/brightness'){state.power.brightness.value=body.value;if(body.persist!==false)saved.brightness=state.preferences.screenBrightness=body.value;json=clone(state.power);}
  else if(path==='/api/preferences'){Object.assign(state.preferences,body);json=state.preferences;}
  else if(path==='/api/player'){state.player={kind:'radio',state:'idle',url:''};json=state.player;}
  else if(path==='/api/media')json={path:'/approved',items:[{path:'/approved/fixture.webm',name:'fixture.webm',kind:'video',media_identity:identity}],parent:null};
  else if(path==='/api/media/continue')json={items:[]};
  else if(path==='/api/media/inspect')json={state:'unavailable'};
  else if(path==='/api/media/video-session'){const sid='L'+String(++sessionNumber).padStart(31,'0');state.player={kind:'radio',state:'idle',url:''};json={session_id:sid,stream_url:'/api/media/file?session_id='+sid,media_identity:identity,resume_position_s:0};}
  else if(path==='/api/media/file'){await streamGate;return route.fulfill({status:204,body:''}).catch(()=>{});}
  else if(path.startsWith('/api/media/video-session/'))json={closed:method==='DELETE',updated:true};
  else if(path==='/api/iptv')json={channels:[{id:'fixture_tv',name:'Fixture TV',favorite:true}],sources:{playlists:[],xmltv:[]}};
  else if(path==='/api/iptv/recordings')json={items:[],service:{active:true}};
  else if(path.startsWith('/api/iptv/guide/'))json={programmes:[]};
  else if(path==='/api/iptv/view')json={session_id:'tv_'+(++sessionNumber),stream_url:'/api/iptv/stream/session/root'};
  else if(path.startsWith('/api/iptv/view/'))json={closed:method==='DELETE',active:true};
  else if(path==='/api/network/scan')json={networks:[]};
  if(method==='DELETE'&&(path.startsWith('/api/iptv/view/')||path.startsWith('/api/media/video-session/'))){
   if(control.holdClose){control.holdClose=false;await new Promise<void>(r=>closeRelease=r);}
   if(control.failClose){control.failClose=false;return route.fulfill({status:503,json:{error:'operation_failed'}});}
  }
  await route.fulfill({json}).catch(()=>{});
 });
 await page.goto('/');await expect(page.locator('.topbar')).toBeVisible();
 const open=async(kind:Kind)=>{
  await page.locator('.main-nav button').nth(2).tap();
  if(kind==='local'){
   await page.locator('.media-item').filter({hasText:'fixture.webm'}).tap();await expect(page.locator('.video-overlay')).toBeVisible();
   await page.locator('.video-overlay video').evaluate(v=>{v.dispatchEvent(new Event('loadedmetadata'));v.dispatchEvent(new Event('canplay'));});
  }else{
   if(!await page.locator('.iptv-page').count()){await page.locator('.media-sections button').nth(1).tap();await page.locator('.service-iptv').tap();}
   await page.getByRole('button',{name:ro?'Privește live':'Watch live',exact:true}).tap();await expect(page.locator('.iptv-live')).toBeVisible();
  }
  const video=page.locator(kind==='tv'?'.iptv-live':'.video-overlay');await expect(video.locator('video')).toHaveJSProperty('paused',false);return video;
 };
 return{state,calls,saved,control,open,closeCalls:()=>calls.filter(c=>c.method==='DELETE'&&(c.path.startsWith('/api/iptv/view/')||c.path.startsWith('/api/media/video-session/'))),releaseClose:()=>closeRelease(),cleanup:()=>{closeRelease();streamRelease();}};
}
const quick=(page:Page,ro:boolean)=>page.getByRole('dialog',{name:ro?'Comenzi rapide':'Quick controls',exact:true});
const command=(video:Locator,ro:boolean)=>video.getByRole('button',{name:ro?'Comenzi rapide':'Quick controls',exact:true});
const screenshot=(page:Page,info:TestInfo,name:string)=>page.screenshot({path:info.outputPath(name+'.png')});
const counters=(page:Page)=>page.evaluate(()=>(window as any).videoCommandMedia as {play:number;pause:number;seek:number});
async function pull(page:Page,handle:Locator){
 await page.mouse.move(400,5);await page.mouse.down();
 // Another primary pointer/cancel cannot replace the existing captured owner.
 await handle.dispatchEvent('pointerdown',{pointerId:9,pointerType:'touch',isPrimary:true,button:0,clientX:400,clientY:5});
 await handle.dispatchEvent('pointercancel',{pointerId:9,pointerType:'touch',isPrimary:true});
 // Continue through the newly appeared Radio shortcut; release must not click it.
 await page.mouse.move(402,98,{steps:16});await page.mouse.up();
}
async function inFront(dialog:Locator){expect(await dialog.evaluate(e=>{const r=e.getBoundingClientRect();return e.contains(document.elementFromPoint(r.x+r.width/2,r.y+Math.min(30,r.height/2)));})).toBe(true);}
async function adjust(page:Page,slider:Locator,fraction:number){const box=(await slider.boundingBox())!;await page.mouse.move(box.x+box.width*fraction,box.y+box.height/2);await page.mouse.down();return Math.round(Number(await slider.getAttribute('min'))+(100-Number(await slider.getAttribute('min')))*fraction);}

for(const theme of ['ink','night'])for(const kind of ['tv','local'] as const){
 if(kind==='tv')test(`Video commands tv ${theme}: long drawer dismissal restores a visible keyboard owner`,async({page},info)=>{
  await page.clock.install();const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme);
  try{
   const video=await f.open(kind),before=await counters(page);await command(video,ro).tap();const d=quick(page,ro);await expect(d).toBeVisible();
   // A user can read or adjust the drawer longer than the TV HUD's 4.5s timeout.
   await page.clock.runFor(6000);await expect(video.locator('video')).toHaveJSProperty('paused',false);
   await page.keyboard.press('Escape');await expect(d).toHaveCount(0);const button=command(video,ro);await expect(button).toBeFocused();await expect(button).toBeVisible();
   expect(await button.evaluate(e=>!e.closest('[inert]'))).toBe(true);expect(await counters(page)).toEqual(before);expect(f.closeCalls()).toHaveLength(0);await screenshot(page,info,'08-long-drawer-focus-restored');
   // The restored owner is usable without first revealing the concealed HUD.
   await page.keyboard.press('Enter');await expect(d).toBeVisible();await page.keyboard.press('Escape');await expect(button).toBeFocused();
  }finally{f.cleanup();}
 });
 test(`Video commands ${kind} ${theme}: edge ownership, live sliders and one Escape preserve playback`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme);
  try{
   const video=await f.open(kind),before=await counters(page),initialClose=f.closeCalls().length,handle=video.locator('.hub-command-pull[data-video=true]');await expect(handle).toBeVisible();
   // Tap, horizontal escape, cancellation and another pointer cannot open it.
   await page.touchscreen.tap(400,5);await expect(quick(page,ro)).toHaveCount(0);
   await page.mouse.move(400,5);await page.mouse.down();await page.mouse.move(450,48);await page.mouse.up();await expect(quick(page,ro)).toHaveCount(0);
   await page.mouse.move(400,5);await page.mouse.down();await handle.dispatchEvent('pointermove',{pointerId:9,pointerType:'touch',clientX:400,clientY:80});await expect(quick(page,ro)).toHaveCount(0);await handle.dispatchEvent('pointercancel',{pointerId:1,pointerType:'mouse'});await page.mouse.up();await expect(quick(page,ro)).toHaveCount(0);
   await pull(page,handle);const d=quick(page,ro);await expect(d).toBeVisible();await inFront(d);await expect(d.locator('.command-context')).toContainText(kind==='tv'?'Fixture TV':'fixture.webm');await expect(d).not.toContainText(ro?'Nimic în redare':'Nothing playing');
   await expect(video.locator('video')).toHaveJSProperty('paused',false);expect(await counters(page)).toEqual(before);expect(f.closeCalls()).toHaveLength(initialClose);await screenshot(page,info,'01-video-shared-drawer');
   for(let i=0;i<15;i++){await page.keyboard.press('Tab');expect(await d.evaluate(e=>e.contains(document.activeElement))).toBe(true);}
   await page.keyboard.press('Escape');await expect(d).toHaveCount(0);await expect(video).toBeVisible();await expect(command(video,ro)).toBeFocused();await expect(video.locator('video')).toHaveJSProperty('paused',false);
   const button=command(video,ro),b=(await button.boundingBox())!;expect(b.width).toBeGreaterThanOrEqual(48);expect(b.height).toBeGreaterThanOrEqual(48);await button.tap();await expect(d).toBeVisible();
   const volume=d.getByRole('slider',{name:ro?'Volum':'Volume',exact:true}),level=await adjust(page,volume,.62);
   try{await expect(volume.locator('..').locator('.audio-volume-value')).toHaveText(level+'%');await expect.poll(()=>f.calls.some(c=>c.path==='/api/audio'&&c.body.volume===level&&c.body.persist===false)).toBe(true);expect(f.saved.volume).toBe(40);}finally{await page.mouse.up();}
   await expect.poll(()=>f.saved.volume).toBe(level);await expect(d).toHaveAttribute('aria-busy','false');
   const brightness=d.getByRole('slider',{name:ro?'Luminozitate ecran':'Screen brightness',exact:true}),light=await adjust(page,brightness,.46);
   try{await expect(brightness.locator('..').locator('.audio-volume-value')).toHaveText(light+'%');await expect.poll(()=>f.calls.some(c=>c.path==='/api/power/brightness'&&c.body.value===light&&c.body.persist===false)).toBe(true);expect(f.saved.brightness).toBe(25);}finally{await page.mouse.up();}
   await expect.poll(()=>f.saved.brightness).toBe(light);await expect(d).toHaveAttribute('aria-busy','false');await screenshot(page,info,'02-video-live-device-controls');
   await d.getByRole('button',{name:ro?'Ieșire audio':'Audio output',exact:true}).tap();await expect(d.locator('.command-output-list')).toBeVisible();await d.getByRole('button',{name:ro?'Înapoi':'Back',exact:true}).tap();
   await d.locator('.command-header-actions').getByRole('button',{name:ro?'Închide':'Close',exact:true}).tap();await expect(d).toHaveCount(0);await expect(command(video,ro)).toBeFocused();expect(await counters(page)).toEqual(before);expect(f.closeCalls()).toHaveLength(initialClose);await screenshot(page,info,'03-video-playback-retained');
  }finally{f.cleanup();}
 });

 test(`Video commands ${kind} ${theme}: all destinations wait for confirmed owner close`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme);
  try{
   for(const [label,index]of [[ro?'Acasă':'Home',0],['Radio',1],['Media',2],[ro?'Toate setările':'All settings',3]] as const){
    const video=await f.open(kind),before=f.closeCalls().length;f.control.holdClose=true;await command(video,ro).tap();await quick(page,ro).getByRole('button',{name:label,exact:true}).tap();
    await expect.poll(()=>f.closeCalls().length).toBe(before+1);await expect(video).toBeVisible();await expect(page.locator('.main-nav button').nth(2)).toHaveClass(/active/);await screenshot(page,info,'04-navigation-close-held-'+index);
    f.releaseClose();await expect(video).toHaveCount(0);await expect(page.locator('.main-nav button').nth(index)).toHaveClass(/active/);expect(f.closeCalls()).toHaveLength(before+1);
   }
  }finally{f.cleanup();}
 });

 test(`Video commands ${kind} ${theme}: failed navigation close retains owner and needs explicit retry`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme);
  try{
   const video=await f.open(kind);f.control.failClose=true;await command(video,ro).tap();await quick(page,ro).getByRole('button',{name:ro?'Acasă':'Home',exact:true}).tap();
   await expect.poll(()=>f.closeCalls().length).toBe(1);await expect(video).toBeVisible();await expect(quick(page,ro)).toHaveCount(0);await expect(page.locator('.main-nav button').nth(2)).toHaveClass(/active/);await expect(video.locator('[role=alert]')).toBeVisible();await screenshot(page,info,'05-close-not-confirmed-retains-video');
   const recover=video.getByRole('button',{name:kind==='tv'?(ro?'Înapoi la TV':'Back to TV'):(ro?'Salvează și închide':'Save and close'),exact:true});await recover.tap();await expect(video).toHaveCount(0);expect(f.closeCalls()).toHaveLength(2);
   // Failed navigation is not replayed behind the user's back after recovery.
   await expect(page.locator('.main-nav button').nth(2)).toHaveClass(/active/);await page.locator('.main-nav button').first().tap();await expect(page.locator('.main-nav button').first()).toHaveClass(/active/);await screenshot(page,info,'06-explicit-navigation-retry');
  }finally{f.cleanup();}
 });

 test(`Video commands ${kind} ${theme}: auxiliary controls stay above the player without transport changes`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme);
  try{
   const video=await f.open(kind),before=await counters(page);
   for(const [action,title]of [['network',ro?'Rețea':'Network'],['bluetooth','Bluetooth'],['standby',ro?'Luminozitate și standby':'Brightness & standby']] as const){
    await command(video,ro).tap();const d=quick(page,ro);if(action==='standby')await d.getByRole('button',{name:'Standby',exact:true}).tap();else await d.locator(`[data-command=${action}]`).tap();
    const dialog=page.getByRole('dialog',{name:title,exact:true});await expect(dialog).toBeVisible();await inFront(dialog);expect(await dialog.evaluate(e=>e.contains(document.activeElement))).toBe(true);await screenshot(page,info,'07-auxiliary-above-'+action);
    await page.keyboard.press('Escape');await expect(dialog).toHaveCount(0);await expect(video).toBeVisible();await expect(video.locator('video')).toHaveJSProperty('paused',false);expect(await counters(page)).toEqual(before);expect(f.closeCalls()).toHaveLength(0);
   }
   expect(f.calls.some(c=>c.path==='/api/power')).toBe(false);await page.keyboard.press('Alt+Shift+P');await expect(quick(page,ro)).toBeVisible();await page.keyboard.press('Escape');await expect(video).toBeVisible();
  }finally{f.cleanup();}
 });
}
