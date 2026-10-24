import {useEffect,useRef,useState,type ReactNode,type PointerEvent} from 'react';
import {useDialogFocus} from './useDialogFocus';
import {AudioVolume} from './AudioVolume';
import type {PowerState} from './PowerPanel';
import './quick-controls.css';

type Props={ro:boolean;audio:any;power?:PowerState;brightness:number;busy:boolean;audioBusy:boolean;recovery:ReactNode;playback:ReactNode;icon:(name:string)=>ReactNode;request:(path:string,init?:RequestInit)=>Promise<any>;refresh:()=>Promise<unknown>;onAudio:(body:{volume?:number;mute?:boolean;output?:string})=>unknown;onClose:()=>void;onNavigate:(page:'home'|'radio'|'media')=>void;onSettings:()=>void;onStandby:()=>void;onNetwork:()=>void;onBluetooth:()=>void;networkLabel:string;bluetoothLabel:string};
export function QuickControls(p:Props){
 const {ro}=p,[pane,setPane]=useState<'controls'|'outputs'>('controls'),[pending,setPending]=useState(false),[failure,setFailure]=useState<{value:number;phase:'action'|'state'}|null>(null),lock=useRef(false);
 const blocked=p.busy||p.audioBusy||pending,dialog=useDialogFocus<HTMLElement>(p.onClose,blocked),close=useRef<HTMLButtonElement>(null),output=useRef<HTMLButtonElement>(null),outputTitle=useRef<HTMLHeadingElement>(null);
 const words={title:ro?'Comenzi rapide':'Quick controls',close:ro?'Închide':'Close',home:ro?'Acasă':'Home',volume:ro?'Volum':'Volume',brightness:ro?'Luminozitate':'Brightness',output:ro?'Ieșire audio':'Audio output',none:ro?'Nicio ieșire audio disponibilă':'No audio output available',unavailable:ro?'Reglaj indisponibil':'Adjustment unavailable',settings:ro?'Toate setările':'All settings',standby:'Standby',back:ro?'Înapoi':'Back',check:ro?'Verifică starea':'Check status',retry:ro?'Încearcă din nou':'Try again',pending:ro?'Se aplică…':'Applying…',unverified:ro?'Rezultatul nu poate fi verificat. Verifică starea înainte de a reîncerca.':'Result could not be verified. Check status before trying again.',failed:ro?'Reglajul cerut nu este confirmat.':'Requested adjustment is not confirmed.'};
 useEffect(()=>{if(pane==='outputs')outputTitle.current?.focus();},[pane]);
 useEffect(()=>{if(blocked)dialog.current?.focus();else if(document.activeElement===dialog.current)close.current?.focus();},[blocked]);
 async function brightness(value:number,phase:'action'|'state'='action'){
  if(lock.current||blocked)return;lock.current=true;setPending(true);setFailure(null);
  try{
   if(phase==='action')await p.request('/api/preferences',{method:'PATCH',body:JSON.stringify({screenBrightness:value})});
   phase='state';const snapshot:any=await p.refresh(),readback=snapshot?.power?.brightness;
   if(!readback?.available||typeof readback.value!=='number')throw new Error('brightness_unverified');
   if(readback.value!==value)setFailure({value,phase:'action'});
  }
  catch(error:any){const rejectedBeforeWrite=error?.definite===true&&[400,401,403,404,405,413,422].includes(error.status);setFailure({value,phase:rejectedBeforeWrite?phase:'state'});}
  finally{lock.current=false;setPending(false);}
 }
 const active=p.audio.outputs?.find((item:any)=>item.active||item.id===p.audio.output),level=p.power?.brightness.value??p.brightness;
 const outputBack=()=>{setPane('controls');requestAnimationFrame(()=>output.current?.focus());};
 return <div className="command-scrim" onPointerDown={event=>{if(event.target===event.currentTarget&&!blocked)p.onClose();}}><section ref={dialog} tabIndex={-1} className="modal-card quick-controls-dialog command-sheet" role="dialog" aria-modal="true" aria-label={words.title} aria-busy={blocked}>
  <header className="command-heading"><div><h2>{pane==='outputs'?words.output:words.title}</h2><span>PySH</span></div><div className="command-header-actions"><button data-command="network" className="icon-button" aria-label={p.networkLabel} disabled={blocked} onClick={p.onNetwork}>{p.icon('wifi')}</button><button data-command="bluetooth" className="icon-button" aria-label={p.bluetoothLabel} disabled={blocked} onClick={p.onBluetooth}>{p.icon('bt')}</button><button ref={close} className="icon-button" aria-label={words.close} disabled={blocked} onClick={p.onClose}>{p.icon('close')}</button></div></header>
  <div className="modal-body command-body">{pane==='controls'?<>
   <nav className="command-nav" aria-label={ro?'Continuă în':'Continue in'}>{(['home','radio','media'] as const).map(page=><button key={page} disabled={blocked} onClick={()=>p.onNavigate(page)}>{page==='radio'?<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M3 8h18v13H3ZM4 8 19 3M7 12h10M7 16h2m6 0h2"/></svg>:p.icon(page)}<span>{page==='home'?words.home:page==='radio'?'Radio':'Media'}</span></button>)}</nav>
   <div className="quick-modal command-settings">
    <div className="command-setting"><label htmlFor="command-volume">{words.volume}<b>{p.audio.available&&p.audio.volume!==null?`${p.audio.volume}%`:'—'}</b></label><div><AudioVolume id="command-volume" label={words.volume} disabled={blocked||!p.audio.ready||typeof p.audio.volume!=='number'} value={p.audio.volume??0} onChange={volume=>p.onAudio({volume})}/><button className="icon-button" aria-label={p.audio.mute?(ro?'Activează sunetul':'Unmute'):(ro?'Fără sunet':'Mute')} aria-pressed={!!p.audio.mute} disabled={blocked||!p.audio.ready||typeof p.audio.mute!=='boolean'} onClick={()=>p.onAudio({mute:!p.audio.mute})}>{p.audio.mute?<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M4 10v4h4l5 4V6l-5 4zM17 9l5 6m0-6-5 6"/></svg>:p.icon('speaker')}</button></div></div>
    <div className="command-setting"><label htmlFor="command-brightness">{words.brightness}{!p.power?.brightness.available?` · ${words.unavailable}`:''}<b>{p.power?.brightness.available?`${level}%`:'—'}</b></label><AudioVolume id="command-brightness" min={1} label={ro?'Luminozitate ecran':'Screen brightness'} disabled={blocked||failure?.phase==='state'||!p.power?.brightness.available} value={level} onChange={value=>brightness(value)}/></div>
   </div>
   <div className="command-output-row"><button ref={output} className="command-output" aria-label={words.output} disabled={blocked||!p.audio.available} onClick={()=>setPane('outputs')}>{p.icon('speaker')}<span><small>{words.output}</small><b>{active?.description||active?.name||words.none}</b></span>{p.icon('next')}</button><button className="command-all-settings" disabled={blocked} onClick={p.onSettings}>{p.icon('settings')}<span>{words.settings}</span></button></div>
   <div className="command-context">{p.playback||<span className="command-empty">{ro?'Nimic în redare':'Nothing playing'}</span>}<button className="icon-button" aria-label={words.standby} disabled={blocked||!p.power} onClick={p.onStandby}>{p.icon('power')}</button></div>
  </>:<><div className="command-output-heading"><button className="icon-button" aria-label={words.back} disabled={blocked} onClick={outputBack}>{p.icon('back')}</button><h3 ref={outputTitle} tabIndex={-1}>{words.output}</h3></div><div className="command-output-list">{p.audio.outputs?.length?p.audio.outputs.map((item:any)=><button key={item.id} disabled={blocked} aria-pressed={!!(item.active||item.id===p.audio.output)} onClick={()=>p.onAudio({output:item.id})}>{p.icon('speaker')}<span>{item.description||item.name||item.id}</span>{(item.active||item.id===p.audio.output)&&p.icon('check')}</button>):<p>{words.none}</p>}</div></>}
  <div className="command-feedback" aria-live="polite">{pending?<p role="status">{words.pending}</p>:failure?<div role="alert" className="network-feedback"><p>{failure.phase==='state'?words.unverified:words.failed}</p><button className="icon-button" aria-label={failure.phase==='state'?words.check:words.retry} disabled={blocked} onClick={()=>brightness(failure.value,failure.phase)}>{p.icon('refresh')}</button><button className="icon-button" aria-label={words.close} disabled={blocked} onClick={()=>setFailure(null)}>{p.icon('close')}</button></div>:p.recovery}</div></div>
 </section></div>;
}

/** A small edge gesture has an existing48px toolbar-button alternative. */
export function HubCommandPull({enabled,onOpen}:{enabled:boolean;onOpen:()=>void}){
 const gesture=useRef<{id:number;x:number;y:number}|null>(null);
 const start=(event:PointerEvent<HTMLDivElement>)=>{if(!enabled||event.button!==0)return;gesture.current={id:event.pointerId,x:event.clientX,y:event.clientY};event.preventDefault();event.currentTarget.setPointerCapture(event.pointerId);};
 const move=(event:PointerEvent<HTMLDivElement>)=>{const start=gesture.current;if(!start||start.id!==event.pointerId)return;if(Math.abs(event.clientX-start.x)>36){gesture.current=null;return;}if(event.clientY-start.y>18){gesture.current=null;onOpen();}};
 return enabled?<div className="hub-command-pull" aria-hidden="true" onPointerDown={start} onPointerMove={move} onPointerUp={()=>gesture.current=null} onPointerCancel={()=>gesture.current=null}/>:null;
}
