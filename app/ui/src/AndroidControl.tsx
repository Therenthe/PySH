import {useRef,useState} from 'react';
import {useDialogFocus} from './useDialogFocus';
import {RemoteIcon} from './PowerPanel';
import './android-control.css';

export type AndroidControlState={available:boolean;enabled:boolean;hubId?:string;pending:{requestId:string;name:string;expiresIn:number}[];devices:{deviceId:string;name:string}[];error?:string};
type Props={control?:AndroidControlState;ro:boolean;request:(path:string,init?:RequestInit)=>Promise<any>;refresh:()=>Promise<unknown>};
const words=(ro:boolean)=>({yes:ro?'Da':'Yes',no:ro?'Nu':'No',title:'Android App Control',active:ro?'Activ':'Active',off:ro?'Dezactivat':'Disabled',unavailable:ro?'Serviciul nu este disponibil.':'Service unavailable.',switch:ro?'Activează Android App Control':'Enable Android App Control',hint:ro?'Deschide aplicația PySH pe un telefon conectat la aceeași rețea Wi-Fi. Hub-ul este găsit automat.':'Open the PySH app on a phone connected to the same Wi-Fi network. Your hub is found automatically.',approval:ro?'Telefoanele noi se conectează după ce alegi Da pe acest ecran.':'New phones connect after you choose Yes on this screen.',devices:ro?'Telefoane asociate':'Paired phones',empty:ro?'Niciun telefon asociat încă.':'No paired phones yet.',remove:ro?'Elimină accesul':'Remove access',cancel:ro?'Anulează':'Cancel',check:ro?'Verifică starea':'Check status',busy:ro?'Se aplică…':'Applying…',failed:ro?'Nu s-a putut confirma rezultatul. Verifică starea înainte de a reîncerca.':'Could not confirm the result. Check status before trying again.'});

function useControlAction({request,refresh}:Props){
 const lock=useRef(false),[pending,setPending]=useState(false),[uncertain,setUncertain]=useState(false);
 async function change(path:string,body?:object,method='POST'){
  if(lock.current||uncertain)return false;lock.current=true;setPending(true);
  try{await request(path,{method,...(body?{body:JSON.stringify(body)}:{})});await refresh();return true;}
  catch{setUncertain(true);return false;}finally{lock.current=false;setPending(false);}
 }
 async function check(){if(lock.current)return;lock.current=true;setPending(true);try{await refresh();setUncertain(false);}catch{setUncertain(true);}finally{lock.current=false;setPending(false);}}
 return {pending,uncertain,change,check};
}
export function AndroidControlPanel(props:Props){
 const {control,ro}=props,text=words(ro),action=useControlAction(props),[remove,setRemove]=useState<string|null>(null);
 const selected=control?.devices.find(device=>device.deviceId===remove);
 return <section className="android-control-panel">
  <div className="panel-heading"><h2>{text.title}</h2><small>{control?.available?(control.enabled?text.active:text.off):'—'}</small></div>
  <div className="android-control-summary"><span className="android-control-mark"><RemoteIcon/></span><div><b>{control?.available?(control.enabled?text.active:text.off):text.unavailable}</b><p>{text.hint}</p></div><button className={`switch ${control?.enabled?'on':''}`} aria-label={text.switch} aria-pressed={!!control?.enabled} disabled={!control?.available||action.pending||action.uncertain} onClick={()=>action.change('/api/android-control',{enabled:!control?.enabled},'PATCH')}><i/></button></div>
  <p className="android-control-hint">{text.approval}</p>
  {control?.error==='discovery_unavailable'&&<div className="android-control-feedback" role="alert"><p>{ro?'Căutarea automată nu este disponibilă momentan. Verifică rețeaua și încearcă din nou.':'Automatic discovery is unavailable for now. Check the network and try again.'}</p><button className="outline" disabled={action.pending} onClick={action.check}>{text.check}</button></div>}
  <ControlFeedback text={text} action={action}/>
  <div className="panel-subhead"><b>{text.devices}</b><span>{control?.devices.length||0}</span></div>
  {!control?.devices.length&&<p className="android-control-hint">{text.empty}</p>}
  {control?.devices.map(device=><div className="android-control-device" key={device.deviceId}><RemoteIcon/><b>{device.name}</b>{selected?.deviceId===device.deviceId?<div className="android-control-remove"><span>{ro?'Elimini accesul acestui telefon?':'Remove this phone’s access?'}</span><button className="outline" disabled={action.pending||action.uncertain} onClick={()=>setRemove(null)}>{text.cancel}</button><button className="outline danger" disabled={action.pending||action.uncertain} onClick={async()=>{if(await action.change('/api/android-control/devices/'+encodeURIComponent(device.deviceId),undefined,'DELETE'))setRemove(null);}}>{text.remove}</button></div>:<button className="outline" disabled={action.pending||action.uncertain} onClick={()=>setRemove(device.deviceId)}>{text.remove}</button>}</div>)}
 </section>;
}
function ControlFeedback({text,action}:{text:ReturnType<typeof words>;action:ReturnType<typeof useControlAction>}){return <>{action.pending&&<p className="android-control-feedback" role="status">{text.busy}</p>}{action.uncertain&&<div className="android-control-feedback" role="alert"><p>{text.failed}</p><button className="outline" disabled={action.pending} onClick={action.check}>{text.check}</button></div>}</>}

export function AndroidPairingPrompt(props:Props){
 const current=props.control?.pending[0];
 if(!props.control?.enabled||!current)return null;
 return <PairingDecision {...props} key={current.requestId} pairing={current}/>;
}
function PairingDecision(props:Props&{pairing:AndroidControlState['pending'][number]}){
 const {pairing,ro}=props,text=words(ro),action=useControlAction(props);
 // Pairing always requires an explicit Yes/No; Escape must not decide it.
 const dialog=useDialogFocus<HTMLElement>(()=>{},true);
 return <div className="android-pairing-scrim"><section ref={dialog} className="android-pairing-card" role="dialog" aria-modal="true" aria-label={ro?'Conectare Android PySH':'PySH Android connection'}>
  <div className="android-pairing-heading"><span className="android-control-mark"><RemoteIcon/></span><span>{text.title}</span></div>
  <div className="android-pairing-body">
  <h2>{ro?'Accepți conectarea de la aplicația Android PySH?':'Accept a connection from the PySH Android app?'}</h2>
  <div className="android-pairing-phone"><RemoteIcon/><b>{pairing.name}</b></div>
  <p>{ro?'Confirmă solicitarea pe care ai inițiat-o pe telefon.':'Confirm the request you started on your phone.'}</p>
  <ControlFeedback text={text} action={action}/>
  </div>
  <div className="android-pairing-actions"><button data-dialog-initial className="outline" disabled={action.pending||action.uncertain} onClick={()=>action.change('/api/android-control/pairing',{requestId:pairing.requestId,accept:false})}>{text.no}</button><button className="primary" disabled={action.pending||action.uncertain} onClick={()=>action.change('/api/android-control/pairing',{requestId:pairing.requestId,accept:true})}>{text.yes}</button></div>
 </section></div>;
}
