import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';

// Camera projections exported by Blender, checked against the delivered pixels.
const report=JSON.parse(readFileSync('assets/blender/sky3d/build-report.json','utf8'));

test('all aircraft renders preserve both complete swept wings inside a transparent frame',async({page})=>{
 await page.route('**/api/**',route=>route.fulfill({json:{token:'fixture',preferences:{setupComplete:true,screensaverMinutes:0},network:{},bluetooth:{},audio:{},player:{},weather:{}}}));await page.goto('/');
 const masks=await page.evaluate(async report=>{
  const results=[];for(const kind of ['airliner','glider'])for(const lighting of ['day','night']){
   const image=new Image();image.src=`/ambient/sky3d/${kind}-${lighting}-blender-v1.png`;await image.decode();const canvas=document.createElement('canvas');canvas.width=image.width;canvas.height=image.height;const ctx=canvas.getContext('2d')!;ctx.drawImage(image,0,0);const pixels=ctx.getImageData(0,0,image.width,image.height).data,points=report[kind].rasterAnchors;
   const alpha=(x:number,y:number)=>pixels[(y*image.width+x)*4+3];let edgePeak=0,count=0,minX=image.width,maxX=0,minY=image.height,maxY=0;for(let y=0;y<image.height;y++)for(let x=0;x<image.width;x++){const value=alpha(x,y);if(x===0||y===0||x===image.width-1||y===image.height-1)edgePeak=Math.max(edgePeak,value);if(value>200){count++;minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y);}}
   const hits=Object.entries(points).map(([name,p])=>{const [px,py]=p as number[];let peak=0;for(let y=Math.max(0,Math.round(py)-3);y<=Math.min(image.height-1,Math.round(py)+3);y++)for(let x=Math.max(0,Math.round(px)-3);x<=Math.min(image.width-1,Math.round(px)+3);x++)peak=Math.max(peak,alpha(x,y));return {name,point:[px,py],peak};});
   results.push({kind,lighting,size:[image.width,image.height],edgePeak,coverage:count/(image.width*image.height),bounds:{minX,maxX,minY,maxY},hits});
  }return results;
 },report);
 for(const mask of masks){expect(mask.size).toEqual([256,128]);expect(mask.edgePeak,`${mask.kind}/${mask.lighting} must not clip a wing at the image edge`).toBeLessThan(20);expect(mask.coverage).toBeGreaterThan(.04);expect(mask.coverage).toBeLessThan(.4);for(const hit of mask.hits){expect(hit.point[0]).toBeGreaterThan(2);expect(hit.point[0]).toBeLessThan(254);expect(hit.point[1]).toBeGreaterThan(2);expect(hit.point[1]).toBeLessThan(126);expect(hit.peak,`${mask.kind}/${mask.lighting} ${hit.name} must hit rendered geometry`).toBeGreaterThan(200);}expect(mask.bounds.minX).toBeGreaterThan(2);expect(mask.bounds.maxX).toBeLessThan(254);expect(mask.bounds.minY).toBeGreaterThan(2);expect(mask.bounds.maxY).toBeLessThan(126);}
});

for(const theme of ['ink','night'])for(const direction of ['east','west'])test(`aircraft swept wings ${direction} ${theme}`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro'),west=direction==='west';
 await page.addInitScript(west=>{crypto.getRandomValues=((array:Uint32Array)=>{array.fill(west?4294967295:0);return array;}) as typeof crypto.getRandomValues;},west);
 await page.route('**/api/**',route=>{const path=new URL(route.request().url()).pathname;return route.fulfill({json:path==='/api/session'?{token:'fixture'}:path==='/api/state'?{preferences:{language:ro?'ro':'en',theme,nightEnabled:false,setupComplete:true,screensaverMinutes:0,decorativeAircraft:true},network:{},bluetooth:{devices:[],prompts:[]},audio:{},player:{},weather:{current:{weather_code:0,is_day:theme==='ink'?1:0},daily:[]}}:{ok:true}});});
 await page.clock.install({time:new Date('2026-10-04T12:00:00Z')});await page.goto('/');
 await page.clock.runFor(west?50020:18020);const flight=page.locator('.ambient-flight');await expect(flight).toHaveCount(1);
 await flight.evaluate(el=>{el.getAnimations().forEach(animation=>{animation.currentTime=Number(getComputedStyle(el).getPropertyValue('--flight-duration').replace('ms',''))/2;animation.pause();});el.getAnimations({subtree:true}).filter(a=>a.effect?.target!==el).forEach(a=>a.pause());});
 const image=flight.locator('.blender-aircraft>img');await expect(image).toHaveAttribute('src',`/ambient/sky3d/airliner-${theme==='night'?'night':'day'}-blender-v1.png`);
 const anchors=report.airliner.rasterAnchors;
 expect(anchors,'Blender must export its actual camera-projected geometry').toBeTruthy();
 const geometry=await flight.locator('.blender-aircraft').evaluate(async(el,anchors)=>{
  const img=el.querySelector('img')!;await img.decode();
  const canvas=document.createElement('canvas');canvas.width=img.naturalWidth;canvas.height=img.naturalHeight;const ctx=canvas.getContext('2d')!;ctx.drawImage(img,0,0);const data=ctx.getImageData(0,0,canvas.width,canvas.height).data;
  const alpha=(x:number,y:number)=>data[(y*canvas.width+x)*4+3];
  const occupied=[];for(let y=0;y<canvas.height;y++)for(let x=0;x<canvas.width;x++)if(alpha(x,y)>200)occupied.push([x,y]);
  const hit=(point:number[])=>{let peak=0;for(let y=Math.max(0,Math.round(point[1])-3);y<=Math.min(canvas.height-1,Math.round(point[1])+3);y++)for(let x=Math.max(0,Math.round(point[0])-3);x<=Math.min(canvas.width-1,Math.round(point[0])+3);x++)peak=Math.max(peak,alpha(x,y));return peak;};
  const matrix=new DOMMatrix(getComputedStyle(el).transform),sx=el.clientWidth/canvas.width,sy=el.clientHeight/canvas.height;
  const transform=(point:number[])=>new DOMPoint(point[0]*sx,point[1]*sy).matrixTransform(matrix);
  const nose=transform(anchors.nose),tail=transform(anchors.tail),forward={x:nose.x-tail.x,y:nose.y-tail.y};
  const sweep=(tip:number[],root:number[])=>{const a=transform(tip),b=transform(root);return (a.x-b.x)*forward.x+(a.y-b.y)*forward.y;};
  const parent=el.closest('.ambient-flight')!,sky=parent.parentElement!,style=getComputedStyle(parent);
  const travel={x:parseFloat(style.getPropertyValue('--flight-dx'))*sky.clientWidth/100,y:parseFloat(style.getPropertyValue('--flight-dy'))*sky.clientHeight/100};
  const lights=Array.from(el.querySelectorAll<HTMLElement>('.blender-aircraft-light')).map(n=>({className:n.className,x:(n.offsetLeft+n.offsetWidth/2)/sx,y:(n.offsetTop+n.offsetHeight/2)/sy,color:getComputedStyle(n).backgroundColor}));
  return {size:[canvas.width,canvas.height],hits:Object.fromEntries(Object.entries(anchors).map(([key,p])=>[key,hit(p as number[])])),coverage:occupied.length/(canvas.width*canvas.height),bounds:{left:Math.min(...occupied.map(p=>p[0])),right:Math.max(...occupied.map(p=>p[0])),top:Math.min(...occupied.map(p=>p[1])),bottom:Math.max(...occupied.map(p=>p[1]))},corners:[alpha(0,0),alpha(canvas.width-1,0),alpha(0,canvas.height-1),alpha(canvas.width-1,canvas.height-1)],forward,upperSweep:sweep(anchors.upperWingTip,anchors.upperWingRoot),lowerSweep:sweep(anchors.lowerWingTip,anchors.lowerWingRoot),headingCosine:(forward.x*travel.x+forward.y*travel.y)/(Math.hypot(forward.x,forward.y)*Math.hypot(travel.x,travel.y)),lights};
 },anchors);
 expect(geometry.size).toEqual([256,128]);expect(geometry.corners).toEqual([0,0,0,0]);expect(geometry.coverage).toBeGreaterThan(.06);expect(geometry.coverage).toBeLessThan(.4);
 for(const [name,alpha]of Object.entries(geometry.hits))expect(alpha,`${name} must land on the actual rendered aircraft`).toBeGreaterThan(200);
 expect(Math.abs(geometry.bounds.right-anchors.nose[0])).toBeLessThan(9);expect(Math.abs(geometry.bounds.top-anchors.upperWingTip[1])).toBeLessThan(6);expect(Math.abs(geometry.bounds.bottom-anchors.lowerWingTip[1])).toBeLessThan(6);
 expect(geometry.forward.x*(west?-1:1)).toBeGreaterThan(0);expect(geometry.headingCosine).toBeGreaterThan(.9);expect(geometry.upperSweep).toBeLessThan(0);expect(geometry.lowerSweep).toBeLessThan(0);
 if(theme==='night'){
  expect(geometry.lights).toHaveLength(2);
  for(const light of geometry.lights){const port=light.className.includes('port'),tip=port?anchors.lowerWingTip:anchors.upperWingTip;expect(Math.hypot(light.x-tip[0],light.y-tip[1]),`${port?'red port':'green starboard'} light must sit on its real wing tip`).toBeLessThan(6);expect(light.color).toBe(port?'rgb(220, 124, 113)':'rgb(154, 200, 172)');}
 }else expect(geometry.lights).toHaveLength(0);
 await page.screenshot({path:info.outputPath(`aircraft-${direction}-${theme}.png`)});
 // Enlarged diagnostic uses the same live raster and lights, not a replacement SVG.
 await flight.locator('.blender-aircraft').evaluate(el=>{const clone=el.cloneNode(true) as HTMLElement;Object.assign(clone.style,{width:'512px',height:'256px',position:'fixed',left:'144px',top:'112px',transform:'none',zIndex:'999'});clone.querySelectorAll<HTMLElement>('.blender-aircraft-light').forEach(n=>{n.style.animation='none';n.style.opacity='.85';});document.body.appendChild(clone);});
 await page.screenshot({path:info.outputPath(`aircraft-silhouette-${direction}-${theme}.png`)});
});
