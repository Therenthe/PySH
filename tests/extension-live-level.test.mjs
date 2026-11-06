import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

// Deterministic DOM/native-bridge double: queue behavior, not device acceptance.
const source=readFileSync(new URL('../app/browser-extension/command-controls.js',import.meta.url),'utf8');
const copy=value=>JSON.parse(JSON.stringify(value));
const tick=async()=>{for(let i=0;i<30;i++)await Promise.resolve();};
function fixture(){
 let now=0,id=0;const timers=new Map(),calls=[],busy=[],windowEvents=new Map();
 const document={activeElement:null};
 function element(tag){
  const node={tag,children:[],style:{},events:new Map(),dataset:{},hidden:false,disabled:false,className:'',textContent:'',value:'',captures:new Set(),
   append(...items){for(const item of items){this.children.push(item);item.parentElement=this;}},
   replaceChildren(...items){this.children=[];this.append(...items);},
   contains(target){return this===target||this.children.some(child=>child.contains(target));},
   setAttribute(name,value){this[name]=String(value);},getAttribute(name){return this[name]??null;},
   addEventListener(name,fn){if(!this.events.has(name))this.events.set(name,[]);this.events.get(name).push(fn);},
   getRootNode(){return document;},getBoundingClientRect(){return{left:0,width:100};},focus(){document.activeElement=this;},
   setPointerCapture(pointer){this.captures.add(pointer);},hasPointerCapture(pointer){return this.captures.has(pointer);},
   releasePointerCapture(pointer){this.captures.delete(pointer);fire(this,'lostpointercapture',{pointerId:pointer});},
   querySelectorAll(selector){const found=[];for(const child of this.children){if(child.tag===selector)found.push(child);found.push(...child.querySelectorAll(selector));}return found;},
   querySelector(selector){return this.querySelectorAll(selector)[0]||null;}
  };node.classList={add(name){node.className+=(node.className?' ':'')+name;}};Object.defineProperty(node,'isConnected',{get:()=>true});return node;
 }
 document.createElement=element;document.createElementNS=(_,tag)=>element(tag);
 const chrome={runtime:{sendMessage(message,callback){calls.push({message:copy(message),callback,time:now});}}};
 const sandbox={document,chrome,window:{addEventListener(name,fn){if(!windowEvents.has(name))windowEvents.set(name,[]);windowEvents.get(name).push(fn);}},Date:class extends Date{static now(){return now;}},setTimeout(fn,ms){timers.set(++id,{fn,at:now+ms});return id;},clearTimeout(id){timers.delete(id);},requestAnimationFrame:fn=>fn()};
 vm.runInNewContext(source,sandbox);
 const controls=sandbox.createPyshDeviceControls({context:element('button'),onBusy:value=>busy.push(value),onPresentation(){},onPane(){}});
 const root=controls.element,settings=root.children[0],volume={element:settings.children[0],input:settings.children[0].children[1].children[0],value:settings.children[0].children[0].children[1]},brightness={element:settings.children[1],input:settings.children[1].children[1].children[0],value:settings.children[1].children[0].children[1]},mute=settings.children[0].children[1].children[1],retry=root.children.at(-1).children[1];
 let state={language:'en',theme:'night',busy:false,audio:{available:true,ready:true,volume:30,mute:false,outputs:[{id:'speaker',active:true,label:'Speaker'}]},brightness:{available:true,value:70}};
 function fire(node,name,props={}){for(const fn of node.events.get(name)||[])fn({button:0,pointerId:1,clientX:0,preventDefault(){},...props});}
 function reply(call,result){if(result===undefined){const m=call.message;if(m.action==='controls-volume')state.audio.volume=m.value;else if(m.action==='controls-brightness')state.brightness.value=m.value;else if(m.action==='controls-mute')state.audio.mute=m.value;result={ok:true,controls:copy(state)};}call.callback(result);}
 async function advance(ms){const end=now+ms;while(true){const next=[...timers.entries()].filter(([,v])=>v.at<=end).sort((a,b)=>a[1].at-b[1].at)[0];if(!next)break;now=next[1].at;timers.delete(next[0]);next[1].fn();await tick();}now=end;await tick();}
 const init=async()=>{void controls.refresh();reply(calls.at(-1));await tick();calls.length=0;};
 const point=(setting,name,value)=>fire(setting.input,name,{clientX:setting===brightness?(value-1)/99*100:value});
 return{controls,root,volume,brightness,mute,retry,calls,busy,document,fire,reply,advance,init,point,state,blur(){for(const fn of windowEvents.get('blur')||[])fn();}};
}

for(const kind of ['volume','brightness'])test(`${kind} previews during drag, preserves draft on old acknowledgement and commits latest exactly once`,async()=>{
 const h=fixture();await h.init();const s=h[kind];s.input.focus();h.point(s,'pointerdown',20);
 assert.equal(s.value.textContent,'20%');assert.equal(s.input.value,'20');assert.equal(s.input.disabled,false);assert.equal(h.controls.busy(),true);assert.equal(h.mute.disabled,true);
 assert.deepEqual(h.calls[0].message,{action:'controls-'+kind,value:20,persist:false});
 h.point(s,'pointermove',85);assert.equal(s.value.textContent,'85%');await h.advance(500);assert.equal(h.calls.length,1,'one in flight');
 h.point(s,'pointerup',87);assert.equal(s.value.textContent,'87%');h.fire(s.input,'change');h.blur();assert.equal(h.calls.length,1);
 h.reply(h.calls[0]);await tick();assert.equal(s.value.textContent,'87%');assert.equal(s.input.disabled,false);assert.equal(h.document.activeElement,s.input);
 assert.deepEqual(h.calls[1].message,{action:'controls-'+kind,value:87,persist:true});h.reply(h.calls[1]);await tick();await h.advance(500);
 assert.equal(h.calls.length,2);assert.equal(s.value.textContent,'87%');assert.equal(h.controls.busy(),false);assert.equal(h.mute.disabled,false);assert.equal(h.busy.at(-1),false);
});

test('preview writes are at most eight per second, coalesce latest and final writes even identical value',async()=>{
 const h=fixture();await h.init();const s=h.volume;h.point(s,'pointerdown',10);h.reply(h.calls[0]);await tick();
 await h.advance(100);h.point(s,'pointermove',20);h.point(s,'pointermove',30);assert.equal(h.calls.length,1);assert.equal(s.value.textContent,'30%');
 await h.advance(25);assert.deepEqual(h.calls[1].message,{action:'controls-volume',value:30,persist:false});h.reply(h.calls[1]);await tick();
 await h.advance(125);h.point(s,'pointermove',40);h.reply(h.calls[2]);await tick();h.point(s,'pointerup',40);
 assert.deepEqual(h.calls.map(c=>c.message.persist),[false,false,false,true]);assert.deepEqual(h.calls.map(c=>c.time),[0,125,250,250]);assert.deepEqual(h.calls.at(-1).message,{action:'controls-volume',value:40,persist:true});h.reply(h.calls.at(-1));await tick();
});

for(const termination of ['pointercancel','lostpointercapture','blur'])test(`${termination} flushes last requested value once and never replays older preview`,async()=>{
 const h=fixture();await h.init();h.point(h.volume,'pointerdown',12);h.reply(h.calls[0]);await tick();h.point(h.volume,'pointermove',76);
 if(termination==='blur')h.blur();else h.fire(h.volume.input,termination,{pointerId:1});
 assert.deepEqual(h.calls.at(-1).message,{action:'controls-volume',value:76,persist:true});h.blur();h.fire(h.volume.input,'pointercancel');h.reply(h.calls.at(-1));await tick();await h.advance(500);
 assert.equal(h.calls.length,2);assert.equal(h.controls.busy(),false);
});

test('uncertain preview failure stops queue and readback requires deliberate final persistence retry',async()=>{
 const h=fixture();await h.init();h.point(h.volume,'pointerdown',20);h.point(h.volume,'pointermove',80);
 h.reply(h.calls[0],{ok:false,uncertain:true,error:'controls_unverified'});await tick();await h.advance(1000);assert.equal(h.calls.length,1);assert.equal(h.volume.input.disabled,true);
 h.fire(h.retry,'click');assert.deepEqual(h.calls.at(-1).message,{action:'controls-status'});h.state.audio.volume=80;h.reply(h.calls.at(-1));await tick();
 assert.equal(h.calls.length,2,'readback never replays mutation');assert.equal(h.retry.hidden,false,'runtime readback cannot prove final persistence');h.fire(h.retry,'click');assert.deepEqual(h.calls.at(-1).message,{action:'controls-volume',value:80,persist:true});h.reply(h.calls.at(-1));await tick();assert.equal(h.retry.hidden,true);
});

test('definite preview failure permits only explicit final retry with the latest target',async()=>{
 const h=fixture();await h.init();h.point(h.brightness,'pointerdown',25);h.point(h.brightness,'pointermove',55);h.reply(h.calls[0],{ok:false,definite:true});await tick();await h.advance(1000);assert.equal(h.calls.length,1);h.fire(h.retry,'click');assert.deepEqual(h.calls[1].message,{action:'controls-brightness',value:55,persist:true});h.reply(h.calls[1]);await tick();
});

test('timeout and late callback cannot revive preview or queued final write',async()=>{
 const h=fixture();await h.init();h.point(h.volume,'pointerdown',20);h.point(h.volume,'pointermove',90);h.point(h.volume,'pointerup',90);await h.advance(12000);assert.equal(h.calls.length,1);assert.equal(h.controls.busy(),false);assert.equal(h.volume.input.disabled,true);h.reply(h.calls[0]);await tick();await h.advance(1000);assert.equal(h.calls.length,1);
});

test('Return intent drops queued previews and final, ignores old acknowledgement and does not claim saved',async()=>{
 const h=fixture();await h.init();h.point(h.volume,'pointerdown',20);h.point(h.volume,'pointermove',92);h.point(h.volume,'pointerup',92);h.controls.returning(true);h.reply(h.calls[0]);await tick();await h.advance(1000);
 assert.equal(h.calls.length,1);assert.equal(h.controls.busy(),false);assert.equal(h.volume.input.disabled,true);h.controls.returning(false);h.fire(h.retry,'click');assert.equal(h.calls.at(-1).message.action,'controls-status');h.state.audio.volume=92;h.reply(h.calls.at(-1));await tick();assert.equal(h.retry.hidden,false);assert.equal(h.calls.length,2);
});

test('Return cancels throttle timer before an unsent preview can overwrite final intent',async()=>{
 const h=fixture();await h.init();h.point(h.volume,'pointerdown',20);h.reply(h.calls[0]);await tick();h.point(h.volume,'pointermove',99);h.controls.returning(true);await h.advance(500);assert.equal(h.calls.length,1);assert.equal(h.volume.input.hasPointerCapture(1),false);
});

test('keyboard range changes commit once with immediate numeric feedback and no preview',async()=>{
 const h=fixture();await h.init();h.volume.input.value='61';h.fire(h.volume.input,'change');assert.equal(h.volume.value.textContent,'61%');assert.deepEqual(h.calls[0].message,{action:'controls-volume',value:61,persist:true});h.fire(h.volume.input,'change');assert.equal(h.calls.length,1);h.reply(h.calls[0]);await tick();assert.equal(h.controls.busy(),false);
});

test('non-scalar controls retain exact action/value protocol and do not interleave with drag',async()=>{
 const h=fixture();await h.init();h.fire(h.mute,'click');assert.deepEqual(h.calls[0].message,{action:'controls-mute',value:true});h.reply(h.calls[0]);await tick();h.calls.length=0;h.point(h.volume,'pointerdown',35);h.fire(h.mute,'click');assert.equal(h.calls.length,1);assert.equal(h.calls[0].message.action,'controls-volume');
});
