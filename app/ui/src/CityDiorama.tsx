import {useEffect,useState,type CSSProperties} from 'react';
import type {SceneWeather} from './sceneWeather';
import {currentWeatherAlerts,type WeatherAlertsDocument} from './weatherAlertModel';
import './city-diorama.css';

/** Original Blender-authored geometry, lit and rendered offline. Runtime uses two
 * flat image layers: no WebGL context or hidden 3D renderer competes with video. */
export function CityDiorama({night,weather,radioPlaying=false,bluetoothPowered=false,bluetoothConnected=false}:{night:boolean;weather:SceneWeather;radioPlaying?:boolean;bluetoothPowered?:boolean;bluetoothConnected?:boolean}) {
 const [active,setActive]=useState(!document.hidden);
 useEffect(()=>{const change=()=>setActive(!document.hidden);document.addEventListener('visibilitychange',change);return()=>document.removeEventListener('visibilitychange',change);},[]);
 return <div className="ambient-city city-diorama" data-city-version="blender-v1" data-season={weather.season} data-thermal={weather.heat?'heat':'normal'} data-radio-emitting={radioPlaying} data-bluetooth={bluetoothPowered?(bluetoothConnected?'connected':'on'):'off'} data-animate={active} data-freezing={weather.freezing}>
  {weather.heat&&<div className="city-heat-haze"/>}
  <img className="city-architecture" src={`/ambient/gothic-city-${night?'night':'day'}-v1.png`} alt="" draggable={false}/>
  <div className="city-metro-track"><img className="city-metro" src="/ambient/metro-v1.png" alt="" draggable={false}/></div>
  {radioPlaying&&<div className="city-radio-emitter"><i/><i/><i/><span/></div>}
  {bluetoothPowered&&<div className={`city-bluetooth ${bluetoothConnected?'connected':''}`}><svg viewBox="0 0 20 24"><path d="m4 6 12 12-6 5V1l6 5L4 18"/></svg><i/></div>}
  {weather.freezing&&<div className="city-frost"/>}
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
