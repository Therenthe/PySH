import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const directory=new URL('../app/browser-extension/',import.meta.url),source=name=>readFileSync(new URL(name,directory),'utf8');
const tick=async()=>{for(let i=0;i<30;i++)await Promise.resolve();};
function event(){const listeners=new Set();return{addListener:fn=>listeners.add(fn),removeListener:fn=>listeners.delete(fn),emit:value=>{for(const fn of [...listeners])fn(value);},listeners};}
function fixture({holdRemove=false}={}){
 const ports=[],removed=[],removalReplies=[],timers=new Map(),onMessage=event(),chrome={runtime:{id:'owned',onMessage,getURL:path=>'chrome-extension://owned/'+path,connectNative(){const port={onMessage:event(),onDisconnect:event(),sent:[],closed:false,postMessage(message){this.sent.push(JSON.parse(JSON.stringify(message)));},disconnect(){this.closed=true;this.onDisconnect.emit();}};ports.push(port);return port;}},windows:{update:async()=>{},remove:(id,done)=>{removed.push(id);if(holdRemove)removalReplies.push(done);else done();}}};
 let timerId=0;
 vm.runInNewContext(source('background.js').replace("importScripts('documentation-navigation.js');",source('documentation-navigation.js')),{chrome,URL,setTimeout:(run,delay)=>{timers.set(++timerId,{run,delay});return timerId;},clearTimeout:id=>timers.delete(id)});
 const listener=[...onMessage.listeners][0],sender=url=>({id:'owned',frameId:0,tab:{windowId:7},url});
 const request=(message,from=sender('https://www.netflix.com/'))=>{const replies=[];return{keepAlive:listener(message,from,reply=>replies.push(JSON.parse(JSON.stringify(reply)))),replies};};
 return{ports,removed,sender,request,timerCount:()=>timers.size,finishRemove(failed=false){chrome.runtime.lastError=failed?{message:'fixture failure'}:undefined;removalReplies.shift()();chrome.runtime.lastError=undefined;},timeout(delay){for(const [id,timer]of [...timers])if(timer.delay===delay){timers.delete(id);timer.run();}}};
}
test('typed controls are accepted only from supported service main frames',async()=>{
 const h=fixture();
 for(const url of ['https://open-meteo.com/','https://creativecommons.org/','https://accounts.google.com/','https://netflix.com.evil.invalid/'])assert.equal(h.request({action:'controls-volume',value:50},h.sender(url)).keepAlive,undefined);
 for(const message of [{action:'controls-volume',value:true},{action:'controls-brightness',value:0},{action:'controls-output',value:'x',url:'file:///private'},{action:'controls-status',value:1},{action:'controls-mute',value:1}])assert.equal(h.request(message).keepAlive,undefined);
 assert.equal(h.request({action:'controls-status'},{...h.sender('https://www.youtube.com/'),frameId:1}).keepAlive,undefined);
 await tick();assert.equal(h.ports.length,0);
 const accepted=h.request({action:'controls-volume',value:50});assert.equal(accepted.keepAlive,true);await tick();assert.deepEqual(h.ports[0].sent,[{action:'controls-volume',value:50}]);h.ports[0].onMessage.emit({ok:true,controls:{busy:false}});await tick();assert.equal(accepted.replies[0].ok,true);
});
test('Return cancels queued mutations and closes only after owned destination acknowledgment',async()=>{
 const h=fixture(),read=h.request({action:'controls-status'});await tick();
 const stale=h.request({action:'controls-mute',value:true}),returning=h.request({action:'return-home'});await tick();
 assert.deepEqual(h.ports[0].sent,[{action:'controls-status'}]);assert.deepEqual(h.removed,[]);
 h.ports[0].onMessage.emit({ok:true,controls:{busy:false}});await tick();
 assert.equal(read.replies[0].ok,true);assert.equal(stale.replies[0].ok,false);assert.deepEqual(h.ports[0].sent,[{action:'controls-status'},{action:'home'}]);assert.deepEqual(h.removed,[]);
 h.ports[0].onMessage.emit({ok:true});await tick();assert.deepEqual(h.removed,[7]);assert.deepEqual(returning.replies,[{ok:true}]);
});

test('a Return retry shares the operation queued behind a ten-second controls timeout',async()=>{
 const h=fixture(),read=h.request({action:'controls-status'});await tick();
 const first=h.request({action:'return-home'}),retry=h.request({action:'return-home'});
 h.timeout(10000);await tick();
 assert.equal(read.replies[0].ok,false);
 assert.equal(h.ports.length,2);assert.deepEqual(h.ports[1].sent,[{action:'home'}]);
 h.ports[1].onMessage.emit({ok:true});await tick();
 assert.deepEqual(h.removed,[7]);assert.equal(h.ports.length,2);
 assert.deepEqual(first.replies,[{ok:true}]);assert.deepEqual(retry.replies,[{ok:true}]);
});

test('only the latest different Return target is dispatched while the operation is queued',async()=>{
 const h=fixture();h.request({action:'controls-status'});await tick();
 const first=h.request({action:'return-home'}),radio=h.request({action:'return-radio'}),media=h.request({action:'return-media'});
 h.ports[0].onMessage.emit({ok:true,controls:{busy:false}});await tick();
 assert.deepEqual(h.ports[0].sent,[{action:'controls-status'},{action:'media'}]);
 h.ports[0].onMessage.emit({ok:true});await tick();
 assert.deepEqual(h.removed,[7]);assert.equal(h.ports.length,1);
 for(const request of [first,radio,media])assert.deepEqual(request.replies,[{ok:true}]);
});

test('a different target cannot replace a Return already dispatched to the native host',async()=>{
 const h=fixture(),first=h.request({action:'return-radio'});await tick();
 const retry=h.request({action:'return-radio'}),different=h.request({action:'return-media'});await tick();
 assert.deepEqual(different.replies,[{ok:false,error:'return_unavailable'}]);
 assert.deepEqual(h.ports[0].sent,[{action:'radio'}]);
 h.ports[0].onMessage.emit({ok:true});await tick();
 assert.deepEqual(h.removed,[7]);assert.equal(h.ports.length,1);
 assert.deepEqual(first.replies,[{ok:true}]);assert.deepEqual(retry.replies,[{ok:true}]);
});

test('closing commits once and prevents controls or keyboard requests from dispatching afterwards',async()=>{
 const h=fixture({holdRemove:true}),first=h.request({action:'return-home'});await tick();
 h.ports[0].onMessage.emit({ok:true});await tick();assert.deepEqual(h.removed,[7]);
 const retry=h.request({action:'return-home'}),different=h.request({action:'return-radio'}),control=h.request({action:'controls-mute',value:true}),keyboard=h.request({action:'show'});
 await tick();assert.deepEqual(different.replies,[{ok:false,error:'return_unavailable'}]);
 assert.equal(h.ports.length,1);assert.deepEqual(control.replies,[]);
 h.finishRemove();await tick();
 assert.equal(h.ports.length,1);assert.deepEqual(h.removed,[7]);
 assert.deepEqual(first.replies,[{ok:true}]);assert.deepEqual(retry.replies,[{ok:true}]);
 assert.equal(control.replies[0].ok,false);assert.equal(keyboard.replies[0].ok,false);
});

test('a newer window Return invalidates queued native dispatch without cancelling the newest operation',async()=>{
 const h=fixture();h.request({action:'controls-status'});await tick();
 const stale=h.request({action:'return-home'}),newest=h.request({action:'return-radio'},{...h.sender('https://www.netflix.com/'),tab:{windowId:8}});
 h.ports[0].onMessage.emit({ok:true,controls:{busy:false}});await tick();
 assert.deepEqual(stale.replies,[{ok:false,error:'return_unavailable'}]);
 assert.deepEqual(h.ports[0].sent,[{action:'controls-status'},{action:'radio'}]);
 h.ports[0].onMessage.emit({ok:true});await tick();assert.deepEqual(h.removed,[8]);assert.deepEqual(newest.replies,[{ok:true}]);
});

test('a superseded in-flight acknowledgment cannot close its window',async()=>{
 const h=fixture(),stale=h.request({action:'return-home'});await tick();
 const newest=h.request({action:'return-radio'},{...h.sender('https://www.netflix.com/'),tab:{windowId:8}});
 h.ports[0].onMessage.emit({ok:true});await tick();
 assert.deepEqual(stale.replies,[{ok:false,error:'return_unavailable'}]);assert.deepEqual(h.removed,[]);
 assert.deepEqual(h.ports[0].sent,[{action:'home'},{action:'radio'}]);
 h.ports[0].onMessage.emit({ok:true});await tick();assert.deepEqual(h.removed,[8]);assert.deepEqual(newest.replies,[{ok:true}]);
});

test('a failed destination acknowledgment clears Return so an explicit retry can succeed',async()=>{
 const h=fixture(),first=h.request({action:'return-home'});await tick();
 h.ports[0].onMessage.emit({ok:false});await tick();assert.deepEqual(first.replies,[{ok:false,error:'return_unavailable'}]);assert.deepEqual(h.removed,[]);
 const retry=h.request({action:'return-media'});await tick();assert.deepEqual(h.ports[0].sent,[{action:'home'},{action:'media'}]);
 h.ports[0].onMessage.emit({ok:true});await tick();assert.deepEqual(h.removed,[7]);assert.deepEqual(retry.replies,[{ok:true}]);
});

test('an unacknowledged window close permits only same-target close recovery, never another destination',async()=>{
 const h=fixture({holdRemove:true}),first=h.request({action:'return-home'});await tick();
 h.ports[0].onMessage.emit({ok:true});await tick();h.finishRemove(true);await tick();
 assert.deepEqual(first.replies,[{ok:false,error:'return_unavailable'}]);
 const different=h.request({action:'return-radio'});await tick();assert.deepEqual(different.replies,[{ok:false,error:'return_unavailable'}]);
 const retry=h.request({action:'return-home'});await tick();
 assert.equal(h.ports.length,1);assert.deepEqual(h.removed,[7,7]);
 h.finishRemove();await tick();assert.deepEqual(retry.replies,[{ok:true}]);
 const late=h.request({action:'return-home'});await tick();assert.deepEqual(late.replies,[{ok:true}]);assert.deepEqual(h.removed,[7,7]);
});

test('full Return promptly cancels the owning keyboard and queued Show without waiting for timeout',async()=>{
 const h=fixture(),first=h.request({action:'show'}),queued=h.request({action:'show'});await tick();
 const returning=h.request({action:'return'});await tick();
 assert.deepEqual(h.removed,[7]);assert.equal(h.ports.length,1);assert.equal(h.ports[0].closed,true);
 assert.deepEqual(first.replies,[{ok:false,error:'keyboard_unavailable'}]);
 assert.deepEqual(queued.replies,[{ok:false,error:'keyboard_unavailable'}]);
 assert.deepEqual(returning.replies,[{ok:true}]);assert.equal(h.timerCount(),0);
});

test('full Return preserves an active device write and deduplicates while waiting for its acknowledgment',async()=>{
 const h=fixture(),write=h.request({action:'controls-volume',value:60});await tick();
 const first=h.request({action:'return'}),retry=h.request({action:'return'}),queued=h.request({action:'show'});await tick();
 assert.deepEqual(h.removed,[]);assert.equal(h.ports[0].closed,false);assert.deepEqual(write.replies,[]);
 h.ports[0].onMessage.emit({ok:true,controls:{busy:false}});await tick();
 assert.deepEqual(h.removed,[7]);assert.equal(h.ports.length,1);assert.equal(h.ports[0].closed,true);
 assert.equal(write.replies[0].ok,true);assert.deepEqual(first.replies,[{ok:true}]);assert.deepEqual(retry.replies,[{ok:true}]);
 assert.equal(queued.replies[0].ok,false);assert.equal(h.timerCount(),0);
});
