import {expect,test,type Locator,type Page} from '@playwright/test';

// Real UI with controlled adapter replies; these tests do not establish speaker audibility.
async function audioFixture(page:Page,ro:boolean,theme:string,acceptedFirst=false){
 const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0},network:{},bluetooth:{devices:[],prompts:[]},player:{state:'idle'},weather:{},audio:{available:true,ready:true,volume:30,mute:false,outputs:[{id:11,name:'Built-in',description:'Built-in audio',active:true},{id:22,name:'Speaker',description:'Test Bluetooth speaker',bluetooth:true,active:false}]}};
 const writes:any[]=[];let release!:()=>void,failStateRead=false;const gate=new Promise<void>(resolve=>release=resolve);
 await page.route('**/api/**',async route=>{
  const req=route.request(),path=new URL(req.url()).pathname;
  if(path==='/api/audio'&&req.method()==='POST'){
   const body=req.postDataJSON();writes.push(body);
   if(writes.length===1){await gate;if(!acceptedFirst){await route.fulfill({status:503,json:{error:'audio_unavailable'}});return;}}
   if('output' in body)state.audio.outputs.forEach((o:any)=>o.active=o.id===body.output);
   if('volume' in body)state.audio.volume=body.volume;
   if('mute' in body)state.audio.mute=body.mute;
   if(acceptedFirst&&writes.length===1)failStateRead=true;await route.fulfill({json:{ok:true}});return;
  }
  if(path==='/api/state'&&failStateRead){failStateRead=false;await route.fulfill({status:503,json:{error:'backend_unavailable'}});return;}
  await route.fulfill({json:path==='/api/session'?{token:'fixture'}:path==='/api/state'?state:{ok:true}});
 });
 await page.goto('/');await page.locator('.rail-bottom button').last().tap();
 const dialog=page.getByRole('dialog',{name:ro?'Audio':'Audio',exact:true});await expect(dialog).toBeVisible();
 return {state,writes,release,dialog};
}

async function pendingLocked(dialog:Locator,writes:any[]){
 await expect(dialog.getByRole('status')).toBeVisible();
 const controls=dialog.locator('.modal-volume input,.modal-volume button,.modal-list button');
 expect(await controls.count()).toBeGreaterThanOrEqual(4);
 for(const control of await controls.all())await expect(control).toBeDisabled();
 // DOM click bypasses Playwright's disabled check but must not issue another mutation.
 for(const button of await dialog.locator('.modal-volume button,.modal-list button').all())await button.evaluate((el:HTMLButtonElement)=>el.click());
 expect(writes).toHaveLength(1);
}

async function hittable(control:Locator){
 const b=(await control.boundingBox())!;expect(b).not.toBeNull();expect(b.width).toBeGreaterThanOrEqual(48);expect(b.height).toBeGreaterThanOrEqual(48);
 expect(b.x).toBeGreaterThanOrEqual(0);expect(b.y).toBeGreaterThanOrEqual(0);expect(b.x+b.width).toBeLessThanOrEqual(800);expect(b.y+b.height).toBeLessThanOrEqual(480);
 expect(await control.evaluate(el=>{const b=el.getBoundingClientRect();return el.contains(document.elementFromPoint(b.x+b.width/2,b.y+b.height/2));})).toBe(true);
}

for(const theme of ['ink','night']){
 test(`Audio ${theme}: failed output remains recoverable inside dialog and retries exact ID`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await audioFixture(page,ro,theme),speaker=f.dialog.getByRole('button').filter({hasText:'Test Bluetooth speaker'}),builtin=f.dialog.getByRole('button').filter({hasText:'Built-in audio'});
  await hittable(speaker);await speaker.tap();await expect.poll(()=>f.writes.length).toBe(1);expect(f.writes[0]).toEqual({output:22});
  await pendingLocked(f.dialog,f.writes);
  expect(f.state.audio.outputs.find((o:any)=>o.active).id).toBe(11);await expect(builtin.locator('svg')).toHaveCount(2);await expect(speaker.locator('svg')).toHaveCount(1);
  f.release();const alert=f.dialog.getByRole('alert');await expect(alert).toBeVisible();await expect(alert).toContainText(ro?'audio':'Audio');const retry=alert.getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true});await hittable(retry);
  await page.screenshot({path:info.outputPath('audio-output-error.png')});expect(f.writes).toHaveLength(1);await retry.tap();await expect.poll(()=>f.writes.length).toBe(2);expect(f.writes[1]).toEqual({output:22});
  await expect(alert).toHaveCount(0);await expect.poll(()=>f.state.audio.outputs.find((o:any)=>o.active).id).toBe(22);await expect(speaker.locator('svg')).toHaveCount(2);await expect(builtin.locator('svg')).toHaveCount(1);
 });

 test(`Audio ${theme}: accepted output plus failed state read retries status without replaying POST`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await audioFixture(page,ro,theme,true),speaker=f.dialog.getByRole('button').filter({hasText:'Test Bluetooth speaker'});
  await speaker.tap();await expect.poll(()=>f.writes.length).toBe(1);await pendingLocked(f.dialog,f.writes);f.release();
  const alert=f.dialog.getByRole('alert');await expect(alert).toBeVisible();expect(f.writes).toEqual([{output:22}]);
  const retry=alert.getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true});await hittable(retry);await retry.tap();await expect(alert).toHaveCount(0);expect(f.writes).toEqual([{output:22}]);await expect(speaker.locator('svg')).toHaveCount(2);
 });

 test(`Audio ${theme}: disappearance updates open dialog without selecting another output`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro');await page.clock.install();const f=await audioFixture(page,ro,theme);
  f.state.audio.outputs=[];f.state.audio.ready=false;await page.clock.runFor(2600);
  await expect(f.dialog.getByText(ro?'Nicio ieșire audio disponibilă':'No audio output available',{exact:true})).toBeVisible();await expect(f.dialog.locator('.network-row')).toHaveCount(0);expect(f.writes).toEqual([]);
  const close=f.dialog.getByRole('button',{name:ro?'Închide':'Close',exact:true});await hittable(close);await close.tap();await expect(f.dialog).toHaveCount(0);
 });

 for(const action of ['volume','mute'] as const)test(`Audio ${theme}: ${action} failure keeps actual state and inline retry repeats intent`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await audioFixture(page,ro,theme);
  if(action==='mute')await f.dialog.getByRole('button',{name:ro?'Fără sunet':'Mute',exact:true}).tap();
  else{const slider=f.dialog.getByRole('slider',{name:ro?'Volum':'Volume',exact:true}),b=(await slider.boundingBox())!;await hittable(slider);await slider.tap({position:{x:b.width*.65,y:b.height*.5}});}
  await expect.poll(()=>f.writes.length).toBe(1);const failed={...f.writes[0]};if(action==='mute')expect(failed).toEqual({mute:true});else expect(failed.volume).toBeGreaterThan(50);
  await pendingLocked(f.dialog,f.writes);
  expect(f.state.audio.volume).toBe(30);expect(f.state.audio.mute).toBe(false);f.release();const alert=f.dialog.getByRole('alert');await expect(alert).toBeVisible();
  const retry=alert.getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true});await hittable(retry);await page.screenshot({path:info.outputPath(`audio-${action}-error.png`)});await retry.tap();await expect.poll(()=>f.writes.length).toBe(2);expect(f.writes[1]).toEqual(failed);await expect(alert).toHaveCount(0);
  if(action==='mute')await expect(f.dialog.getByRole('button',{name:ro?'Activează sunetul':'Unmute',exact:true})).toBeVisible();else await expect(f.dialog.getByRole('slider')).toHaveValue(String(failed.volume));
 });

 test(`Audio ${theme}: volume drag previews without POST and commits only final clamped value`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await audioFixture(page,ro,theme),slider=f.dialog.getByRole('slider'),b=(await slider.boundingBox())!;
  await page.mouse.move(b.x+b.width*.2,b.y+b.height/2);await page.mouse.down();await page.mouse.move(b.x+b.width*.7,b.y+b.height/2,{steps:12});await expect(slider).toHaveValue('70');expect(f.writes).toEqual([]);expect(f.state.audio.volume).toBe(30);
  await page.mouse.move(b.x+b.width+20,b.y+b.height/2,{steps:6});await expect(slider).toHaveValue('100');expect(f.writes).toEqual([]);await page.mouse.up();await expect.poll(()=>f.writes.length).toBe(1);expect(f.writes).toEqual([{volume:100}]);await pendingLocked(f.dialog,f.writes);f.release();await expect(f.dialog.getByRole('alert')).toBeVisible();
 });

 for(const cancellation of ['pointercancel','blur'] as const)test(`Audio ${theme}: cancelled volume drag ${cancellation} never commits`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await audioFixture(page,ro,theme),slider=f.dialog.getByRole('slider'),b=(await slider.boundingBox())!;
  await page.mouse.move(b.x+b.width*.3,b.y+b.height/2);await page.mouse.down();await page.mouse.move(b.x+b.width*.8,b.y+b.height/2,{steps:10});await expect(slider).toHaveValue('80');expect(f.writes).toEqual([]);
  if(cancellation==='pointercancel')await slider.dispatchEvent('pointercancel',{pointerId:1,pointerType:'mouse',isPrimary:true});else await page.evaluate(()=>window.dispatchEvent(new Event('blur')));
  await expect(slider).toHaveValue('30');await page.mouse.up();expect(f.writes).toEqual([]);expect(f.state.audio.volume).toBe(30);await expect(slider).toBeEnabled();
 });

 test(`Audio ${theme}: keyboard volume sends one value and pending ignores a second key`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await audioFixture(page,ro,theme),slider=f.dialog.getByRole('slider');
  await slider.focus();await slider.press('ArrowRight');await expect.poll(()=>f.writes.length).toBe(1);expect(f.writes).toEqual([{volume:31}]);await pendingLocked(f.dialog,f.writes);await page.keyboard.press('ArrowRight');expect(f.writes).toEqual([{volume:31}]);f.release();await expect(f.dialog.getByRole('alert')).toBeVisible();
 });

 test(`Audio ${theme}: Settings held volume drag survives clock and state polling without remount`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro');await page.clock.install();const f=await audioFixture(page,ro,theme);
  await f.dialog.locator('header').getByRole('button',{name:ro?'Închide':'Close',exact:true}).tap();await page.locator('.main-nav button').nth(3).tap();await page.locator('.settings-tabs button').filter({hasText:ro?'Audio':'Audio'}).tap();
  const slider=page.locator('.settings-panel').getByRole('slider',{name:ro?'Volum':'Volume',exact:true}),node=(await slider.elementHandle())!,b=(await slider.boundingBox())!;
  await page.mouse.move(b.x+b.width*.3,b.y+b.height/2);await page.mouse.down();await page.mouse.move(b.x+b.width*.8,b.y+b.height/2,{steps:10});await expect(slider).toHaveValue('80');expect(await node.evaluate(el=>(el as HTMLInputElement).hasPointerCapture(1))).toBe(true);
  // Cross both the one-second clock tick and the 2.5-second state refresh while held.
  await page.clock.runFor(2700);expect(await node.evaluate(el=>el.isConnected)).toBe(true);expect(await slider.evaluate((el,old)=>el===old,node)).toBe(true);expect(await node.evaluate(el=>(el as HTMLInputElement).hasPointerCapture(1))).toBe(true);await expect(slider).toHaveValue('80');expect(f.state.audio.volume).toBe(30);expect(f.writes).toEqual([]);
  await page.mouse.up();await expect.poll(()=>f.writes.length).toBe(1);expect(f.writes).toEqual([{volume:80}]);f.release();await expect(page.locator('.settings-panel').getByRole('alert')).toBeVisible();
 });

 for(const accepted of [false,true])test(`Audio ${theme}: navigation retains ${accepted?'accepted status-check':'failed mutation'} recovery without changing retry ownership`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await audioFixture(page,ro,theme,accepted);
  await f.dialog.getByRole('button').filter({hasText:'Test Bluetooth speaker'}).tap();await expect.poll(()=>f.writes.length).toBe(1);await pendingLocked(f.dialog,f.writes);
  await f.dialog.locator('header').getByRole('button',{name:ro?'Închide':'Close',exact:true}).tap();await page.locator('.main-nav button').nth(1).tap();await expect(f.dialog).toHaveCount(0);await expect(page.locator('[data-recovery=audio][role=status]')).toBeVisible();f.release();
  const alert=page.locator('[data-recovery=audio][role=alert]');await expect(alert).toBeVisible();await expect(alert).toContainText('Test Bluetooth speaker');const retry=alert.getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true});await hittable(retry);await retry.tap();await expect(alert).toHaveCount(0);
  expect(f.writes).toEqual(accepted?[{output:22}]:[{output:22},{output:22}]);await page.locator('.rail-bottom button').last().tap();await expect(f.dialog.getByRole('button').filter({hasText:'Test Bluetooth speaker'}).locator('svg')).toHaveCount(2);
 });
}
