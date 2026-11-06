import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {stripTypeScriptTypes} from 'node:module';
const code=stripTypeScriptTypes(readFileSync(new URL('../app/ui/src/liveLevel.ts',import.meta.url),'utf8'),{mode:'transform'});
const {LiveLevel}=await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
test('live scalar replaces unsent previews and preserves final persistence after an identical preview',async()=>{
 const writes=[];let release;const first=new Promise(r=>release=r),queue=new LiveLevel(async(value,persist)=>{writes.push({value,persist});if(writes.length===1)await first;return{value};});
 const initial=queue.set(20,false);await sleep(10);for(let i=21;i<80;i++)void queue.set(i,false);const final=queue.set(80,true);assert.deepEqual(writes,[{value:20,persist:false}]);release();await initial;await final;assert.deepEqual(writes,[{value:20,persist:false},{value:80,persist:true}]);
 const again=queue.set(80,true);await again;assert.deepEqual(writes.at(-1),{value:80,persist:true});
});
test('an uncertain scalar write drops unsent mutations instead of replaying them',async()=>{
 let release;const pending=new Promise(r=>release=r),writes=[],queue=new LiveLevel(async(value,persist)=>{writes.push({value,persist});await pending;return null;});
 const first=queue.set(20,false);await sleep(10);const final=queue.set(90,true);release();assert.equal(await first,null);assert.equal(await final,null);await sleep(150);assert.equal(writes.length,1);
});
test('continuous input has bounded preview rate and a serial trailing commit',async()=>{
 const times=[];let running=0,maximum=0;const queue=new LiveLevel(async(value,persist)=>{maximum=Math.max(maximum,++running);times.push({at:performance.now(),persist,value});await sleep(5);running--;return{value};});
 for(let i=0;i<35;i++){void queue.set(i,false);await sleep(5);}await queue.set(35,true);
 assert.equal(maximum,1);const previews=times.filter(t=>!t.persist);assert.ok(previews.length>=1);for(let i=1;i<previews.length;i++)assert.ok(previews[i].at-previews[i-1].at>=100,'preview rate exceeded');assert.deepEqual(times.at(-1).value,35);assert.equal(times.at(-1).persist,true);
});
