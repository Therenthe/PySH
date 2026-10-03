import {useId} from 'react';

/** Low-precision geocentric solar/lunar longitude: illustration, not an ephemeris or sky position. */
export function lunarPhase(now:Date) {
 const d=now.getTime()/86400000-10957.5,r=Math.PI/180;
 const m=(357.5291+.98560028*d)*r;
 const sun=m+(1.9148*Math.sin(m)+.02*Math.sin(2*m)+.0003*Math.sin(3*m)+102.9372+180)*r;
 const moon=(218.316+13.176396*d+6.289*Math.sin((134.963+13.064993*d)*r))*r;
 const latitude=5.128*Math.sin((93.272+13.229350*d)*r)*r;
 const angle=((moon-sun)%(2*Math.PI)+2*Math.PI)%(2*Math.PI);
 return {waxing:angle<Math.PI,illumination:(1-Math.cos(latitude)*Math.cos(angle))/2};
}

export function Moon({now=new Date()}:{now?:Date}){
 const id=useId().replace(/:/g,''),{waxing,illumination}=lunarPhase(now);
 const outer:string[]=[],inner:string[]=[];
 for(let y=-44;y<=44;y+=2){const x=Math.sqrt(Math.max(0,44*44-y*y));outer.push(`${48+(waxing?x:-x)},${48+y}`);inner.unshift(`${48+(waxing?1:-1)*(1-2*illumination)*x},${48+y}`);}
 return <svg className="ambient-orb ambient-moon" viewBox="0 0 96 96" data-lunar-illumination={illumination.toFixed(3)} data-lunar-direction={waxing?'waxing':'waning'} aria-hidden="true">
 <defs><clipPath id={id+'disc'}><circle cx="48" cy="48" r="44"/></clipPath><clipPath id={id+'lit'}><path d={'M'+outer.concat(inner).join('L')+'Z'}/></clipPath></defs>
 <circle cx="48" cy="48" r="44" fill="#23323c"/>
 {/* Static NASA SVS surface material; the existing computed phase supplies illumination.
     Texture alignment is illustrative, not current libration or a local sky position. */}
 <g clipPath={`url(#${id}disc)`}><image data-moon-surface="nasa-svs" href="/assets/moon-surface-nasa.jpg" x="-4" y="-4" width="104" height="104" opacity=".1"/>
 <g clipPath={`url(#${id}lit)`}><image href="/assets/moon-surface-nasa.jpg" x="-4" y="-4" width="104" height="104"/></g>
 </g></svg>;
}
