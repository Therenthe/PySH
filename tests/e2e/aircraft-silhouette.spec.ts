import {test,expect} from '@playwright/test';

for(const theme of ['ink','night'])for(const direction of ['east','west'])test(`aircraft swept wings ${direction} ${theme}`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro'),west=direction==='west';
 await page.addInitScript(west=>{crypto.getRandomValues=((array:Uint32Array)=>{array.fill(west?4294967295:0);return array;}) as typeof crypto.getRandomValues;},west);
 await page.route('**/api/**',route=>{const path=new URL(route.request().url()).pathname;return route.fulfill({json:path==='/api/session'?{token:'fixture'}:path==='/api/state'?{preferences:{language:ro?'ro':'en',theme,nightEnabled:false,setupComplete:true,screensaverMinutes:0,decorativeAircraft:true},network:{},bluetooth:{devices:[],prompts:[]},audio:{},player:{},weather:{current:{weather_code:0,is_day:theme==='ink'?1:0},daily:[]}}:{ok:true}});});
 await page.clock.install({time:new Date('2026-10-04T12:00:00Z')});await page.goto('/');
 await page.clock.runFor(west?50020:18020);const flight=page.locator('.ambient-flight');await expect(flight).toHaveCount(1);
 await flight.evaluate(el=>{el.getAnimations().forEach(animation=>{animation.currentTime=Number(getComputedStyle(el).getPropertyValue('--flight-duration').replace('ms',''))/2;animation.pause();});el.getAnimations({subtree:true}).filter(a=>a.effect?.target!==el).forEach(a=>a.pause());});
 const geometry=await flight.locator('svg').evaluate(async svg=>{
  const node=svg as SVGSVGElement,matrix=node.getScreenCTM()!;
  const point=(x:number,y:number)=>new DOMPoint(x,y).matrixTransform(matrix);
  const nose=point(38,10),tail=point(2,10),upperTip=point(13,2),lowerTip=point(13,18),upperRoot=point(21,7),lowerRoot=point(21,13);
  const forward={x:nose.x-tail.x,y:nose.y-tail.y};
  const swept=(tip:DOMPoint,root:DOMPoint)=>(tip.x-root.x)*forward.x+(tip.y-root.y)*forward.y;
  // Rasterize the real outline, without navigation-light animation, rather than testing path strings.
  const clone=node.cloneNode(true) as SVGSVGElement;clone.setAttribute('xmlns','http://www.w3.org/2000/svg');clone.removeAttribute('style');clone.setAttribute('width','400');clone.setAttribute('height','200');clone.querySelectorAll('circle').forEach(n=>n.remove());clone.querySelector('path')!.setAttribute('fill','#000');
  const image=new Image();image.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(new XMLSerializer().serializeToString(clone));await image.decode();
  const canvas=document.createElement('canvas');canvas.width=400;canvas.height=200;const ctx=canvas.getContext('2d')!;ctx.drawImage(image,0,0);const data=ctx.getImageData(0,0,400,200).data;
  const extent=(y:number,minX=0)=>{const xs=[];for(let x=Math.ceil(minX*10);x<400;x++)if(data[(Math.round(y*10)*400+x)*4+3]>200)xs.push(x/10);return {min:Math.min(...xs),max:Math.max(...xs)};};
  const lights=Array.from(node.querySelectorAll('circle')).map(n=>({x:Number(n.getAttribute('cx')),y:Number(n.getAttribute('cy')),fill:getComputedStyle(n).fill}));
  // Isolate the main wing at its root; the aft tailplane also crosses this row.
  return {forward,upperSweep:swept(upperTip,upperRoot),lowerSweep:swept(lowerTip,lowerRoot),tip:extent(2.5),root:extent(7.5,10),body:extent(10),lights};
 });
 expect(geometry.forward.x*(west?-1:1)).toBeGreaterThan(0);expect(geometry.upperSweep).toBeLessThan(0);expect(geometry.lowerSweep).toBeLessThan(0);
 expect(geometry.tip.max).toBeLessThan(geometry.root.min);expect(geometry.body.max).toBeGreaterThan(37);expect(geometry.body.min).toBeLessThan(3);
 expect(geometry.lights).toEqual([{x:13,y:2,fill:'rgb(214, 166, 162)'},{x:13,y:18,fill:'rgb(183, 211, 199)'}]);
 await page.screenshot({path:info.outputPath(`aircraft-${direction}-${theme}.png`)});
 // Enlarged diagnostic uses the exact live SVG; normal screenshot above retains actual 40×20px size.
 await flight.locator('svg').evaluate(svg=>{const clone=svg.cloneNode(true) as SVGSVGElement;clone.style.width='400px';clone.style.height='200px';clone.style.position='fixed';clone.style.left='200px';clone.style.top='140px';clone.style.transformOrigin='center';clone.style.fill=getComputedStyle(svg).fill;clone.style.opacity=getComputedStyle(svg).opacity;const originals=svg.querySelectorAll('circle');clone.querySelectorAll('circle').forEach((c,i)=>{(c as SVGElement).style.animation='none';(c as SVGElement).style.fill=getComputedStyle(originals[i]).fill;});document.body.appendChild(clone);});
 await page.screenshot({path:info.outputPath(`aircraft-silhouette-${direction}-${theme}.png`)});
});
