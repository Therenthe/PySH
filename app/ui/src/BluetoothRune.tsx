import {useEffect,useRef,useState} from 'react';

/** The atlas contains32 actual Blender Z-axis poses; CSS only advances frames. */
export function BluetoothRune({palette,connected,active}:{palette:'day'|'night';connected:boolean;active:boolean}){
 const [turning,setTurning]=useState(false),first=useRef(true);
 const [quiet,setQuiet]=useState(()=>window.matchMedia('(prefers-reduced-motion: reduce)').matches);
 useEffect(()=>{
  const query=window.matchMedia('(prefers-reduced-motion: reduce)'),change=()=>setQuiet(query.matches);
  query.addEventListener('change',change);return()=>query.removeEventListener('change',change);
 },[]);
 useEffect(()=>{
  if(!active||quiet){setTurning(false);return;}
  if(turning){first.current=false;const fallback=window.setTimeout(()=>setTurning(false),3400);return()=>clearTimeout(fallback);}
  const wait=first.current?18000+Math.random()*10000:45000+Math.random()*30000;
  const timer=window.setTimeout(()=>setTurning(true),wait);return()=>clearTimeout(timer);
 },[active,quiet,turning]);
 return <span className="city-bluetooth-rune" data-turning={turning} style={{backgroundImage:`url('/ambient/city-bluetooth-turn-${palette}-${connected?'connected':'idle'}-v1.png')`}} onAnimationEnd={event=>{if(event.animationName==='city-bluetooth-turn')setTurning(false);}}/>;
}
