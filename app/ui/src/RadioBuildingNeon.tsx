import {useEffect, useState} from 'react';
import {useOutputSignal} from './AudioVisualizer';
import './radio-building-neon.css';

/** Eight separately rendered Blender light circuits share the city camera.
 * Their opacity follows measured PCM amplitude, never a decorative light loop. */
export function RadioBuildingNeon({night,enabled,active}:{night:boolean;enabled:boolean;active:boolean}) {
 const [quiet,setQuiet]=useState(()=>window.matchMedia('(prefers-reduced-motion: reduce)').matches);
 useEffect(()=>{const query=window.matchMedia('(prefers-reduced-motion: reduce)');const update=()=>setQuiet(query.matches);query.addEventListener('change',update);return()=>query.removeEventListener('change',update);},[]);
 const signal=useOutputSignal(enabled&&active,quiet);
 const audible=signal.available&&!signal.silent&&(signal.rms??0)>0&&(signal.peak??0)>0;
 return <div className="city-radio-neon" data-signal-status={!enabled||!active?'inactive':signal.available?'ready':'unavailable'} data-neon-night={night} data-animate={enabled&&active&&!quiet}>
  {Array.from({length:8},(_,index)=>{
   const amplitude=audible?Math.max(signal.bars[index*2],signal.bars[index*2+1]):0;
   const opacity=amplitude>0?Math.min(1,Math.sqrt(amplitude)*(night?1:.22)):0;
   return <img key={index} data-neon-zone={index} src={`/ambient/radio-neon-zone-${String(index+1).padStart(2,'0')}.png`} style={{opacity}} alt="" draggable={false}/>;
  })}
 </div>;
}
