import {test,expect,type Page} from '@playwright/test';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
const identity='m1_'+'a'.repeat(64),sid='D'.repeat(32),clip=await readFile(resolve('app/ui/public/ambient/city-entry-media-day-v1.webm'));
async function fixture(page:Page,ro:boolean,theme:string,unreachable=false){
 const deletes:any[]=[],otherWrites:string[]=[];const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,navigationCollapsed:false,navigationAutoHide:false,screensaverMinutes:0,nightEnabled:false},network:{},bluetooth:{devices:[],prompts:[]},audio:{ready:true,available:true,volume:30,mute:false,outputs:[]},player:{state:'idle'},weather:{}};
 await page.route('**/api/**',async route=>{
  const request=route.request(),url=new URL(request.url()),method=request.method(),body=request.postData()?request.postDataJSON():undefined;let json:any={ok:true};
  if(url.pathname==='/api/session')json={token:'owned-fixture'};
  else if(url.pathname==='/api/state')json=state;
  else if(url.pathname==='/api/media'&&method==='GET')json={path:'/approved',items:[{path:'/approved/Film.webm',name:'Film.webm',kind:'video',media_identity:identity}]};
  else if(url.pathname==='/api/media/continue')json={items:[]};
  else if(url.pathname==='/api/media/inspect')json={state:'unavailable',metadata:null,artwork_available:false};
  else if(url.pathname==='/api/player')json=state.player;
  else if(url.pathname==='/api/media/video-session')json={session_id:sid,media_identity:identity,resume_position_s:0,stream_url:`/api/media/file?session_id=${sid}`};
  else if(url.pathname===`/api/media/video-session/${sid}`){
   if(method==='DELETE'){deletes.push(body);if(unreachable)return route.fulfill({status:503,json:{error:'backend_unavailable'}});if(body)return route.fulfill({status:500,json:{error:'history_write_failed'}});json={closed:true};}
  }else if(url.pathname==='/api/media/file'){
   const range=request.headers().range?.match(/bytes=(\d+)-(\d*)/),start=range?Number(range[1]):0,end=range?Math.min(Number(range[2]||clip.length-1),clip.length-1):clip.length-1;
   return route.fulfill({status:range?206:200,contentType:'video/webm',headers:{'Accept-Ranges':'bytes',...(range?{'Content-Range':`bytes ${start}-${end}/${clip.length}`}:{})},body:clip.subarray(start,end+1)});
  }else if(method!=='GET')otherWrites.push(url.pathname);
  await route.fulfill({json});
 });
 await page.goto('/');await page.locator('.main-nav button').nth(2).tap();await page.locator('.media-item').tap();const video=page.locator('.video-overlay video');await expect.poll(()=>video.evaluate((node:HTMLVideoElement)=>Number.isFinite(node.duration)&&node.duration>0)).toBe(true);await video.evaluate((node:HTMLVideoElement)=>node.pause());
 await page.getByRole('button',{name:ro?'Înapoi la Media':'Back to Media',exact:true}).tap();await expect(page.locator('.video-progress-error')).toBeVisible();return {deletes,otherWrites};
}
for(const theme of ['ink','night']){
 test(`persistent history failure allows only explicit absent-body discard ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme),recovery=page.locator('.video-progress-error');
  await recovery.getByRole('button',{name:ro?'Salvează și închide':'Save and close',exact:true}).tap();await expect.poll(()=>f.deletes.length).toBe(2);await expect(page.locator('.video-overlay')).toBeVisible();expect(f.deletes.every(body=>typeof body?.position_s==='number'&&body.duration_s>0)).toBe(true);
  await recovery.getByRole('button',{name:ro?'Înapoi fără salvare':'Leave without saving',exact:true}).tap();await expect(page.locator('.video-overlay')).toHaveCount(0);expect(f.deletes).toHaveLength(3);expect(f.deletes[2]).toBeUndefined();expect(f.otherWrites).toEqual([]);await expect(page.locator('.media-library')).toBeVisible();await page.screenshot({path:info.outputPath('discard-returns-to-library.png')});
 });
 test(`unreachable cleanup requires a second explicit local leave confirmation ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,true),recovery=page.locator('.video-progress-error');
  await expect(page.getByRole('button',{name:ro?'Ieși oricum':'Leave anyway',exact:true})).toHaveCount(0);
  await recovery.getByRole('button',{name:ro?'Înapoi fără salvare':'Leave without saving',exact:true}).tap();await expect(recovery).toContainText(ro?'Hubul nu a confirmat':'The hub did not confirm');await expect(page.locator('.video-overlay')).toBeVisible();expect(f.deletes[1]).toBeUndefined();
  await recovery.getByRole('button',{name:ro?'Rămâi aici':'Stay here',exact:true}).tap();await expect(recovery.getByRole('button',{name:ro?'Salvează și închide':'Save and close',exact:true})).toBeVisible();await expect(page.locator('.video-overlay')).toBeVisible();
  await recovery.getByRole('button',{name:ro?'Înapoi fără salvare':'Leave without saving',exact:true}).tap();await expect(recovery.getByRole('button',{name:ro?'Ieși oricum':'Leave anyway',exact:true})).toBeVisible();const before=f.deletes.length;
  await recovery.getByRole('button',{name:ro?'Ieși oricum':'Leave anyway',exact:true}).tap();await expect(page.locator('.video-overlay')).toHaveCount(0);expect(f.deletes).toHaveLength(before);expect(f.otherWrites).toEqual([]);await page.locator('.main-nav button').nth(0).tap();await expect(page.locator('.ambient-home')).toBeVisible();
 });
}
