import {test,expect,type Page} from '@playwright/test';
import {openSettingsSection} from './settings-navigation';
const selectors={weather:'.ambient-weather',forecast:'.ambient-forecast',playback:'.ambient-dock',visualizer:'.ambient-visualizer'};
async function fixture(page:Page,ro:boolean,theme:string){
 const positions={weather:{x:.08,y:.1,z:4,anchorX:'left',anchorY:'top'},forecast:{x:.5,y:.12,z:3,anchorX:'left',anchorY:'top'},playback:{x:.03,y:.75,z:2,anchorX:'left',anchorY:'top'},visualizer:{x:.4,y:.5,z:1,anchorX:'left',anchorY:'top'}};
 const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,nightEnabled:false,navigationCollapsed:false,navigationAutoHide:false,screensaverMinutes:0,visualizerStyle:'bars',visualizerSize:'compact',homeCards:['weather','forecast','playback'],homePositions:positions,timezone:'Europe/Bucharest',shortcuts:['radio','media']},network:{},bluetooth:{devices:[],prompts:[]},audio:{ready:true,volume:30,mute:false},player:{state:'playing',kind:'radio',station_name:'Retained radio',title:'Artist · Song',url:'https://example.invalid/stream'},weather:{current:{temperature_c:13,weather_code:2,is_day:1,feels_like_c:11},daily:Array.from({length:5},(_,i)=>({date:`2026-10-${24+i}`,weather_code:0,max_c:22,min_c:11})),stale:false}};
 const writes:any[]=[],other:any[]=[],control={failSave:false};
 await page.route('**/api/**',async route=>{const req=route.request(),path=new URL(req.url()).pathname;let json:any={ok:true};if(path==='/api/session')json={token:'isolated-arrangement-assists'};else if(path==='/api/state')json=state;else if(path==='/api/audio/visualization')json={available:true,status:'ready',waveform:Array(64).fill(.2),bars:Array(16).fill(.3),peak:.3,rms:.2,silent:false};else if(req.method()!=='GET'){if(path==='/api/preferences'){writes.push(req.postDataJSON());if(control.failSave){await route.fulfill({status:500,json:{error:'preferences_unavailable'}});return;}Object.assign(state.preferences,req.postDataJSON());json=state.preferences;}else other.push({path,body:req.postDataJSON()});}await route.fulfill({json});});
 await page.goto('/');await expect(page.locator('.ambient-home')).toBeVisible();return {state,writes,other,control};
}
async function arrange(page:Page,ro:boolean){await page.locator('.main-nav button').nth(3).tap();await openSettingsSection(page,'home');await page.getByRole('button',{name:ro?'Aranjează Acasă':'Arrange Home',exact:true}).tap();await expect(page.locator('.ambient-home')).toHaveAttribute('data-layout-editing','true');}
async function tool(page:Page,ro:boolean,name:string){await page.getByRole('button',{name:ro?'Opțiuni':'Options',exact:true}).tap();await page.getByRole('button',{name,exact:true}).tap();}
async function boxes(page:Page){return page.locator('[data-layout-handle]').evaluateAll(handles=>Object.fromEntries(handles.map(handle=>[handle.getAttribute('data-layout-handle'),handle.parentElement!.getBoundingClientRect().toJSON()])));}
async function move(page:Page,key:keyof typeof selectors,left:number,top:number,release=true){const card=(await page.locator(selectors[key]).boundingBox())!,grip=page.locator(`[data-layout-handle=${key}]`),g=(await grip.boundingBox())!;await page.mouse.move(g.x+24,g.y+24);await page.mouse.down();await page.mouse.move(g.x+24+left-card.x,g.y+24+top-card.y,{steps:5});if(release)await page.mouse.up();}
for(const theme of ['ink','night']){
 test(`Arrangement assists ${theme}: optional snap preserves free overlap and exact keyboard nudges`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme);await arrange(page,ro);const initial=await boxes(page);
  await move(page,'forecast',initial.weather.x+4,initial.weather.y+7,false);await expect(page.locator('.home-alignment-guide').first()).toBeVisible();await expect(page.locator('.home-alignment-guide').first()).toHaveCSS('pointer-events','none');expect(Math.abs((await page.locator('.ambient-forecast').boundingBox())!.x-initial.weather.x-4)).toBeLessThan(1);await page.mouse.up();await expect(page.locator('.home-alignment-guide')).toHaveCount(0);
  await tool(page,ro,ro?'Aliniere la ghidaje':'Snap to guides');await move(page,'forecast',initial.weather.x+4,initial.weather.y+7);expect(Math.abs((await page.locator('.ambient-forecast').boundingBox())!.x-initial.weather.x)).toBeLessThan(1);
  const grip=page.locator('[data-layout-handle=forecast]');await grip.focus();const before=(await page.locator('.ambient-forecast').boundingBox())!;await page.keyboard.press('ArrowRight');expect((await page.locator('.ambient-forecast').boundingBox())!.x-before.x).toBeGreaterThan(5);
  expect(f.writes).toEqual([]);expect(f.other).toEqual([]);await page.getByRole('button',{name:ro?'Anulează':'Cancel',exact:true}).tap();await arrange(page,ro);await page.getByRole('button',{name:ro?'Opțiuni':'Options',exact:true}).tap();await expect(page.getByRole('button',{name:ro?'Aliniere la ghidaje':'Snap to guides',exact:true})).toHaveAttribute('aria-pressed','false');
 });
 test(`Arrangement assists ${theme}: completed move Undo includes stacking, tap keeps Undo, pointer cancel restores`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme);await arrange(page,ro);const before=await boxes(page);await move(page,'weather',before.weather.x+35,before.weather.y+25);await page.locator('[data-layout-handle=weather]').tap();await tool(page,ro,ro?'Anulează mutarea':'Undo move');
  const after=await boxes(page);for(const key of Object.keys(before)){expect(Math.abs(after[key].x-before[key].x)).toBeLessThan(1);expect(Math.abs(after[key].y-before[key].y)).toBeLessThan(1);}
  await move(page,'weather',before.weather.x+50,before.weather.y+30,false);
  // Explicit synthetic cancellation exercises a real captured pointer, not mocked card geometry.
  await page.locator('[data-layout-handle=weather]').dispatchEvent('pointercancel',{pointerId:1,buttons:0});await page.mouse.up();expect(Math.abs((await page.locator('.ambient-weather').boundingBox())!.x-before.weather.x)).toBeLessThan(1);
  await page.getByRole('button',{name:ro?'Gata':'Done',exact:true}).tap();expect(f.state.preferences.homePositions.weather.z).toBe(4);expect(f.state.preferences.homePositions.forecast.z).toBe(3);expect(f.other).toEqual([]);
 });
 test(`Arrangement assists ${theme}: pointer drag owns Escape even when another toolbar control had focus`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme);await arrange(page,ro);const before=await boxes(page),options=page.getByRole('button',{name:ro?'Opțiuni':'Options',exact:true});await options.focus();
  await move(page,'weather',before.weather.x+35,before.weather.y+25,false);const grip=page.locator('[data-layout-handle=weather]');await expect(grip).toBeFocused();
  await page.keyboard.press('Escape');await expect.poll(async()=>Math.abs((await page.locator('.ambient-weather').boundingBox())!.x-before.weather.x)).toBeLessThan(1);
  await page.mouse.move(before.weather.x+160,before.weather.y+120);await page.mouse.up();const after=await boxes(page);
  for(const key of Object.keys(before)){expect(Math.abs(after[key].x-before[key].x)).toBeLessThan(1);expect(Math.abs(after[key].y-before[key].y)).toBeLessThan(1);}
  await options.tap();await expect(page.getByRole('button',{name:ro?'Anulează mutarea':'Undo move',exact:true})).toBeDisabled();expect(f.writes).toEqual([]);expect(f.other).toEqual([]);
 });
 test(`Arrangement assists ${theme}: Escape cancels a held arrow until keyup rather than restarting on repeat`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme);await arrange(page,ro);const grip=page.locator('[data-layout-handle=weather]'),before=(await page.locator('.ambient-weather').boundingBox())!;await grip.focus();
  await page.keyboard.down('ArrowRight');await expect.poll(async()=>(await page.locator('.ambient-weather').boundingBox())!.x-before.x).toBeGreaterThan(5);await page.keyboard.press('Escape');
  // Synthetic repeat represents the OS repeating the still-held physical key after Escape.
  await grip.dispatchEvent('keydown',{key:'ArrowRight',code:'ArrowRight',repeat:true});await expect.poll(async()=>Math.abs((await page.locator('.ambient-weather').boundingBox())!.x-before.x)).toBeLessThan(1);
  await page.keyboard.up('ArrowRight');await page.keyboard.press('ArrowRight');await expect.poll(async()=>(await page.locator('.ambient-weather').boundingBox())!.x-before.x).toBeGreaterThan(5);
  await tool(page,ro,ro?'Anulează mutarea':'Undo move');expect(Math.abs((await page.locator('.ambient-weather').boundingBox())!.x-before.x)).toBeLessThan(1);expect(f.writes).toEqual([]);expect(f.other).toEqual([]);
 });
 test(`Arrangement assists ${theme}: real expanded preview preserves zero right/bottom anchors and read-only actions`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme);await arrange(page,ro);const root=(await page.locator('.ambient-home').boundingBox())!,card=(await page.locator('.ambient-forecast').boundingBox())!;await move(page,'forecast',root.x+root.width-card.width,root.y+root.height-card.height);await tool(page,ro,ro?'Previzualizează':'Preview expansion');
  await expect(page.locator('.ambient-forecast')).toHaveAttribute('data-layout-preview','true');await expect(page.locator('.forecast-day')).toHaveCount(5);await expect(page.locator('.ambient-forecast')).toHaveAttribute('inert','');const expanded=(await page.locator('.ambient-forecast').boundingBox())!;expect(Math.abs(expanded.x+expanded.width-root.x-root.width)).toBeLessThan(1.5);expect(Math.abs(expanded.y+expanded.height-root.y-root.height)).toBeLessThan(1.5);expect(expanded.width).toBeGreaterThan(card.width);
  await page.keyboard.press('Escape');await expect(page.getByRole('button',{name:ro?'Opțiuni':'Options',exact:true})).toBeFocused();await expect(page.locator('.forecast-day')).toHaveCount(1);expect(f.writes).toEqual([]);expect(f.other).toEqual([]);
  await page.getByRole('button',{name:ro?'Gata':'Done',exact:true}).tap();const saved=f.state.preferences.homePositions.forecast;expect(saved.anchorX).toBe('right');expect(saved.anchorY).toBe('bottom');expect(saved.x).toBe(0);expect(saved.y).toBe(0);await page.reload();await expect.poll(async()=>{const b=(await page.locator('.ambient-forecast').boundingBox())!,r=(await page.locator('.ambient-home').boundingBox())!;return Math.abs(b.x+b.width-r.x-r.width);}).toBeLessThan(1.5);
 });
 test(`Arrangement assists ${theme}: visualizer expansion shows its inert playback companion without changing compact positions`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme),saved=JSON.stringify(f.state.preferences.homePositions),player=JSON.stringify(f.state.player);await arrange(page,ro);
  await page.getByRole('button',{name:ro?'Selectează cardul':'Choose card',exact:true}).tap();await page.getByRole('radio',{name:ro?'Vizualizator':'Visualizer',exact:true}).tap();
  const before=await boxes(page);await tool(page,ro,ro?'Previzualizează':'Preview expansion');
  const signal=page.locator('.ambient-visualizer'),companion=page.locator('.ambient-dock');await expect(signal).toHaveAttribute('data-layout-preview','true');await expect(page.locator('[data-layout-preview=true]')).toHaveCount(1);
  await expect(companion).toHaveAttribute('data-layout-preview-companion','true');await expect(companion).not.toHaveAttribute('data-layout-preview','true');await expect(companion).toHaveAttribute('inert','');await expect(companion).toHaveAttribute('aria-hidden','true');await expect(companion).not.toHaveClass(/card-compact/);
  const transport=companion.locator('.mini-controls button');await expect(transport).toHaveCount(2);for(const button of await transport.all()){await expect(button).toBeVisible();await expect(button).toBeDisabled();await button.evaluate((node:HTMLButtonElement)=>node.click());}
  await expect(companion.locator('.ambient-shortcuts')).toBeVisible();await page.screenshot({path:info.outputPath(`visualizer-preview-companion-${theme}.png`)});await page.keyboard.press('Escape');
  await expect(page.locator('[data-layout-preview-companion]')).toHaveCount(0);await expect(companion).toHaveClass(/card-compact/);
  await expect.poll(async()=>{const after=await boxes(page);return Math.max(...Object.keys(before).flatMap(key=>[Math.abs(after[key].x-before[key].x),Math.abs(after[key].y-before[key].y)]));}).toBeLessThan(1);
  expect(JSON.stringify(f.state.preferences.homePositions)).toBe(saved);expect(JSON.stringify(f.state.player)).toBe(player);expect(f.writes).toEqual([]);expect(f.other).toEqual([]);
 });
 test(`Arrangement assists ${theme}: preview keeps live appearance but unavailable controls stay dim`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme),saved=JSON.stringify(f.state.preferences);
  for(const available of [true,false]){
   if(!available){f.state.audio.ready=false;f.state.player={kind:'radio',state:'idle',url:'',title:''};await page.reload();await expect(page.locator('.ambient-home')).toBeVisible();}
   await arrange(page,ro);await page.locator('[data-layout-handle=playback]').tap();await tool(page,ro,ro?'Previzualizează':'Preview expansion');
   const dock=page.locator('.ambient-dock');await expect(dock).toHaveAttribute('inert','');
   const play=dock.locator('.playback-toggle'),stop=dock.locator('.mini-controls .outline');await expect(play).toBeDisabled();await expect(stop).toBeDisabled();
   if(available){await expect(play).toHaveCSS('opacity','1');await expect(stop).toHaveCSS('opacity','1');}
   else{expect(Number(await play.evaluate(node=>getComputedStyle(node).opacity))).toBeLessThan(1);expect(Number(await stop.evaluate(node=>getComputedStyle(node).opacity))).toBeLessThan(1);}
   await expect(dock.locator('.playback-expand')).toHaveCSS('opacity','1');
   await page.screenshot({path:info.outputPath(`playback-preview-${available?'ready':'unavailable'}-${theme}.png`)});
   await page.getByRole('button',{name:ro?'Restrânge':'Collapse',exact:true}).tap();await page.getByRole('button',{name:ro?'Anulează':'Cancel',exact:true}).tap();
  }
  expect(JSON.stringify(f.state.preferences)).toBe(saved);expect(f.writes).toEqual([]);expect(f.other).toEqual([]);
 });
 test(`Arrangement assists ${theme}: failed save keeps draft and Undo; Cancel preserves preferences`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme),saved=JSON.stringify(f.state.preferences),player=JSON.stringify(f.state.player),audio=JSON.stringify(f.state.audio);await arrange(page,ro);const before=await boxes(page);await move(page,'weather',before.weather.x+30,before.weather.y+20);const moved=(await page.locator('.ambient-weather').boundingBox())!;f.control.failSave=true;await page.getByRole('button',{name:ro?'Gata':'Done',exact:true}).tap();await expect(page.locator('.home-layout-toolbar [role=alert]')).toBeVisible();await expect(page.locator('.ambient-home')).toHaveAttribute('data-layout-editing','true');expect(Math.abs((await page.locator('.ambient-weather').boundingBox())!.x-moved.x)).toBeLessThan(1);await tool(page,ro,ro?'Anulează mutarea':'Undo move');await page.getByRole('button',{name:ro?'Anulează':'Cancel',exact:true}).tap();expect(JSON.stringify(f.state.preferences)).toBe(saved);expect(JSON.stringify(f.state.player)).toBe(player);expect(JSON.stringify(f.state.audio)).toBe(audio);expect(f.other).toEqual([]);
 });
 test(`Arrangement assists ${theme}: disclosed toolbar stays48px and on canvas without covering grips by default`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro');await fixture(page,ro,theme);await arrange(page,ro);await expect(page.locator('#home-layout-tools')).toBeHidden();await page.getByRole('button',{name:ro?'Opțiuni':'Options',exact:true}).tap();const bounds=await page.locator('.home-layout-toolbar button:visible').evaluateAll(nodes=>nodes.map(node=>node.getBoundingClientRect().toJSON()));for(const b of bounds){expect(b.width).toBeGreaterThanOrEqual(48);expect(b.height).toBeGreaterThanOrEqual(48);expect(b.left).toBeGreaterThanOrEqual(0);expect(b.right).toBeLessThanOrEqual(800);expect(b.bottom).toBeLessThanOrEqual(480);}await page.screenshot({path:info.outputPath(`arrangement-options-${theme}.png`)});await page.getByRole('button',{name:ro?'Opțiuni':'Options',exact:true}).tap();for(const grip of await page.locator('.home-drag-handle').all()){expect(await grip.evaluate(node=>{const b=node.getBoundingClientRect();return node.contains(document.elementFromPoint(b.x+b.width/2,b.y+b.height/2));})).toBe(true);}
 });
}
