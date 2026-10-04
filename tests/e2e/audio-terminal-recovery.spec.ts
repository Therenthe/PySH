import {expect,test,type Page,type Locator} from '@playwright/test';

// Control/lifecycle fixtures only: this file does not certify media decoding or sound.
async function fixture(page:Page,ro:boolean,theme:string,mode:'reject'|'accepted'|'success'='reject',long=false){
 const label=long?'OUTPUT_'+('W'.repeat(400)):'Test speaker';
 const state:any={appliance:true,serviceMode:false,preferences:{language:ro?'ro':'en',theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0},network:{available:true},bluetooth:{available:true,devices:[],prompts:[]},player:{state:'idle'},weather:{},audio:{available:true,ready:true,volume:30,mute:false,outputs:[{id:11,description:label,active:true},{id:22,description:label+' second',active:false}]}};
 const writes:any[]=[];let release!:()=>void,failRead=false;const gate=new Promise<void>(r=>release=r);
 await page.addInitScript(()=>{
  Object.defineProperty(HTMLMediaElement.prototype,'duration',{get:()=>20});
  Object.defineProperty(HTMLMediaElement.prototype,'paused',{get:()=>true});
  HTMLMediaElement.prototype.play=function(){return Promise.resolve();};HTMLMediaElement.prototype.pause=function(){};
 });
 await page.route('**/api/**',async route=>{
  const req=route.request(),path=new URL(req.url()).pathname;let json:any={ok:true};
  if(path==='/api/media/file')return; // Keep decoder input pending; only application controls are under test.
  if(path==='/api/session')json={token:'fixture'};else if(path==='/api/state'){if(failRead){failRead=false;await route.fulfill({status:503,json:{error:'backend_unavailable'}});return;}json=state;}
  else if(path==='/api/media')json={path:'',items:[{name:'control-fixture.webm',path:'/approved/control-fixture.webm',kind:'video'}]};
  else if(path==='/api/audio'&&req.method()==='POST'){
   const body=req.postDataJSON();writes.push(body);if(writes.length===1){await gate;if(mode==='reject'){await route.fulfill({status:503,json:{error:'audio_unavailable'}});return;}}
   if('output'in body)state.audio.outputs.forEach((o:any)=>o.active=o.id===body.output);if('volume'in body)state.audio.volume=body.volume;if('mute'in body)state.audio.mute=body.mute;if(mode==='accepted'&&writes.length===1)failRead=true;
  }else if(path==='/api/exit'){state.serviceMode=true;}else if(path==='/api/service/return'){state.serviceMode=false;}else if(path==='/api/preferences'){Object.assign(state.preferences,req.postDataJSON());json=state.preferences;}
  await route.fulfill({json});
 });
 await page.goto('/');return{state,writes,release,label};
}
async function hit(control:Locator){
 await control.scrollIntoViewIfNeeded();const b=(await control.boundingBox())!;expect(b.width).toBeGreaterThanOrEqual(48);expect(b.height).toBeGreaterThanOrEqual(48);expect(b.x).toBeGreaterThanOrEqual(0);expect(b.y).toBeGreaterThanOrEqual(0);expect(b.x+b.width).toBeLessThanOrEqual(800);expect(b.y+b.height).toBeLessThanOrEqual(480);expect(await control.evaluate(el=>{const b=el.getBoundingClientRect();return el.contains(document.elementFromPoint(b.x+b.width/2,b.y+b.height/2));})).toBe(true);
}
async function video(page:Page,ro:boolean){
 await page.locator('.main-nav button').nth(2).tap();await page.locator('.media-item').tap();await expect(page.locator('.video-overlay')).toBeVisible();await page.locator('video').evaluate(v=>{v.dispatchEvent(new Event('loadedmetadata'));v.dispatchEvent(new Event('canplay'));});return page.getByRole('slider',{name:ro?'Volum':'Volume',exact:true});
}
async function pendingOutput(page:Page,ro:boolean){
 await page.locator('.rail-bottom button').last().tap();const dialog=page.getByRole('dialog',{name:'Audio',exact:true});await dialog.locator('.modal-list button').last().tap();await expect(dialog.getByRole('status')).toBeVisible();await dialog.locator('header').getByRole('button',{name:ro?'Închide':'Close',exact:true}).tap();
}
for(const theme of ['ink','night']){
 test(`Terminal audio ${theme}: late old background state cannot replace confirmed output or volume`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro');await page.clock.install();const f=await fixture(page,ro,theme,'success');const old=JSON.parse(JSON.stringify(f.state));let started=false,finished=false,releaseOld!:()=>void;const oldGate=new Promise<void>(r=>releaseOld=r);
  await page.route('**/api/state',async route=>{if(!started){started=true;await oldGate;await route.fulfill({json:old});finished=true;}else await route.fulfill({json:f.state});});
  await page.clock.runFor(2600);await expect.poll(()=>started).toBe(true);f.release();await page.locator('.rail-bottom button').last().tap();const dialog=page.getByRole('dialog',{name:'Audio',exact:true});await dialog.locator('.modal-list button').last().tap();await expect(dialog.locator('.modal-list button').last().locator('svg')).toHaveCount(2);
  const slider=dialog.getByRole('slider'),b=(await slider.boundingBox())!;await slider.tap({position:{x:b.width*.65,y:b.height*.5}});await expect(slider).toHaveValue('65');expect(f.writes).toEqual([{output:22},{volume:65}]);releaseOld();await expect.poll(()=>finished).toBe(true);await page.clock.runFor(100);
  await expect(slider).toHaveValue('65');await expect(dialog.locator('.modal-list button').last().locator('svg')).toHaveCount(2);await expect(dialog.locator('.modal-list button').first().locator('svg')).toHaveCount(1);expect(f.writes).toEqual([{output:22},{volume:65}]);
 });
 test(`Terminal audio ${theme}: video held volume survives clock and poll and commits once`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro');await page.clock.install();const f=await fixture(page,ro,theme),slider=await video(page,ro),node=(await slider.elementHandle())!,b=(await slider.boundingBox())!;
  await page.mouse.move(b.x+b.width*.3,b.y+b.height/2);await page.mouse.down();await page.mouse.move(b.x+b.width*.8,b.y+b.height/2,{steps:10});await expect(slider).toHaveValue('80');await page.clock.runFor(2700);expect(await node.evaluate(el=>el.isConnected)).toBe(true);expect(await node.evaluate(el=>(el as HTMLInputElement).hasPointerCapture(1))).toBe(true);await expect(slider).toHaveValue('80');expect(f.writes).toEqual([]);await page.mouse.up();await expect.poll(()=>f.writes.length).toBe(1);expect(f.writes).toEqual([{volume:80}]);f.release();await expect(page.locator('.video-audio-recovery').getByRole('alert')).toBeVisible();
 });
 for(const cause of ['pointercancel','blur','close'] as const)test(`Terminal audio ${theme}: video volume ${cause} cancels without mutation`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme),slider=await video(page,ro),b=(await slider.boundingBox())!;await page.mouse.move(b.x+b.width*.3,b.y+b.height/2);await page.mouse.down();await page.mouse.move(b.x+b.width*.8,b.y+b.height/2,{steps:8});await expect(slider).toHaveValue('80');expect(f.writes).toEqual([]);
  if(cause==='pointercancel')await slider.dispatchEvent('pointercancel',{pointerId:1,pointerType:'mouse'});else if(cause==='blur')await page.evaluate(()=>window.dispatchEvent(new Event('blur')));else await page.locator('.video-back').evaluate((el:HTMLButtonElement)=>el.click());await page.mouse.up();expect(f.writes).toEqual([]);expect(f.state.audio.volume).toBe(30);if(cause!=='close')await expect(slider).toHaveValue('30');else await expect(page.locator('.video-overlay')).toHaveCount(0);
 });
 test(`Terminal audio ${theme}: long output recovery is bounded with reachable video Retry and Close`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,'reject',true);await pendingOutput(page,ro);await video(page,ro);f.release();const area=page.locator('.video-audio-recovery'),alert=area.getByRole('alert');await expect(alert).toBeVisible();await expect(alert).toContainText(f.label+' second');
  const b=(await area.boundingBox())!;expect(b.x).toBeGreaterThanOrEqual(0);expect(b.x+b.width).toBeLessThanOrEqual(800);expect(b.y).toBeGreaterThanOrEqual(0);expect(b.y+b.height).toBeLessThanOrEqual(480);expect(b.height).toBeLessThanOrEqual(144);expect(await area.evaluate(el=>el.scrollWidth<=el.clientWidth+1)).toBe(true);
  await page.evaluate(()=>{(window as any).__terminalAudioEvents=[];for(const type of ['pointerdown','pointerup','pointercancel','touchstart','touchend','click'])for(const capture of [true,false])window.addEventListener(type,event=>{const target=event.target as Element,button=target.closest('button');(window as any).__terminalAudioEvents.push({type,capture,trusted:event.isTrusted,time:performance.now(),target:target.tagName,button:button?.textContent?.trim(),disabled:(button as HTMLButtonElement)?.disabled,scrollTop:document.querySelector('.video-audio-recovery')?.scrollTop,defaultPrevented:event.defaultPrevented,pointerId:(event as PointerEvent).pointerId,clientX:(event as PointerEvent).clientX,clientY:(event as PointerEvent).clientY});},capture);});
  const diagnostic=async()=>info.attach('audio-retry-event-diagnostic',{body:JSON.stringify({writes:f.writes,events:await page.evaluate(()=>(window as any).__terminalAudioEvents),gestureFrames:await page.evaluate(()=>(window as any).__terminalGestureFrames),recovery:await page.evaluate(()=>{const el=document.querySelector('.video-audio-recovery');return el?{scrollTop:el.scrollTop,scrollHeight:el.scrollHeight,clientHeight:el.clientHeight}:null;})},null,2),contentType:'application/json'});
  const cdp=await page.context().newCDPSession(page),x=b.x+b.width/2,y=b.y+b.height-12;
  // A deliberate native pan: move on animation frames, hold the finger until scroll
  // stabilizes, then release. Fast-fling behavior remains a separate unverified path.
  let ended=false;
  try{await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]});for(let i=1;i<=8;i++){await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x,y:y-i*12}]});await page.evaluate(()=>new Promise<void>(resolve=>requestAnimationFrame(()=>resolve())));}
   await expect.poll(()=>area.evaluate(el=>el.scrollTop)).toBeGreaterThan(0);
   const stable=await area.evaluate(async el=>{let previous=el.scrollTop,count=0;const samples:number[]=[];for(let frame=0;frame<120;frame++){await new Promise<void>(resolve=>requestAnimationFrame(()=>resolve()));const current=el.scrollTop;samples.push(current);count=Math.abs(current-previous)<.1?count+1:0;previous=current;if(count>=8){(window as any).__terminalGestureFrames=samples;return true;}}(window as any).__terminalGestureFrames=samples;return false;});expect(stable).toBe(true);
   await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});ended=true;const events=await page.evaluate(()=>(window as any).__terminalAudioEvents as {type:string;trusted:boolean}[]);expect(events.some(e=>e.trusted&&e.type==='touchstart')).toBe(true);expect(events.some(e=>e.trusted&&e.type==='pointerdown')).toBe(true);expect(events.some(e=>e.trusted&&e.type==='touchend')).toBe(true);
  }catch(error){await diagnostic();throw error;}finally{if(!ended)await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]}).catch(()=>{});await cdp.detach();}
  const retry=alert.getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true}),close=alert.getByRole('button',{name:ro?'Închide':'Close',exact:true});await hit(retry);await hit(close);await hit(page.locator('.video-back'));await hit(page.locator('.video-play'));await page.screenshot({path:info.outputPath('video-long-output-recovery.png')});await hit(retry);await retry.tap();
  try{await expect.poll(()=>f.writes.length,{message:'Retry must dispatch the second exact audio operation before clearing feedback'}).toBe(2);expect(f.writes).toEqual([{output:22},{output:22}]);await expect(alert).toHaveCount(0);}
  finally{await diagnostic();}
 });
 for(const terminal of ['setup','service'] as const)for(const mode of ['reject','accepted'] as const)test(`Terminal audio ${theme}: ${terminal} late ${mode} failure retains exact recovery ownership`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro');await page.clock.install();const f=await fixture(page,ro,theme,mode,true);await pendingOutput(page,ro);await page.locator('.main-nav button').nth(3).tap();
  if(terminal==='setup'){const rerun=ro?'Reia configurarea':'Run setup again';await page.getByRole('button',{name:rerun,exact:true}).tap();await page.locator('.dialog-actions').getByRole('button',{name:rerun,exact:true}).tap();await expect(page.locator('.setup-card')).toBeVisible();}
  else{await page.locator('.settings-tabs button').last().tap();await page.locator('.dialog-actions button').last().tap();await expect(page.locator('.service-screen')).toBeVisible();}
  const area=page.locator(terminal==='setup'?'.setup-audio-recovery':'.service-audio-recovery');await expect(area.getByRole('status')).toBeVisible();f.release();const alert=area.getByRole('alert');await expect(alert).toBeVisible();await expect(alert).toContainText(f.label+' second');
  const retry=alert.getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true}),close=alert.getByRole('button',{name:ro?'Închide':'Close',exact:true});await hit(retry);await hit(close);await expect(alert.getByRole('button',{name:'Audio',exact:true})).toHaveCount(0);
  const node=(await area.elementHandle())!;await area.evaluate(el=>el.scrollTop=el.scrollHeight);const position=await area.evaluate(el=>el.scrollTop);await page.clock.runFor(2700);expect(await node.evaluate(el=>el.isConnected)).toBe(true);expect(await area.evaluate(el=>el.scrollTop)).toBe(position);await page.screenshot({path:info.outputPath(`${terminal}-${mode}-audio-recovery.png`)});
  await retry.tap();await expect(alert).toHaveCount(0);expect(f.writes).toEqual(mode==='accepted'?[{output:22}]:[{output:22},{output:22}]);if(terminal==='service'){const back=page.getByRole('button',{name:ro?'Revino în hub':'Return to hub',exact:true});await hit(back);await back.tap();await expect(page.locator('.service-screen')).toHaveCount(0);}
 });
}
