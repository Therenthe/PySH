import {test,expect} from '@playwright/test';

const scenes=[
 {name:'spring-drizzle',month:3,code:51,temp:12,wind:8,type:'rain',intensity:'light'},
 {name:'summer-clear',month:6,code:0,temp:28,wind:5,type:'none',intensity:'none'},
 {name:'summer-heat',month:7,code:0,temp:39,wind:9,type:'none',intensity:'none'},
 {name:'autumn-rain',month:9,code:63,temp:14,wind:24,type:'rain',intensity:'moderate'},
 {name:'autumn-downpour',month:9,code:65,temp:13,wind:48,type:'rain',intensity:'heavy'},
 {name:'winter-snow',month:0,code:71,temp:-2,wind:10,type:'snow',intensity:'light'},
 {name:'winter-blizzard',month:1,code:75,temp:-9,wind:68,type:'snow',intensity:'heavy'},
 {name:'winter-ice',month:0,code:67,temp:-3,wind:26,type:'ice',intensity:'heavy'},
 {name:'storm-hail',month:7,code:99,temp:19,wind:73,type:'ice',intensity:'heavy'},
 {name:'autumn-fog',month:9,code:45,temp:8,wind:1,type:'none',intensity:'none'},
] as const;

for(const theme of ['ink','night'])for(const scene of scenes)test(`Blender city ${theme} ${scene.name}: actual conditions and bounded precipitation`,async({page},info)=>{
 const language=info.project.name.endsWith('ro')?'ro':'en';
 const now=new Date(Date.UTC(2026,scene.month,10,theme==='night'?22:10));
 const state={preferences:{language,theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,visualizerStyle:'wave',timezone:'Europe/Bucharest',homeCards:[],location:{name:'București · Sector 5',latitude:44.4,longitude:26.1},favorites:[],shortcuts:['radio','media'],lastStation:{name:'Radio fixture',url:'https://example.invalid/fixture'}},network:{available:true,state:'connected',connection:'Ethernet',devices:[],saved:[]},bluetooth:{available:true,powered:true,devices:[{name:'Owned fixture',connected:true}],prompts:[]},audio:{available:true,ready:true,volume:20,mute:false,outputs:[]},player:{state:'playing',kind:'radio',station_name:'Radio fixture',url:'https://example.invalid/fixture'},weather:{current:{temperature_c:scene.temp,weather_code:scene.code,is_day:theme==='night'?0:1,wind_kmh:scene.wind},daily:[],updated_at:now.toISOString(),stale:false}};
 await page.route('**/api/**',async route=>{const path=new URL(route.request().url()).pathname;await route.fulfill({json:path==='/api/session'?{token:'scene-browser-fixture'}:path==='/api/state'?state:{ok:true}})});
 await page.clock.install({time:now});await page.goto('/');
 const city=page.locator('.city-diorama');await expect(city).toBeVisible();
 await expect(city).toHaveAttribute('data-city-version','blender-v4');
 await expect(city).toHaveAttribute('data-radio-emitting','true');
 await expect(city).toHaveAttribute('data-bluetooth','connected');
 await page.locator('.city-architecture,.city-metro,.city-rail-front').evaluateAll(nodes=>Promise.all(nodes.map(node=>(node as HTMLImageElement).decode())));
 const assets=await page.locator('.city-architecture,.city-metro').evaluateAll(nodes=>nodes.map(el=>({loaded:(el as HTMLImageElement).complete&&(el as HTMLImageElement).naturalWidth>0,src:(el as HTMLImageElement).getAttribute('src')})));
 expect(assets.every(asset=>asset.loaded)).toBeTruthy();
 await expect(page.locator('.ambient-star-texture,.city-material')).toHaveCount(0);
 if(scene.type==='none')await expect(page.locator('.scene-precipitation')).toHaveCount(0);
 else {
  const layer=page.locator('.scene-precipitation');await expect(layer).toHaveAttribute('data-precipitation',scene.type);await expect(layer).toHaveAttribute('data-intensity',scene.intensity);
  const count=await page.locator('.weather-particle').count();expect(count).toBeGreaterThan(0);expect(count).toBeLessThanOrEqual(64);
  expect(await layer.evaluate(el=>getComputedStyle(el).backgroundImage)).toBe('none');
  // CSS compositor time uses real frames even with the JS clock simulated.
  const particle=page.locator('.weather-particle').nth(3);
  const first=await particle.evaluate(el=>getComputedStyle(el).transform);
  await expect.poll(()=>particle.evaluate(el=>getComputedStyle(el).transform)).not.toBe(first);
 }
 await expect(page.locator('.weather-alert-notice.has-alerts')).toHaveCount(0);
 await page.clock.runFor(1000);
 await page.screenshot({path:info.outputPath(`${theme}-${scene.name}.png`)});
 await page.emulateMedia({reducedMotion:'reduce'});
 const animations=await page.locator('.weather-particle,.city-metro,.city-radio-emission,.city-bluetooth-emission').evaluateAll(elements=>elements.map(el=>getComputedStyle(el).animationName));
 expect(animations.every(name=>name==='none')).toBeTruthy();
});

test('weather model covers WMO and hemispheric seasons without inventing emergency alerts',async({page})=>{
 await page.route('**/scene-model-fixture.html',route=>route.fulfill({contentType:'text/html',body:'<main>Isolated scene model fixture</main>'}));await page.goto('/scene-model-fixture.html');
 const result=await page.evaluate(async()=>{
  const modulePath='/src/sceneWeather.ts';const {sceneWeather}=await import(/* @vite-ignore */modulePath);
  const codes=[0,1,2,3,45,48,51,53,55,56,57,61,63,65,66,67,71,73,75,77,80,81,82,85,86,95,96,97,99,null,100,'rain'];
  return {all:codes.map(code=>sceneWeather(code,false,19,35,new Date('2026-10-23T12:00:00Z'),44.4)),stale:sceneWeather(99,true,-5,90,new Date('2026-01-01'),44.4),north:[0,3,6,9].map(month=>sceneWeather(0,false,20,0,new Date(Date.UTC(2026,month,10)),44)),south:[0,3,6,9].map(month=>sceneWeather(0,false,20,0,new Date(Date.UTC(2026,month,10)),-33))};
 });
 expect(result.north.map((x:any)=>x.season)).toEqual(['winter','spring','summer','autumn']);
 expect(result.south.map((x:any)=>x.season)).toEqual(['summer','autumn','winter','spring']);
 expect(result.all.every((scene:any)=>scene.count<=64&&!('alert'in scene)&&!('tornado'in scene)&&!('flood'in scene))).toBeTruthy();
 expect(result.stale).toMatchObject({precipitation:'none',count:0,freezing:false,thunder:false,wind:0});
});

test('live device state transitions stop antenna emissions and distinguish Bluetooth powered from connected',async({page})=>{
 const state={preferences:{language:'en',theme:'night',setupComplete:true,nightEnabled:false,screensaverMinutes:0,timezone:'Europe/Bucharest',homeCards:[],favorites:[],location:{latitude:44.4,longitude:26.1}},player:{state:'playing',kind:'radio'},network:{available:true,state:'connected'},bluetooth:{available:true,powered:true,devices:[{connected:true}],prompts:[]},audio:{available:true,ready:true},weather:{current:{weather_code:0,is_day:0},updated_at:'2026-10-04T23:00:00Z'}};
 await page.route('**/api/**',route=>route.fulfill({json:new URL(route.request().url()).pathname==='/api/state'?state:{token:'fixture'}}));
 await page.clock.install({time:new Date('2026-10-04T23:00:00Z')});await page.goto('/');
 await expect(page.locator('.city-radio-emitter')).toHaveCount(1);await expect(page.locator('.city-bluetooth.connected')).toHaveCount(1);
 state.player.state='paused';state.bluetooth.devices=[];await page.clock.runFor(2500);
 await expect(page.locator('.city-radio-emitter')).toHaveCount(0);await expect(page.locator('.city-bluetooth:not(.connected)')).toHaveCount(1);
 state.bluetooth.powered=false;await page.clock.runFor(2500);await expect(page.locator('.city-bluetooth')).toHaveCount(0);
});
