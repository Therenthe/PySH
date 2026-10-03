type ThemePrefs={theme:'ink'|'night';nightEnabled:boolean;nightMode?:'solar'|'schedule';nightStart:string;nightEnd:string;timezone:string};
/** Solar intervals use provider UTC epochs, independent of the browser's time zone. */
export function effectiveTheme(now:Date,prefs:ThemePrefs,weather:any):'ink'|'night' {
 if(!prefs.nightEnabled)return prefs.theme;
 if((prefs.nightMode||'solar')==='solar'){
  const epoch=now.getTime()/1000;
  const date=new Intl.DateTimeFormat('en-CA',{timeZone:weather?.timezone||prefs.timezone,year:'numeric',month:'2-digit',day:'2-digit'}).format(now);
  const day=weather?.daily?.find((day:any)=>day.date===date);
  if(day&&Number.isFinite(day.sunrise_epoch)&&Number.isFinite(day.sunset_epoch)&&day.sunrise_epoch<day.sunset_epoch)
   return epoch<day.sunrise_epoch||epoch>=day.sunset_epoch?'night':'ink';
  // No location/current-day solar times: retain the chosen theme, never invent an apus.
  return prefs.theme;
 }
 const local=now.toLocaleTimeString('en-GB',{hour:'2-digit',minute:'2-digit',hour12:false,timeZone:prefs.timezone});
 const active=prefs.nightStart<=prefs.nightEnd?local>=prefs.nightStart&&local<prefs.nightEnd:local>=prefs.nightStart||local<prefs.nightEnd;
 return active?'night':'ink';
}
