import {test,expect,type Page} from '@playwright/test';
import {createMeteor} from '../../app/ui/src/Meteors';

test('meteor geometry follows a descending direction with independently varied trajectory and speed',()=>{
 let seed=173;const rng=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
 const samples=Array.from({length:128},(_,id)=>createMeteor(id,rng));
 for(const m of samples){expect(m.dy).toBeGreaterThan(0);const angle=Math.atan2(m.dy,m.dx)*180/Math.PI;expect(angle).toBeCloseTo(m.angle,8);expect(m.length).toBeGreaterThanOrEqual(38);expect(m.length).toBeLessThan(130);expect(Math.hypot(m.dx,m.dy)/(m.duration/1000)).toBeGreaterThanOrEqual(175);}
 expect(samples.some(m=>m.dx>0)).toBe(true);expect(samples.some(m=>m.dx<0)).toBe(true);
 for(const key of ['length','angle','duration','brightness','left','top','thickness'] as const)expect(new Set(samples.map(m=>m[key].toFixed(3))).size).toBeGreaterThan(100);
});
async function night(page:Page,lang:string,theme:string){
 const state={preferences:{language:lang,theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,visualizerStyle:'off',timezone:'Europe/Bucharest',favorites:[],shortcuts:[]},network:{state:'connected'},bluetooth:{devices:[],prompts:[]},audio:{ready:false},player:{state:'idle'},weather:{stale:false,current:{temperature_c:13,weather_code:0,is_day:0},daily:[]}};
 await page.route('**/api/**',r=>r.fulfill({json:new URL(r.request().url()).pathname==='/api/state'?state:{token:'test'}}));
 await page.clock.install();await page.goto('/');await expect(page.locator('.ambient-moon')).toBeVisible();
}
async function awaitMeteor(page:Page){for(let i=0;i<200;i++){await page.clock.runFor(100);if(await page.locator('.meteor-transient').count())return;}throw new Error('No decorative meteor appeared within the allowed initial delay');}
for(const theme of ['ink','night'])test(`leading meteor head moves down with its tail behind it in ${theme}`,async({page},info)=>{
 await night(page,info.project.name.endsWith('ro')?'ro':'en',theme);await awaitMeteor(page);
 const shape=await page.locator('.meteor-transient').first().evaluate(el=>{
  const animation=el.getAnimations()[0];animation.pause();const duration=Number(animation.effect!.getTiming().duration);
  const sample=(fraction:number)=>{animation.currentTime=duration*fraction;const head=el.querySelector('.meteor-head')!.getBoundingClientRect(),tail=el.querySelector('.meteor-tail')!.getBoundingClientRect();return {head:{x:head.x+head.width/2,y:head.y+head.height/2},tail:{x:tail.x+tail.width/2,y:tail.y+tail.height/2}};};
  const first=sample(.2),second=sample(.65),css=getComputedStyle(el);return {first,second,dx:parseFloat(css.getPropertyValue('--meteor-dx')),dy:parseFloat(css.getPropertyValue('--meteor-dy')),background:getComputedStyle(el.querySelector('.meteor-tail')!).backgroundImage};
 });
 expect(shape.second.head.y).toBeGreaterThan(shape.first.head.y);expect((shape.second.head.x-shape.first.head.x)*shape.dx).toBeGreaterThan(0);
 for(const sample of [shape.first,shape.second])expect((sample.head.x-sample.tail.x)*shape.dx+(sample.head.y-sample.tail.y)*shape.dy).toBeGreaterThan(0);
 expect(shape.background).toContain('linear-gradient');await page.screenshot({path:info.outputPath(`meteor-leading-head-${theme}.png`)});
});
test('meteors stop and clear when hidden or reduced motion is enabled',async({page},info)=>{
 await night(page,info.project.name.endsWith('ro')?'ro':'en','night');await awaitMeteor(page);
 await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'));});await expect(page.locator('.meteor-transient')).toHaveCount(0);await page.clock.runFor(60000);await expect(page.locator('.meteor-transient')).toHaveCount(0);
 await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:false});document.dispatchEvent(new Event('visibilitychange'));});await awaitMeteor(page);
 await page.emulateMedia({reducedMotion:'reduce'});await expect(page.locator('.meteor-transient')).toHaveCount(0);await page.clock.runFor(60000);await expect(page.locator('.meteor-transient')).toHaveCount(0);
});
