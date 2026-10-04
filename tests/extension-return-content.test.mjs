import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

// Return recovery contracts based on the keyboard content harness.
// Synthetic DOM/runtime only; no actual browser, native window or account access.
const directory=new URL('../app/browser-extension/',import.meta.url);
const source=name=>readFileSync(new URL(name,directory),'utf8');
const copy=value=>JSON.parse(JSON.stringify(value));
function content(surface,language='en',lateStatus=false){
 const sent=[],calls=[],nodes=[],listeners=new Map(),windowListeners=new Map(),timers=new Map(),ids=new Map();let timerId=0,throwReturn=false;
 function element(tag){
  const e={tag,tagName:tag.toUpperCase(),nodeType:1,children:[],style:{},events:new Map(),
   append(...children){for(const child of children){if(child.parentElement)child.parentElement.children=child.parentElement.children.filter(n=>n!==child);this.children.push(child);child.parentElement=this;}},
   after(child){assert.ok(this.parentElement);this.parentElement.append(child);},
   contains:child=>e===child||e.children.some(n=>n.contains(child)),
   setAttribute(name,value){this[name]=value;},getAttribute(name){return this[name]??null;},removeAttribute(name){delete this[name];},
   addEventListener(name,fn){this.events.set(name,fn);},
   attachShadow(options){assert.equal(options.mode,'closed');this.shadow=element('shadow');return this.shadow;}
  };Object.defineProperty(e,'isConnected',{get:()=>Boolean(e.parentElement)||e===document.documentElement});nodes.push(e);return e;
 }
 const document={documentElement:element('html'),createElement:element,activeElement:null,addEventListener:(name,fn)=>listeners.set(name,fn),getElementById:id=>ids.get(id)};
 if(surface==='recovery'){for(const id of ['title','message','return']){const e=element(id==='return'?'button':id==='title'?'h1':'p');ids.set(id,e);document.documentElement.append(e);}}
 const chrome={runtime:{sendMessage(message,callback){sent.push(copy(message));calls.push({message:copy(message),callback});if(message.action==='return'&&throwReturn){throwReturn=false;throw new Error('Synthetic transport failure');}if(message.action==='status'&&!lateStatus)callback({ok:true,language});}}};
 const window={innerWidth:800,addEventListener:(name,fn)=>windowListeners.set(name,fn)};
 const location={href:'https://open-meteo.com/en/licence',assign:()=>{throw new Error('No navigation expected');}};
 const filename={service:'return.js',documentation:'documentation.js',recovery:'documentation-return.js'}[surface];
 vm.runInNewContext(source(filename),{document,chrome,window,location,URL,setTimeout:(fn,ms)=>{timers.set(++timerId,{fn,ms});return timerId;},clearTimeout:id=>timers.delete(id)});
 const back=surface==='recovery'?ids.get('return'):nodes.find(n=>n.tag==='button'&&(surface==='service'?n.textContent==='← Pi Smart Hub':n.textContent.includes('PySH')));
 const feedback=nodes.find(n=>n.role==='status');
 const click=node=>node.events.get('click')({preventDefault(){},stopPropagation(){},stopImmediatePropagation(){}});
 function runTimers(maxDelay){for(const[id,timer]of[...timers])if(timer.ms<=maxDelay&&timers.has(id)){timers.delete(id);timer.fn();}}
 function reply(call,result,lastError=false){if(lastError)chrome.runtime.lastError={message:'Synthetic forbidden raw error'};try{call.callback(result);}finally{delete chrome.runtime.lastError;}}
 return{surface,language,back,feedback,nodes,sent,calls,timers,chrome,click,runTimers,reply,returns:()=>calls.filter(c=>c.message.action==='return'),failNextReturn:()=>{throwReturn=true;}};
}
function pending(h){assert.equal(h.back.disabled,true);assert.equal(h.back['aria-busy'],'true');assert.equal(h.back.textContent,h.language==='ro'?'Se revine…':'Returning…');}
function failure(h){assert.equal(h.back.disabled,false);assert.equal(h.back['aria-busy'],'false');assert.equal(h.back.textContent,h.language==='ro'?'Reîncearcă revenirea':'Retry return');assert.equal(h.feedback.textContent,h.language==='ro'?'Revenirea la PySH nu a reușit. Reîncearcă.':'Could not return to PySH. Try again.');if(h.surface==='recovery')assert.equal(h.feedback.hidden,false);else assert.equal(h.feedback.style.display,'block');assert.ok(!h.feedback.textContent.includes('Synthetic forbidden'));}
function success(h){assert.equal(h.back.disabled,false);assert.equal(h.back['aria-busy'],'false');assert.ok(!h.back.textContent.includes('Retry')&&!h.back.textContent.includes('Reîncearcă'));if(h.surface==='recovery')assert.equal(h.feedback.hidden,true);else assert.equal(h.feedback.style.display,'none');assert.equal([...h.timers.values()].filter(t=>t.ms===5000).length,0);}
for(const language of ['en','ro'])for(const surface of ['documentation','recovery','service']){
 test(`${surface} ${language} synchronous duplicate Return stays pending until actual acknowledgement`,()=>{const h=content(surface,language);h.click(h.back);h.click(h.back);assert.equal(h.returns().length,1);pending(h);assert.match(h.back.style.cssText||'',surface==='service'?/min-height:52px/:/min-height:48px|^$/);h.reply(h.returns()[0],{ok:true});success(h);});
 test(`${surface} ${language} callback runtime.lastError overrides a misleading positive reply and Retry is usable`,()=>{const h=content(surface,language);h.click(h.back);h.reply(h.returns()[0],{ok:true},true);failure(h);h.click(h.back);h.click(h.back);assert.equal(h.returns().length,2);pending(h);h.reply(h.returns()[1],{ok:true});success(h);});
 test(`${surface} ${language} synchronous sendMessage exception exposes localized Retry without leaking timeout`,()=>{const h=content(surface,language);h.failNextReturn();h.click(h.back);failure(h);assert.equal([...h.timers.values()].filter(t=>t.ms===5000).length,0);h.click(h.back);pending(h);h.reply(h.returns()[1],{ok:true});success(h);});
 test(`${surface} ${language} absent callback times out and old callback cannot settle a newer Retry`,()=>{const h=content(surface,language);h.click(h.back);h.runTimers(4999);pending(h);h.runTimers(5000);failure(h);const old=h.returns()[0];h.click(h.back);pending(h);h.reply(old,{ok:true});pending(h);assert.equal(h.returns().length,2);h.reply(h.returns()[1],{ok:false,error:'return_unavailable'});failure(h);h.reply(old,{ok:true});failure(h);h.click(h.back);h.reply(h.returns()[2],{ok:true});success(h);});
 test(`${surface} ${language} undefined acknowledgement is failure rather than claimed successful close`,()=>{const h=content(surface,language);h.click(h.back);h.reply(h.returns()[0],undefined);failure(h);});
 test(`${surface} ${language} late status language reply preserves pending and failed Return ownership`,()=>{const h=content(surface,'en',true);h.click(h.back);const status=h.calls.find(c=>c.message.action==='status');h.reply(status,{ok:true,language});h.language=language;pending(h);h.reply(h.returns()[0],{ok:false});failure(h);h.reply(status,{ok:true,language});failure(h);});
}
for(const language of ['en','ro'])test(`service ${language} Return pending/error resists auto-retraction and late keyboard feedback`,()=>{
 const h=content('service',language),host=h.nodes.find(n=>n.tag==='pi-hub-return'),controls=host.shadow.children.find(n=>n.tag==='div'),keyboard=h.nodes.find(n=>n.tag==='button'&&n!==h.back&&n.textContent===(language==='ro'?'Tastatură':'Keyboard'));
 h.click(keyboard);const keyboardCall=h.calls.find(c=>c.message.action==='show');h.click(h.back);h.runTimers(4000);pending(h);assert.equal(controls.style.display,'flex');h.reply(h.returns()[0],{ok:false});failure(h);const errorText=h.feedback.textContent;h.reply(keyboardCall,{ok:false});assert.equal(h.feedback.textContent,errorText);h.runTimers(4000);assert.equal(controls.style.display,'flex');failure(h);h.click(h.back);h.reply(h.returns()[1],{ok:true});success(h);h.runTimers(4000);assert.equal(controls.style.display,'none');
});
