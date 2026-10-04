import {useEffect} from 'react';

/** Explicit pressed feedback survives neither scrolling nor cancelled pointers. */
export function useTouchFeedback(){
 useEffect(()=>{
  const pressed=new Map<number,{button:HTMLButtonElement;x:number;y:number}>();
  const release=(id:number)=>{const entry=pressed.get(id);if(entry){delete entry.button.dataset.pressed;pressed.delete(id)}};
  const clear=()=>{for(const id of pressed.keys())release(id)};
  const down=(event:PointerEvent)=>{
   const button=event.target instanceof Element?event.target.closest('button'):null;
   if(!button||button.disabled||!button.closest('.app'))return;
   release(event.pointerId);button.dataset.pressed='true';pressed.set(event.pointerId,{button,x:event.clientX,y:event.clientY});
  };
  const up=(event:PointerEvent)=>release(event.pointerId);
  const move=(event:PointerEvent)=>{const item=pressed.get(event.pointerId);if(item&&Math.hypot(event.clientX-item.x,event.clientY-item.y)>12)release(event.pointerId)};
  const visibility=()=>{if(document.hidden)clear()};
  document.addEventListener('pointerdown',down,true);document.addEventListener('pointerup',up,true);document.addEventListener('pointercancel',up,true);document.addEventListener('lostpointercapture',up,true);document.addEventListener('pointermove',move,true);document.addEventListener('visibilitychange',visibility);window.addEventListener('blur',clear);
  return()=>{clear();document.removeEventListener('pointerdown',down,true);document.removeEventListener('pointerup',up,true);document.removeEventListener('pointercancel',up,true);document.removeEventListener('lostpointercapture',up,true);document.removeEventListener('pointermove',move,true);document.removeEventListener('visibilitychange',visibility);window.removeEventListener('blur',clear)};
 },[]);
}
