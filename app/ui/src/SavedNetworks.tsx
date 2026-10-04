type Props={networks:any[];busy:boolean;t:(key:string)=>string;onPassword:(profile:any)=>void;onForget:(profile:any)=>void};

/** Names are labels; only the supplied profile UUID identifies the saved connection. */
export function SavedNetworks({networks,busy,t,onPassword,onForget}:Props){
 if(!networks.length)return null;
 return <section className="saved-networks" aria-label={t('savedConnection')}><h3>{t('savedConnection')}</h3>
  {networks.map(profile=><div className="saved-network" key={profile.id}>
   <div className="saved-network-copy"><b>{profile.name||profile.ssid}</b><small>{profile.ssid||t(profile.type==='802-3-ethernet'?'ethernet':'wifi')}{profile.active?` · ${t('connected')}`:''}</small></div>
   <div className="saved-network-actions">
    {profile.type==='802-11-wireless'&&profile.security==='secured'&&profile.ssid&&<button className="outline" disabled={busy} aria-label={`${t('changePassword')}: ${profile.name||profile.ssid}`} onClick={()=>onPassword(profile)}>{t('changePassword')}</button>}
    <button className="outline danger" disabled={busy} aria-label={`${t('forgetNetwork')}: ${profile.name||profile.ssid}`} onClick={()=>onForget(profile)}>{t('forgetNetwork')}</button>
   </div>
  </div>)}
 </section>;
}
