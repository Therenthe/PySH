import { useEffect, useId, useState } from 'react';
import './audio-visualizer.css';

export type VisualizerStyle = 'off' | 'wave' | 'bars' | 'orbit';
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
  const orbit = signal.bars.map((value, index) => {const angle = index / 16 * Math.PI * 2; const radius = 18 + value * 20; return `${index ? 'L' : 'M'}${(160 + Math.cos(angle) * radius).toFixed(1)},${(40 + Math.sin(angle) * radius).toFixed(1)}`;}).join(' ') + ' Z';
  return <div className="audio-visualizer" data-signal-status="ready" data-signal-style={style}>
    <svg viewBox="0 0 320 80" role="img" aria-label={signal.silent ? `${label}: ${silence}` : label}>
      <defs><linearGradient id={gradient}><stop stopColor="#a78bfa"/><stop offset=".5" stopColor="#34d399"/><stop offset="1" stopColor="#f59e0b"/></linearGradient></defs>
      {style === 'wave' && <path d={wave} fill="none" stroke={`url(#${gradient})`} strokeWidth="2"/>}
      {style === 'bars' && signal.bars.map((value, index) => <rect key={index} x={index * 20 + 4} y={40 - value * 38} width="12" height={Math.max(1, value * 76)} rx="2" fill={`url(#${gradient})`}/>)}
      {style === 'orbit' && <path d={orbit} fill="none" stroke={`url(#${gradient})`} strokeWidth="2"/>}
    </svg>
  </div>;
}
