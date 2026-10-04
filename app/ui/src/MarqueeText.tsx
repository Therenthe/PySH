import {useLayoutEffect,useRef,useState,type CSSProperties} from 'react';
import './marquee.css';

/** Moves only overflowing live metadata; never duplicates accessible text. */
export function MarqueeText({text,active=false}:{text:string;active?:boolean}){
 const container=useRef<HTMLSpanElement>(null),content=useRef<HTMLSpanElement>(null);
 const [distance,setDistance]=useState(0);
 useLayoutEffect(()=>{
  const measure=()=>{if(container.current&&content.current)setDistance(Math.max(0,content.current.scrollWidth-container.current.clientWidth))};
  const observer=new ResizeObserver(measure);
  if(container.current)observer.observe(container.current);
  if(content.current)observer.observe(content.current);
  measure();return()=>observer.disconnect();
 },[text]);
 const moving=active&&distance>1;
 const style={'--marquee-offset':`${-distance}px`,'--marquee-duration':`${Math.max(14,distance/18+6)}s`} as CSSProperties;
 return <span ref={container} className={`marquee-text ${moving?'marquee-moving':''}`} style={style} title={text}><span key={text} ref={content} className="marquee-content">{text}</span></span>;
}
