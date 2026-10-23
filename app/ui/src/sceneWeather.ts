import {weatherCondition} from './weatherCondition';

export type SceneWeather = {
 category:ReturnType<typeof weatherCondition>; precipitation:'none'|'rain'|'snow'|'ice';
 intensity:'none'|'light'|'moderate'|'heavy'; count:number; wind:number;
 freezing:boolean; thunder:boolean; heat:boolean; season:'spring'|'summer'|'autumn'|'winter';
};
const finite=(value:unknown)=>typeof value==='number'&&Number.isFinite(value)?value:undefined;

/** WMO observations describe precipitation, never a flood/tornado or an alert.
 * Decorations must not manufacture emergency information absent a real alert source.
 */
export function sceneWeather(code:unknown,stale:boolean,temperature:unknown,wind:unknown,now:Date,latitude:unknown):SceneWeather {
 const category=weatherCondition(stale?null:code),n=typeof code==='number'?code:-1;
 const snow=['snow','snow-showers'].includes(category),ice=['freezing-rain','freezing-drizzle','thunder-hail'].includes(category);
 const wet=['rain','rain-showers','drizzle','thunder'].includes(category);
 const precipitation=snow?'snow':ice?'ice':wet?'rain':'none';
 const light=[51,56,61,66,71,77,80,85].includes(n),heavy=[55,57,65,67,75,82,86,99].includes(n);
 const intensity=precipitation==='none'?'none':light?'light':heavy?'heavy':'moderate';
 const month=now.getUTCMonth(),north=(finite(latitude)??45)>=0;
 const northern=month===11||month<2?'winter':month<5?'spring':month<8?'summer':'autumn';
 const season=north?northern:({winter:'summer',summer:'winter',spring:'autumn',autumn:'spring'} as const)[northern];
 return {category,precipitation,intensity,count:intensity==='none'?0:intensity==='light'?18:intensity==='heavy'?64:38,
  wind:stale?0:Math.min(100,Math.max(0,finite(wind)??0)),freezing:!stale&&(ice||(snow&&(finite(temperature)??1)<=0)),
  thunder:!stale&&['thunder','thunder-hail'].includes(category),heat:!stale&&(finite(temperature)??0)>=35,season};
}
