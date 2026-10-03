import { MarqueeText } from './MarqueeText';
import type { ReactNode } from 'react';
import { WeatherIcon } from './WeatherIcon';
import {Moon} from './Moon';
import { weatherCondition, weatherIsNight } from './weatherCondition';
type Props = {
 time:string;date:string;language:'en'|'ro';timezone:string;greeting:string;
 weather:any;temperature:unknown;condition:string;location:string;stale:boolean;
 player:any;stationName:string;trackTitle:string;audioReady:boolean;canPlay:boolean;pauses:boolean;
 shortcuts:string[];t:(key:string)=>string;icon:(name:string,size?:number)=>ReactNode;
 onWeather:()=>void;onToggle:()=>void;onStop:()=>void;onNavigate:(page:'radio'|'media')=>void;visualizer?:ReactNode;
};
const degrees=(v:unknown)=>typeof v==='number'&&Number.isFinite(v)?`${Math.round(v)}°`:'—';
const measured=(v:unknown,u:string)=>typeof v==='number'&&Number.isFinite(v)?`${Math.round(v)} ${u}`:'—';
function AmbientSky({code,isDay,stale}:{code:unknown;isDay:unknown;stale:boolean}){
 const category=weatherCondition(stale?null:code),known=!['missing','unknown'].includes(category)&&[true,false,0,1].includes(isDay as boolean|number),night=known&&weatherIsNight(isDay as boolean|number|null);
 const clear=['clear','mainly-clear'].includes(category),rain=['rain','rain-showers','drizzle','freezing-rain','freezing-drizzle','thunder','thunder-hail'].includes(category),snow=['snow','snow-showers'].includes(category);
 return <div className={`ambient-sky ${known?(night?'sky-night':'sky-day'):'sky-neutral'} sky-${category}`} aria-hidden="true">
 {night&&clear&&<svg className="ambient-stars" viewBox="0 0 694 422" preserveAspectRatio="none"><g fill="currentColor">{Array.from({length:170},(_,i)=>[12+(i*137.507%670),8+((i*73.13+i*i*3.11)%360)]).map(([cx,cy],i)=><circle key={i} cx={cx} cy={cy} r={i%4===0?1.4:.8}/>)}</g></svg>}
 {known&&(clear||category==='partly-cloudy')&&(night?<Moon/>:<div className="ambient-orb ambient-sun"/>)}{night&&clear&&<i className="ambient-meteor"/>}{known&&!clear&&<div className="ambient-clouds"/>}{rain&&<div className="ambient-rain"/>}{snow&&<div className="ambient-snow"/>}
 <svg className="ambient-city" viewBox="0 0 694 120" preserveAspectRatio="none"><path d="M0 120V71h25V53h14V44h4v9h14v28h21V66h19V43h7v-8h3v8h8v23h13v24h25V46h15V30h28v-8h3v8h17v50h20V60h25V44h22v-9h3v9h16v33h18V91h26V67h22V55h5V28h3v27h19v23h23V60h26V39h18V26h3v13h18v50h19V69h26V52h12v-9h3v9h20v26h25V62h16V45h23V31h3v14h17v39h24V72h25V58h17v-7h3v7h18v62Z" fill="currentColor"/></svg>
 </div>;
}
export function Home({language,timezone,weather:w,temperature,condition,location,stale,player,stationName,trackTitle,audioReady,canPlay,pauses,shortcuts,t,icon,onWeather,onToggle,onStop,onNavigate,visualizer}:Props){
 const hasWeather=typeof temperature==='number'&&Number.isFinite(temperature),active=['playing','paused','buffering','connecting'].includes(player.state);
 const title=player.kind==='radio'?(player.url?stationName:''):player.title,metadata=player.kind==='radio'&&!!player.url&&trackTitle&&trackTitle!==stationName?trackTitle:'';
 const status=player.state==='error'?t('errorState'):t(player.state||'idle'),locale=language==='ro'?'ro-RO':'en-GB';
 const stamp=w.updated_at?new Date(w.updated_at).toLocaleTimeString(locale,{hour:'2-digit',minute:'2-digit',timeZone:timezone}):'';
 const labels=language==='ro'?{forecast:'Prognoză 5 zile',wind:'Vânt',humidity:'Umiditate',pressure:'Presiune',uv:'Indice UV'}:{forecast:'5-day forecast',wind:'Wind',humidity:'Humidity',pressure:'Pressure',uv:'UV index'};
 const days=Array.isArray(w.daily)?w.daily.slice(0,5):[];
 return <div className={`home-layout home-v2 ambient-home ${visualizer?'ambient-has-signal':''}`}>
 <AmbientSky code={w.current?.weather_code} isDay={w.current?.is_day} stale={stale}/>
 <section className="home-weather ambient-weather" aria-label={t('weather')}><header className="weather-top"><div className="weather-heading"><h2>{location||t('noLocation')}</h2><small className={stale?'stale-mark':'weather-updated'}>{stale?t('stale'):stamp?`${t('updated')} ${stamp}`:t('weather')}</small></div><button className="icon-button" aria-label={t('chooseCity')} onClick={onWeather}>{icon('globe',19)}</button></header>
 {hasWeather?<div className="ambient-weather-body"><div className="ambient-current"><div className="temp-row"><span className="temp">{degrees(temperature)}</span><WeatherIcon weather_code={w.current?.weather_code} isDay={w.current?.is_day} size={42}/></div><div className="ambient-condition">{condition||t('weather')}</div><div className="weather-details"><span>{t('feels')} {degrees(w.current?.feels_like_c)}</span><span>{t('min')} {degrees(days[0]?.min_c)} · {t('max')} {degrees(days[0]?.max_c)}</span></div></div><dl className="ambient-metrics"><div><dt>{labels.wind}</dt><dd>{measured(w.current?.wind_kmh,'km/h')}</dd></div><div><dt>{labels.humidity}</dt><dd>{measured(w.current?.humidity_pct,'%')}</dd></div><div><dt>{labels.pressure}</dt><dd>{measured(w.current?.pressure_hpa,'hPa')}</dd></div><div><dt>{labels.uv}</dt><dd>{measured(w.current?.uv_index,'')}</dd></div></dl></div>:<button className="weather-empty" onClick={onWeather}><WeatherIcon weather_code={null} size={32}/><span>{location?t('weatherUnavailable'):t('noWeather')}</span><small>{t('chooseCity')} →</small></button>}
 </section>
 <section className="ambient-forecast" aria-label={labels.forecast}><header><h2>{labels.forecast}</h2>{w.attribution&&<span className="weather-attribution">Open-Meteo</span>}</header><div className="forecast-line">{days.length?days.map((day:any)=><div className="forecast-day" key={day.date}><b>{new Date(`${day.date}T12:00:00`).toLocaleDateString(locale,{weekday:'short'})}</b><WeatherIcon weather_code={day.weather_code} isDay={true} size={24}/><span><strong>{degrees(day.max_c)}</strong><i>{degrees(day.min_c)}</i></span></div>):<div className="forecast-unavailable">{t('weatherUnavailable')}</div>}</div></section>
 {visualizer&&<div className="ambient-visualizer">{visualizer}</div>}
 <section className={`home-focus home-playback ambient-dock ${player.state||'idle'}`} aria-label={t('nowPlaying')}><div className="playback-copy"><div className="playback-caption"><span className="eyebrow">{t(player.kind==='radio'?'radio':active?'localMedia':'nowPlaying')}</span><span className={`player-state ${player.state||'idle'}`}><i aria-hidden="true"/>{status}</span></div><h1 className="playback-source"><MarqueeText text={title||t('nothingPlaying')} active={player.state==='playing'}/></h1>{metadata&&<p className="playback-metadata"><MarqueeText text={metadata} active={player.state==='playing'}/></p>}{!title&&<p className="playback-metadata">{audioReady?(language==='ro'?'Alege un post sau un fișier.':'Choose a station or a file.'):t('chooseOutput')}</p>}</div><div className="mini-controls"><button className="primary playback-toggle" aria-label={t(pauses?'pause':'play')} disabled={!pauses&&(!canPlay||!audioReady)} onClick={onToggle}>{icon(pauses?'pause':'play',25)}</button><button className="outline" aria-label={t('stop')} disabled={!player.url&&!active} onClick={onStop}>{icon('stop',20)}</button></div><nav className="ambient-shortcuts" aria-label={t('quickAccess')}>{(['radio','media'] as const).filter(page=>shortcuts.includes(page)).map(page=><button className="shortcut" key={page} onClick={()=>onNavigate(page)}>{icon(page,23)}<b>{t(page)}</b></button>)}</nav></section>
 </div>;
}
