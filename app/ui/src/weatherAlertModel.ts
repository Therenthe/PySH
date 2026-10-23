export type WeatherAlert={id:string;event:string;headline:string;description?:string;severity:'minor'|'moderate'|'severe'|'extreme';onset:string;expires:string;provider:string;source:string;hazard?:'flood'|'rain_flood'|'wind'|'thunderstorm'|'snow'|'snow_ice'|'ice'|'heat'|'cold'|'tornado'|'fog'|'rain'|'forest_fire'|'avalanche'};
export type WeatherAlertsDocument={state:'available'|'unavailable'|'stale';updated_at?:string;partial?:boolean;alerts:WeatherAlert[]};

/** Only sourced, current provider alerts are eligible. WMO code/temperature is
 * deliberately absent: precipitation never implies a civil warning. */
export function currentWeatherAlerts(document:WeatherAlertsDocument|undefined,now:Date):WeatherAlert[]{
 if(document?.state!=='available'||!Array.isArray(document.alerts))return [];
 const instant=now.getTime();
 return document.alerts.filter(alert=>typeof alert?.id==='string'&&alert.id&&typeof alert.event==='string'&&alert.event&&typeof alert.headline==='string'&&alert.headline&&typeof alert.provider==='string'&&alert.provider&&typeof alert.source==='string'&&alert.source&&['minor','moderate','severe','extreme'].includes(alert.severity)&&Number.isFinite(Date.parse(alert.onset))&&Number.isFinite(Date.parse(alert.expires))&&Date.parse(alert.onset)<=instant&&Date.parse(alert.expires)>instant);
}
