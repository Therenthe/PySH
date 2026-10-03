import { useEffect, useId, useState } from 'react';
import './audio-visualizer.css';

export type VisualizerStyle = 'off' | 'wave' | 'bars' | 'orbit' | 'ribbon' | 'mirror' | 'rings';
type Signal = {available: boolean; status: string; waveform: number[]; bars: number[]; peak: number | null; rms: number | null; silent: boolean | null};
const empty: Signal = {available: false, status: 'starting', waveform: [], bars: [], peak: null, rms: null, silent: null};
export function validSignal(value: unknown): value is Signal {
  if (!value || typeof value !== 'object') return false;
  const data = value as Signal;
  if (typeof data.available !== 'boolean' || typeof data.status !== 'string') return false;
  if (!data.available) return true;
  return Array.isArray(data.waveform) && data.waveform.length === 64 && data.waveform.every(n => Number.isFinite(n) && n >= -1 && n <= 1)
    && Array.isArray(data.bars) && data.bars.length === 16 && data.bars.every(n => Number.isFinite(n) && n >= 0 && n <= 1)
    && typeof data.peak === 'number' && Number.isFinite(data.peak) && data.peak >= 0 && data.peak <= 1
    && typeof data.rms === 'number' && Number.isFinite(data.rms) && data.rms >= 0 && data.rms <= 1 && typeof data.silent === 'boolean';
}

export function useOutputSignal(enabled: boolean, reducedMotion = false): Signal {
  const [signal, setSignal] = useState<Signal>(empty);
  useEffect(() => {
    let disposed = false;
    let generation = 0;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let abort: AbortController | undefined;
    const stop = () => { generation++; clearTimeout(timer); abort?.abort(); setSignal(empty); };
    const poll = async () => {
      if (disposed || !enabled || document.hidden) return;
      const currentGeneration = generation;
      const controller = new AbortController();
      abort = controller;
      const timeout = setTimeout(() => controller.abort(), 900);
      try {
        const response = await fetch('/api/audio/visualization', {signal: controller.signal, cache: 'no-store'});
        const result: unknown = response.ok ? await response.json() : null;
        if (!disposed && currentGeneration === generation && !document.hidden) setSignal(validSignal(result) ? result : {...empty, status: 'unavailable'});
      } catch { if (!disposed && currentGeneration === generation && !document.hidden) setSignal({...empty, status: 'unavailable'}); }
      finally {
        clearTimeout(timeout);
        if (abort === controller) abort = undefined;
        if (!disposed && currentGeneration === generation && enabled && !document.hidden) timer = setTimeout(poll, reducedMotion ? 1000 : 100);
      }
    };
    const visibility = () => { stop(); if (!document.hidden && enabled) timer = setTimeout(poll, 100); };
    document.addEventListener('visibilitychange', visibility);
    if (enabled && !document.hidden) void poll(); else setSignal(empty);
    return () => { disposed = true; clearTimeout(timer); abort?.abort(); document.removeEventListener('visibilitychange', visibility); };
  }, [enabled, reducedMotion]);
  return enabled ? signal : {...empty, status: 'inactive'};
}

export function AudioVisualizer({style, canVisualize, language, reducedMotion = false}: {style: VisualizerStyle; canVisualize: boolean; language: 'en' | 'ro'; reducedMotion?: boolean}) {
  const [systemReducedMotion, setSystemReducedMotion] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  useEffect(() => {
    const query = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setSystemReducedMotion(query.matches);
    query.addEventListener('change', update);
    return () => query.removeEventListener('change', update);
  }, []);
  const quiet = reducedMotion || systemReducedMotion;
  const signal = useOutputSignal(style !== 'off' && canVisualize, quiet);
  const gradient = 'signal-' + useId().replace(/:/g, '');
  if (style === 'off') return null;
  const label = language === 'ro' ? 'Semnal audio de ieșire' : 'Output audio signal';
  const unavailable = language === 'ro' ? 'Semnal audio indisponibil' : 'Audio signal unavailable';
  const inactive = language === 'ro' ? 'Redarea este oprită' : 'Playback inactive';
  const silence = language === 'ro' ? 'Liniște în semnal' : 'Signal is silent';
  if (!signal.available || !canVisualize) return <div className="audio-visualizer signal-empty" data-signal-status={canVisualize ? signal.status : 'inactive'}>{canVisualize ? unavailable : inactive}</div>;
  if (quiet) return <div className="audio-visualizer signal-level" aria-label={label}>{signal.silent ? silence : `${language === 'ro' ? 'Nivel' : 'Level'} ${Math.round((signal.rms ?? 0) * 100)}%`}</div>;
  const wave = signal.waveform.map((value, index) => `${index ? 'L' : 'M'}${(index * 320 / 63).toFixed(1)},${(40 - value * 36).toFixed(1)}`).join(' ');
  // These are views of PCM amplitude, not frequency bins. No decorative motion:
  // every contour, spoke and ring is driven by the measured output signal.
  const envelope = signal.bars.map((value,index)=>({x:index*320/15, amplitude:value*35}));
  const ribbon = envelope.map(({x,amplitude},index)=>`${index?'L':'M'}${x.toFixed(1)},${(40-amplitude).toFixed(1)}`).join(' ')
    + ' ' + [...envelope].reverse().map(({x,amplitude})=>`L${x.toFixed(1)},${(40+amplitude).toFixed(1)}`).join(' ') + ' Z';
  const level = signal.rms ?? 0;
  return <div className="audio-visualizer" data-signal-status="ready" data-signal-style={style}>
    <svg viewBox="0 0 320 80" preserveAspectRatio="none" role="img" aria-label={signal.silent ? `${label}: ${silence}` : label}>
      <defs><linearGradient id={gradient} gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="320" y2="0"><stop stopColor="#a78bfa"/><stop offset=".5" stopColor="#34d399"/><stop offset="1" stopColor="#f59e0b"/></linearGradient></defs>
      {style === 'wave' && <path d={wave} fill="none" stroke={`url(#${gradient})`} strokeWidth="2" vectorEffect="non-scaling-stroke"/>}
      {style === 'bars' && signal.bars.map((value, index) => <rect key={index} x={index * 20 + 4} y={76 - Math.max(1,value * 72)} width="12" height={Math.max(1, value * 72)} rx="2" fill={`url(#${gradient})`}/>)}
      {style === 'orbit' && <g fill="none" stroke={`url(#${gradient})`} strokeWidth="2" strokeLinecap="round">
        <ellipse cx="160" cy="40" rx="94" ry="19" opacity=".25"/>
        {signal.bars.map((value,index)=>{const angle=index/16*Math.PI*2;return <line key={index}
          x1={160+Math.cos(angle)*94} y1={40+Math.sin(angle)*19}
          x2={160+Math.cos(angle)*(94+value*56)} y2={40+Math.sin(angle)*(19+value*18)} vectorEffect="non-scaling-stroke"/>;})}
      </g>}
      {style === 'ribbon' && <path d={ribbon} fill={`url(#${gradient})`} fillOpacity=".4" stroke={`url(#${gradient})`} strokeWidth="1.5" vectorEffect="non-scaling-stroke"/>}
      {style === 'mirror' && <g stroke={`url(#${gradient})`} strokeWidth="3" strokeLinecap="round">
        {signal.bars.map((value,index)=><line key={index} x1={160-value*150} x2={160+value*150} y1={4+index*4.8} y2={4+index*4.8} opacity={.5+value*.5} vectorEffect="non-scaling-stroke"/>)}
      </g>}
      {style === 'rings' && <g fill="none" stroke={`url(#${gradient})`} strokeWidth="2">
        {[0,1,2,3].map(index=><ellipse key={index} cx="160" cy="40" rx={30+index*29+level*12} ry={6+index*7+level*5} opacity={1-index*.18} vectorEffect="non-scaling-stroke"/>)}
      </g>}
    </svg>
  </div>;
}
