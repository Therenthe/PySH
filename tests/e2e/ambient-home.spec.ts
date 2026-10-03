import {test,expect} from '@playwright/test';
for(const theme of ['ink','night']) for(const scene of ['clear-day','clear-night','rain','snow','stale']) {
 test(`ambient home ${theme} ${scene}: genuine weather scene and five forecast symbols`,async({page},info)=>{
  const language=info.project.name.endsWith('ro')?'ro':'en';
  const state={preferences:{language,theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,timezone:'Europe/Bucharest',location:{name:'București'},favorites:[],shortcuts:['radio','media']},network:{available:true,state:'connected',connection:'Ethernet',devices:[],saved:[]},bluetooth:{available:true,powered:true,devices:[],prompts:[]},audio:{available:true,ready:true,volume:20,mute:false,outputs:[]},player:{state:'playing',kind:'radio',station_name:'Radio România Actualități',title:'Artist · A distinct song title',url:'https://example.invalid/radio'},weather:{current:{temperature_c:13,feels_like_c:10,weather_code:scene==='rain'?63:scene==='snow'?73:0,is_day:scene==='clear-night'?0:1,wind_kmh:8},daily:Array.from({length:5},(_,i)=>({date:`2026-10-0${i+3}`,weather_code:[0,2,63,73,95][i],max_c:22-i,min_c:11-i})),updated_at:'2026-10-03T12:00:00Z',stale:scene==='stale',attribution:'Open-Meteo'}};
  await page.route('**/api/**',async route=>{const path=new URL(route.request().url()).pathname;await route.fulfill({json:path==='/api/session'?{token:'isolated-browser-fixture'}:path==='/api/state'?state:{ok:true}})});
  await page.goto('/');
  await expect(page.locator('.ambient-home')).toBeVisible();
  const headerBounds=await page.locator('.topbar').evaluate(header=>{const bounds=header.getBoundingClientRect();return [...header.querySelectorAll('.eyebrow,.navigation-toggle,.date-label')].map(el=>el.getBoundingClientRect()).every(r=>r.top>=bounds.top&&r.bottom<=bounds.bottom&&r.left>=bounds.left&&r.right<=bounds.right);});
  expect(headerBounds).toBe(true);
  await expect(page.locator('.forecast-day')).toHaveCount(5);
  await expect(page.locator('.forecast-day svg')).toHaveCount(5);
  await expect(page.locator('.forecast-day strong')).toHaveCount(5);
  await expect(page.locator('.forecast-day i')).toHaveCount(5);
  await expect(page.locator('.playback-source')).toHaveText('Radio România Actualități');
  await expect(page.locator('.playback-metadata')).toHaveText('Artist · A distinct song title');
  await expect(page.locator('.home-clock-card,.clock-greeting')).toHaveCount(0);
  if(scene==='clear-night')await expect(page.locator('.ambient-moon')).toBeVisible();
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
 });
}
