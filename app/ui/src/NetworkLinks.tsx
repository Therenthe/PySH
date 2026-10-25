import './network-links.css';

type NetworkDevice={interface?:string;type?:string;state?:string;ssid?:string|null;ip?:string};

/** A working Ethernet route must not imply that the Wi-Fi radio is connected. */
export function NetworkLinks({devices,t}:{devices:NetworkDevice[];t:(key:string)=>string}){
 const label=(state?:string)=>state==='connected'?t('connected'):
  ['prepare','config','ip_config','ip_check','secondaries'].includes(state||'')?t('connecting'):
  state==='failed'?t('statusError'):state==='unavailable'||state==='unmanaged'?t('deviceUnavailable'):t('notConnected');
 return <div className="network-links">{devices.filter(d=>d.type==='ethernet'||d.type==='wifi').map(d=><div className="network-link" key={`${d.type}:${d.interface}`} data-network-type={d.type}>
  <span className={`status-orb ${d.state==='connected'?'good':''}`} aria-hidden="true"/>
  <div><b>{t(d.type==='wifi'?'wifi':'ethernet')}</b><small>{d.ssid||label(d.state)}{d.ssid?` · ${label(d.state)}`:''}</small></div>
  {d.ip&&<span className="network-link-ip">{d.ip}</span>}
 </div>)}</div>;
}
