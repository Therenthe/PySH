import {useEffect,useLayoutEffect,useMemo,useRef,useState,type CSSProperties} from 'react';
export type HomeKey='weather'|'forecast'|'playback'|'visualizer';
export type HomePositions=Partial<Record<HomeKey,{x:number;y:number;z?:number}>>;
const keys:HomeKey[]=['weather','forecast','playback','visualizer'];
export function useHomeLayout(positions:HomePositions,editing:boolean){
 const root=useRef<HTMLDivElement>(null),nodes=useRef<Partial<Record<HomeKey,HTMLElement>>>({}),observer=useRef<ResizeObserver|null>(null);
 const [draft,setDraft]=useState<HomePositions>(positions),[sizes,setSizes]=useState<Record<string,{width:number;height:number}>>({});
 const [selected,setSelected]=useState<HomeKey|null>(null);
 const drag=useRef<{key:HomeKey;pointer:number;x:number;y:number;left:number;top:number}|null>(null);
 useEffect(()=>{if(!editing)setDraft(positions);},[editing,positions]);
 const measure=()=>{const next:Record<string,{width:number;height:number}>={};for(const [key,node] of Object.entries(nodes.current)){if(node){const r=node.getBoundingClientRect();next[key]={width:r.width,height:r.height};}}setSizes(old=>JSON.stringify(old)===JSON.stringify(next)?old:next);};
 const refs=useMemo(()=>Object.fromEntries(keys.map(key=>[key,(node:HTMLElement|null)=>{const previous=nodes.current[key];if(previous)observer.current?.unobserve(previous);if(node){nodes.current[key]=node;observer.current?.observe(node);}else delete nodes.current[key];}])) as Record<HomeKey,(node:HTMLElement|null)=>void>,[]);
 useLayoutEffect(()=>{const ro=new ResizeObserver(measure);observer.current=ro;if(root.current)ro.observe(root.current);Object.values(nodes.current).forEach(node=>node&&ro.observe(node));measure();return()=>{ro.disconnect();observer.current=null;};},[]);
 const bounded=(key:HomeKey,left:number,top:number)=>{const r=root.current!.getBoundingClientRect(),n=nodes.current[key]!.getBoundingClientRect();return {x:Math.max(0,Math.min(left,r.width-n.width))/r.width,y:Math.max(0,Math.min(top,r.height-n.height))/r.height};};
 const select=(key:HomeKey)=>{if(!root.current||!nodes.current[key])return;setSelected(key);const r=root.current.getBoundingClientRect(),n=nodes.current[key]!.getBoundingClientRect();setDraft(old=>({...Object.fromEntries(Object.entries(old).map(([id,value])=>[id,{...value,z:Math.min(3,value!.z||1)}])),[key]:{...bounded(key,n.left-r.left,n.top-r.top),z:4}}));};
 const move=(key:HomeKey,left:number,top:number)=>setDraft(old=>({...old,[key]:{...old[key],...bounded(key,left,top)}}));
 const handle=(key:HomeKey)=>({
  onPointerDown:(e:React.PointerEvent<HTMLButtonElement>)=>{if(!editing||!root.current||!nodes.current[key])return;e.preventDefault();e.stopPropagation();select(key);const r=root.current.getBoundingClientRect(),n=nodes.current[key]!.getBoundingClientRect();drag.current={key,pointer:e.pointerId,x:e.clientX,y:e.clientY,left:n.left-r.left,top:n.top-r.top};e.currentTarget.setPointerCapture(e.pointerId);},
  onPointerMove:(e:React.PointerEvent<HTMLButtonElement>)=>{const d=drag.current;if(d&&d.pointer===e.pointerId)move(d.key,d.left+e.clientX-d.x,d.top+e.clientY-d.y);},
  onPointerUp:()=>{drag.current=null;},onPointerCancel:()=>{drag.current=null;},
  onKeyDown:(e:React.KeyboardEvent<HTMLButtonElement>)=>{const delta:Record<string,[number,number]>={ArrowLeft:[-10,0],ArrowRight:[10,0],ArrowUp:[0,-10],ArrowDown:[0,10]};if(!delta[e.key]||!root.current||!nodes.current[key])return;e.preventDefault();const r=root.current.getBoundingClientRect(),n=nodes.current[key]!.getBoundingClientRect(),[dx,dy]=delta[e.key];move(key,n.left-r.left+dx,n.top-r.top+dy);},
 });
 const props=(key:HomeKey)=>{const value=draft[key],size=sizes[key];const style:CSSProperties=value?{position:'absolute',margin:0,gridArea:'auto',alignSelf:'start',justifySelf:'start',left:`clamp(0px,${value.x*100}%,calc(100% - ${size?.width||0}px))`,top:`clamp(0px,${value.y*100}%,calc(100% - ${size?.height||0}px))`,zIndex:editing&&selected===key?5:value.z||1}:{};return {ref:refs[key],style,'data-home-positioned':!!value};};
 return {root,draft,props,handle,selected,select,reset:()=>{setDraft({});setSelected(null);}};
}
