import {useEffect,useRef,useState} from 'react';
import './heart-confetti.css';

export type HeartConfettiProps={enabled:boolean;now:Date;timezone:string};
type Moment={key:string;hour:number;minute:number;second:number;epoch:number};
type Heart={left:number;size:number;drift:number;delay:number;duration:number;rotation:number;tone:number};

/** Local civil time from the same zone as the hub clock; never infer a zone. */
export function confettiMoment(now:Date,timezone:string):Moment|null{
 if(!Number.isFinite(now.getTime()))return null;
 try{
  const parts=new Intl.DateTimeFormat('en-GB',{timeZone:timezone,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).formatToParts(now);
  const value=(name:string)=>parts.find(part=>part.type===name)?.value||'';
  const hour=Number(value('hour')),minute=Number(value('minute')),second=Number(value('second'));
  return {key:`${value('year')}-${value('month')}-${value('day')}T${value('hour')}:${value('minute')}`,hour,minute,second,epoch:now.getTime()};
 }catch{return null}
}
export function isConfettiBoundary(previous:Moment|null,current:Moment|null):boolean{
 return !!previous&&!!current&&current.epoch>previous.epoch&&current.epoch-previous.epoch<=2000&&previous.key!==current.key&&current.second===0&&(current.minute===0||current.hour===current.minute);
}

/** Decorative celebration only: bounded lifetime, no pointer/keyboard interception. */
export function HeartConfetti({enabled,now,timezone}:HeartConfettiProps){
 const [hearts,setHearts]=useState<Heart[]>([]),[reduced,setReduced]=useState(()=>typeof window!=='undefined'&&window.matchMedia('(prefers-reduced-motion: reduce)').matches);
 const timer=useRef<ReturnType<typeof setTimeout>|null>(null),cursor=useRef<Moment|null>(null),context=useRef(''),seen=useRef(new Set<string>()),latestEvent=useRef(-Infinity);
 const clear=()=>{if(timer.current!==null){clearTimeout(timer.current);timer.current=null}setHearts(current=>current.length?[]:current)};
 useEffect(()=>{
  const media=window.matchMedia('(prefers-reduced-motion: reduce)');
  const motion=()=>{setReduced(media.matches);cursor.current=null;clear()};
  const visibility=()=>{cursor.current=null;clear()};
  media.addEventListener('change',motion);document.addEventListener('visibilitychange',visibility);
  return()=>{media.removeEventListener('change',motion);document.removeEventListener('visibilitychange',visibility);if(timer.current!==null)clearTimeout(timer.current)};
 },[]);
 useEffect(()=>{
  const current=confettiMoment(now,timezone),newContext=`${enabled}:${reduced}:${timezone}`;
  if(context.current!==newContext){context.current=newContext;cursor.current=current;clear();return}
  const previous=cursor.current;cursor.current=current;
  if(!enabled||reduced||document.hidden){clear();return}
  if(!isConfettiBoundary(previous,current)||!current||seen.current.has(current.key)||current.epoch<=latestEvent.current)return;
  latestEvent.current=current.epoch;
  seen.current.add(current.key);
  // Keep a small bounded event ledger; repeated/backward ticks cannot restart a burst.
  if(seen.current.size>96)seen.current.delete(seen.current.values().next().value!);
  clear();
  const count=14+Math.floor(Math.random()*7);
  setHearts(Array.from({length:count},()=>({left:4+Math.random()*92,size:9+Math.random()*9,drift:-30+Math.random()*60,delay:Math.random()*350,duration:3500+Math.random()*1100,rotation:-25+Math.random()*50,tone:Math.floor(Math.random()*3)})));
  timer.current=setTimeout(()=>{timer.current=null;setHearts([])},5000);
 },[enabled,now.getTime(),timezone,reduced]);
 if(!enabled||reduced||!hearts.length)return null;
 return <div className="heart-confetti" aria-hidden="true" data-testid="heart-confetti">{hearts.map((heart,index)=><svg key={index} className={`confetti-heart confetti-tone-${heart.tone}`} viewBox="0 0 24 24" focusable="false" style={{left:`${heart.left}%`,width:heart.size,height:heart.size,animationDelay:`${heart.delay}ms`,animationDuration:`${heart.duration}ms`,'--heart-drift':`${heart.drift}px`,'--heart-rotation':`${heart.rotation}deg`} as React.CSSProperties}><path d="M12 21 3.3 12.5C-2 7.1 5.5-1.2 12 5.2 18.5-1.2 26 7.1 20.7 12.5Z" fill="currentColor"/></svg>)}</div>;
}
