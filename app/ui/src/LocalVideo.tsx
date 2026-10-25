import {AudioVolume} from './AudioVolume';
import {LocalVideoSession,readVideoObservation} from './localMediaApi';
import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from 'react';

function TouchRange({label,min=0,max,value,disabled=false,step=1,onCommit}:{label:string;min?:number;max:number;value:number;disabled?:boolean;step?:number;onCommit:(value:number)=>void}){
 const [draft,setDraft]=useState<number|null>(null);
 const point=(e:React.PointerEvent<HTMLInputElement>)=>{const box=e.currentTarget.getBoundingClientRect();return Math.round((min+Math.max(0,Math.min(1,(e.clientX-box.left)/box.width))*(max-min))/step)*step;};
 return <input type="range" aria-label={label} min={min} max={max} step={step} value={draft??value} disabled={disabled} onChange={e=>onCommit(Number(e.target.value))} onPointerDown={e=>{e.preventDefault();e.currentTarget.setPointerCapture(e.pointerId);setDraft(point(e));}} onPointerMove={e=>{if(e.currentTarget.hasPointerCapture(e.pointerId))setDraft(point(e));}} onPointerUp={e=>{if(e.currentTarget.hasPointerCapture(e.pointerId)){e.currentTarget.releasePointerCapture(e.pointerId);const next=point(e);setDraft(null);onCommit(next);}}} onPointerCancel={()=>setDraft(null)}/>;
}
type Props = { item:{path:string;name:string}; session:LocalVideoSession; language:'en'|'ro'; t:(key:string)=>string; audio:{ready:boolean;volume:number;mute:boolean;output?:string;outputs?:{id:string;name?:string;description?:string;active?:boolean}[]}; audioPending?:boolean;audioFeedback?:ReactNode; onAudio:(change:{volume?:number;mute?:boolean})=>Promise<unknown>; closeError?:boolean;onReplay:()=>Promise<void>;onDiscard:(localOnly:boolean)=>Promise<boolean>;onClose:()=>Promise<boolean> };
const timestamp=(value:number)=>{const n=Math.max(0,Math.floor(value||0));return `${Math.floor(n/60)}:${String(n%60).padStart(2,'0')}`};

// Chromium decodes the real approved local file; every control remains app-owned and touch-sized.
export function LocalVideo({item,session,language,closeError=false,t,audio,audioPending=false,audioFeedback,onAudio,onReplay,onDiscard,onClose}:Props){
 const element=useRef<HTMLVideoElement>(null),initialPlay=useRef(false),completed=useRef(false),resumeReady=useRef(false),mounted=useRef(false);
 const [closing,setClosing]=useState(false),[saveFailed,setSaveFailed]=useState(false),[sessionExpired,setSessionExpired]=useState(false),[discardFailed,setDiscardFailed]=useState(false);
 const [audioInterrupted,setAudioInterrupted]=useState(false);
 const [state,setState]=useState({paused:true,position:0,duration:0,waiting:true,ended:false}),[failed,setFailed]=useState(false);
 const sync=()=>{const v=element.current;if(v)setState(s=>({...s,paused:v.paused,position:v.currentTime,duration:Number.isFinite(v.duration)?v.duration:0,ended:v.ended}));};
 const play=()=>{const v=element.current;if(!v||!audio.ready||!resumeReady.current||closing||session.unavailable)return;if(completed.current){void onReplay();return;}setAudioInterrupted(false);v.play().catch(()=>{if(mounted.current)setFailed(true);});};
 const retry=()=>{setFailed(false);setState(s=>({...s,waiting:true}));initialPlay.current=false;resumeReady.current=false;element.current?.load();};
 const persist=(heartbeat=false)=>{void session.update(heartbeat).then(()=>{if(mounted.current)setSaveFailed(false);},()=>{if(mounted.current)setSaveFailed(true);});};
 useLayoutEffect(()=>{
  mounted.current=true;const video=element.current!;
  const unbind=session.bind(()=>readVideoObservation(video),()=>video.pause());
  const leave=()=>{setSessionExpired(true);void session.close(true).catch(()=>{});};
  window.addEventListener('pagehide',leave);
  const timer=window.setInterval(()=>persist(video.paused||video.ended),10000);
  return()=>{mounted.current=false;clearInterval(timer);window.removeEventListener('pagehide',leave);void session.close(true).catch(()=>{});unbind();};
 },[session]);
 useEffect(()=>{if(!audio.ready){element.current?.pause();setAudioInterrupted(true);sync();}},[audio.ready]);
 const ready=()=>{setFailed(false);setState(s=>({...s,waiting:false}));sync();if(resumeReady.current&&!initialPlay.current){initialPlay.current=true;if(audio.ready&&!audioInterrupted)play();}};
 const metadata=()=>{const video=element.current;if(!video||!Number.isFinite(video.duration)||video.duration<=0)return;if(resumeReady.current){sync();return;}const target=Math.min(session.session.resume_position_s,Math.max(0,video.duration-.1));if(target>0&&Math.abs(video.currentTime-target)>.1){video.currentTime=target;}else{resumeReady.current=true;}sync();};
 const seeked=()=>{resumeReady.current=true;ready();persist();};
 const updateAudio=(change:{volume?:number;mute?:boolean})=>closing||session.unavailable?Promise.resolve():onAudio(change);
 const close=async()=>{if(closing)return;setClosing(true);setSaveFailed(false);try{if(!await onClose())setSaveFailed(true);}catch{setSaveFailed(true);}finally{if(mounted.current)setClosing(false);}};
 const discard=async(localOnly=false)=>{if(closing)return;setClosing(true);setDiscardFailed(false);try{if(!await onDiscard(localOnly))setDiscardFailed(true);}catch{setDiscardFailed(true);}finally{if(mounted.current)setClosing(false);}};
 const output=audio.outputs?.find(item=>item.id===audio.output||item.active); 
 return <section className="video-overlay" aria-label={t('videos')}>
  <header className="video-header"><button className="video-back outline" disabled={closing} onClick={()=>void close()}>{language==='ro'?'Înapoi la Media':'Back to Media'}</button><div className="video-title" title={item.name}>{item.name}</div></header>
  <div className="video-stage"><video ref={element} src={session.session.stream_url} disableRemotePlayback disablePictureInPicture playsInline aria-label={item.name} onLoadedMetadata={metadata} onDurationChange={metadata} onSeeked={seeked} onTimeUpdate={sync} onPlay={()=>{if(!audio.ready){element.current?.pause();setAudioInterrupted(true);}sync();}} onPause={()=>{sync();persist();}} onEnded={()=>{completed.current=true;sync();persist();}} onWaiting={()=>setState(s=>({...s,waiting:true}))} onPlaying={()=>{setFailed(false);setState(s=>({...s,waiting:false}));sync();}} onCanPlay={ready} onError={()=>setFailed(true)}/>
   {(failed||sessionExpired)&&<div className="video-error" role="alert"><h2>{sessionExpired?(language==='ro'?'Sesiunea video s-a închis.':'Video session closed.'):t('videoPlaybackFailed')}</h2><p>{sessionExpired?(language==='ro'?'Revino la Media pentru a redeschide fișierul.':'Return to Media to reopen this file.'):t('videoRecoveryHint')}</p>{!sessionExpired&&<button className="outline" disabled={session.unavailable} onClick={retry}>{t('retry')}</button>}</div>}
  </div>
  <div className="video-controls">
   <div className="video-transport"><button className="outline video-play" disabled={failed||!audio.ready||closing||session.unavailable} onClick={()=>state.paused?play():element.current?.pause()}>{t(state.paused?'play':'pause')}</button><label className="video-progress"><span>{t('progress')} · {timestamp(state.position)} / {state.duration?timestamp(state.duration):t('unknown')}</span><TouchRange label={t('progress')} max={state.duration||1} step={0.1} value={Math.min(state.position,state.duration||1)} disabled={failed||!state.duration||closing||session.unavailable} onCommit={value=>{if(!session.unavailable&&element.current)element.current.currentTime=value;sync();}}/></label><span className="video-state" role="status">{!audio.ready?t('audioLostVideo'):audioInterrupted?t('audioRestoredVideo'):t(failed?'errorState':state.ended?'ended':state.waiting?'loading':state.paused?'paused':'playing')}</span></div>
   <div className="video-audio"><button className="outline" disabled={!audio.ready||audioPending||closing||session.unavailable} onClick={()=>updateAudio({mute:!audio.mute})}>{t(audio.mute?'unmute':'mute')}</button><label className="video-volume"><span>{t('volume')} · {Math.round(audio.volume||0)}%</span><AudioVolume label={t('volume')} value={audio.volume||0} disabled={!audio.ready||audioPending||closing||session.unavailable} onChange={volume=>updateAudio({volume})}/></label>{!audio.ready?<span className="video-audio-warning" role="status">{t('noOutput')}</span>:<span className="video-output">{audioPending?t('updating'):(output?.description||output?.name||t('audioOutput'))}</span>}</div>
   {(saveFailed||closeError)&&<div className="video-progress-error" role="alert"><span>{discardFailed?(language==='ro'?'Hubul nu a confirmat închiderea. Ieși fără salvare? Sesiunea se va închide automat.':'The hub did not confirm cleanup. Leave without saving? The session will expire automatically.'):(language==='ro'?'Progresul nu a putut fi salvat.':'Progress could not be saved.')}</span><div className="video-progress-recovery-actions">{discardFailed?<><button className="outline" disabled={closing} onClick={()=>setDiscardFailed(false)}>{language==='ro'?'Rămâi aici':'Stay here'}</button><button className="outline video-leave-confirm" disabled={closing} onClick={()=>void discard(true)}>{language==='ro'?'Ieși oricum':'Leave anyway'}</button></>:<><button className="outline" disabled={closing} onClick={()=>void close()}>{language==='ro'?'Salvează și închide':'Save and close'}</button><button className="outline video-leave-unsaved" disabled={closing} onClick={()=>void discard()}>{language==='ro'?'Înapoi fără salvare':'Leave without saving'}</button></>}</div></div>}
   {audioFeedback&&<div className="video-audio-recovery">{audioFeedback}</div>}
  </div>
 </section>;
}
