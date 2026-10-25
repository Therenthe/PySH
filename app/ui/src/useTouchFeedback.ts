import {useEffect} from 'react';

/** Pressed feedback is visual only; actions stay with each control's handlers. */
export function useTouchFeedback(){
 useEffect(()=>{
  const pressed=new Map<number,{button:HTMLElement;x:number;y:number}>();let keyboard:HTMLElement|null=null;
  const paint=(button:HTMLElement)=>{if(keyboard===button||[...pressed.values()].some(entry=>entry.button===button))button.dataset.pressed='true';else delete button.dataset.pressed;};
  const release=(id:number)=>{const entry=pressed.get(id);if(entry){pressed.delete(id);paint(entry.button);}};
  const releaseKey=()=>{const previous=keyboard;keyboard=null;if(previous)paint(previous);};
  const clear=()=>{releaseKey();for(const id of pressed.keys())release(id);};
  const control=(target:EventTarget|null)=>{const button=target instanceof Element?target.closest('button,.ambient-home [role="button"]'):null;return button instanceof HTMLElement&&button.closest('.app')&&!button.matches(':disabled,[aria-disabled="true"]')&&!button.closest('[inert]')?button:null;};
  const down=(event:PointerEvent)=>{const button=control(event.target);if(!button)return;release(event.pointerId);pressed.set(event.pointerId,{button,x:event.clientX,y:event.clientY});paint(button);};
  const up=(event:PointerEvent)=>release(event.pointerId);
  const move=(event:PointerEvent)=>{const entry=pressed.get(event.pointerId);if(entry&&Math.hypot(event.clientX-entry.x,event.clientY-entry.y)>12)release(event.pointerId);};
  const keyDown=(event:KeyboardEvent)=>{if(!['Enter',' '].includes(event.key)||event.repeat||event.altKey||event.ctrlKey||event.metaKey)return;releaseKey();keyboard=control(event.target);if(keyboard)paint(keyboard);};
  const keyUp=(event:KeyboardEvent)=>{if(['Enter',' '].includes(event.key))releaseKey();};
  const focusOut=(event:FocusEvent)=>{if(keyboard&&!keyboard.contains(event.relatedTarget as Node|null))releaseKey();};
  const visibility=()=>{if(document.hidden)clear();};
  document.addEventListener('pointerdown',down,true);document.addEventListener('pointerup',up,true);document.addEventListener('pointercancel',up,true);document.addEventListener('lostpointercapture',up,true);document.addEventListener('pointermove',move,true);document.addEventListener('keydown',keyDown,true);document.addEventListener('keyup',keyUp,true);document.addEventListener('focusout',focusOut,true);document.addEventListener('visibilitychange',visibility);window.addEventListener('blur',clear);
  return()=>{clear();document.removeEventListener('pointerdown',down,true);document.removeEventListener('pointerup',up,true);document.removeEventListener('pointercancel',up,true);document.removeEventListener('lostpointercapture',up,true);document.removeEventListener('pointermove',move,true);document.removeEventListener('keydown',keyDown,true);document.removeEventListener('keyup',keyUp,true);document.removeEventListener('focusout',focusOut,true);document.removeEventListener('visibilitychange',visibility);window.removeEventListener('blur',clear);};
 },[]);
}
