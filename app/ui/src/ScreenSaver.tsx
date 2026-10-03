import { MarqueeText } from './MarqueeText';
import type { MouseEvent, ReactNode } from 'react';
import './screensaver.css';

export type ScreenSaverPlayer = {
  station_name?: string;
  title?: string;
  metadata?: string;
  artist?: string;
  kind?: string;
  state?: string;
};

export type ScreenSaverProps = {
  visualizer?: ReactNode;
  time: string;
  date: string;
  language: 'en' | 'ro';
  theme: 'ink' | 'night';
  player: ScreenSaverPlayer;
  canPlay: boolean;
  canPrevious: boolean;
  canNext: boolean;
  onPlayPause: () => void | Promise<unknown>;
  onPrevious: () => void | Promise<unknown>;
  onNext: () => void | Promise<unknown>;
  onWake: () => void;
};

const labels = {
  en: {
    screen: 'Clock and playback', home: 'Back to hub', hint: 'Touch the background to return to the hub',
    radio: 'Radio', audio: 'Local audio', nothing: 'Nothing playing', play: 'Play', pause: 'Pause',
    previousStation: 'Previous station', nextStation: 'Next station', previousTrack: 'Previous track', nextTrack: 'Next track',
    playing: 'Playing', paused: 'Paused', buffering: 'Buffering…', connecting: 'Connecting…', ended: 'Ended',
    error: 'Playback unavailable', idle: 'Stopped', unknown: 'Playback status unavailable',
  },
  ro: {
    screen: 'Ceas și redare', home: 'Revino în hub', hint: 'Atinge fundalul pentru a reveni în hub',
    radio: 'Radio', audio: 'Audio local', nothing: 'Nimic în redare', play: 'Redă', pause: 'Pauză',
    previousStation: 'Postul anterior', nextStation: 'Postul următor', previousTrack: 'Piesa anterioară', nextTrack: 'Piesa următoare',
    playing: 'În redare', paused: 'În pauză', buffering: 'Se încarcă…', connecting: 'Se conectează…', ended: 'Încheiat',
    error: 'Redare indisponibilă', idle: 'Oprit', unknown: 'Starea redării este indisponibilă',
  },
};

function TransportIcon({ action }: { action: 'previous' | 'next' | 'play' | 'pause' }) {
  return <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    {action === 'play' ? <path d="m8 5 11 7-11 7z" /> : action === 'pause' ? <><path d="M8 5v14M16 5v14" /></> : action === 'previous' ? <><path d="M5 5v14m13-14L8 12l10 7z" /></> : <><path d="M19 5v14M6 5l10 7-10 7z" /></>}
  </svg>;
}

/** Transport callbacks own backend operations. Capability flags must include pending/audio state. */
export function ScreenSaver({ visualizer, time, date, language, theme, player, canPlay, canPrevious, canNext, onPlayPause, onPrevious, onNext, onWake }: ScreenSaverProps) {
  const t = labels[language], radio = player.kind === 'radio';
  const active = ['playing', 'buffering', 'connecting'].includes(player.state || '');
  const title = (radio ? player.station_name : '') || player.title || player.station_name || '';
  const detail = [player.artist, player.metadata || (radio ? player.title : '')]
    .filter((value): value is string => Boolean(value?.trim()) && value!.trim() !== title.trim())
    .filter((value, index, values) => values.indexOf(value) === index).join(' · ');
  const state = player.state || 'idle';
  const status = state in t ? t[state as keyof typeof t] : t.unknown;
  const invoke = (event: MouseEvent<HTMLButtonElement>, action: () => void | Promise<unknown>) => {
    event.stopPropagation();
    void action();
  };
  return <section className={`pysh-screensaver ${visualizer ? 'saver-with-signal' : ''}`} data-theme={theme} role="region" aria-label={t.screen}
    onPointerDown={event => event.stopPropagation()}
    onClick={event => { event.stopPropagation(); onWake(); }}>
    <header className="saver-header"><span className="saver-brand">PI SMART HUB</span>
      <button className="saver-home" onClick={event => invoke(event, onWake)}>{t.home}<span aria-hidden="true">↗</span></button>
    </header>
    <div className="saver-clock"><time>{time}</time><p>{date}</p></div>
    <section className={`saver-playback ${title ? '' : 'saver-empty'}`} aria-label={radio ? t.radio : t.audio}>
      <div className="saver-source">{title ? (radio ? t.radio : t.audio) : t.nothing}</div>
      {title && <><h1 title={title}><MarqueeText text={title} active={player.state==='playing'}/></h1><p className="saver-metadata" title={detail}><MarqueeText text={detail || '\u00a0'} active={player.state==='playing'}/></p></>}
      {visualizer&&<div className="saver-visualizer">{visualizer}</div>}
      <div className="saver-transport" onClick={event => event.stopPropagation()}>
        <button disabled={!canPrevious} aria-label={radio ? t.previousStation : t.previousTrack} onClick={event => invoke(event, onPrevious)}><TransportIcon action="previous" /><span>{radio ? t.previousStation : t.previousTrack}</span></button>
        <button className="saver-primary" disabled={!canPlay} aria-label={active ? t.pause : t.play} onClick={event => invoke(event, onPlayPause)}><TransportIcon action={active ? 'pause' : 'play'} /><span>{active ? t.pause : t.play}</span></button>
        <button disabled={!canNext} aria-label={radio ? t.nextStation : t.nextTrack} onClick={event => invoke(event, onNext)}><TransportIcon action="next" /><span>{radio ? t.nextStation : t.nextTrack}</span></button>
      </div>
      <p className="saver-status" role="status" aria-live="polite">{title ? status : '\u00a0'}</p>
    </section>
    <footer className="saver-hint">{t.hint}</footer>
  </section>;
}
