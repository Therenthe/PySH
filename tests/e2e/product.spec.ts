import { expect, test, type Page, type TestInfo } from '@playwright/test';
import { textLegibility } from './legibility';

// Strict browser-only fixtures: no production adapter returns these states.
async function fixture(page: Page, language: 'en'|'ro', theme: 'ink'|'night', setupComplete = true) {
  const state: any = {
    appliance:false, serviceMode:false,
    preferences: { language, theme, setupComplete, nightEnabled: false, screensaverMinutes: 0, location: { name: 'București', latitude: 44.4, longitude: 26.1 }, favorites: [], shortcuts: ['radio','media'] },
    network: { available: true, state: 'connected', connection: 'Ethernet', devices: [{type:'ethernet', state:'connected', ip:'192.0.2.1'}], saved: [] },
    bluetooth: { available: true, powered: true, devices: [{address:'00:00:00:00:00:01', name:'Test speaker', paired:true, connected:true}], prompts: [] },
    audio: { available:true, ready:true, volume:25, mute:false, output:'test-speaker', outputs:[{id:'test-speaker',name:'Test speaker',description:'Bluetooth test output', bluetooth:true,active:true}] },
    player:{state:'idle'}, weather:{ available:true, current:{temperature_c:21,feels_like_c:20,weather_code:0}, daily:[{date:'2026-10-02',max_c:23,min_c:14},{date:'2026-10-03',max_c:22,min_c:15}],updated_at:'2026-10-02T12:00:00+03:00',attribution:'Open-Meteo' },
  };
  const f = { state, unexpected:[] as string[], actions:[] as any[], radio:'populated', media:'populated', backendDown:false, radioQueries:[] as string[] };
  await page.route('**/api/**', async route => {
    const req=route.request(), path=new URL(req.url()).pathname, method=req.method();
    if(f.backendDown && path==='/api/state') { await route.abort('failed'); return; }
    let json:any; let status=200; const body=method==='GET'?{}:req.postDataJSON();
    if(path==='/api/session' && method==='GET') json={token:'browser-test-only'};
    else if(path==='/api/state' && method==='GET') json=state;
    else if(path==='/api/preferences' && method==='PATCH'){f.actions.push({path,body});Object.assign(state.preferences,body);json=state.preferences;}
    else if(path==='/api/radio' && method==='GET') {
      f.radioQueries.push(req.url());if(f.radio==='error'){json={stations:[],error:'radio_catalog_unavailable'};}
      else json={stations:f.radio==='empty'?[]:[{stationuuid:'test-station',name:'Test station',country:'Romania',language:'Romanian',codec:'MP3',url:'https://example.com/test.mp3'}]};
    } else if(path==='/api/media' && method==='GET') {
      if(f.media==='error'){status=503;json={error:'media_unavailable'};}
      else json={path:'Test library',parent:'',items:f.media==='empty'?[]:[{name:'Test audio.mp3',path:'/test/audio.mp3',kind:'audio',size_human:'1 MB'},{name:'Test folder',path:'/test/folder',is_dir:true}]};
    } else if(path==='/api/geocode' && method==='GET') json={results:[{name:'București',latitude:44.4,longitude:26.1,country:'Romania'}]};
    else if(path==='/api/network/scan' && method==='POST') json={networks:[{ssid:'Protected test Wi-Fi',security:'secured',signal:80}]};
    else if(['/api/play','/api/player','/api/audio','/api/bluetooth/power','/api/bluetooth/scan','/api/bluetooth/action','/api/bluetooth/reply','/api/weather/refresh','/api/network/connect','/api/external','/api/exit','/api/service/return','/api/favorites'].includes(path) && method==='POST') {
      f.actions.push({path,body});
      if(path==='/api/play'){state.player={state:'playing',title:body.title,kind:body.source==='radio'?'radio':'audio',url:body.url||body.path};if(body.source==='radio')state.preferences.lastStation={uuid:'test-station',name:body.title,url:body.url};}
      if(path==='/api/player'){if(body.action==='seek')state.player.position=body.value;else if(body.action==='stop')Object.assign(state.player,{state:'idle',url:'',title:'',canPrevious:false,canNext:false});else state.player.state=body.action==='pause'?'paused':'playing';}
      if(path==='/api/favorites')state.preferences.favorites=body.remove?[]:[body.station];
      if(path==='/api/audio')Object.assign(state.audio,body);
      if(path==='/api/bluetooth/reply')state.bluetooth.prompts=[];
      if(path==='/api/exit'&&state.appliance){state.serviceMode=true;state.player={state:'idle'};}
      if(path==='/api/service/return')state.serviceMode=false;
      json={ok:true};
    } else {f.unexpected.push(`${method} ${path}`);status=500;json={error:'unexpected_test_request'};}
    await route.fulfill({status,json});
  });
  return f;
}

async function capture(page:Page, info:TestInfo, name:string, defects:string[]) {
  await page.screenshot({path:info.outputPath(`${name}.png`)});
  const issues=await page.evaluate(()=> {
    const results:string[]=[];
    for(const el of document.querySelectorAll<HTMLElement>('button, select, input[type=range], a.download-link')) {
      const r=el.getBoundingClientRect(), s=getComputedStyle(el);
      if(!r.width||!r.height||s.visibility==='hidden'||s.display==='none'||r.bottom<=0||r.top>=480||r.right<=0||r.left>=800)continue;
      const accessible=el.getAttribute('aria-label')||el.innerText;const name=accessible||el.className;
      if(!accessible?.trim()&&el.tagName==='BUTTON')results.push(`unnamed button ${el.className}`);
      if(r.width<47.9||r.height<47.9)results.push(`small target ${name}: ${r.width.toFixed(1)}×${r.height.toFixed(1)}`);
      // Scrollable lists/panels legitimately show part of the next row.
      let scrollable=false;
      for(let p=el.parentElement;p;p=p.parentElement)if(/auto|scroll/.test(getComputedStyle(p).overflowY)&&p.scrollHeight>p.clientHeight)scrollable=true;
      if(!scrollable&&(r.top<-.5||r.left<-.5||r.right>800.5||r.bottom>480.5))results.push(`clipped target ${name}: bottom ${r.bottom.toFixed(1)}`);
    }
    if(document.querySelector('button button'))results.push('nested buttons');
    return results;
  });
  defects.push(...issues.map(x=>`${name}: ${x}`));
  defects.push(...(await textLegibility(page)).map(x=>`${name}: ${x}`));
}
async function closeModal(page:Page, ro:boolean){await page.locator('.modal-card header').getByRole('button',{name:ro?'Închide':'Close',exact:true}).tap();}

for(const theme of ['ink','night'] as const) {
  test(`video handoff queues behind an in-flight radio play ${theme}`,async({page},info)=>{
    const ro=info.project.name==='touch-ro',f=await fixture(page,ro?'ro':'en',theme);
    await page.route('**/api/media?**',route=>route.fulfill({json:{path:'Video test folder',items:[{name:'Test video.mp4',path:'/test/video.mp4',kind:'video'}]}}));
    await page.route('**/api/media/file?**',route=>route.fulfill({contentType:'video/mp4',body:'invalid decoder input'}));
    let release!:()=>void,playStarted=false,stopStarted=false;const gate=new Promise<void>(resolve=>release=resolve);
    await page.route('**/api/play',async route=>{playStarted=true;await gate;f.state.player={state:'playing',kind:'radio',url:'https://example.com/test.mp3',title:'Test station'};await route.fulfill({json:f.state.player});});
    await page.route('**/api/player',async route=>{expect(route.request().postDataJSON()).toEqual({action:'stop'});stopStarted=true;f.state.player={state:'idle',url:'',title:''};await route.fulfill({json:f.state.player});});
    await page.goto('/');await page.locator('.main-nav button').nth(1).tap();await page.locator('.station-row').first().getByRole('button').first().tap();await expect.poll(()=>playStarted).toBe(true);
    await page.locator('.main-nav button').nth(2).tap();await page.getByRole('button',{name:'Test video.mp4',exact:false}).tap();await page.waitForTimeout(300);expect(stopStarted).toBe(false);await expect(page.locator('.video-overlay')).toHaveCount(0);
    release();await expect(page.locator('.video-overlay')).toBeVisible();expect(stopStarted).toBe(true);expect(f.state.player.state).toBe('idle');expect(f.unexpected).toEqual([]);
  });
  test(`local video waits for successful stop of other playback ${theme}`,async({page},info)=>{
    const ro=info.project.name==='touch-ro',f=await fixture(page,ro?'ro':'en',theme);
    await page.route('**/api/media?**',route=>route.fulfill({json:{path:'Video test folder',items:[{name:'Test video.mp4',path:'/test/video.mp4',kind:'video'}]}}));
    await page.route('**/api/media/file?**',route=>route.fulfill({contentType:'video/mp4',body:'invalid decoder input'}));
    for(const kind of ['radio','audio','stale-idle']){
      // Idle can be the last polled snapshot while actual playback has already started.
      const originalState=kind==='stale-idle'?'idle':'playing';
      f.state.player={state:originalState,kind:kind==='stale-idle'?'radio':kind,url:kind==='stale-idle'?'':kind==='radio'?'https://example.com/radio':'/test/audio.mp3',title:'Existing playback'};
      await page.route('**/api/player',route=>route.fulfill({status:503,json:{error:'player_timeout'}}));
      await page.goto('/');await page.locator('.main-nav button').nth(2).tap();await page.getByRole('button',{name:'Test video.mp4',exact:false}).tap();
      await expect(page.locator('.error-strip')).toBeVisible();await expect(page.locator('.video-overlay')).toHaveCount(0);expect(f.state.player.state).toBe(originalState);
      let release!:()=>void,requested=false;const gate=new Promise<void>(resolve=>release=resolve);
      await page.route('**/api/player',async route=>{expect(route.request().postDataJSON()).toEqual({action:'stop'});requested=true;await gate;Object.assign(f.state.player,{state:'idle',url:'',title:''});await route.fulfill({json:{ok:true}});});
      await page.getByRole('button',{name:'Test video.mp4',exact:false}).tap();await expect.poll(()=>requested).toBe(true);await expect(page.locator('.video-overlay')).toHaveCount(0);
      release();await expect(page.locator('.video-overlay')).toBeVisible();expect(f.state.player.state).toBe('idle');await page.locator('.video-back').tap();
    }
    expect(f.unexpected).toEqual([]);
  });
  test(`pairing prompt wakes and suspends idle screensaver ${theme}`,async({page},info)=>{
    const ro=info.project.name==='touch-ro',f=await fixture(page,ro?'ro':'en',theme);f.state.preferences.screensaverMinutes=1;await page.clock.install();
    await page.goto('/');await expect(page.locator('.home-layout')).toBeVisible();await page.clock.fastForward(61000);await expect(page.locator('.screensaver')).toBeVisible();
    f.state.bluetooth.prompts=[{id:'wake-prompt',name:'Test speaker',kind:'confirmation',value:'123456'}];await page.clock.runFor(2600);
    await expect(page.locator('.pair-code')).toBeVisible();await expect(page.locator('.screensaver')).toHaveCount(0);await page.clock.fastForward(120000);await expect(page.locator('.screensaver')).toHaveCount(0);
    await page.locator('.dialog-actions button').first().tap();await expect(page.locator('.pair-code')).toHaveCount(0);await page.clock.fastForward(61000);await expect(page.locator('.screensaver')).toBeVisible();expect(f.unexpected).toEqual([]);
  });
  test(`city search explains empty results and ignores late old results ${theme}`,async({page},info)=>{
    const ro=info.project.name==='touch-ro',f=await fixture(page,ro?'ro':'en',theme);let release!:()=>void,oldDone=false;const gate=new Promise<void>(resolve=>release=resolve);
    await page.route('**/api/geocode?**',async route=>{const q=new URL(route.request().url()).searchParams.get('q');if(q==='a'){await gate;await route.fulfill({json:{results:[{name:'Old search city',latitude:1,longitude:2}]}});oldDone=true;}else await route.fulfill({json:{results:[]}});});
    await page.goto('/');await page.locator('.main-nav button').nth(3).tap();await page.locator('.settings-tabs button').nth(1).tap();
    const search=async(letter:string)=>{await page.locator('.settings-panel .setting-value').tap();for(let i=0;i<'București'.length;i++)await page.getByRole('button',{name:ro?'Șterge caracterul':'Delete character',exact:true}).tap();await page.locator('.keys').getByRole('button',{name:letter,exact:true}).tap();await page.locator('.final-row').getByRole('button',{name:ro?'Aplică':'Apply',exact:true}).tap();};
    await search('a');await expect(page.locator('.settings-panel [role=status]')).toHaveText(ro?'Se încarcă…':'Loading…');await search('b');await expect(page.locator('.settings-panel [role=status]')).toHaveText(ro?'Nu s-au găsit orașe':'No matching cities');
    release();await expect.poll(()=>oldDone).toBe(true);await expect(page.locator('.compact-geo')).toHaveCount(0);await expect(page.locator('.settings-panel [role=status]')).toHaveText(ro?'Nu s-au găsit orașe':'No matching cities');expect(f.state.preferences.location.name).toBe('București');expect(f.unexpected).toEqual([]);
  });

  test(`local audio transport uses queue availability and touch seek ${theme}`,async({page},info)=>{
    const ro=info.project.name==='touch-ro',f=await fixture(page,ro?'ro':'en',theme),defects:string[]=[];
    f.state.player={state:'playing',kind:'audio',title:'Test local track',url:'/test/audio.mp3',duration:120,position:30,canPrevious:false,canNext:true};
    await page.goto('/');await page.locator('.main-nav button').nth(2).tap();const bar=page.locator('.local-audio-bar');await expect(bar).toBeVisible();
    const previous=bar.getByRole('button',{name:ro?'Anterior':'Previous',exact:true}),next=bar.getByRole('button',{name:ro?'Următor':'Next',exact:true});
    await expect(previous).toBeDisabled();await expect(next).toBeEnabled();await expect(bar.locator('.audio-time')).toHaveText('0:30 / 2:00');
    await bar.getByRole('button',{name:ro?'Pauză':'Pause',exact:true}).tap();await expect(bar.getByRole('button',{name:ro?'Redă':'Play',exact:true})).toBeVisible();
    const slider=bar.getByRole('slider',{name:ro?'Progres':'Progress',exact:true}),rect=await slider.boundingBox();await slider.tap({position:{x:rect!.width*.5,y:rect!.height*.5}});
    await expect.poll(()=>f.actions.filter(a=>a.path==='/api/player'&&a.body.action==='seek').at(-1)?.body.value).toBeGreaterThan(55);expect(f.state.player.position).toBeLessThan(65);await expect(bar.locator('.audio-time')).toContainText('/ 2:00');
    await bar.getByRole('button',{name:ro?'Redă':'Play',exact:true}).tap();await next.tap();expect(f.actions.filter(a=>a.path==='/api/player').at(-1)?.body.action).toBe('next');
    f.state.player.canPrevious=true;f.state.player.canNext=false;await page.reload();await expect(previous).toBeEnabled();await expect(next).toBeDisabled();await previous.tap();expect(f.actions.filter(a=>a.path==='/api/player').at(-1)?.body.action).toBe('previous');
    await capture(page,info,'local-audio-transport',defects);await bar.getByRole('button',{name:ro?'Oprește':'Stop',exact:true}).tap();await expect(bar).toHaveCount(0);expect(defects).toEqual([]);expect(f.unexpected).toEqual([]);
  });
  test(`ended or failed local audio retains replay and queue controls ${theme}`,async({page},info)=>{
    const ro=info.project.name==='touch-ro',f=await fixture(page,ro?'ro':'en',theme),defects:string[]=[];
    for(const state of ['ended','error']){
      f.state.player={state,kind:'audio',title:'Completed local track',url:'/test/audio.mp3',duration:120,position:120,canPrevious:true,canNext:true};
      await page.goto('/');const bar=page.locator('.local-audio-bar');await expect(bar).toBeVisible();await expect(page.locator('.home-focus .player-state')).toHaveText(ro?'Pregătit':'Ready');
      await expect(bar.locator('.audio-time')).toHaveText(state==='error'?(ro?'Problemă de redare':'Playback problem'):(ro?'Redare încheiată':'Playback finished'));await expect(bar.getByRole('slider')).toBeDisabled();
      await expect(bar.getByRole('button',{name:ro?'Următor':'Next',exact:true})).toBeEnabled();await capture(page,info,`local-audio-${state}`,defects);
      await bar.getByRole('button',{name:ro?'Redă':'Play',exact:true}).tap();expect(f.actions.filter(a=>a.path==='/api/play').at(-1)?.body).toEqual({source:'local',path:'/test/audio.mp3',title:'Completed local track'});await expect(bar.getByRole('button',{name:ro?'Pauză':'Pause',exact:true})).toBeVisible();
      f.state.player={state,kind:'audio',title:'Completed local track',url:'/test/audio.mp3',canPrevious:true,canNext:true};await page.reload();await bar.getByRole('button',{name:ro?'Următor':'Next',exact:true}).tap();expect(f.actions.filter(a=>a.path==='/api/player').at(-1)?.body.action).toBe('next');
    }
    expect(defects).toEqual([]);expect(f.unexpected).toEqual([]);
  });
  test(`radio transport explains idle and replays stopped or failed sources ${theme}`,async({page},info)=>{
    const ro=info.project.name==='touch-ro',f=await fixture(page,ro?'ro':'en',theme),defects:string[]=[];
    await page.goto('/');await page.locator('.main-nav button').nth(1).tap();const controls=page.locator('.radio-side .player-controls'),play=()=>controls.getByRole('button',{name:ro?'Redă':'Play',exact:true});
    await expect(play()).toBeDisabled();await expect(controls.getByRole('button',{name:ro?'Anterior':'Previous',exact:true})).toHaveCount(0);await expect(controls.getByRole('button',{name:ro?'Oprește':'Stop',exact:true})).toBeDisabled();
    await page.locator('.station-main').tap();await controls.getByRole('button',{name:ro?'Oprește':'Stop',exact:true}).tap();expect(f.state.player.url).toBe('');await expect(play()).toBeEnabled();await play().tap();expect(f.actions.filter(a=>a.path==='/api/play')).toHaveLength(2);expect(f.actions.filter(a=>a.path==='/api/play').at(-1)?.body).toEqual({source:'radio',url:'https://example.com/test.mp3',title:'Test station'});
    for(const state of ['error','ended']){f.state.player={state,kind:'radio',url:'https://example.com/failing.mp3',title:'Current failed station'};await page.reload();await page.locator('.main-nav button').nth(1).tap();await play().tap();expect(f.actions.filter(a=>a.path==='/api/play').at(-1)?.body).toEqual({source:'radio',url:'https://example.com/failing.mp3',title:'Current failed station'});}
    for(const state of ['buffering','connecting']){f.state.player={state,kind:'radio',url:'https://example.com/test.mp3',title:'Test station'};await page.reload();await page.locator('.main-nav button').nth(1).tap();await controls.getByRole('button',{name:ro?'Pauză':'Pause',exact:true}).tap();expect(f.actions.filter(a=>a.path==='/api/player').at(-1)?.body.action).toBe('pause');await expect(play()).toBeEnabled();}
    await capture(page,info,'radio-transport-recovery',defects);expect(defects).toEqual([]);expect(f.unexpected).toEqual([]);
  });
  test(`active radio station pauses and resumes without reload ${theme}`,async({page},info)=>{
    const ro=info.project.name==='touch-ro',f=await fixture(page,ro?'ro':'en',theme);
    await page.goto('/');await page.locator('.main-nav button').nth(1).tap();const station=page.locator('.station-main');await station.tap();await expect(page.locator('.radio-side .state-text')).toHaveText(ro?'Se redă':'Playing');
    await expect(station).toHaveAccessibleName(`${ro?'Pauză':'Pause'} · Test station`);await station.tap();await expect(station).toHaveAccessibleName(`${ro?'Redă':'Play'} · Test station`);await expect(page.locator('.radio-side .state-text')).toHaveText(ro?'În pauză':'Paused');expect(f.actions.filter(a=>a.path==='/api/play')).toHaveLength(1);expect(f.actions.filter(a=>a.path==='/api/player').at(-1)?.body.action).toBe('pause');
    await station.tap();await expect(page.locator('.radio-side .state-text')).toHaveText(ro?'Se redă':'Playing');expect(f.actions.filter(a=>a.path==='/api/play')).toHaveLength(1);expect(f.actions.filter(a=>a.path==='/api/player').at(-1)?.body.action).toBe('resume');f.state.player.url='https://example.com/other.mp3';await page.reload();await page.locator('.main-nav button').nth(1).tap();await expect(station).toHaveAccessibleName(`${ro?'Redă':'Play'} · Test station`);await station.tap();expect(f.actions.filter(a=>a.path==='/api/play')).toHaveLength(2);expect(f.unexpected).toEqual([]);
  });

  test(`local video owns persistent touch playback controls ${theme}`,async({page},info)=>{
    const ro=info.project.name==='touch-ro',f=await fixture(page,ro?'ro':'en',theme),defects:string[]=[];
    await page.goto('/');
    // Real VP8 decoder input generated inside the test browser, not a simulated video element.
    const bytes=await page.evaluate(async()=>{
      const canvas=document.createElement('canvas');canvas.width=160;canvas.height=90;const ctx=canvas.getContext('2d')!;
      const stream=canvas.captureStream(12),recorder=new MediaRecorder(stream,{mimeType:'video/webm;codecs=vp8'}),parts:BlobPart[]=[];
      const done=new Promise<Blob>(resolve=>{recorder.ondataavailable=e=>parts.push(e.data);recorder.onstop=()=>resolve(new Blob(parts,{type:'video/webm'}));});
      let frame=0;const draw=setInterval(()=>{ctx.fillStyle=frame++%2?'#4a7c6a':'#e5c257';ctx.fillRect(0,0,160,90);},80);
      recorder.start();await new Promise(resolve=>setTimeout(resolve,2400));recorder.stop();const blob=await done;clearInterval(draw);stream.getTracks().forEach(track=>track.stop());return Array.from(new Uint8Array(await blob.arrayBuffer()));
    });
    await page.route('**/api/media?**',route=>route.fulfill({json:{path:'Browser decoder fixture',items:[{name:'Real generated test.webm',path:'/test/real.webm',kind:'video'}]}}));
    await page.route('**/api/media/file?**',route=>{const range=route.request().headers().range?.match(/bytes=(\d+)-(\d*)/);const data=Buffer.from(bytes);if(!range)return route.fulfill({contentType:'video/webm',headers:{'Accept-Ranges':'bytes'},body:data});const start=Number(range[1]),end=Math.min(range[2]?Number(range[2]):data.length-1,data.length-1);return route.fulfill({status:206,contentType:'video/webm',headers:{'Accept-Ranges':'bytes','Content-Range':`bytes ${start}-${end}/${data.length}`},body:data.subarray(start,end+1)});});
    await page.locator('.main-nav button').nth(2).tap();await page.locator('.media-item').tap();
    // MediaRecorder WebM initially exposes infinite duration; a normal local seekable file has a finite duration.
    await page.locator('video').evaluate(async(v:HTMLVideoElement)=>{await new Promise<void>(resolve=>{if(v.readyState>=2)resolve();else v.addEventListener('loadeddata',()=>resolve(),{once:true});});if(!Number.isFinite(v.duration)){v.currentTime=1e6;await new Promise<void>(resolve=>v.addEventListener('seeked',()=>resolve(),{once:true}));v.currentTime=0;}});
    await expect.poll(()=>page.locator('video').evaluate((v:HTMLVideoElement)=>Number.isFinite(v.duration)&&v.duration>0)).toBe(true);
    await expect(page.locator('video')).not.toHaveAttribute('controls');await expect(page.locator('.video-controls')).toBeVisible();
    await page.locator('video').evaluate((v:HTMLVideoElement)=>v.pause());await expect(page.locator('.video-play')).toHaveText(ro?'Redă':'Play');
    const seek=page.getByRole('slider',{name:ro?'Progres':'Progress',exact:true}),rect=await seek.boundingBox();await seek.tap({position:{x:rect!.width*.5,y:rect!.height*.5}});
    await expect.poll(()=>page.locator('video').evaluate((v:HTMLVideoElement)=>v.currentTime)).toBeGreaterThan(.5);
    await page.locator('.video-play').tap();await expect(page.locator('.video-play')).toHaveText(ro?'Pauză':'Pause');await page.locator('.video-play').tap();await expect(page.locator('video')).toHaveJSProperty('paused',true);
    await page.locator('.video-audio button').tap();expect(f.actions.filter(a=>a.path==='/api/audio').at(-1)?.body).toEqual({mute:true});await expect(page.locator('.video-audio button')).toHaveText(ro?'Activează sunetul':'Unmute');
    const volume=page.getByRole('slider',{name:ro?'Volum':'Volume',exact:true}),vr=await volume.boundingBox();await volume.tap({position:{x:vr!.width*.65,y:vr!.height*.5}});await expect.poll(()=>f.actions.filter(a=>a.path==='/api/audio').at(-1)?.body.volume).toBeGreaterThan(50);
    await capture(page,info,'local-video-controls',defects);
    const controlContrast=await page.evaluate(()=>{const lum=(s:string)=>{const c=(s.match(/[\d.]+/g)||[]).slice(0,3).map(Number).map(x=>x/255).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4);return c.reduce((a,x,i)=>a+x*[.2126,.7152,.0722][i],0);};return [...document.querySelectorAll('.video-controls button,.video-header button')].map(el=>{const s=getComputedStyle(el),a=lum(s.borderTopColor),b=lum(s.backgroundColor);return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);});});expect(controlContrast.every(ratio=>ratio>=3)).toBe(true);await page.locator('.video-back').tap();await expect(page.locator('.media-page')).toBeVisible();await expect(page.locator('.video-overlay')).toHaveCount(0);expect(defects).toEqual([]);expect(f.unexpected).toEqual([]);
  });
  test(`invalid local video keeps retry and return visible ${theme}`,async({page},info)=>{
    const ro=info.project.name==='touch-ro',f=await fixture(page,ro?'ro':'en',theme),defects:string[]=[];
    f.state.audio.ready=false;let attempts=0;
    await page.route('**/api/media?**',route=>route.fulfill({json:{path:'Test video folder',items:[{name:'Broken video.mp4',path:'/test/broken.mp4',kind:'video'}]}}));
    await page.route('**/api/media/file?**',route=>{attempts++;return route.fulfill({contentType:'video/mp4',body:'invalid video test content'});});
    await page.goto('/');await page.locator('.main-nav button').nth(2).tap();await page.locator('.media-item').tap();
    await expect(page.locator('.video-error')).toBeVisible();await expect(page.locator('.video-audio-warning')).toBeVisible();await capture(page,info,'invalid-video',defects);
    const before=attempts;await page.locator('.video-error button').tap();await expect.poll(()=>attempts).toBeGreaterThan(before);await expect(page.locator('.video-error')).toBeVisible();await page.locator('.video-back').tap();await expect(page.locator('.video-overlay')).toHaveCount(0);await expect(page.locator('.media-page')).toBeVisible();expect(defects).toEqual([]);expect(f.unexpected).toEqual([]);
  });
  test(`weather, radio and media retry target the failed operation ${theme}`,async({page},info)=>{
    const ro=info.project.name==='touch-ro',f=await fixture(page,ro?'ro':'en',theme);
    f.state.weather={available:false,error:'weather_unavailable'};
    await page.goto('/');await expect(page.locator('.weather-empty')).toContainText(ro?'Meteo indisponibilă':'Weather is unavailable');await page.locator('.weather-empty').tap();expect(f.actions.some(a=>a.path==='/api/weather/refresh')).toBeTruthy();await expect(page.locator('.home-layout')).toBeVisible();
    f.radio='error';await page.locator('.main-nav button').nth(1).tap();await expect(page.locator('.error-strip')).toBeVisible();f.radio='populated';await page.locator('.error-strip').getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true}).tap();await expect(page.locator('.station-main')).toHaveCount(1);await expect(page.locator('.error-strip')).toHaveCount(0);
    f.media='error';await page.locator('.main-nav button').nth(2).tap();await expect(page.locator('.error-strip')).toBeVisible();f.media='populated';await page.locator('.error-strip').getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true}).tap();await expect(page.locator('.media-item')).toHaveCount(2);await expect(page.locator('.error-strip')).toHaveCount(0);expect(f.unexpected).toEqual([]);
  });
  test(`radio retains catalog and ignores superseded filters ${theme}`,async({page},info)=>{
    const ro=info.project.name==='touch-ro',f=await fixture(page,ro?'ro':'en',theme);
    let releaseOld!:()=>void;const oldGate=new Promise<void>(resolve=>releaseOld=resolve);let oldStarted=false,oldDone=false;
    await page.route('**/api/radio?**',async route=>{
      const country=new URL(route.request().url()).searchParams.get('country');f.radioQueries.push(route.request().url());
      if(country==='old'){oldStarted=true;await oldGate;}
      try{await route.fulfill({json:{stations:[{stationuuid:country||'initial',name:country==='new'?'Newest station':country==='old'?'Old station':'Initial station',url:'https://example.com/test.mp3'}]}});}catch{/* Superseded browser request may already be aborted. */}
      if(country==='old')oldDone=true;
    });
    await page.goto('/');await page.locator('.main-nav button').nth(1).tap();await expect(page.locator('.station-main')).toContainText('Initial station');
    const count=f.radioQueries.length;await page.locator('.main-nav button').first().tap();await page.locator('.main-nav button').nth(1).tap();await expect(page.locator('.station-main')).toContainText('Initial station');expect(f.radioQueries).toHaveLength(count);
    let previous='';const filter=async(value:string)=>{await page.locator('.radio-toolbar .filter-button').first().tap();for(let i=0;i<previous.length;i++)await page.getByRole('button',{name:ro?'Șterge caracterul':'Delete character',exact:true}).tap();previous=value;for(const letter of value)await page.locator('.key-row').getByRole('button',{name:letter,exact:true}).tap();await page.locator('.final-row').getByRole('button',{name:ro?'Aplică':'Apply',exact:true}).tap();};
    await filter('old');await expect.poll(()=>oldStarted).toBe(true);await filter('new');await expect(page.locator('.station-main')).toContainText('Newest station');releaseOld();await expect.poll(()=>oldDone).toBe(true);await expect(page.locator('.station-main')).toContainText('Newest station');expect(f.unexpected).toEqual([]);
  });
  test(`appliance service recovery ${theme}`,async({page},info)=> {
    const ro=info.project.name==='touch-ro',f=await fixture(page,ro?'ro':'en',theme),defects:string[]=[];
    f.state.appliance=true;f.state.preferences.screensaverMinutes=1;const prefs=JSON.stringify(f.state.preferences);await page.clock.install();
    await page.goto('/');await expect(page.locator('.home-layout')).toBeVisible();
    await page.locator('.main-nav button').nth(3).tap();
    await page.locator('.settings-tabs button').nth(7).tap();
    await expect(page.getByRole('dialog')).toContainText(ro?'Deschizi modul de service?':'Open service mode?');
    await capture(page,info,'service-confirmation',defects);
    await page.locator('.dialog-actions button').first().tap();expect(f.actions.some(a=>a.path==='/api/exit')).toBeFalsy();
    await page.locator('.settings-tabs button').nth(7).tap();await page.locator('.dialog-actions button').last().tap();
    await expect(page.locator('.service-screen')).toBeVisible();await expect(page.locator('.main-nav')).toHaveCount(0);
    await capture(page,info,'service-mode',defects);
    f.backendDown=true;await expect(page.locator('.error-strip')).toBeVisible({timeout:6000});await capture(page,info,'service-backend-error',defects);
    f.backendDown=false;await page.locator('.error-strip button').tap();await expect(page.locator('.error-strip')).toHaveCount(0);
    await page.clock.fastForward(120000);await expect(page.locator('.service-screen')).toBeVisible();await page.getByRole('button',{name:ro?'Revino în hub':'Return to hub',exact:true}).tap();await expect(page.locator('.screensaver')).toHaveCount(0);
    await expect(page.locator('.service-screen')).toHaveCount(0);await expect(page.locator('.main-nav')).toBeVisible();
    expect(JSON.stringify(f.state.preferences)).toBe(prefs);expect(f.unexpected).toEqual([]);expect(defects).toEqual([]);
  });
  test(`filters, cancellation and shortcuts ${theme}`,async({page},info)=> {
    const ro=info.project.name==='touch-ro', f=await fixture(page,ro?'ro':'en',theme);
    await page.goto('/');await expect(page.locator('.home-layout')).toBeVisible();
    await page.locator('.main-nav button').nth(1).tap();
    await expect(page.locator('.station-main')).toHaveCount(1); // catalog loads on entry
    await page.locator('.radio-toolbar .filter-button').first().tap();
    for(const letter of ['r','o'])await page.locator('.key-row').getByRole('button',{name:letter,exact:true}).tap();
    await page.locator('.final-row').getByRole('button',{name:ro?'Aplică':'Apply',exact:true}).tap();
    await expect.poll(()=>new URL(f.radioQueries.at(-1)!).searchParams.get('country')).toBe('ro');
    await page.locator('.favorite-button').tap();await expect(page.locator('.favorite-button')).toHaveAttribute('aria-pressed','true');
    await page.locator('.favorite-button').tap();await expect(page.locator('.favorite-button')).toHaveAttribute('aria-pressed','false');
    await page.locator('.main-nav button').nth(3).tap();
    await page.locator('.settings-tabs button').first().tap();
    const before=f.actions.filter(a=>a.path==='/api/preferences').length;
    await page.locator('.setting-value').tap();await page.locator('.keyboard-card header button').tap();
    expect(f.actions.filter(a=>a.path==='/api/preferences')).toHaveLength(before);
    await page.locator('.settings-tabs button').nth(5).tap();await page.locator('.settings-panel button.switch').first().tap();
    await page.locator('.main-nav button').first().tap();await expect(page.locator('.shortcut')).toHaveCount(1);await expect(page.locator('.shortcut')).toContainText('Media');
    await page.reload();await expect(page.locator('.shortcut')).toHaveCount(1);
    expect(f.unexpected).toEqual([]);
  });

  test(`full product tour ${theme}`,async({page},info)=> {
    const ro=info.project.name==='touch-ro', f=await fixture(page,ro?'ro':'en',theme), defects:string[]=[],errors:string[]=[];
    page.on('pageerror',e=>errors.push(e.message));
    await page.goto('/'); await expect(page.locator('.home-layout')).toBeVisible();
    await capture(page,info,'home-weather',defects);
    if(ro)expect.soft(await page.locator('.home-focus').innerText()).not.toContain('YOUR HUB');
    const nav=async(index:number)=>page.locator('.main-nav button').nth(index).tap();
    await nav(1); await page.locator('.radio-toolbar button.primary').tap();
    await expect(page.locator('.station-main')).toHaveCount(1); await capture(page,info,'radio-populated',defects);
    if(ro)expect.soft(await page.locator('.radio-page').innerText()).not.toMatch(/LISTEN|DISCOVER|\bidle\b/);
    await page.locator('.station-main').tap(); await capture(page,info,'radio-playing',defects);
    f.radio='empty';await page.locator('.radio-toolbar button.primary').tap();await expect(page.locator('.station-main')).toHaveCount(0);await capture(page,info,'radio-empty',defects);
    f.radio='error';await page.locator('.radio-toolbar button.primary').tap();await expect(page.locator('.error-strip')).toBeVisible();await capture(page,info,'radio-error',defects);
    await nav(2); await expect(page.locator('.media-item')).toHaveCount(2);await capture(page,info,'media-populated',defects);
    await page.locator('.media-item').first().tap();expect(f.actions.some(a=>a.path==='/api/play'&&a.body.source==='local')).toBeTruthy();
    f.media='empty';await page.locator('.crumb-actions button').first().tap();await expect(page.locator('.media-item')).toHaveCount(0);await capture(page,info,'media-empty',defects);
    f.media='error';await page.locator('.crumb-actions button').first().tap();await expect(page.locator('.error-strip')).toBeVisible();await capture(page,info,'media-error',defects);
    await nav(3);
    for(let i=0;i<7;i++){await page.locator('.settings-tabs button').nth(i).tap();await capture(page,info,`settings-${['appearance','weather','network','bluetooth','audio','home','diagnostics'][i]}`,defects);}
    await page.locator('.settings-tabs button').nth(7).tap();await capture(page,info,'exit-dialog',defects);await page.locator('.dialog-actions button').first().tap();expect(f.actions.some(a=>a.path==='/api/exit')).toBeFalsy();
    await nav(0);
    await page.getByRole('button',{name:ro?'Deschide setările':'Open settings',exact:true}).first().tap();await capture(page,info,'quick-settings',defects);
    for(const [index,name] of [[0,'network'],[1,'bluetooth'],[2,'audio']] as const) {
      await page.locator('.quick-modal>button').nth(index).tap();await capture(page,info,`${name}-dialog`,defects);await closeModal(page,ro);
      if(index<2)await page.locator('.topbar-right button').tap();
    }
    await nav(1);await page.locator('.radio-toolbar .search-field').tap();await expect(page.locator('.keyboard-card')).toBeVisible();await capture(page,info,'keyboard',defects);
    await page.locator('.diacritics-row button').first().tap();await expect(page.locator('.keyboard-value')).toContainText('ă');await page.locator('.keyboard-card header button').tap();await expect(page.locator('.keyboard-card')).toHaveCount(0);
    await info.attach('layout-audit',{body:JSON.stringify(defects,null,2),contentType:'application/json'});
    expect.soft(defects).toEqual([]);expect(f.unexpected).toEqual([]);expect(errors).toEqual([]);
  });

  test(`first run and pairing ${theme}`,async({page},info)=> {
    const ro=info.project.name==='touch-ro',f=await fixture(page,ro?'ro':'en',theme,false),defects:string[]=[];
    await page.goto('/');await expect(page.locator('.setup-card')).toBeVisible();
    for(let step=0;step<4;step++){await capture(page,info,`setup-${step}`,defects);await page.locator('.setup-actions button.primary').tap();}
    await expect(page.locator('.home-layout')).toBeVisible();expect(f.state.preferences.setupComplete).toBe(true);
    f.state.bluetooth.prompts=[{id:'prompt-1',name:'Test speaker',kind:'confirmation',value:'123456'}];
    await expect(page.locator('.pair-code')).toBeVisible({timeout:6000});await capture(page,info,'pairing-confirmation',defects);
    await page.locator('.dialog-actions button').first().tap();await expect(page.locator('.pair-code')).toHaveCount(0);
    expect(f.actions.some(a=>a.path==='/api/bluetooth/reply'&&a.body.accept===false)).toBeTruthy();
    await info.attach('layout-audit',{body:JSON.stringify(defects,null,2),contentType:'application/json'});expect.soft(defects).toEqual([]);expect(f.unexpected).toEqual([]);
  });

  test(`backend failure keeps recovery reachable ${theme}`,async({page},info)=> {
    const ro=info.project.name==='touch-ro', f=await fixture(page,ro?'ro':'en',theme),defects:string[]=[];
    await page.goto('/');await expect(page.locator('.home-layout')).toBeVisible();f.backendDown=true;
    await expect(page.locator('.error-strip')).toBeVisible({timeout:6000});await capture(page,info,'backend-unavailable',defects);
    await page.locator('.main-nav button').nth(3).tap();await expect(page.locator('.settings-panel')).toBeVisible();
    f.backendDown=false;await expect.poll(()=>page.locator('.error-strip').count(),{timeout:6000}).toBe(0);
    await capture(page,info,'backend-recovered',defects);await info.attach('layout-audit',{body:JSON.stringify(defects,null,2),contentType:'application/json'});expect.soft(defects).toEqual([]);
  });
}
