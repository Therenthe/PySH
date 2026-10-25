import {test,expect,type Page} from '@playwright/test';

// Browser UTC deliberately differs from the selected location. These isolated
// fixtures cannot alter the Pi's weather, preferences, network or audio.
test.use({timezoneId:'UTC'});
const destinations=[
 ['radio','.radio-page','.radio-page .search-field'],
 ['media','.media-page','.media-heading h1'],
 ['audio','.settings-panel[data-settings-section=audio]','.settings-panel[data-settings-section=audio] .panel-heading h2'],
 ['network','.settings-panel[data-settings-section=network]','.settings-panel[data-settings-section=network] .panel-heading h2'],
 ['settings','.settings-page','.settings-intro-title h1'],
] as const;
type Destination=typeof destinations[number][0];
const building=(page:Page,id:Destination)=>page.locator(`button.city-building-entry[data-destination=${id}]`);
async function fixture(page:Page,ro:boolean,theme:string,instant='2026-10-24T10:00:00Z'){
 await page.addInitScript(()=>{(window as any).__cityMovieEnds=[];(window as any).__cityMoviePlays=[];for(const eventName of ['playing','ended'])document.addEventListener(eventName,event=>{const video=event.target as HTMLVideoElement;if(video.matches?.('.city-entry video'))(window as any)[eventName==='ended'?'__cityMovieEnds':'__cityMoviePlays'].push({direction:video.closest('.city-entry')?.getAttribute('data-direction'),src:video.getAttribute('src'),muted:video.muted,canonicalPageAttached:!!document.querySelector('.radio-page,.media-page,.settings-page')});},true);});
 const station={name:'Retained radio',url:'https://example.invalid/retained',favicon:'https://example.invalid/logo.svg'};
 const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,visualizerStyle:'off',timezone:'Europe/Bucharest',location:{name:'București · Sector 5',latitude:44.4,longitude:26.1},homeCards:[],navigationCollapsed:false,navigationAutoHide:false,decorativeAircraft:false,decorativeLunarDust:false,lastStation:station,favorites:[],shortcuts:[]},network:{available:true,state:'connected',connection:'Ethernet'},bluetooth:{available:true,powered:false,devices:[],prompts:[]},audio:{available:true,ready:true,volume:23,mute:false,outputs:[]},player:{state:'playing',kind:'radio',url:station.url,station_name:station.name,title:'Retained track'},weather:{timezone:'Europe/Bucharest',stale:false,current:{weather_code:0,is_day:1,temperature_c:14},daily:[{date:'2026-10-24',sunrise_epoch:Date.parse('2026-10-24T04:40:00Z')/1000,sunset_epoch:Date.parse('2026-10-24T15:16:00Z')/1000}],updated_at:instant,alerts:{state:'available',updated_at:instant,alerts:[]}}};
 const actions:any[]=[],errors:string[]=[];page.on('pageerror',error=>errors.push(String(error)));
 await page.route('**/api/**',async route=>{const req=route.request(),path=new URL(req.url()).pathname;if(req.method()!=='GET')actions.push({path,body:req.postDataJSON()});await route.fulfill({json:path==='/api/state'?state:path==='/api/session'?{token:'isolated-city-atmosphere-fixture'}:path==='/api/radio'?{stations:[station]}:path==='/api/media'?{items:[],roots:[]}:{} });});
 await page.clock.install({time:new Date(Date.parse(instant)-1000)});await page.clock.pauseAt(new Date(instant));
 await page.goto('/');await expect(page.locator('.ambient-home')).toBeVisible();return {state,actions,errors};
}
const returnControl=(page:Page,id:Destination)=>['audio','network','settings'].includes(id)?page.locator('.settings-back'):page.locator('.main-nav button').first();
async function returnCommand(page:Page,id:Destination){await returnControl(page,id).tap();}
async function noSideEffects(f:Awaited<ReturnType<typeof fixture>>,saved:string){
 expect(f.actions).toEqual([]);expect(f.errors).toEqual([]);expect(JSON.stringify(f.state)).toBe(saved);
}

const city=(page:Page)=>page.locator('.city-diorama');
const lighting=(page:Page)=>city(page).getAttribute('data-window-level').then(value=>Number(value));
async function settleState(page:Page){await page.clock.runFor(2700);}
async function at(page:Page,instant:string){await page.clock.setSystemTime(new Date(instant));await page.clock.runFor(1000);}
async function capture(page:Page,name:string){await page.screenshot({path:test.info().outputPath(name+'.png')});}
async function opaqueGround(page:Page){
 const image=page.locator('.city-architecture');await image.evaluate(node=>(node as HTMLImageElement).decode());
 await expect(image).toHaveCSS('opacity','1');
 const transparent=await image.evaluate(node=>{const image=node as HTMLImageElement,canvas=document.createElement('canvas');canvas.width=image.naturalWidth;canvas.height=image.naturalHeight;const ctx=canvas.getContext('2d')!;ctx.drawImage(image,0,0);return [...ctx.getImageData(0,canvas.height-4,canvas.width,4).data].filter((_,index)=>index%4===3).some(alpha=>alpha!==255);});
 expect(transparent).toBe(false);
}
for(const theme of ['ink','night'])test(`city atmosphere ${theme}: local-date solar windows fade without changing transport or ground`,async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro'),theme),saved=JSON.stringify(f.state);
 await expect(city(page)).toHaveAttribute('data-window-source','solar');await expect(page.locator('.app')).toHaveAttribute('data-theme',theme);expect(await lighting(page)).toBe(0);
 await expect(page.locator('.city-window-bank')).toHaveCount(3);await page.locator('.city-window-bank').evaluateAll(nodes=>Promise.all(nodes.map(node=>(node as HTMLImageElement).decode())));
 const windowPixels=await page.locator('.city-window-bank').evaluateAll(nodes=>nodes.map(node=>{const image=node as HTMLImageElement,canvas=document.createElement('canvas');canvas.width=image.naturalWidth;canvas.height=image.naturalHeight;const ctx=canvas.getContext('2d')!;ctx.drawImage(image,0,0);const pixels=ctx.getImageData(0,0,canvas.width,canvas.height).data;for(let index=3;index<pixels.length;index+=4)if(pixels[index]>0)return true;return false;}));expect(windowPixels).toEqual([true,true,true]);
 await opaqueGround(page);await capture(page,'solar-midday-'+theme);
 const levels:number[]=[];
 for(const instant of ['2026-10-24T14:56:00Z','2026-10-24T15:13:00Z','2026-10-24T15:16:00Z','2026-10-24T15:36:00Z']){
  await at(page,instant);await expect(city(page)).toHaveAttribute('data-window-source','solar');await expect(page.locator('.app')).toHaveAttribute('data-theme',theme);const value=await lighting(page);expect(Number.isFinite(value)).toBe(true);expect(value).toBeGreaterThanOrEqual(0);expect(value).toBeLessThanOrEqual(1);levels.push(value);await capture(page,'solar-'+instant.slice(11,16).replace(':','')+'-'+theme);
 }
 expect(levels[0]).toBe(0);expect(levels.at(-1)).toBe(1);expect(new Set(levels).size).toBeGreaterThanOrEqual(3);expect(levels.every((value,index)=>index===0||value>=levels[index-1])).toBe(true);
 const banks=await page.locator('.city-window-bank').evaluateAll(nodes=>nodes.map(node=>Number(getComputedStyle(node).opacity)));expect(banks.every(value=>Number.isFinite(value)&&value>0&&value<=1)).toBe(true);
 await opaqueGround(page);
 // Move backward to the same day's pre-sunrise instant, then observe a real dawn.
 const dawn:number[]=[];
 for(const instant of ['2026-10-24T04:20:00Z','2026-10-24T04:37:00Z','2026-10-24T04:40:00Z','2026-10-24T05:00:00Z']){await at(page,instant);await expect(city(page)).toHaveAttribute('data-window-source','solar');await expect(page.locator('.app')).toHaveAttribute('data-theme',theme);dawn.push(await lighting(page));await capture(page,'dawn-'+instant.slice(11,16).replace(':','')+'-'+theme);}
 expect(dawn[0]).toBe(1);expect(dawn.at(-1)).toBe(0);expect(new Set(dawn).size).toBeGreaterThanOrEqual(3);expect(dawn.every((value,index)=>Number.isFinite(value)&&value>=0&&value<=1&&(index===0||value<=dawn[index-1]))).toBe(true);
 // The next selected-location day starts while the UTC browser still shows24October.
 f.state.weather.daily=[{date:'2026-10-25',sunrise_epoch:Date.parse('2026-10-25T04:41:00Z')/1000,sunset_epoch:Date.parse('2026-10-25T15:14:00Z')/1000}];await at(page,'2026-10-24T21:30:00Z');await settleState(page);
 await expect(city(page)).toHaveAttribute('data-window-source','solar');expect(await lighting(page)).toBe(1);
 // Exclude the deliberate fixture weather mutation from the preservation oracle.
 f.state.weather.daily=JSON.parse(saved).weather.daily;await noSideEffects(f,saved);
});
for(const theme of ['ink','night'])test(`city atmosphere ${theme}: missing stale or malformed solar timing uses honest astronomy then unknown`,async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro'),theme),saved=JSON.stringify(f.state);
 const cases=[[],[{date:'2026-10-23',sunrise_epoch:1792740000,sunset_epoch:1792778160}],[{date:'2026-10-24',sunrise_epoch:Date.parse('2026-10-23T04:40:00Z')/1000,sunset_epoch:Date.parse('2026-10-23T15:16:00Z')/1000}],[{date:'invalid-date',sunrise_epoch:null,sunset_epoch:null}],[{date:'2026-10-24',sunrise_epoch:1e300,sunset_epoch:1e301}],[{date:'2026-10-24',sunrise_epoch:null,sunset_epoch:null}],[{date:'2026-10-24',sunrise_epoch:Date.parse('2026-10-24T15:16:00Z')/1000,sunset_epoch:Date.parse('2026-10-24T04:40:00Z')/1000}]];
 for(const [index,daily] of cases.entries()){f.state.weather.daily=daily;await settleState(page);await expect(city(page)).toHaveAttribute('data-window-source','astronomy');expect(await lighting(page)).toBe(0);await capture(page,`solar-fallback-${index}-${theme}`);}
 f.state.weather.daily=JSON.parse(saved).weather.daily;f.state.weather.timezone='Not/AZone';await settleState(page);await expect(city(page)).toHaveAttribute('data-window-source','astronomy');expect(await lighting(page)).toBe(0);await capture(page,'solar-invalid-provider-timezone-'+theme);
 f.state.weather.timezone='Europe/Bucharest';f.state.weather.stale=true;await settleState(page);await expect(city(page)).toHaveAttribute('data-window-source','astronomy');
 f.state.preferences.location.latitude=null;f.state.preferences.location.longitude=null;await settleState(page);await expect(city(page)).toHaveAttribute('data-window-source','unknown');expect(await lighting(page)).toBe(0);await capture(page,'solar-unknown-'+theme);
 f.state.preferences=JSON.parse(saved).preferences;f.state.weather=JSON.parse(saved).weather;await noSideEffects(f,saved);
});
for(const theme of ['ink','night'])test(`city atmosphere ${theme}: wet streets follow genuine rain and never invent a hazard`,async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro'),theme),saved=JSON.stringify(f.state);
 for(const [code,expected] of [[51,.30],[63,.52],[65,.72],[95,.52],[0,0],[73,0],[66,0],[999,0]] as const){
  f.state.weather.current.weather_code=code;await settleState(page);await expect.poll(async()=>Number(await page.locator('.city-road-reflections').getAttribute('data-wet-level'))).toBe(expected);await expect(page.locator('.city-road-reflections')).toHaveCSS('opacity',String(expected));await page.locator('.city-road-reflections').evaluate(node=>(node as HTMLImageElement).decode());await expect(page.locator('.scene-warning-illustration')).toHaveCount(0);await capture(page,`wet-${code}-${theme}`);await opaqueGround(page);
 }
 f.state.weather.current.weather_code=65;f.state.weather.stale=true;await settleState(page);await expect.poll(async()=>Number(await page.locator('.city-road-reflections').getAttribute('data-wet-level'))).toBe(0);await expect(page.locator('.scene-warning-illustration')).toHaveCount(0);await capture(page,'wet-stale-'+theme);
 f.state.weather=JSON.parse(saved).weather;await noSideEffects(f,saved);
});

for(const theme of ['ink','night'])for(const [id,target,focus] of destinations)test(`city return ${id} ${theme}: natural entrance and outward movie restore the originating building`,async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro'),theme),saved=JSON.stringify(f.state);await page.clock.resume();await building(page,id).tap();
 await expect(page.locator(target)).toBeVisible({timeout:9000});await expect(page.locator(focus)).toBeFocused();await capture(page,`return-${id}-${theme}-destination`);
 await returnCommand(page,id);
 await expect(page.locator('.ambient-home')).toBeVisible({timeout:9000});await expect(page.locator('.city-entry')).toHaveCount(0);await page.clock.runFor(100);await expect(building(page,id)).toBeFocused();expect(await page.evaluate(()=>(window as any).__cityMovieEnds.map((event:any)=>event.direction))).toEqual(['enter','exit']);const plays=await page.evaluate(()=>(window as any).__cityMoviePlays);expect([...new Set(plays.map((event:any)=>event.direction))]).toEqual(['enter','exit']);expect(plays.every((event:any)=>event.muted&&event.src===`/ambient/city-${event.direction==='enter'?'entry':'exit'}-${id}-day-v1.webm`)).toBe(true);expect(plays.find((event:any)=>event.direction==='exit').canonicalPageAttached).toBe(true);await noSideEffects(f,saved);await capture(page,`return-${id}-${theme}-home`);
});
for(const outcome of ['cancel','skip','error','reduced'] as const)for(const [index,[id,target,focus]] of destinations.entries())test(`city return ${id}: ${outcome} stays usable and preserves the canonical task`,async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro'),index%2?'ink':'night'),saved=JSON.stringify(f.state);await page.emulateMedia({reducedMotion:'reduce'});await building(page,id).tap();await expect(page.locator(target)).toBeVisible();
  // Direct reduced-motion arrival schedules focus on the deliberately paused rAF clock.
  await page.clock.runFor(100);await expect(page.locator(focus)).toBeFocused();await page.emulateMedia({reducedMotion:'no-preference'});
 let release!:()=>void;let held=new Promise<void>(resolve=>release=resolve);await page.route(`**/ambient/city-exit-${id}-*.webm`,async route=>{await held;await route.abort('failed').catch(()=>{});});
 await returnCommand(page,id);await expect(page.locator('.city-entry')).toHaveAttribute('data-direction','exit');await expect(page.locator('.city-entry')).toHaveAttribute('data-phase','loading');await expect(page.locator(target)).toBeAttached();await capture(page,`return-${id}-${outcome}-loading`);
 if(outcome==='cancel'){
  await page.locator('.radio-entry-actions button').first().tap();release();await page.clock.runFor(6000);await expect(page.locator('.city-entry')).toHaveCount(0);await expect(page.locator(target)).toBeVisible();await expect(returnControl(page,id)).toBeFocused();await expect(page.locator('.ambient-home')).toHaveCount(0);await capture(page,`return-${id}-cancel-stays-destination`);
  // Retry needs a fresh loading gate; the first failed request has already settled.
  held=new Promise<void>(resolve=>release=resolve);
  await returnCommand(page,id);await expect(page.locator('.city-entry')).toHaveAttribute('data-direction','exit');await page.locator('.radio-entry-actions button').last().tap();release();await expect(page.locator('.ambient-home')).toBeVisible();await page.clock.runFor(100);await expect(building(page,id)).toBeFocused();
 }else{
  if(outcome==='skip')await page.locator('.radio-entry-actions button').last().tap();else if(outcome==='error')release();else await page.emulateMedia({reducedMotion:'reduce'});
  await expect(page.locator('.ambient-home')).toBeVisible();await expect(page.locator('.city-entry')).toHaveCount(0);await page.clock.runFor(100);await expect(building(page,id)).toBeFocused();release();
 }
 await noSideEffects(f,saved);await capture(page,`return-${id}-${outcome}-result`);
});

for(const theme of ['ink','night'])test(`city return ${theme}: ordinary navigation and a changed destination do not replay an old building exit`,async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro'),theme),saved=JSON.stringify(f.state);
 await page.locator('.main-nav button').nth(1).tap();await expect(page.locator('.radio-page')).toBeVisible();await page.locator('.main-nav button').first().tap();await expect(page.locator('.ambient-home')).toBeVisible();await expect(page.locator('.city-entry')).toHaveCount(0);
 await page.emulateMedia({reducedMotion:'reduce'});await building(page,'radio').tap();await expect(page.locator('.radio-page')).toBeVisible();await page.emulateMedia({reducedMotion:'no-preference'});
 await page.locator('.main-nav button').nth(2).tap();await expect(page.locator('.media-page')).toBeVisible();await page.locator('.main-nav button').first().tap();await expect(page.locator('.ambient-home')).toBeVisible();await expect(page.locator('.city-entry')).toHaveCount(0);expect(await page.evaluate(()=>(window as any).__cityMovieEnds)).toEqual([]);await noSideEffects(f,saved);await capture(page,'ordinary-navigation-'+theme);
});

for(const theme of ['ink','night'])test(`city return ${theme}: reduced motion already active skips every outward movie`,async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro'),theme),saved=JSON.stringify(f.state),exitRequests:string[]=[];page.on('request',request=>{if(new URL(request.url()).pathname.includes('/ambient/city-exit-'))exitRequests.push(request.url());});await page.emulateMedia({reducedMotion:'reduce'});
 for(const [id,target,focus] of destinations){await building(page,id).tap();await expect(page.locator(target)).toBeVisible();
  // Direct reduced-motion arrival schedules focus on the deliberately paused rAF clock.
  await page.clock.runFor(100);await expect(page.locator(focus)).toBeFocused();await returnCommand(page,id);await page.clock.runFor(100);await expect(page.locator('.ambient-home')).toBeVisible();await expect(page.locator('.city-entry')).toHaveCount(0);await expect(building(page,id)).toBeFocused();}
 expect(exitRequests).toEqual([]);await noSideEffects(f,saved);await capture(page,'reduced-direct-'+theme);
});
