import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {stripTypeScriptTypes} from 'node:module';
const source=await readFile(new URL('../app/ui/src/localMediaApi.ts',import.meta.url),'utf8');
const compiled=stripTypeScriptTypes(source,{mode:'transform'});
const {LocalVideoSession,validateVideoSession,readVideoObservation,continueItems}=await import(`data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`);
const identity='m1_'+'a'.repeat(64),sid='a'.repeat(32),session={session_id:sid,media_identity:identity,resume_position_s:12,stream_url:`/api/media/file?session_id=${sid}`};
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};};
test('session response accepts only the exact owner stream and requested identity',()=>{
 assert.equal(validateVideoSession(session,identity),session);
 for(const patch of [{stream_url:'https://outside.invalid/file'},{stream_url:session.stream_url+'&path=other'},{stream_url:session.stream_url+'#fragment'},{session_id:'../different'},{media_identity:'m1_'+'b'.repeat(64)},{resume_position_s:NaN},{resume_position_s:true},{resume_position_s:-1}])assert.throws(()=>validateVideoSession({...session,...patch},identity),/invalid_video_session/);
});
test('only real finite video observations are progress; no fabricated unknown-duration zero',()=>{
 for(const duration of [NaN,Infinity,0,-1])assert.equal(readVideoObservation({currentTime:4,duration,ended:false}),null);
 assert.equal(readVideoObservation({currentTime:NaN,duration:40,ended:false}),null);
 assert.deepEqual(readVideoObservation({currentTime:42,duration:40,ended:true}),{position_s:40,duration_s:40,ended:true});
});
test('early final close sends absolutely no observation body',async()=>{
 const calls=[],owner=new LocalVideoSession(session,async(...args)=>calls.push(args));
 owner.bind(()=>null,()=>{});await owner.close();
 assert.equal(calls.length,1);assert.equal(calls[0][1].method,'DELETE');assert.equal('body' in calls[0][1],false);
});
test('close pauses first and atomically captures the latest element observation once',async()=>{
 const calls=[],hold=deferred();let position=3,paused=false;
 const owner=new LocalVideoSession(session,async(path,init)=>{calls.push({path,init});await hold.promise;});
 owner.bind(()=>({position_s:position,duration_s:90,ended:false}),()=>{paused=true;position=17;});
 const first=owner.close(),second=owner.close();assert.equal(first,second);assert.equal(paused,true);await Promise.resolve();position=30;hold.resolve();await first;
 assert.equal(calls.length,1);assert.deepEqual(JSON.parse(calls[0].init.body),{sequence:1,position_s:17,duration_s:90,ended:false});
 await owner.update();await owner.update(true);await owner.close();assert.equal(calls.length,1);
});
test('inflight PATCH settles before final DELETE; queued stale progress is dropped',async()=>{
 const calls=[],hold=deferred();let position=4;
 const owner=new LocalVideoSession(session,async(_path,init)=>{calls.push(init);if(init.method==='PATCH')await hold.promise;});
 owner.bind(()=>({position_s:position,duration_s:100,ended:false}),()=>{});
 const active=owner.update();await Promise.resolve();position=5;const queued=owner.update();position=19;const close=owner.close();await Promise.resolve();assert.equal(calls.length,1);
 hold.resolve();await Promise.all([active,queued,close]);assert.deepEqual(calls.map(call=>call.method),['PATCH','DELETE']);
 assert.deepEqual(JSON.parse(calls[1].body),{sequence:2,position_s:19,duration_s:100,ended:false});
});
test('heartbeat renews without position fields and sequence increases',async()=>{
 const calls=[],owner=new LocalVideoSession(session,async(_path,init)=>calls.push(init));
 owner.bind(()=>null,()=>{});await owner.update(true);await owner.update();await owner.close();
 assert.deepEqual(JSON.parse(calls[0].body),{sequence:1,heartbeat:true});assert.equal(calls.length,2);assert.equal('body' in calls[1],false);
});
test('failed final persistence remains retryable with the same captured observation',async()=>{
 const calls=[];let fail=true,position=7;
 const owner=new LocalVideoSession(session,async(_path,init)=>{calls.push(init);if(fail){fail=false;throw new Error('history_write_failed');}});
 owner.bind(()=>({position_s:position,duration_s:80,ended:false}),()=>{});
 await assert.rejects(owner.close(),/history_write_failed/);position=1;await owner.close();assert.equal(calls.length,2);assert.equal(calls[0].body,calls[1].body);
});
test('lost final acknowledgement cannot close or mutate a newer descriptor',async()=>{
 const calls=[];let first=true;
 const owner=new LocalVideoSession(session,async(path,init)=>{calls.push({path,init});if(first){first=false;throw new Error('timeout');}throw new Error('stale_video_session');});
 owner.bind(()=>({position_s:7,duration_s:80,ended:false}),()=>{});
 await assert.rejects(owner.close(),/timeout/);await owner.close();await owner.update();
 assert.equal(calls.length,2);assert.ok(calls.every(call=>call.path.endsWith(sid)&&call.init.method==='DELETE'));
});
test('history rejects malformed response and excludes invalid records',()=>{
 assert.throws(()=>continueItems({ok:true}),/media_unavailable/);
 const item={path:'/owned/a.webm',name:'A',media_identity:identity,position_s:3,duration_s:30,updated_at:1};
 assert.deepEqual(continueItems({items:[item,{...item,media_identity:'unknown'},{...item,duration_s:0},{...item,position_s:true}]}),[item]);
 assert.equal(continueItems({items:Array(30).fill(item)}).length,12);
});
test('explicit discard after failed save sends absent-body owner DELETE and no fake progress',async()=>{
 const calls=[],owner=new LocalVideoSession(session,async(path,init)=>{calls.push({path,init});if(init.body)throw new Error('history_write_failed');});
 owner.bind(()=>({position_s:18,duration_s:80,ended:false}),()=>{});
 await assert.rejects(owner.close(),/history_write_failed/);await owner.discard();
 assert.deepEqual(calls.map(call=>call.init.method),['DELETE','DELETE']);assert.equal('body' in calls[1].init,false);assert.ok(calls.every(call=>call.path.endsWith(sid)));await owner.close();await owner.update();assert.equal(calls.length,2);
});
test('discard deduplicates overlapping requests and waits for owned PATCH ordering',async()=>{
 const calls=[],hold=deferred(),owner=new LocalVideoSession(session,async(_path,init)=>{calls.push(init);if(init.method==='PATCH')await hold.promise;});
 owner.bind(()=>({position_s:18,duration_s:80,ended:false}),()=>{});
 const patch=owner.update();await Promise.resolve();const first=owner.discard(),second=owner.discard();assert.equal(first,second);assert.equal(owner.close(),first);await owner.update();assert.equal(calls.length,1);
 hold.resolve();await Promise.all([patch,first]);assert.equal(calls.length,2);assert.equal(calls[1].method,'DELETE');assert.equal('body' in calls[1],false);
});
test('failed discard stays owned until a separate explicit local abandon',async()=>{
 const calls=[],owner=new LocalVideoSession(session,async(_path,init)=>{calls.push(init);throw new Error('timeout');});let paused=0;
 owner.bind(()=>({position_s:18,duration_s:80,ended:false}),()=>paused++);
 await assert.rejects(owner.discard(),/timeout/);assert.equal(owner.unavailable,true);assert.equal(calls.length,1);
 owner.abandon();await owner.close();await owner.discard();await owner.update(true);assert.equal(calls.length,1);assert.equal(paused,2);
});
test('Save retry after a failed discard reads current real observation instead of cached final',async()=>{
 const calls=[];let position=18,offline=true;
 const owner=new LocalVideoSession(session,async(_path,init)=>{calls.push(init);if(offline)throw new Error('timeout');});
 owner.bind(()=>({position_s:position,duration_s:80,ended:false}),()=>{});
 await assert.rejects(owner.close(),/timeout/);await assert.rejects(owner.discard(),/timeout/);position=21;offline=false;await owner.close();
 assert.equal('body' in calls[1],false);assert.deepEqual(JSON.parse(calls[2].body),{sequence:2,position_s:21,duration_s:80,ended:false});
});
test('local abandon blocks an already queued final request before dispatch',async()=>{
 const calls=[],owner=new LocalVideoSession(session,async(...args)=>calls.push(args));
 owner.bind(()=>({position_s:18,duration_s:80,ended:false}),()=>{});const final=owner.close();owner.abandon();await final;assert.equal(calls.length,0);
});
