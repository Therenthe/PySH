import {test,expect,type Page} from '@playwright/test';

// Isolated loopback state; movies are actual local Blender exports.
async function fixture(page:Page,ro:boolean,theme:string){
 const now=new Date('2026-10-24T10:00:00Z');
 const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,visualizerStyle:'off',timezone:'Europe/Bucharest',location:{name:'București · Sector 5',latitude:44.4,longitude:26.1},homeCards:[],navigationCollapsed:true,navigationAutoHide:false,decorativeAircraft:false,decorativeLunarDust:false,favorites:[],shortcuts:[]},network:{available:true,state:'connected'},bluetooth:{available:true,powered:false,devices:[],prompts:[]},audio:{available:true,ready:true,volume:3,mute:false,outputs:[]},player:{state:'paused',kind:'radio',url:'https://example.invalid/retained',station_name:'Retained station'},weather:{stale:false,current:{weather_code:3,is_day:1,temperature_c:14},daily:[],updated_at:now.toISOString(),alerts:{state:'available',updated_at:now.toISOString(),alerts:[]}}};
 const writes:string[]=[],errors:string[]=[];page.on('pageerror',error=>errors.push(String(error)));
 await page.route('**/api/**',async route=>{const req=route.request(),path=new URL(req.url()).pathname;if(req.method()!=='GET')writes.push(path);const json=path==='/api/state'?state:path==='/api/session'?{token:'city-destinations-fixture'}:path==='/api/radio'?{stations:[]}:path==='/api/media'?{items:[],roots:[]}:{};await route.fulfill({json});});
 await page.clock.install({time:now});await page.goto('/');await expect(page.locator('.ambient-home')).toBeVisible();return {state,writes,errors};
}
const destinations=[['radio','.radio-page','.radio-page .search-field'],['media','.media-page','.media-heading h1'],['audio','.settings-panel[data-settings-section=audio]','.settings-panel[data-settings-section=audio] .panel-heading h2'],['network','.settings-panel[data-settings-section=network]','.settings-panel[data-settings-section=network] .panel-heading h2'],['settings','.settings-page','.settings-intro-title h1']] as const;
const button=(page:Page,id:string)=>page.locator(`button.city-building-entry[data-destination=${id}]`);
for(const theme of ['ink','night'])for(const [id,target,focus] of destinations)test(`City ${id} ${theme}: actual entrance and canonical destination preserve paused transport`,async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro'),theme),saved=JSON.stringify(f.state);await expect(button(page,id)).toBeVisible();const b=(await button(page,id).boundingBox())!;expect(b.width).toBeGreaterThanOrEqual(48);expect(b.height).toBeGreaterThanOrEqual(48);
 await page.clock.resume();await button(page,id).tap();await expect(page.locator(`.city-entry[data-destination=${id}]`)).toHaveAttribute('data-phase','playing');const video=page.locator('.city-entry video');await expect(video).toHaveJSProperty('muted',true);await expect(video).toHaveAttribute('src',`/ambient/city-entry-${id}-day-v1.webm`);
 await expect(page.locator(target)).toBeVisible({timeout:9000});await expect(page.locator('.city-entry')).toHaveCount(0);await expect(page.locator(focus)).toBeFocused();expect(f.writes).toEqual([]);expect(f.errors).toEqual([]);expect(JSON.stringify(f.state)).toBe(saved);await page.screenshot({path:info.outputPath(`${id}-${theme}-arrival.png`)});
 if(['audio','network','settings'].includes(id))await page.locator('.settings-back').tap();else{await page.locator('.navigation-toggle').tap();await expect(page.locator('.app')).toHaveAttribute('data-navigation','open');await page.locator('.main-nav button').first().tap();}await expect(page.locator('.ambient-home')).toBeVisible();await expect(button(page,id)).toBeFocused();
});

for(const theme of ['ink','night'])for(const [id,target,focus] of destinations)test(`City ${id} ${theme}: cancelled load and failed-media fallback stay usable`,async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro'),theme);let release!:()=>void;const held=new Promise<void>(resolve=>release=resolve);await page.route(`**/ambient/city-entry-${id}-*.webm`,async route=>{await held;await route.abort('failed').catch(()=>{});});
 await button(page,id).tap();await expect(page.locator('.city-entry')).toHaveAttribute('data-phase','loading');await page.locator('.radio-entry-actions button').first().tap();await expect(button(page,id)).toBeFocused();await page.clock.runFor(6000);await expect(page.locator('.city-entry')).toHaveCount(0);await expect(page.locator('.ambient-home')).toBeVisible();
 await button(page,id).tap();release();await expect(page.locator(target)).toBeVisible();await page.clock.runFor(80);await expect(page.locator(focus)).toBeFocused();expect(f.writes).toEqual([]);expect(f.errors).toEqual([]);
});

test('physical clock center stays fixed through rail, ambient and Android presence',async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro'),'night');f.state.remote={connected:true,count:1};await page.clock.runFor(2700);
 const centered=async()=>{const b=(await page.locator('.top-clock').boundingBox())!;expect(Math.abs(b.x+b.width/2-400)).toBeLessThan(1);};await centered();await page.locator('.navigation-toggle').tap();await page.clock.runFor(400);await centered();await page.clock.runFor(31000);await centered();expect(f.errors).toEqual([]);
});

for(const theme of ['ink','night'])test(`City ground ${theme}: full-width opaque support and foreground rail remain grounded`,async({page},info)=>{
 await fixture(page,info.project.name.endsWith('ro'),theme);const architecture=page.locator('.city-architecture');await architecture.evaluate(n=>(n as HTMLImageElement).decode());await expect(architecture).toHaveCSS('opacity','1');await expect(page.locator('.city-scenery')).toHaveCSS('opacity','1');
 const ground=await architecture.evaluate(node=>{const image=node as HTMLImageElement,c=document.createElement('canvas');c.width=image.naturalWidth;c.height=image.naturalHeight;const ctx=c.getContext('2d')!;ctx.drawImage(image,0,0);const pixels=ctx.getImageData(0,c.height-4,c.width,4).data;let transparent=0;for(let i=3;i<pixels.length;i+=4)if(pixels[i]!==255)transparent++;return{transparent,width:c.width,height:c.height};});expect(ground).toEqual({transparent:0,width:1600,height:570});
 await expect(page.locator('.city-rail-front')).toHaveAttribute('src','/ambient/gothic-city-rail-front-day-v4.png');await page.locator('.city-rail-front').evaluate(n=>(n as HTMLImageElement).decode());await expect(page.locator('.city-metro')).toHaveAttribute('src','/ambient/metro-v4.png');
});

test('connected network without a profile name is not labelled offline',async({page},info)=>{
 const ro=info.project.name.endsWith('ro');await page.emulateMedia({reducedMotion:'reduce'});await fixture(page,ro,'ink');await button(page,'network').tap();await expect(page.locator('.settings-panel[data-settings-section=network] .panel-heading small')).toHaveText(ro?'Conectat':'Connected');
});
