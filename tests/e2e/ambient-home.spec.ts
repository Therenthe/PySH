import {test,expect} from '@playwright/test';
for(const signal of ['off','wave']) for(const theme of ['ink','night']) for(const scene of ['clear-day','clear-night','cloud-night','rain','snow','stale']) {
 test(`ambient home ${theme} ${scene} ${signal}: genuine weather scene and five forecast symbols`,async({page},info)=>{
  const language=info.project.name.endsWith('ro')?'ro':'en';
  const state={preferences:{language,theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,visualizerStyle:signal,lastStation:{name:'Radio România Actualități',url:'https://example.invalid/radio',favicon:'https://radio.example.org/logo.svg'},timezone:'Europe/Bucharest',location:{name:'București'},favorites:[],shortcuts:['radio','media']},network:{available:true,state:'connected',connection:'Ethernet',devices:[],saved:[]},bluetooth:{available:true,powered:true,devices:[],prompts:[]},audio:{available:true,ready:true,volume:20,mute:false,outputs:[]},player:{state:'playing',kind:'radio',station_name:'Radio România Actualități',title:'Artist · A distinct song title',url:'https://example.invalid/radio'},weather:{current:{temperature_c:13,feels_like_c:10,weather_code:scene==='rain'?63:scene==='snow'?73:scene==='cloud-night'?2:0,is_day:scene.endsWith('night')?0:1,wind_kmh:8},daily:Array.from({length:5},(_,i)=>({date:`2026-10-0${i+3}`,weather_code:[0,2,63,73,95][i],max_c:22-i,min_c:11-i})),updated_at:'2026-10-03T12:00:00Z',stale:scene==='stale',attribution:'Open-Meteo'}};
  await page.route('**/api/**',async route=>{const path=new URL(route.request().url()).pathname;await route.fulfill({json:path==='/api/session'?{token:'isolated-browser-fixture'}:path==='/api/state'?state:{ok:true}})});
  await page.route('https://radio.example.org/logo.svg',route=>route.fulfill({contentType:'image/svg+xml',body:'<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48"><rect width="48" height="48" fill="#67cba4"/></svg>'}));
  await page.clock.install();
  await page.goto('/');
  await expect(page.locator('.ambient-home')).toBeVisible();
  const headerBounds=await page.locator('.topbar').evaluate(header=>{const bounds=header.getBoundingClientRect();return [...header.querySelectorAll('.eyebrow,.date-label')].map(el=>el.getBoundingClientRect()).every(r=>r.top>=bounds.top&&r.bottom<=bounds.bottom&&r.left>=bounds.left&&r.right<=bounds.right);});
  expect(headerBounds).toBe(true);
  await expect(page.locator('.forecast-day')).toHaveCount(5);
  await expect(page.locator('.forecast-day svg')).toHaveCount(5);
  await expect(page.locator('.forecast-day strong')).toHaveCount(5);
  await expect(page.locator('.forecast-day i')).toHaveCount(5);
  await expect(page.locator('.playback-source')).toHaveText('Radio România Actualități');
  await expect(page.locator('.playback-metadata')).toHaveText('Artist · A distinct song title');
  await expect(page.locator('.home-clock-card,.clock-greeting')).toHaveCount(0);
  if(scene==='clear-night')await expect(page.locator('.ambient-moon')).toBeVisible();
  if(scene==='cloud-night'){await expect(page.locator('.ambient-moon')).toBeVisible();await expect(page.locator('.ambient-clouds')).toBeVisible();}
  if(scene==='clear-day')await expect(page.locator('.ambient-sun')).toBeVisible();
  if(scene==='rain'){await expect(page.locator('.ambient-rain')).toBeVisible();await expect(page.locator('.ambient-snow,.ambient-sun,.ambient-moon')).toHaveCount(0)}
  if(scene==='snow'){await expect(page.locator('.ambient-snow')).toBeVisible();await expect(page.locator('.ambient-rain')).toHaveCount(0)}
  if(scene==='stale'){await expect(page.locator('.sky-neutral')).toBeVisible();await expect(page.locator('.ambient-rain,.ambient-snow,.ambient-sun,.ambient-moon')).toHaveCount(0)}
  const issues=await page.locator('.ambient-home').evaluate(root=>{
   const errors:string[]=[];const box=root.getBoundingClientRect();
   if(root.scrollWidth>root.clientWidth+1||root.scrollHeight>root.clientHeight+1)errors.push('canvas scroll overflow');
   for(const el of root.querySelectorAll('button,.forecast-day,.ambient-condition,.ambient-metrics')){const r=el.getBoundingClientRect();if(r.left<box.left||r.right>box.right+1||r.top<box.top||r.bottom>box.bottom+1)errors.push(`off-canvas ${el.className}`);if(el.tagName==='BUTTON'&&(r.width<47.99||r.height<47.99))errors.push(`small touch target ${el.className} ${r.width}x${r.height}`)}
   return errors;
  });expect(issues).toEqual([]);
  await page.screenshot({path:info.outputPath(`ambient-${theme}-${scene}.png`)});
  const nav=page.locator('.navigation-toggle');
  const openX=(await nav.boundingBox())!.x;
  await nav.click();await page.clock.runFor(300);
  await expect.poll(async()=>(await nav.boundingBox())!.x).toBe(4);
  expect(openX).toBeGreaterThan(4);
  await nav.click();await page.clock.runFor(300);
  await page.clock.fastForward(16000);
  await expect(page.locator('.ambient-weather')).toHaveClass(/card-compact/);
  await expect(page.locator('.ambient-metrics')).toBeHidden();
  await expect(page.locator('.forecast-day')).toHaveCount(1);
  await expect(page.locator('.ambient-dock')).toHaveClass(/card-compact/);
  await expect.poll(async()=>Math.round((await page.locator('.ambient-forecast').boundingBox())!.width)).toBe(186);
  await expect.poll(async()=>(await page.locator('.ambient-weather').boundingBox())!.width).toBeLessThanOrEqual(250);
  if(signal==='wave'){await expect(page.locator('.ambient-dock')).toBeHidden();await expect(page.locator('.ambient-visualizer')).toBeVisible();expect((await page.locator('.ambient-visualizer').boundingBox())!.height).toBe(88);await expect(page.locator('.signal-station img')).toBeVisible();}else{await expect(page.locator('.playback-toggle')).toBeVisible();await expect(page.locator('.playback-expand .radio-artwork img')).toBeVisible();}
  await page.screenshot({path:info.outputPath(`ambient-compact-${theme}-${scene}.png`)});
  await page.locator('.weather-heading').click();
  await expect(page.locator('.ambient-metrics')).toBeVisible();
  await page.locator('.ambient-forecast').click();await expect(page.locator('.forecast-day')).toHaveCount(5);
  await page.locator('.ambient-forecast').click();await expect(page.locator('.forecast-day')).toHaveCount(1);
  await page.locator(signal==='wave'?'.ambient-visualizer':'.playback-expand').click();await expect(page.locator('.ambient-shortcuts')).toBeVisible();
  await page.clock.fastForward(10000);await page.locator('.weather-heading').click();await page.locator('.weather-heading').click();
  await page.clock.fastForward(6000);await expect(page.locator('.ambient-metrics')).toBeVisible();
  await page.clock.fastForward(10000);await expect(page.locator('.ambient-metrics')).toBeHidden();
 });
}



