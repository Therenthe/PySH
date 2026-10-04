import {expect,test,type Page,type Request} from '@playwright/test';

// Synthetic adapter fixtures, exact backend string identities; no catalog/device execution.
const stationA={uuid:'11111111-1111-4111-8111-111111111111',name:'Synthetic shared station',url:'https://radio.example.org/a',country:'Romania',language:'Romanian',codec:'MP3'};
const stationB={...stationA,uuid:'22222222-2222-4222-8222-222222222222',url:'https://radio.example.org/b'};
function deferred(){let release!:()=>void;const promise=new Promise<void>(resolve=>release=resolve);return{promise,release};}
async function fixture(page:Page,ro:boolean,theme:string,options:{mode?:'success'|'reject'|'accepted';saved?:any[];stations?:any[]}={}){
 await page.clock.install();const stations=options.stations||[stationA,stationB],state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,accent:'sage',nightEnabled:false,screensaverMinutes:0,navigationCollapsed:false,navigationAutoHide:false,favorites:structuredClone(options.saved||[])},network:{},bluetooth:{devices:[],prompts:[]},audio:{ready:true,volume:30,mute:false},player:{state:'idle'},weather:{}};
 const writes:any[]=[],postGate=deferred(),staleGate=deferred(),laterGate=deferred();let stateReads=0,stateFailure=false,holdNext=false,staleStarted=false,staleRequest:Request|undefined,freezeLater=false;
 await page.route('**/api/**',async route=>{
  const req=route.request(),path=new URL(req.url()).pathname;
  if(path==='/api/state'){
   stateReads++;if(holdNext){holdNext=false;staleStarted=true;staleRequest=req;const old=structuredClone(state);old.preferences.accent='amber';await staleGate.promise;await route.fulfill({json:old});return;}
   if(freezeLater)await laterGate.promise;
   if(stateFailure){await route.fulfill({status:503,json:{error:'backend_unavailable'}});return;}
   await route.fulfill({json:state});return;
  }
  if(path==='/api/favorites'&&req.method()==='POST'){
   const body=req.postDataJSON();writes.push(body);
   if(writes.length===1&&options.mode&&options.mode!=='success'){await postGate.promise;if(options.mode==='reject'){await route.fulfill({status:500,json:{error:'preferences_unavailable'}});return;}}
   state.preferences.favorites=state.preferences.favorites.filter((s:any)=>s.uuid!==body.station.uuid);if(!body.remove)state.preferences.favorites.push({...body.station});if(writes.length===1&&options.mode==='accepted')stateFailure=true;
   // Actual backend returns persisted full Preferences, not {ok:true}.
   await route.fulfill({json:state.preferences});return;
  }
  await route.fulfill({json:path==='/api/session'?{token:'fixture'}:path==='/api/radio'?{stations}:{ok:true}});
 });
 await page.goto('/');await page.locator('.main-nav button').nth(1).tap();await expect(page.locator('.station-row')).toHaveCount(stations.length);
 return{state,writes,postGate,staleGate,laterGate,reads:()=>stateReads,heart:(index:number)=>page.locator('.station-row').nth(index).locator('.favorite-button'),holdNextState:()=>{holdNext=true;},staleStarted:()=>staleStarted,staleRequest:()=>staleRequest,freezeLaterStates:()=>{freezeLater=true;},stateFailureOff:()=>{stateFailure=false;}};
}
async function frames(page:Page){await page.evaluate(()=>new Promise<void>(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve()))));}

for(const theme of ['ink','night']){
 test(`UI35 ${theme} valid legacy identity strings remain exact instead of name or lowercase equality`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),a={...stationA,uuid:' Legacy-Case-A '},b={...stationB,uuid:'legacy-case-a'},f=await fixture(page,ro,theme,{stations:[a,b],saved:[b]});await expect(f.heart(0)).toHaveAttribute('aria-pressed','false');await f.heart(0).tap();await expect.poll(()=>f.writes.length).toBe(1);expect(f.writes).toEqual([{station:a,remove:false}]);await expect(f.heart(0)).toHaveAttribute('aria-pressed','true');expect(f.state.preferences.favorites.map((s:any)=>s.uuid)).toEqual([b.uuid,a.uuid]);await f.heart(0).tap();await expect.poll(()=>f.writes.length).toBe(2);expect(f.writes[1]).toEqual({station:a,remove:true});expect(f.state.preferences.favorites).toEqual([b]);
 });

 test(`UI35 ${theme} name fallback is used only without an accepted station identity`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),a={name:'Synthetic legacy without identity',url:stationA.url,country:'Romania'},saved={...a,uuid:a.name},f=await fixture(page,ro,theme,{stations:[a],saved:[saved]});await expect(f.heart(0)).toHaveAttribute('aria-pressed','true');await f.heart(0).tap();await expect.poll(()=>f.writes.length).toBe(1);expect(f.writes).toEqual([{station:saved,remove:true}]);await expect(f.heart(0)).toHaveAttribute('aria-pressed','false');await page.reload();await page.locator('.main-nav button').nth(1).tap();await expect(f.heart(0)).toHaveAttribute('aria-pressed','false');
 });

 test(`UI35 ${theme} stale ordinary state response cannot restore pre-save favorites`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme);f.holdNextState();await page.clock.runFor(2600);await expect.poll(f.staleStarted).toBe(true);await f.heart(0).tap();await expect(f.heart(0)).toHaveAttribute('aria-pressed','true');await expect(page.locator('[data-recovery=favorites]')).toHaveCount(0);
  // Prevent a later fresh poll masking an old response regression before the negative assertion.
  await expect(page.locator('.app')).toHaveAttribute('data-accent','sage');
  await page.evaluate(()=>{
   const probe={regressed:false,observer:null as MutationObserver|null};(window as any).__favoriteProbe=probe;
   const first=()=>document.querySelector('.station-row .favorite-button');
   probe.observer=new MutationObserver(records=>{
    const heart=first();if(heart?.getAttribute('aria-pressed')==='false')probe.regressed=true;
    // oldValue=false also catches a false->true recovery batched before the callback.
    if(records.some(r=>r.type==='attributes'&&r.attributeName==='aria-pressed'&&r.target===heart&&r.oldValue==='false'))probe.regressed=true;
   });probe.observer.observe(document.querySelector('.app')!,{subtree:true,childList:true,attributes:true,attributeOldValue:true,attributeFilter:['aria-pressed']});
  });
  f.freezeLaterStates();try{
   const response=page.waitForResponse(r=>r.request()===f.staleRequest());f.staleGate.release();await (await response).finished();
   // Positive commit witness: this marker exists only in the held stale snapshot.
   await expect(page.locator('.app')).toHaveAttribute('data-accent','amber');await frames(page);
   await expect(f.heart(0)).toHaveAttribute('aria-pressed','true');expect(await page.evaluate(()=>(window as any).__favoriteProbe.regressed)).toBe(false);expect(f.writes).toEqual([{station:stationA,remove:false}]);
  }finally{f.laterGate.release();await page.evaluate(()=>(window as any).__favoriteProbe.observer.disconnect());}
 });

 test(`UI35 ${theme} pending rejected favorite survives navigation and same-frame Retry posts once`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,{mode:'reject'});await f.heart(0).evaluate((el:HTMLButtonElement)=>{el.click();el.click();});await expect.poll(()=>f.writes.length).toBe(1);await expect(f.heart(0)).toBeDisabled();await expect(page.locator('.station-main').first()).toBeEnabled();await page.locator('.main-nav button').nth(0).tap();const banner=page.locator('[data-recovery=favorites]');await expect(banner).toHaveAttribute('role','status');await expect(banner).toContainText(stationA.name);const response=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/favorites');f.postGate.release();await (await response).finished();await frames(page);await expect(banner).toHaveAttribute('role','alert');const retry=banner.getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true});await retry.evaluate((el:HTMLButtonElement)=>{el.click();el.click();});await expect.poll(()=>f.writes.length).toBe(2);expect(f.writes).toEqual([{station:stationA,remove:false},{station:stationA,remove:false}]);await expect(banner).toHaveCount(0);await page.locator('.main-nav button').nth(1).tap();await expect(f.heart(0)).toHaveAttribute('aria-pressed','true');
 });

 test(`UI35 ${theme} accepted change GET-only recovery remains owned after leaving Radio`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,{mode:'accepted'});await f.heart(0).tap();await page.locator('.main-nav button').nth(0).tap();f.postGate.release();const banner=page.locator('[data-recovery=favorites][role=alert]');await expect(banner).toContainText(ro?'a fost acceptată':'accepted');await expect(banner).toContainText(stationA.name);expect(f.writes).toEqual([{station:stationA,remove:false}]);const reads=f.reads();f.stateFailureOff();await banner.getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true}).tap();await expect(banner).toHaveCount(0);expect(f.reads()).toBeGreaterThan(reads);expect(f.writes).toHaveLength(1);await page.locator('.main-nav button').nth(1).tap();await expect(f.heart(0)).toHaveAttribute('aria-pressed','true');
 });

 test(`UI35 ${theme} accepted remove uses returned authoritative favorites and never retries POST`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,{mode:'accepted',saved:[stationA]});await f.heart(0).tap();f.postGate.release();const banner=page.locator('[data-recovery=favorites][role=alert]');await expect(banner).toBeVisible();await expect(f.heart(0)).toHaveAttribute('aria-pressed','false');expect(f.writes).toEqual([{station:stationA,remove:true}]);f.stateFailureOff();await banner.getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true}).tap();await expect(banner).toHaveCount(0);expect(f.writes).toHaveLength(1);await expect(f.heart(0)).toHaveAttribute('aria-pressed','false');await page.reload();await page.locator('.main-nav button').nth(1).tap();await expect(f.heart(0)).toHaveAttribute('aria-pressed','false');
 });
}
