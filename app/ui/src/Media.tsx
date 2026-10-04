import {useRef,useState,type ReactNode} from 'react';
import {formatMediaSize} from './formatMediaSize';
import './media.css';

export type MediaItem={path:string;name:string;kind?:string;type?:string;is_dir?:boolean;mime?:string;size?:unknown;deletable?:boolean;delete_token?:string;[key:string]:unknown};
export type MediaListing={path?:string;parent?:string|null;items?:MediaItem[];error?:string;partial?:boolean};
export type MediaProps={
 language:'en'|'ro';media:MediaListing;loading?:boolean;busy?:boolean;
 localMediaPending?:boolean;externalMediaPending?:boolean;deletionPending?:boolean;
 localAudioError?:boolean;localAudioFilename?:string;localAudioErrorMessage?:string;audioReady:boolean;
 currentPath?:string;playerState?:string;deleteDisabledPaths?:string[];
 t:(key:string)=>string;icon:(name:string,size?:number)=>ReactNode;statusText:(error:string)=>string;
 onBrowse:(path?:string)=>void|Promise<unknown>;onSelect:(item:MediaItem,isVideo:boolean)=>void;
 onService:(id:string)=>void;onReplayCurrent:()=>void;onDelete?:(item:MediaItem)=>void;
 onSearch?:(initial:string)=>Promise<string|null>;
};
export const isMediaDirectory=(item:MediaItem)=>Boolean(item.is_dir||item.type==='directory'||item.kind==='directory');
const isVideo=(item:MediaItem)=>item.kind==='video'||item.mime?.startsWith('video/')||/\.(mp4|m4v|mkv|webm|mov)$/i.test(item.name);
const searchKey=(value:string)=>value.normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase().trim();
const basename=(path:string)=>path.split(/[\\/]/).filter(Boolean).at(-1)||'';

/** Browsing and search stay local to the listing; all device mutations belong to App. */
export function Media({language,media,loading=false,busy=false,localMediaPending=false,externalMediaPending=false,deletionPending=false,localAudioError=false,localAudioFilename='',localAudioErrorMessage='',audioReady,currentPath,playerState,deleteDisabledPaths=[],t,icon,statusText,onBrowse,onSelect,onService,onReplayCurrent,onDelete,onSearch}:MediaProps){
 const ro=language==='ro',[section,setSection]=useState<'files'|'services'>('files'),[query,setQuery]=useState(''),[searchPending,setSearchPending]=useState(false),[browsing,setBrowsing]=useState(false),browseSerial=useRef(0);
 const pending=busy||localMediaPending||externalMediaPending||deletionPending;
 const items=media.items||[],matches=items.filter(item=>searchKey(item.name).includes(searchKey(query))),hasParent=Boolean(media.parent&&media.parent!==media.path);
 const inFolder=Boolean(media.path),folderName=inFolder?basename(media.path||''):t('root');
 const browse=async(path?:string)=>{const serial=++browseSerial.current;setBrowsing(true);setQuery('');try{await onBrowse(path);}finally{if(serial===browseSerial.current)setBrowsing(false);}};
 const search=async()=>{if(!onSearch||pending||searchPending)return;setSearchPending(true);try{const result=await onSearch(query);if(result!==null)setQuery(result.trim());}finally{setSearchPending(false);}};
 const deleteLabel=ro?'Șterge fișierul':'Delete file';
 return <div className="media-page media-redesign">
  <header className="media-heading"><h1>{t('media')}</h1><div className="media-sections" role="group" aria-label={ro?'Sursă media':'Media source'}>
   <button className={section==='files'?'selected':''} aria-pressed={section==='files'} onClick={()=>setSection('files')}>{icon('folder',20)}<span>{t('onDevice')}</span></button>
   <button className={section==='services'?'selected':''} aria-pressed={section==='services'} onClick={()=>setSection('services')}>{icon('globe',20)}<span>{t('services')}</span></button>
  </div></header>
  {section==='files'?<section className="media-library" aria-label={t('root')} aria-busy={pending||loading||browsing}>
   <div className="media-library-toolbar">
    <div className="crumb-actions">
     {hasParent&&<button className="media-parent" aria-label={t('parentFolder')} disabled={pending} onClick={()=>void browse(media.parent||'')}>{icon('back',20)}</button>}
     {(inFolder||browsing||loading)&&<button className="media-root" disabled={pending} onClick={()=>void browse('')}>{t('root')}</button>}
     {inFolder&&<span className="media-crumb-separator" aria-hidden="true">/</span>}
     <div className="library-path"><b>{folderName}</b><span className="media-sr-only">{media.path||''}</span></div>
    </div>
    <span className="media-file-count" aria-label={ro?'Număr de elemente':'Item count'}>{matches.length}</span>
    {onSearch&&<button className={`media-search-toggle ${query?'active':''}`} disabled={pending||searchPending} onClick={()=>void search()} aria-label={ro?'Caută în acest dosar':'Search this folder'}>{icon('search',21)}</button>}
   </div>
   {query&&<div className="media-query"><button className="media-query-edit" disabled={pending} onClick={()=>void search()}>{icon('search',17)}<span>{query}</span></button><button className="media-query-clear" aria-label={ro?'Șterge căutarea':'Clear search'} onClick={()=>setQuery('')}>{icon('close',20)}</button></div>}
   <div className="media-items">
    {localAudioError&&<section className="local-audio-recovery" role="alert"><div><b>{localAudioFilename}</b><p>{localAudioErrorMessage}</p><small>{ro?'Reîncearcă redarea sau alege alt fișier.':'Replay or choose another file.'}</small></div><button className="outline" disabled={!audioReady||pending} onClick={onReplayCurrent}>{ro?'Reia redarea':'Replay'}</button></section>}
    {(localMediaPending||loading||browsing)&&<p className="media-pending" role="status">{localMediaPending?(ro?'Se deschide fișierul…':'Opening media…'):t('loading')}</p>}
    {media.partial&&<div className="media-partial" role="status"><span>{t('mediaPartial')}</span><button className="outline" disabled={pending} onClick={()=>void browse()}>{t('retry')}</button></div>}
    {media.error?<div className="empty-state" role="status">{icon('folder',32)}<b>{statusText(media.error)}</b><button className="outline" disabled={pending} onClick={()=>void browse()}>{t('retry')}</button></div>:matches.length?matches.map(item=>{
     const directory=isMediaDirectory(item),video=Boolean(isVideo(item)),selected=Boolean(!directory&&currentPath===item.path&&playerState&&playerState!=='idle');
     const canDelete=!directory&&item.deletable===true&&typeof item.delete_token==='string'&&item.delete_token.length>0;
     const active=deleteDisabledPaths.includes(item.path)||Boolean(selected&&['playing','paused','buffering','connecting'].includes(playerState||''));
     return <div className={`media-entry ${selected?'selected':''}`} key={item.path}>
      <button className="media-item" disabled={pending||loading||browsing} onClick={()=>directory?void browse(item.path):onSelect(item,video)}>
       <span className={`file-icon ${directory?'folder':video?'video':'audio'}`}>{icon(directory?'folder':video?'media':'speaker',26)}</span>
       <span className="media-file-copy"><b>{item.name}</b><small>{directory?t('folders'):formatMediaSize(item.size,language)}</small></span>
       <span className="media-file-action" aria-hidden="true">{icon(directory?'next':'play',20)}</span>
      </button>
      {canDelete&&onDelete&&<button className="media-delete" disabled={pending||loading||browsing||active} title={active?(ro?'Oprește redarea înainte de ștergere':'Stop playback before deleting'):deleteLabel} aria-label={`${deleteLabel}: ${item.name}`} onClick={()=>onDelete(item)}><svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7"/></svg></button>}
     </div>;
    }):loading||browsing?null:<div className="empty-state">{icon(query?'search':'folder',32)}<b>{query?(ro?'Niciun fișier găsit':'No matching files'):t('noFiles')}</b><span>{query?(ro?'Caută alt nume în acest dosar.':'Try another name in this folder.'):t('selectFile')}</span>{query&&<button className="outline" onClick={()=>setQuery('')}>{ro?'Șterge căutarea':'Clear search'}</button>}</div>}
   </div>
  </section>:<section className="service-panel" aria-label={t('services')} aria-busy={externalMediaPending}>
   <p className="muted" role={externalMediaPending?'status':undefined}>{externalMediaPending?(ro?'Se deschide serviciul…':'Opening service…'):t('websiteOpens')}</p>
   <div className="media-service-list">{['youtube','netflix','spotify'].map((id,index)=><button className="service-row" key={id} disabled={pending} onClick={()=>onService(id)}><span className={`service-logo service-${id}`} aria-hidden="true">{['▶','N','●'][index]}</span><span className="media-service-copy"><b>{t(id)}</b><small>{ro?'Deschide site-ul oficial':'Open official website'}</small></span><span className="service-arrow">{icon('next',22)}</span></button>)}</div>
  </section>}
 </div>;
}
