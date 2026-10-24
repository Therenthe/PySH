import {useEffect,useLayoutEffect,useMemo,useRef,useState,type CSSProperties} from 'react';
export type HomeKey='weather'|'forecast'|'playback'|'visualizer';
export type HomePosition={x:number;y:number;z?:number;anchorX?:'left'|'right';anchorY?:'top'|'bottom'};
export type HomePositions=Partial<Record<HomeKey,HomePosition>>;
type Snapshot={positions:HomePositions;selected:HomeKey|null};
type Guide={axis:'x'|'y';at:number;snapped:boolean};
type Gesture={key:HomeKey;start:Snapshot;left:number;top:number;changed:boolean;pointer?:number;x?:number;y?:number};
const keys:HomeKey[]=['weather','forecast','playback','visualizer'];
export function useHomeLayout(positions:HomePositions,editing:boolean){
 const root=useRef<HTMLDivElement>(null),nodes=useRef<Partial<Record<HomeKey,HTMLElement>>>({}),observer=useRef<ResizeObserver|null>(null);
 const [draft,setDraft]=useState<HomePositions>(positions),draftRef=useRef(draft),[sizes,setSizes]=useState<Record<string,{width:number;height:number}>>({});
 const [selected,setSelected]=useState<HomeKey|null>(null),selectedRef=useRef<HomeKey|null>(null),[originX,setOriginX]=useState(0);
 const [snap,setSnap]=useState(false),[guides,setGuides]=useState<Guide[]>([]),[moving,setMoving]=useState(false),[undoState,setUndoState]=useState<Snapshot|null>(null);
 const [preview,setPreview]=useState<{key:HomeKey;position:HomePosition}|null>(null),gesture=useRef<Gesture|null>(null);
 const write=(next:HomePositions)=>{draftRef.current=next;setDraft(next);};
 const choose=(key:HomeKey|null)=>{selectedRef.current=key;setSelected(key);};
 const snapshot=():Snapshot=>({positions:Object.fromEntries(Object.entries(draftRef.current).map(([key,value])=>[key,{...value}])),selected:selectedRef.current});
 const restore=(state:Snapshot)=>{write(state.positions);choose(state.selected);};
 const closePreview=()=>setPreview(null);
 const finish=(cancel=false)=>{const active=gesture.current;if(!active)return;gesture.current=null;if(cancel)restore(active.start);else if(active.changed)setUndoState(active.start);setMoving(false);setGuides([]);};
 useEffect(()=>{if(!editing){gesture.current=null;write(positions);choose(null);setPreview(null);setSnap(false);setGuides([]);setMoving(false);setUndoState(null);}},[editing,positions]);
 useEffect(()=>{if(!editing)return;const cancel=()=>finish(true),hidden=()=>{if(document.hidden)cancel();};window.addEventListener('blur',cancel);document.addEventListener('visibilitychange',hidden);return()=>{window.removeEventListener('blur',cancel);document.removeEventListener('visibilitychange',hidden);};},[editing]);
 const measure=()=>{if(root.current)setOriginX(root.current.getBoundingClientRect().left);const next:Record<string,{width:number;height:number}>={};for(const [key,node] of Object.entries(nodes.current)){if(node){const r=node.getBoundingClientRect();next[key]={width:r.width,height:r.height};}}setSizes(old=>JSON.stringify(old)===JSON.stringify(next)?old:next);};
 const refs=useMemo(()=>Object.fromEntries(keys.map(key=>[key,(node:HTMLElement|null)=>{const previous=nodes.current[key];if(previous)observer.current?.unobserve(previous);if(node){nodes.current[key]=node;observer.current?.observe(node);}else delete nodes.current[key];}])) as Record<HomeKey,(node:HTMLElement|null)=>void>,[]);
 useLayoutEffect(()=>{const ro=new ResizeObserver(measure);observer.current=ro;if(root.current)ro.observe(root.current);Object.values(nodes.current).forEach(node=>node&&ro.observe(node));measure();return()=>{ro.disconnect();observer.current=null;};},[]);
 // Store the nearest edge, not a compact card's top-left corner. Growth then
 // uses the free space toward the canvas center without moving the saved edge.
 const bounded=(key:HomeKey,left:number,top:number):HomePosition=>{const r=root.current!.getBoundingClientRect(),n=nodes.current[key]!.getBoundingClientRect();const x=Math.max(0,Math.min(left,Math.max(0,r.width-n.width))),y=Math.max(0,Math.min(top,Math.max(0,r.height-n.height)));const anchorX=x+n.width/2>r.width/2?'right':'left',anchorY=y+n.height/2>r.height/2?'bottom':'top';return {x:(anchorX==='right'?Math.max(0,r.width-x-n.width):x)/Math.max(1,r.width),y:(anchorY==='bottom'?Math.max(0,r.height-y-n.height):y)/Math.max(1,r.height),anchorX,anchorY};};
 const select=(key:HomeKey)=>{if(!editing||preview||!root.current||!nodes.current[key])return;choose(key);const r=root.current.getBoundingClientRect(),n=nodes.current[key]!.getBoundingClientRect();write({...Object.fromEntries(Object.entries(draftRef.current).map(([id,value])=>[id,{...value,z:Math.min(3,value!.z||1)}])),[key]:{...bounded(key,n.left-r.left,n.top-r.top),z:4}});};
 const begin=(key:HomeKey):Gesture|null=>{if(!editing||preview||!root.current||!nodes.current[key])return null;const r=root.current.getBoundingClientRect(),n=nodes.current[key]!.getBoundingClientRect(),start=snapshot();select(key);const next={key,start,left:n.left-r.left,top:n.top-r.top,changed:false};gesture.current=next;setMoving(true);return next;};
 const move=(active:Gesture,left:number,top:number)=>{
  if(!root.current||!nodes.current[active.key])return;
  const r=root.current.getBoundingClientRect(),n=nodes.current[active.key]!.getBoundingClientRect();
  const maxX=Math.max(0,r.width-n.width),maxY=Math.max(0,r.height-n.height);left=Math.max(0,Math.min(left,maxX));top=Math.max(0,Math.min(top,maxY));
  const xs=[0,r.width/2,r.width],ys=[0,r.height/2,r.height];
  for(const [key,node] of Object.entries(nodes.current)){if(key===active.key||!node)continue;const b=node.getBoundingClientRect();if(b.width<=0||b.height<=0||!node.getClientRects().length)continue;xs.push(b.left-r.left,b.left-r.left+b.width/2,b.right-r.left);ys.push(b.top-r.top,b.top-r.top+b.height/2,b.bottom-r.top);}
  const nearest=(start:number,size:number,max:number,candidates:number[])=>{let hit:{delta:number;at:number}|null=null;for(const at of candidates)for(const offset of [0,size/2,size]){const delta=at-(start+offset),next=start+delta;if(next>=0&&next<=max&&Math.abs(delta)<=6&&(!hit||Math.abs(delta)<Math.abs(hit.delta)))hit={delta,at};}return hit;};
  const x=nearest(left,n.width,maxX,xs),y=nearest(top,n.height,maxY,ys);
  setGuides([...(x?[{axis:'x' as const,at:x.at,snapped:snap}]:[]),...(y?[{axis:'y' as const,at:y.at,snapped:snap}]:[])]);
  if(snap){left+=x?.delta||0;top+=y?.delta||0;}
  active.changed=Math.abs(left-active.left)>.5||Math.abs(top-active.top)>.5;
  write({...draftRef.current,[active.key]:{...draftRef.current[active.key],...bounded(active.key,left,top)}});
 };
 const handle=(key:HomeKey)=>({
  onPointerDown:(e:React.PointerEvent<HTMLButtonElement>)=>{if(gesture.current||preview)return;e.preventDefault();e.stopPropagation();const next=begin(key);if(!next)return;Object.assign(next,{pointer:e.pointerId,x:e.clientX,y:e.clientY});e.currentTarget.focus({preventScroll:true});e.currentTarget.setPointerCapture(e.pointerId);},
  onPointerMove:(e:React.PointerEvent<HTMLButtonElement>)=>{const active=gesture.current;if(active?.pointer===e.pointerId)move(active,active.left+e.clientX-active.x!,active.top+e.clientY-active.y!);},
  onPointerUp:(e:React.PointerEvent<HTMLButtonElement>)=>{if(gesture.current?.pointer===e.pointerId)finish();},
  onPointerCancel:(e:React.PointerEvent<HTMLButtonElement>)=>{if(gesture.current?.pointer===e.pointerId)finish(true);},
  onLostPointerCapture:(e:React.PointerEvent<HTMLButtonElement>)=>{if(gesture.current?.pointer===e.pointerId)finish(true);},
  onKeyDown:(e:React.KeyboardEvent<HTMLButtonElement>)=>{if(e.key==='Escape'&&gesture.current){e.preventDefault();finish(true);return;}const delta:Record<string,[number,number]>={ArrowLeft:[-10,0],ArrowRight:[10,0],ArrowUp:[0,-10],ArrowDown:[0,10]};if(!delta[e.key]||preview||(e.repeat&&!gesture.current)||gesture.current?.pointer!==undefined||!root.current||!nodes.current[key])return;e.preventDefault();const active=gesture.current||begin(key);if(!active)return;const r=root.current.getBoundingClientRect(),n=nodes.current[key]!.getBoundingClientRect(),[dx,dy]=delta[e.key];move(active,n.left-r.left+dx,n.top-r.top+dy);},
  onKeyUp:(e:React.KeyboardEvent<HTMLButtonElement>)=>{if(e.key.startsWith('Arrow')&&gesture.current?.pointer===undefined)finish();},
  onBlur:()=>{if(gesture.current?.pointer===undefined)finish();},
 });
 const togglePreview=(key:HomeKey)=>{if(!editing||gesture.current||!root.current||!nodes.current[key])return;if(preview){closePreview();return;}const r=root.current.getBoundingClientRect(),n=nodes.current[key]!.getBoundingClientRect();setPreview({key,position:draftRef.current[key]||bounded(key,n.left-r.left,n.top-r.top)});setGuides([]);};
 const props=(key:HomeKey)=>{const isPreview=preview?.key===key,isCompanion=preview?.key==='visualizer'&&key==='playback',value=isPreview?preview.position:draft[key],size=sizes[key];const style:CSSProperties=value?{position:'absolute',margin:0,gridArea:'auto',alignSelf:'start',justifySelf:'start',[value.anchorX==='right'?'right':'left']:`clamp(0px,${value.x*100}%,max(0px,calc(100% - ${size?.width||0}px)))`,[value.anchorY==='bottom'?'bottom':'top']:`clamp(0px,${value.y*100}%,max(0px,calc(100% - ${size?.height||0}px)))`,zIndex:isPreview?6:editing&&selected===key?5:value.z||1}:{};return {ref:refs[key],style,'data-home-positioned':!!draft[key],'data-layout-preview':isPreview||undefined,'data-layout-preview-companion':isCompanion||undefined,inert:isPreview||isCompanion||undefined,'aria-hidden':isPreview||isCompanion||undefined};};
 return {root,originX,draft,props,handle,selected,select,guides,snap,setSnap,moving,preview:preview?.key||null,togglePreview,closePreview,canUndo:!!undoState,undo:()=>{if(!undoState||gesture.current)return;closePreview();restore(undoState);setUndoState(null);setGuides([]);},reset:()=>{if(gesture.current)return;closePreview();write({});choose(null);setGuides([]);setUndoState(null);}};
}
