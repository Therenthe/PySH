import {test,expect,type Locator} from '@playwright/test';

// A translucent caption must remain legible over both dark masonry and lit windows.
async function captionContrast(locator: Locator) {
 return locator.evaluate(el=>{
  const style=getComputedStyle(el),parse=(value:string)=>value.match(/[\d.]+/g)!.map(Number);
  const text=parse(style.color),back=parse(style.backgroundColor),alpha=back[3]??1;
  const luminance=(rgb:number[])=>rgb.map(n=>n/255).map(n=>n<=.04045?n/12.92:((n+.055)/1.055)**2.4).reduce((sum,n,i)=>sum+n*[.2126,.7152,.0722][i],0);
  const foreground=luminance(text.slice(0,3));
  const ratios=[0,255].map(under=>{const background=luminance(back.slice(0,3).map(n=>n*alpha+under*(1-alpha)));return (Math.max(foreground,background)+.05)/(Math.min(foreground,background)+.05);});
  return {alpha,minimum:Math.min(...ratios),font:parseFloat(style.fontSize)};
 });
}

for(const theme of ['ink','night'])for(const day of [true,false])for(const size of ['compact','balanced','large']){
 test(`Home captions stay legible over city: ${theme} ${day?'day':'night'} ${size}`,async({page},info)=>{
  const language=info.project.name.endsWith('ro')?'ro':'en';
  let signalReady=false;
  const state:any={preferences:{language,theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,visualizerStyle:'wave',visualizerSize:size,timezone:'Europe/Bucharest',location:{name:'București',latitude:44.4,longitude:26.1},homeCards:['weather','forecast','playback'],shortcuts:[]},network:{},bluetooth:{devices:[],prompts:[]},audio:{ready:true,volume:30,mute:false},player:{state:'playing',kind:'radio',url:'https://example.invalid/radio',station_name:'Radio România Actualități'},weather:{stale:false,current:{temperature_c:13,weather_code:0,is_day:day?1:0},daily:[]}};
  await page.clock.install({time:new Date(day?'2026-10-23T10:00:00Z':'2026-10-23T20:00:00Z')});
  await page.route('**/api/**',async route=>{const path=new URL(route.request().url()).pathname;let json:any={ok:true};if(path==='/api/state')json=state;else if(path==='/api/session')json={token:'fixture'};else if(path==='/api/audio/visualization')json=signalReady?{available:true,status:'ready',waveform:Array(64).fill(.2),bars:Array(16).fill(.2),peak:.3,rms:.2,silent:false}:{available:false,status:'unavailable'};await route.fulfill({json});});
  await page.goto('/');await expect(page.locator('.ambient-home')).toBeVisible();
  await page.clock.runFor(16500);
  const station=page.locator('.signal-station>span:last-child'),unavailable=page.locator('.ambient-visualizer .signal-empty>span');
  await expect(station).toHaveText('Radio România Actualități');await expect(unavailable).toHaveText(language==='ro'?'Semnal audio indisponibil':'Audio signal unavailable');
  for(const caption of [station,unavailable]){const result=await captionContrast(caption);expect(result.alpha).toBeGreaterThanOrEqual(.95);expect(result.minimum).toBeGreaterThanOrEqual(4.5);expect(result.font).toBeGreaterThanOrEqual(14);}
  const box=(await page.locator('.ambient-visualizer').boundingBox())!;expect(box.height).toBe({compact:64,balanced:88,large:112}[size]);expect(box.y+box.height).toBeLessThanOrEqual(480);
  await page.emulateMedia({reducedMotion:'reduce'});signalReady=true;await page.clock.runFor(1500);
  const level=page.locator('.ambient-visualizer .signal-level>span');await expect(level).toContainText(language==='ro'?'Nivel':'Level');expect((await captionContrast(level)).minimum).toBeGreaterThanOrEqual(4.5);
  await page.screenshot({path:info.outputPath(`captions-${theme}-${day?'day':'night'}-${size}.png`)});
  await page.locator('.ambient-visualizer').tap();await expect(page.locator('.ambient-dock')).toBeVisible();
 });
}
