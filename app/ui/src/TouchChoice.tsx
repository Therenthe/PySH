import {useEffect, useRef, useState} from 'react';
import './touch-choice.css';
import {useDialogFocus} from './useDialogFocus';

/** Stable app-owned selector: polling/clock renders must not dismiss an open choice. */
export function TouchChoice({label,value,options,onChange,closeLabel,onOpenChange}:{label:string;value:string;options:{value:string;label:string}[];onChange:(value:string)=>Promise<unknown>;closeLabel:string;onOpenChange?:(open:boolean)=>void}) {
 const [open,setOpen]=useState(false),[saving,setSaving]=useState(false);
 const [failed,setFailed]=useState(false);
 useEffect(()=>{onOpenChange?.(open);return()=>{if(open)onOpenChange?.(false);};},[open,onOpenChange]);
 const trigger=useRef<HTMLButtonElement>(null),dialog=useDialogFocus<HTMLDivElement>(()=>setOpen(false),saving,open);
 const moveChoice=(event:React.KeyboardEvent<HTMLDivElement>)=>{
  if(!['ArrowDown','ArrowUp','ArrowLeft','ArrowRight','Home','End'].includes(event.key)||saving)return;
  const radios=Array.from(event.currentTarget.querySelectorAll<HTMLButtonElement>('[role="radio"]:not(:disabled)'));
  const index=radios.indexOf(document.activeElement as HTMLButtonElement);
  if(index<0)return;
  event.preventDefault();const next=event.key==='Home'?0:event.key==='End'?radios.length-1:(index+(['ArrowUp','ArrowLeft'].includes(event.key)?-1:1)+radios.length)%radios.length;
  radios[next]?.focus();
 };
 return <><button ref={trigger} className="touch-choice-trigger" aria-label={label} aria-haspopup="dialog" aria-expanded={open} onClick={()=>setOpen(true)}><span>{options.find(o=>o.value===value)?.label||value}</span><span aria-hidden="true">⌄</span></button>
 {open&&<div className="touch-choice-scrim" onPointerDown={e=>{if(e.target===e.currentTarget&&!saving)setOpen(false);}}><div ref={dialog} tabIndex={-1} onKeyDown={moveChoice} className="touch-choice-dialog" role="dialog" aria-modal="true" aria-label={label}>
 <header><h2>{label}</h2><button disabled={saving} aria-label={closeLabel} onClick={()=>setOpen(false)}>×</button></header>
 {saving&&<p role="status">{closeLabel==='Închide'?'Se salvează…':'Saving…'}</p>}{failed&&<p role="alert">{closeLabel==='Închide'?'Nu s-a salvat. Încearcă din nou sau închide lista.':'Not saved. Try again or close this list.'}</p>}
 <div className="touch-choice-options" role="radiogroup" aria-label={label}>{options.map(option=><button key={option.value} role="radio" data-dialog-initial={value===option.value?true:undefined} aria-checked={value===option.value} disabled={saving} onClick={async()=>{setSaving(true);setFailed(false);try{const result=await onChange(option.value);if(result!==null)setOpen(false);else setFailed(true);}catch{setFailed(true);}finally{setSaving(false);}}}><span>{option.label}</span><span aria-hidden="true">{value===option.value?'✓':''}</span></button>)}</div>
 </div></div>}</>;
}
