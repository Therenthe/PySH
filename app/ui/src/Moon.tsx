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
 <defs><radialGradient id={id+'tone'} cx="35%" cy="30%"><stop stopColor="#e4e5dd"/><stop offset=".7" stopColor="#b7bfba"/><stop offset="1" stopColor="#788787"/></radialGradient><clipPath id={id+'lit'}><path d={'M'+outer.concat(inner).join('L')+'Z'}/></clipPath></defs>
 <circle cx="48" cy="48" r="44" fill="#23323c"/>
 <g clipPath={`url(#${id}lit)`}><circle cx="48" cy="48" r="44" fill={`url(#${id}tone)`}/>
 <path d="M18 25q13-12 25-6l8 14-9 12-17-2-10-9zM53 16l16 9 5 15-14 8-13-11zM17 50l14-8 14 7 6 19-12 10-17-11zM58 53l17-5 7 13-9 17-16-7z" fill="#667b7e" opacity=".32"/>
 {Array.from({length:34},(_,i)=><ellipse key={i} cx={16+(i*13.37%65)} cy={14+(i*19.17%67)} rx={1+i%3*.8} ry={.7+i%3*.5} fill="none" stroke={i%2?'#f1f0e6':'#647576'} strokeWidth=".6" opacity=".24"/>)}
 </g></svg>;
}
