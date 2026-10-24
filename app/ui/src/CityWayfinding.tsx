import {useEffect,useLayoutEffect,useRef,useState,type CSSProperties} from 'react';
import {createPortal} from 'react-dom';
import {cityDestinations,type CityDestination} from './CityDestinations';
import {cityWayfinding} from './CityWayfindingData';
import './city-wayfinding.css';

/** Blender poses and projected world-space buoyancy; no live 3D context. */
export function CityWayfinding({open,language,night,onEnter}:{open:boolean;language:'en'|'ro';night:boolean;onEnter:(id:CityDestination)=>void}){
 const [present,setPresent]=useState(open),[ready,setReady]=useState(false),[failed,setFailed]=useState(false);
 const [visible,setVisible]=useState(!document.hidden);
 const panel=useRef<HTMLDivElement|null>(null),reloadFocus=useRef<{id:CityDestination;origin:Element}|null>(null);
 const startArtDeadline=useRef<(()=>()=>void)|null>(null);
 const [reduced,setReduced]=useState(()=>matchMedia('(prefers-reduced-motion:reduce)').matches);
 const nodes=useRef<(HTMLSpanElement|null)[]>([]),carriers=useRef<(HTMLDivElement|null)[]>([]),floating=useRef<Animation[]>([]),animations=useRef<Animation[]>([]),latestOpen=useRef(open);latestOpen.current=open;
 useEffect(()=>{const change=()=>setVisible(!document.hidden);document.addEventListener('visibilitychange',change);return()=>document.removeEventListener('visibilitychange',change);},[]);
 useEffect(()=>{const query=matchMedia('(prefers-reduced-motion:reduce)'),change=()=>setReduced(query.matches);query.addEventListener('change',change);return()=>query.removeEventListener('change',change);},[]);
 useEffect(()=>{
  const focused=document.activeElement,id=focused?.closest<HTMLElement>('[data-destination]')?.dataset.destination;
  if(focused&&panel.current?.contains(focused)&&cityDestinations.some(d=>d.id===id))reloadFocus.current={id:id as CityDestination,origin:focused};
  let disposed=false,settled=false,timeout:number|undefined;setReady(false);setFailed(false);animations.current.forEach(a=>a.cancel());animations.current=[];floating.current.forEach(a=>a.cancel());floating.current=[];
  const start=()=>{clearTimeout(timeout);if(!disposed&&!settled)timeout=window.setTimeout(()=>{if(!disposed&&!settled){settled=true;setFailed(true);}},2500);return()=>clearTimeout(timeout);};
  startArtDeadline.current=start;
  Promise.all(cityDestinations.map(d=>{const image=new Image();image.src='/ambient/'+cityWayfinding.signs[d.id].languages[language][night?'night':'day'];return image.decode();})).then(()=>{if(!disposed&&!settled){settled=true;clearTimeout(timeout);setReady(true);}},()=>{if(!disposed&&!settled){settled=true;clearTimeout(timeout);setFailed(true);}});
  return()=>{disposed=true;clearTimeout(timeout);if(startArtDeadline.current===start)startArtDeadline.current=null;};
 },[language,night]);
 // Preloading a closed feature must not exhaust its user's waiting budget.
 useEffect(()=>{if(open)return startArtDeadline.current?.();},[open,language,night]);
 useLayoutEffect(()=>{
  if(!open){reloadFocus.current=null;return;}
  if((!ready&&!failed)||!present||!reloadFocus.current)return;
  const previous=reloadFocus.current;reloadFocus.current=null;
  // Reloading disables/removes the focused artwork control; never steal a newer user focus.
  if(document.activeElement===document.body||document.activeElement===previous.origin){
   const destination=panel.current?.querySelector<HTMLElement>(`[data-destination="${previous.id}"]`);
   (destination?.matches('button')?destination:destination?.querySelector<HTMLButtonElement>('button'))?.focus({preventScroll:true});
  }
 },[open,present,ready,failed]);
 useLayoutEffect(()=>{
  if(open&&!present){setPresent(true);return;}
  if(!open&&(failed||!ready)){animations.current.forEach(a=>a.cancel());animations.current=[];setPresent(false);return;}
  if(!present||!ready)return;
  if(reduced){animations.current.forEach(a=>a.cancel());animations.current=[];if(!open)setPresent(false);return;}
  if(!animations.current.length){animations.current=nodes.current.map((node,index)=>{
   const animation=node!.animate([{backgroundPosition:'0% 0%'},{backgroundPosition:'100% 0%'}],{duration:cityWayfinding.duration_ms,easing:`steps(${cityWayfinding.signs[cityDestinations[index].id].frame_count-1},end)`,delay:index*35,fill:'both'});animation.pause();animation.currentTime=0;return animation;
  });}
  const current=animations.current;for(const animation of current){
   animation.playbackRate=open?1:-1;
   const end=Number(animation.effect?.getComputedTiming().endTime??0);
   // play() rewinds a finished animation; returning to the tab must keep its settled pose.
   if(!visible||(open&&Number(animation.currentTime)>=end-.01))animation.pause();else animation.play();
  }
  if(!open)void Promise.all(current.map(a=>a.finished.catch(()=>{}))).then(()=>{if(!latestOpen.current){current.forEach(a=>a.cancel());animations.current=[];setPresent(false);}});
 },[open,present,ready,reduced,failed,visible]);
 useEffect(()=>{
  if(!present||!ready||failed||reduced){floating.current.forEach(a=>a.cancel());floating.current=[];return;}
  if(open&&visible&&!floating.current.length){
   const frames=cityWayfinding.float_keyframes.map(k=>({offset:k.offset,transform:`translate(${k.x/8}vw,${k.y}px)`}));
   floating.current=carriers.current.map((node,index)=>node!.animate(frames,{duration:cityWayfinding.float_duration_ms,iterations:Infinity,easing:'linear',delay:index*160}));
  }
  for(const animation of floating.current){if(open&&visible)animation.play();else animation.pause();}
 },[present,ready,failed,reduced,open,visible]);
 useEffect(()=>()=>{animations.current.forEach(a=>a.cancel());floating.current.forEach(a=>a.cancel());},[]);
 if(!present&&!open)return null;
 return createPortal(<div ref={panel} className="city-wayfinding" data-state={open?'open':'closing'} data-art-status={failed?'error':ready?'ready':'loading'} aria-hidden={!open||undefined}>
  {failed?<nav className="city-wayfinding-fallback" aria-label={language==='ro'?'Destinații':'Destinations'}>{cityDestinations.map(d=><button key={d.id} data-destination={d.id} disabled={!open} onClick={()=>onEnter(d.id)}>{d[language]}</button>)}</nav>:cityDestinations.map((d,index)=>{
   const item=cityWayfinding.signs[d.id],crop=item.crop,face=item.final_face_rect;
   const styles={'--sign-x':crop.x/1600*100+'vw','--sign-y':crop.y/570*208+'px','--sign-w':crop.width/1600*100+'vw','--sign-h':crop.height/570*208+'px','--target-x':face.x/1600*100+'vw','--target-y':(face.y+face.height/2)/570*208+'px','--target-w':face.width/1600*100+'vw'} as CSSProperties;
   return <div ref={node=>{carriers.current[index]=node;}} className="city-wayfinding-sign" key={d.id} style={styles} data-destination={d.id}>
    <span ref={node=>{nodes.current[index]=node;}} className="city-wayfinding-art" data-frames={item.frame_count} style={{backgroundImage:`url(/ambient/${item.languages[language][night?'night':'day']})`,backgroundSize:`${item.frame_count*100}% 100%`}}/>
    <button className="city-wayfinding-target" aria-label={language==='ro'?`Intră în ${d.ro}`:`Enter ${d.en}`} disabled={!open||!ready} onClick={()=>onEnter(d.id)}/>
   </div>;
  })}
 </div>,document.querySelector('.app')!);
}
