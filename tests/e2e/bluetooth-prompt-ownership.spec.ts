import {expect,test,type Locator,type Page} from '@playwright/test';

// Private adapter fixtures only. All IDs, codes and device details below are synthetic.
const id='0123456789abcdef0123456789abcdef',replacementId='11111111111111111111111111111111';
type Kind='confirmation'|'pin_code'|'passkey';
function deferred(){let release!:()=>void;const promise=new Promise<void>(resolve=>release=resolve);return{promise,release};}
function prompt(kind:Kind='confirmation',promptId=id,name='Synthetic test speaker'){return{id:promptId,name,kind,...(kind==='confirmation'?{value:'001234'}:{})};}
async function fixture(page:Page,ro:boolean,theme:string,kind:Kind='confirmation',options:{gated?:boolean;error?:string;secondError?:string;shape?:Record<string,unknown>;cached?:boolean;stateFailure?:boolean;pair?:boolean}={}){
 await page.clock.install();
 const first=prompt(kind),state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,nightEnabled:false,screensaverMinutes:1,navigationCollapsed:false,navigationAutoHide:false},network:{},audio:{available:true,ready:true,volume:30,mute:false,outputs:[]},player:{state:'idle'},weather:{},bluetooth:{available:true,powered:true,devices:options.pair?[{address:'00:00:00:00:00:01',name:'Synthetic pairing speaker',paired:false,connected:false}]:[],prompts:options.pair?[]:[first]}};
 const replies:any[]=[],methods:{path:string;method:string}[]=[],gate=deferred(),pairGate=deferred();let stateReads=0,stateFailureActive=false;
 await page.route('**/api/**',async route=>{
  const request=route.request(),path=new URL(request.url()).pathname;methods.push({path,method:request.method()});
  if(path==='/api/bluetooth/reply'&&request.method()==='POST'){
   const body=request.postDataJSON();replies.push(body);const index=replies.length;
   if(index===1&&options.gated)await gate.promise;
   if(index===1&&options.error){await route.fulfill({status:options.error==='not_found'?404:503,json:{error:options.error}});return;}
   if(index===2&&options.secondError){await route.fulfill({status:503,json:{error:options.secondError}});return;}
   if(index===1&&options.shape){await route.fulfill({json:options.shape});return;}
   if(!options.cached)state.bluetooth.prompts=state.bluetooth.prompts.filter((p:any)=>p.id!==body.id);
   if(index===1&&options.stateFailure)stateFailureActive=true;
   await route.fulfill({json:{available:true,replied:true,id:body.id,error:null}});return;
  }
  if(path==='/api/bluetooth/action'&&request.method()==='POST'&&options.pair){state.bluetooth.prompts=[first];await pairGate.promise;await route.fulfill({json:{available:true,error:null}});return;}
  if(path==='/api/state'){stateReads++;if(stateFailureActive){await route.fulfill({status:503,json:{error:'backend_unavailable'}});return;}await route.fulfill({json:state});return;}
  await route.fulfill({json:path==='/api/session'?{token:'fixture'}:{ok:true}});
 });
 await page.goto('/');const dialog=page.getByRole('dialog',{name:ro?'Solicitare de asociere':'Pairing request',exact:true});
 if(!options.pair)await expect(dialog).toBeVisible();else await expect(page.locator('.ambient-home')).toBeVisible();
 return{state,replies,methods,gate,pairGate,dialog,reads:()=>stateReads,stateFailureOff:()=>{stateFailureActive=false;}};
}
async function hit(button:Locator){const box=await button.boundingBox();expect(box).not.toBeNull();expect(box!.width).toBeGreaterThanOrEqual(48);expect(box!.height).toBeGreaterThanOrEqual(48);expect(box!.x).toBeGreaterThanOrEqual(0);expect(box!.y).toBeGreaterThanOrEqual(0);expect(box!.x+box!.width).toBeLessThanOrEqual(800);expect(box!.y+box!.height).toBeLessThanOrEqual(480);expect(await button.evaluate(el=>{const r=el.getBoundingClientRect();return el.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2));})).toBe(true);}
async function codeEntry(page:Page,dialog:Locator,ro:boolean){await dialog.locator('.pairing-input').tap();const keyboard=page.locator('.keyboard-card');await expect(keyboard).toBeVisible();for(const digit of '001234')await keyboard.locator('.row-0').getByRole('button',{name:digit,exact:true}).tap();await expect(keyboard.locator('.keyboard-value')).toHaveText('001234');const apply=keyboard.locator('.final-row').getByRole('button',{name:ro?'Aplică':'Apply',exact:true});await hit(apply);return{keyboard,apply};}

for(const theme of ['ink','night']){
 for(const shape of [{available:true,replied:false,id,error:null},{available:true,replied:true,id:replacementId,error:null}])test(`UI34 ${theme} rejects invalid reply acknowledgement ${shape.replied?'foreign-id':'not-replied'}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,'confirmation',{shape});await f.dialog.getByRole('button',{name:ro?'Acceptă':'Accept',exact:true}).tap();
  const retry=f.dialog.getByRole('alert').getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true});await expect(retry).toBeVisible();await retry.tap();await expect.poll(()=>f.replies.length).toBe(2);expect(f.replies).toEqual([{id,accept:true},{id,accept:true}]);await expect(f.dialog).toHaveCount(0);
 });

 test(`UI34 ${theme} same-frame Accept Reject Close is one first-intent mutation`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,'confirmation',{gated:true});await f.dialog.evaluate(el=>{const buttons=el.querySelectorAll<HTMLButtonElement>('.dialog-actions button');buttons[1].click();buttons[1].click();buttons[0].click();el.querySelector<HTMLButtonElement>('header button')!.click();});
  await expect.poll(()=>f.replies.length).toBe(1);expect(f.replies).toEqual([{id,accept:true}]);await expect(f.dialog.getByRole('status')).toBeVisible();for(const button of await f.dialog.locator('.dialog-actions button,header button').all())await expect(button).toBeDisabled();f.gate.release();await expect(f.dialog).toHaveCount(0);
 });

 for(const kind of ['pin_code','passkey'] as const)test(`UI34 ${theme} ${kind} duplicate keyboard and Apply cannot lose first code intent`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,kind,{gated:true});await f.dialog.locator('.pairing-input').evaluate((el:HTMLButtonElement)=>{el.click();el.click();});const keyboard=page.locator('.keyboard-card');await expect(keyboard).toHaveCount(1);
  for(const digit of '001234')await keyboard.locator('.row-0').getByRole('button',{name:digit,exact:true}).tap();await keyboard.locator('.final-row').getByRole('button',{name:ro?'Aplică':'Apply',exact:true}).evaluate((el:HTMLButtonElement)=>{el.click();el.click();document.querySelector<HTMLButtonElement>('.dialog-actions .outline')!.click();});
  await expect.poll(()=>f.replies.length).toBe(1);expect(f.replies).toEqual([{id,accept:true,value:'001234'}]);await expect(keyboard).toHaveCount(0);f.gate.release();await expect(f.dialog).toHaveCount(0);
 });

 test(`UI34 ${theme} accepted reply failed state checks retry GET only`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,'pin_code',{cached:true,stateFailure:true}),k=await codeEntry(page,f.dialog,ro);await k.apply.tap();
  const alert=f.dialog.getByRole('alert');await expect(alert).toContainText(ro?'Răspunsul a fost acceptat':'Reply accepted');await expect(alert).not.toContainText('001234');expect(f.replies).toEqual([{id,accept:true,value:'001234'}]);const retry=alert.getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true});await hit(retry);const reads=f.reads();f.state.bluetooth.prompts=[];f.stateFailureOff();await retry.tap();await expect(f.dialog).toHaveCount(0);expect(f.reads()).toBeGreaterThan(reads);expect(f.replies).toHaveLength(1);
 });

 test(`UI34 ${theme} ordinary poll recovers accepted failed state without resending`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,'confirmation',{cached:true,stateFailure:true});await f.dialog.getByRole('button',{name:ro?'Acceptă':'Accept',exact:true}).tap();await expect(f.dialog.getByRole('alert')).toBeVisible();f.state.bluetooth.prompts=[];f.stateFailureOff();await page.clock.runFor(2600);await expect(f.dialog).toHaveCount(0);expect(f.replies).toEqual([{id,accept:true}]);
 });

 test(`UI34 ${theme} accepted cached prompt stays inert until authoritative withdrawal`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,'confirmation',{cached:true});await f.dialog.getByRole('button',{name:ro?'Acceptă':'Accept',exact:true}).tap();await expect(f.dialog.getByRole('status')).toContainText(ro?'Răspuns trimis':'Reply sent');await page.clock.runFor(2600);
  for(const button of await f.dialog.locator('.dialog-actions button,header button').all()){await expect(button).toBeDisabled();await button.evaluate((el:HTMLButtonElement)=>el.click());}expect(f.replies).toEqual([{id,accept:true}]);f.state.bluetooth.prompts=[];await page.clock.runFor(2600);await expect(f.dialog).toHaveCount(0);
 });

 for(const failed of [false,true])test(`UI34 ${theme} pending reply replacement ignores old ${failed?'failure':'acceptance'}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,'confirmation',{gated:true,...(failed?{error:'bluetooth_unavailable'}:{})});await f.dialog.getByRole('button',{name:ro?'Acceptă':'Accept',exact:true}).tap();await expect.poll(()=>f.replies.length).toBe(1);
  f.state.bluetooth.prompts=[prompt('confirmation',replacementId,'Synthetic replacement speaker')];await page.clock.runFor(2600);await expect(f.dialog).toContainText('Synthetic replacement speaker');const response=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/bluetooth/reply'&&r.request().postDataJSON().id===id);f.gate.release();await (await response).finished();await page.evaluate(()=>new Promise<void>(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve()))));await expect(f.dialog.getByRole('alert')).toHaveCount(0);await expect(page.locator('.error-strip')).toHaveCount(0);
  const accept=f.dialog.getByRole('button',{name:ro?'Acceptă':'Accept',exact:true});await expect(accept).toBeEnabled();await accept.tap();await expect.poll(()=>f.replies.length).toBe(2);expect(f.replies).toEqual([{id,accept:true},{id:replacementId,accept:true}]);await expect(f.dialog).toHaveCount(0);
 });

 for(const kind of ['pin_code','passkey'] as const)test(`UI34 ${theme} ${kind} replaced keyboard is gone and new lease accepts its own ID`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,kind),old=await codeEntry(page,f.dialog,ro);await old.apply.evaluate(el=>{(window as any).__syntheticOldPromptApply=el;});f.state.bluetooth.prompts=[prompt(kind,replacementId,'Synthetic replacement speaker')];await page.clock.runFor(2600);await expect(old.keyboard).toHaveCount(0);await expect(f.dialog).toContainText('Synthetic replacement speaker');await page.evaluate(()=>{(window as any).__syntheticOldPromptApply.click();delete (window as any).__syntheticOldPromptApply;});expect(f.replies).toHaveLength(0);
  const next=await codeEntry(page,f.dialog,ro);await next.apply.tap();await expect.poll(()=>f.replies.length).toBe(1);expect(f.replies).toEqual([{id:replacementId,accept:true,value:'001234'}]);
 });

 test(`UI34 ${theme} cancelled code entry can reopen with a clean independent keyboard lease`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,'pin_code'),old=await codeEntry(page,f.dialog,ro);await old.keyboard.locator('header').getByRole('button',{name:ro?'Închide':'Close',exact:true}).tap();await expect(old.keyboard).toHaveCount(0);expect(f.replies).toHaveLength(0);const next=await codeEntry(page,f.dialog,ro);await page.evaluate(()=>Promise.resolve());await expect(next.keyboard).toBeVisible();await next.apply.tap();await expect.poll(()=>f.replies.length).toBe(1);expect(f.replies).toEqual([{id,accept:true,value:'001234'}]);
 });

 test(`UI34 ${theme} withdrawn prompt cannot close a later unrelated search keyboard`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,'pin_code'),old=await codeEntry(page,f.dialog,ro);f.state.bluetooth.prompts=[];await page.clock.runFor(2600);await expect(old.keyboard).toHaveCount(0);await page.locator('.main-nav button').nth(1).tap();await page.locator('.radio-redesign .search-field').tap();await expect(page.locator('.keyboard-card')).toBeVisible();await page.clock.runFor(65000);await expect(page.locator('.keyboard-card')).toBeVisible();expect(f.replies).toHaveLength(0);await page.locator('.keyboard-card header').getByRole('button',{name:ro?'Închide':'Close',exact:true}).tap();await expect(page.locator('.radio-redesign')).toBeVisible();
 });

 test(`UI34 ${theme} withdrawn pending reply ignores late failure and releases Home idle guard`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,'confirmation',{gated:true,error:'bluetooth_unavailable'});await f.dialog.getByRole('button',{name:ro?'Acceptă':'Accept',exact:true}).tap();await expect.poll(()=>f.replies.length).toBe(1);f.state.bluetooth.prompts=[];await page.clock.runFor(2600);await expect(f.dialog).toHaveCount(0);const response=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/bluetooth/reply');f.gate.release();await (await response).finished();await page.evaluate(()=>new Promise<void>(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve()))));await expect(page.locator('.error-strip')).toHaveCount(0);await page.clock.runFor(31000);await expect(page.locator('.app')).toHaveAttribute('data-home-phase','ambient');expect(f.replies).toEqual([{id,accept:true}]);
 });

 test(`UI34 ${theme} failed code acceptance superseded by Reject retries only Reject`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,'pin_code',{error:'bluetooth_unavailable',secondError:'bluetooth_unavailable'}),k=await codeEntry(page,f.dialog,ro);await k.apply.tap();await expect(f.dialog.getByRole('alert')).toBeVisible();await f.dialog.getByRole('button',{name:ro?'Refuză':'Reject',exact:true}).tap();await expect.poll(()=>f.replies.length).toBe(2);const retry=f.dialog.getByRole('alert').getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true});await expect(retry).toBeVisible();await retry.tap();await expect.poll(()=>f.replies.length).toBe(3);expect(f.replies).toEqual([{id,accept:true,value:'001234'},{id,accept:false},{id,accept:false}]);await expect(f.dialog).toHaveCount(0);
 });

 test(`UI34 ${theme} failed Reject retries Reject without confirmation value`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,'confirmation',{error:'bluetooth_unavailable'});await f.dialog.getByRole('button',{name:ro?'Refuză':'Reject',exact:true}).tap();await f.dialog.getByRole('alert').getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true}).tap();await expect.poll(()=>f.replies.length).toBe(2);expect(f.replies).toEqual([{id,accept:false},{id,accept:false}]);await expect(f.dialog).toHaveCount(0);
 });

 test(`UI34 ${theme} backend not_found recovery refreshes state without another reply`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,'confirmation',{error:'not_found'});await f.dialog.getByRole('button',{name:ro?'Acceptă':'Accept',exact:true}).tap();const alert=f.dialog.getByRole('alert');await expect(alert).toContainText(ro?'Solicitarea nu mai este activă':'request is no longer active');const reads=f.reads();f.state.bluetooth.prompts=[];await alert.getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true}).tap();await expect(f.dialog).toHaveCount(0);expect(f.reads()).toBeGreaterThan(reads);expect(f.replies).toEqual([{id,accept:true}]);
 });

 test(`UI34 ${theme} pending device Pair does not disable its required prompt reply`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,'confirmation',{pair:true});if(await page.locator('.rail').getAttribute('aria-hidden')==='true')await page.locator('.navigation-toggle').tap();await page.locator('.rail-bottom .status-button').nth(1).tap();const bluetooth=page.getByRole('dialog',{name:'Bluetooth',exact:true});await bluetooth.locator('.device-row').getByRole('button',{name:ro?'Asociază':'Pair',exact:true}).tap();await page.clock.runFor(2600);await expect(f.dialog).toBeVisible();const accept=f.dialog.getByRole('button',{name:ro?'Acceptă':'Accept',exact:true});await expect(accept).toBeEnabled();await accept.tap();await expect.poll(()=>f.replies.length).toBe(1);expect(f.replies).toEqual([{id,accept:true}]);f.pairGate.release();await expect(f.dialog).toHaveCount(0);
 });
}
