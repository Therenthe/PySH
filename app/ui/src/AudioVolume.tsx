import {useEffect,useRef,useState,type PointerEvent} from 'react';

const bounded=(value:number)=>Number.isFinite(value)?Math.max(0,Math.min(100,Math.round(value))):0;

/** A drag previews only the thumb; commit exactly its final position on release. */
export function AudioVolume({label,value,disabled=false,onChange}:{label:string;value:number;disabled?:boolean;onChange:(volume:number)=>unknown}){
 const [draft,setDraft]=useState<number|null>(null);
 const pointer=useRef<number|null>(null),input=useRef<HTMLInputElement>(null);
 const cancel=()=>{const id=pointer.current;pointer.current=null;setDraft(null);if(id!==null&&input.current?.hasPointerCapture(id))input.current.releasePointerCapture(id);};
 useEffect(()=>{if(disabled)cancel();},[disabled]);
 useEffect(()=>{const blur=()=>cancel();window.addEventListener('blur',blur);return()=>{window.removeEventListener('blur',blur);const id=pointer.current;pointer.current=null;if(id!==null&&input.current?.hasPointerCapture(id))input.current.releasePointerCapture(id);};},[]);
 const point=(event:PointerEvent<HTMLInputElement>)=>{const rect=event.currentTarget.getBoundingClientRect();return rect.width>0?bounded((event.clientX-rect.left)/rect.width*100):bounded(value);};
 return <input ref={input} type="range" aria-label={label} min="0" max="100" step="1" value={draft??bounded(value)} disabled={disabled}
  onChange={event=>{if(pointer.current===null&&!disabled)onChange(bounded(Number(event.target.value)));}}
  onPointerDown={event=>{if(disabled||pointer.current!==null||event.button!==0)return;event.preventDefault();event.currentTarget.setPointerCapture(event.pointerId);pointer.current=event.pointerId;setDraft(point(event));}}
  onPointerMove={event=>{if(pointer.current===event.pointerId)setDraft(point(event));}}
  onPointerUp={event=>{if(pointer.current!==event.pointerId)return;const next=point(event);cancel();if(!disabled)onChange(next);}}
  onPointerCancel={event=>{if(pointer.current===event.pointerId)cancel();}}
  onLostPointerCapture={event=>{if(pointer.current===event.pointerId){pointer.current=null;setDraft(null);}}}/>
}
