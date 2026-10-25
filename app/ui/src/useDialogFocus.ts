import {useEffect,useRef} from 'react';

const dialogs:HTMLElement[]=[],isolated=new Map<HTMLElement,boolean>();
function isolateTop(){
 for(const [element,inert] of isolated)element.inert=inert;isolated.clear();
 let branch=dialogs.at(-1);
 while(branch?.parentElement){for(const sibling of branch.parentElement.children)if(sibling!==branch&&sibling instanceof HTMLElement){isolated.set(sibling,sibling.inert);sibling.inert=true;}branch=branch.parentElement;if(branch===document.body)break;}
}
const focusable='button:not(:disabled),a[href],input:not(:disabled),select:not(:disabled),textarea:not(:disabled),[tabindex]:not([tabindex="-1"])';

/** Each nested dialog temporarily owns its siblings; closing restores their prior state. */
export function useDialogFocus<T extends HTMLElement=HTMLElement>(onClose:()=>void,closeDisabled=false,open=true){
 const ref=useRef<T>(null),latest=useRef({onClose,closeDisabled});
 latest.current={onClose,closeDisabled};
 useEffect(()=>{
  const dialog=ref.current;if(!open||!dialog)return;
  const previous=document.activeElement instanceof HTMLElement?document.activeElement:null;
  const entry=previous?.closest('.media-entry');
  const entryIndex=entry?Array.from(document.querySelectorAll('.media-entry')).indexOf(entry):-1;
  dialogs.push(dialog);isolateTop();
  const buttons=()=>Array.from(dialog.querySelectorAll<HTMLElement>(focusable)).filter(el=>!el.closest('[inert]')&&el.getClientRects().length>0);
  (dialog.querySelector<HTMLElement>('[data-dialog-initial]')||buttons()[0]||dialog).focus();
  const key=(event:KeyboardEvent)=>{
   if(dialog.closest('[inert]'))return;
   if(event.key==='Escape'&&!latest.current.closeDisabled){event.preventDefault();event.stopImmediatePropagation();latest.current.onClose();}
   if(event.key==='Tab'){
    const available=buttons(),index=available.indexOf(document.activeElement as HTMLElement);
    event.preventDefault();(available[(index+(event.shiftKey?-1:1)+available.length)%available.length]||dialog).focus();
   }
  };
  const focus=(event:FocusEvent)=>{if(!dialog.closest('[inert]')&&!dialog.contains(event.target as Node))(buttons()[0]||dialog).focus();};
  document.addEventListener('keydown',key,true);document.addEventListener('focusin',focus);
  return()=>{
   document.removeEventListener('keydown',key,true);document.removeEventListener('focusin',focus);
   const index=dialogs.indexOf(dialog);if(index>=0)dialogs.splice(index,1);isolateTop();
   requestAnimationFrame(()=>{
    if(previous?.isConnected&&!previous.closest('[inert]')&&!previous.matches(':disabled'))previous.focus();
    else if(entryIndex>=0){const entries=document.querySelectorAll<HTMLElement>('.media-entry .media-item');(entries[Math.min(entryIndex,entries.length-1)]||document.querySelector<HTMLElement>('.library-path'))?.focus();}
   });
  };
 },[open]);
 return ref;
}
