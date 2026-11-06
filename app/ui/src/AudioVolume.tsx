import {useEffect,useRef,useState,type PointerEvent} from 'react';
import './live-level.css';

const bounded=(value:number)=>Number.isFinite(value)?Math.max(0,Math.min(100,Math.round(value))):0;

/** The owner's queue applies previews while this draft shields the drag from polling. */
export function AudioVolume({label,value,disabled=false,pending=false,closing=false,onChange,min=0,id}:{label:string;value:number;disabled?:boolean;pending?:boolean;closing?:boolean;onChange:(volume:number,persist:boolean)=>unknown;min?:number;id?:string}){
 const clamp=(next:number)=>Math.max(min,bounded(next));
 const [draft,setDraft]=useState<number|null>(null),[working,setWorking]=useState(false);
 const pointer=useRef<number|null>(null),input=useRef<HTMLInputElement>(null),latest=useRef<number|null>(null),generation=useRef(0),mounted=useRef(true),callback=useRef(onChange),finalized=useRef(true);
 callback.current=onChange;
 const release=()=>{const id=pointer.current;pointer.current=null;if(id!==null&&input.current?.hasPointerCapture(id))input.current.releasePointerCapture(id);};
 const send=(next:number,persist:boolean)=>{
  const own=generation.current;setWorking(true);
  void Promise.resolve(callback.current(next,persist)).then(result=>{
   if(!mounted.current||own!==generation.current)return;
   if(persist||result===null||result===false){if(result===null||result===false)release();latest.current=null;finalized.current=true;setDraft(null);setWorking(false);}
  },()=>{if(mounted.current&&own===generation.current){release();latest.current=null;finalized.current=true;setDraft(null);setWorking(false);}});
 };
 const preview=(next:number)=>{latest.current=next;setDraft(next);finalized.current=false;send(next,false);};
 const finish=()=>{if(latest.current===null||finalized.current)return;const next=latest.current;release();finalized.current=true;send(next,true);};
 useEffect(()=>{if(disabled){release();latest.current=null;finalized.current=true;generation.current++;setDraft(null);setWorking(false);}},[disabled]);
 useEffect(()=>{if(closing)finish();},[closing]);
 useEffect(()=>{mounted.current=true;const blur=()=>finish();window.addEventListener('blur',blur);return()=>{mounted.current=false;window.removeEventListener('blur',blur);release();if(latest.current!==null&&!finalized.current){finalized.current=true;void callback.current(latest.current,true);}};},[]);
 const point=(event:PointerEvent<HTMLInputElement>)=>{const rect=event.currentTarget.getBoundingClientRect();return rect.width>0?clamp(min+(event.clientX-rect.left)/rect.width*(100-min)):clamp(value);};
 const level=draft??clamp(value),blocked=disabled||closing||pending&&!working&&pointer.current===null;
 return <span className="live-level" data-active={draft!==null||working}>
  <input ref={input} id={id} type="range" aria-label={label} min={min} max="100" step="1" value={level} disabled={blocked}
   onChange={event=>{if(pointer.current===null&&!blocked){generation.current++;latest.current=clamp(Number(event.target.value));setDraft(latest.current);finalized.current=true;send(latest.current,true);}}}
   onPointerDown={event=>{if(blocked||pointer.current!==null||event.button!==0)return;generation.current++;event.preventDefault();event.currentTarget.setPointerCapture(event.pointerId);pointer.current=event.pointerId;preview(point(event));}}
   onPointerMove={event=>{if(pointer.current===event.pointerId)preview(point(event));}}
   onPointerUp={event=>{if(pointer.current!==event.pointerId)return;latest.current=point(event);setDraft(latest.current);finish();}}
   onPointerCancel={event=>{if(pointer.current===event.pointerId)finish();}}
   onLostPointerCapture={event=>{if(pointer.current===event.pointerId)finish();}}/>
  <span className="audio-volume-value" aria-hidden="true">{level}%</span>
 </span>;
}
