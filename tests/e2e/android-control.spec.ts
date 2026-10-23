import {openSettingsSection} from './settings-navigation';
import {expect,test} from '@playwright/test';
import {settingsFixture} from './settings-fixture';

for(const theme of ['ink','night'] as const){
 async function fixture(page:any,ro:boolean){
  const f=await settingsFixture(page,ro?'ro':'en',theme);
  f.state.androidControl={available:true,enabled:true,pending:[],devices:[{deviceId:'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',name:'Samsung Galaxy Note10'}]};
  const writes:any[]=[],fail={write:false,read:false};
  await page.route('**/api/state',async(route:any)=>{await route.fulfill(fail.read?{status:503,json:{error:'backend_unavailable'}}:{json:f.state});});
  await page.route('**/api/android-control**',async(route:any)=>{const request=route.request(),path=new URL(request.url()).pathname,body=request.postData()?request.postDataJSON():undefined;writes.push({path,method:request.method(),body});if(fail.write){await route.fulfill({status:503,json:{error:'remote_unavailable'}});return;}
   if(path.endsWith('/pairing'))f.state.androidControl.pending=f.state.androidControl.pending.filter((p:any)=>p.requestId!==body.requestId);
   else if(request.method()==='PATCH')f.state.androidControl.enabled=body.enabled;
   else if(request.method()==='DELETE')f.state.androidControl.devices=[];
   await route.fulfill({json:f.state.androidControl});
  });
  await page.clock.runFor(2100);return {...f,writes,fail};
 }
 test(`${theme}: physical approval shows phone name and explicit Yes or No`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro);
  f.state.androidControl.pending=[{requestId:'pending-a',name:'Samsung Galaxy S24 Ultra · Telefonul familiei',expiresIn:120}];
  await page.clock.runFor(2100);
  const dialog=page.getByRole('dialog',{name:ro?'Conectare Android PySH':'PySH Android connection'});
  await expect(dialog).toBeVisible();await expect(dialog).toContainText(f.state.androidControl.pending[0].name);
  await expect(dialog).toHaveCSS('opacity','1');
  await expect(page.locator('.android-pairing-card')).toHaveCSS('opacity','1');
  for(const label of [ro?'Da':'Yes',ro?'Nu':'No']){const box=await dialog.getByRole('button',{name:label,exact:true}).boundingBox();expect(box!.height).toBeGreaterThanOrEqual(48);expect(box!.y+box!.height).toBeLessThanOrEqual(480);}
  await page.screenshot({path:`.runtime/android-control-ui/pairing-${info.project.name}-${theme}.png`});
  await dialog.getByRole('button',{name:ro?'Nu':'No',exact:true}).tap();await expect(dialog).toBeHidden();
  expect(f.writes).toEqual([{path:'/api/android-control/pairing',method:'POST',body:{requestId:'pending-a',accept:false}}]);
  f.state.androidControl.pending=[{requestId:'pending-b',name:'Pixel 9',expiresIn:120}];await page.clock.runFor(2100);
  await dialog.getByRole('button',{name:ro?'Da':'Yes',exact:true}).tap();await expect(dialog).toBeHidden();
  expect(f.writes.at(-1).body).toEqual({requestId:'pending-b',accept:true});
 });
 test(`${theme}: menu enables service and revokes only the confirmed phone`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro);
  await openSettingsSection(page,'androidControl');
  await page.locator('.android-control-panel h2').scrollIntoViewIfNeeded();
  await expect(page.locator('.android-control-panel')).toContainText(ro?'Activ':'Active');
  const toggle=page.getByRole('button',{name:ro?'Activează Android App Control':'Enable Android App Control'});
  await toggle.tap();await expect(toggle).toHaveAttribute('aria-pressed','false');await toggle.tap();await expect(toggle).toHaveAttribute('aria-pressed','true');
  const remove=page.getByRole('button',{name:ro?'Elimină accesul':'Remove access',exact:true});await remove.tap();expect(f.writes).toHaveLength(2);
  await page.getByRole('button',{name:ro?'Anulează':'Cancel',exact:true}).tap();expect(f.writes).toHaveLength(2);
  await remove.tap();await remove.tap();await expect(page.locator('.android-control-panel')).toContainText(ro?'Niciun telefon asociat încă.':'No paired phones yet.');
  expect(f.writes.at(-1).path).toBe('/api/android-control/devices/aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa');
  await page.locator('.android-control-panel h2').scrollIntoViewIfNeeded();
  await page.screenshot({path:`.runtime/android-control-ui/menu-${info.project.name}-${theme}.png`});
 });
 test(`${theme}: uncertain approval is checked without automatic replay or trapped actions`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro);
  f.state.androidControl.pending=[{requestId:'pending-a',name:'T'.repeat(80),expiresIn:120}];await page.clock.runFor(2100);
  const yes=page.getByRole('button',{name:ro?'Da':'Yes',exact:true});await expect(yes).toBeVisible();await page.clock.pauseAt(await page.evaluate(()=>Date.now()+1000));
  f.fail.write=true;await yes.tap();await expect(yes).toBeDisabled();
  const check=page.getByRole('button',{name:ro?'Verifică starea':'Check status',exact:true});const box=await check.boundingBox();expect(box!.y+box!.height).toBeLessThanOrEqual(480);
  await check.tap();await expect(yes).toBeEnabled();expect(f.writes).toHaveLength(1);
  f.fail.write=false;f.fail.read=true;await yes.tap();await expect(page.getByRole('dialog')).toBeVisible();await expect(check).toBeVisible();expect(f.writes).toHaveLength(2);
  f.fail.read=false;await check.tap();await expect(page.getByRole('dialog')).toBeHidden();expect(f.writes).toHaveLength(2);
 });
 test(`${theme}: expiry removes request and pending approval wakes ambient presentation`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro);
  await page.locator('.main-nav button').first().tap();await page.clock.runFor(31000);await expect(page.locator('.app')).toHaveAttribute('data-home-phase','ambient');
  f.state.androidControl.pending=[{requestId:'pending-a',name:'Pixel 9',expiresIn:120}];await page.clock.runFor(2100);
  await expect(page.getByRole('dialog')).toBeVisible();await expect(page.locator('.app')).toHaveAttribute('data-home-phase','interactive');
  f.state.androidControl.pending=[];await page.clock.runFor(2100);await expect(page.getByRole('dialog')).toBeHidden();expect(f.writes).toHaveLength(0);
 });
}
