import './weather-source.css';
export const WEATHER_DOCUMENTS={
 'open-meteo':'https://open-meteo.com/',
 'cc-by':'https://creativecommons.org/licenses/by/4.0/',
} as const;
export type WeatherDocument=keyof typeof WEATHER_DOCUMENTS;
/** Attribution is informational; weather settings never launch an external page. */
export function WeatherSource({language,licence=false}:{language:'en'|'ro';licence?:boolean;pending?:boolean;onOpen?:(id:WeatherDocument)=>void|Promise<unknown>}){
 return <span className="weather-source" aria-label={language==='ro'?'Sursa datelor meteo':'Weather data source'}>
  <span>Open-Meteo</span>
  {licence&&<span>CC BY 4.0</span>}
 </span>;
}
