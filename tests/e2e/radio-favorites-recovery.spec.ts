import {expect,test,type Page,type Locator} from '@playwright/test';

// Private proposal: faithful UUID-based backend semantics, no hardware/catalog requests.
const stationA={uuid:'11111111-1111-4111-8111-111111111111',name:'Same station name',url:'https://radio.example.org/a',country:'Romania',language:'Romanian',codec:'MP3'};
const stationB={uuid:'22222222-2222-4222-8222-222222222222',name:'Same station name',url:'https://radio.example.org/b',country:'Romania',language:'Romanian',codec:'MP3'};
type Mode='success'|'reject'|'accepted';
async function fixture(page:Page,ro:boolean,theme:string,mode:Mode='success',saved:any[]=[]){
 const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,favorites:saved.map(s=>({...s}))},network:{},bluetooth:{devices:[],prompts:[]},audio:{ready:true,volume:30},player:{state:'idle'},weather:{}};
 const writes:any[]=[];let reads=0,failRead=false,release!:()=>void;const gate=new Promise<void>(r=>release=r);
 await page.route('**/api/**',async route=>{const req=route.request(),path=new URL(req.url()).pathname;let json:any={ok:true};
  if(path==='/api/session')json={token:'fixture'};else if(path==='/api/state'){reads++;if(failRead){failRead=false;await route.fulfill({status:503,json:{error:'backend_unavailable'}});return;}json=state;}
  else if(path==='/api/radio')json={stations:[stationA,stationB]};
  else if(path==='/api/favorites'&&req.method()==='POST'){
   const body=req.postDataJSON();writes.push(body);if(writes.length===1&&mode!=='success'){await gate;if(mode==='reject'){await route.fulfill({status:500,json:{error:'preferences_unavailable'}});return;}}
   state.preferences.favorites=state.preferences.favorites.filter((s:any)=>s.uuid!==body.station.uuid);if(!body.remove)state.preferences.favorites.push({...body.station});if(mode==='accepted'&&writes.length===1)failRead=true;json=state.preferences;
  }
  await route.fulfill({json});
 });
 await page.goto('/');await page.locator('.main-nav button').nth(1).tap();await expect(page.locator('.station-row')).toHaveCount(2);return{state,writes,release,reads:()=>reads,heart:(index:number)=>page.locator('.station-row').nth(index).locator('.favorite-button')};
}
async function hit(button:Locator){const b=(await button.boundingBox())!;expect(b.width).toBeGreaterThanOrEqual(48);expect(b.height).toBeGreaterThanOrEqual(48);expect(b.x).toBeGreaterThanOrEqual(0);expect(b.y).toBeGreaterThanOrEqual(0);expect(b.x+b.width).toBeLessThanOrEqual(800);expect(b.y+b.height).toBeLessThanOrEqual(480);expect(await button.evaluate(el=>{const b=el.getBoundingClientRect();return el.contains(document.elementFromPoint(b.x+b.width/2,b.y+b.height/2));})).toBe(true);}
for(const theme of ['ink','night']){
 test(`Favorites ${theme}: same names stay separate by UUID through add remove and reload`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,'success',[stationB]);await expect(f.heart(0)).toHaveAttribute('aria-pressed','false');await expect(f.heart(1)).toHaveAttribute('aria-pressed','true');await hit(f.heart(0));await f.heart(0).tap();await expect.poll(()=>f.writes.length).toBe(1);expect(f.writes[0]).toEqual({station:stationA,remove:false});await expect(f.heart(0)).toHaveAttribute('aria-pressed','true');expect(f.state.preferences.favorites.map((s:any)=>s.uuid)).toEqual([stationB.uuid,stationA.uuid]);
  await page.locator('.favorites-filter').tap();await expect(page.locator('.station-row')).toHaveCount(2);await page.locator('.favorites-filter').tap();await f.heart(0).tap();await expect.poll(()=>f.writes.length).toBe(2);expect(f.writes[1]).toEqual({station:stationA,remove:true});await expect(f.heart(0)).toHaveAttribute('aria-pressed','false');await expect(f.heart(1)).toHaveAttribute('aria-pressed','true');expect(f.state.preferences.favorites).toEqual([stationB]);await page.reload();await page.locator('.main-nav button').nth(1).tap();await expect(f.heart(0)).toHaveAttribute('aria-pressed','false');await expect(f.heart(1)).toHaveAttribute('aria-pressed','true');
 });
 for(const remove of [false,true])test(`Favorites ${theme}: rejected ${remove?'remove':'add'} preserves heart and explicit Retry repeats exact station`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,'reject',remove?[stationA]:[]),expected={station:stationA,remove};await f.heart(0).tap();await expect.poll(()=>f.writes.length).toBe(1);expect(f.writes).toEqual([expected]);await expect(f.heart(0)).toBeDisabled();await f.heart(0).evaluate((el:HTMLButtonElement)=>el.click());expect(f.writes).toEqual([expected]);f.release();
  const banner=page.locator('.error-strip');await expect(banner).toBeVisible();await expect(f.heart(0)).toHaveAttribute('aria-pressed',String(remove));const retry=banner.getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true});await hit(retry);await retry.tap();await expect.poll(()=>f.writes.length,{message:'Rejected favorite Retry must replay the exact mutation, not merely read state'}).toBe(2);expect(f.writes).toEqual([expected,expected]);await expect(banner).toHaveCount(0);await expect(f.heart(0)).toHaveAttribute('aria-pressed',String(!remove));await page.reload();await page.locator('.main-nav button').nth(1).tap();await expect(f.heart(0)).toHaveAttribute('aria-pressed',String(!remove));
 });
 test(`Favorites ${theme}: accepted POST with failed confirmation only repeats state GET`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,'accepted');await f.heart(0).tap();await expect.poll(()=>f.writes.length).toBe(1);f.release();const banner=page.locator('.error-strip');await expect(banner).toBeVisible();expect(f.writes).toEqual([{station:stationA,remove:false}]);const reads=f.reads();const retry=banner.getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true});await hit(retry);await retry.tap();await expect.poll(()=>f.reads()).toBeGreaterThan(reads);await expect(banner).toHaveCount(0);expect(f.writes).toEqual([{station:stationA,remove:false}]);await expect(f.heart(0)).toHaveAttribute('aria-pressed','true');
 });
}
