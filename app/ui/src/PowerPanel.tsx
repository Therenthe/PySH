import {useEffect,useRef,useState} from 'react';
import {AudioVolume} from './AudioVolume';
import './power.css';

export type PowerState={standby:boolean;brightness:{available:boolean;value?:number;error?:string};timer:{deadline?:string|null;remainingSeconds?:number};daily:{enabled:boolean;time:string};error?:string};
type Request=(path:string,init?:RequestInit)=>Promise<any>;
export function PowerIcon(){return <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" aria-hidden="true"><path d="M12 3v9M7 5.7a8 8 0 1 0 10 0"/></svg>}
export function RemoteIcon(){return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" aria-hidden="true"><rect x="7" y="2" width="10" height="20" rx="3"/><path d="M10 5h4M11 18h2"/><circle cx="12" cy="11" r="2"/></svg>}
export const powerWords=(ro:boolean)=>({title:ro?'Ecran și standby':'Display & standby',standby:ro?'Standby':'Standby',wake:ro?'Pornește PySH':'Turn on PySH',sleep:ro?'Oprește PySH':'Turn off PySH',hint:ro?'Redarea se oprește, ecranul se stinge. Atinge ecranul sau pornește din aplicație.':'Playback stops and the screen turns off. Touch the screen or turn on from the app.',brightness:ro?'Luminozitate ecran':'Screen brightness',unavailable:ro?'Reglajul ecranului nu este disponibil.':'Display adjustment is unavailable.',timer:ro?'Oprire după':'Turn off after',cancel:ro?'Anulează temporizatorul':'Cancel timer',daily:ro?'Oprire zilnică':'Daily turn off',at:ro?'Ora de oprire':'Turn off time',pending:ro?'Se aplică…':'Applying…',failed:ro?'Nu s-a putut aplica. Verifică starea înainte de a reîncerca.':'Could not apply. Check status before trying again.',check:ro?'Verifică starea':'Check status',none:ro?'Fără temporizator':'No timer',remaining:ro?'Standby în':'Standby in',wakeHint:ro?'Atinge pentru a porni':'Touch to turn on'});

export function PowerPanel({power,prefs,ro,request,refresh,editTime}:{power?:PowerState;prefs:any;ro:boolean;request:Request;refresh:()=>Promise<unknown>;editTime:(value:string)=>Promise<string|null>}){
 const text=powerWords(ro),lock=useRef(false);
 const [pending,setPending]=useState(false),[error,setError]=useState(false);
 async function change(path:string,body:object,method='POST'){
  if(lock.current)return;lock.current=true;setPending(true);setError(false);
  try{await request(path,{method,body:JSON.stringify(body)});await refresh();}catch{setError(true);}finally{lock.current=false;setPending(false);}
 }
 const remaining=Math.max(0,Math.ceil((power?.timer.remainingSeconds||0)/60));
 const daily=power?.daily||{enabled:!!prefs.dailyStandbyEnabled,time:prefs.dailyStandbyTime||'23:00'};
 return <div className="power-panel">
  <div className="panel-heading"><h2>{text.title}</h2><small>PySH</small></div>
  <div className="power-summary"><span className="power-symbol"><PowerIcon/></span><div><b>{power?.standby?text.standby:(ro?'Pornit':'On')}</b><p>{text.hint}</p></div><button className="outline" disabled={pending||!power} onClick={()=>change('/api/power',{standby:!power?.standby})}>{power?.standby?text.wake:text.sleep}</button></div>
  {pending&&<p role="status">{text.pending}</p>}{error&&<div role="alert" className="power-feedback"><p>{text.failed}</p><button className="outline" disabled={pending} onClick={async()=>{try{await refresh();setError(false);}catch{setError(true);}}}>{text.check}</button></div>}
  <div className="power-setting"><div><b>{text.brightness}</b><span>{power?.brightness.available?`${power.brightness.value??prefs.screenBrightness??100}%`:'—'}</span></div><AudioVolume label={text.brightness} value={power?.standby?prefs.screenBrightness??100:power?.brightness.value??prefs.screenBrightness??100} disabled={pending||!power?.brightness.available} onChange={value=>change('/api/preferences',{screenBrightness:Math.max(1,value)},'PATCH')}/>{!power?.brightness.available&&<p className="setting-help">{text.unavailable}</p>}</div>
  <div className="power-setting"><div><b>{text.timer}</b><span>{remaining?`${text.remaining} ${remaining} min`:text.none}</span></div><div className="sleep-presets">{[15,30,60,90,120].map(minutes=><button className="outline" key={minutes} disabled={pending||!power||power.standby} onClick={()=>change('/api/power/timer',{minutes})}>{minutes} min</button>)}</div>{remaining>0&&<button className="text-button" disabled={pending} onClick={()=>change('/api/power/timer',{minutes:0})}>{text.cancel}</button>}</div>
  <div className="power-setting"><div><b>{text.daily}</b><button className={`switch ${daily.enabled?'on':''}`} aria-label={text.daily} aria-pressed={daily.enabled} disabled={pending||!power} onClick={()=>change('/api/preferences',{dailyStandbyEnabled:!daily.enabled},'PATCH')}><i/></button></div><div><span>{text.at}</span><button className="setting-value" disabled={pending||!power} onClick={async()=>{const value=await editTime(daily.time);if(value!==null){if(/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(value))await change('/api/preferences',{dailyStandbyTime:value},'PATCH');else setError(true);}}}>{daily.time}</button></div><p className="setting-help">{prefs.timezone||'Europe/Bucharest'}</p></div>
 </div>;
}

export function StandbyScreen({ro,request,onWake}:{ro:boolean;request:Request;onWake:()=>Promise<unknown>}){
 const text=powerWords(ro),locked=useRef(false),[pending,setPending]=useState(false),[failed,setFailed]=useState(false);
 const wake=async()=>{if(locked.current)return;locked.current=true;setPending(true);setFailed(false);try{await request('/api/power',{method:'POST',body:JSON.stringify({standby:false})});await onWake();}catch{setFailed(true);}finally{locked.current=false;setPending(false);}};
 useEffect(()=>{const press=(event:MouseEvent)=>{event.preventDefault();event.stopImmediatePropagation();void wake();};const key=(event:KeyboardEvent)=>{if(['Enter',' '].includes(event.key)){event.preventDefault();void wake();}};window.addEventListener('click',press,{capture:true});window.addEventListener('keydown',key);return()=>{window.removeEventListener('click',press,true);window.removeEventListener('keydown',key);};},[]);
 return <main className="standby-screen"><span className="standby-brand">PySH</span><button aria-label={text.wake} disabled={pending} onClick={wake}><PowerIcon/><h1>{text.standby}</h1><p>{pending?text.pending:text.wakeHint}</p></button>{failed&&<p role="alert">{text.failed}</p>}</main>;
}
