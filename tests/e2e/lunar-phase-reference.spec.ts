import {test,expect} from '@playwright/test';
import {readFileSync,writeFileSync} from 'node:fs';

const reference=JSON.parse(readFileSync('tests/lunar-phase-usno-2026.json','utf8'));

test('actual lunar phase model follows all 2026 USNO primary phases and current waxing gibbous',async({page},info)=>{
 await page.route('**/api/**',route=>route.fulfill({json:{token:'reference-fixture',preferences:{setupComplete:true,screensaverMinutes:0},network:{},bluetooth:{},audio:{},player:{},weather:{}}}));await page.goto('/');
 const measured=await page.evaluate(async reference=>{
  const {lunarPhase}=await import('/src/Moon.tsx' as string),{moonAtlasFrame}=await import('/src/AmbientCelestial3D.tsx' as string);
  const delta=reference.tolerance.transitionBracketHours*3600000;
  const phases=reference.phases.map((fixture:{utc:string;phase:string})=>{
   const at=new Date(fixture.utc),value=lunarPhase(at),before=lunarPhase(new Date(at.getTime()-delta)),after=lunarPhase(new Date(at.getTime()+delta));
   const nominal=fixture.phase==='new'?0:fixture.phase==='full'?1:.5;
   return {...fixture,...value,before,after,absoluteError:Math.abs(value.illumination-nominal)};
  });
  const current=lunarPhase(new Date(reference.currentAuditInstant)),frame=moonAtlasFrame(current.illumination,current.waxing);
  return {phases,current:{utc:reference.currentAuditInstant,...current,atlasFrame:frame,atlasIllumination:(1-Math.cos(frame/128*Math.PI*2))/2},worst:phases.reduce((a:any,b:any)=>a.absoluteError>b.absoluteError?a:b)};
 },reference);
 const measurementPath=info.outputPath('usno-measurements.json');writeFileSync(measurementPath,JSON.stringify({source:reference.source,...measured},null,2));await info.attach('independent-usno-lunar-reference',{path:measurementPath,contentType:'application/json'});
 console.log(JSON.stringify({lunarReferenceWorst:measured.worst,current:measured.current}));
 expect(measured.phases).toHaveLength(50);
 for(const value of measured.phases){
  expect(value.absoluteError,`${value.phase} ${value.utc}: computed illumination ${value.illumination}`).toBeLessThan(reference.tolerance.absoluteIllumination);
  if(value.phase==='first-quarter'||value.phase==='last-quarter'){
   const waxing=value.phase==='first-quarter';expect(value.waxing,value.utc).toBe(waxing);expect(value.before.waxing,value.utc).toBe(waxing);expect(value.after.waxing,value.utc).toBe(waxing);
   expect((value.after.illumination-value.before.illumination)*(waxing?1:-1),value.utc).toBeGreaterThan(0);
  }else{expect(value.before.waxing,value.utc).toBe(value.phase==='full');expect(value.after.waxing,value.utc).toBe(value.phase==='new');}
 }
 expect(measured.current.waxing).toBe(true);expect(measured.current.illumination).toBeGreaterThan(.5);expect(measured.current.illumination).toBeLessThan(.99);expect(Math.abs(measured.current.atlasIllumination-measured.current.illumination)).toBeLessThan(.01228);
});
