import {test,expect,type Page} from '@playwright/test';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
const identity='m1_'+'a'.repeat(64),sid='S'.repeat(32),film={path:'/approved/Film.webm',name:'Film.webm',kind:'video',media_identity:identity,size:123456,deletable:true,delete_token:'owned-delete-token'};
// Decoder fixture is an existing owned clip. It does not certify inspection or hardware playback.
const clip=await readFile(resolve('app/ui/public/ambient/city-entry-media-day-v1.webm'));
const art=await readFile(resolve('app/ui/public/assets/moon-surface-nasa.jpg'));
async function fixture(page:Page,ro:boolean,theme:string,{history=true,inspectFail=false,artFail=false,holdStart=false,holdStream=false}={}){
 const calls:{path:string;method:string;body:any}[]=[],streams:string[]=[];
 let released=!holdStart,release!:()=>void,releaseStream!:()=>void,releaseDelete!:()=>void,holdDelete=false,deleteFailure=false,removeLost=false,starts=0;
 const gate=new Promise<void>(r=>release=()=>{released=true;r();}),streamGate=new Promise<void>(r=>releaseStream=r);
 let historyItems:any[]=history?[{...film,position_s:.2,duration_s:60,updated_at:1}]:[];
 const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,navigationCollapsed:false,navigationAutoHide:false,screensaverMinutes:0,nightEnabled:false},network:{},bluetooth:{devices:[],prompts:[]},audio:{ready:true,available:true,volume:30,mute:false,outputs:[]},player:{state:'idle'},weather:{}};
 await page.route('**/api/**',async route=>{
  const request=route.request(),url=new URL(request.url()),method=request.method(),body=request.postData()?request.postDataJSON():undefined;
  let json:any={ok:true};
  if(method!=='GET')calls.push({path:url.pathname,method,body});
  if(url.pathname==='/api/session')json={token:'owned-fixture'};
  else if(url.pathname==='/api/state')json=state;
  else if(url.pathname==='/api/media'&&method==='GET')json={path:'/approved',items:[film,{path:'/approved/Music.wav',name:'Music.wav',kind:'audio',media_identity:'m1_'+'b'.repeat(64)}]};
  else if(url.pathname==='/api/media/continue'){
   if(method==='DELETE'){historyItems=[];if(removeLost){removeLost=false;return route.abort('failed');}}
   json={items:historyItems};
  }else if(url.pathname==='/api/media/inspect'){
   if(inspectFail)return route.fulfill({status:503,json:{error:'media_inspection_unavailable'}});
   json={state:'ready',metadata:{title:'Owned title',artist:'Owned artist',duration_s:60},artwork_available:true};
  }else if(url.pathname==='/api/media/artwork'){
   if(artFail)return route.fulfill({status:404,json:{error:'media_artwork_unavailable'}});
   return route.fulfill({contentType:'image/jpeg',body:art});
  }else if(url.pathname==='/api/player'){state.player={state:'idle'};json=state.player;}
  else if(url.pathname==='/api/media/video-session'){
   if(!released)await gate;
   const currentSid=starts++?'R'.repeat(32):sid;
   json={session_id:currentSid,media_identity:identity,resume_position_s:body.resume?.2:0,stream_url:`/api/media/file?session_id=${currentSid}`};
  }else if(url.pathname.startsWith('/api/media/video-session/')){
   if(method==='DELETE'){
    if(holdDelete)await new Promise<void>(r=>releaseDelete=r);
    if(deleteFailure){deleteFailure=false;return route.fulfill({status:500,json:{error:'history_write_failed'}});}
   }
   json={updated:true,closed:method==='DELETE'};
  }else if(url.pathname==='/api/media/file'){
   streams.push(url.search);if(holdStream)await streamGate;
   const range=request.headers().range?.match(/bytes=(\d+)-(\d*)/),start=range?Number(range[1]):0,end=range?Math.min(Number(range[2]||clip.length-1),clip.length-1):clip.length-1;
   return route.fulfill({status:range?206:200,contentType:'video/webm',headers:{'Accept-Ranges':'bytes',...(range?{'Content-Range':`bytes ${start}-${end}/${clip.length}`}:{})},body:clip.subarray(start,end+1)}).catch(()=>{});
  }
  await route.fulfill({json}).catch(()=>{});
 });
 await page.goto('/');await page.locator('.main-nav button').nth(2).tap();await expect(page.locator('.media-item').filter({hasText:'Film.webm'})).toBeVisible();
 return {calls,streams,state,release,releaseStream,releaseDelete:()=>releaseDelete?.(),holdDelete:()=>{holdDelete=true;},failDelete:()=>{deleteFailure=true;},loseRemoveAck:()=>{removeLost=true;}};
}
const closeButton=(page:Page,ro:boolean)=>page.getByRole('button',{name:ro?'Înapoi la Media':'Back to Media',exact:true});
for(const theme of ['ink','night']){
 test(`real metadata and decoded owned artwork stay local to usable listing ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,{history:false});
  const row=page.locator('.media-entry').filter({hasText:'Film.webm'});await expect(row).toContainText('Owned title · Owned artist · 1:00');
  const image=row.locator('img');await expect.poll(()=>image.evaluate((img:HTMLImageElement)=>img.complete&&img.naturalWidth>0)).toBe(true);
  await expect(page.getByRole('button',{name:`${ro?'Șterge fișierul':'Delete file'}: Film.webm`,exact:true})).toBeVisible();
  expect(f.calls.filter(call=>call.path==='/api/play'||call.path==='/api/preferences')).toEqual([]);
  await page.screenshot({path:info.outputPath('library-real-metadata.png')});
 });
 test(`inspection failure and broken artwork retain browsing and file management ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro');await fixture(page,ro,theme,{history:false,inspectFail:true});
  await expect(page.locator('.media-item')).toHaveCount(2);await expect(page.locator('.error-strip')).toHaveCount(0);
  await expect(page.locator('.media-name-toggle').first()).toBeEnabled();
  // A separate page load exercises decoded-art failure rather than only missing metadata.
  await page.unroute('**/api/**');await fixture(page,ro,theme,{history:false,artFail:true});
  const row=page.locator('.media-entry').filter({hasText:'Film.webm'});await expect(row.locator('img')).toHaveCount(0);await expect(row.locator('.file-icon svg')).toBeVisible();await expect(row.locator('.media-item')).toBeEnabled();
 });
 test(`Continue actions are explicit; lost remove acknowledgement verifies before any second write ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme),section=page.getByRole('region',{name:ro?'Continuă vizionarea':'Continue watching'});
  for(const name of [ro?'Reia':'Resume',ro?'De la început':'Start over'])await expect(section.getByRole('button',{name,exact:true})).toBeVisible();
  f.loseRemoveAck();await section.getByRole('button',{name:`${ro?'Elimină din istoric':'Remove from history'}: Film.webm`,exact:true}).tap();
  await expect(section.getByRole('alert')).toBeVisible();await section.getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true}).tap();await expect(section).toHaveCount(0);
  expect(f.calls.filter(call=>call.path==='/api/media/continue'&&call.method==='DELETE')).toHaveLength(1);expect(f.calls.filter(call=>call.path==='/api/media'&&call.method==='DELETE')).toHaveLength(0);
 });
 test(`resume seek precedes actual play; final progress and close are atomic ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme);
  await page.evaluate(()=>{const original=HTMLMediaElement.prototype.play;(window as any).__ownedVideoPlayPositions=[];HTMLMediaElement.prototype.play=function(){if(this.closest('.video-overlay'))(window as any).__ownedVideoPlayPositions.push(this.currentTime);return original.call(this);};});
  await page.locator('.media-continue').getByRole('button',{name:ro?'Reia':'Resume',exact:true}).tap();
  const video=page.locator('.video-overlay video');await expect.poll(()=>video.evaluate((node:HTMLVideoElement)=>Number.isFinite(node.duration)&&node.currentTime>=.19)).toBe(true);
  await expect.poll(()=>page.evaluate(()=>(window as any).__ownedVideoPlayPositions.length)).toBeGreaterThan(0);
  expect((await page.evaluate(()=>(window as any).__ownedVideoPlayPositions as number[]))[0]).toBeGreaterThanOrEqual(.19);
  await video.evaluate((node:HTMLVideoElement)=>{node.pause();node.currentTime=Math.min(.6,node.duration/2);});await expect.poll(()=>video.evaluate((node:HTMLVideoElement)=>!node.seeking)).toBe(true);
  const observed=await video.evaluate((node:HTMLVideoElement)=>({position_s:node.currentTime,duration_s:node.duration,ended:node.ended}));
  f.holdDelete();await closeButton(page,ro).tap();await expect.poll(()=>f.calls.some(call=>call.method==='DELETE'&&call.path.endsWith(sid))).toBe(true);await expect(page.locator('.video-overlay')).toBeVisible();
  const final=f.calls.findLast(call=>call.method==='DELETE'&&call.path.endsWith(sid))!;expect(final.body).toMatchObject(observed);expect(final.body.sequence).toBeGreaterThan(0);
  f.releaseDelete();await expect(page.locator('.video-overlay')).toHaveCount(0);expect(f.streams.every(query=>query===`?session_id=${sid}`)).toBe(true);
  expect(f.calls.find(call=>call.path==='/api/media/video-session')?.body).toEqual({path:film.path,media_identity:identity,resume:true});
 });
 test(`Start over is a separate intent and early close fabricates no progress ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,{holdStream:true});await page.locator('.media-continue').getByRole('button',{name:ro?'De la început':'Start over',exact:true}).tap();await expect(page.locator('.video-overlay')).toBeVisible();await closeButton(page,ro).tap();await expect(page.locator('.video-overlay')).toHaveCount(0);f.releaseStream();
  expect(f.calls.find(call=>call.path==='/api/media/video-session')?.body.resume).toBe(false);expect(f.calls.find(call=>call.method==='DELETE'&&call.path.endsWith(sid))?.body).toBeUndefined();
 });
 test(`late session acknowledgement is closed without reviving abandoned selection ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,{history:false,holdStart:true});await page.locator('.media-item').filter({hasText:'Film.webm'}).tap();await expect.poll(()=>f.calls.some(call=>call.path==='/api/media/video-session')).toBe(true);await page.locator('.main-nav button').nth(0).tap();f.release();await expect.poll(()=>f.calls.some(call=>call.method==='DELETE'&&call.path.endsWith(sid))).toBe(true);await expect(page.locator('.video-overlay')).toHaveCount(0);expect(f.streams).toEqual([]);
 });
 test(`failed final persistence keeps a recoverable paused video ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,{history:false});await page.locator('.media-item').filter({hasText:'Film.webm'}).tap();await expect.poll(()=>page.locator('.video-overlay video').evaluate((node:HTMLVideoElement)=>Number.isFinite(node.duration)&&node.duration>0)).toBe(true);f.failDelete();await closeButton(page,ro).tap();await expect(page.locator('.video-progress-error')).toBeVisible();await expect(page.locator('.video-overlay video')).toHaveJSProperty('paused',true);await page.locator('.video-progress-error').getByRole('button',{name:ro?'Salvează și închide':'Save and close',exact:true}).tap();await expect(page.locator('.video-overlay')).toHaveCount(0);
 });
 test(`return to Media preserves the folder and search, without opening another file ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,{history:false,holdStream:true});
  await page.getByRole('button',{name:ro?'Caută în acest dosar':'Search this folder',exact:true}).tap();
  for(const letter of 'film')await page.locator('.keyboard-card .keys').getByRole('button',{name:letter,exact:true}).tap();
  await page.locator('.keyboard-card .keys').getByRole('button',{name:ro?'Aplică':'Apply',exact:true}).tap();await expect(page.locator('.media-entry')).toHaveCount(1);
  const row=page.locator('.media-item').filter({hasText:'Film.webm'});await row.tap();await closeButton(page,ro).tap();await expect(page.locator('.video-overlay')).toHaveCount(0);f.releaseStream();
  await expect(page.locator('.media-query-edit')).toContainText('film');await expect(page.locator('.library-path')).toContainText('approved');await expect(page.locator('.media-entry')).toHaveCount(1);await expect(row).toBeFocused();expect(f.calls.filter(call=>call.path==='/api/media/video-session')).toHaveLength(1);
 });
 test(`explicit replay after genuine end closes ended owner then mounts a fresh start-over session ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,{history:false});await page.locator('.media-item').filter({hasText:'Film.webm'}).tap();const video=page.locator('.video-overlay video');
  await expect.poll(()=>video.evaluate((node:HTMLVideoElement)=>Number.isFinite(node.duration)&&node.duration>0)).toBe(true);
  await video.evaluate(async(node:HTMLVideoElement)=>{node.currentTime=Math.max(0,node.duration-.08);await node.play();});await expect(video).toHaveJSProperty('ended',true);
  await page.locator('.video-play').tap();await expect.poll(()=>f.calls.filter(call=>call.path==='/api/media/video-session')).toHaveLength(2);
  await expect(video).toHaveAttribute('src',`/api/media/file?session_id=${'R'.repeat(32)}`);await expect(video).not.toHaveJSProperty('ended',true);
  expect(f.calls.find(call=>call.method==='DELETE'&&call.path.endsWith(sid))?.body.ended).toBe(true);expect(f.calls.filter(call=>call.path==='/api/media/video-session')[1].body.resume).toBe(false);
 });
}
