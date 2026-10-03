import {useEffect,useState} from 'react';
type Meteor={id:number;left:number;top:number;width:number};
const random=()=>crypto.getRandomValues(new Uint32Array(1))[0]/4294967296;
// Decorative bursts with fresh timings/positions; never a forecast of a meteor event.
export function Meteors({enabled}:{enabled:boolean}){
 const [meteors,setMeteors]=useState<Meteor[]>([]);
 useEffect(()=>{const media=window.matchMedia('(prefers-reduced-motion: reduce)');let next=0;const timers=new Set<ReturnType<typeof setTimeout>>();let serial=0;
  const later=(fn:()=>void,delay:number)=>{const timer=setTimeout(()=>{timers.delete(timer);fn();},delay);timers.add(timer);return timer;};
  const stop=()=>{timers.forEach(clearTimeout);timers.clear();setMeteors([]);};
  const burst=()=>{if(!enabled||media.matches||document.hidden)return;const count=1+Math.floor(random()*3);for(let i=0;i<count;i++)later(()=>{const meteor={id:++serial,left:40+random()*57,top:8+random()*40,width:55+random()*65};setMeteors(old=>[...old.slice(-3),meteor]);later(()=>setMeteors(old=>old.filter(m=>m.id!==meteor.id)),1900);},i*(300+random()*900));next=later(burst,7000+random()*22000);};
  const reset=()=>{stop();if(enabled&&!media.matches&&!document.hidden)next=later(burst,4000+random()*13000);};
  reset();media.addEventListener('change',reset);document.addEventListener('visibilitychange',reset);
  return()=>{clearTimeout(next);stop();media.removeEventListener('change',reset);document.removeEventListener('visibilitychange',reset);};
 },[enabled]);
 return <>{meteors.map(m=><i className="ambient-meteor meteor-transient" key={m.id} style={{left:`${m.left}%`,top:`${m.top}%`,width:m.width}}/>)}</>;
}
