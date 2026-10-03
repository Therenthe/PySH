import {useEffect,useState,type CSSProperties} from 'react';
type Meteor={id:number;left:number;top:number;length:number;angle:number;dx:number;dy:number;duration:number;brightness:number;thickness:number};
const random=()=>crypto.getRandomValues(new Uint32Array(1))[0]/4294967296;

/** The local positive x axis points from the tail toward the moving head. */
export function createMeteor(id:number,rng:()=>number=random):Meteor{
 const right=rng()<.32,angle=right?24+rng()*40:116+rng()*40;
 const distance=170+rng()*250,speed=175+rng()*205,radians=angle*Math.PI/180;
 return {id,left:right?8+rng()*45:42+rng()*53,top:3+rng()*36,
  length:38+rng()*92,angle,dx:Math.cos(radians)*distance,dy:Math.sin(radians)*distance,
  duration:distance/speed*1000,brightness:.38+rng()*.55,thickness:1+rng()*.9};
}

// Fresh, bounded decorative bursts, not a forecast of astronomical events.
export function Meteors({enabled}:{enabled:boolean}){
 const [meteors,setMeteors]=useState<Meteor[]>([]);
 useEffect(()=>{
  const media=window.matchMedia('(prefers-reduced-motion: reduce)'),timers=new Set<ReturnType<typeof setTimeout>>();let serial=0,disposed=false;
  const active=()=>!disposed&&enabled&&!media.matches&&!document.hidden;
  const later=(fn:()=>void,delay:number)=>{const timer=setTimeout(()=>{timers.delete(timer);if(!disposed)fn();},delay);timers.add(timer);};
  const clear=()=>{timers.forEach(clearTimeout);timers.clear();setMeteors([]);};
  const launch=()=>{if(!active())return;const meteor=createMeteor(++serial);setMeteors(old=>[...old.slice(-3),meteor]);later(()=>setMeteors(old=>old.filter(m=>m.id!==meteor.id)),meteor.duration+50);};
  const burst=()=>{if(!active())return;launch();const additional=random()<.28?1+(random()<.25?1:0):0;
   for(let i=0;i<additional;i++)later(launch,240+random()*1500+i*300);
   later(burst,8000+random()*28000);
  };
  const reset=()=>{clear();if(active())later(burst,4500+random()*14000);};
  reset();media.addEventListener('change',reset);document.addEventListener('visibilitychange',reset);
  return()=>{disposed=true;timers.forEach(clearTimeout);timers.clear();media.removeEventListener('change',reset);document.removeEventListener('visibilitychange',reset);};
 },[enabled]);
 return <>{meteors.map(m=><i aria-hidden="true" className="ambient-meteor meteor-transient" key={m.id} data-meteor-id={m.id}
  style={{left:`${m.left}%`,top:`${m.top}%`,'--meteor-angle':`${m.angle}deg`,'--meteor-dx':`${m.dx}px`,'--meteor-dy':`${m.dy}px`,'--meteor-duration':`${m.duration}ms`,'--meteor-length':`${m.length}px`,'--meteor-brightness':m.brightness,'--meteor-thickness':`${m.thickness}px`} as CSSProperties}>
  <span className="meteor-tail"/><span className="meteor-head"/>
 </i>)}</>;
}
