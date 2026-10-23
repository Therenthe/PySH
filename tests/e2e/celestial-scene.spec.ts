import {test,expect,type Page} from '@playwright/test';

async function fixture(page:Page,ro:boolean,theme:string,time:string){
 const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,visualizerStyle:'off',homeCards:[],location:{name:'București · Sector 5',latitude:44.4,longitude:26.1},decorativeAircraft:false,decorativeLunarDust:false},network:{state:'connected'},bluetooth:{devices:[],prompts:[]},audio:{ready:true,volume:30,mute:false},player:{state:'playing',kind:'radio',station_name:'Retained radio',url:'https://example.org/radio'},weather:{current:{temperature_c:13,weather_code:0,is_day:0},daily:[],stale:false}};
 let fail=false;const writes:any[]=[];
 await page.addInitScript(()=>{crypto.getRandomValues=((a:Uint32Array)=>{a.fill(0);return a;}) as typeof crypto.getRandomValues;});
 await page.route('**/api/**',async route=>{const path=new URL(route.request().url()).pathname;let json:any={ok:true};if(path==='/api/session')json={token:'fixture'};else if(path==='/api/state')json=state;else if(path==='/api/preferences'){writes.push(route.request().postDataJSON());if(fail)return route.fulfill({status:500,json:{error:'save_failed'}});Object.assign(state.preferences,route.request().postDataJSON());json=state.preferences;}await route.fulfill({json});});
 await page.clock.install({time:new Date(time)});await page.goto('/');await expect(page.locator('.ambient-home')).toBeVisible();
 return {state,writes,fail:(value:boolean)=>{fail=value;}};
}

async function assertSparseBlenderStars(page:Page){
 const stars=page.locator('[data-blender-star]');await expect(stars).toHaveCount(170);await expect(page.locator('.ambient-stars')).toHaveCSS('opacity','0.8');
 const points=await stars.evaluateAll(nodes=>nodes.map(node=>({id:Number(node.getAttribute('data-blender-star')),x:Number(node.getAttribute('x'))+Number(node.getAttribute('width'))/2,y:Number(node.getAttribute('y'))+Number(node.getAttribute('height'))/2,size:Number(node.getAttribute('width'))})));
 for(const star of points){expect(star.x).toBeCloseTo(12+(star.id*137.507%670),6);expect(star.y).toBeCloseTo(8+((star.id*73.13+star.id*star.id*3.11)%360),6);expect(star.size).toBeLessThanOrEqual(7);}
 expect(points.filter(s=>s.size>5)).toHaveLength(5);
 const sprite=await page.locator('.ambient-stars image').first().evaluate(async el=>{
  const image=new Image();image.src=el.getAttribute('href')!;await image.decode();const canvas=document.createElement('canvas');canvas.width=image.width;canvas.height=image.height;const ctx=canvas.getContext('2d')!;ctx.drawImage(image,0,0);const pixels=ctx.getImageData(0,0,image.width,image.height).data;let occupied=0;for(let i=3;i<pixels.length;i+=4)if(pixels[i]>20)occupied++;return {width:image.width,height:image.height,coverage:occupied/(image.width*image.height),src:image.src};
 });
 expect(sprite.src).toContain('/ambient/sky3d/star-glints-blender-v1.png');expect([sprite.width,sprite.height]).toEqual([96,96]);expect(sprite.coverage).toBeGreaterThan(.002);expect(sprite.coverage).toBeLessThan(.5);
}

async function assertRenderedMoonPhase(page:Page){
 await expect(page.locator('.blender-moon')).toHaveCSS('background-image',/moon-phases-blender-v1\.png/);
 const result=await page.locator('.blender-moon').evaluate(async el=>{
  const illumination=Number(el.getAttribute('data-lunar-illumination')),waxing=el.getAttribute('data-lunar-direction')==='waxing',frame=Number(el.getAttribute('data-blender-phase-frame')),style=getComputedStyle(el);
  const image=new Image();image.src=style.backgroundImage.match(/url\(["']?([^"')]+)/)![1];await image.decode();const tile=image.width/16,canvas=document.createElement('canvas');canvas.width=tile;canvas.height=tile;const ctx=canvas.getContext('2d')!;ctx.drawImage(image,frame%16*tile,Math.floor(frame/16)*tile,tile,tile,0,0,tile,tile);const data=ctx.getImageData(0,0,tile,tile).data;
  const sums=[0,0],counts=[0,0];for(let y=0;y<tile;y++)for(let x=0;x<tile;x++){const i=(y*tile+x)*4;if(data[i+3]>200&&Math.hypot(x-tile/2,y-tile/2)<tile*.38){const half=x<tile/2?0:1;sums[half]+=.2126*data[i]+.7152*data[i+1]+.0722*data[i+2];counts[half]++;}}
  return {illumination,waxing,frame,dimensions:[image.width,image.height],backgroundPosition:style.backgroundPosition,light:sums.map((sum,i)=>sum/counts[i])};
 });
 expect(result.dimensions).toEqual([2304,1152]);expect(result.frame).toBeGreaterThanOrEqual(0);expect(result.frame).toBeLessThan(128);
 expect(Math.abs((1-Math.cos(result.frame/128*Math.PI*2))/2-result.illumination)).toBeLessThan(.013);
 expect(result.waxing?result.frame<=64:result.frame>=64).toBe(true);
 // This date is close to a waning half Moon: actual raster must illuminate its left hemisphere.
 expect(result.illumination).toBeGreaterThan(.25);expect(result.illumination).toBeLessThan(.75);expect(result.waxing).toBe(false);expect(result.light[0]).toBeGreaterThan(result.light[1]*1.5);
 const [column,row]=result.backgroundPosition.split(' ').map(parseFloat);expect(column).toBeCloseTo(result.frame%16/15*100,3);expect(row).toBeCloseTo(Math.floor(result.frame/16)/7*100,3);
}

for(const theme of ['ink','night'])test(`celestial positions update with time, independent of theme and cached is_day ${theme}`,async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro'),theme,'2026-10-04T06:00:00Z');
 const read=()=>page.locator('[data-celestial-body=sun]').evaluate(el=>({x:parseFloat((el as HTMLElement).style.left),y:parseFloat((el as HTMLElement).style.top),alt:Number(el.getAttribute('data-altitude')),az:Number(el.getAttribute('data-azimuth'))}));
 f.state.preferences.homeCards=['weather','forecast'];f.state.weather.daily=[{date:'2026-10-03',max_c:20,min_c:10,weather_code:0}];await page.clock.runFor(3500);await expect(page.locator('.home-weather .temp-row svg circle')).toHaveCount(1);await expect(page.locator('.ambient-sun')).toBeVisible();const morning=await read();expect(morning.x).toBeGreaterThan(50);expect(Math.abs(morning.alt-16.918517)).toBeLessThan(.2);
 await page.clock.setFixedTime(new Date('2026-10-04T10:00:00Z'));await page.clock.runFor(1100);const noon=await read();expect(noon.x).toBeLessThan(morning.x);expect(noon.y).toBeLessThan(morning.y);expect(noon.y).toBeLessThan(40);expect(noon.y).toBeGreaterThan(14);expect(Math.abs(noon.alt-41.157556)).toBeLessThan(.2);await expect(page.locator('.ambient-moon')).toHaveCount(0);await page.screenshot({path:info.outputPath(`sun-noon-${theme}.png`)});
 await page.clock.setFixedTime(new Date('2026-10-04T15:00:00Z'));await page.clock.runFor(1100);const evening=await read();expect(evening.x).toBeLessThan(noon.x);expect(evening.y).toBeGreaterThan(noon.y);
 await page.clock.setFixedTime(new Date('2026-10-04T18:00:00Z'));await page.clock.runFor(1100);await expect(page.locator('.ambient-sun,.ambient-moon')).toHaveCount(0);
 await page.clock.setFixedTime(new Date('2026-10-04T23:00:00Z'));await page.clock.runFor(1100);await expect(page.locator('.ambient-moon')).toBeVisible();await expect(page.locator('.ambient-sun')).toHaveCount(0);await expect(page.locator('.sky-night')).toHaveCount(1);await expect(page.locator('.home-weather .temp-row svg circle')).toHaveCount(0);await expect(page.locator('.ambient-forecast h2')).toHaveText(info.project.name.endsWith('ro')?'Prognoză 5 zile':'5-day forecast');await expect(page.locator('.ambient-star-texture')).toHaveCount(0);await expect(page.locator('.city-material')).toHaveCount(0);await expect(page.locator('.city-diorama')).toHaveAttribute('data-city-version','blender-v2');await expect(page.locator('.city-architecture')).toHaveAttribute('src','/ambient/gothic-city-night-v2.png');await expect.poll(()=>page.locator('.city-architecture').evaluate(el=>(el as HTMLImageElement).complete&&(el as HTMLImageElement).naturalWidth>0)).toBe(true);await assertSparseBlenderStars(page);await assertRenderedMoonPhase(page);await expect(page.locator('[data-night-encounter],.bat-signal,.batplane,.night-encounters')).toHaveCount(0);await page.screenshot({path:info.outputPath(`moon-rising-${theme}.png`)});
 f.state.preferences.location={name:'Unknown'};await page.clock.runFor(3500);await expect(page.locator('[data-celestial-body]')).toHaveCount(0);
});

for(const theme of ['ink','night'])for(const key of ['decorativeAircraft','decorativeLunarDust'] as const)test(`ambient setting ${key} owns exact retry, prior value and reload ${theme}`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,'2026-10-04T23:00:00Z');
 const settings=async()=>{await page.locator('.main-nav button').nth(3).tap();await page.locator('.settings-tabs button').filter({hasText:ro?'Acasă':'Home'}).tap();};
 const button=page.getByRole('button',{name:key==='decorativeAircraft'?(ro?'Aeronave decorative':'Decorative aircraft'):(ro?'Praf lunar decorativ':'Decorative lunar dust'),exact:true});await settings();await button.scrollIntoViewIfNeeded();await expect(button).toHaveAttribute('aria-pressed','false');const bounds=(await button.boundingBox())!;expect(bounds.width).toBeGreaterThanOrEqual(48);expect(bounds.height).toBeGreaterThanOrEqual(48);
 f.fail(true);await button.tap();await expect(page.locator('.error-strip')).toBeVisible();await expect(button).toHaveAttribute('aria-pressed','false');expect(f.state.preferences[key]).toBe(false);
 f.fail(false);await page.locator('.error-strip').getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true}).tap();await expect(button).toHaveAttribute('aria-pressed','true');expect(f.writes).toEqual([{[key]:true},{[key]:true}]);await page.reload();await settings();await button.scrollIntoViewIfNeeded();await expect(button).toHaveAttribute('aria-pressed','true');await expect(page.getByRole('button',{name:/superheroes|supereroi/i})).toHaveCount(0);
});

test('lunar dust follows the actual moving Moon center and clears below the horizon',async({page},info)=>{
 const f=await fixture(page,info.project.name.endsWith('ro'),'night','2026-10-04T23:00:00Z');f.state.preferences.decorativeLunarDust=true;await page.clock.runFor(2500);await page.clock.runFor(65020);await expect(page.locator('.ambient-lunar-event')).toHaveCount(1);
 const gap=await page.evaluate(()=>{const a=document.querySelector('.celestial-anchor[data-celestial-body=moon]')!.getBoundingClientRect(),b=document.querySelector('.ambient-lunar-event')!.getBoundingClientRect();return Math.hypot(a.x+a.width/2-b.x-b.width/2,a.y+a.height/2-b.y-b.height/2);});expect(gap).toBeLessThan(.1);
 await page.clock.setFixedTime(new Date('2026-10-04T18:00:00Z'));await page.clock.runFor(1100);await expect(page.locator('.ambient-moon,.ambient-lunar-event')).toHaveCount(0);
});
