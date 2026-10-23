import {test,expect,type Page} from '@playwright/test';

async function fixture(page:Page,ro:boolean,theme:string,kind:'active'|'stale'|'unavailable'|'expired'){
 const now=new Date('2026-10-23T18:00:00Z');
 const report={state:kind==='active'||kind==='expired'?'available':kind,updated_at:now.toISOString(),alerts:[{id:'isolated-fixture',event:'Heavy rain',headline:ro?'Avertizare de ploi abundente':'Heavy rain warning',description:ro?'Acesta este un scenariu izolat de test, nu o avertizare reală.':'This is an isolated test scenario, not a real warning.',severity:'severe',onset:'2026-10-23T17:00:00Z',expires:kind==='expired'?'2026-10-23T17:59:00Z':'2026-10-23T20:00:00Z',provider:'Fixture ANM',source:'Fixture Meteoalarm',hazard:'flood'}]};
 const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,visualizerStyle:'off',timezone:'Europe/Bucharest',homeCards:['weather','forecast'],favorites:[],shortcuts:[],location:{name:'București · Sector 5',latitude:44.4,longitude:26.1}},player:{state:'idle'},network:{available:true,state:'connected'},bluetooth:{available:true,powered:false,devices:[],prompts:[]},audio:{available:true,ready:true,outputs:[]},weather:{current:{weather_code:63,is_day:0,temperature_c:14},daily:[],updated_at:now.toISOString(),alerts:report}};
 await page.route('**/api/**',async route=>{const path=new URL(route.request().url()).pathname;if(path==='/api/preferences'){Object.assign(state.preferences,route.request().postDataJSON());return route.fulfill({json:state.preferences});}await route.fulfill({json:path==='/api/state'?state:{token:'isolated-alert-fixture'}})});
 await page.clock.install({time:now});await page.goto('/');await expect(page.locator('.home-weather')).toBeVisible();return {state,report};
}

for(const theme of ['ink','night'])test(`sourced active warning remains accessible when weather folds, fits 800x480 and is absent during Arrange ${theme}`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro');await fixture(page,ro,theme,'active');
 const notice=page.getByRole('button',{name:ro?'Avertizări meteo':'Weather alerts',exact:true});
 await expect(notice).toBeVisible();await notice.tap();const dialog=page.getByRole('dialog');
 await expect(dialog).toBeVisible();await expect(dialog).toContainText('Fixture ANM');await expect(dialog).toContainText('Fixture Meteoalarm');await expect(dialog).toContainText(ro?'Până la':'Until');
 const box=await dialog.boundingBox();expect(box!.x).toBeGreaterThanOrEqual(0);expect(box!.y).toBeGreaterThanOrEqual(0);expect(box!.x+box!.width).toBeLessThanOrEqual(800);expect(box!.y+box!.height).toBeLessThanOrEqual(480);
 await expect(dialog.locator('a')).toHaveCount(0);
 await page.screenshot({path:info.outputPath(`warning-${theme}.png`)});
 await dialog.getByRole('button',{name:ro?'Închide':'Close',exact:true}).tap();await expect(dialog).toHaveCount(0);
 await page.clock.runFor(16000);await expect(page.locator('.home-weather')).toHaveClass(/card-compact/);await expect(notice).toBeVisible();
 const geometry=await page.locator('.weather-top').evaluate(header=>{const rect=header.getBoundingClientRect();return [...header.querySelectorAll('button')].map(button=>{const b=button.getBoundingClientRect();return {w:b.width,h:b.height,inside:b.left>=rect.left&&b.right<=rect.right+.1};});});
 expect(geometry.every(item=>item.w>=48&&item.h>=48&&item.inside)).toBeTruthy();
 await page.locator('.main-nav button').nth(3).tap();await page.locator('.settings-tabs button').filter({hasText:ro?'Acasă':'Home'}).tap();
 await page.getByRole('button',{name:ro?'Aranjează Acasă':'Arrange Home',exact:true}).tap();
 await expect(page.locator('[data-layout-editing=true]')).toBeVisible();await expect(page.locator('.weather-alert-notice')).toHaveCount(0);
});

for(const kind of ['stale','unavailable','expired'] as const)test(`warning data ${kind} never becomes a current hazard`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro');await fixture(page,ro,'night',kind);
 await expect(page.locator('.weather-alert-notice.has-alerts')).toHaveCount(0);
 if(kind==='expired'){await expect(page.locator('.weather-alert-notice')).toHaveCount(0);return;}
 const notice=page.getByRole('button',{name:ro?'Avertizări indisponibile':'Alerts unavailable'});await notice.tap();await expect(page.getByRole('dialog')).toContainText(kind==='stale'?(ro?'expirate':'out of date'):(ro?'nu este disponibil':'unavailable'));
 await page.keyboard.press('Escape');await expect(page.getByRole('dialog')).toHaveCount(0);
 await page.clock.runFor(16000);await expect(page.locator('.weather-alert-notice')).toHaveCount(0);
});

test('alert eligibility rejects missing sources, future onset, stale and expired data including simulated extreme hazards',async({page})=>{
 await page.route('**/alert-model-fixture.html',route=>route.fulfill({contentType:'text/html',body:'<main>Isolated warning model fixture</main>'}));await page.goto('/alert-model-fixture.html');
 const results=await page.evaluate(async()=>{
  const path='/src/weatherAlertModel.ts';const {currentWeatherAlerts}=await import(/* @vite-ignore */path);const now=new Date('2026-10-23T18:00:00Z');
  const base={id:'fixture',event:'Hazard',headline:'Isolated simulation',severity:'extreme',onset:'2026-10-23T17:00:00Z',expires:'2026-10-23T20:00:00Z',provider:'Test provider',source:'Test CAP'};
  return {valid:['tornado','flood','wind','snow','ice','heat','cold','thunderstorm'].map(hazard=>currentWeatherAlerts({state:'available',alerts:[{...base,hazard}]},now).length),invalid:[{...base,source:''},{...base,provider:''},{...base,onset:'2026-10-23T19:00:00Z'},{...base,expires:'2026-10-23T17:59:00Z'}].map(alert=>currentWeatherAlerts({state:'available',alerts:[alert]},now).length),stale:currentWeatherAlerts({state:'stale',alerts:[base]},now).length};
 });
 expect(results.valid).toEqual(Array(8).fill(1));expect(results.invalid).toEqual([0,0,0,0]);expect(results.stale).toBe(0);
});

for(const theme of ['ink','night'])for(const hazard of ['flood','tornado'])test(`explicit ${hazard} warning illustration is bounded, sourced and expires ${theme}`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,'active');
 f.report.alerts[0].hazard=hazard;f.report.alerts[0].severity='extreme';
 await page.clock.runFor(2500);const illustration=page.locator('.scene-warning-illustration');
 await expect(illustration).toHaveAttribute('data-warning-hazard',hazard);
 await expect(illustration).toContainText(ro?'Ilustrație avertizare':'Warning illustration');
 const images=await illustration.locator('img').evaluateAll(elements=>elements.map(element=>(element as HTMLImageElement).complete&&(element as HTMLImageElement).naturalWidth>0));expect(images.every(Boolean)).toBeTruthy();expect(images.length).toBeLessThanOrEqual(3);
 await page.screenshot({path:info.outputPath(`warning-illustration-${hazard}-${theme}.png`)});
 await page.getByRole('button',{name:ro?'Avertizări meteo':'Weather alerts',exact:true}).tap();await expect(page.getByRole('dialog')).toContainText(ro?'nu imagini live':'not live imagery');await page.keyboard.press('Escape');
 f.report.alerts[0].severity='moderate';await page.clock.runFor(2500);await expect(illustration).toHaveCount(0);
 f.report.alerts[0].severity='extreme';f.report.alerts[0].expires='2026-10-23T17:59:59Z';await page.clock.runFor(2500);await expect(illustration).toHaveCount(0);
});

test('verified local alert remains visible with incomplete coverage and uses a human source label',async({page},info)=>{
 const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,'night','active');
 Object.assign(f.report,{partial:true});f.report.alerts[0].source='https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-romania';await page.clock.runFor(2500);
 await page.getByRole('button',{name:ro?'Avertizări meteo':'Weather alerts',exact:true}).tap();
 const dialog=page.getByRole('dialog');await expect(dialog).toContainText(ro?'Unele avertizări nu au putut fi verificate':'Some warnings could not be verified');await expect(dialog).toContainText('Fixture ANM');await expect(dialog).toContainText(ro?'Avertizare oficială':'Official warning');await expect(dialog).not.toContainText('https://');
});

test('an expired warning closes its dialog and a later warning does not reopen it without an action',async({page},info)=>{
 const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,'night','active');
 const notice=page.getByRole('button',{name:ro?'Avertizări meteo':'Weather alerts',exact:true});
 await notice.tap();await expect(page.getByRole('dialog')).toBeVisible();
 f.report.alerts[0].expires='2026-10-23T17:59:59Z';await page.clock.runFor(2500);await expect(page.getByRole('dialog')).toHaveCount(0);
 f.report.alerts[0].id='second-isolated-fixture';f.report.alerts[0].expires='2026-10-23T20:00:00Z';await page.clock.runFor(2500);await expect(notice).toBeVisible();await expect(page.getByRole('dialog')).toHaveCount(0);
});
