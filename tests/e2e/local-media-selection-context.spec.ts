import {test,expect} from '@playwright/test';
const videoIdentity='m1_'+'a'.repeat(64),videoSessionId='S'.repeat(32);
for(const theme of ['ink','night'])for(const first of ['video','audio'])for(const outcome of ['reject','accept'])test(`selection ownership ${theme} ${first} ${outcome} replaced listing`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro');let release!:()=>void,pending=false,attempts=0,lists=0;const gate=new Promise<void>(r=>release=r),actions:any[]=[];const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,screensaverMinutes:0,nightEnabled:false},network:{},bluetooth:{devices:[],prompts:[]},audio:{ready:true,volume:30,mute:false},player:{state:'idle'},weather:{}};
 const sessions:any[]=[],commandOrder:string[]=[];
 await page.route('**/api/**',async route=>{const fixtureRequest=route.request(),fixtureUrl=new URL(fixtureRequest.url());
  if(fixtureUrl.pathname==='/api/media/continue'){expect(fixtureRequest.method()).toBe('GET');return route.fulfill({json:{items:[]}});}
  if(fixtureUrl.pathname==='/api/media/inspect'){expect(fixtureRequest.method()).toBe('POST');return route.fulfill({json:{state:'unavailable'}});}
  if(fixtureUrl.pathname==='/api/media/video-session'){
   expect(fixtureRequest.method()).toBe('POST');const body=fixtureRequest.postDataJSON();
   expect(body).toEqual({path:'/original/Original.webm',media_identity:videoIdentity,resume:false});
   sessions.push({method:'POST',body});commandOrder.push(fixtureUrl.pathname);
   return route.fulfill({json:{session_id:videoSessionId,media_identity:videoIdentity,resume_position_s:0,stream_url:`/api/media/file?session_id=${videoSessionId}`}});
  }
  if(fixtureUrl.pathname.startsWith('/api/media/video-session/')){
   expect(fixtureUrl.pathname).toBe(`/api/media/video-session/${videoSessionId}`);
   const method=fixtureRequest.method(),body=fixtureRequest.postData()?fixtureRequest.postDataJSON():null;
   expect(['PATCH','DELETE']).toContain(method);if(body){expect(Number.isSafeInteger(body.sequence)&&body.sequence>0).toBe(true);if(!body.heartbeat){expect(Number.isFinite(body.position_s)&&body.position_s>=0).toBe(true);expect(Number.isFinite(body.duration_s)&&body.duration_s>0).toBe(true);expect(typeof body.ended).toBe('boolean');}}
   sessions.push({method,body});commandOrder.push(fixtureUrl.pathname);
   return route.fulfill({json:{updated:true,closed:method==='DELETE'}});
  }
  const u=new URL(route.request().url());let json:any={ok:true};if(u.pathname==='/api/session')json={token:'fixture'};else if(u.pathname==='/api/state')json=state;else if(u.pathname==='/api/media'){lists++;json={path:lists===1?'/original':'/replacement',items:lists===1?[{name:'Original.webm',path:'/original/Original.webm',kind:'video',media_identity:videoIdentity},{name:'Original.wav',path:'/original/Original.wav',kind:'audio'}]:[{name:'Replacement.wav',path:'/replacement/Replacement.wav',kind:'audio'}]};}else if(u.pathname==='/api/media/file'){expect(u.search).toBe(`?session_id=${videoSessionId}`);return route.fulfill({contentType:'video/webm',body:''});}else if(route.request().method()==='POST'){const body=route.request().postDataJSON();actions.push({path:u.pathname,body});commandOrder.push(u.pathname);if(u.pathname==='/api/player'||u.pathname==='/api/play'){attempts++;if(attempts===1){pending=true;await gate;if(outcome==='reject')return route.fulfill({status:409,json:{error:'media_not_found'}});}if(u.pathname==='/api/play')state.player={state:'playing',kind:'audio',url:body.path,title:body.title,position:1,duration:300};}}await route.fulfill({json});});
 await page.goto('/');await page.locator('.main-nav button').nth(2).tap();await page.getByRole('button',{name:first==='video'?'Original.webm':'Original.wav',exact:false}).and(page.locator('.media-item')).tap();await expect.poll(()=>pending).toBe(true);
 await page.locator('.main-nav button').nth(0).tap();await expect(page.locator('.ambient-home')).toBeVisible();await page.locator('.main-nav button').nth(2).tap();await expect(page.getByRole('button',{name:'Replacement.wav',exact:false}).and(page.locator('.media-item'))).toBeVisible();release();await page.waitForTimeout(250);await expect(page.locator('.video-overlay')).toHaveCount(0);await expect(page.locator('.error-strip')).toHaveCount(0);await expect(page.getByRole('button',{name:'Replacement.wav',exact:false}).and(page.locator('.media-item'))).toBeEnabled();expect(actions).toHaveLength(1);expect(sessions).toEqual([]);
 // Next explicit intent succeeds. Old payload cannot reappear in Retry or execute automatically.
 await page.getByRole('button',{name:'Replacement.wav',exact:false}).and(page.locator('.media-item')).tap();await expect.poll(()=>actions.length).toBe(2);expect(actions[1]).toEqual({path:'/api/play',body:{source:'local',path:'/replacement/Replacement.wav',title:'Replacement.wav'}});await expect(page.locator('.local-audio-bar')).toBeVisible();expect(sessions).toEqual([]);expect(commandOrder).toEqual([first==='video'?'/api/player':'/api/play','/api/play']);
});

for(const theme of ['ink','night'])for(const first of ['video','audio'])test(`queued selection ${theme} ${first} abandoned before backend launch`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro');let release!:()=>void,pending=false,lists=0;const gate=new Promise<void>(r=>release=r),actions:any[]=[];const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,screensaverMinutes:0,nightEnabled:false},network:{},bluetooth:{devices:[],prompts:[]},audio:{ready:true,volume:30,mute:false},player:{state:'playing',kind:'audio',url:'/old/Playing.wav',title:'Playing.wav',position:1,duration:300},weather:{}};
 const sessions:any[]=[],commandOrder:string[]=[];
 await page.route('**/api/**',async route=>{const fixtureRequest=route.request(),fixtureUrl=new URL(fixtureRequest.url());
  if(fixtureUrl.pathname==='/api/media/continue'){expect(fixtureRequest.method()).toBe('GET');return route.fulfill({json:{items:[]}});}
  if(fixtureUrl.pathname==='/api/media/inspect'){expect(fixtureRequest.method()).toBe('POST');return route.fulfill({json:{state:'unavailable'}});}
  if(fixtureUrl.pathname==='/api/media/video-session'){
   expect(fixtureRequest.method()).toBe('POST');const body=fixtureRequest.postDataJSON();
   expect(body).toEqual({path:'/original/Original.webm',media_identity:videoIdentity,resume:false});
   sessions.push({method:'POST',body});commandOrder.push(fixtureUrl.pathname);
   return route.fulfill({json:{session_id:videoSessionId,media_identity:videoIdentity,resume_position_s:0,stream_url:`/api/media/file?session_id=${videoSessionId}`}});
  }
  if(fixtureUrl.pathname.startsWith('/api/media/video-session/')){
   expect(fixtureUrl.pathname).toBe(`/api/media/video-session/${videoSessionId}`);
   const method=fixtureRequest.method(),body=fixtureRequest.postData()?fixtureRequest.postDataJSON():null;
   expect(['PATCH','DELETE']).toContain(method);if(body){expect(Number.isSafeInteger(body.sequence)&&body.sequence>0).toBe(true);if(!body.heartbeat){expect(Number.isFinite(body.position_s)&&body.position_s>=0).toBe(true);expect(Number.isFinite(body.duration_s)&&body.duration_s>0).toBe(true);expect(typeof body.ended).toBe('boolean');}}
   sessions.push({method,body});commandOrder.push(fixtureUrl.pathname);
   return route.fulfill({json:{updated:true,closed:method==='DELETE'}});
  }
  const u=new URL(route.request().url());let json:any={ok:true};if(u.pathname==='/api/session')json={token:'fixture'};else if(u.pathname==='/api/state')json=state;else if(u.pathname==='/api/media'){lists++;json={path:lists===1?'/original':'/replacement',items:lists===1?[{name:'Original.webm',path:'/original/Original.webm',kind:'video',media_identity:videoIdentity},{name:'Original.wav',path:'/original/Original.wav',kind:'audio'}]:[{name:'Replacement.wav',path:'/replacement/Replacement.wav',kind:'audio'}]};}else if(route.request().method()==='POST'){const body=route.request().postDataJSON();actions.push({path:u.pathname,body});commandOrder.push(u.pathname);if(u.pathname==='/api/player'&&body.action==='pause'){pending=true;await gate;state.player={...state.player,state:'paused'};}if(u.pathname==='/api/play')state.player={state:'playing',kind:'audio',url:body.path,title:body.title,position:1,duration:300};}await route.fulfill({json});});
 await page.goto('/');await page.locator('.main-nav button').nth(2).tap();await page.locator('.local-audio-bar').getByRole('button',{name:ro?'Pauză':'Pause',exact:true}).tap();await expect.poll(()=>pending).toBe(true);await page.getByRole('button',{name:first==='video'?'Original.webm':'Original.wav',exact:false}).and(page.locator('.media-item')).tap();await expect(page.locator('.media-library')).toHaveAttribute('aria-busy','true');await page.locator('.main-nav button').nth(0).tap();await page.locator('.main-nav button').nth(2).tap();await expect(page.getByRole('button',{name:'Replacement.wav',exact:false}).and(page.locator('.media-item'))).toBeVisible();release();await expect(page.locator('.media-library')).toHaveAttribute('aria-busy','false');await page.waitForTimeout(200);expect(actions).toEqual([{path:'/api/player',body:{action:'pause'}}]);expect(sessions).toEqual([]);await expect(page.locator('.video-overlay')).toHaveCount(0);await expect(page.locator('.error-strip')).toHaveCount(0);await page.getByRole('button',{name:'Replacement.wav',exact:false}).and(page.locator('.media-item')).tap();await expect.poll(()=>actions.length).toBe(2);expect(actions[1]).toEqual({path:'/api/play',body:{source:'local',path:'/replacement/Replacement.wav',title:'Replacement.wav'}});expect(sessions).toEqual([]);expect(commandOrder).toEqual(['/api/player','/api/play']);
});
