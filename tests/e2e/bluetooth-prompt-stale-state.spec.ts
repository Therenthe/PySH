import {expect,test,type Page,type Request} from '@playwright/test';

// Synthetic UUID and code only. These cases
// specifically exercise real UI-issued GET merges returning out of order.
const id='0123456789abcdef0123456789abcdef';
type Origin='poll'|'bluetooth'|'audio';
function deferred(){let release!:()=>void;const promise=new Promise<void>(resolve=>release=resolve);return{promise,release};}
async function fixture(page:Page,ro:boolean,theme:string,origin:Origin,keyboard:boolean){
 await page.clock.install();
 const prompt={id,name:'Synthetic stale snapshot speaker',kind:keyboard?'pin_code':'confirmation',...(keyboard?{}:{value:'001234'})};
 const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,nightEnabled:false,screensaverMinutes:1,navigationCollapsed:false,navigationAutoHide:false},network:{},audio:{available:true,ready:true,volume:30,mute:false,outputs:[]},player:{state:'idle'},weather:{current:{temperature_c:13,weather_code:0,is_day:1},daily:[]},bluetooth:{available:true,powered:true,devices:[],prompts:origin==='poll'?[prompt]:[]}};
 const held=deferred(),captured=deferred(),replies:any[]=[];let arm=false,heldRequest:Request|undefined;
 await page.route('**/api/**',async route=>{
  const request=route.request(),path=new URL(request.url()).pathname;
  if(path==='/api/bluetooth/reply'&&request.method()==='POST'){
   const body=request.postDataJSON();replies.push(body);state.bluetooth.prompts=[];
   await route.fulfill({json:{available:true,replied:true,id:body.id,error:null}});return;
  }
  if((origin==='bluetooth'&&path==='/api/bluetooth/scan')||(origin==='audio'&&path==='/api/audio')){
   state.bluetooth.prompts=[prompt];arm=true;
   if(origin==='audio')Object.assign(state.audio,request.postDataJSON());
   await route.fulfill({json:{available:true,error:null}});return;
  }
  if(path==='/api/state'){
   const snapshot=JSON.parse(JSON.stringify(state));
   if(arm&&!heldRequest){arm=false;heldRequest=request;captured.release();await held.promise;}
   await route.fulfill({json:snapshot});return;
  }
  await route.fulfill({json:path==='/api/session'?{token:'fixture'}:{ok:true}});
 });
 await page.goto('/');
 const dialog=page.getByRole('dialog',{name:ro?'Solicitare de asociere':'Pairing request',exact:true});
 if(origin==='poll'){
  await expect(dialog).toBeVisible();arm=true;await page.clock.runFor(2600);
 }else{
  await expect(page.locator('.ambient-home')).toBeVisible();
  await page.locator('.rail-bottom .status-button').nth(origin==='bluetooth'?1:2).tap();
  const operationDialog=page.getByRole('dialog',{name:origin==='bluetooth'?'Bluetooth':'Audio',exact:true});
  await operationDialog.getByRole('button',{name:origin==='bluetooth'?(ro?'Scanează':'Scan nearby'):(ro?'Fără sunet':'Mute'),exact:true}).tap();
 }
 await captured.promise;
 state.weather.current.temperature_c=17;
 if(origin!=='poll'){await page.clock.runFor(2600);await expect(dialog).toBeVisible();}
 return{state,prompt,dialog,replies,async releaseAndSettle(){
  await expect(page.locator('.ambient-weather .temp')).toHaveText('17°');
  await page.evaluate(()=>{const w=window as any;w.__stalePromptResurrected=false;const sample=()=>{if(Array.from(document.querySelectorAll('[role=dialog]')).some(el=>['Pairing request','Solicitare de asociere'].includes(el.getAttribute('aria-label')||'')))w.__stalePromptResurrected=true;};w.__stalePromptObserver=new MutationObserver(sample);w.__stalePromptObserver.observe(document.documentElement,{subtree:true,childList:true,attributes:true});sample();});
  const responsePromise=page.waitForResponse(response=>response.request()===heldRequest);
  held.release();const response=await responsePromise;await response.finished();
  await page.evaluate(()=>new Promise<void>(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve()))));
  // Witness the held snapshot's React commit, not only HTTP completion.
  await expect(page.locator('.ambient-weather .temp')).toHaveText('13°');
  const resurrected=await page.evaluate(()=>{const w=window as any;w.__stalePromptObserver.disconnect();return w.__stalePromptResurrected;});
  expect(resurrected,'A withdrawn prompt must never reappear, even transiently').toBe(false);
 }};
}

for(const theme of ['ink','night'])for(const origin of ['poll','bluetooth','audio'] as const){
 test(`UI34 ${theme} late ${origin} GET cannot resurrect accepted UUID`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,origin,false);
  await f.dialog.getByRole('button',{name:ro?'Acceptă':'Accept',exact:true}).tap();
  await expect(f.dialog).toHaveCount(0);expect(f.replies).toEqual([{id,accept:true}]);
  await f.releaseAndSettle();await expect(f.dialog).toHaveCount(0);await expect(page.locator('.keyboard-card')).toHaveCount(0);
  expect(f.replies).toEqual([{id,accept:true}]);
 });
 test(`UI34 ${theme} late ${origin} GET cannot resurrect withdrawn code keyboard`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,origin,true);
  await f.dialog.locator('.pairing-input').tap();const keyboard=page.locator('.keyboard-card');await expect(keyboard).toBeVisible();
  for(const digit of '001234')await keyboard.locator('.row-0').getByRole('button',{name:digit,exact:true}).tap();
  f.state.bluetooth.prompts=[];await page.clock.runFor(2600);await expect(f.dialog).toHaveCount(0);await expect(keyboard).toHaveCount(0);
  await f.releaseAndSettle();await expect(f.dialog).toHaveCount(0);await expect(keyboard).toHaveCount(0);expect(f.replies).toHaveLength(0);
 });
}
