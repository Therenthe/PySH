import {test, expect, type Page} from '@playwright/test';

// Deliberately keep the browser in UTC while the selected clock is Bucharest.
// Otherwise a browser-local date comparison could conceal the midnight defect.
test.use({timezoneId:'UTC'});

async function fixture(page:Page,language:'en'|'ro',theme:string,instant:string,isDay:number,stale=false){
 const state:any={
  preferences:{language,theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,
   visualizerStyle:'off',homeCards:['weather','forecast'],timezone:'Europe/Bucharest',
   location:{name:'București · Sector 5',latitude:44.4,longitude:26.1},
   decorativeAircraft:false,decorativeLunarDust:false,favorites:[],shortcuts:[]},
  network:{available:true,state:'connected',connection:'Ethernet',devices:[],saved:[]},
  bluetooth:{available:true,powered:true,devices:[],prompts:[]},
  audio:{available:true,ready:true,volume:30,mute:false,outputs:[]},
  player:{state:'playing',kind:'radio',station_name:'Retained radio',url:'https://example.invalid/radio'},
  weather:{available:true,stale,current:{temperature_c:13,feels_like_c:10,weather_code:0,is_day:isDay},
   updated_at:instant,daily:[{date:'2026-10-03',weather_code:0,max_c:22,min_c:11}]},
 };
 const writes:any[]=[];
 await page.route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(route.request().method()!=='GET')writes.push({path,body:route.request().postDataJSON()});
  await route.fulfill({json:path==='/api/session'?{token:'coherence-fixture'}:path==='/api/state'?state:{ok:true}});
 });
 // Pause before loading application code; only explicit runFor advances timers.
 await page.clock.install({time:new Date(Date.parse(instant)-1000)});
 await page.clock.pauseAt(new Date(instant));
 await page.goto('/');await expect(page.locator('.ambient-home')).toBeVisible();
 return {state,writes};
}

const currentIcon=(page:Page)=>page.locator('.home-weather .temp-row svg[data-weather-condition="clear"]');

for(const theme of ['ink','night']){
 test(`compact forecast: old cache is not Today, selected timezone midnight changes the same-day label in ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),language=ro?'ro':'en';
  const f=await fixture(page,language,theme,'2026-10-04T20:59:00Z',0);
  const card=page.locator('.ambient-forecast'),heading=card.locator('h2');
  const today=ro?'Astăzi':'Today',forecast=ro?'Prognoză 5 zile':'5-day forecast';
  await expect(card).toHaveAttribute('aria-expanded','true');
  await card.tap();await page.clock.runFor(350);
  await expect(card).toHaveClass(/card-compact/);await expect(card).toHaveAttribute('aria-expanded','false');
  await expect(card.locator('.forecast-day')).toHaveCount(1);
  await expect(heading).toHaveText(forecast);await expect(heading).not.toHaveText(today);
  await expect(card.locator('.forecast-day b')).toHaveText(ro?'sâm.':'Sat');
  await expect(card.locator('.forecast-day strong')).toHaveText('22°');
  await page.screenshot({path:info.outputPath(`compact-old-cache-${theme}.png`)});

  // A normal automatic state refresh supplies today's date, without a user
  // reopening the card or replacing the existing compact component.
  f.state.weather.daily=[{date:'2026-10-04',weather_code:0,max_c:23,min_c:12}];
  await page.clock.runFor(2600);
  await expect(card).toHaveClass(/card-compact/);await expect(card).toHaveAttribute('aria-expanded','false');
  await expect(heading).toHaveText(today);await expect(card.locator('.forecast-day b')).toHaveText(ro?'dum.':'Sun');
  await expect(card.locator('.forecast-day strong')).toHaveText('23°');

  // At21:00UTC Bucharest reaches5October, while the browser's UTC date remains
  //4October. Keep precisely the same provider cache and compact card.
  await page.clock.setSystemTime(new Date('2026-10-04T21:00:00Z'));
  await page.clock.runFor(1100);
  expect(await page.evaluate(()=>new Date().toISOString().slice(0,10))).toBe('2026-10-04');
  await expect(page.locator('.date-label')).toContainText(ro?/luni/i:/monday/i);
  await expect(card).toBeVisible();await expect(card).toHaveClass(/card-compact/);
  await expect(card).toHaveAttribute('aria-expanded','false');
  await expect(heading).toHaveText(forecast);await expect(heading).not.toHaveText(today);
  await expect(card.locator('.forecast-day b')).toHaveText(ro?'dum.':'Sun');
  await expect(card.locator('.forecast-day strong')).toHaveText('23°');
  expect(f.state.weather.daily[0].date).toBe('2026-10-04');expect(f.writes).toEqual([]);
  await page.screenshot({path:info.outputPath(`compact-after-local-midnight-${theme}.png`)});
 });

 for(const scenario of [
  {name:'actual day with held provider night',instant:'2026-10-04T10:00:00Z',provider:0,sky:'.sky-day',sun:true},
  {name:'actual night with held provider day',instant:'2026-10-04T23:00:00Z',provider:1,sky:'.sky-night',sun:false},
 ])test(`current weather icon follows ${scenario.name} in ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro?'ro':'en',theme,scenario.instant,scenario.provider);
  await expect(page.locator(scenario.sky)).toBeVisible();await expect(currentIcon(page)).toBeVisible();
  // A clear Sun has a visible disc and rays; the clear Moon is a crescent path.
  // Assert the actual rendered weather glyph, not only its condition label.
  await expect(currentIcon(page).locator('circle')).toHaveCount(scenario.sun?1:0);
  await expect(currentIcon(page).locator('path')).toHaveCount(1);
  if(scenario.sun)await expect(page.locator('.ambient-sun')).toBeVisible();
  else{await expect(page.locator('.ambient-sun')).toHaveCount(0);await expect(page.locator('.ambient-moon')).toBeVisible();}
  expect(f.state.weather.current.is_day).toBe(scenario.provider);
  await page.clock.runFor(2600); // another unchanged backend poll must not undo it
  await expect(currentIcon(page).locator('circle')).toHaveCount(scenario.sun?1:0);
  expect(f.writes).toEqual([]);
  await page.screenshot({path:info.outputPath(`current-icon-${scenario.sun?'day':'night'}-${theme}.png`)});
 });

 for(const scenario of [
  {name:'saved night during current day',instant:'2026-10-04T10:00:00Z',provider:0,sun:false},
  {name:'saved day during current night',instant:'2026-10-04T23:00:00Z',provider:1,sun:true},
 ])test(`stale weather retains ${scenario.name} icon in ${theme}`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro?'ro':'en',theme,scenario.instant,scenario.provider,true);
  await expect(page.locator('.sky-neutral')).toBeVisible();
  await expect(page.locator('.home-weather .stale-mark')).toHaveText(ro?'Se afișează ultima prognoză salvată':'Showing saved weather');
  await expect(currentIcon(page)).toBeVisible();
  await expect(currentIcon(page).locator('circle')).toHaveCount(scenario.sun?1:0);
  await expect(currentIcon(page).locator('path')).toHaveCount(1);
  await expect(page.locator('[data-celestial-body],.ambient-stars,.ambient-star-texture,.ambient-rain,.ambient-snow')).toHaveCount(0);
  await page.clock.runFor(2600);await expect(currentIcon(page).locator('circle')).toHaveCount(scenario.sun?1:0);
  expect(f.state.weather.current.is_day).toBe(scenario.provider);expect(f.writes).toEqual([]);
  await page.screenshot({path:info.outputPath(`cached-icon-${scenario.sun?'day':'night'}-${theme}.png`)});
 });
}
