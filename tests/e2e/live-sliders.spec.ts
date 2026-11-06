import {expect,test,type Locator,type Page,type TestInfo} from '@playwright/test';
import {openSettingsSection} from './settings-navigation';

// Charter: user-visible draft AND device API preview must change before release.
// A delayed device, stale poll, cancellation or another surface must not lose the
// latest intent or persist every pointer move. Hardware/audio is mocked here;
// these checks do not certify an acoustic change or the physical backlight.
type Kind='volume'|'brightness';
type Write={kind:Kind;body:{volume?:number;value?:number;persist?:boolean}};
const clone=<T,>(value:T):T=>JSON.parse(JSON.stringify(value));
async function fixture(page:Page,ro:boolean,theme:string){
 const station={uuid:'11111111-1111-4111-8111-111111111111',name:'Fixture Radio',url:'https://example.org/radio'};
 const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,navigationCollapsed:false,navigationAutoHide:false,timezone:'Europe/Bucharest',screenBrightness:80,lastStation:station,favorites:[station]},network:{available:true,state:'connected'},bluetooth:{available:true,devices:[],prompts:[]},audio:{available:true,ready:true,volume:40,mute:false,output:'fixture',outputs:[{id:'fixture',description:'Fixture speaker',active:true}]},player:{kind:'radio',state:'playing',station_name:station.name,title:'Fixture song',url:station.url},weather:{},power:{standby:false,brightness:{available:true,value:80},timer:{remainingSeconds:0},daily:{enabled:false,time:'23:00'}}};
 const writes:Write[]=[],legacyBrightness:any[]=[],saved={volume:40,brightness:80},active={volume:0,brightness:0},maxActive={volume:0,brightness:0};
 const control={holdNext:{volume:false,brightness:false},loseNext:{volume:false,brightness:false},holdState:false,holdAllStates:false,failStateReads:false,stateFailures:0,stateHeld:0,staleAudio:0,staleBrightness:0,audioReply:'normal' as 'normal'|'mismatch'|'unready'|'unavailable'};
 state.preferences.volume=40;
 const releaseWrite:Partial<Record<Kind,()=>void>>={},stateReleases:(()=>void)[]=[];let releaseState=()=>{};
 const apply=async(kind:Kind,body:Write['body'])=>{
  writes.push({kind,body});active[kind]++;maxActive[kind]=Math.max(maxActive[kind],active[kind]);
  try{
   if(control.holdNext[kind]){control.holdNext[kind]=false;await new Promise<void>(resolve=>releaseWrite[kind]=resolve);}
   const value=kind==='volume'?body.volume!:body.value!;
   if(kind==='volume')state.audio.volume=value;else state.power.brightness.value=value;
   if(body.persist!==false){saved[kind]=value;if(kind==='brightness')state.preferences.screenBrightness=value;else state.preferences.volume=value;}
   return clone(kind==='volume'?state.audio:state.power);
  }finally{active[kind]--;}
 };
 const identity='m1_'+'a'.repeat(64),session='S'.repeat(32);
 await page.route('**/api/**',async route=>{
  const request=route.request(),path=new URL(request.url()).pathname,method=request.method(),body=request.postData()?request.postDataJSON():{};let json:any={ok:true};
  if(path==='/api/session')json={token:'live-slider-fixture'};
  else if(path==='/api/state'){
   json=clone(state);
   if(control.failStateReads){control.stateFailures++;return route.fulfill({status:503,json:{error:'backend_unavailable'}});}
   if(control.holdAllStates){control.stateHeld++;await new Promise<void>(resolve=>stateReleases.push(resolve));}
   else if(control.holdState){control.holdState=false;control.stateHeld++;control.staleAudio=json.audio.volume;control.staleBrightness=json.power.brightness.value;await new Promise<void>(resolve=>releaseState=resolve);}
  }
  else if(path==='/api/audio'&&method==='POST'){
   if(typeof body.volume==='number'){
    json=await apply('volume',body);
    if(control.audioReply==='mismatch')json.volume=state.audio.volume=Math.max(0,body.volume-1);
    if(control.audioReply==='unready')json.ready=state.audio.ready=false;
    if(control.audioReply==='unavailable'){json.available=state.audio.available=false;json.ready=state.audio.ready=false;}
    if(control.loseNext.volume){control.loseNext.volume=false;return route.abort('failed');}
   }else{Object.assign(state.audio,body);json=state.audio;}
  }
  else if(path==='/api/power/brightness'&&method==='POST'){json=await apply('brightness',body);if(control.loseNext.brightness){control.loseNext.brightness=false;return route.abort('failed');}}
  else if(path==='/api/preferences'&&method==='PATCH'){
   if('screenBrightness'in body)legacyBrightness.push(body);Object.assign(state.preferences,body);json=state.preferences;
  }
  else if(path==='/api/radio')json={stations:[station]};
  else if(path==='/api/player'){state.player={state:'idle'};json=state.player;}
  else if(path==='/api/media')json={path:'/approved',parent:null,items:[{path:'/approved/fixture.webm',name:'fixture.webm',kind:'video',media_identity:identity}]};
  else if(path==='/api/media/continue')json={items:[]};
  else if(path==='/api/media/inspect')json={state:'unavailable'};
  else if(path==='/api/media/video-session')json={session_id:session,stream_url:'/api/media/file?session_id='+session,media_identity:identity,resume_position_s:0};
  else if(path.startsWith('/api/media/video-session/'))json={closed:method==='DELETE',updated:true};
  else if(path==='/api/media/file')return route.fulfill({status:503,json:{error:'fixture_no_decoder_claim'}});
  else if(path==='/api/iptv')json={channels:[{id:'tv_one',name:'Fixture TV',favorite:true}],sources:{playlists:[],xmltv:[]}};
  else if(path==='/api/iptv/recordings')json={items:[],service:{active:true}};
  else if(path.startsWith('/api/iptv/guide/'))json={programmes:[]};
  else if(path==='/api/iptv/view')json={session_id:'viewer_one',stream_url:'/api/iptv/stream/viewer_one/root'};
  else if(path.startsWith('/api/iptv/view/'))json={closed:method==='DELETE',active:true};
  else if(path.startsWith('/api/iptv/stream/'))return route.fulfill({status:503,json:{error:'iptv_stream_unavailable'}});
  await route.fulfill({json}).catch(()=>{});
 });
 await page.goto('/');await expect(page.locator('.topbar')).toBeVisible();
 return{state,writes,saved,maxActive,control,legacyBrightness,release:(kind:Kind)=>releaseWrite[kind]?.(),releaseState:()=>releaseState(),releaseAllStates:()=>{control.holdAllStates=false;control.failStateReads=false;for(const release of stateReleases.splice(0))release();},value:(kind:Kind)=>kind==='volume'?state.audio.volume:state.power.brightness.value};
}
const number=(slider:Locator)=>slider.locator('..').locator('.audio-volume-value');
async function quick(page:Page,ro:boolean,kind:Kind){
 await page.locator('.quick-controls-button').tap();const dialog=page.getByRole('dialog',{name:ro?'Comenzi rapide':'Quick controls',exact:true});
 await dialog.evaluate(async e=>{await Promise.all(e.getAnimations().map(a=>a.finished.catch(()=>{})));});
 const slider=dialog.getByRole('slider',{name:kind==='volume'?(ro?'Volum':'Volume'):(ro?'Luminozitate ecran':'Screen brightness'),exact:true});await expect(slider).toBeEnabled();return slider;
}
async function point(page:Page,slider:Locator,fraction:number,down=false){
 const rect=(await slider.boundingBox())!;await page.mouse.move(rect.x+rect.width*fraction,rect.y+rect.height/2);if(down)await page.mouse.down();
 return Math.round(Number(await slider.getAttribute('min'))+(100-Number(await slider.getAttribute('min')))*fraction);
}
const snap=(page:Page,info:TestInfo,name:string)=>page.screenshot({path:info.outputPath(name+'.png')});

for(const theme of ['ink','night'])for(const kind of ['volume','brightness'] as const){
 test(`Live slider ${kind} previews numeric and API before release, then persists same value ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme),slider=await quick(page,ro,kind);
  const target=await point(page,slider,.73,true);
  try{
   await expect(slider).toHaveValue(String(target));await expect(number(slider)).toHaveText(target+'%');
   await expect.poll(()=>f.writes.filter(w=>w.kind===kind&&w.body.persist===false).length).toBeGreaterThan(0);
   await expect.poll(()=>f.value(kind)).toBe(target);expect(f.saved[kind]).toBe(kind==='volume'?40:80);
   await expect(slider).toBeEnabled();await snap(page,info,'01-live-preview-before-release');
  }finally{await page.mouse.up();}
  await expect.poll(()=>f.writes.filter(w=>w.kind===kind&&w.body.persist===true).length).toBe(1);
  await expect.poll(()=>f.saved[kind]).toBe(target);expect(f.maxActive[kind]).toBe(1);expect(f.legacyBrightness).toEqual([]);await snap(page,info,'02-final-persisted');
 });

 test(`Live slider ${kind} serializes delayed writes, coalesces latest and survives stale polls ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme),slider=await quick(page,ro,kind);
  f.control.holdState=true;await expect.poll(()=>f.control.stateHeld,{timeout:6000}).toBe(1);f.control.holdNext[kind]=true;
  await point(page,slider,.2,true);
  try{
   await expect.poll(()=>f.writes.filter(w=>w.kind===kind).length).toBe(1);await expect(slider).toBeEnabled();
   let target=0;for(const fraction of [.38,.46,.6,.82,.9])target=await point(page,slider,fraction);
   await expect(number(slider)).toHaveText(target+'%');f.releaseState();await expect(number(slider)).toHaveText(target+'%');
   await snap(page,info,'03-delayed-owner-with-latest-draft');await page.mouse.up();
   expect(f.writes.filter(w=>w.kind===kind)).toHaveLength(1);f.release(kind);
   await expect.poll(()=>f.saved[kind]).toBe(target);await expect.poll(()=>f.value(kind)).toBe(target);
   await expect(slider).toHaveValue(String(target));expect(f.maxActive[kind]).toBe(1);
   const writes=f.writes.filter(w=>w.kind===kind);expect(writes.at(-1)?.body.persist).toBe(true);expect(writes.length).toBeLessThanOrEqual(3);
   await snap(page,info,'04-latest-value-settled');
  }finally{f.releaseState();f.release(kind);await page.mouse.up();}
 });

 test(`Live slider ${kind} flushes cancellation and blur, supports keyboard persistence ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme),slider=await quick(page,ro,kind);
  let target=await point(page,slider,.62,true);
  try{
   await expect.poll(()=>f.value(kind)).toBe(target);
   await slider.dispatchEvent('pointercancel',{pointerId:1,pointerType:'mouse',button:0});
  }finally{await page.mouse.up();}
  await expect.poll(()=>f.saved[kind]).toBe(target);
  target=await point(page,slider,.37,true);
  try{await expect.poll(()=>f.value(kind)).toBe(target);await page.evaluate(()=>window.dispatchEvent(new Event('blur')));}finally{await page.mouse.up();}
  await expect.poll(()=>f.saved[kind]).toBe(target);await slider.focus();await page.keyboard.press('ArrowRight');
  await expect.poll(()=>f.saved[kind]).toBe(target+1);await expect(number(slider)).toHaveText(target+1+'%');
  expect(f.writes.filter(w=>w.kind===kind).at(-1)?.body.persist).toBe(true);await snap(page,info,'05-keyboard-after-cancel-blur');
  target=await point(page,slider,.84,true);
  try{await expect.poll(()=>f.value(kind)).toBe(target);await expect(page.locator('.quick-controls-dialog')).toHaveAttribute('aria-busy','false');await page.keyboard.press('Escape');}finally{await page.mouse.up();}
  await expect(page.locator('.quick-controls-dialog')).toHaveCount(0);await expect.poll(()=>f.saved[kind]).toBe(target);
  const reopened=await quick(page,ro,kind);await expect(reopened).toHaveValue(String(target));await expect(number(reopened)).toHaveText(target+'%');
 });
}

for(const theme of ['ink','night'])test(`Live sliders share behavior across Radio, audio, settings, power, TV and local video ${theme}`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme);let target=55,step=0;
 const preview=async(slider:Locator,label:string)=>{
  const before=f.writes.length;target=await point(page,slider,.3+.07*step++,true);
  try{await expect(number(slider)).toHaveText(target+'%');await expect.poll(()=>f.writes.slice(before).some(w=>w.body.persist===false)).toBe(true);await snap(page,info,label);}finally{await page.mouse.up();}
  await expect.poll(()=>f.writes.slice(before).some(w=>w.body.persist===true)).toBe(true);
 };
 await page.locator('.main-nav button').nth(1).tap();await preview(page.locator('.radio-page').getByRole('slider',{name:ro?'Volum':'Volume',exact:true}),'06-radio');
 await page.locator('.rail-bottom .status-button').last().tap();const audio=page.getByRole('dialog',{name:ro?'Audio':'Audio',exact:true});await preview(audio.getByRole('slider',{name:ro?'Volum':'Volume',exact:true}),'07-audio-dialog');await page.keyboard.press('Escape');
 await page.locator('.main-nav button').nth(3).tap();await openSettingsSection(page,'audio');await preview(page.locator('.settings-panel').getByRole('slider',{name:ro?'Volum':'Volume',exact:true}),'08-audio-settings');
 await openSettingsSection(page,'power');await preview(page.locator('.settings-panel').getByRole('slider',{name:ro?'Luminozitate ecran':'Screen brightness',exact:true}),'09-power-settings');
 await page.locator('.power-button').tap();await preview(page.getByRole('dialog',{name:ro?'Luminozitate și standby':'Brightness & standby'}).getByRole('slider',{name:ro?'Luminozitate ecran':'Screen brightness',exact:true}),'10-power-dialog');await page.keyboard.press('Escape');
 await page.locator('.main-nav button').nth(2).tap();await page.locator('.media-item').filter({hasText:'fixture.webm'}).tap();await preview(page.locator('.video-overlay').getByRole('slider',{name:ro?'Volum':'Volume',exact:true}),'11-local-video');await page.getByRole('button',{name:ro?'Înapoi la Media':'Back to Media',exact:true}).tap();
 await page.locator('.media-sections button').nth(1).tap();await page.locator('.service-iptv').tap();await page.getByRole('button',{name:ro?'Privește live':'Watch live',exact:true}).tap();await preview(page.locator('.iptv-live').getByRole('slider',{name:ro?'Volum':'Volume',exact:true}),'12-tv-fullscreen');
 expect(f.maxActive.volume).toBe(1);expect(f.maxActive.brightness).toBe(1);expect(f.legacyBrightness).toEqual([]);
});

for(const theme of ['ink','night'])for(const kind of ['volume','brightness'] as const)test(`Live slider ${kind} uncertain preview stops queued final and requires verified explicit persistence ${theme}`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme),slider=await quick(page,ro,kind);f.control.holdNext[kind]=true;f.control.loseNext[kind]=true;
 const target=await point(page,slider,.68,true);
 try{
  await expect.poll(()=>f.writes.filter(w=>w.kind===kind).length).toBe(1);expect(f.writes.at(-1)?.body.persist).toBe(false);await page.mouse.up();f.release(kind);
  const dialog=page.getByRole('dialog',{name:ro?'Comenzi rapide':'Quick controls',exact:true}),alert=dialog.getByRole('alert');await expect(alert).toBeVisible();
  expect(f.value(kind)).toBe(target);expect(f.saved[kind]).toBe(kind==='volume'?40:80);expect(f.writes.filter(w=>w.kind===kind)).toHaveLength(1);
  await snap(page,info,'13-uncertain-preview-no-automatic-persist');
  const check=alert.getByRole('button',{name:kind==='brightness'?(ro?'Verifică starea':'Check status'):(ro?'Încearcă din nou':'Try again'),exact:true});await check.tap();
  await expect(alert).toBeVisible();expect(f.writes.filter(w=>w.kind===kind)).toHaveLength(1);expect(f.saved[kind]).toBe(kind==='volume'?40:80);
  // Matching hardware alone is not a durable save: the explicit second action commits.
  await alert.getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true}).tap();await expect.poll(()=>f.saved[kind]).toBe(target);await expect(alert).toHaveCount(0);
  const writes=f.writes.filter(w=>w.kind===kind);expect(writes).toHaveLength(2);expect(writes[1].body.persist).toBe(true);await snap(page,info,'14-preview-recovery-explicitly-saved');
 }finally{f.release(kind);await page.mouse.up();}
});

for(const theme of ['ink','night'])test(`Live slider local video close preserves final intent behind a held preview ${theme}`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme);
 await page.locator('.main-nav button').nth(2).tap();await page.locator('.media-item').filter({hasText:'fixture.webm'}).tap();
 const video=page.locator('.video-overlay'),slider=video.getByRole('slider',{name:ro?'Volum':'Volume',exact:true});await expect(slider).toBeEnabled();f.control.holdNext.volume=true;
 const target=await point(page,slider,.71,true);
 try{
  await expect.poll(()=>f.writes.filter(w=>w.kind==='volume').length).toBe(1);expect(f.writes[0].body.persist).toBe(false);await expect(number(slider)).toHaveText(target+'%');
  const back=video.getByRole('button',{name:ro?'Înapoi la Media':'Back to Media',exact:true});await back.focus();await page.keyboard.press('Enter');await expect(video).toHaveCount(0);
  expect(f.writes.filter(w=>w.kind==='volume')).toHaveLength(1);f.release('volume');await expect.poll(()=>f.saved.volume).toBe(target);
  const writes=f.writes.filter(w=>w.kind==='volume');expect(writes).toHaveLength(2);expect(writes[1].body).toEqual({volume:target,persist:true});expect(f.maxActive.volume).toBe(1);await snap(page,info,'15-local-video-close-flush');
 }finally{f.release('volume');await page.mouse.up();}
});

for(const theme of ['ink','night'])for(const kind of ['volume','brightness'] as const)test(`Live slider ${kind} failure while held discards unsent final instead of saving automatically ${theme}`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro');await page.clock.install();const f=await fixture(page,ro,theme),slider=await quick(page,ro,kind);f.control.holdNext[kind]=true;f.control.loseNext[kind]=true;
 const target=await point(page,slider,.76,true);
 try{
  await expect.poll(()=>f.writes.filter(w=>w.kind===kind).length).toBe(1);f.release(kind);await expect(page.locator('.quick-controls-dialog').getByRole('alert')).toBeVisible();
  await page.mouse.up();await page.clock.runFor(300);expect(f.value(kind)).toBe(target);expect(f.saved[kind]).toBe(kind==='volume'?40:80);expect(f.writes.filter(w=>w.kind===kind)).toHaveLength(1);expect(f.writes[0].body.persist).toBe(false);await snap(page,info,'16-held-failure-no-auto-save');
 }finally{f.release(kind);await page.mouse.up();}
});

for(const theme of ['ink','night'])for(const mode of ['delayed','unavailable'] as const)test(`Live volume previews bypass ${mode} unrelated state reads ${theme}`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme),slider=await quick(page,ro,'volume');
 if(mode==='delayed')f.control.holdAllStates=true;else f.control.failStateReads=true;
 await expect.poll(()=>mode==='delayed'?f.control.stateHeld:f.control.stateFailures,{timeout:6000}).toBeGreaterThan(0);
 await point(page,slider,.31,true);
 try{
  await expect.poll(()=>f.value('volume')).toBe(31);await expect.poll(()=>f.writes.filter(w=>w.kind==='volume'&&w.body.persist===false).length).toBe(1);await expect(slider).toBeEnabled();
  const target=await point(page,slider,.78);await expect.poll(()=>f.value('volume')).toBe(target);await expect.poll(()=>f.writes.filter(w=>w.kind==='volume'&&w.body.persist===false).length).toBe(2);await expect(number(slider)).toHaveText(target+'%');expect(f.saved.volume).toBe(40);
  await snap(page,info,'17-preview-independent-of-state-read');f.releaseAllStates();await page.mouse.up();await expect.poll(()=>f.saved.volume).toBe(target);expect(f.maxActive.volume).toBe(1);
 }finally{f.releaseAllStates();await page.mouse.up();}
});

for(const theme of ['ink','night'])for(const reply of ['mismatch','unready','unavailable'] as const)test(`Live volume ${reply} actual readback stops queued unsent intent ${theme}`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro');await page.clock.install();const f=await fixture(page,ro,theme),slider=await quick(page,ro,'volume');f.control.holdNext.volume=true;f.control.audioReply=reply;
 const first=await point(page,slider,.63,true);
 try{
  await expect.poll(()=>f.writes.filter(w=>w.kind==='volume').length).toBe(1);await point(page,slider,.83);await expect(number(slider)).toHaveText('83%');await page.mouse.up();f.release('volume');
  await expect(page.locator('.quick-controls-dialog').getByRole('alert')).toBeVisible();await page.clock.runFor(300);expect(f.writes.filter(w=>w.kind==='volume')).toHaveLength(1);expect(f.writes[0].body.persist).toBe(false);expect(f.saved.volume).toBe(40);
  expect(f.value('volume')).toBe(reply==='mismatch'?first-1:first);await snap(page,info,'18-invalid-actual-readback-no-auto-replay');
 }finally{f.release('volume');await page.mouse.up();}
});
