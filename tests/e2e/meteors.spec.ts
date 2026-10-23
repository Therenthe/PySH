import {test,expect,type Page} from '@playwright/test';

test('meteor geometry follows a descending direction with independently varied trajectory and speed',async({page},info)=>{
 await night(page,info.project.name.endsWith('ro')?'ro':'en','night');
 const samples=await page.evaluate(async()=>{const {createMeteor}=await import('/src/Meteors.tsx' as string);let seed=173;const rng=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};return Array.from({length:128},(_,id)=>createMeteor(id,rng));});
 for(const m of samples){expect(m.dy).toBeGreaterThan(0);const angle=Math.atan2(m.dy,m.dx)*180/Math.PI;expect(angle).toBeCloseTo(m.angle,8);expect(m.length).toBeGreaterThanOrEqual(38);expect(m.length).toBeLessThan(130);expect(Math.hypot(m.dx,m.dy)/(m.duration/1000)).toBeGreaterThanOrEqual(175);}
 expect(samples.some(m=>m.dx>0)).toBe(true);expect(samples.some(m=>m.dx<0)).toBe(true);
 for(const key of ['length','angle','duration','brightness','left','top','thickness'] as const)expect(new Set(samples.map(m=>m[key].toFixed(3))).size).toBeGreaterThan(100);
});
async function night(page:Page,lang:string,theme:string){
 const state={preferences:{language:lang,theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,visualizerStyle:'off',timezone:'Europe/Bucharest',favorites:[],shortcuts:[]},network:{state:'connected'},bluetooth:{devices:[],prompts:[]},audio:{ready:false},player:{state:'idle'},weather:{stale:false,current:{temperature_c:13,weather_code:0,is_day:0},daily:[]}};
 await page.route('**/api/**',r=>r.fulfill({json:new URL(r.request().url()).pathname==='/api/state'?state:{token:'test'}}));
 (state.preferences as any).location={name:'București',latitude:44.4,longitude:26.1};
 await page.clock.install({time:new Date('2026-10-04T23:00:00Z')});await page.goto('/');await expect(page.locator('.ambient-moon')).toBeVisible();
}
async function awaitMeteor(page:Page){for(let i=0;i<200;i++){await page.clock.runFor(100);if(await page.locator('.meteor-transient').count())return;}throw new Error('No decorative meteor appeared within the allowed initial delay');}
for(const theme of ['ink','night'])test(`leading meteor head moves down with its tail behind it in ${theme}`,async({page},info)=>{
 await night(page,info.project.name.endsWith('ro')?'ro':'en',theme);await awaitMeteor(page);
 const shape=await page.locator('.meteor-transient').first().evaluate(async el=>{
  const animation=el.getAnimations()[0];animation.pause();const duration=Number(animation.effect!.getTiming().duration);
  const sprite=el.querySelector('.blender-meteor')!,style=getComputedStyle(sprite),image=new Image();image.src=style.backgroundImage.match(/url\(["']?([^"')]+)/)![1];await image.decode();
  const canvas=document.createElement('canvas');canvas.width=image.width;canvas.height=image.height;const ctx=canvas.getContext('2d')!;ctx.drawImage(image,0,0);const pixels=ctx.getImageData(0,0,image.width,image.height).data;
  const columns=Array.from({length:image.width},(_,x)=>{let value=0;for(let y=0;y<image.height;y++){const i=(y*image.width+x)*4;value+=(.2126*pixels[i]+.7152*pixels[i+1]+.0722*pixels[i+2])*pixels[i+3]/255;}return value;});
  const peak=Math.max(...columns),headColumn=columns.indexOf(peak);let tailWeight=0,tailX=0;for(let x=0;x<image.width*.75;x++){tailWeight+=columns[x];tailX+=x*columns[x];}tailX/=tailWeight;
  const spriteMatrix=new DOMMatrix(style.transform),width=parseFloat(style.width),height=parseFloat(style.height);
  const sample=(fraction:number)=>{animation.currentTime=duration*fraction;const carrier=el.getBoundingClientRect(),matrix=new DOMMatrix(getComputedStyle(el).transform);
   const point=(x:number)=>{const local=new DOMPoint(x/image.width*width,height/2).matrixTransform(spriteMatrix);return {x:carrier.x+matrix.a*local.x+matrix.c*local.y,y:carrier.y+matrix.b*local.x+matrix.d*local.y};};return {head:point(headColumn),tail:point(tailX)};};
  const first=sample(.2),second=sample(.65),css=getComputedStyle(el);return {first,second,dx:parseFloat(css.getPropertyValue('--meteor-dx')),dy:parseFloat(css.getPropertyValue('--meteor-dy')),src:image.src,size:[image.width,image.height],head:headColumn/image.width,tail:tailX/image.width,peak,tailWeight,bodyPeak:Math.max(...columns.slice(0,Math.floor(image.width*.75)))};
 });
 expect(shape.second.head.y).toBeGreaterThan(shape.first.head.y);expect((shape.second.head.x-shape.first.head.x)*shape.dx).toBeGreaterThan(0);
 for(const sample of [shape.first,shape.second])expect((sample.head.x-sample.tail.x)*shape.dx+(sample.head.y-sample.tail.y)*shape.dy).toBeGreaterThan(0);
 expect(shape.src).toContain('/ambient/sky3d/meteor-blender-v1.png');expect(shape.size).toEqual([256,32]);expect(shape.head).toBeGreaterThan(.9);expect(shape.head).toBeLessThan(.99);expect(shape.tail).toBeLessThan(.75);expect(shape.tailWeight).toBeGreaterThan(0);expect(shape.peak).toBeGreaterThan(shape.bodyPeak*1.2);
 await page.screenshot({path:info.outputPath(`meteor-leading-head-${theme}.png`)});
});
test('meteors stop and clear when hidden or reduced motion is enabled',async({page},info)=>{
 await night(page,info.project.name.endsWith('ro')?'ro':'en','night');await awaitMeteor(page);
 await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'));});await expect(page.locator('.meteor-transient')).toHaveCount(0);await page.clock.runFor(60000);await expect(page.locator('.meteor-transient')).toHaveCount(0);
 await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:false});document.dispatchEvent(new Event('visibilitychange'));});await awaitMeteor(page);
 await page.emulateMedia({reducedMotion:'reduce'});await expect(page.locator('.meteor-transient')).toHaveCount(0);await page.clock.runFor(60000);await expect(page.locator('.meteor-transient')).toHaveCount(0);
});
