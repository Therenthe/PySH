import { MarqueeText } from './MarqueeText';
import { useState, type ReactNode } from 'react';
import './radio.css';

export type RadioStation = {
  name: string; url?: string; url_resolved?: string; uuid?: string; stationuuid?: string;
  favicon?: string; country?: string; language?: string; codec?: string;
  [key: string]: unknown;
};

/** Transport flags include pending actions/audio availability; previous/next select stations. */
export type RadioProps = {
  language: 'en' | 'ro'; stations: RadioStation[]; favorites: RadioStation[];
  query: string; country: string; radioLanguage: string; favoritesOnly: boolean;
  loading: boolean; error?: string | null; busy: boolean;
  currentStation?: RadioStation | null; currentUrl?: string | null;
  stationName: string; trackTitle: string; playerState: string; playerKind?: string;
  pauses: boolean; canPlay: boolean; canStop: boolean; canPrevious: boolean; canNext: boolean; audioReady: boolean;
  volume: number; muted: boolean; visualizer?: ReactNode;
  t: (key: string) => string; icon: (name: string, size?: number) => ReactNode;
  isFavorite: (station: RadioStation) => boolean; isStationPausing: (station: RadioStation) => boolean;
  onSearch: () => void; onCountry: () => void; onLanguage: () => void;
  onFavoritesFilter: () => void; onRetry: () => void;
  onPlayStation: (station: RadioStation) => void; onFavorite: (station: RadioStation) => void;
  onPlayPause: () => void; onStop: () => void; onPrevious: () => void; onNext: () => void;
  onVolume: (value: number) => void; onMute: () => void;
};

/** Catalog artwork is optional. Never request insecure URLs or LAN/IP hosts. */
export function safeRadioLogo(value: unknown): string | null {
  if (typeof value !== 'string' || !value.trim()) return null;
  try {
    const url = new URL(value);
    const host = url.hostname.toLowerCase();
    if (url.protocol !== 'https:' || url.username || url.password || (url.port && url.port !== '443')) return null;
    if (!host.includes('.') || host.includes(':') || /^[\d.]+$/.test(host)) return null;
    if (!/^[a-z0-9.-]+$/.test(host) || /(?:^|\.)(?:localhost|local|internal|lan|home|test|invalid|example)$/.test(host)) return null;
    // IP literals encoded as decimal/octal/hex are normalized to numeric hosts by URL.
    return url.href;
  } catch { return null; }
}

function StationArtwork({ station, name, large = false }: { station?: RadioStation | null; name: string; large?: boolean }) {
  const source = safeRadioLogo(station?.favicon);
  const [failed, setFailed] = useState<string | null>(null);
  const initials = name.trim().split(/\s+/).slice(0, 2).map(word => Array.from(word)[0] || '').join('').toUpperCase();
  return <span className={`radio-artwork ${large ? 'radio-artwork-large' : ''}`} aria-hidden="true">
    {source && failed !== source
      ? <img src={source} alt="" referrerPolicy="no-referrer" loading={large ? 'eager' : 'lazy'} onError={() => setFailed(source)} />
      : <span className="radio-monogram">{initials || '♫'}</span>}
  </span>;
}

export function Radio(props: RadioProps) {
  const { language, stations, favorites, query, country, radioLanguage, favoritesOnly, loading, error, busy,
    currentStation, currentUrl, stationName, trackTitle, playerState, playerKind = 'radio', pauses, canPlay, canStop, canPrevious, canNext,
    audioReady, volume, muted, visualizer, t, icon, isFavorite, isStationPausing,
    onSearch, onCountry, onLanguage, onFavoritesFilter, onRetry, onPlayStation, onFavorite,
    onPlayPause, onStop, onPrevious, onNext, onVolume, onMute } = props;
  const ro = language === 'ro';
  const items = favoritesOnly ? favorites : stations;
  const isRadio = playerKind === 'radio';
  const title = (isRadio ? stationName : trackTitle) || t('nothingPlaying');
  const metadata = isRadio && trackTitle && trackTitle !== stationName ? trackTitle : '';
  const status = playerState === 'error' ? t('errorState') : t(playerState || 'idle');
  return <div className="radio-page radio-redesign">
    <div className="radio-columns">
      <section className="station-list" aria-label={t('stations')}>
        <div className="radio-toolbar">
          <button className="search-field" onClick={onSearch} disabled={busy} aria-label={t('searchStations')}>
            {icon('search', 20)}<span>{query || t('searchStations')}</span>
          </button>
          <div className="radio-filter-pills">
            <button className="filter-button" onClick={onCountry} disabled={busy}>{icon('globe', 16)}<span>{country || t('country')}</span></button>
            <button className="filter-button" onClick={onLanguage} disabled={busy}><span>{radioLanguage || t('language')}</span></button>
            <button className={`filter-button favorites-filter ${favoritesOnly ? 'active' : ''}`} onClick={onFavoritesFilter} aria-pressed={favoritesOnly}>
              <span aria-hidden="true">♥</span><span>{t('favorites')}</span><small>{favorites.length}</small>
            </button>
          </div>
        </div>
        <div className="list-head"><span>{favoritesOnly ? t('favorites') : t('stations')}</span><small>{items.length}</small>{!favoritesOnly && <button className="radio-refresh" aria-label={t('retry')} onClick={onRetry} disabled={busy || loading}>{icon('refresh', 18)}</button>}</div>
        <div className={`scroll-list ${favoritesOnly ? 'radio-favorites' : ''}`} aria-busy={!favoritesOnly && loading}>
          {!favoritesOnly && loading ? <div className="empty-state" role="status">{t('loading')}</div>
            : !favoritesOnly && error ? <div className="empty-state" role="status">{icon('radio', 28)}<b>{ro ? 'Posturile nu sunt disponibile' : 'Stations unavailable'}</b><span>{ro ? 'Verifică rețeaua și încearcă din nou.' : 'Check the network and try again.'}</span><button className="outline" onClick={onRetry} disabled={busy}>{t('retry')}</button></div>
            : items.length ? items.map((station, index) => {
              const selected = Boolean(isRadio && currentUrl && currentUrl === (station.url || station.url_resolved));
              const favorite = isFavorite(station);
              return <div className={`station-row ${selected ? 'selected' : ''}`} key={station.stationuuid || station.uuid || station.url || `${station.name}-${index}`}>
                <button className={`station-main ${favorite ? 'favorite-row' : ''}`} aria-label={`${t(isStationPausing(station) ? 'pause' : 'play')} · ${station.name}`} disabled={busy} onClick={() => onPlayStation(station)}>
                  <StationArtwork station={station} name={station.name} />
                  <span className="station-txt"><b>{station.name}</b><small>{[station.country, station.language, station.codec].filter(Boolean).join(' · ') || (ro ? 'Post de radio' : 'Radio station')}</small></span>
                  {selected && <span className="station-play" aria-hidden="true">{icon(isStationPausing(station) ? 'pause' : 'play', 17)}</span>}
                </button>
                <button className={`favorite-button ${favorite ? 'favorited' : ''}`} disabled={busy} onClick={() => onFavorite(station)} aria-label={`${favorite ? t('removeFavorite') : t('addFavorite')}: ${station.name}`} aria-pressed={favorite}><span aria-hidden="true">♥</span></button>
              </div>;
            }) : <div className={`empty-state ${favoritesOnly ? 'favorites-empty' : ''}`}>
              {icon('radio', 28)}<b>{favoritesOnly ? t('favoritesEmpty') : t('noStations')}</b>
              <span>{favoritesOnly ? (ro ? 'Atinge inima unui post pentru a-l păstra aici.' : 'Tap a station heart to save it here.') : t('searchHint')}</span>
              {!favoritesOnly && <button className="outline" onClick={onRetry} disabled={busy}>{t('retry')}</button>}
            </div>}
        </div>
      </section>
      <section className="radio-side" aria-label={t('nowPlaying')}>
        <div className="mini-player">
          <span className="eyebrow">{t('nowPlaying')}</span>
          <StationArtwork station={isRadio ? currentStation : null} name={isRadio ? stationName : ''} large />
          <b className="radio-station-name"><MarqueeText text={title} active={playerState==='playing'}/></b>
          {metadata && <span className="radio-track-name"><MarqueeText text={metadata} active={playerState==='playing'}/></span>}
          <small className={`state-text ${playerState}`} role="status">{status}</small>
          {visualizer && <div className="radio-visualizer">{visualizer}</div>}
          <div className="player-controls">
            <button aria-label={ro ? 'Postul anterior' : 'Previous station'} disabled={busy || !isRadio || !canPrevious} onClick={onPrevious}>{icon('back', 20)}</button>
            <button className="play-large" aria-label={pauses ? t('pause') : t('play')} disabled={busy || (!pauses && (!canPlay || !audioReady))} onClick={onPlayPause}>{icon(pauses ? 'pause' : 'play', 27)}</button>
            <button aria-label={ro ? 'Postul următor' : 'Next station'} disabled={busy || !isRadio || !canNext} onClick={onNext}>{icon('next', 20)}</button>
            <button aria-label={t('stop')} disabled={busy || !canStop} onClick={onStop}>{icon('stop', 17)}</button>
          </div>
          <div className="radio-volume">
            <button aria-label={muted ? t('unmute') : t('mute')} aria-pressed={muted} disabled={busy || !audioReady} onClick={onMute}>{icon('speaker', 19)}</button>
            <input type="range" min="0" max="100" value={Number.isFinite(volume) ? Math.max(0, Math.min(100, volume)) : 0} disabled={busy || !audioReady} aria-label={t('volume')} onChange={event => onVolume(Number(event.target.value))} />
            <small className="radio-volume-value">{Math.round(Number.isFinite(volume) ? Math.max(0, Math.min(100, volume)) : 0)}%</small>
          </div>
          {!audioReady && <small className="radio-output-warning">{ro ? 'Alege o ieșire audio pentru redare.' : 'Select an audio output to play.'}</small>}
        </div>
      </section>
    </div>
  </div>;
}
