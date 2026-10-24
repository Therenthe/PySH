import {useEffect,useRef,useState,type CSSProperties} from 'react';
import {useDialogFocus} from './useDialogFocus';
import {ScenePrecipitation} from './CityDiorama';
import type {SceneWeather} from './sceneWeather';
import './radio-city-entry.css';

export type RadioEntryScene={night:boolean;darkSurface:boolean;weather:SceneWeather;haze:number};
type Phase='loading'|'playing'|'leaving';

/** One bounded Blender shot; navigation never changes playback or preferences. */
export function RadioCityEntry({scene,language,onComplete,onCancel,onPhase}:{scene:RadioEntryScene;language:'en'|'ro';onComplete:()=>void;onCancel:()=>void;onPhase:(phase:Phase)=>void}){
 const video=useRef<HTMLVideoElement>(null),latest=useRef({onComplete,onCancel,onPhase});
 latest.current={onComplete,onCancel,onPhase};
 const settle=useRef<(destination:'radio'|'home')=>void>(()=>{});
 const dialog=useDialogFocus<HTMLDivElement>(()=>settle.current('home'));
 const [phase,setPhase]=useState<Phase>('loading');
 const src=`/ambient/radio-entry-${scene.night?'night':'day'}-v1.webm`;
 useEffect(()=>{
  const element=video.current;if(!element)return;
  let disposed=false,settled=false,loadTimer:number|undefined,playTimer:number|undefined,leaveTimer:number|undefined;
  const clear=()=>{clearTimeout(loadTimer);clearTimeout(playTimer);clearTimeout(leaveTimer);};
  const finish=(destination:'radio'|'home')=>{
   if(disposed||settled)return;settled=true;clear();element.pause();
   if(destination==='home')latest.current.onCancel();else latest.current.onComplete();
  };
  settle.current=finish;
  const playing=()=>{
   if(disposed||settled)return;clearTimeout(loadTimer);clearTimeout(playTimer);setPhase('playing');latest.current.onPhase('playing');
   // A stalled decoder must not leave the user trapped in the shot.
   playTimer=window.setTimeout(()=>finish('radio'),5500);
  };
  const ended=()=>{
   if(disposed||settled)return;clearTimeout(playTimer);setPhase('leaving');latest.current.onPhase('leaving');
   leaveTimer=window.setTimeout(()=>finish('radio'),160);
  };
  const failed=()=>finish('radio'),hidden=()=>{if(document.hidden)finish('home');};
  const reduced=window.matchMedia('(prefers-reduced-motion: reduce)'),motion=()=>{if(reduced.matches)finish('radio');};
  element.addEventListener('playing',playing);element.addEventListener('ended',ended);element.addEventListener('error',failed);
  document.addEventListener('visibilitychange',hidden);reduced.addEventListener('change',motion);
  if(reduced.matches)finish('radio');
  else if(document.hidden)finish('home');
  else{loadTimer=window.setTimeout(()=>finish('radio'),2500);void element.play().catch(()=>{if(!disposed)failed();});}
  return()=>{
   disposed=true;clear();element.removeEventListener('playing',playing);element.removeEventListener('ended',ended);element.removeEventListener('error',failed);
   document.removeEventListener('visibilitychange',hidden);reduced.removeEventListener('change',motion);element.pause();
   element.removeAttribute('src');element.load();settle.current=()=>{};
  };
 },[src]);
 const ro=language==='ro';
 return <div ref={dialog} className={`radio-city-entry ${scene.night?'sky-night':'sky-day'}`} role="dialog" aria-modal="true" aria-label={ro?'Intrare în Radio':'Entering Radio'} data-phase={phase} data-actual-night={scene.night} data-dark-surface={scene.darkSurface} style={{'--entry-haze':scene.haze} as CSSProperties} tabIndex={-1}>
  <video ref={video} src={src} muted playsInline preload="auto" disablePictureInPicture disableRemotePlayback aria-hidden="true"/>
  <div className="radio-entry-fog" aria-hidden="true"/>
  <ScenePrecipitation weather={scene.weather}/>
  <div className="radio-entry-actions"><button onClick={()=>settle.current('home')} data-dialog-initial>{ro?'Anulează':'Cancel'}</button><span role="status">{ro?'Intrare în Radio':'Entering Radio'}</span><button onClick={()=>settle.current('radio')}>{ro?'Omite animația':'Skip animation'}</button></div>
 </div>;
}
