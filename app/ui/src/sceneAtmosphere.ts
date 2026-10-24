import {weatherCondition} from './weatherCondition';

export type SkyCover='none'|'sparse'|'broken'|'overcast'|'unknown';
const finite=(value:unknown)=>typeof value==='number'&&Number.isFinite(value)?value:null;

/** Presentation strengths, not a second weather classification. Visibility describes
 * ground haze; cloud fraction describes the sky. Neither replaces the WMO label. */
export function sceneAtmosphere(code:unknown,stale:boolean,visibility:unknown,cloudCover:unknown){
 const category=weatherCondition(stale?null:code),known=!['missing','unknown'].includes(category);
 const distance=finite(visibility),fraction=finite(cloudCover);
 const metres=distance!==null&&distance>=0?distance:null;
 const percent=fraction!==null&&fraction>=0&&fraction<=100?fraction:null;
 if(!known)return {haze:0,cloudCover:'unknown' as SkyCover,openSky:false,transmission:0};
 // A fog code alone cannot tell us either visibility or an overcast sky.
 const haze=metres===null?(category==='fog'?.12:0):metres>=8000?0:metres>=1000?.16*(8000-metres)/7000:metres>=100?.16+.64*(1000-metres)/900:.8+.2*(100-metres)/100;
 const fallback:SkyCover=category==='clear'?'none':category==='mainly-clear'?'sparse':category==='partly-cloudy'?'broken':category==='fog'?'unknown':'overcast';
 const dry=['clear','mainly-clear','partly-cloudy','overcast','fog'].includes(category);
 const cover:SkyCover=!dry?'overcast':percent===null?fallback:percent===0?'none':percent<=25?'sparse':percent<=70?'broken':'overcast';
 const openSky=dry&&haze<.5&&['none','sparse','broken'].includes(cover)&&(category!=='fog'||metres!==null&&percent!==null);
 const transmission=openSky?Math.max(.25,(1-(percent??(cover==='broken'?45:cover==='sparse'?10:0))/100*.8)*(1-haze)):0;
 return {haze,cloudCover:cover,openSky,transmission};
}
