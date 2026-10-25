import {test,expect,type Page} from '@playwright/test';
import path from 'node:path';
import {readFileSync} from 'node:fs';

const variants=['airliner','turboprop','business-jet','tv-helicopter','police-helicopter'];
const anchors=JSON.parse(readFileSync('app/ui/public/ambient/aircraft/anchors-v1.json','utf8')).models;

async function fixture(page:Page){
 const entry='/@fs/'+path.resolve('tests/e2e/aircraft.fixture.tsx').replaceAll('\\','/');
 await page.route('**/aircraft-audit',route=>route.fulfill({contentType:'text/html',body:`<html><head><style>html,body,#root{margin:0;width:800px;height:480px;overflow:hidden}</style></head><body><div id="root"></div><script type="module">import RefreshRuntime from '/@react-refresh';RefreshRuntime.injectIntoGlobalHook(window);window.$RefreshReg$=()=>{};window.$RefreshSig$=()=>type=>type;window.__vite_plugin_react_preamble_installed__=true;</script><script type="module" src="${entry}"></script></body></html>`}));
 await page.goto('/aircraft-audit');await page.waitForFunction(()=>(window as any).aircraftFixtureReady);
}

test('fleet selection is genuinely varied, slower lower helicopters and no immediate repeats',async({page})=>{
 await fixture(page);
 const fleet=await page.evaluate(()=>{
  const create=(window as any).createAircraft,make=(index:number,west=false,previous?:string)=>{
   const values=[(index+.5)/5,west?.9:.1,.5,.6,.5,.5];let i=0;
   return create(index,()=>values[i++],800/422,previous);
  };
  return {east:[0,1,2,3,4].map(index=>make(index)),west:[0,1,2,3,4].map(index=>make(index,true)),again:make(0,false,'airliner')};
 });
 expect(fleet.east.map(f=>f.variant)).toEqual(variants);expect(fleet.again.variant).not.toBe('airliner');
 for(const [index,east]of fleet.east.entries()){
  const west=fleet.west[index];expect(east.facing).toBe(1);expect(west.facing).toBe(-1);
  expect(Math.abs(east.heading)).toBeLessThan(5);expect(west.heading).toBeCloseTo(-east.heading);
  const helicopter=east.variant.endsWith('helicopter');
  expect(east.fromY).toBe(helicopter?39:24.5);expect(east.duration).toBe(helicopter?56500:east.variant==='turboprop'?41000:east.variant==='business-jet'?27000:33000);
 }
});

for(const night of [false,true])test(`all five Blender aircraft have distinct unclipped ${night?'night':'day'} renders`,async({page})=>{
 await fixture(page);
 const masks=await page.evaluate(async({variants,night})=>{
  const results=[];
  for(const variant of variants){
   const helicopter=variant.endsWith('helicopter'),frames=[];
   for(let frame=0;frame<(helicopter?3:1);frame++){
    const image=new Image();image.src=`/ambient/aircraft/${variant}-${night?'night':'day'}${helicopter?`-${frame}`:''}-v1.png`;await image.decode();
    const canvas=document.createElement('canvas');canvas.width=image.width;canvas.height=image.height;const ctx=canvas.getContext('2d')!;ctx.drawImage(image,0,0);const pixels=ctx.getImageData(0,0,image.width,image.height).data;
    let edge=0,occupied=0,signature=2166136261,minX=image.width,minY=image.height,maxX=0,maxY=0;
    for(let y=0;y<image.height;y++)for(let x=0;x<image.width;x++){
     const offset=(y*image.width+x)*4,alpha=pixels[offset+3];if(x===0||y===0||x===image.width-1||y===image.height-1)edge=Math.max(edge,alpha);
     if(alpha>180){occupied++;minX=Math.min(minX,x);minY=Math.min(minY,y);maxX=Math.max(maxX,x);maxY=Math.max(maxY,y);}
     for(let c=0;c<4;c++)signature=Math.imul(signature^pixels[offset+c],16777619)>>>0;
    }
    frames.push({size:[image.width,image.height],edge,occupied,signature,bounds:{minX,minY,maxX,maxY}});
   }results.push({variant,frames});
  }return results;
 },{variants,night});
 expect(new Set(masks.map(item=>item.frames[0].signature)).size).toBe(5);
 for(const item of masks){
  expect(new Set(item.frames.map(frame=>frame.signature)).size).toBe(item.frames.length);
  for(const frame of item.frames){expect(frame.size).toEqual([160,80]);expect(frame.edge,`${item.variant} must be fully in frame`).toBeLessThan(20);expect(frame.occupied).toBeGreaterThan(350);expect(frame.occupied).toBeLessThan(8000);expect(frame.bounds.minX).toBeGreaterThan(1);expect(frame.bounds.minY).toBeGreaterThan(1);expect(frame.bounds.maxX).toBeLessThan(158);expect(frame.bounds.maxY).toBeLessThan(78);}
 }
});

for(const variant of variants)for(const night of [false,true])for(const facing of [1,-1] as const)test(`upright ${variant} ${night?'night':'day'} ${facing===1?'east':'west'}`,async({page},info)=>{
 await fixture(page);await page.evaluate(({night,variant,facing})=>(window as any).showAircraft(night,variant,facing),{night,variant,facing});
 const aircraft=page.locator('.blender-aircraft');await expect(aircraft).toBeVisible();
 await aircraft.locator('img').evaluateAll(images=>Promise.all(images.map(image=>(image as HTMLImageElement).decode())));
 const transform=await aircraft.evaluate((el,points)=>{
  const m=new DOMMatrix(getComputedStyle(el).transform),top=points.finTop||points.rotorTop,bottom=points.finBase||points.skidBottom;
  const project=(p:number[])=>new DOMPoint(p[0]*el.clientWidth,p[1]*el.clientHeight).matrixTransform(m);
  const image=el.querySelector('img')!,canvas=document.createElement('canvas');canvas.width=image.naturalWidth;canvas.height=image.naturalHeight;
  const ctx=canvas.getContext('2d')!;ctx.drawImage(image,0,0);const pixels=ctx.getImageData(0,0,canvas.width,canvas.height).data;
  const hit=(point:number[])=>{let peak=0;for(let y=Math.max(0,Math.round(point[1]*canvas.height)-3);y<=Math.min(canvas.height-1,Math.round(point[1]*canvas.height)+3);y++)for(let x=Math.max(0,Math.round(point[0]*canvas.width)-3);x<=Math.min(canvas.width-1,Math.round(point[0]*canvas.width)+3);x++)peak=Math.max(peak,pixels[(y*canvas.width+x)*4+3]);return peak;};
  const lights=Array.from(el.querySelectorAll<HTMLElement>('.blender-aircraft-light')).map(light=>{const key=light.classList.contains('port')?'port':light.classList.contains('starboard')?'starboard':'beacon';return {key,x:parseFloat(light.style.left)/100,y:parseFloat(light.style.top)/100,hit:hit(points[key])};});
  return {xx:m.a,yy:m.d,det:m.a*m.d-m.b*m.c,pointer:getComputedStyle(el).pointerEvents,top:project(top).y,bottom:project(bottom).y,topHit:hit(top),bottomHit:hit(bottom),lights};
 },anchors[variant]);
 expect(transform.xx*facing).toBeGreaterThan(0);expect(transform.yy,'the aircraft top must never flip below its belly').toBeGreaterThan(0);expect(Math.sign(transform.det)).toBe(facing);expect(transform.pointer).toBe('none');
 expect(transform.top,'actual Blender fin/rotor must stay above body/skids in both directions').toBeLessThan(transform.bottom);expect(transform.topHit).toBeGreaterThan(180);expect(transform.bottomHit).toBeGreaterThan(180);
 expect(transform.lights).toHaveLength(night?(variant.endsWith('helicopter')?1:2):0);
 for(const light of transform.lights){expect(light.x).toBeCloseTo(anchors[variant][light.key][0],5);expect(light.y).toBeCloseTo(anchors[variant][light.key][1],5);expect(light.hit,'navigation light must sit on its rendered airframe').toBeGreaterThan(180);}
 const helicopter=variant.endsWith('helicopter');await expect(aircraft.locator('img')).toHaveCount(helicopter?3:1);
 if(helicopter){
  const visible=await aircraft.locator('img').evaluateAll(images=>images.map(image=>getComputedStyle(image).opacity));expect(visible.filter(value=>value==='1')).toHaveLength(1);
  await expect(aircraft.locator('.aircraft-hover')).toHaveCSS('animation-name','blender-helicopter-hover');
 }
 await page.screenshot({path:info.outputPath(`fleet-${variant}-${night?'night':'day'}-${facing===1?'east':'west'}.png`)});
 await page.emulateMedia({reducedMotion:'reduce'});
 expect(await aircraft.locator('.aircraft-hover,.aircraft-rotor-frame').evaluateAll(nodes=>nodes.every(node=>getComputedStyle(node).animationName==='none'))).toBeTruthy();
 if(helicopter)await expect(aircraft.locator('.rotor-frame-1')).toBeHidden();
});
