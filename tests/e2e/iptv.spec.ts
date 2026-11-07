import {test,expect,type Page,type TestInfo} from '@playwright/test';

for(const ro of [false,true])for(const theme of ['ink','night'])test(`official Digi player handoff ${ro?'ro':'en'} ${theme}`,async({page},info)=>{
 const f=await fixture(page,ro,theme);let finish!:()=>void;const held=new Promise<void>(r=>finish=r),opened:any[]=[];
 await page.route('**/api/external',async route=>{opened.push(route.request().postDataJSON());await held;await route.fulfill({json:{opened:true,service:'digisport'}});});
 const entry=page.getByRole('button',{name:ro?'Digi Sport 1 · Player oficial':'Digi Sport 1 · Official player',exact:true});
 await expect(entry).toBeVisible();await expect(entry).toContainText(ro?'Rețea Digi':'Digi network');
 await page.getByRole('button',{name:ro?'Caută canale':'Search channels',exact:true}).tap();await keyboardType(page,'digi',ro);
 await expect(page.locator('.iptv-channel')).toHaveCount(0);await expect(entry).toBeVisible();await expect(page.getByText(ro?'Niciun canal. Caută în Toate sau verifică Surse.':'No channels. Try All or check Sources.',{exact:true})).toHaveCount(0);
 const box=await entry.boundingBox();expect(box!.width).toBeGreaterThanOrEqual(48);expect(box!.height).toBeGreaterThanOrEqual(48);expect(box!.y+box!.height).toBeLessThanOrEqual(480);
 await snap(page,info,'digi-official-entry');await entry.tap();await expect(entry).toBeDisabled();await expect(entry).toContainText(ro?'Se deschide playerul oficial':'Opening official player');
 await entry.evaluate((e:HTMLButtonElement)=>e.click());expect(opened).toEqual([{service:'digisport'}]);
 expect(f.calls.filter(c=>c.path==='/api/iptv/view'||c.path==='/api/iptv/recordings')).toEqual([]);
 await snap(page,info,'digi-official-pending');finish();await expect(entry).toBeEnabled();
});

// These are API/UI contract fixtures. They do not certify a broadcaster stream,
// codec, hardware playback, or the independent Linux recording service.
const NOW=Date.parse('2026-11-05T16:00:00Z');
const when=(minutes:number)=>new Date(NOW+minutes*60000).toISOString();
const source='https://example.org/list.m3u',guideSource='https://www.open-epg.com/files/romania1.xml.gz';
type Call={path:string;method:string;body:any};
type Job={id:string;title:string;channel_name:string;channel_id?:string;start_at:string;end_at:string;before_minutes:number;after_minutes:number;state:string;has_file:boolean;error?:string};
const job=(id:string,title:string,state:string,has_file=false):Job=>({id,title,state,has_file,channel_id:'tv_one',channel_name:'PRO TV HD (1080p)',start_at:when(30),end_at:when(90),before_minutes:0,after_minutes:0});

async function fixture(page:Page,ro:boolean,theme:string,{initialRecords=false,service=true,empty=false,audioReady=true,screensaverMinutes=0}={}){
 await page.clock.setFixedTime(NOW);
 const state:any={preferences:{language:ro?'ro':'en',theme,timezone:'Europe/Bucharest',setupComplete:true,navigationCollapsed:false,navigationAutoHide:false,screensaverMinutes,nightEnabled:false},network:{},bluetooth:{devices:[],prompts:[]},audio:{ready:audioReady,available:true,volume:30,mute:false,outputs:[]},player:{state:'idle'},weather:{}};
 const channels=empty?[]:[{id:'tv_one',name:'PRO TV HD (1080p)',group:'România',favorite:true},{id:'tv_two',name:'Antena 1 (Romania)',group:'România',favorite:false},{id:'tv_three',name:'NBC Sports NOW (1080p)',group:'Undefined',favorite:true}];
 const programmes=[{id:'pg_past',title:'Emisiune încheiată',start:when(-120),end:when(-60),description:'Nu trebuie afișată înaintea programului actual.',source:guideSource},{id:'pg_current',title:'Jurnalul de seară',start:when(-20),end:when(10),description:'Descriere verificabilă a emisiunii curente.',source:guideSource},{id:'pg_next',title:'Documentar despre oraș',start:when(10),end:when(70),description:'Următoarea emisiune are un interval distinct.',source:guideSource}];
 const catalogue:any={channels,sources:{playlists:[source],xmltv:[guideSource]},favorite_requests:[{name:'PokerGo',channel_id:null,status:'not_in_playlists'}],source_status:{},refreshing:false,guide_updated_at:when(-60)};
 let records:Job[]=initialRecords?[job('scheduled_one','Programare existentă','scheduled'),job('live_one','Emisiune în curs','recording'),job('saved_one','Înregistrare salvată','completed',true),{...job('failed_one','Înregistrare eșuată','failed'),error:'recorder_disk_full'}]:[];
 const calls:Call[]=[],idempotency=new Map<string,Job>();
 const control={loseCreateAck:false,failView:true,holdView:false,failGuide:false,failCloseOnce:false,holdCloseOnce:false,refreshGuideTitle:false,stallStream:false,manifestReads:0};
 let releaseView:()=>void=()=>{},releaseClose:()=>void=()=>{},viewerNumber=0,guideReads=0;
 await page.route('**/api/**',async route=>{
  const request=route.request(),url=new URL(request.url()),path=url.pathname,method=request.method(),body=request.postData()?request.postDataJSON():undefined;
  if(method!=='GET')calls.push({path,method,body});
  let json:any={ok:true};
  if(path==='/api/session')json={token:'owned-iptv-fixture'};
  else if(path==='/api/state')json=state;
  else if(path==='/api/media'&&method==='GET')json={path:'/approved',items:[]};
  else if(path==='/api/media/continue')json={items:[]};
  else if(path==='/api/media/inspect')json={state:'unavailable'};
  else if(path==='/api/player'){state.player={state:'idle'};json=state.player;}
  else if(path==='/api/audio'){const{persist,...change}=body;Object.assign(state.audio,change);if(persist!==false&&body.volume!==undefined)state.preferences.volume=body.volume;json=state.audio;}
  else if(path==='/api/iptv')json=catalogue;
  else if(path.startsWith('/api/iptv/guide/')){
   guideReads++;
   if(control.failGuide)return route.fulfill({status:503,json:{error:'iptv_source_unavailable'}});
   const id=decodeURIComponent(path.split('/').at(-1)!);
   json={channel_id:id,matched_by:'identifier',programmes:id==='tv_three'?[]:programmes,current:id==='tv_three'?null:programmes.find(p=>p.id==='pg_current'),upcoming:id==='tv_three'?[]:programmes.filter(p=>p.id==='pg_next'),stale:false,updated_at:when(0),errors:[]};
  }else if(path==='/api/iptv/favorites'){
   const channel=channels.find(c=>c.id===body.channel_id)!;channel.favorite=body.favorite;json=catalogue;
  }else if(path==='/api/iptv/sources'){
   catalogue.sources[body.kind]=body.urls;json={saved:true};
  }else if(path==='/api/iptv/refresh'){
   if(body.kind==='guide'&&control.refreshGuideTitle){programmes[1]={...programmes[1],title:'Ghid XMLTV actualizat'};catalogue.guide_updated_at=when(0);}
   json={accepted:true};
  }
  else if(path==='/api/iptv/recordings'&&method==='GET')json={items:records,service:{active:service,service_active:service}};
  else if(path==='/api/iptv/recordings'&&method==='POST'){
   let row=idempotency.get(body.request_id);
   if(!row){row={...job('created_'+(idempotency.size+1),body.title,'scheduled'),channel_id:body.channel_id,start_at:body.start_at,end_at:body.end_at,before_minutes:body.before_minutes,after_minutes:body.after_minutes};idempotency.set(body.request_id,row);records.unshift(row);}
   if(control.loseCreateAck){control.loseCreateAck=false;return route.abort('failed');}
   json=row;
  }else if(path.startsWith('/api/iptv/recordings/')){
   const [, , , ,id,action]=path.split('/'),row=records.find(r=>r.id===id)!;
   if(method==='PATCH'){Object.assign(row,body);json=row;}
   else if(method==='POST'&&action==='cancel'){row.state='cancelled';json=row;}
   else if(method==='POST'&&action==='stop'){row.state='stopped';row.has_file=true;json=row;}
   else if(method==='DELETE'){records=records.filter(r=>r.id!==id);json={deleted:true};}
   else if(method==='GET'&&action==='media')json={path:'/approved/recording.mkv',name:'recording.mkv',kind:'video',media_identity:'m1_'+'a'.repeat(64),deletable:true,delete_token:'owned-synthetic-recording'};
  }else if(path==='/api/media/video-session')json={session_id:'R'.repeat(32),stream_url:'/api/media/file?session_id='+'R'.repeat(32),media_identity:'m1_'+'a'.repeat(64),resume_position_s:0};
  else if(path.startsWith('/api/media/video-session/'))json={closed:method==='DELETE',updated:true};
  else if(path==='/api/media/file')return route.fulfill({status:503,json:{error:'owned_fixture_no_decoder_claim'}});
  else if(path==='/api/iptv/view'&&method==='POST'){
   if(control.failView)return route.fulfill({status:503,json:{error:'iptv_stream_unavailable'}});
   const current=++viewerNumber;
   if(control.holdView){control.holdView=false;await new Promise<void>(resolve=>releaseView=resolve);}
   json={session_id:'viewer_'+current,stream_url:'/api/iptv/stream/viewer_'+current+'/root'};
  }else if(path.startsWith('/api/iptv/view/')&&method==='DELETE'){
   if(control.holdCloseOnce){control.holdCloseOnce=false;await new Promise<void>(resolve=>releaseClose=resolve);}
   if(control.failCloseOnce){control.failCloseOnce=false;return route.fulfill({status:503,json:{error:'iptv_stream_unavailable'}});}
   json={closed:true};
  }
  else if(path.startsWith('/api/iptv/stream/')){
   if(control.stallStream){
    if(path.endsWith('/root')){control.manifestReads++;return route.fulfill({contentType:'application/vnd.apple.mpegurl',body:'#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:2\n#EXT-X-MEDIA-SEQUENCE:1\n#EXTINF:2,\nsegment.ts\n'});}
    // Deliberately no segment response: valid manifest, no decoder progress.
    await new Promise<void>(()=>{});return;
   }
   return route.fulfill({status:503,json:{error:'iptv_stream_unavailable'}});
  }
  await route.fulfill({json}).catch(()=>{});
 });
 await page.goto('/');await page.locator('.main-nav button').nth(2).tap();
 await page.locator('.media-sections').getByRole('button',{name:ro?'Servicii':'Services',exact:true}).tap();
 await expect(page.locator('.service-row')).toHaveCount(5);
 await page.locator('.service-row').filter({hasText:ro?'Live, ghid și înregistrări':'Live, guide & recordings'}).tap();
 await expect(page.getByRole('region',{name:ro?'Televiziune IPTV':'IPTV television'})).toBeVisible();
 await expect(page.locator('.iptv-channel')).toHaveCount(empty?0:2);
 return{state,catalogue,channels,programmes,calls,control,records:()=>records,releaseView:()=>releaseView(),releaseClose:()=>releaseClose(),idempotency,guideReads:()=>guideReads};
}

async function snap(page:Page,info:TestInfo,name:string){await page.screenshot({path:info.outputPath(name+'.png'),animations:'disabled'});}
async function shellGeometry(page:Page){
 expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(800);
 const boxes=await page.locator('.iptv-heading button,.iptv-tabs button,.iptv-filter button,.iptv-guide>header button,.iptv-channel-actions button,.iptv-guide-heading button').evaluateAll(nodes=>nodes.map(n=>{const r=n.getBoundingClientRect();return{label:n.getAttribute('aria-label')||n.textContent,x:r.x,y:r.y,w:r.width,h:r.height};}));
 for(const b of boxes){expect(b.w,b.label||'target width').toBeGreaterThanOrEqual(48);expect(b.h,b.label||'target height').toBeGreaterThanOrEqual(48);expect(b.x).toBeGreaterThanOrEqual(0);expect(b.y).toBeGreaterThanOrEqual(0);expect(b.x+b.w).toBeLessThanOrEqual(800.5);expect(b.y+b.h).toBeLessThanOrEqual(480.5);}
 for(const selector of ['.iptv-channel-list','.iptv-programmes'])await expect(page.locator(selector)).toHaveCSS('scrollbar-width','none');
}
async function keyboardType(page:Page,value:string,ro:boolean,{clear=false}={}){
 const keyboard=page.locator('.keyboard-card');await expect(keyboard).toBeVisible();
 if(clear)await keyboard.getByRole('button',{name:ro?'Șterge tot textul':'Clear all text',exact:true}).tap();
 let symbols=false,caps=false;
 const symbolToggle=()=>keyboard.locator('.keys').getByRole('button',{name:ro?'Schimbă simbolurile tastaturii':'Change keyboard symbols',exact:true});
 for(const c of value){
  if(c===' '){await keyboard.locator('.keys').getByRole('button',{name:ro?'Spațiu':'Space',exact:true}).tap();continue;}
  const letter=/[a-zăâîșț]/i.test(c);
  if(letter&&symbols){await symbolToggle().tap();symbols=false;}
  if(letter&&caps!==(c===c.toUpperCase())){await keyboard.locator('.key-special[aria-pressed]').tap();caps=!caps;}
  let button=keyboard.locator('.keys').getByRole('button',{name:c,exact:true});
  if(await button.count()===0){await symbolToggle().tap();symbols=!symbols;button=keyboard.locator('.keys').getByRole('button',{name:c,exact:true});}
  await button.tap();
 }
 await keyboard.locator('.keys').getByRole('button',{name:ro?'Aplică':'Apply',exact:true}).tap();await expect(keyboard).toHaveCount(0);
}
const recordsTab=(page:Page,ro:boolean)=>page.locator('.iptv-tabs').getByRole('button',{name:ro?'Înregistrări':'Recordings',exact:true});
const sourcesTab=(page:Page,ro:boolean)=>page.locator('.iptv-tabs').getByRole('button',{name:ro?'Surse':'Sources',exact:true});
const editor=(page:Page,ro:boolean)=>page.getByRole('dialog',{name:ro?'Programează înregistrarea':'Schedule recording',exact:true});
const row=(page:Page,title:string)=>page.locator('.iptv-recording').filter({has:page.getByRole('heading',{name:title,exact:true})});

// A media-element state double for control/lifecycle tests, never playback proof.
// The stall test below uses the untouched browser element and a real HLS parser.
async function syntheticTVClock(page:Page){
 // Keep the media state double independent of HLS network retry exhaustion.
 // The real parser and missing segments are exercised in the no-frame test.
 await page.route('**/node_modules/.vite/deps/hls__js.js*',route=>route.fulfill({contentType:'application/javascript',body:`
 export default class Hls {
  static Events={ERROR:'error',MANIFEST_PARSED:'manifest'};static isSupported(){return true;}
  events={};on(name,listener){this.events[name]=listener;}loadSource(){}
  attachMedia(){queueMicrotask(()=>this.events.manifest?.());}destroy(){}
 }`}));
 await page.addInitScript(()=>{
  const proto=HTMLMediaElement.prototype,states=new WeakMap<HTMLMediaElement,{paused:boolean;position:number;started:number}>();
  const own=(v:HTMLMediaElement)=>v.closest('.iptv-live')!==null;
  const state=(v:HTMLMediaElement)=>{let s=states.get(v);if(!s){s={paused:true,position:0,started:performance.now()};states.set(v,s);}return s;};
  const position=(v:HTMLMediaElement)=>{const s=state(v);return s.position+(s.paused?0:(performance.now()-s.started)/1000);};
  for(const name of ['paused','currentTime','readyState'] as const){
   const native=Object.getOwnPropertyDescriptor(proto,name)!;
   Object.defineProperty(proto,name,{configurable:true,get(){if(!own(this))return native.get!.call(this);return name==='paused'?state(this).paused:name==='readyState'?4:position(this);},...(name==='currentTime'?{set(value:number){if(!own(this))return native.set!.call(this,value);const s=state(this);s.position=value;s.started=performance.now();}}:{})});
  }
  const play=proto.play,pause=proto.pause;
  const width=Object.getOwnPropertyDescriptor(HTMLVideoElement.prototype,'videoWidth')!;
  Object.defineProperty(HTMLVideoElement.prototype,'videoWidth',{configurable:true,get(){return own(this)?1280:width.get!.call(this);}});
  proto.play=function(){if(!own(this))return play.call(this);const s=state(this);s.started=performance.now();s.paused=false;this.dispatchEvent(new Event('play'));this.dispatchEvent(new Event('playing'));return Promise.resolve();};
  proto.pause=function(){if(!own(this))return pause.call(this);const s=state(this);if(s.paused)return;s.position=position(this);s.paused=true;this.dispatchEvent(new Event('pause'));};
 });
}

for(const theme of ['ink','night']){
 test(`TV recovery no-frame deadline retries one owned session without a speaker ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro');await page.clock.install({time:NOW});
  const f=await fixture(page,ro,theme,{audioReady:false});f.control.failView=false;f.control.stallStream=true;
  await page.getByRole('button',{name:ro?'Privește live':'Watch live',exact:true}).tap();
  const live=page.getByRole('dialog',{name:'PRO TV HD (1080p)',exact:true});
  await expect.poll(()=>f.control.manifestReads).toBeGreaterThan(0);await expect(live.locator('.iptv-live-status[role=status]')).toContainText(ro?'Se conectează':'Connecting');
  await expect(live.locator('.iptv-live-caption>span')).toHaveText(ro?'Se conectează…':'Connecting…');
  await expect(live.locator('.iptv-volume input')).toBeDisabled();await expect(live.locator('.iptv-volume-value')).toContainText(ro?'Nicio ieșire audio':'No audio output');
  await snap(page,info,'recovery-01-valid-manifest-no-frames-no-speaker');
  await page.clock.runFor(27000);
  await expect(live.getByRole('alert')).toContainText(ro?'Sursa TV nu mai livrează imagine':'The TV source is not delivering video');
  await expect(live.locator('.iptv-live-caption>span')).toHaveText(ro?'Problemă de redare':'Playback problem');
  await snap(page,info,'recovery-02-bounded-actionable-no-frame-error');
  const retry=live.getByRole('button',{name:ro?'Reîncearcă':'Retry',exact:true});
  await retry.evaluate((button:HTMLButtonElement)=>{button.click();button.click();});
  await expect.poll(()=>f.calls.filter(c=>c.path==='/api/iptv/view'&&c.method==='POST').length).toBe(2);
  expect(f.calls.filter(c=>c.path==='/api/iptv/view/viewer_1'&&c.method==='DELETE')).toHaveLength(1);
  expect(f.calls.findIndex(c=>c.path==='/api/iptv/view/viewer_1'&&c.method==='DELETE')).toBeLessThan(f.calls.findIndex(c=>c.path==='/api/iptv/view'&&c.method==='POST'&&f.calls.indexOf(c)>f.calls.findIndex(v=>v.path==='/api/iptv/view')));
  await live.getByRole('button',{name:ro?'Înapoi la TV':'Back to TV',exact:true}).tap();await expect(live).toHaveCount(0);
  await expect.poll(()=>f.calls.filter(c=>c.path==='/api/iptv/view/viewer_2'&&c.method==='DELETE').length).toBe(1);
 });

 test(`TV recovery intentional pause and progressing playback avoid false stall ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro');await page.clock.install({time:NOW});await syntheticTVClock(page);
  const f=await fixture(page,ro,theme);f.control.failView=false;f.control.stallStream=true;
  await page.getByRole('button',{name:ro?'Privește live':'Watch live',exact:true}).tap();
  const live=page.getByRole('dialog',{name:'PRO TV HD (1080p)',exact:true});
  const pause=live.getByRole('button',{name:ro?'Pauză':'Pause',exact:true});await expect(pause).toBeEnabled();
  await page.clock.runFor(27000);await expect(live.getByRole('alert')).toHaveCount(0);await expect(live.locator('video')).toHaveJSProperty('paused',false);
  await live.locator('video').tap();await pause.tap();await expect(live.locator('video')).toHaveJSProperty('paused',true);
  await page.clock.runFor(27000);await expect(live.getByRole('alert')).toHaveCount(0);await snap(page,info,'recovery-03-intentional-pause-survives-deadline-fixture');
  await expect(live.locator('.iptv-live-caption>span')).toHaveText(ro?'În pauză':'Paused');
  await live.getByRole('button',{name:ro?'Redă':'Play',exact:true}).tap();await expect(live.locator('video')).toHaveJSProperty('paused',false);
  await expect(live.locator('.iptv-live-caption>span')).toHaveText(ro?'În direct':'Live');
  await page.clock.runFor(27000);await expect(live.getByRole('alert')).toHaveCount(0);
  await live.locator('video').evaluate(v=>v.dispatchEvent(new Event('ended')));
  await expect(live.getByRole('alert')).toContainText(ro?'Sursa TV nu mai livrează imagine':'The TV source is not delivering video');
  await snap(page,info,'recovery-04-ended-live-stream-is-actionable-fixture');
 });

 test(`TV recovery viewer excludes idle screensaver and releases it on close ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro');await page.clock.install({time:NOW});await syntheticTVClock(page);
  const f=await fixture(page,ro,theme,{screensaverMinutes:1});f.control.failView=false;f.control.stallStream=true;
  await page.getByRole('button',{name:ro?'Privește live':'Watch live',exact:true}).tap();
  const live=page.getByRole('dialog',{name:'PRO TV HD (1080p)',exact:true});await expect(live.getByRole('button',{name:ro?'Pauză':'Pause',exact:true})).toBeEnabled();
  await page.clock.runFor(65000);await expect(page.locator('.pysh-screensaver')).toHaveCount(0);await expect(live.getByRole('alert')).toHaveCount(0);
  await snap(page,info,'recovery-05-viewer-keeps-idle-screen-away-fixture');
  await live.locator('video').tap();await live.getByRole('button',{name:ro?'Înapoi la TV':'Back to TV',exact:true}).tap();await expect(live).toHaveCount(0);
  await page.clock.runFor(61000);await expect(page.locator('.pysh-screensaver')).toBeVisible();
  await snap(page,info,'recovery-06-idle-policy-resumes-after-close');
 });

 test(`TV recovery fullscreen volume and mute use shared confirmed audio state ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro');await page.clock.install({time:NOW});await syntheticTVClock(page);
  const f=await fixture(page,ro,theme);f.control.failView=false;f.control.stallStream=true;
  await page.getByRole('button',{name:ro?'Privește live':'Watch live',exact:true}).tap();
  const live=page.getByRole('dialog',{name:'PRO TV HD (1080p)',exact:true});await expect(live.getByRole('button',{name:ro?'Pauză':'Pause',exact:true})).toBeEnabled();
  const bounds=await live.boundingBox();expect(bounds).toEqual({x:0,y:0,width:800,height:480});
  const slider=live.getByRole('slider',{name:ro?'Volum':'Volume',exact:true}),box=(await slider.boundingBox())!;
  await slider.tap({position:{x:box.width*.65,y:box.height/2}});
  await expect.poll(()=>f.calls.filter(c=>c.path==='/api/audio'&&c.body.persist===true).length).toBe(1);expect(f.calls.filter(c=>c.path==='/api/audio'&&c.body.persist===true)[0].body).toEqual({volume:65,persist:true});
  await expect(slider).toHaveValue('65');await expect(live.locator('.audio-volume-value')).toHaveText('65%');
  await live.getByRole('button',{name:ro?'Fără sunet':'Mute',exact:true}).tap();await expect(live.getByRole('button',{name:ro?'Activează sunetul':'Unmute',exact:true})).toHaveAttribute('aria-pressed','true');
  expect(f.state.audio.mute).toBe(true);await snap(page,info,'recovery-07-fullscreen-shared-volume-mute-confirmed-fixture');
  await live.getByRole('button',{name:ro?'Activează sunetul':'Unmute',exact:true}).tap();await expect(live.getByRole('button',{name:ro?'Fără sunet':'Mute',exact:true})).toHaveAttribute('aria-pressed','false');
  await live.getByRole('button',{name:ro?'Canalul următor':'Next channel',exact:true}).tap();
  await expect(page.getByRole('dialog',{name:'NBC Sports NOW (1080p)',exact:true})).toBeVisible();
  const close=f.calls.findIndex(c=>c.path==='/api/iptv/view/viewer_1'&&c.method==='DELETE');
  const next=f.calls.findIndex(c=>c.path==='/api/iptv/view'&&c.method==='POST'&&c.body.channel_id==='tv_three');expect(close).toBeGreaterThanOrEqual(0);expect(next).toBeGreaterThan(close);
  await page.getByRole('button',{name:ro?'Oprește TV':'Stop TV',exact:true}).tap();await expect(page.locator('.iptv-live')).toHaveCount(0);
  await expect(page.locator('.iptv-guide h2')).toHaveText('NBC Sports NOW (1080p)');
  await expect(page.locator('.iptv-channel').filter({hasText:'NBC Sports NOW'})).toHaveAttribute('aria-pressed','true');
 });

 test(`TV recovery fullscreen controls persist during volume drag and keyboard use ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro');await page.clock.install({time:NOW});await syntheticTVClock(page);
  const f=await fixture(page,ro,theme);f.control.failView=false;f.control.stallStream=true;
  await page.getByRole('button',{name:ro?'Privește live':'Watch live',exact:true}).tap();
  const live=page.getByRole('dialog',{name:'PRO TV HD (1080p)',exact:true});await expect(live.getByRole('button',{name:ro?'Pauză':'Pause',exact:true})).toBeEnabled();
  const controls=live.locator('.iptv-live-controls'),slider=live.getByRole('slider',{name:ro?'Volum':'Volume',exact:true}),box=(await slider.boundingBox())!;
  await page.mouse.move(box.x+box.width*.6,box.y+box.height/2);await page.mouse.down();
  await page.clock.runFor(6000);await expect(controls).not.toHaveClass(/concealed/);
  await snap(page,info,'recovery-08-held-volume-keeps-controls-visible-fixture');
  expect(f.calls.some(c=>c.path==='/api/audio'&&c.body.persist===false)).toBe(true);await page.mouse.up();await expect.poll(()=>f.calls.filter(c=>c.path==='/api/audio'&&c.body.persist===true).length).toBe(1);
  await page.clock.runFor(5000);await expect(controls).toHaveClass(/concealed/);
  await live.locator('video').tap();await expect(controls).not.toHaveClass(/concealed/);
  await live.getByRole('button',{name:ro?'Înapoi la TV':'Back to TV',exact:true}).focus();await page.keyboard.press('Tab');
  expect(await page.evaluate(()=>!!document.activeElement?.closest('.iptv-live-controls'))).toBe(true);
  await page.clock.runFor(6000);await expect(controls).not.toHaveClass(/concealed/);
  await snap(page,info,'recovery-09-keyboard-focus-keeps-controls-visible-fixture');
  await live.locator('video').tap();await page.clock.runFor(5000);await expect(controls).toHaveClass(/concealed/);
 });
}

for(const theme of ['ink','night']){
 test(`IPTV catalogue entry, current/next guide, local times and touch geometry ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme);
  await expect(page.locator('.iptv-guide h2')).toHaveText('PRO TV HD (1080p)');await expect(page.locator('.iptv-programmes')).not.toContainText('Emisiune încheiată');await expect(page.locator('.iptv-programmes article').first()).toHaveClass('current');await expect(page.locator('.iptv-channel').filter({hasText:'NBC Sports NOW'})).not.toContainText('Undefined');
  await expect(page.locator('.iptv-programmes .current')).toContainText((ro?'Acum · ':'Now · ')+'Jurnalul de seară');
  const currentDetails=page.locator('.iptv-programmes .current .iptv-programme-details');
  await expect(currentDetails).toHaveAttribute('aria-expanded','false');
  await currentDetails.tap();await expect(page.locator('.iptv-programmes .current')).toContainText('Descriere verificabilă a emisiunii curente.');
  await currentDetails.tap();await expect(currentDetails).toHaveAttribute('aria-expanded','false');
  await expect(page.locator('.iptv-programmes .current time')).toContainText('17:40');
  await expect(page.locator('.iptv-programmes .current time')).toContainText('18:10');
  await expect(page.locator('.iptv-programmes article').nth(1)).toContainText('Documentar despre oraș');
  await expect(page.locator('.iptv-guide')).toContainText('Europe/Bucharest');
  await expect(page.locator('.iptv-missing')).toContainText('PokerGo');await shellGeometry(page);await snap(page,info,'01-catalogue-guide-local-time');
  await page.locator('.iptv-heading').getByRole('button',{name:ro?'Servicii':'Services',exact:true}).tap();
  await expect(page.locator('.media-service-list')).toBeVisible();expect(f.calls.filter(c=>c.path==='/api/iptv/view'||c.path==='/api/play')).toEqual([]);
 });

 test(`IPTV favorite changes and touch search handle case and diacritics ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme);
  await page.locator('.iptv-filter').getByRole('button',{name:ro?'Favorite':'Favorites',exact:true}).tap();await expect(page.locator('.iptv-channel')).toHaveCount(3);
  await page.locator('.iptv-channel').filter({hasText:'Antena 1 (Romania)'}).tap();
  await page.getByRole('button',{name:ro?'Adaugă la favorite':'Add favorite',exact:true}).tap();
  await expect(page.getByRole('button',{name:ro?'Elimină din favorite':'Remove favorite',exact:true})).toHaveAttribute('aria-pressed','true');
  expect(f.calls.find(c=>c.path==='/api/iptv/favorites')?.body).toEqual({channel_id:'tv_two',favorite:true});
  await page.getByRole('button',{name:ro?'Caută canale':'Search channels',exact:true}).tap();await keyboardType(page,'ROMANIA',ro);
  await expect(page.locator('.iptv-channel')).toHaveCount(2);await expect(page.locator('.iptv-query')).toHaveText('ROMANIA');await snap(page,info,'02-uppercase-touch-query');
  await page.getByRole('button',{name:ro?'Șterge căutarea':'Clear search',exact:true}).tap();await expect(page.locator('.iptv-channel')).toHaveCount(3);
  await page.locator('.iptv-filter').getByRole('button',{name:ro?'Toate':'All',exact:true}).tap();await expect(page.locator('.iptv-channel')).toHaveCount(3);
  await page.getByRole('button',{name:ro?'Elimină din favorite':'Remove favorite',exact:true}).tap();await expect(page.locator('.iptv-channel')).toHaveCount(2);
 });

 test(`IPTV guide schedule supports padding and safe idempotent save retry ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme);
  const next=page.locator('.iptv-programmes article').nth(1);await next.getByRole('button',{name:(ro?'Programează':'Schedule')+' Documentar despre oraș',exact:true}).tap();
  const dialog=editor(page,ro);await expect(dialog).toBeVisible();await expect(dialog).toContainText('Documentar despre oraș');
  await expect(dialog.getByRole('button',{name:(ro?'Înainte':'Before')+' −1',exact:true})).toBeDisabled();
  for(let i=0;i<2;i++)await dialog.getByRole('button',{name:(ro?'Înainte':'Before')+' +1',exact:true}).tap();
  await dialog.getByRole('button',{name:(ro?'După':'After')+' +1',exact:true}).tap();
  await dialog.getByRole('button',{name:(ro?'Început':'Start')+' −1 min',exact:true}).tap();
  await dialog.getByRole('button',{name:(ro?'Sfârșit':'End')+' +1 min',exact:true}).tap();
  await snap(page,info,'03-recording-padding-editor');f.control.loseCreateAck=true;
  const save=dialog.getByRole('button',{name:ro?'Salvează înregistrarea':'Save recording',exact:true});await save.tap();
  await expect(save).toBeEnabled();await expect(dialog).toBeVisible();await expect(dialog.getByRole('alert')).toBeVisible();await expect.poll(()=>f.idempotency.size).toBe(1);await snap(page,info,'04-recording-acknowledgement-lost');
  await save.tap();await expect(dialog).toHaveCount(0);await expect(recordsTab(page,ro)).toHaveAttribute('aria-pressed','true');
  const writes=f.calls.filter(c=>c.path==='/api/iptv/recordings'&&c.method==='POST');expect(writes).toHaveLength(2);expect(writes[1].body).toEqual(writes[0].body);
  expect(writes[0].body).toMatchObject({channel_id:'tv_one',programme_id:'pg_next',before_minutes:2,after_minutes:1,start_at:when(9),end_at:when(71)});
  expect(writes[0].body.request_id).toMatch(/^[0-9a-f-]{36}$/);expect(f.records()).toHaveLength(1);await snap(page,info,'05-one-persisted-schedule-after-retry');
 });

 test(`IPTV manual recording and inactive service are distinct ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme);
  await page.locator('.iptv-channel-actions').getByRole('button',{name:ro?'Înregistrează':'Record',exact:true}).tap();
  const dialog=editor(page,ro);await expect(dialog).toContainText('PRO TV HD (1080p)');
  await dialog.getByRole('button',{name:ro?'Salvează înregistrarea':'Save recording',exact:true}).tap();await expect(dialog).toHaveCount(0);
  const write=f.calls.find(c=>c.path==='/api/iptv/recordings'&&c.method==='POST')!;expect(write.body.programme_id).toBeUndefined();expect(write.body.start_at).toBe(when(0));expect(write.body.end_at).toBe(when(60));
  await page.unroute('**/api/**');await fixture(page,ro,theme,{service:false});
  await expect(page.locator('.iptv-channel-actions').getByRole('button',{name:ro?'Înregistrează':'Record',exact:true})).toBeDisabled();
  await expect(page.locator('.iptv-programmes .iptv-programme-record').first()).toBeDisabled();
  await recordsTab(page,ro).tap();await expect(page.locator('.iptv-recordings')).toContainText(ro?'Serviciu inactiv':'Service inactive');await snap(page,info,'06-recorder-unavailable');
 });

 test(`IPTV imports XMLTV with touchscreen keyboard and refreshes each source kind ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme);
  await expect(page.locator('.iptv-programmes .current')).toContainText('Jurnalul de seară');const initialReads=f.guideReads();f.control.refreshGuideTitle=true;
  await page.getByRole('button',{name:ro?'Actualizează ghidul':'Refresh guide',exact:true}).tap();expect(f.calls.find(c=>c.path==='/api/iptv/refresh')?.body).toEqual({kind:'guide'});
  await expect(page.locator('.iptv-programmes .current')).toContainText('Ghid XMLTV actualizat');expect(f.guideReads()).toBeGreaterThan(initialReads);await snap(page,info,'07a-selected-guide-refreshed-immediately');
  await sourcesTab(page,ro).tap();await page.locator('.iptv-source-tools').getByRole('button',{name:ro?'Actualizează':'Refresh',exact:true}).tap();
  expect(f.calls.filter(c=>c.path==='/api/iptv/refresh').at(-1)?.body).toEqual({kind:'playlists'});
  await page.getByRole('button',{name:'XMLTV',exact:true}).tap();await expect(page.locator('.iptv-source')).toContainText(guideSource);
  await page.getByRole('button',{name:ro?'Adaugă sursă':'Add source',exact:true}).tap();await keyboardType(page,'epg.example/guide.xml.gz',ro);
  const imported='https://epg.example/guide.xml.gz';await expect.poll(()=>f.catalogue.sources.xmltv).toEqual([guideSource,imported]);
  expect(f.calls.find(c=>c.path==='/api/iptv/sources')?.body).toEqual({kind:'xmltv',urls:[guideSource,imported]});await snap(page,info,'07-imported-xmltv-source');
  await page.getByRole('button',{name:`${ro?'Elimină sursa':'Remove source'} ${imported}`,exact:true}).tap();await expect(page.locator('.iptv-source')).toHaveCount(1);
  await page.locator('.iptv-source-tools').getByRole('button',{name:ro?'Actualizează':'Refresh',exact:true}).tap();expect(f.calls.filter(c=>c.path==='/api/iptv/refresh').at(-1)?.body).toEqual({kind:'guide'});
 });

 test(`IPTV recording list edits, cancels, saves, plays and confirms deletion ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,{initialRecords:true});await recordsTab(page,ro).tap();
  await expect(page.locator('.iptv-recordings')).toContainText(ro?'Serviciu activ':'Service active');await expect(page.locator('.iptv-recordings')).toContainText('Videos/MediaTool · MKV');await snap(page,info,'08-recording-list');
  await row(page,'Programare existentă').getByRole('button',{name:ro?'Modifică':'Edit',exact:true}).tap();
  const dialog=editor(page,ro);await dialog.getByRole('button',{name:(ro?'Sfârșit':'End')+' +1 min',exact:true}).tap();
  await dialog.getByRole('button',{name:ro?'Salvează înregistrarea':'Save recording',exact:true}).tap();await expect(dialog).toHaveCount(0);
  expect(f.calls.find(c=>c.path==='/api/iptv/recordings/scheduled_one'&&c.method==='PATCH')?.body.end_at).toBe(when(91));
  await row(page,'Programare existentă').getByRole('button',{name:ro?'Anulează':'Cancel',exact:true}).tap();await expect(row(page,'Programare existentă')).toContainText(ro?'Anulată':'Cancelled');
  await row(page,'Emisiune în curs').getByRole('button',{name:ro?'Oprește și salvează':'Stop and save',exact:true}).tap();
  await expect(row(page,'Emisiune în curs').getByRole('button',{name:ro?'Redă':'Play',exact:true})).toBeEnabled();expect(f.calls.some(c=>c.path==='/api/iptv/recordings/live_one/stop')).toBe(true);
  await row(page,'Înregistrare salvată').getByRole('button',{name:ro?'Redă':'Play',exact:true}).tap();await expect(page.locator('.video-overlay')).toBeVisible();
  expect(f.calls.some(c=>c.path==='/api/media/video-session'&&c.body.path==='/approved/recording.mkv'&&c.body.resume===false)).toBe(true);
  await page.getByRole('button',{name:ro?'Înapoi la Media':'Back to Media',exact:true}).tap();await expect(page.locator('.video-overlay')).toHaveCount(0);
  await row(page,'Înregistrare salvată').getByRole('button',{name:ro?'Șterge':'Delete',exact:true}).tap();
  const confirm=page.getByRole('dialog',{name:ro?'Șterge înregistrarea':'Delete recording',exact:true});await expect(confirm).toContainText('Înregistrare salvată');await snap(page,info,'09-recording-delete-confirmation');
  await confirm.getByRole('button',{name:ro?'Păstrează':'Keep',exact:true}).tap();await expect(confirm).toHaveCount(0);expect(f.calls.filter(c=>c.path==='/api/iptv/recordings/saved_one'&&c.method==='DELETE')).toHaveLength(0);
  await row(page,'Înregistrare salvată').getByRole('button',{name:ro?'Șterge':'Delete',exact:true}).tap();await confirm.getByRole('button',{name:ro?'Șterge definitiv':'Delete permanently',exact:true}).tap();
  await expect(confirm).toHaveCount(0);await expect(row(page,'Înregistrare salvată')).toHaveCount(0);expect(f.calls.filter(c=>c.path==='/api/iptv/recordings/saved_one'&&c.method==='DELETE')).toHaveLength(1);
 });

 test(`IPTV live start failure retries without fake playback and returns reliably ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme);await page.getByRole('button',{name:ro?'Privește live':'Watch live',exact:true}).tap();
  const live=page.getByRole('dialog',{name:'PRO TV HD (1080p)',exact:true});await expect(live.getByRole('alert')).toContainText(ro?'Fluxul nu răspunde':'The stream is unavailable');
  await snap(page,info,'10-live-start-unavailable');await live.getByRole('button',{name:ro?'Reîncearcă':'Retry',exact:true}).tap();await expect.poll(()=>f.calls.filter(c=>c.path==='/api/iptv/view'&&c.method==='POST').length).toBe(2);
  const stop=f.calls.findIndex(c=>c.path==='/api/player'&&c.body.action==='stop'),start=f.calls.findIndex(c=>c.path==='/api/iptv/view');expect(stop).toBeGreaterThanOrEqual(0);expect(stop).toBeLessThan(start);
  await live.getByRole('button',{name:ro?'Înapoi la TV':'Back to TV',exact:true}).tap();await expect(live).toHaveCount(0);await expect(page.locator('.iptv-channel-actions')).toBeVisible();
 });

 test(`IPTV late viewer acknowledgement is closed and never revives an exited player ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme);f.control.failView=false;f.control.holdView=true;
  await page.getByRole('button',{name:ro?'Privește live':'Watch live',exact:true}).tap();const live=page.getByRole('dialog',{name:'PRO TV HD (1080p)',exact:true});
  await expect(live.getByRole('status')).toContainText(ro?'Se conectează':'Connecting');await expect.poll(()=>f.calls.filter(c=>c.path==='/api/iptv/view').length).toBe(1);
  await live.getByRole('button',{name:ro?'Înapoi la TV':'Back to TV',exact:true}).tap();await expect(live).toHaveCount(0);f.releaseView();
  await expect.poll(()=>f.calls.some(c=>c.path==='/api/iptv/view/viewer_1'&&c.method==='DELETE')).toBe(true);await expect(page.locator('.iptv-live')).toHaveCount(0);
  expect(f.calls.filter(c=>c.path==='/api/iptv/view/viewer_1'&&c.method==='DELETE')).toHaveLength(1);await snap(page,info,'11-abandoned-viewer-stays-closed');
 });

 test(`IPTV failed viewer close keeps ownership until explicit successful retry ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme);f.control.failView=false;f.control.failCloseOnce=true;f.control.holdCloseOnce=true;
  await page.getByRole('button',{name:ro?'Privește live':'Watch live',exact:true}).tap();const live=page.getByRole('dialog',{name:'PRO TV HD (1080p)',exact:true});
  await expect.poll(()=>f.calls.some(c=>c.path==='/api/iptv/view'&&c.method==='POST')).toBe(true);
  // The local proxy fixture deliberately fails decoding; a session nevertheless
  // exists and must be closed before the application can relinquish ownership.
  await expect(live.locator('.iptv-live-status[role=alert]').filter({hasText:ro?'Fluxul nu răspunde':'The stream is unavailable'})).toBeVisible();
  const back=live.getByRole('button',{name:ro?'Înapoi la TV':'Back to TV',exact:true});await back.tap();
  await expect.poll(()=>f.calls.filter(c=>c.path==='/api/iptv/view/viewer_1'&&c.method==='DELETE').length).toBe(1);
  const transport=live.locator('.iptv-live-transport button').nth(1),mute=live.getByRole('button',{name:ro?'Fără sunet':'Mute',exact:true});
  await expect(back).toBeDisabled();await expect(transport).toBeDisabled();await expect(mute).toBeDisabled();await expect(live.locator('video')).toHaveJSProperty('paused',true);
  await transport.evaluate((button:HTMLButtonElement)=>button.click());await mute.evaluate((button:HTMLButtonElement)=>button.click());
  await expect(live.locator('video')).toHaveJSProperty('paused',true);await expect(live.locator('video')).toHaveJSProperty('muted',false);await expect(live).toHaveAttribute('aria-busy','true');await expect(live.getByRole('status')).toContainText(ro?'Se închide TV':'Closing TV');await snap(page,info,'12a-viewer-close-pending-blocks-play-and-mute');f.releaseClose();
  await expect(live.locator('[role=alert]').filter({hasText:ro?'Închiderea nu a fost confirmată':'Closing was not confirmed'})).toBeVisible();await expect(back).toBeEnabled();
  await expect(live).toBeVisible();await expect(transport).toBeDisabled();await expect(mute).toBeDisabled();expect(f.calls.filter(c=>c.path==='/api/iptv/view/viewer_1'&&c.method==='DELETE')).toHaveLength(1);await snap(page,info,'12-viewer-close-unconfirmed-keeps-dialog');
  await back.tap();await expect(live).toHaveCount(0);await expect(page.locator('.iptv-channel-actions')).toBeVisible();
  expect(f.calls.filter(c=>c.path==='/api/iptv/view/viewer_1'&&c.method==='DELETE')).toHaveLength(2);expect(f.calls.filter(c=>c.path==='/api/iptv/view'&&c.method==='POST')).toHaveLength(1);
 });
}
