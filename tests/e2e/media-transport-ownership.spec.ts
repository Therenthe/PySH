import {test,expect,type Page} from '@playwright/test';

const gate=()=>{let release!:()=>void;const promise=new Promise<void>(resolve=>{release=resolve;});return {promise,release};};
const renderSettled=(page:Page)=>page.evaluate(()=>new Promise<void>(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve()))));
const initialState=(ro:boolean,theme:string)=>({preferences:{language:ro?'ro':'en',theme,setupComplete:true,screensaverMinutes:0,nightEnabled:false},audio:{ready:true,volume:30},network:{},bluetooth:{devices:[],prompts:[]},player:{kind:'audio',state:'playing',url:'/Music/A.wav',title:'A.wav',canNext:true,canPrevious:true,position:1,duration:20},weather:{}});

for(const theme of ['ink','night'])test(`abandoned pending Next cannot revive Media error ${theme}`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro'),state=initialState(ro,theme),pending=gate(),commands:any[]=[];
 await page.route('**/api/**',async route=>{
  const endpoint=new URL(route.request().url()).pathname;
  if(endpoint==='/api/session')return route.fulfill({json:{token:'fixture'}});
  if(endpoint==='/api/state')return route.fulfill({json:state});
  if(endpoint==='/api/media')return route.fulfill({json:{path:'',items:[{name:'B.wav',path:'/Music/B.wav',kind:'audio'}]}});
  if(endpoint==='/api/player'){
   commands.push(route.request().postDataJSON());await pending.promise;
   return route.fulfill({status:409,json:{error:'media_not_found'}});
  }
  return route.fulfill({json:{ok:true}});
 });
 try{
  await page.goto('/');await page.locator('.main-nav button').nth(2).tap();
  const completed=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/player'&&r.request().method()==='POST');
  await page.getByRole('button',{name:ro?'Următor':'Next',exact:true}).tap();await expect.poll(()=>commands.length).toBe(1);
  await page.locator('.main-nav button').first().tap();await expect(page.locator('.ambient-home')).toBeVisible();
  await page.locator('.main-nav button').nth(2).tap();await expect(page.locator('.media-item')).toHaveText(/B\.wav/);
  pending.release();const response=await completed;await response.finished();await renderSettled(page);
  expect(response.status()).toBe(409);expect(commands).toEqual([{action:'next'}]);
  await expect(page.locator('.error-strip')).toHaveCount(0);await expect(page.locator('.media-error-filename')).toHaveCount(0);
  await expect(page.locator('.media-item')).toBeEnabled();await expect(page.locator('.local-audio-bar')).toContainText('A.wav');
 }finally{pending.release();}
});

for(const theme of ['ink','night'])test(`pending selection yields recovery ownership to Next ${theme}`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro'),state=initialState(ro,theme),selection=gate(),transport=gate(),plays:any[]=[],commands:any[]=[];
 await page.route('**/api/**',async route=>{
  const endpoint=new URL(route.request().url()).pathname;
  if(endpoint==='/api/session')return route.fulfill({json:{token:'fixture'}});
  if(endpoint==='/api/state')return route.fulfill({json:state});
  if(endpoint==='/api/media')return route.fulfill({json:{path:'',items:[{name:'B.wav',path:'/Music/B.wav',kind:'audio'}]}});
  if(endpoint==='/api/play'){
   plays.push(route.request().postDataJSON());await selection.promise;
   return route.fulfill({status:409,json:{error:'media_not_found'}});
  }
  if(endpoint==='/api/player'){
   commands.push(route.request().postDataJSON());
   if(commands.length===1){await transport.promise;return route.fulfill({status:409,json:{error:'media_not_found'}});}
   return route.fulfill({json:state.player});
  }
  return route.fulfill({json:{ok:true}});
 });
 try{
  await page.goto('/');await page.locator('.main-nav button').nth(2).tap();
  const selected=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/play'&&r.request().method()==='POST');
  await page.locator('.media-item').tap();await expect.poll(()=>plays.length).toBe(1);await expect(page.locator('.media-item')).toBeDisabled();
  const next=page.getByRole('button',{name:ro?'Următor':'Next',exact:true});await expect(next).toBeEnabled();await next.tap();
  // The new user intent supersedes B while playback commands remain serialized.
  expect(commands).toEqual([]);selection.release();const selectedResponse=await selected;await selectedResponse.finished();
  await expect.poll(()=>commands.length).toBe(1);await renderSettled(page);
  expect(selectedResponse.status()).toBe(409);await expect(page.locator('.error-strip')).toHaveCount(0);await expect(page.locator('.media-error-filename')).toHaveCount(0);
  const nextResponse=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/player'&&r.request().method()==='POST');transport.release();
  const failedNext=await nextResponse;await failedNext.finished();const error=page.locator('.error-strip');
  expect(failedNext.status()).toBe(409);await expect(error).toContainText(ro?'Fișierul sau dosarul media nu este disponibil.':'This media file or folder is unavailable.');
  await expect(error.locator('.media-error-filename')).toHaveCount(0);await expect(error).not.toContainText('B.wav');
  await error.getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true}).tap();await expect.poll(()=>commands.length).toBe(2);
  expect(commands).toEqual([{action:'next'},{action:'next'}]);expect(plays).toEqual([{source:'local',path:'/Music/B.wav',title:'B.wav'}]);
  await expect(error).toHaveCount(0);await expect(page.locator('.media-error-filename')).toHaveCount(0);
 }finally{selection.release();transport.release();}
});
