import {useEffect,useRef,useState,type CSSProperties} from 'react';
import type {SceneWeather} from './sceneWeather';
import {currentWeatherAlerts,type WeatherAlertsDocument} from './weatherAlertModel';
import './city-diorama.css';
import {RadioBuildingNeon} from './RadioBuildingNeon';
import {BluetoothRune} from './BluetoothRune';
import {cityWindowBankLevel,cityWetRoadLevel} from './cityAtmosphere';

/** Original Blender geometry rendered offline; small raster layers avoid a live
 * WebGL context competing with video and touch on the appliance. */
export function CityDiorama({night,darkSurface=false,weather,windowLighting={level:0,source:'unknown'},radioPlaying=false,visualizeRadio=false,radioCanVisualize=false,bluetoothPowered=false,bluetoothConnected=false,wifiState='unknown',wifiActive=false}:{night:boolean;darkSurface?:boolean;weather:SceneWeather;windowLighting?:{level:number;source:'solar'|'astronomy'|'unknown'};radioPlaying?:boolean;visualizeRadio?:boolean;radioCanVisualize?:boolean;bluetoothPowered?:boolean;bluetoothConnected?:boolean;wifiState?:'off'|'disconnected'|'connecting'|'connected'|'unknown';wifiActive?:boolean}) {
 const [active,setActive]=useState(!document.hidden);
 const [inView,setInView]=useState(true),city=useRef<HTMLDivElement>(null);
 useEffect(()=>{const change=()=>setActive(!document.hidden);document.addEventListener('visibilitychange',change);return()=>document.removeEventListener('visibilitychange',change);},[]);
 useEffect(()=>{
  if(!city.current||!('IntersectionObserver'in window))return;
  const observer=new IntersectionObserver(([entry])=>setInView(entry.isIntersecting));
  observer.observe(city.current);return()=>observer.disconnect();
 },[]);
 const palette=night||darkSurface?'night':'day';
 const emission=(service:'radio'|'bluetooth')=><><img className="city-signal-core" src={`/ambient/city-beacon-${service}-core-${palette}-v2.png`} alt="" draggable={false}/>{[1,2,3].map(ring=><img key={ring} className="city-signal-ring" data-ring={ring} style={{'--ring-order':ring-1} as CSSProperties} src={`/ambient/city-beacon-${service}-ring-${ring}-${palette}-v2.png`} alt="" draggable={false}/>)}</>;
 return <div ref={city} aria-hidden="true" className="ambient-city city-diorama" data-city-version="blender-v4" data-window-source={windowLighting.source} data-window-level={windowLighting.level.toFixed(4)} data-beacon-palette={palette} data-season={weather.season} data-thermal={weather.heat?'heat':'normal'} data-radio-emitting={radioPlaying} data-bluetooth={bluetoothPowered?(bluetoothConnected?'connected':'on'):'off'} data-wifi={wifiState} data-wifi-active={wifiState==='connected'&&wifiActive} data-animate={active&&inView} data-freezing={weather.freezing}>
  <div className="city-scenery">
   {weather.heat&&<div className="city-heat-haze"/>}
   <img className="city-architecture" src={`/ambient/gothic-city-${night?'night':'day'}-unlit-v1.png`} alt="" draggable={false}/>
   <img className="city-road-reflections" data-wet-level={cityWetRoadLevel(weather)} src={`/ambient/city-road-wet-${night?'night':'day'}-v1.png`} alt="" draggable={false} style={{opacity:cityWetRoadLevel(weather)}}/>
   {[0,1,2].map(bank=><img key={bank} className="city-window-bank" data-bank={bank} src={`/ambient/city-window-bank-${bank}-v1.png`} alt="" draggable={false} style={{opacity:cityWindowBankLevel(windowLighting.level,bank)}}/>)}
   <div className="city-metro-track"><img className="city-metro" src="/ambient/metro-v4.png" alt="" draggable={false}/></div>
   <img className="city-rail-front" src={`/ambient/gothic-city-rail-front-${night?'night':'day'}-v4.png`} alt="" draggable={false}/>
   <div className="city-ground-mist"/>
   {weather.freezing&&<div className="city-frost"/>}
  </div>
  {visualizeRadio&&<RadioBuildingNeon night={night} darkSurface={darkSurface} enabled={radioCanVisualize} active={active&&inView}/>}
  <div className="city-wifi" aria-hidden="true">
   <div className="city-wifi-emission">{[1,2,3].map(band=><img key={band} className="city-wifi-wave" data-band={band} style={{'--ring-order':band-1} as CSSProperties} src={`/ambient/city-wifi-wave-${band}-${palette}-motion-v1.png`} alt="" draggable={false}/>)}</div>
  </div>
  <div className="city-radio-tower">
   <img className="city-radio-hardware" src={`/ambient/city-beacon-radio-hardware-${palette}-v2.png`} alt="" draggable={false}/>
   {radioPlaying&&<div className="city-radio-emitter"><div className="city-radio-emission">{emission('radio')}</div></div>}
  </div>
  {bluetoothPowered&&<div className={`city-bluetooth ${bluetoothConnected?'connected':''}`}>
   <img className="city-bluetooth-hardware" src={`/ambient/city-bluetooth-support-${palette}-motion-v1.png`} alt="" draggable={false}/>
   <BluetoothRune key={`${palette}-${bluetoothConnected}`} palette={palette} connected={bluetoothConnected} active={active&&inView}/>
   <div className="city-bluetooth-emission">{[1,2,3].map(band=><img key={band} className="city-signal-ring" data-ring={band} style={{'--ring-order':band-1} as CSSProperties} src={`/ambient/city-beacon-bluetooth-ring-${band}-${palette}-v2.png`} alt="" draggable={false}/>)}</div>
  </div>}
 </div>;
}

/** An illustration of a validated warning, never a live view or WMO inference. */
export function SceneWarningIllustration({alerts,now,language='en'}:{alerts?:WeatherAlertsDocument;now:Date;language?:'en'|'ro'}){
 const eligible=currentWeatherAlerts(alerts,now).filter(alert=>['severe','extreme'].includes(alert.severity));
 const tornado=eligible.some(alert=>alert.hazard==='tornado'),flood=eligible.some(alert=>['flood','rain_flood'].includes(alert.hazard||''));
 if(!tornado&&!flood)return null;
 return <div className="scene-warning-illustration" data-warning-hazard={tornado?'tornado':'flood'}>
  {tornado&&<div className="warning-tornado">{[0,1,2].map(frame=><img key={frame} src={`/ambient/tornado-${frame}-v1.png`} alt="" draggable={false}/>)}</div>}
  {flood&&<div className="warning-flood"><img src="/ambient/flood-ripple-v1.png" alt="" draggable={false}/></div>}
  <span className="warning-scene-caption">{language==='ro'?'Ilustrație avertizare':'Warning illustration'} · {tornado?(language==='ro'?'tornadă':'tornado'):(language==='ro'?'inundații':'flood')}</span>
 </div>;
}

export function ScenePrecipitation({weather}:{weather:SceneWeather}){
 if(weather.precipitation==='none')return null;
 const snow=weather.precipitation==='snow';
 return <div className={`scene-precipitation ${snow?'ambient-snow':'ambient-rain'}`} data-intensity={weather.intensity} data-precipitation={weather.precipitation} style={{'--weather-wind':`${Math.min(80,weather.wind)}px`} as CSSProperties}>
  {Array.from({length:weather.count},(_,i)=>{
   const seed=(i*47+13)%101,depth=(i*17+7)%10/10,ice=weather.precipitation==='ice'&&i%4===0;
   const sprite=snow?'snowflake':ice?'ice':'raindrop';
   return <i key={i} className={`weather-particle particle-${sprite}`} style={{left:`${(i*61.803+11)%105-2}%`,'--particle-duration':`${snow?7+depth*6:ice?1.5+depth:1.05+depth*.75}s`,'--particle-delay':`${-(seed/101)*(snow?14:2.5)}s`,'--particle-opacity':.25+depth*.37,'--particle-lean':`${4+seed%12}deg`,'--particle-still-y':`${seed*5}px`,'--particle-width':`${snow?3+depth*5:ice?2+depth*2:1+depth*1.2}px`,'--particle-height':`${snow?3+depth*5:ice?3+depth*3:11+depth*13}px`,'--particle-drift':`${snow?(seed-50)*1.1:-18-depth*32}px`} as CSSProperties}/>;
  })}
 </div>;
}
