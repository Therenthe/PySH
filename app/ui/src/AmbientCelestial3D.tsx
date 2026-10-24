import {useId,type CSSProperties} from 'react';
import {lunarPhase} from './Moon';
import type {WeatherCondition} from './weatherCondition';
import {aircraftAnchors} from './aircraftAnchors';
import type {SkyCover} from './sceneAtmosphere';
import './ambient-celestial-3d.css';

const assets='/ambient/sky3d/';

export function moonAtlasFrame(illumination:number,waxing:boolean){
 const fraction=Math.max(0,Math.min(1,Number.isFinite(illumination)?illumination:0));
 const phase=Math.acos(1-2*fraction);
 return Math.round((waxing?phase:Math.PI*2-phase)/(Math.PI*2)*128)%128;
}

/** The sphere/material/lighting are rendered in Blender. Existing phase metadata
 * stays continuous; atlas selection has at most 1.23% illumination rounding. */
export function BlenderMoon({now=new Date()}:{now?:Date}){
 const {illumination,waxing}=lunarPhase(now),frame=moonAtlasFrame(illumination,waxing);
 const style={backgroundPosition:`${frame%16/15*100}% ${Math.floor(frame/16)/7*100}%`} as CSSProperties;
 return <span className="ambient-orb ambient-moon blender-moon" style={style} data-lunar-illumination={illumination.toFixed(3)} data-lunar-direction={waxing?'waxing':'waning'} data-blender-phase-frame={frame} data-moon-surface="blender-nasa-svs" aria-hidden="true"/>;
}

/** Same 170 centres as VariantaBack; the sprite adds a small optical core/glint,
 * not an astrophotography background or a denser fictional star map. */
export function BlenderStars(){
 const id=useId().replace(/:/g,'');
 return <svg className="ambient-stars stars-blender3d" viewBox="0 0 694 422" preserveAspectRatio="none" aria-hidden="true"><defs>{[0,1,2,3].map(frame=><symbol key={frame} id={`${id}-star-${frame}`} viewBox={`${frame%2*48} ${Math.floor(frame/2)*48} 48 48`}><image href={`${assets}star-glints-blender-v1.png`} width="96" height="96"/></symbol>)}</defs>{Array.from({length:170},(_,i)=>{
  const x=12+(i*137.507%670),y=8+((i*73.13+i*i*3.11)%360),size=i%37===0?7:i%4===0?4.8:4.0;
  return <use key={i} className={i%37===0?'blender-star-glint':undefined} data-blender-star={i} href={`#${id}-star-${i%37===0?3:i%4===0?1:0}`} x={x-size/2} y={y-size/2} width={size} height={size} opacity={i%4===0?.85:.65}/>;
 })}</svg>;
}

export function BlenderClouds({night,condition,cover:override}:{night:boolean;condition:WeatherCondition;cover?:SkyCover}){
 const cover=override??(condition==='mainly-clear'?'sparse':condition==='partly-cloudy'?'broken':['clear','missing','unknown'].includes(condition)?'none':'overcast');
 if(cover==='none'||cover==='unknown')return null;
 return <div className={`ambient-clouds blender-clouds cloud-cover-${cover}`} data-cloud-model="blender-volume" data-cloud-cover={cover} aria-hidden="true">
  <img className="cloud-mass cloud-primary" src={`${assets}clouds-${night?'night':'day'}-blender-v1.png`} alt="" draggable={false}/>
  {cover!=='sparse'&&<img className="cloud-mass cloud-secondary" src={`${assets}clouds-${night?'night':'day'}-blender-v1.png`} alt="" draggable={false}/>}
  {cover==='overcast'&&<img className="cloud-mass cloud-low" src={`${assets}clouds-${night?'night':'day'}-blender-v1.png`} alt="" draggable={false}/>}
 </div>;
}

export type AircraftVariant='airliner'|'turboprop'|'business-jet'|'tv-helicopter'|'police-helicopter';

export function BlenderAircraft({night,heading=0,facing=1,scale=1,variant='airliner'}:{night:boolean;heading?:number;facing?:1|-1;scale?:number;variant?:AircraftVariant}){
 const helicopter=variant.endsWith('helicopter'),prefix=`/ambient/aircraft/${variant}-${night?'night':'day'}`,points=aircraftAnchors[variant];
 const lights:ReadonlyArray<readonly[string,readonly[number,number]]>='port' in points?[['port',points.port],['starboard',points.starboard]]:[['beacon',points.beacon]];
 return <span className={`blender-aircraft aircraft-${variant}`} data-aircraft-model="blender3d" data-aircraft-variant={variant} data-facing={facing} style={{transform:`rotate(${heading}deg) scale(${facing*scale},${scale})`}}>
  <span className={helicopter?'blender-aircraft-body aircraft-hover':'blender-aircraft-body'}>
   {(helicopter?[0,1,2]:[null]).map(frame=><img key={frame??'fixed'} className={frame===null?undefined:`aircraft-rotor-frame rotor-frame-${frame}`} src={`${prefix}${frame===null?'':`-${frame}`}-v1.png`} alt="" draggable={false}/>)}
   {night&&lights.map(([name,point])=><i key={name} className={`blender-aircraft-light ${name}${variant==='police-helicopter'?' police':''}`} style={{left:`${point[0]*100}%`,top:`${point[1]*100}%`}}/>)}
  </span>
 </span>;
}

export function BlenderSun(){return <span className="ambient-orb ambient-sun blender-sun" data-sun-model="blender3d" aria-hidden="true"/>;}

/** The scheduler owns heading/trajectory. This sprite's bright point faces +X. */
export function BlenderMeteor(){return <span className="blender-meteor" data-meteor-model="blender3d" aria-hidden="true"/>;}
