import {test,expect} from '@playwright/test';

for(const theme of ['ink','night'])test(`Home ${theme}: compact placement preserves right and bottom edges through growth, overlap and reload`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro');
 const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,nightEnabled:false,navigationCollapsed:false,navigationAutoHide:false,screensaverMinutes:0,visualizerStyle:'off',homeCards:['weather','forecast','playback'],homePositions:{},timezone:'Europe/Bucharest',shortcuts:['radio','media']},network:{state:'connected'},bluetooth:{devices:[],prompts:[]},audio:{ready:true,volume:30,mute:false},player:{state:'playing',kind:'radio',station_name:'Radio One',url:'https://example.org/stream'},weather:{current:{temperature_c:13,weather_code:0,is_day:0,feels_like_c:11,wind_kmh:8},daily:Array.from({length:5},(_,i)=>({date:`2026-10-0${i+4}`,weather_code:0,max_c:22,min_c:11})),stale:false}};
 await page.route('**/api/**',async route=>{const path=new URL(route.request().url()).pathname;let json:any={ok:true};if(path==='/api/session')json={token:'fixture'};else if(path==='/api/state')json=state;else if(path==='/api/preferences'){Object.assign(state.preferences,route.request().postDataJSON());json=state.preferences;}await route.fulfill({json});});
 await page.goto('/');const weather=page.locator('.ambient-weather'),forecast=page.locator('.ambient-forecast'),canvas=page.locator('.ambient-home');await expect(weather).toBeVisible();
 const arrange=async()=>{await page.locator('.main-nav button').nth(3).tap();await page.locator('.settings-tabs button').filter({hasText:ro?'Acasă':'Home'}).tap();await page.getByRole('button',{name:ro?'Aranjează Acasă':'Arrange Home',exact:true}).tap();await expect(weather).toHaveClass(/card-compact/);await expect(forecast).toHaveClass(/card-compact/);};
 const choose=async(key:'weather'|'forecast')=>{await page.getByRole('button',{name:ro?'Selectează cardul':'Choose card',exact:true}).tap();await page.getByRole('dialog').getByRole('radio',{name:key==='weather'?(ro?'Vreme':'Weather'):(ro?'Prognoză':'Forecast'),exact:true}).tap();};
 const drag=async(key:'weather'|'forecast',left:number,top:number)=>{await choose(key);const card=key==='weather'?weather:forecast,box=(await card.boundingBox())!,handle=(await page.locator(`[data-layout-handle=${key}]`).boundingBox())!;await page.mouse.move(handle.x+24,handle.y+24);await page.mouse.down();await page.mouse.move(handle.x+24+left-box.x,handle.y+24+top-box.y,{steps:10});await page.mouse.up();await expect.poll(async()=>Math.abs((await card.boundingBox())!.x-left)).toBeLessThan(2);await expect.poll(async()=>Math.abs((await card.boundingBox())!.y-top)).toBeLessThan(2);};
 const edges=async(card:typeof weather)=>{const r=(await card.boundingBox())!;return {right:r.x+r.width,bottom:r.y+r.height,width:r.width,height:r.height};};
 await arrange();const root=(await canvas.boundingBox())!,w=(await weather.boundingBox())!,f=(await forecast.boundingBox())!;
 // Swap vertical regions first: placement is free, not tied to a CSS grid row.
 const upperY=root.y+12,lowerY=root.y+root.height-w.height-12;await drag('weather',w.x,lowerY);await drag('forecast',f.x,upperY);expect((await weather.boundingBox())!.y).toBeGreaterThan((await forecast.boundingBox())!.y);
 const right=root.x+root.width-12,bottom=root.y+root.height-12;
 // Selecting a grid item removes row stretching; use its actual positioned size.
 await choose('weather');const placedWeather=(await weather.boundingBox())!;await drag('weather',right-placedWeather.width,bottom-placedWeather.height);
 await choose('forecast');const placedForecast=(await forecast.boundingBox())!;await drag('forecast',right-placedForecast.width,bottom-placedForecast.height);await choose('forecast');
 const before=await edges(forecast);expect(Math.abs(before.right-right)).toBeLessThan(2);expect(Math.abs(before.bottom-bottom)).toBeLessThan(2);
 // Intentional overlap stays allowed; the most recently chosen card is above.
 expect(await page.evaluate(({x,y})=>Boolean(document.elementFromPoint(x,y)?.closest('.ambient-forecast')),{x:right-60,y:bottom-20})).toBe(true);
 await page.getByRole('button',{name:ro?'Gata':'Done',exact:true}).tap();
 for(const key of ['weather','forecast']){expect(state.preferences.homePositions[key].anchorX).toBe('right');expect(state.preferences.homePositions[key].anchorY).toBe('bottom');}
 expect(state.preferences.homePositions.forecast.z).toBe(4);
 await page.reload();await expect(forecast).toBeVisible();
 // Expanded forecast grows toward the left, keeping its saved right/bottom edges.
 await expect.poll(async()=>Math.abs((await edges(forecast)).right-before.right)).toBeLessThan(2);await expect.poll(async()=>Math.abs((await edges(forecast)).bottom-before.bottom)).toBeLessThan(2);
 const expanded=await edges(forecast);expect(expanded.width).toBeGreaterThan(before.width+100);
 await forecast.tap();await expect(forecast).toHaveClass(/card-compact/);const collapsed=await edges(forecast);expect(Math.abs(collapsed.right-before.right)).toBeLessThan(2);expect(Math.abs(collapsed.bottom-before.bottom)).toBeLessThan(2);
 await forecast.tap();await expect(forecast).not.toHaveClass(/card-compact/);expect(Math.abs((await edges(forecast)).right-before.right)).toBeLessThan(2);
 await page.screenshot({path:info.outputPath(`anchored-${theme}.png`)});
});

test('legacy Home positions retain top-left semantics before a deliberate new drag',async({page})=>{
 const prefs:any={language:'en',theme:'night',setupComplete:true,nightEnabled:false,screensaverMinutes:0,visualizerStyle:'off',homeCards:['weather'],homePositions:{weather:{x:.1,y:.15,z:3}}};
 const state={preferences:prefs,network:{},bluetooth:{devices:[],prompts:[]},audio:{},player:{},weather:{current:{temperature_c:13,weather_code:0,is_day:1},daily:[]}};
 await page.route('**/api/**',route=>route.fulfill({json:new URL(route.request().url()).pathname==='/api/session'?{token:'fixture'}:state}));await page.goto('/');await expect(page.locator('.ambient-weather')).toBeVisible();
 const canvas=(await page.locator('.ambient-home').boundingBox())!,card=(await page.locator('.ambient-weather').boundingBox())!;
 expect(Math.abs(card.x-(canvas.x+.1*canvas.width))).toBeLessThan(2);expect(Math.abs(card.y-(canvas.y+.15*canvas.height))).toBeLessThan(2);
});
