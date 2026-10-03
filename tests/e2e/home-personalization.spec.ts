import {test,expect} from '@playwright/test';
for(const theme of ['ink','night'])test(`personalized Home ${theme}: idle header, sizes, visibility, persisted drag and recovery`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro');let failSave=false;
 const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,nightEnabled:false,navigationCollapsed:true,screensaverMinutes:0,visualizerStyle:'wave',visualizerSize:'compact',homeCards:['weather','forecast','playback'],homePositions:{},timezone:'Europe/Bucharest',shortcuts:['radio','media']},network:{state:'connected'},bluetooth:{devices:[],prompts:[]},audio:{ready:true,volume:30,mute:false},player:{state:'playing',kind:'radio',station_name:'Radio One',url:'https://example.org/stream'},weather:{current:{temperature_c:13,weather_code:2,is_day:0,feels_like_c:11},daily:Array.from({length:5},(_,i)=>({date:`2026-10-0${i+3}`,weather_code:0,max_c:22,min_c:11})),stale:false}};
 await page.route('**/api/**',async route=>{const path=new URL(route.request().url()).pathname;let json:any={ok:true};if(path==='/api/session')json={token:'fixture'};else if(path==='/api/state')json=state;else if(path==='/api/preferences'){if(failSave)return route.fulfill({status:500,json:{error:'save_failed'}});Object.assign(state.preferences,route.request().postDataJSON());json=state.preferences;}else if(path==='/api/audio/visualization')json={available:true,status:'ready',waveform:Array.from({length:64},(_,i)=>Math.sin(i)*.3),bars:Array(16).fill(.3),peak:.3,rms:.2,silent:false};await route.fulfill({json});});
 await page.clock.install();await page.goto('/');await expect(page.locator('.ambient-home')).toBeVisible();
 const w=(await page.locator('.ambient-weather').boundingBox())!,f=(await page.locator('.ambient-forecast').boundingBox())!;expect(f.y-(w.y+w.height)).toBeGreaterThanOrEqual(16);
 await page.clock.runFor(10500);await expect(page.locator('.topbar')).toHaveClass(/topbar-idle/);await expect.poll(()=>page.locator('.topbar').evaluate(el=>getComputedStyle(el).backgroundColor)).toBe('rgba(0, 0, 0, 0)');
 await page.locator('.navigation-toggle').tap();await expect(page.locator('.topbar')).not.toHaveClass(/topbar-idle/);await page.clock.runFor(300);await page.locator('.navigation-toggle').tap();await page.clock.runFor(300);
 await page.screenshot({path:info.outputPath(`personalized-active-${theme}.png`)});
 const settings=async()=>{await page.locator('.navigation-toggle').tap();await page.clock.runFor(300);await page.locator('.main-nav button').nth(3).tap();};
 const homeTab=()=>page.locator('.settings-tabs button').filter({hasText:ro?'Acasă':'Home'});
 await settings();
 for(const [label,size] of [[ro?'Mare':'Large','large'],[ro?'Echilibrat':'Balanced','balanced'],['Compact','compact']]){
  const trigger=page.getByRole('button',{name:ro?'Dimensiune vizualizator':'Visualizer size',exact:true});await trigger.scrollIntoViewIfNeeded();await trigger.tap();await page.getByRole('dialog').getByRole('radio',{name:label,exact:true}).tap();expect(state.preferences.visualizerSize).toBe(size);
  await page.locator('.main-nav button').nth(0).tap();await page.clock.runFor(16000);expect((await page.locator('.ambient-visualizer').boundingBox())!.height).toBe({compact:64,balanced:88,large:112}[size]);
  await page.locator('.main-nav button').nth(3).tap();
 }
 await homeTab().tap();
 for(const button of await page.locator('.settings-panel .switch').all()){const label=await button.getAttribute('aria-label');if(label?.startsWith(ro?'Afișează':'Show'))await button.tap();}
 expect(state.preferences.homeCards).toEqual([]);await page.locator('.main-nav button').nth(0).tap();await expect(page.locator('.ambient-weather,.ambient-forecast,.ambient-dock,.ambient-visualizer')).toHaveCount(0);await expect(page.locator('.ambient-city')).toBeVisible();
 state.preferences.homeCards=['weather','forecast','playback'];
 for(const key of ['weather','forecast','playback','visualizer']){
  state.preferences.homePositions={};await page.reload();await expect(page.locator('.ambient-home')).toBeVisible();
  if(await page.locator('.rail').getAttribute('aria-hidden')==='true'){await page.locator('.navigation-toggle').tap();await page.clock.runFor(300);}
  await page.locator('.main-nav button').nth(3).tap();await homeTab().tap();await page.getByRole('button',{name:ro?'Aranjează Acasă':'Arrange Home',exact:true}).tap();
  const handle=page.locator(`[data-layout-handle=${key}]`),before=(await handle.boundingBox())!;
  await page.mouse.move(before.x+24,before.y+24);await page.mouse.down();await page.mouse.move(before.x+44,before.y+4,{steps:8});await page.mouse.up();
  await page.clock.runFor(6000);await expect(handle).toBeVisible();await expect(page.locator('.pysh-screensaver')).toHaveCount(0);
  await page.getByRole('button',{name:ro?'Gata':'Done',exact:true}).tap();expect(state.preferences.homePositions[key]).toBeDefined();const saved={...state.preferences.homePositions[key]};await page.reload();await expect(page.locator(`[data-home-positioned=true]`)).toBeVisible();expect(state.preferences.homePositions[key]).toEqual(saved);
 }
 await page.locator('.main-nav button').nth(3).tap();await homeTab().tap();await page.getByRole('button',{name:ro?'Aranjează Acasă':'Arrange Home',exact:true}).tap();
 await page.getByRole('button',{name:ro?'Resetează':'Reset',exact:true}).tap();failSave=true;await page.getByRole('button',{name:ro?'Gata':'Done',exact:true}).tap();await expect(page.locator('.home-layout-toolbar [role=alert]')).toBeVisible();await expect(page.locator('[data-layout-editing=true]')).toBeVisible();
 await page.getByRole('button',{name:ro?'Anulează':'Cancel',exact:true}).tap();expect(state.preferences.homePositions.visualizer).toBeDefined();
 await page.screenshot({path:info.outputPath(`personalized-layout-${theme}.png`)});
});

test('missing saved station artwork is enriched only for the currently matching stream',async({page})=>{
 const state:any={preferences:{language:'en',theme:'night',setupComplete:true,nightEnabled:false,screensaverMinutes:0,lastStation:{name:'Station',url:'https://example.org/stream'}},network:{},bluetooth:{devices:[],prompts:[]},audio:{},player:{kind:'radio',url:'https://example.org/stream',state:'paused'},weather:{}};
 await page.route('**/api/**',async route=>{const path=new URL(route.request().url()).pathname;let json:any={ok:true};if(path==='/api/session')json={token:'fixture'};if(path==='/api/state')json=state;if(path==='/api/radio')json={stations:[{name:'Wrong',url:'https://wrong.example.org',favicon:'https://radio.example.org/wrong.svg'},{name:'Station',url_resolved:state.player.url,favicon:'https://radio.example.org/logo.svg'}]};if(path==='/api/preferences'){Object.assign(state.preferences,route.request().postDataJSON());json=state.preferences;}await route.fulfill({json});});
 await page.route('https://radio.example.org/logo.svg',route=>route.fulfill({contentType:'image/svg+xml',body:'<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48"><rect width="48" height="48" fill="white"/></svg>'}));
 await page.goto('/');await expect(page.locator('.playback-expand img')).toBeVisible();expect(state.preferences.lastStation.favicon).toBe('https://radio.example.org/logo.svg');
});



test('artwork lookup cannot update the saved station after playback changed',async({page})=>{
 const original='https://example.org/one',next='https://example.org/two';let release:()=>void=()=>{};const waiting=new Promise<void>(resolve=>release=resolve);let patchCount=0;
 const state:any={preferences:{language:'en',theme:'night',setupComplete:true,nightEnabled:false,screensaverMinutes:0,lastStation:{name:'One',url:original}},network:{},bluetooth:{devices:[],prompts:[]},audio:{},player:{kind:'radio',url:original,state:'paused'},weather:{}};
 await page.route('**/api/**',async route=>{const path=new URL(route.request().url()).pathname;let json:any={ok:true};if(path==='/api/session')json={token:'fixture'};if(path==='/api/state')json=state;if(path==='/api/radio'){await waiting;json={stations:[{url:original,favicon:'https://radio.example.org/logo.svg'}]};}if(path==='/api/preferences'){patchCount++;json=state.preferences;}await route.fulfill({json});});
 await page.goto('/');await expect(page.locator('.ambient-home')).toBeVisible();state.player.url=next;release();await expect.poll(()=>page.locator('.playback-source').textContent()).toBe('Radio');expect(patchCount).toBe(0);expect(state.preferences.lastStation.favicon).toBeUndefined();
});

for(const theme of ['ink','night'])test(`nocturnal signal stays readable over the sky in ${theme}`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro');const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,visualizerStyle:'wave',navigationCollapsed:true},network:{},bluetooth:{devices:[],prompts:[]},audio:{ready:true,volume:30,mute:false},player:{kind:'radio',state:'playing',station_name:'Radio',url:'https://example.org/radio'},weather:{stale:false,current:{weather_code:0,is_day:0,temperature_c:12},daily:[]}};
 await page.route('**/api/**',route=>{const path=new URL(route.request().url()).pathname;return route.fulfill({json:path==='/api/session'?{token:'fixture'}:path==='/api/state'?state:path==='/api/audio/visualization'?{available:true,status:'ready',waveform:Array(64).fill(.3),bars:Array(16).fill(.3),rms:.3,peak:.3,silent:false}:{ok:true}});});
 await page.goto('/');await expect(page.locator('.ambient-visualizer svg')).toBeVisible();if(theme==='ink')await expect(page.locator('.ambient-visualizer svg path')).toHaveCSS('stroke','rgb(215, 235, 231)');
 await page.locator('.ambient-visualizer').tap();await expect(page.locator('.signal-station')).toHaveCSS('color',theme==='ink'?'rgb(244, 247, 251)':'rgb(241, 243, 238)');await page.screenshot({path:info.outputPath(`night-signal-contrast-${theme}.png`)});
});
