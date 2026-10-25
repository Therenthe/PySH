import {useEffect,useRef,useState,type ReactNode,type RefObject} from 'react';
import {continueItems,mediaArtwork,mediaIdentity,type ContinueItem,type LocalMediaMetadata,type MediaReference,type MediaRequest} from './localMediaApi';
export const mediaTime=(value:number)=>{const seconds=Math.max(0,Math.floor(value));return `${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,'0')}`;};
export function mediaSubtitle(metadata:LocalMediaMetadata|undefined,fallback:string){
 return [metadata?.title,metadata?.artist,metadata?.album,typeof metadata?.duration_s==='number'&&Number.isFinite(metadata.duration_s)&&metadata.duration_s>0?mediaTime(metadata.duration_s):'',fallback].filter(Boolean).join(' · ');
}
export function MediaArtwork({item,available,fallback}:{item:MediaReference;available?:boolean;fallback:ReactNode}){
 const [failed,setFailed]=useState(false),url=mediaArtwork(item);
 useEffect(()=>setFailed(false),[url]);
 return available&&!failed?<img className="media-artwork" src={url} alt="" loading="lazy" onError={()=>setFailed(true)}/>:<>{fallback}</>;
}
type Inspection={metadata?:LocalMediaMetadata;artwork_available?:boolean};
export function useMediaInspection(root:RefObject<HTMLDivElement|null>,listingKey:string,request?:MediaRequest){
 const [inspected,setInspected]=useState<Record<string,Inspection>>({});
 useEffect(()=>{
  if(!request||!root.current)return;
  const controller=new AbortController(),seen=new Set<string>(),queue:MediaReference[]=[];let running=false;
  const drain=async()=>{
   if(running)return;running=true;
   try{while(queue.length&&!controller.signal.aborted){const item=queue.shift()!;try{const result=await request('/api/media/inspect',{method:'POST',body:JSON.stringify(item),signal:controller.signal});if(!controller.signal.aborted)setInspected(old=>Object.fromEntries([...Object.entries(old),[item.media_identity,result]].slice(-64)));}catch{/* A usable listing remains usable without optional metadata. */}}}finally{running=false;}
  };
  const observer=new IntersectionObserver(entries=>{for(const entry of entries){if(!entry.isIntersecting||queue.length>=6)continue;const row=entry.target as HTMLElement,identity=row.dataset.mediaIdentity,path=row.dataset.mediaPath;if(!path||!mediaIdentity(identity)||seen.has(identity))continue;seen.add(identity);queue.push({path,media_identity:identity});observer.unobserve(row);}void drain();},{root:root.current});
  root.current.querySelectorAll('.media-entry[data-media-identity]').forEach(row=>observer.observe(row));
  return()=>{controller.abort();observer.disconnect();};
 },[root,listingKey,request]);
 return inspected;
}

export function ContinueWatching({request,revision,ro,pending,onSelect}:{request:MediaRequest;revision:number;ro:boolean;pending:boolean;onSelect:(item:ContinueItem,resume:boolean)=>void}){
 const [items,setItems]=useState<ContinueItem[]>([]),[error,setError]=useState(false),[removing,setRemoving]=useState<string|null>(null),[expanded,setExpanded]=useState(false);
 const uncertain=useRef<ContinueItem|null>(null),mounted=useRef(false),serial=useRef(0),lock=useRef(false);
 const refresh=async()=>{const id=++serial.current;try{const next=continueItems(await request('/api/media/continue'));if(mounted.current&&id===serial.current){setItems(next);setError(false);}return next;}catch(error){if(mounted.current&&id===serial.current)setError(true);throw error;}};
 useEffect(()=>{mounted.current=true;void refresh().catch(()=>{});return()=>{mounted.current=false;serial.current++;};},[request,revision]);
 const remove=async(item:ContinueItem)=>{
  if(lock.current)return;lock.current=true;setRemoving(item.media_identity);setError(false);
  try{
   if(uncertain.current?.media_identity===item.media_identity){const current=await refresh();if(!current.some(row=>row.media_identity===item.media_identity&&row.path===item.path)){uncertain.current=null;return;}}
   uncertain.current=item;
   await request('/api/media/continue',{method:'DELETE',body:JSON.stringify({path:item.path,media_identity:item.media_identity})});
   uncertain.current=null;await refresh();
  }catch{if(mounted.current)setError(true);}finally{lock.current=false;if(mounted.current)setRemoving(null);}
 };
 if(!items.length&&!error)return null;
 const visible=expanded?items:items.slice(0,1);
 return <section className="media-continue" aria-label={ro?'Continuă vizionarea':'Continue watching'}>
  <header><h2>{ro?'Continuă vizionarea':'Continue watching'}</h2>{items.length>1&&<button className="outline" aria-expanded={expanded} onClick={()=>setExpanded(value=>!value)}>{expanded?(ro?'Mai puține':'Show less'):(ro?`Toate (${items.length})`:`Show all (${items.length})`)}</button>}</header>
  {visible.map(item=><article className="media-continue-item" key={item.media_identity} data-continue-path={item.path}>
   <div className="media-continue-copy"><b>{item.name}</b><small>{mediaTime(item.position_s)} / {mediaTime(item.duration_s)}</small></div>
   <div className="media-continue-actions"><button className="outline" disabled={pending||!!removing} onClick={()=>onSelect(item,true)}>{ro?'Reia':'Resume'}</button><button className="outline" disabled={pending||!!removing} onClick={()=>onSelect(item,false)}>{ro?'De la început':'Start over'}</button><button className="outline" disabled={pending||!!removing} onClick={()=>void remove(item)} aria-label={`${ro?'Elimină din istoric':'Remove from history'}: ${item.name}`}>{ro?'Elimină din istoric':'Remove from history'}</button></div>
  </article>)}
  {error&&<div className="media-continue-error" role="alert"><span>{ro?'Istoricul nu a putut fi actualizat. Fișierele sunt disponibile mai jos.':'History could not be updated. Files are available below.'}</span><button className="outline" disabled={pending||!!removing} onClick={()=>uncertain.current?void remove(uncertain.current):void refresh().catch(()=>{})}>{ro?'Încearcă din nou':'Try again'}</button></div>}
 </section>;
}
