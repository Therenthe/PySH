import {test,expect} from '@playwright/test';
import {createHash} from 'node:crypto';

const styles=['wave','bars','orbit','ribbon','mirror','rings'] as const;
const signal=(amplitude=.65)=>({available:true,status:'ready',waveform:Array.from({length:64},(_,i)=>Math.sin(i*.49)*amplitude),bars:Array.from({length:16},(_,i)=>(.18+(i%5)*.15)*amplitude),peak:amplitude,rms:amplitude*.4,silent:amplitude===0});

for(const theme of ['ink','night']){
 test(`six genuinely distinct output geometries ${theme}, silence and reduced motion`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro');let current=signal();
  const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,visualizerStyle:'wave'},network:{},bluetooth:{devices:[],prompts:[]},audio:{ready:true,volume:30,mute:false},player:{state:'playing',kind:'radio',station_name:'Station',url:'https://example.org/stream'},weather:{}};
  await page.route('**/api/**',route=>{const path=new URL(route.request().url()).pathname;return route.fulfill({json:path==='/api/audio/visualization'?current:path==='/api/session'?{token:'fixture'}:path==='/api/state'?state:{ok:true}});});
  // Crop only the signal: animated weather cannot make two identical
  // visualizers appear different in this pixel comparison.
  const fingerprints=new Set<string>();
  for(const style of styles){
   state.preferences.visualizerStyle=style;await page.goto('/');await page.reload();
   const svg=page.locator('.audio-visualizer svg');await expect(svg).toBeVisible();await expect(page.locator('.audio-visualizer')).toHaveAttribute('data-signal-style',style);
   const painted=await svg.evaluate(async el=>{
    const clone=el.cloneNode(true) as SVGElement;clone.setAttribute('xmlns','http://www.w3.org/2000/svg');clone.setAttribute('width','320');clone.setAttribute('height','80');
    const image=new Image();image.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(new XMLSerializer().serializeToString(clone));await image.decode();
    const canvas=document.createElement('canvas');canvas.width=320;canvas.height=80;const context=canvas.getContext('2d')!;context.drawImage(image,0,0);const pixels=context.getImageData(0,0,320,80).data;let count=0;for(let i=3;i<pixels.length;i+=4)if(pixels[i]>10)count++;return count;
   });expect(painted).toBeGreaterThan(30);
   const pixels=await svg.screenshot({path:info.outputPath(`geometry-${theme}-${style}.png`)});fingerprints.add(createHash('sha256').update(pixels).digest('hex'));
   const geometry=await svg.evaluate(el=>Array.from(el.querySelectorAll('path,rect,line,ellipse')).map(n=>n.outerHTML).join(''));
   current=signal(.3);await expect.poll(()=>svg.evaluate(el=>Array.from(el.querySelectorAll('path,rect,line,ellipse')).map(n=>n.outerHTML).join(''))).not.toBe(geometry);
   current=signal();
  }
  expect(fingerprints.size).toBe(6);
  state.player.state='paused';await page.reload();await expect(page.locator('.audio-visualizer svg')).toHaveCount(0);await expect(page.locator('.audio-visualizer')).toContainText(ro?'oprită':'inactive');
  state.player.state='playing';await page.emulateMedia({reducedMotion:'reduce'});await page.reload();await expect(page.locator('.signal-level')).toContainText(ro?'Nivel':'Level');await expect(page.locator('.audio-visualizer svg')).toHaveCount(0);
  current=signal(0);await expect(page.locator('.signal-level')).toContainText(ro?'Liniște':'silent');
 });

 test(`chosen size changes every style with expanded and collapsed playback ${theme}`,async({page},info)=>{
  test.setTimeout(90000);
  const ro=info.project.name.endsWith('ro');
  const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,nightEnabled:false,navigationCollapsed:false,screensaverMinutes:0,visualizerStyle:'wave',visualizerSize:'compact',homeCards:['weather','forecast','playback'],homePositions:{visualizer:{x:.08,y:.62,z:4}},timezone:'Europe/Bucharest',shortcuts:['radio','media']},network:{state:'connected'},bluetooth:{devices:[],prompts:[]},audio:{ready:true,volume:30,mute:false},player:{state:'playing',kind:'radio',station_name:'Radio One',url:'https://example.org/stream'},weather:{}};
  await page.route('**/api/**',async route=>{const path=new URL(route.request().url()).pathname;let json:any={ok:true};if(path==='/api/session')json={token:'fixture'};else if(path==='/api/state')json=state;else if(path==='/api/audio/visualization')json=signal();else if(path==='/api/preferences'){Object.assign(state.preferences,route.request().postDataJSON());json=state.preferences;}await route.fulfill({json});});
  await page.clock.install();await page.goto('/');
  // First exercise the real preference action, not only preloaded fixture values.
  await page.locator('.main-nav button').nth(3).tap();
  for(const [label,size] of [[ro?'Mare':'Large','large'],[ro?'Echilibrat':'Balanced','balanced'],['Compact','compact']]){
   const choice=page.getByRole('button',{name:ro?'Dimensiune vizualizator':'Visualizer size',exact:true});await choice.scrollIntoViewIfNeeded();await choice.tap();await page.getByRole('dialog').getByRole('radio',{name:label,exact:true}).tap();expect(state.preferences.visualizerSize).toBe(size);
  }
  state.preferences.location={name:'București, Sectorul 5',latitude:44.4,longitude:26.07};
  state.weather={current:{temperature_c:13,weather_code:2,is_day:0,feels_like_c:10,wind_kmh:8,humidity_pct:48,pressure_hpa:1018,uv_index:0},daily:Array.from({length:5},(_,i)=>({date:`2026-10-0${i+4}`,weather_code:i,max_c:22+i,min_c:9+i})),stale:false};
  const positioned=state.preferences.homePositions;state.preferences.homePositions={};
  for(const size of ['compact','balanced','large']){
   state.preferences.visualizerSize=size;await page.reload();await expect(page.locator('.ambient-home')).toHaveClass(/transport-expanded/);await expect(page.locator('.audio-visualizer svg')).toBeVisible();
   const overflow=await page.locator('.ambient-weather,.ambient-forecast,.ambient-visualizer,.ambient-dock,.ambient-dock button').evaluateAll(elements=>elements.filter(el=>{const r=el.getBoundingClientRect();return r.width>0&&(r.left<0||r.top<0||r.right>800.5||r.bottom>480.5);}).map(el=>el.className));expect(overflow).toEqual([]);
   const weather=(await page.locator('.ambient-weather').boundingBox())!,forecast=(await page.locator('.ambient-forecast').boundingBox())!;expect(forecast.x-weather.x-weather.width).toBeGreaterThanOrEqual(15);
   await page.screenshot({path:info.outputPath(`expanded-layout-${theme}-${size}.png`)});
  }
  state.preferences.homePositions=positioned;
  for(const style of styles){let previous=0;
   for(const [size,height] of [['compact',64],['balanced',88],['large',112]] as const){
    state.preferences.visualizerStyle=style;state.preferences.visualizerSize=size;await page.reload();await expect(page.locator('.ambient-home')).toBeVisible();
    const visualizer=page.locator('.ambient-visualizer'),svg=visualizer.locator('svg');await expect(svg).toBeVisible();
    await expect.poll(()=>visualizer.evaluate(el=>el.getBoundingClientRect().height)).toBe(height);
    const expanded=(await svg.boundingBox())!;expect(expanded.height).toBeGreaterThan(previous);previous=expanded.height;
    await page.clock.runFor(16000);await expect(visualizer).toHaveAttribute('aria-expanded','false');await expect.poll(()=>visualizer.evaluate(el=>el.getBoundingClientRect().height)).toBe(height);
    const collapsed=(await svg.boundingBox())!;expect(collapsed.height).toBeGreaterThan(0);expect(collapsed.x).toBeGreaterThanOrEqual(0);expect(collapsed.y+collapsed.height).toBeLessThanOrEqual(480);
    await svg.screenshot({path:info.outputPath(`size-${theme}-${style}-${size}.png`)});
   }
  }
 });
}
