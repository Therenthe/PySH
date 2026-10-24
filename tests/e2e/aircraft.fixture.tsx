import React from 'react';
import {createRoot} from 'react-dom/client';
import {AmbientSky} from '../../app/ui/src/Home';
import {BlenderAircraft,type AircraftVariant} from '../../app/ui/src/AmbientCelestial3D';
import {createAircraft} from '../../app/ui/src/AmbientEvents';
import '../../app/ui/src/style.css';
import '../../app/ui/src/ambient-home.css';

const root=createRoot(document.getElementById('root')!);
(window as any).showAircraft=(night:boolean,variant:AircraftVariant,facing:1|-1)=>{
 root.render(<div className="app" data-theme={night?'night':'ink'} style={{position:'relative',width:800,height:480,margin:0}}>
  <AmbientSky code={0} isDay={night?0:1} stale={false} aircraft={false} now={new Date(night?'2026-10-04T23:00:00Z':'2026-10-23T10:00:00Z')} latitude={44.4} longitude={26.1}/>
  <div className="ambient-flight" data-aircraft-variant={variant} style={{left:350,top:140,animation:'none',zIndex:4}}><BlenderAircraft night={night} variant={variant} facing={facing}/></div>
  <div style={{position:'absolute',top:15,left:0,right:0,textAlign:'center',fontSize:25,color:night?'#eff5f4':'#253c43'}}> {night?'02:00':'13:00'}</div>
 </div>);
};
(window as any).createAircraft=createAircraft;
(window as any).aircraftFixtureReady=true;
