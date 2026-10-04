import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
const source=name=>readFileSync(new URL('../app/browser-extension/'+name,import.meta.url),'utf8');
const tick=async()=>{for(let i=0;i<30;i++)await Promise.resolve();};
function harness(mode='ok'){
 let listener;const removed=[],responses=[],timers=new Map();let serial=0;
 const chrome={runtime:{id:'owned',getURL:path=>'chrome-extension://owned/'+path,onMessage:{addListener:fn=>listener=fn}},windows:{remove:(id,callback)=>{removed.push(id);if(mode==='throw')throw new Error('synthetic failure');if(mode==='timeout')return;if(mode==='error')chrome.runtime.lastError={message:'private native failure'};callback();delete chrome.runtime.lastError;}}};
 vm.runInNewContext(source('background.js').replace("importScripts('documentation-navigation.js');",source('documentation-navigation.js')),{chrome,URL,setTimeout:fn=>{timers.set(++serial,fn);return serial;},clearTimeout:id=>timers.delete(id)});
 return{removed,responses,timers,send(url,extra={}){return listener({action:'return'},{id:'owned',frameId:0,tab:{windowId:7},url,...extra},value=>responses.push(JSON.parse(JSON.stringify(value))));}};
}
for(const url of ['https://open-meteo.com/','https://open-meteo.com/en/docs','https://creativecommons.org/licenses/by/4.0/','chrome-extension://owned/documentation-return.html'])test('acknowledges owned window close '+url,async()=>{
 const h=harness();assert.equal(h.send(url),true);await tick();assert.deepEqual(h.removed,[7]);assert.deepEqual(h.responses,[{ok:true}]);assert.equal(h.timers.size,0);
});
for(const mode of ['error','throw','timeout'])test('return recovers from '+mode,async()=>{
 const h=harness(mode);assert.equal(h.send('https://open-meteo.com/'),true);if(mode==='timeout')[...h.timers.values()][0]();await tick();assert.deepEqual(h.removed,[7]);assert.deepEqual(h.responses,[{ok:false,error:'return_unavailable'}]);assert.equal(h.timers.size,0);
});
test('untrusted sender cannot close browser windows',async()=>{
 for(const [url,extra]of [['https://open-meteo.com.evil.example/',{}],['http://open-meteo.com/',{}],['https://open-meteo.com/',{frameId:1}],['https://open-meteo.com/',{id:'foreign'}]]){
  const h=harness();assert.equal(h.send(url,extra),undefined);await tick();assert.deepEqual(h.removed,[]);assert.deepEqual(h.responses,[]);
 }
});
