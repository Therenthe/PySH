import {useEffect,useRef,useState,type CSSProperties} from 'react';
import './ambient-events.css';
import {BlenderAircraft,type AircraftVariant} from './AmbientCelestial3D';

type Aircraft={kind:'aircraft';id:number;variant:AircraftVariant;facing:1|-1;fromX:number;fromY:number;toX:number;toY:number;duration:number;heading:number;scale:number};
type Dust={kind:'lunar-dust';id:number;x:number;y:number;duration:number;radius:number};
type AmbientEvent=Aircraft|Dust;
const random=()=>crypto.getRandomValues(new Uint32Array(1))[0]/4294967296;

export function createAircraft(id:number,rng:()=>number=random,aspectRatio=800/480,previous?:AircraftVariant):Aircraft{
 const variants:AircraftVariant[]=['airliner','turboprop','business-jet','tv-helicopter','police-helicopter'];
 const choices=variants.filter(variant=>variant!==previous),variant=choices[Math.min(choices.length-1,Math.floor(rng()*choices.length))];
 const helicopter=variant.endsWith('helicopter'),facing=rng()<.5?1:-1,fromX=facing===1?-14:114,toX=facing===1?114:-14;
 const fromY=(helicopter?30:12)+rng()*(helicopter?18:25),toY=Math.max(10,Math.min(52,fromY+(rng()-.5)*(helicopter?6:12)));
 const duration=helicopter?48000+rng()*17000:variant==='turboprop'?34000+rng()*14000:variant==='business-jet'?22000+rng()*10000:26000+rng()*14000;
 // Mirror westbound sprites; a 180° turn would put their fins and rotors underneath.
 return {kind:'aircraft',id,variant,facing,fromX,fromY,toX,toY,duration,
  heading:Math.atan2((toY-fromY)*facing,Math.abs(toX-fromX)*aspectRatio)*180/Math.PI,scale:helicopter?.95+rng()*.15:.9+rng()*.25};
}
export function createLunarDust(id:number,rng:()=>number=random):Dust{
 return {kind:'lunar-dust',id,x:37+rng()*20,y:37+rng()*20,duration:1700+rng()*1000,radius:7+rng()*7};
}

/** Decorative encounters, never a representation of tracked flights or lunar impacts.
 * Mount inside the full-scene sky. Lunar dust shares Moon's 90px/23px/85px anchor.
 */
export function AmbientEvents({enabled,night,moonVisible=false,lunarDust=false,aircraft=true,moonPosition}:{enabled:boolean;night:boolean;moonVisible?:boolean;lunarDust?:boolean;aircraft?:boolean;moonPosition?:{x:number;y:number}}){
 const [events,setEvents]=useState<AmbientEvent[]>([]),container=useRef<HTMLDivElement>(null);
 useEffect(()=>{
  const media=window.matchMedia('(prefers-reduced-motion: reduce)'),timers=new Set<ReturnType<typeof setTimeout>>();let disposed=false,id=0,previous:AircraftVariant|undefined;
  const active=()=>enabled&&!disposed&&!document.hidden&&!media.matches;
  const later=(fn:()=>void,delay:number)=>{const timer=setTimeout(()=>{timers.delete(timer);if(!disposed)fn();},delay);timers.add(timer);};
  const clear=()=>{timers.forEach(clearTimeout);timers.clear();setEvents([]);};
  const show=(event:AmbientEvent)=>{if(!active())return;setEvents(old=>old.length<2?[...old,event]:old);later(()=>setEvents(old=>old.filter(item=>item.id!==event.id)),event.duration+100);};
  const flight=()=>{if(!active()||!aircraft)return;const el=container.current,event=createAircraft(++id,random,el?.clientHeight?el.clientWidth/el.clientHeight:800/480,previous);previous=event.variant;show(event);later(flight,event.duration+35000+random()*60000);};
  const dust=()=>{if(!active()||!night||!moonVisible||!lunarDust)return;show(createLunarDust(++id));later(dust,150000+random()*270000);};
  const reset=()=>{clear();if(active()){if(aircraft)later(flight,18000+random()*32000);if(night&&moonVisible&&lunarDust)later(dust,65000+random()*85000);}};
  reset();document.addEventListener('visibilitychange',reset);media.addEventListener('change',reset);
  return()=>{disposed=true;timers.forEach(clearTimeout);timers.clear();document.removeEventListener('visibilitychange',reset);media.removeEventListener('change',reset);};
 },[enabled,night,moonVisible,lunarDust,aircraft]);
 return <div ref={container} className="ambient-events" data-night={night} aria-hidden="true">
  {events.map(event=>event.kind==='aircraft'?<div key={event.id} className="ambient-flight" data-ambient-event="aircraft" data-aircraft-variant={event.variant} data-facing={event.facing} style={{left:`${event.fromX}%`,top:`${event.fromY}%`,'--flight-dx':`${event.toX-event.fromX}cqw`,'--flight-dy':`${event.toY-event.fromY}cqh`,'--flight-duration':`${event.duration}ms`} as CSSProperties}>
   <BlenderAircraft night={night} heading={event.heading} facing={event.facing} scale={event.scale} variant={event.variant}/>
  </div>:<div key={event.id} className="ambient-lunar-event" data-ambient-event="lunar-dust" style={{left:moonPosition?`${moonPosition.x}%`:undefined,top:moonPosition?`${moonPosition.y}%`:undefined,right:moonPosition?'auto':undefined,transform:moonPosition?'translate(-50%,-50%)':undefined,'--dust-duration':`${event.duration}ms`,'--dust-radius':`${event.radius}px`} as CSSProperties}>
   <svg viewBox="0 0 90 90"><g transform={`translate(${event.x} ${event.y})`}>
    <circle className="lunar-contact" r="1.6"/>
    {[0,1,2].map(index=><ellipse key={index} className={`lunar-dust dust-${index}`} cx={index*2-2} cy={-index*2} rx={event.radius*(.65+index*.2)} ry={event.radius*(.45+index*.15)}/>) }
   </g></svg>
  </div>)}
 </div>;
}
