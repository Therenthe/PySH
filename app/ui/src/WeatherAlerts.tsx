import {useState,useEffect,useRef} from 'react';
import {createPortal} from 'react-dom';
import {useDialogFocus} from './useDialogFocus';
import './weather-alerts.css';

import {currentWeatherAlerts,type WeatherAlertsDocument} from './weatherAlertModel';
export {currentWeatherAlerts} from './weatherAlertModel';
export type {WeatherAlert,WeatherAlertsDocument} from './weatherAlertModel';

export function WeatherAlertNotice({document:report,now,language,timezone,onOpenChange}:{onOpenChange?:(open:boolean)=>void;document?:WeatherAlertsDocument;now:Date;language:'en'|'ro';timezone:string}){
 const [open,setOpen]=useState(false),button=useRef<HTMLButtonElement>(null),weatherHeading=useRef<HTMLButtonElement|null>(null);
 const alerts=currentWeatherAlerts(report,now),ro=language==='ro';
 useEffect(()=>{if(!report||(report.state==='available'&&alerts.length===0))setOpen(false);},[report?.state,alerts.length]);
 const finish=()=>setOpen(false);
 const dialog=useDialogFocus<HTMLElement>(finish,false,open);
 useEffect(()=>{
  if(open){weatherHeading.current=button.current?.closest('.home-weather')?.querySelector<HTMLButtonElement>('.weather-heading')||null;return;}
  const target=weatherHeading.current;weatherHeading.current=null;
  if(target&&!button.current){const frame=requestAnimationFrame(()=>{if(target.isConnected&&!target.closest('[inert]'))target.focus({preventScroll:true});});return()=>cancelAnimationFrame(frame);}
 },[open]);
 useEffect(()=>{onOpenChange?.(open);return()=>onOpenChange?.(false);},[open,onOpenChange]);
 if(!report)return null;
 const stale=report.state==='stale',unavailable=report.state==='unavailable';
 if(!alerts.length&&!stale&&!unavailable)return null;
 const label=alerts.length?(ro?'Avertizări meteo':'Weather alerts'):(ro?'Avertizări indisponibile':'Alerts unavailable');
 return <><button ref={button} className={`weather-alert-notice ${alerts.length?'has-alerts':'alerts-unknown'}`} aria-label={label} aria-haspopup="dialog" aria-expanded={open} onClick={()=>setOpen(true)}><svg aria-hidden="true" viewBox="0 0 24 24"><path d="M12 3 2 21h20Z"/><path d="M12 9v5m0 3v.2"/></svg>{alerts.length>0&&<span>{alerts.length}</span>}</button>
 {open&&createPortal(<div className="weather-alert-backdrop" onClick={event=>{if(event.target===event.currentTarget)finish();}}><section ref={dialog} role="dialog" aria-modal="true" aria-labelledby="weather-alert-title" className="weather-alert-dialog"><header><h2 id="weather-alert-title">{label}</h2><button data-dialog-initial aria-label={ro?'Închide':'Close'} onClick={finish}>×</button></header>{report.partial&&<p className="weather-alert-partial">{ro?'Unele avertizări nu au putut fi verificate. Avertizările confirmate sunt afișate mai jos.':'Some warnings could not be verified. Confirmed warnings are shown below.'}</p>}{alerts.length?alerts.map(alert=><article key={alert.id} data-severity={alert.severity}><span className="weather-alert-severity">{{minor:ro?'Informare':'Information',moderate:ro?'Atenționare':'Advisory',severe:ro?'Avertizare':'Warning',extreme:ro?'Pericol extrem':'Extreme danger'}[alert.severity]}</span><h3>{alert.headline}</h3>{alert.description&&<p>{alert.description}</p>}{['flood','rain_flood','tornado'].includes(alert.hazard||'')&&<p className="weather-alert-illustration">{ro?'Efectul de pe cer este o ilustrație a avertizării, nu imagini live sau confirmarea unui dezastru la adresă.':'The scene effect illustrates the warning. It is not live imagery or confirmation of a disaster at your address.'}</p>}<footer><strong>{alert.provider}</strong><span>{/^https?:\/\//.test(alert.source)?(ro?'Avertizare oficială':'Official warning'):alert.source}</span><span>{ro?'Până la':'Until'} {new Intl.DateTimeFormat(ro?'ro-RO':'en-GB',{weekday:'short',hour:'2-digit',minute:'2-digit',timeZone:timezone}).format(new Date(alert.expires))}</span></footer></article>):<p className="weather-alert-unknown">{stale?(ro?'Datele de avertizare sunt expirate. Nu putem confirma avertizările active.':'Alert information is out of date. Active warnings cannot be confirmed.'):(ro?'Avertizările meteo nu pot fi verificate momentan. PySH reîncearcă automat.':'Weather warnings cannot be verified right now. PySH retries automatically.')}</p>}</section></div>,document.querySelector('.app')||document.body)}
 </>;
}
