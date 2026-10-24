import React from 'react';
import {createRoot} from 'react-dom/client';
import {AmbientSky} from '../../app/ui/src/Home';
import '../../app/ui/src/style.css';
import '../../app/ui/src/ambient-home.css';

const root=createRoot(document.getElementById('root')!);
(window as any).showCityWifi=(night:boolean,wifiState:'off'|'disconnected'|'connecting'|'connected'|'unknown',wifiActive:boolean)=>{
 root.render(<div className="app" data-theme={night?'night':'ink'} style={{position:'relative',width:800,height:480,margin:0}}><AmbientSky code={0} isDay={night?0:1} stale={false} aircraft={false} now={new Date(night?'2026-10-23T19:00:00Z':'2026-10-23T10:00:00Z')} latitude={44.4} longitude={26.1} wifiState={wifiState} wifiActive={wifiActive}/></div>);
};
(window as any).cityWifiFixtureReady=true;
