import './network-status.css';

export type NetworkDeviceStatus = {type?:string;interface?:string;state?:string;ssid?:string|null;signal?:number};
export type NetworkStatusData = {
 available?:boolean;state?:string;wireless_enabled?:boolean;
 devices?:NetworkDeviceStatus[];
 networks?:{ssid?:string;in_use?:boolean;signal?:number}[];
};
type LinkState='connected'|'connecting'|'disconnected'|'unavailable'|'off'|'unknown'|'failed';
const words={
 en:{network:'Network',connected:'Connected',connecting:'Connecting',disconnected:'Not connected',unavailable:'Unavailable',off:'Off',unknown:'Status unknown',failed:'Connection failed',signal:'Signal',signalUnknown:'Signal strength unavailable',open:'Open network settings'},
 ro:{network:'Rețea',connected:'Conectat',connecting:'Se conectează',disconnected:'Neconectat',unavailable:'Indisponibil',off:'Oprit',unknown:'Stare necunoscută',failed:'Conectare eșuată',signal:'Semnal',signalUnknown:'Puterea semnalului indisponibilă',open:'Deschide setările de rețea'},
};
const connecting=new Set(['prepare','config','ip_config','ip_check','secondaries','connecting']);
function linkState(state?:string):LinkState{
 if(state==='connected')return 'connected';
 if(connecting.has(state||''))return 'connecting';
 if(state==='failed')return 'failed';
 if(state==='unavailable'||state==='unmanaged')return 'unavailable';
 if(state==='disconnected'||state==='deactivating')return 'disconnected';
 return 'unknown';
}

/** Link association is not an assertion that the internet is reachable. */
export function networkStatusModel(network:NetworkStatusData,language:'en'|'ro'){
 const text=words[language];
 const devices=(network.devices||[]).filter(d=>d.type==='wifi'||d.type==='ethernet');
 const links=(['wifi','ethernet'] as const).flatMap(type=>{
  const candidates=devices.filter(d=>d.type===type);
  if(!candidates.length)return [];
  const device=candidates.find(d=>d.state==='connected')||candidates.find(d=>connecting.has(d.state||''))||candidates[0];
  const state=type==='wifi'&&network.wireless_enabled===false?'off':linkState(device.state);
  // Never use the strongest neighbouring AP as the connected link's strength.
  const ap=type==='wifi'&&state==='connected'&&device.ssid
   ?network.networks?.find(n=>n.in_use===true&&n.ssid===device.ssid):undefined;
  const validSignal=(value:unknown):value is number=>typeof value==='number'&&Number.isFinite(value)&&value>=0&&value<=100;
  const signal=type==='wifi'&&state==='connected'&&validSignal(device.signal)?Math.round(device.signal):validSignal(ap?.signal)?Math.round(ap.signal):null;
  const label=type==='wifi'?'Wi-Fi':'Ethernet';
  const detail=`${label}: ${text[state]}${type==='wifi'&&state==='connected'?`, ${signal===null?text.signalUnknown:`${text.signal} ${signal}%`}`:''}`;
  return [{type,state,signal,label,detail}];
 });
 if(links.length)return {links,label:links.map(l=>l.detail).join('; ')};
 const state=network.available===false?'unavailable':linkState(network.state);
 return {links:[{type:'network' as const,state,signal:null,label:text.network,detail:`${text.network}: ${text[state]}`}],label:`${text.network}: ${text[state]}`};
}

function LinkIcon({type,state,signal}:{type:'wifi'|'ethernet'|'network';state:LinkState;signal:number|null}){
 const disconnected=!['connected','connecting','unknown'].includes(state);
 const level=signal===null?null:signal<25?0:signal<50?1:signal<75?2:3;
 return <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" data-signal={level===null?'unknown':level}>
  {type==='wifi'?<>
   <path className={level!==null&&level<3?'network-arc-inactive':''} strokeDasharray={level===null&&state==='connected'?'1 3':undefined} d="M2.5 8.5a15 15 0 0 1 19 0"/>
   <path className={level!==null&&level<2?'network-arc-inactive':''} strokeDasharray={level===null&&state==='connected'?'1 3':undefined} d="M5.7 12a10 10 0 0 1 12.6 0"/>
   <path className={level!==null&&level<1?'network-arc-inactive':''} d="M9 15.5a4.7 4.7 0 0 1 6 0"/>
   <circle cx="12" cy="19" r="1.25" fill="currentColor" stroke="none"/>
  </>:type==='ethernet'?<><path d="M5 4h14v10l-4 4H9l-4-4Z"/><path d="M8 4v5m4-5v5m4-5v5M12 18v4m-4 0h8"/></>:<><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c5 5 5 13 0 18-5-5-5-13 0-18"/></>}
  {disconnected&&<path className="network-link-slash" d="m3 3 18 18"/>}
  {state==='connecting'&&<circle cx="20" cy="19" r="2.2" fill="currentColor" stroke="none"/>}
 </svg>;
}

/** A single 48px touch target; two rows preserve independent wired/Wi-Fi state. */
export function NetworkStatus({network,language,onOpen,className=''}:{network:NetworkStatusData;language:'en'|'ro';onOpen:()=>void;className?:string}){
 const model=networkStatusModel(network,language);
 return <button type="button" className={`network-status ${className}`} onClick={onOpen} aria-label={`${model.label}. ${words[language].open}`} title={model.label}>
  {model.links.map(link=><span className="network-status-link" data-network-link={link.type} data-link-state={link.state} key={link.type}>
   <LinkIcon type={link.type} state={link.state} signal={link.signal}/><span>{link.label}</span>
   {link.state==='connecting'&&<span className="network-status-progress" aria-hidden="true">…</span>}
  </span>)}
 </button>;
}
