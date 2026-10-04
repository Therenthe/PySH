import {expect,test,type Page,type Request} from '@playwright/test';

// Private supplemental contract tests. Synthetic data; no real device/catalog operations.
const station={uuid:'11111111-1111-4111-8111-111111111111',name:'Synthetic station with a meaningful long name',url:'https://radio.example.org/a',country:'Romania',language:'Romanian',codec:'MP3'};
type Origin='preferences'|'audio'|'bluetooth';
function gate(){let release!:()=>void;const promise=new Promise<void>(resolve=>release=resolve);return{promise,release};}
async function fixture(page:Page,ro:boolean,theme:string,origin:Origin){
 await page.clock.install();
 const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,accent:'sage',nightEnabled:false,screensaverMinutes:0,navigationCollapsed:false,navigationAutoHide:false,favorites:[]},network:{},bluetooth:{available:true,powered:true,devices:[],prompts:[]},audio:{available:true,ready:true,volume:30,mute:false,outputs:[]},player:{state:'idle'},weather:{}};
 const favoriteGate=gate(),staleGate=gate(),laterGate=gate(),writes:any[]=[],unexpected:string[]=[];
 let arm=false,heldRequest:Request|undefined,freeze=false,rejectFavorite=false;
 await page.route('**/api/**',async route=>{
  const req=route.request(),path=new URL(req.url()).pathname,method=req.method();
  if(path==='/api/session'){await route.fulfill({json:{token:'fixture'}});return;}
  if(path==='/api/radio'){await route.fulfill({json:{stations:[station]}});return;}
  if(path==='/api/favorites'&&method==='POST'){
   const body=req.postDataJSON();writes.push(body);
   if(rejectFavorite){await route.fulfill({status:503,json:{error:'preferences_unavailable'}});return;}
   await favoriteGate.promise;state.preferences.favorites=body.remove?[]:[{...body.station}];
   await route.fulfill({json:structuredClone(state.preferences)});return;
  }
  if(path==='/api/preferences'&&method==='PATCH'&&origin==='preferences'){
   Object.assign(state.preferences,req.postDataJSON());const old=structuredClone(state.preferences);heldRequest=req;
   // A harmless unrelated-field marker proves the delayed PATCH itself reached React,
   // after mutate() has performed its fresh GET. It is not the favorite assertion.
   state.preferences.accent='sage';await staleGate.promise;await route.fulfill({json:old});return;
  }
  if((path==='/api/audio'&&origin==='audio')||(path==='/api/bluetooth/scan'&&origin==='bluetooth')){
   arm=true;if(origin==='audio')Object.assign(state.audio,req.postDataJSON());
   await route.fulfill({json:origin==='audio'?{...state.audio,error:null}:{available:true,devices:[],error:null}});return;
  }
  if(path==='/api/state'){
   const snapshot=structuredClone(state);
   if(arm&&!heldRequest){arm=false;heldRequest=req;snapshot.preferences.accent='amber';await staleGate.promise;}
   else if(freeze)await laterGate.promise;
   await route.fulfill({json:snapshot});return;
  }
  unexpected.push(`${method} ${path}`);await route.fulfill({status:500,json:{error:'unexpected_test_request'}});
 });
 await page.goto('/');await page.locator('.main-nav button').nth(1).tap();
 const heart=page.locator('.station-row .favorite-button');await expect(heart).toBeVisible();
 return{state,writes,unexpected,heart,favoriteGate,staleGate,laterGate,held:()=>heldRequest,freeze:()=>{freeze=true;},reject:()=>{rejectFavorite=true;}};
}

for(const theme of ['ink','night'])for(const origin of ['preferences','audio','bluetooth'] as const){
 test(`UI35 cross-reader ${theme} delayed ${origin} response preserves acknowledged favorite`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,origin);
  // Start the favorite first: its independent lock permits the real audio/settings
  // action, whereas starting audio first correctly disables Radio's heart controls.
  await f.heart.tap();await expect.poll(()=>f.writes.length).toBe(1);
  if(origin==='preferences'){
   await page.locator('.main-nav button').nth(3).tap();await page.locator('.accent-choice.amber').tap();
  }else{
   await page.locator('.rail-bottom .status-button').nth(origin==='bluetooth'?1:2).tap();
   const dialog=page.getByRole('dialog',{name:origin==='bluetooth'?'Bluetooth':'Audio',exact:true});
   await dialog.getByRole('button',{name:origin==='bluetooth'?(ro?'Scanează':'Scan nearby'):(ro?'Fără sunet':'Mute'),exact:true}).tap();
   await dialog.locator('header').getByRole('button',{name:ro?'Închide':'Close',exact:true}).tap();
  }
  await expect.poll(()=>!!f.held()).toBe(true);
  f.favoriteGate.release();await expect(page.locator('[data-recovery=favorites]')).toHaveCount(0);
  await page.locator('.main-nav button').nth(1).tap();await expect(f.heart).toHaveAttribute('aria-pressed','true');
  await expect(page.locator('.app')).toHaveAttribute('data-accent','sage');
  await page.evaluate(()=>{
   const w=window as any;w.__crossFavoriteRegressed=false;
   w.__crossFavoriteObserver=new MutationObserver((records:MutationRecord[])=>{
    const heart=document.querySelector('.station-row .favorite-button');
    if(heart?.getAttribute('aria-pressed')==='false'||records.some(r=>r.target===heart&&r.attributeName==='aria-pressed'&&r.oldValue==='false'))w.__crossFavoriteRegressed=true;
   });w.__crossFavoriteObserver.observe(document.querySelector('.app')!,{subtree:true,attributes:true,attributeOldValue:true,childList:true,attributeFilter:['aria-pressed']});
  });
  // Frozen clock prevents new polling; GET-origin cases also gate subsequent reads.
  // PATCH needs its intentional fresh mutate GET to complete before savePrefs applies.
  if(origin!=='preferences')f.freeze();
  try{
   const response=page.waitForResponse(r=>r.request()===f.held());f.staleGate.release();await (await response).finished();
   await expect(page.locator('.app')).toHaveAttribute('data-accent','amber');
   await page.evaluate(()=>new Promise<void>(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve()))));
   await expect(f.heart).toHaveAttribute('aria-pressed','true');
   expect(await page.evaluate(()=>(window as any).__crossFavoriteRegressed)).toBe(false);
   expect(f.writes).toEqual([{station,remove:false}]);expect(f.state.preferences.favorites).toEqual([station]);
  }finally{f.laterGate.release();await page.evaluate(()=>(window as any).__crossFavoriteObserver.disconnect());}
  // Save the real failed-remove recovery banner in both locales/themes. A deliberately
  // rejected adapter response must retain the acknowledged heart and expose Retry.
  f.reject();await f.heart.tap();const banner=page.locator('[data-recovery=favorites][role=alert]');
  await expect(banner).toBeVisible();await expect(banner).toContainText(station.name);
  await expect(f.heart).toHaveAttribute('aria-pressed','true');
  const retry=banner.getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true});
  const b=(await retry.boundingBox())!;expect(b.width).toBeGreaterThanOrEqual(48);expect(b.height).toBeGreaterThanOrEqual(48);expect(b.x).toBeGreaterThanOrEqual(0);expect(b.y).toBeGreaterThanOrEqual(0);expect(b.x+b.width).toBeLessThanOrEqual(800);expect(b.y+b.height).toBeLessThanOrEqual(480);
  expect(await retry.evaluate(el=>{const r=el.getBoundingClientRect();return el.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2));})).toBe(true);
  await page.screenshot({path:info.outputPath(`favorites-failed-${origin}-${theme}-${ro?'ro':'en'}.png`)});
  expect(f.writes).toEqual([{station,remove:false},{station,remove:true}]);expect(f.unexpected).toEqual([]);
 });
}
