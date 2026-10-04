import { useEffect, useRef, useState, type ReactNode } from 'react';

function TouchRange({label,min=0,max,value,disabled=false,step=1,onCommit}:{label:string;min?:number;max:number;value:number;disabled?:boolean;step?:number;onCommit:(value:number)=>void}){
 const [draft,setDraft]=useState<number|null>(null);
 const point=(e:React.PointerEvent<HTMLInputElement>)=>{const box=e.currentTarget.getBoundingClientRect();return Math.round((min+Math.max(0,Math.min(1,(e.clientX-box.left)/box.width))*(max-min))/step)*step;};
 return <input type="range" aria-label={label} min={min} max={max} step={step} value={draft??value} disabled={disabled} onChange={e=>onCommit(Number(e.target.value))} onPointerDown={e=>{e.preventDefault();e.currentTarget.setPointerCapture(e.pointerId);setDraft(point(e));}} onPointerMove={e=>{if(e.currentTarget.hasPointerCapture(e.pointerId))setDraft(point(e));}} onPointerUp={e=>{if(e.currentTarget.hasPointerCapture(e.pointerId)){e.currentTarget.releasePointerCapture(e.pointerId);const next=point(e);setDraft(null);onCommit(next);}}} onPointerCancel={()=>setDraft(null)}/>;
}
type Props = { item:{path:string;name:string}; t:(key:string)=>string; audio:{ready:boolean;volume:number;mute:boolean;output?:string;outputs?:{id:string;name?:string;description?:string;active?:boolean}[]}; audioPending?:boolean;audioFeedback?:ReactNode; onAudio:(change:{volume?:number;mute?:boolean})=>Promise<unknown>; onClose:()=>void };
const timestamp=(value:number)=>{const n=Math.max(0,Math.floor(value||0));return `${Math.floor(n/60)}:${String(n%60).padStart(2,'0')}`};

// Chromium decodes the real approved local file; every control remains app-owned and touch-sized.
export function LocalVideo({item,t,audio,audioPending=false,audioFeedback,onAudio,onClose}:Props){
 const element=useRef<HTMLVideoElement>(null),initialPlay=useRef(false);
 const [audioInterrupted,setAudioInterrupted]=useState(false);
 const [state,setState]=useState({paused:true,position:0,duration:0,waiting:true,ended:false}),[failed,setFailed]=useState(false);
 const sync=()=>{const v=element.current;if(v)setState(s=>({...s,paused:v.paused,position:v.currentTime,duration:Number.isFinite(v.duration)?v.duration:0,ended:v.ended}));};
 const play=()=>{const v=element.current;if(!v||!audio.ready)return;setAudioInterrupted(false);v.play().catch(()=>setFailed(true));};
 const retry=()=>{setFailed(false);setState(s=>({...s,waiting:true}));element.current?.load();play();};
 useEffect(()=>{if(!audio.ready){element.current?.pause();setAudioInterrupted(true);sync();}},[audio.ready]);
 const ready=()=>{setFailed(false);setState(s=>({...s,waiting:false}));sync();if(!initialPlay.current){initialPlay.current=true;if(audio.ready&&!audioInterrupted)play();}};
 const updateAudio=(change:{volume?:number;mute?:boolean})=>onAudio(change);
 const close=()=>{element.current?.pause();onClose();};
 const output=audio.outputs?.find(item=>item.id===audio.output||item.active); 
 return <section className="video-overlay" aria-label={t('videos')}>
  <header className="video-header"><button className="video-back outline" onClick={close}>{t('backToHub')}</button><div className="video-title" title={item.name}>{item.name}</div></header>
  <div className="video-stage"><video ref={element} src={`/api/media/file?path=${encodeURIComponent(item.path)}`} disableRemotePlayback disablePictureInPicture playsInline aria-label={item.name} onLoadedMetadata={sync} onTimeUpdate={sync} onPlay={()=>{if(!audio.ready){element.current?.pause();setAudioInterrupted(true);}sync();}} onPause={sync} onEnded={sync} onWaiting={()=>setState(s=>({...s,waiting:true}))} onPlaying={()=>{setFailed(false);setState(s=>({...s,waiting:false}));sync();}} onCanPlay={ready} onError={()=>setFailed(true)}/>
   {failed&&<div className="video-error" role="alert"><h2>{t('videoPlaybackFailed')}</h2><p>{t('videoRecoveryHint')}</p><button className="outline" onClick={retry}>{t('retry')}</button></div>}
  </div>
  <div className="video-controls">
   <div className="video-transport"><button className="outline video-play" disabled={failed||!audio.ready} onClick={()=>state.paused?play():element.current?.pause()}>{t(state.paused?'play':'pause')}</button><label className="video-progress"><span>{t('progress')} · {timestamp(state.position)} / {state.duration?timestamp(state.duration):t('unknown')}</span><TouchRange label={t('progress')} max={state.duration||1} step={0.1} value={Math.min(state.position,state.duration||1)} disabled={failed||!state.duration} onCommit={value=>{if(element.current)element.current.currentTime=value;sync();}}/></label><span className="video-state" role="status">{!audio.ready?t('audioLostVideo'):audioInterrupted?t('audioRestoredVideo'):t(failed?'errorState':state.ended?'ended':state.waiting?'loading':state.paused?'paused':'playing')}</span></div>
   <div className="video-audio"><button className="outline" disabled={!audio.ready||audioPending} onClick={()=>updateAudio({mute:!audio.mute})}>{t(audio.mute?'unmute':'mute')}</button><label className="video-volume"><span>{t('volume')} · {Math.round(audio.volume||0)}%</span><TouchRange label={t('volume')} max={100} value={audio.volume||0} disabled={!audio.ready||audioPending} onCommit={volume=>updateAudio({volume})}/></label>{!audio.ready?<span className="video-audio-warning" role="status">{t('noOutput')}</span>:<span className="video-output">{audioPending?t('updating'):(output?.description||output?.name||t('audioOutput'))}</span>}</div>
   {audioFeedback&&<div className="video-audio-recovery">{audioFeedback}</div>}
  </div>
 </section>;
}
