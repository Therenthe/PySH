import { weatherCondition, weatherIsNight } from './weatherCondition';

type Props = { weather_code: unknown; isDay?: boolean | number | null; size?: number };

function Sun(){return <><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.4 1.4m11.2 11.2L19 19M5 19l1.4-1.4M17.6 6.4 19 5"/></>}
function Moon(){return <path d="M20.5 15A8.5 8.5 0 0 1 9 3.5 8.5 8.5 0 1 0 20.5 15Z"/>}
function Cloud(){return <path d="M6 14a4 4 0 1 1 .6-8 5.2 5.2 0 0 1 10.2 1.6A3.3 3.3 0 1 1 18 14Z"/>}
function Snowflake(){return <path d="M12 16v6m-2.6-4.5 5.2 3m-5.2 0 5.2-3"/>}

// The adjacent localized condition supplies the accessible text.
export function WeatherIcon({weather_code,isDay,size=24}:Props){
 const condition=weatherCondition(weather_code), night=weatherIsNight(isDay);
 const clear=<>{night?<Moon/>:<Sun/>}</>;
 return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false" data-weather-condition={condition}>
  {condition==='clear'&&clear}
  {condition==='mainly-clear'&&<><g transform="translate(-1 -1) scale(.85)">{clear}</g><path d="M14 20a2.7 2.7 0 1 1 .4-5.3 3 3 0 0 1 5.8.9A2.2 2.2 0 0 1 20 20Z"/></>}
  {condition==='partly-cloudy'&&<><g transform="translate(1 -1) scale(.65)">{clear}</g><g transform="translate(2 6) scale(.9)"><Cloud/></g></>}
  {condition==='overcast'&&<g transform="translate(0 3)"><Cloud/></g>}
  {condition==='fog'&&<><Cloud/><path d="M3 17h18M5 21h14"/></>}
  {(condition==='drizzle'||condition==='freezing-drizzle')&&<><Cloud/><path d="M7 18h.01M12 20h.01M17 18h.01" strokeWidth="3"/>{condition==='freezing-drizzle'&&<path d="M19 20v3m-1.3-2.2 2.6 1.5m-2.6 0 2.6-1.5"/>}</>}
  {(condition==='rain'||condition==='freezing-rain')&&<><Cloud/><path d="m7 17-1 4m6-4-1 4m6-4-1 4"/>{condition==='freezing-rain'&&<path d="M20 18v5m-2-3.8 4 2.6m-4 0 4-2.6"/>}</>}
  {condition==='snow'&&<><Cloud/><Snowflake/></>}
  {condition==='rain-showers'&&<><g transform="translate(1 -1) scale(.55)">{clear}</g><g transform="translate(2 3) scale(.9)"><Cloud/></g><path d="m7 18-1 3m6-3-1 3m6-3-1 3"/></>}
  {condition==='snow-showers'&&<><g transform="translate(1 -1) scale(.55)">{clear}</g><g transform="translate(2 3) scale(.9)"><Cloud/></g><Snowflake/></>}
  {(condition==='thunder'||condition==='thunder-hail')&&<><Cloud/><path d="m13 16-3 4h4l-2 3"/>{condition==='thunder-hail'&&<><circle cx="6" cy="19" r="1"/><circle cx="19" cy="21" r="1"/></>}</>}
  {condition==='missing'&&<><circle cx="12" cy="12" r="8"/><path d="M8 12h8"/></>}
  {condition==='unknown'&&<><circle cx="12" cy="12" r="8"/><path d="M9.5 9a2.5 2.5 0 1 1 4 2l-1.5 1.5v1M12 17h.01"/></>}
 </svg>;
}
