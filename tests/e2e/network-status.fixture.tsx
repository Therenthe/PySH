import React from 'react';
import {createRoot} from 'react-dom/client';
import {NetworkStatus,networkStatusModel,type NetworkStatusData} from '../../app/ui/src/NetworkStatus';
import '../../app/ui/src/style.css';
import '../../app/ui/src/canvas-shell.css';

const root=createRoot(document.getElementById('root')!);
(window as any).showNetworkStatus=(network:NetworkStatusData,language:'en'|'ro',theme:'ink'|'night')=>{
 document.documentElement.lang=language;
 (window as any).networkModel=networkStatusModel(network,language);
 root.render(<div className="app" data-theme={theme}><main style={{width:'100%'}}>
  <header className="topbar"><span>PI SMART HUB</span><div className="topbar-time"><span className="top-clock">22:39</span><span className="date-label">{language==='ro'?'Sâmbătă, 3 Octombrie':'Saturday, 3 October'}</span></div>
   <div className="topbar-right"><NetworkStatus className="top-network" network={network} language={language} onOpen={()=>{(window as any).networkOpens=((window as any).networkOpens||0)+1}}/><button className="icon-button" aria-label="Standby">◯</button><button className="icon-button" aria-label="Settings">⚙</button></div>
  </header>
 </main></div>);
};
(window as any).networkFixtureReady=true;
