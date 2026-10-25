import {test,expect} from '@playwright/test';

// Safety prompts arrive through the same state poll as the appliance. These
// isolated fixtures never contact a speaker, change audio or save preferences.
test.use({timezoneId:'UTC'});
for(const theme of ['ink','night'])test(`city return ${theme}: withdrawn Bluetooth safety prompt restores the original Return control`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro'),now=new Date('2026-10-24T10:00:00Z');
 const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,visualizerStyle:'off',timezone:'Europe/Bucharest',location:{name:'București · Sector 5',latitude:44.4,longitude:26.1},homeCards:[],navigationCollapsed:false,navigationAutoHide:false,decorativeAircraft:false,decorativeLunarDust:false,favorites:[],shortcuts:[]},network:{available:true,state:'connected',active_type:'ethernet',connection:'Ethernet',devices:[]},bluetooth:{available:true,powered:true,devices:[],prompts:[]},audio:{available:true,ready:true,volume:23,mute:false,outputs:[]},player:{state:'playing',kind:'radio',url:'https://example.invalid/isolated-retained',station_name:'Retained radio',title:'Retained track'},weather:{timezone:'Europe/Bucharest',stale:false,current:{weather_code:0,is_day:1,temperature_c:14},daily:[],updated_at:now.toISOString(),alerts:{state:'available',updated_at:now.toISOString(),alerts:[]}}};
 const saved=JSON.stringify(state),actions:any[]=[],errors:string[]=[],external:string[]=[];
 let release!:()=>void;const held=new Promise<void>(resolve=>release=resolve);
 page.on('pageerror',error=>errors.push(String(error)));
 await page.route('**/*',async route=>{
  const request=route.request(),url=new URL(request.url());
  if(url.hostname!=='127.0.0.1'){external.push(url.origin);return route.abort();}
  if(url.pathname.startsWith('/api/')){
   if(request.method()!=='GET')actions.push({path:url.pathname,method:request.method(),body:request.postDataJSON()});
   return route.fulfill({json:url.pathname==='/api/state'?state:url.pathname==='/api/session'?{token:'isolated-city-return-focus'}:url.pathname==='/api/radio'?{stations:[]}:url.pathname==='/api/media'?{items:[],roots:[]}:{} });
  }
  if(/\/city-exit-.*\.webm$/.test(url.pathname)){await held;return route.abort('failed').catch(()=>{});}
  return route.continue();
 });
 try{
  await page.clock.install({time:now});await page.clock.pauseAt(now);await page.goto('/');await expect(page.locator('.ambient-home')).toBeVisible();
  // Enter between state polls: the next2500ms poll must precede the exit's
  // independent2500ms loading timeout, so the safety prompt really preempts it.
  await page.clock.runFor(800);
  await page.emulateMedia({reducedMotion:'reduce'});await page.locator('button.city-building-entry[data-destination=audio]').focus();await page.keyboard.press('Enter');await page.clock.runFor(100);
  const canonical=page.locator('.settings-panel[data-settings-section=audio] .panel-heading h2'),back=page.locator('.settings-back');
  await expect(canonical).toBeFocused();await page.emulateMedia({reducedMotion:'no-preference'});await back.focus();await page.keyboard.press('Enter');
  await expect(page.locator('.city-entry')).toHaveAttribute('data-direction','exit');await expect(page.locator('.city-entry')).toHaveAttribute('data-phase','loading');await expect(page.locator('.radio-entry-actions button').first()).toBeFocused();
  state.bluetooth.prompts=[{id:'isolated-return-confirmation',kind:'confirmation',name:'Isolated speaker',address:'00:00:00:00:00:01',value:'123456'}];
  await page.clock.runFor(2100);const prompt=page.getByRole('dialog',{name:ro?'Solicitare de asociere':'Pairing request',exact:true});
  await expect(prompt).toBeVisible();await expect(page.locator('.city-entry')).toHaveCount(0);expect(await prompt.evaluate(node=>node.contains(document.activeElement))).toBe(true);
  await page.screenshot({path:info.outputPath('bluetooth-preempts-return.png')});
  state.bluetooth.prompts=[];await page.clock.runFor(2100);await expect(prompt).toHaveCount(0);
  // Prompt removal and canonical focus restoration each schedule a real frame.
  await page.clock.runFor(100);await expect(canonical).toBeVisible();await expect(page.locator('.ambient-home')).toHaveCount(0);await expect(page.locator('.city-entry')).toHaveCount(0);
  expect(await page.locator('.main-area').evaluate(node=>(node as HTMLElement).inert)).toBe(false);
  expect(actions).toEqual([]);expect(errors).toEqual([]);expect(external).toEqual([]);expect(JSON.stringify(state)).toBe(saved);
  await page.screenshot({path:info.outputPath('bluetooth-withdrawn-canonical-return-focus.png')});await expect(back).toBeFocused();
  // No superseded load/stall timer may navigate after the safety prompt closes.
  await page.clock.runFor(6000);await expect(canonical).toBeVisible();await expect(back).toBeFocused();await expect(page.locator('.ambient-home')).toHaveCount(0);await expect(page.locator('.city-entry')).toHaveCount(0);
  expect(actions).toEqual([]);expect(errors).toEqual([]);expect(external).toEqual([]);expect(JSON.stringify(state)).toBe(saved);
 }finally{release();}
});

// Android approval must own focus without treating Escape as a pairing decision.
for(const theme of ['ink','night'])test(`city return ${theme}: Android safety prompt owns focus and restores the original Return control`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro'),now=new Date('2026-10-24T10:00:00Z');
 const state:any={androidControl:{available:true,enabled:true,pending:[],devices:[]},preferences:{language:ro?'ro':'en',theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,visualizerStyle:'off',timezone:'Europe/Bucharest',location:{name:'București · Sector 5',latitude:44.4,longitude:26.1},homeCards:[],navigationCollapsed:false,navigationAutoHide:false,decorativeAircraft:false,decorativeLunarDust:false,favorites:[],shortcuts:[]},network:{available:true,state:'connected',active_type:'ethernet',connection:'Ethernet',devices:[]},bluetooth:{available:true,powered:true,devices:[],prompts:[]},audio:{available:true,ready:true,volume:23,mute:false,outputs:[]},player:{state:'playing',kind:'radio',url:'https://example.invalid/isolated-retained',station_name:'Retained radio',title:'Retained track'},weather:{timezone:'Europe/Bucharest',stale:false,current:{weather_code:0,is_day:1,temperature_c:14},daily:[],updated_at:now.toISOString(),alerts:{state:'available',updated_at:now.toISOString(),alerts:[]}}};
 const saved=JSON.stringify(state),actions:any[]=[],errors:string[]=[],external:string[]=[];
 let release!:()=>void;const held=new Promise<void>(resolve=>release=resolve);
 page.on('pageerror',error=>errors.push(String(error)));
 await page.route('**/*',async route=>{
  const request=route.request(),url=new URL(request.url());
  if(url.hostname!=='127.0.0.1'){external.push(url.origin);return route.abort();}
  if(url.pathname.startsWith('/api/')){
   if(request.method()!=='GET')actions.push({path:url.pathname,method:request.method(),body:request.postDataJSON()});
   return route.fulfill({json:url.pathname==='/api/state'?state:url.pathname==='/api/session'?{token:'isolated-android-return-focus'}:url.pathname==='/api/radio'?{stations:[]}:url.pathname==='/api/media'?{items:[],roots:[]}:{} });
  }
  if(/\/city-exit-.*\.webm$/.test(url.pathname)){await held;return route.abort('failed').catch(()=>{});}
  return route.continue();
 });
 try{
  await page.clock.install({time:now});await page.clock.pauseAt(now);await page.goto('/');await expect(page.locator('.ambient-home')).toBeVisible();
  // Enter between state polls: the next2500ms poll must precede the exit's
  // independent2500ms loading timeout, so the safety prompt really preempts it.
  await page.clock.runFor(800);
  await page.emulateMedia({reducedMotion:'reduce'});await page.locator('button.city-building-entry[data-destination=audio]').focus();await page.keyboard.press('Enter');await page.clock.runFor(100);
  const canonical=page.locator('.settings-panel[data-settings-section=audio] .panel-heading h2'),back=page.locator('.settings-back');
  await expect(canonical).toBeFocused();await page.emulateMedia({reducedMotion:'no-preference'});await back.focus();await page.keyboard.press('Enter');
  await expect(page.locator('.city-entry')).toHaveAttribute('data-direction','exit');await expect(page.locator('.city-entry')).toHaveAttribute('data-phase','loading');await expect(page.locator('.radio-entry-actions button').first()).toBeFocused();
  state.androidControl.pending=[{requestId:'isolated-return-phone',name:'Isolated phone',expiresIn:60}];
  await page.clock.runFor(2100);const prompt=page.getByRole('dialog',{name:ro?'Conectare Android PySH':'PySH Android connection',exact:true});
  await expect(prompt).toBeVisible();await expect(page.locator('.city-entry')).toHaveCount(0);await page.clock.runFor(400);
  const decline=prompt.getByRole('button',{name:ro?'Nu':'No',exact:true}),approve=prompt.getByRole('button',{name:ro?'Da':'Yes',exact:true});
  await expect(decline).toBeFocused();expect(await page.locator('.main-area').evaluate(node=>(node as HTMLElement).inert)).toBe(true);
  await page.keyboard.press('Tab');await expect(approve).toBeFocused();await page.keyboard.press('Tab');await expect(decline).toBeFocused();await page.keyboard.press('Shift+Tab');await expect(approve).toBeFocused();
  await back.focus();await expect(approve).toBeFocused();await page.keyboard.press('Escape');await expect(prompt).toBeVisible();await expect(approve).toBeFocused();expect(actions).toEqual([]);
  await page.screenshot({path:info.outputPath('android-preempts-return.png')});
  state.androidControl.pending=[];await page.clock.runFor(2100);await expect(prompt).toHaveCount(0);
  // Prompt removal and canonical focus restoration each schedule a real frame.
  await page.clock.runFor(100);await expect(canonical).toBeVisible();await expect(page.locator('.ambient-home')).toHaveCount(0);await expect(page.locator('.city-entry')).toHaveCount(0);
  expect(await page.locator('.main-area').evaluate(node=>(node as HTMLElement).inert)).toBe(false);
  expect(actions).toEqual([]);expect(errors).toEqual([]);expect(external).toEqual([]);expect(JSON.stringify(state)).toBe(saved);
  await page.screenshot({path:info.outputPath('android-withdrawn-canonical-return-focus.png')});await expect(back).toBeFocused();
  // No superseded load/stall timer may navigate after the safety prompt closes.
  await page.clock.runFor(6000);await expect(canonical).toBeVisible();await expect(back).toBeFocused();await expect(page.locator('.ambient-home')).toHaveCount(0);await expect(page.locator('.city-entry')).toHaveCount(0);
  expect(actions).toEqual([]);expect(errors).toEqual([]);expect(external).toEqual([]);expect(JSON.stringify(state)).toBe(saved);
 }finally{release();}
});
