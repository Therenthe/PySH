import {expect,test,type Locator,type Page} from '@playwright/test';

// Private proposal: actual React prompt controls with adapter fixtures, not hardware proof.
const promptId='0123456789abcdef0123456789abcdef';
type Kind='confirmation'|'pin_code'|'passkey';
async function fixture(page:Page,ro:boolean,theme:string,kind:Kind,failFirst=false){
 const prompt={id:promptId,name:'Test speaker with a long but meaningful name',kind,...(kind==='confirmation'?{value:'001234'}:{})};
 const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,nightEnabled:false,screensaverMinutes:1},network:{},audio:{},player:{state:'idle'},weather:{},bluetooth:{available:true,powered:true,devices:[],prompts:[prompt]}};
 const replies:any[]=[];let release!:()=>void;const gate=new Promise<void>(resolve=>release=resolve);
 await page.route('**/api/**',async route=>{
  const req=route.request(),path=new URL(req.url()).pathname;
  if(path==='/api/bluetooth/reply'&&req.method()==='POST'){
   replies.push(req.postDataJSON());if(failFirst&&replies.length===1){await gate;await route.fulfill({status:503,json:{error:'bluetooth_unavailable'}});return;}
   state.bluetooth.prompts=[];await route.fulfill({json:{available:true,replied:true,id:promptId,error:null}});return;
  }
  await route.fulfill({json:path==='/api/session'?{token:'fixture'}:path==='/api/state'?state:{ok:true}});
 });
 await page.goto('/');const dialog=page.getByRole('dialog',{name:ro?'Solicitare de asociere':'Pairing request',exact:true});await expect(dialog).toBeVisible();return{state,replies,release,dialog};
}
async function hit(control:Locator){
 const b=await control.boundingBox();expect(b).not.toBeNull();expect(b!.width).toBeGreaterThanOrEqual(48);expect(b!.height).toBeGreaterThanOrEqual(48);expect(b!.x).toBeGreaterThanOrEqual(0);expect(b!.y).toBeGreaterThanOrEqual(0);expect(b!.x+b!.width).toBeLessThanOrEqual(800);expect(b!.y+b!.height).toBeLessThanOrEqual(480);
 expect(await control.evaluate(el=>{const b=el.getBoundingClientRect();return el.contains(document.elementFromPoint(b.x+b.width/2,b.y+b.height/2));})).toBe(true);
}
async function codeKeyboard(page:Page,dialog:Locator,ro:boolean,code='001234'){
 await dialog.locator('.pairing-input').tap();const keyboard=page.locator('.keyboard-card');await expect(keyboard).toBeVisible();const b=(await keyboard.boundingBox())!;expect(b.x).toBeGreaterThanOrEqual(0);expect(b.y).toBeGreaterThanOrEqual(0);expect(b.x+b.width).toBeLessThanOrEqual(800);expect(b.y+b.height).toBeLessThanOrEqual(480);
 for(const button of await keyboard.locator('.keys button,header button').all())await hit(button);
 for(const c of code)await keyboard.locator('.row-0').getByRole('button',{name:c,exact:true}).tap();await expect(keyboard.locator('.keyboard-value')).toHaveText(code);
 const apply=keyboard.locator('.final-row').getByRole('button',{name:ro?'Aplică':'Apply',exact:true});await hit(apply);return{keyboard,apply};
}

for(const theme of ['ink','night']){
 for(const kind of ['confirmation','pin_code','passkey'] as const)test(`Pairing ${theme} ${kind}: deliberate acceptance sends exact prompt and code`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,kind);
  if(kind==='confirmation'){await expect(f.dialog.locator('.pair-code')).toHaveText('001234');const accept=f.dialog.getByRole('button',{name:ro?'Acceptă':'Accept',exact:true});await hit(accept);await accept.tap();}
  else{const k=await codeKeyboard(page,f.dialog,ro);await page.screenshot({path:info.outputPath('pairing-code-keyboard.png')});await k.apply.tap();await expect(k.keyboard).toHaveCount(0);}
  await expect.poll(()=>f.replies.length).toBe(1);expect(f.replies).toEqual([{id:promptId,accept:true,...(kind==='confirmation'?{}:{value:'001234'})}]);await expect(f.dialog).toHaveCount(0);
 });

 test(`Pairing ${theme}: confirmation Reject does not accept or submit a displayed value`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,'confirmation'),reject=f.dialog.getByRole('button',{name:ro?'Refuză':'Reject',exact:true});await hit(reject);await reject.tap();await expect.poll(()=>f.replies.length).toBe(1);expect(f.replies).toEqual([{id:promptId,accept:false}]);await expect(f.dialog).toHaveCount(0);
 });

 for(const kind of ['pin_code','passkey'] as const)test(`Pairing ${theme} ${kind}: cancelling code entry preserves prompt without sending reply`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,kind),k=await codeKeyboard(page,f.dialog,ro);await k.keyboard.locator('header').getByRole('button',{name:ro?'Închide':'Close',exact:true}).tap();await expect(k.keyboard).toHaveCount(0);expect(f.replies).toEqual([]);await expect(f.dialog).toBeVisible();
  await f.dialog.getByRole('button',{name:ro?'Refuză':'Reject',exact:true}).tap();await expect.poll(()=>f.replies.length).toBe(1);expect(f.replies).toEqual([{id:promptId,accept:false}]);
 });

 for(const kind of ['confirmation','pin_code','passkey'] as const)test(`Pairing ${theme} ${kind}: failed reply stays inside prompt with exact retry and duplicate lock`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,kind,true);
  if(kind==='confirmation')await f.dialog.getByRole('button',{name:ro?'Acceptă':'Accept',exact:true}).tap();else{const k=await codeKeyboard(page,f.dialog,ro);await k.apply.tap();}
  await expect.poll(()=>f.replies.length).toBe(1);await expect(f.dialog.getByRole('status')).toBeVisible();const expected={id:promptId,accept:true,...(kind==='confirmation'?{}:{value:'001234'})};expect(f.replies).toEqual([expected]);
  // Every reply-producing control must be disabled while the adapter owns the operation.
  const controls=f.dialog.locator('.dialog-actions button,.pairing-input,header button');for(const button of await controls.all()){await expect(button).toBeDisabled();await button.evaluate((el:HTMLButtonElement)=>el.click());}expect(f.replies).toEqual([expected]);
  f.release();const alert=f.dialog.getByRole('alert');await expect(alert).toBeVisible();const retry=alert.getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true});await hit(retry);await page.screenshot({path:info.outputPath('pairing-reply-error.png')});await retry.tap();await expect.poll(()=>f.replies.length).toBe(2);expect(f.replies).toEqual([expected,expected]);await expect(f.dialog).toHaveCount(0);
 });

 for(const kind of ['pin_code','passkey'] as const)test(`Pairing ${theme} ${kind}: withdrawn prompt closes its keyboard and cannot send stale acceptance`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro');await page.clock.install();const f=await fixture(page,ro,theme,kind),k=await codeKeyboard(page,f.dialog,ro);f.state.bluetooth.prompts=[];await page.clock.runFor(2600);await expect(f.dialog).toHaveCount(0);await expect(k.keyboard).toHaveCount(0);expect(f.replies).toEqual([]);await page.clock.runFor(65000);expect(f.replies).toEqual([]);
 });
}
