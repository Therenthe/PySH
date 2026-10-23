import {expect,test} from '@playwright/test';
import {settingsFixture} from './settings-fixture';

for(const theme of ['ink','night'] as const){
 async function fixture(page:any,ro:boolean){
  const f=await settingsFixture(page,ro?'ro':'en',theme);
  Object.assign(f.state.preferences,{screenBrightness:80,dailyStandbyEnabled:false,dailyStandbyTime:'23:00'});
  f.state.power={standby:false,brightness:{available:true,value:80},timer:{remainingSeconds:0,deadline:null},daily:{enabled:false,time:'23:00'}};
  f.state.remote={connected:true,count:1};
  const commands:any[]=[],fail={write:false,read:false};
  await page.route('**/api/state',async(route:any)=>{if(fail.read){await route.fulfill({status:503,json:{error:'backend_unavailable'}});return;}f.state.power.brightness.value=f.state.preferences.screenBrightness;f.state.power.daily={enabled:f.state.preferences.dailyStandbyEnabled,time:f.state.preferences.dailyStandbyTime};await route.fulfill({json:f.state});});
  await page.route('**/api/power**',async(route:any)=>{const path=new URL(route.request().url()).pathname,body=route.request().postDataJSON();commands.push({path,body});if(fail.write){await route.fulfill({status:409,json:{error:'standby_failed'}});return;}if(path==='/api/power')f.state.power.standby=body.standby;else f.state.power.timer={remainingSeconds:body.minutes*60,deadline:null};await route.fulfill({json:f.state.power});});
  await page.clock.runFor(2100);
  await expect(page.locator('.remote-presence')).toBeVisible();
  return {...f,commands,fail};
 }
 test(`${theme}: connected app icon precedes network and power touch-wakes without stray actions`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro);
  await page.locator('.main-nav button').first().tap();
  expect(await page.locator('.remote-presence').evaluate(e=>e.nextElementSibling?.matches('button.top-network'))).toBe(true);
  const power=page.getByRole('button',{name:ro?'Oprește PySH':'Turn off PySH',exact:true});
  const box=await power.boundingBox();expect(box!.width).toBeGreaterThanOrEqual(48);expect(box!.height).toBeGreaterThanOrEqual(48);
  await power.tap();await expect(page.getByRole('dialog',{name:ro?'Ecran și standby':'Display & standby'})).toBeVisible();
  await page.locator('.power-summary button').tap();await expect(page.locator('.standby-screen')).toBeVisible();
  await page.locator('.standby-screen').tap({position:{x:40,y:40}});await expect(page.locator('.standby-screen')).toBeHidden();
  expect(f.commands).toEqual([{path:'/api/power',body:{standby:true}},{path:'/api/power',body:{standby:false}}]);
  await expect(page.locator('.modal-scrim')).toBeHidden();
  f.state.remote={connected:false,count:0};await page.clock.runFor(2100);await expect(page.locator('.remote-presence')).toBeHidden();
 });
 test(`${theme}: brightness timer daily schedule save and cancellation with actual readback`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro);
  await page.locator('.settings-tabs button').filter({hasText:ro?'Ecran / standby':'Display / standby'}).tap();
  const slider=page.getByRole('slider',{name:ro?'Luminozitate ecran':'Screen brightness'});
  await slider.tap({position:{x:70,y:24}});expect(f.writes.at(-1).screenBrightness).toBeGreaterThan(0);expect(f.writes.at(-1).screenBrightness).toBeLessThan(80);
  await page.getByRole('button',{name:'30 min',exact:true}).tap();await expect(page.locator('.power-panel')).toContainText(ro?'Standby în 30 min':'Standby in 30 min');
  await page.getByRole('button',{name:ro?'Anulează temporizatorul':'Cancel timer'}).tap();await expect(page.locator('.power-panel')).toContainText(ro?'Fără temporizator':'No timer');
  await page.getByRole('button',{name:ro?'Oprire zilnică':'Daily turn off',exact:true}).tap();await expect(page.getByRole('button',{name:ro?'Oprire zilnică':'Daily turn off',exact:true})).toHaveAttribute('aria-pressed','true');
  await page.getByRole('button',{name:'23:00',exact:true}).tap();await expect(page.locator('.keyboard-card')).toBeVisible();
  for(let i=0;i<5;i++)await page.getByRole('button',{name:ro?'Șterge caracterul':'Delete character',exact:true}).tap();
  for(const key of ['2','2'])await page.locator('.key-row.row-0').getByRole('button',{name:key,exact:true}).tap();
  await page.getByRole('button',{name:ro?'Schimbă simbolurile tastaturii':'Change keyboard symbols'}).tap();
  await page.locator('.keys').getByRole('button',{name:':',exact:true}).tap();
  await page.getByRole('button',{name:ro?'Schimbă simbolurile tastaturii':'Change keyboard symbols'}).tap();
  for(const key of ['4','5'])await page.locator('.key-row.row-0').getByRole('button',{name:key,exact:true}).tap();
  await page.getByRole('button',{name:ro?'Aplică':'Apply',exact:true}).tap();await expect(page.getByRole('button',{name:'22:45',exact:true})).toBeVisible();
  expect(f.writes).toContainEqual({dailyStandbyTime:'22:45'});expect(f.writes).toContainEqual({dailyStandbyEnabled:true});
  expect(f.commands).toEqual([{path:'/api/power/timer',body:{minutes:30}},{path:'/api/power/timer',body:{minutes:0}}]);
  await page.screenshot({path:`.runtime/power-ui/${info.project.name}-${theme}.png`});
 });
 test(`${theme}: rejected writes and uncertain state stay visible and never auto-repeat`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro);await page.locator('.settings-tabs button').filter({hasText:ro?'Ecran / standby':'Display / standby'}).tap();
  f.failKeys.add('screenBrightness');await page.getByRole('slider').tap({position:{x:70,y:24}});await expect(page.locator('.power-feedback')).toBeVisible();expect(f.state.preferences.screenBrightness).toBe(80);
  f.fail.write=true;await page.getByRole('button',{name:'30 min',exact:true}).tap();await expect(page.locator('.power-feedback')).toBeVisible();expect(f.state.power.timer.remainingSeconds).toBe(0);
  f.fail.write=false;f.fail.read=true;await page.getByRole('button',{name:'60 min',exact:true}).tap();await expect(page.locator('.power-feedback')).toBeVisible();
  f.fail.read=false;await page.getByRole('button',{name:ro?'Verifică starea':'Check status'}).tap();await expect(page.locator('.power-feedback')).toBeHidden();expect(f.commands).toHaveLength(2);
  f.state.power.brightness.available=false;await page.clock.runFor(2100);await expect(page.getByRole('slider')).toBeDisabled();
 });
}
