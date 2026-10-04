import {useEffect,useState,type CSSProperties} from 'react';
import './ambient-events.css';

type Aircraft={kind:'aircraft';id:number;fromX:number;fromY:number;toX:number;toY:number;duration:number;heading:number;scale:number};
type Dust={kind:'lunar-dust';id:number;x:number;y:number;duration:number;radius:number};
type AmbientEvent=Aircraft|Dust;
const random=()=>crypto.getRandomValues(new Uint32Array(1))[0]/4294967296;

export function createAircraft(id:number,rng:()=>number=random):Aircraft{
 const east=rng()<.5,fromX=east?-8:108,toX=east?108:-8;
 const fromY=12+rng()*34,toY=Math.max(8,Math.min(54,fromY+(rng()-.5)*18));
 return {kind:'aircraft',id,fromX,fromY,toX,toY,duration:24000+rng()*18000,
  heading:Math.atan2((toY-fromY)*.6,toX-fromX)*180/Math.PI,scale:.8+rng()*.45};
}
export function createLunarDust(id:number,rng:()=>number=random):Dust{
 return {kind:'lunar-dust',id,x:37+rng()*20,y:37+rng()*20,duration:1700+rng()*1000,radius:7+rng()*7};
}

/** Decorative encounters, never a representation of tracked flights or lunar impacts.
 * Mount inside the full-scene sky. Lunar dust shares Moon's 90px/23px/85px anchor.
 */
export function AmbientEvents({enabled,night,moonVisible=false,lunarDust=false,aircraft=true,moonPosition}:{enabled:boolean;night:boolean;moonVisible?:boolean;lunarDust?:boolean;aircraft?:boolean;moonPosition?:{x:number;y:number}}){
 const [events,setEvents]=useState<AmbientEvent[]>([]);
 useEffect(()=>{
  const media=window.matchMedia('(prefers-reduced-motion: reduce)'),timers=new Set<ReturnType<typeof setTimeout>>();let disposed=false,id=0;
  const active=()=>enabled&&!disposed&&!document.hidden&&!media.matches;
  const later=(fn:()=>void,delay:number)=>{const timer=setTimeout(()=>{timers.delete(timer);if(!disposed)fn();},delay);timers.add(timer);};
  const clear=()=>{timers.forEach(clearTimeout);timers.clear();setEvents([]);};
  const show=(event:AmbientEvent)=>{if(!active())return;setEvents(old=>old.length<2?[...old,event]:old);later(()=>setEvents(old=>old.filter(item=>item.id!==event.id)),event.duration+100);};
  const flight=()=>{if(!active()||!aircraft)return;show(createAircraft(++id));later(flight,55000+random()*105000);};
  const dust=()=>{if(!active()||!night||!moonVisible||!lunarDust)return;show(createLunarDust(++id));later(dust,150000+random()*270000);};
  const reset=()=>{clear();if(active()){if(aircraft)later(flight,18000+random()*32000);if(night&&moonVisible&&lunarDust)later(dust,65000+random()*85000);}};
  reset();document.addEventListener('visibilitychange',reset);media.addEventListener('change',reset);
  return()=>{disposed=true;timers.forEach(clearTimeout);timers.clear();document.removeEventListener('visibilitychange',reset);media.removeEventListener('change',reset);};
 },[enabled,night,moonVisible,lunarDust,aircraft]);
 return <div className="ambient-events" data-night={night} aria-hidden="true">
  {events.map(event=>event.kind==='aircraft'?<div key={event.id} className="ambient-flight" data-ambient-event="aircraft" style={{left:`${event.fromX}%`,top:`${event.fromY}%`,'--flight-dx':`${event.toX-event.fromX}cqw`,'--flight-dy':`${event.toY-event.fromY}cqh`,'--flight-duration':`${event.duration}ms`} as CSSProperties}>
   <svg viewBox="0 0 40 20" style={{transform:`rotate(${event.heading}deg) scale(${event.scale})`}}>
    {/* Nose points +X; both main wings and tailplanes sweep back toward -X. */}
    <path d="M38 10C38 9 35 8.3 32 8.3H24L15 2H11L18 8.3H7L4 5H2L4 9H2V11H4L2 15H4L7 11.7H18L11 18H15L24 11.7H32C35 11.7 38 11 38 10Z"/>
    <circle className="aircraft-navigation" cx="13" cy="2" r=".7"/><circle className="aircraft-navigation aircraft-navigation-secondary" cx="13" cy="18" r=".7"/>
   </svg>
  </div>:<div key={event.id} className="ambient-lunar-event" data-ambient-event="lunar-dust" style={{left:moonPosition?`${moonPosition.x}%`:undefined,top:moonPosition?`${moonPosition.y}%`:undefined,right:moonPosition?'auto':undefined,transform:moonPosition?'translate(-50%,-50%)':undefined,'--dust-duration':`${event.duration}ms`,'--dust-radius':`${event.radius}px`} as CSSProperties}>
   <svg viewBox="0 0 90 90"><g transform={`translate(${event.x} ${event.y})`}>
    <circle className="lunar-contact" r="1.6"/>
    {[0,1,2].map(index=><ellipse key={index} className={`lunar-dust dust-${index}`} cx={index*2-2} cy={-index*2} rx={event.radius*(.65+index*.2)} ry={event.radius*(.45+index*.15)}/>) }
   </g></svg>
  </div>)}
 </div>;
}
