import type {MouseEvent} from 'react';
import './weather-source.css';
export const WEATHER_DOCUMENTS={
 'open-meteo':'https://open-meteo.com/',
 'cc-by':'https://creativecommons.org/licenses/by/4.0/',
} as const;
export type WeatherDocument=keyof typeof WEATHER_DOCUMENTS;
/** Actual link semantics. The fixed-ID broker opens this exact destination in an owned docs window. */
export function WeatherSource({language,licence=false,pending=false,onOpen}:{language:'en'|'ro';licence?:boolean;pending?:boolean;onOpen:(id:WeatherDocument)=>void|Promise<unknown>}){
 const open=(event:MouseEvent<HTMLAnchorElement>,id:WeatherDocument)=>{event.preventDefault();event.stopPropagation();if(!pending)void onOpen(id);};
 return <span className="weather-source" aria-label={language==='ro'?'Sursa datelor meteo':'Weather data source'}>
  <a href={WEATHER_DOCUMENTS['open-meteo']} target="_blank" rel="noopener noreferrer" aria-label={language==='ro'?'Date meteo: Open-Meteo':'Weather data: Open-Meteo'} aria-disabled={pending||undefined} aria-busy={pending||undefined} tabIndex={pending?-1:0} onPointerDown={event=>event.stopPropagation()} onKeyDown={event=>event.stopPropagation()} onClick={event=>open(event,'open-meteo')}>Open-Meteo</a>
  {licence&&<a href={WEATHER_DOCUMENTS['cc-by']} target="_blank" rel="noopener noreferrer" aria-label={language==='ro'?'Licența datelor: CC BY 4.0':'Data licence: CC BY 4.0'} aria-disabled={pending||undefined} tabIndex={pending?-1:0} onPointerDown={event=>event.stopPropagation()} onKeyDown={event=>event.stopPropagation()} onClick={event=>open(event,'cc-by')}>CC BY 4.0</a>}
 </span>;
}
