import {getCelestialScene} from './CelestialMotion';
import type {SceneWeather} from './sceneWeather';

const clamp=(value:number)=>Math.max(0,Math.min(1,value));
const smooth=(value:number)=>{const x=clamp(value);return x*x*(3-2*x);};

/** Window lighting follows the real local sun, independently of the UI theme. */
export function cityWindowLighting(now:Date,timezone:string,daily:any[],stale:boolean,latitude:unknown,longitude:unknown):{level:number;source:'solar'|'astronomy'|'unknown'} {
 if(!Number.isFinite(now.getTime()))return {level:0,source:'unknown'};
 try{
  const local=new Intl.DateTimeFormat('en-CA',{timeZone:timezone,year:'numeric',month:'2-digit',day:'2-digit'});
  const date=local.format(now),day=Array.isArray(daily)?daily.find(day=>day?.date===date):undefined;
  const rise=day?.sunrise_epoch,set=day?.sunset_epoch,epoch=now.getTime()/1000;
  if(!stale&&typeof rise==='number'&&typeof set==='number'&&Number.isFinite(rise)&&Number.isFinite(set)&&rise<set&&local.format(new Date(rise*1000))===date&&local.format(new Date(set*1000))===date){
   const dawn=1-smooth((epoch-rise+900)/1800),dusk=smooth((epoch-set+900)/1800);
   return {level:Math.max(dawn,dusk),source:'solar'};
  }
 }catch{/* Invalid provider time zones/epochs cannot become a fabricated sunset. */}
 const celestial=getCelestialScene(now,latitude,longitude);
 return celestial?{level:smooth((6-celestial.sun.altitude)/12),source:'astronomy'}:{level:0,source:'unknown'};
}

export const cityWindowBankLevel=(level:number,bank:number)=>smooth((level-bank*.14)/(1-bank*.14));
export const cityWetRoadLevel=(weather:SceneWeather)=>weather.precipitation==='rain'?({light:.30,moderate:.52,heavy:.72,none:0}[weather.intensity]):0;
