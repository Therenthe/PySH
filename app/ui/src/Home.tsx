import type { ReactNode } from 'react';
import { WeatherIcon } from './WeatherIcon';

type Props = {
 time:string; date:string; language:'en'|'ro'; timezone:string; greeting:string;
 weather:any; temperature:unknown; condition:string; location:string; stale:boolean;
 player:any; stationName:string; trackTitle:string; audioReady:boolean; canPlay:boolean; pauses:boolean;
 shortcuts:string[]; t:(key:string)=>string; icon:(name:string,size?:number)=>ReactNode;
 onWeather:()=>void; onToggle:()=>void; onStop:()=>void; onNavigate:(page:'radio'|'media')=>void;
};
const degrees=(value:unknown)=>typeof value==='number'&&Number.isFinite(value)?`${Math.round(value)}°`:'—';

export function Home({time,date,language,timezone,greeting,weather:w,temperature,condition,location,stale,player,stationName,trackTitle,audioReady,canPlay,pauses,shortcuts,t,icon,onWeather,onToggle,onStop,onNavigate}:Props){
 const hasWeather=typeof temperature==='number'&&Number.isFinite(temperature);
 const active=['playing','paused','buffering','connecting'].includes(player.state);
 const title=player.kind==='radio'?stationName:player.title;
 const metadata=player.kind==='radio'&&trackTitle&&trackTitle!==stationName?trackTitle:'';
 const status=player.state==='error'?t('errorState'):t(player.state||'idle');
 const stamp=w.updated_at?new Date(w.updated_at).toLocaleTimeString(language==='ro'?'ro-RO':'en-GB',{hour:'2-digit',minute:'2-digit',timeZone:timezone}):'';
 return <div className="home-layout home-v2">
  <section className="home-clock-card" aria-label={t('today')}>
   <span className="clock-greeting">{greeting}</span>
   <div className="focus-clock">{time}</div>
   <div className="clock-date">{date}</div>
  </section>
  <section className="home-weather" aria-label={t('weather')}>
   <header className="weather-top">
    <div className="weather-heading"><h2>{location||t('noLocation')}</h2><small className={stale?'stale-mark':'weather-updated'}>{stale?t('stale'):stamp?`${t('updated')} ${stamp}`:t('weather')}</small></div>
    <button className="icon-button" aria-label={t('refreshWeather')} onClick={onWeather}>{icon('refresh',19)}</button>
   </header>
   {hasWeather?<>
    <div className="temp-row"><span className="temp">{degrees(temperature)}</span><div className="weather-symbol"><WeatherIcon weather_code={w.current?.weather_code} isDay={w.current?.is_day} size={32}/><span>{condition||t('weather')}</span></div></div>
    <div className="weather-details"><span>{t('feels')} {degrees(w.current?.feels_like_c??temperature)}</span><span>{t('max')} {degrees(w.daily?.[0]?.max_c)} · {t('min')} {degrees(w.daily?.[0]?.min_c)}</span></div>
    {w.daily?.length>1&&<div className="forecast-line">{w.daily.slice(1,5).map((day:any)=><span key={day.date}><b>{new Date(`${day.date}T12:00:00`).toLocaleDateString(language==='ro'?'ro-RO':'en-GB',{weekday:'short'})}</b><i>{degrees(day.max_c)}</i></span>)}</div>}
   </>:<button className="weather-empty" onClick={onWeather}><WeatherIcon weather_code={null} size={30}/><span>{location?t('weatherUnavailable'):t('noWeather')}</span><small>{location?t('retry'):t('chooseCity')} →</small></button>}
   {w.attribution&&<span className="weather-attribution">Open-Meteo</span>}
  </section>
  <section className={`home-focus home-playback ${player.state||'idle'}`} aria-label={t('nowPlaying')}>
   <div className="playback-copy">
    <div className="playback-caption"><span className="eyebrow">{t(player.kind==='radio'?'radio':active?'localMedia':'nowPlaying')}</span><span className={`player-state ${player.state||'idle'}`}><i aria-hidden="true"/>{status}</span></div>
    <h1 className="playback-source">{title||t('nothingPlaying')}</h1>
    {metadata&&<p className="playback-metadata">{metadata}</p>}
    {!title&&<p className="playback-metadata">{audioReady?(language==='ro'?'Alege un post radio sau un fișier.':'Choose a station or a local file.'):t('chooseOutput')}</p>}
   </div>
   <div className="focus-footer"><div className="mini-controls">
    <button className="primary playback-toggle" aria-label={t(pauses?'pause':'play')} disabled={!pauses&&(!canPlay||!audioReady)} onClick={onToggle}>{icon(pauses?'pause':'play',22)}</button>
    <button className="outline" aria-label={t('stop')} disabled={!player.url&&!active} onClick={onStop}>{icon('stop',20)}</button>
   </div></div>
  </section>
  <section className="home-shortcuts" aria-label={t('quickAccess')}>
   <div className="shortcut-row">{(['radio','media'] as const).filter(page=>shortcuts.includes(page)).map(page=><button className="shortcut" key={page} onClick={()=>onNavigate(page)}>{icon(page,22)}<b>{t(page)}</b>{icon('next',18)}</button>)}{!shortcuts.length&&<p>{t('noShortcuts')}</p>}</div>
  </section>
 </div>;
}
