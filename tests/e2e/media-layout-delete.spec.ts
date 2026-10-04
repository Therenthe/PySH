import {test,expect,type Page} from '@playwright/test';
import type {MediaListing} from '../../app/ui/src/Media';

async function mediaFixture(page:Page,language:'en'|'ro',theme:'ink'|'night'){
 const folder='/library/Albums',song='/library/Școală în oraș.mp3';
 const rootItems=[{name:'Albums',path:folder,is_dir:true},{name:'Școală în oraș.mp3',path:song,kind:'audio',size:1500000,deletable:true,delete_token:'fixture-song-token'},{name:'Film.webm',path:'/library/Film.webm',kind:'video',size:43000000,deletable:true,delete_token:'fixture-film-token'},{name:'Read only.wav',path:'/library/Read only.wav',kind:'audio',deletable:false}];
 const listing:MediaListing&{items:typeof rootItems}={path:'/library',parent:null,items:rootItems};
 const state:any={preferences:{language,theme,setupComplete:true,screensaverMinutes:0,nightEnabled:false,navigationCollapsed:false,navigationAutoHide:false},network:{},bluetooth:{devices:[],prompts:[]},audio:{ready:true,volume:30,mute:false},player:{state:'idle'},weather:{}};
 const requested:string[]=[],mutations:any[]=[],control={failDelete:false,failNextListing:false,partialNextListing:false,malformedNextListing:false,loseDelete:'none' as 'none'|'absent'|'replacement'|'retained'};let gate:Promise<void>|undefined,release=()=>{};
 await page.route('**/api/**',async route=>{
  const req=route.request(),u=new URL(req.url());let json:any={ok:true};
  if(u.pathname==='/api/session')json={token:'fixture'};
  else if(u.pathname==='/api/state')json=state;
  else if(u.pathname==='/api/media'&&req.method()==='GET'){
   const target=u.searchParams.get('path')||'';requested.push(target);
   if(control.failNextListing){control.failNextListing=false;return route.fulfill({status:503,json:{error:'media_unavailable'}});}
   if(control.partialNextListing){control.partialNextListing=false;return route.fulfill({json:{...listing,items:[],partial:true}});}
   if(control.malformedNextListing){control.malformedNextListing=false;return route.fulfill({json:{path:listing.path}});}
   json=target===folder?{path:folder,parent:'/library',items:[{name:'Track.mp3',path:folder+'/Track.mp3',kind:'audio',size:2000000,deletable:true,delete_token:'fixture-track-token'}]}:listing;
  }else if(req.method()!=='GET'){
   const body=req.postDataJSON();mutations.push({url:u.pathname,method:req.method(),body});
   if(u.pathname==='/api/media'&&req.method()==='DELETE'){
    if(gate)await gate;if(control.failDelete){control.failDelete=false;return route.fulfill({status:503,json:{error:'operation_failed'}});}
    if(control.loseDelete==='replacement')listing.items=listing.items.map(item=>item.path===body.path?{...item,delete_token:'replacement-token'}:item);
    else if(control.loseDelete!=='retained')listing.items=listing.items.filter(item=>item.path!==body.path);
    if(control.loseDelete!=='none'){control.loseDelete='none';return route.abort('failed');}
    json={deleted:true};
   }
  }
  await route.fulfill({json});
 });
 await page.goto('/');await page.locator('.main-nav button').nth(2).tap();await expect(page.locator('.media-redesign')).toBeVisible();await expect(page.locator('.media-item')).toHaveCount(4);return{requested,mutations,listing,state,song,control,holdDelete:()=>{gate=new Promise<void>(resolve=>release=resolve);},releaseDelete:()=>{release();gate=undefined;}};
}

for(const theme of ['ink','night'] as const){
 test(`Media ${theme} initial loading is not mistaken for an empty approved folder`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),state={preferences:{language:ro?'ro':'en',theme,setupComplete:true,screensaverMinutes:0,nightEnabled:false},network:{},bluetooth:{devices:[],prompts:[]},audio:{ready:true},player:{state:'idle'},weather:{}};let release!:()=>void,requested=false;const gate=new Promise<void>(resolve=>release=resolve);
  await page.route('**/api/**',async route=>{const path=new URL(route.request().url()).pathname;if(path==='/api/media'){requested=true;await gate;return route.fulfill({json:{path:'/home/pysh/Music',parent:null,items:[]}});}await route.fulfill({json:path==='/api/session'?{token:'fixture'}:path==='/api/state'?state:{ok:true}});});
  await page.goto('/');await page.locator('.main-nav button').nth(2).tap();await expect.poll(()=>requested).toBe(true);await expect(page.locator('.media-library')).toHaveAttribute('aria-busy','true');await expect(page.locator('.media-items .empty-state')).toHaveCount(0);await expect(page.locator('.media-pending')).toContainText(ro?'Se încarcă':'Loading');release();await expect(page.locator('.media-items .empty-state')).toContainText(ro?'Acest dosar este gol':'This folder is empty');await expect(page.locator('.library-path b')).toHaveText('Music');await expect(page.getByRole('button',{name:ro?'Dosarul anterior':'Up one level',exact:true})).toHaveCount(0);const library=page.locator('.crumb-actions').getByRole('button',{name:ro?'Bibliotecă media':'Media library',exact:true});await expect(library).toBeVisible();await library.tap();
 });

 test(`Media ${theme} coherent source navigation and file action geometry`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),lang=ro?'ro':'en';const f=await mediaFixture(page,lang,theme);
  await expect(page.getByRole('button',{name:ro?'Dosarul anterior':'Up one level',exact:true})).toHaveCount(0);
  await expect(page.locator('.crumb-actions').getByRole('button',{name:ro?'Bibliotecă media':'Media library',exact:true})).toBeVisible();
  await expect(page.locator('.media-query')).toHaveCount(0);await expect(page.locator('.service-row')).toHaveCount(0);
  await expect(page.locator('.media-delete')).toHaveCount(2);await expect(page.locator('.media-entry').filter({hasText:'Albums'}).locator('.media-delete')).toHaveCount(0);await expect(page.locator('.media-entry').filter({hasText:'Read only.wav'}).locator('.media-delete')).toHaveCount(0);
  const targets=await page.locator('.media-redesign button:visible').evaluateAll(els=>els.map(el=>{const r=el.getBoundingClientRect();return{label:el.textContent||el.getAttribute('aria-label'),w:r.width,h:r.height,x:r.x,y:r.y};}));for(const button of targets){expect(button.w,`${button.label}: width`).toBeGreaterThanOrEqual(48);expect(button.h,`${button.label}: height`).toBeGreaterThanOrEqual(48);expect(button.x+button.w).toBeLessThanOrEqual(800);}
  expect(await page.locator('.media-items').evaluate(el=>getComputedStyle(el).scrollbarWidth)).toBe('none');
  await page.screenshot({path:info.outputPath(`media-library-${theme}.png`)});
  await page.locator('.media-item').filter({hasText:'Albums'}).tap();await expect(page.locator('.library-path b')).toHaveText('Albums');await expect(page.locator('.library-path b')).not.toContainText('/library');await expect(page.getByRole('button',{name:ro?'Dosarul anterior':'Up one level',exact:true})).toBeVisible();await page.getByRole('button',{name:ro?'Dosarul anterior':'Up one level',exact:true}).tap();expect(f.requested.at(-1)).toBe('/library');await expect(page.locator('.media-item')).toHaveCount(4);
  await page.locator('.media-sections').getByRole('button',{name:ro?'Servicii':'Services',exact:true}).tap();await expect(page.locator('.service-row')).toHaveCount(3);await expect(page.locator('.media-items')).toHaveCount(0);await page.screenshot({path:info.outputPath(`media-services-${theme}.png`)});
  await page.locator('.service-row').filter({hasText:'Netflix'}).tap();await expect.poll(()=>f.mutations.length).toBe(1);expect(f.mutations[0].body).toMatchObject({service:'netflix'});
 });

 test(`Media ${theme} touch search is optional insensitive and cancel preserves filter`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),lang=ro?'ro':'en';await mediaFixture(page,lang,theme);const search=page.getByRole('button',{name:ro?'Caută în acest dosar':'Search this folder',exact:true});
  await search.tap();await expect(page.locator('.keyboard-card')).toBeVisible();await page.locator('.keyboard-card header').getByRole('button',{name:ro?'Închide':'Close',exact:true}).tap();await expect(page.locator('.media-query')).toHaveCount(0);await expect(page.locator('.media-item')).toHaveCount(4);
  await search.tap();for(const c of 'scoala')await page.locator('.key-row:not(.diacritics-row)').getByRole('button',{name:c,exact:true}).tap();await page.locator('.final-row').getByRole('button',{name:ro?'Aplică':'Apply',exact:true}).tap();await expect(page.locator('.keyboard-card')).toHaveCount(0);await expect(page.locator('.media-item')).toHaveCount(1);await expect(page.locator('.media-item')).toContainText('Școală în oraș.mp3');await expect(page.locator('.media-query')).toContainText('scoala');
  await search.tap();await page.locator('.key-row:not(.diacritics-row)').getByRole('button',{name:'x',exact:true}).tap();await page.locator('.keyboard-card header').getByRole('button',{name:ro?'Închide':'Close',exact:true}).tap();await expect(page.locator('.media-query')).toContainText('scoala');await expect(page.locator('.media-query')).not.toContainText('scoalax');await expect(page.locator('.media-item')).toHaveCount(1);
  await page.screenshot({path:info.outputPath(`media-search-${theme}.png`)});await page.getByRole('button',{name:ro?'Șterge căutarea':'Clear search',exact:true}).tap();await expect(page.locator('.media-query')).toHaveCount(0);await expect(page.locator('.media-item')).toHaveCount(4);
 });

 test(`Media ${theme} delete requires confirmation and locks repeated pending taps`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),lang=ro?'ro':'en',f=await mediaFixture(page,lang,theme),deleteLabel=ro?'Șterge fișierul':'Delete file';
  const remove=page.getByRole('button',{name:`${deleteLabel}: Școală în oraș.mp3`,exact:true});await remove.tap();const dialog=page.getByRole('dialog',{name:ro?'Ștergi acest fișier?':'Delete this file?',exact:true});await expect(dialog).toContainText('Școală în oraș.mp3');await dialog.getByRole('button',{name:ro?'Anulează':'Cancel',exact:true}).tap();expect(f.mutations).toHaveLength(0);await expect(page.locator('.media-item')).toHaveCount(4);
  f.holdDelete();await remove.tap();await page.screenshot({path:info.outputPath(`media-delete-confirm-${theme}.png`)});await dialog.getByRole('button',{name:deleteLabel,exact:true}).tap();await expect.poll(()=>f.mutations.length).toBe(1);expect(f.mutations[0]).toEqual({url:'/api/media',method:'DELETE',body:{path:f.song,token:'fixture-song-token'}});await expect(dialog.getByRole('button',{name:ro?'Anulează':'Cancel',exact:true})).toBeDisabled();await expect(dialog.getByRole('button',{name:ro?'Se șterge…':'Deleting…',exact:true})).toBeDisabled();expect(await page.locator('.media-delete').evaluateAll(buttons=>buttons.every(button=>(button as HTMLButtonElement).disabled))).toBe(true);
  await dialog.locator('button').evaluateAll(buttons=>buttons.forEach(button=>(button as HTMLButtonElement).click()));expect(f.mutations).toHaveLength(1);f.releaseDelete();await expect(dialog).toHaveCount(0);await expect(page.locator('.media-item')).toHaveCount(3);await expect(page.locator('.media-item').filter({hasText:'Școală în oraș.mp3'})).toHaveCount(0);
 });

 test(`Media ${theme} rejected delete retries exact file token`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),lang=ro?'ro':'en',f=await mediaFixture(page,lang,theme),deleteLabel=ro?'Șterge fișierul':'Delete file';f.control.failDelete=true;
  await page.getByRole('button',{name:`${deleteLabel}: Școală în oraș.mp3`,exact:true}).tap();const dialog=page.getByRole('dialog',{name:ro?'Ștergi acest fișier?':'Delete this file?',exact:true});await dialog.getByRole('button',{name:deleteLabel,exact:true}).tap();await expect(dialog.getByRole('alert')).toBeVisible();await expect(dialog).toContainText('Școală în oraș.mp3');await expect(page.locator('.media-item')).toHaveCount(4);await page.screenshot({path:info.outputPath(`media-delete-failed-${theme}.png`)});await dialog.getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true}).tap();await expect(dialog).toHaveCount(0);expect(f.mutations).toHaveLength(2);expect(f.mutations[1]).toEqual(f.mutations[0]);await expect(page.locator('.media-item')).toHaveCount(3);
 });

 test(`Media ${theme} acknowledged delete with unavailable listing retries read only`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),lang=ro?'ro':'en',f=await mediaFixture(page,lang,theme),deleteLabel=ro?'Șterge fișierul':'Delete file';f.control.failNextListing=true;
  await page.getByRole('button',{name:`${deleteLabel}: Școală în oraș.mp3`,exact:true}).tap();const dialog=page.getByRole('dialog',{name:ro?'Ștergi acest fișier?':'Delete this file?',exact:true});await dialog.getByRole('button',{name:deleteLabel,exact:true}).tap();await expect(dialog.getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true})).toBeVisible();expect(f.mutations.filter(x=>x.method==='DELETE')).toHaveLength(1);const before=f.requested.length;await dialog.getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true}).tap();await expect(dialog).toHaveCount(0);await expect(page.locator('.media-item')).toHaveCount(3);expect(f.requested.length).toBe(before+1);expect(f.mutations.filter(x=>x.method==='DELETE')).toHaveLength(1);
 });

 test(`Media ${theme} active local file cannot be deleted`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await mediaFixture(page,ro?'ro':'en',theme),deleteLabel=ro?'Șterge fișierul':'Delete file';f.state.player={state:'playing',kind:'audio',url:f.song,title:'Școală în oraș.mp3',duration:300,position:1};
  const remove=page.getByRole('button',{name:`${deleteLabel}: Școală în oraș.mp3`,exact:true});await expect(remove).toBeDisabled();await expect(remove).toHaveAttribute('title',ro?'Oprește redarea înainte de ștergere':'Stop playback before deleting');await remove.evaluate(button=>(button as HTMLButtonElement).click());await expect(page.getByRole('dialog',{name:ro?'Ștergi acest fișier?':'Delete this file?',exact:true})).toHaveCount(0);expect(f.mutations).toHaveLength(0);await expect(page.getByRole('button',{name:`${deleteLabel}: Film.webm`,exact:true})).toBeEnabled();
 });

 for(const outcome of ['absent','replacement'] as const)test(`Media ${theme} lost delete response checks ${outcome} before another mutation`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await mediaFixture(page,ro?'ro':'en',theme),deleteLabel=ro?'Șterge fișierul':'Delete file';f.control.loseDelete=outcome;
  await page.getByRole('button',{name:`${deleteLabel}: Școală în oraș.mp3`,exact:true}).tap();const dialog=page.getByRole('dialog',{name:ro?'Ștergi acest fișier?':'Delete this file?',exact:true});await dialog.getByRole('button',{name:deleteLabel,exact:true}).tap();
  if(outcome==='absent'){await expect(dialog).toHaveCount(0);await expect(page.locator('.media-item')).toHaveCount(3);}else{await expect(dialog.getByRole('alert')).toBeVisible();const retry=dialog.getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true});await expect(retry).toBeDisabled();await retry.evaluate(button=>(button as HTMLButtonElement).click());await expect(dialog).toContainText('Școală în oraș.mp3');expect(f.listing.items.find(item=>item.path===f.song)?.delete_token).toBe('replacement-token');}
  expect(f.requested).toHaveLength(2);expect(f.mutations.filter(x=>x.method==='DELETE')).toHaveLength(1);
 });

 test(`Media ${theme} lost response retaining original token waits for explicit retry`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await mediaFixture(page,ro?'ro':'en',theme),deleteLabel=ro?'Șterge fișierul':'Delete file';f.control.loseDelete='retained';
  await page.getByRole('button',{name:`${deleteLabel}: Școală în oraș.mp3`,exact:true}).tap();const dialog=page.getByRole('dialog',{name:ro?'Ștergi acest fișier?':'Delete this file?',exact:true});await dialog.getByRole('button',{name:deleteLabel,exact:true}).tap();await expect(dialog.getByRole('alert')).toContainText(ro?'Fișierul original este încă prezent':'original file is still present');expect(f.requested).toHaveLength(2);expect(f.mutations).toHaveLength(1);await expect(page.locator('.media-item')).toHaveCount(4);await dialog.getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true}).tap();await expect(dialog).toHaveCount(0);expect(f.mutations).toHaveLength(2);expect(f.mutations[1]).toEqual(f.mutations[0]);await expect(page.locator('.media-item')).toHaveCount(3);
 });

 for(const incomplete of ['partial','malformed'] as const)test(`Media ${theme} lost response ${incomplete} listing cannot prove deletion`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await mediaFixture(page,ro?'ro':'en',theme),deleteLabel=ro?'Șterge fișierul':'Delete file';f.control.loseDelete='absent';if(incomplete==='partial')f.control.partialNextListing=true;else f.control.malformedNextListing=true;
  await page.getByRole('button',{name:`${deleteLabel}: Școală în oraș.mp3`,exact:true}).tap();const dialog=page.getByRole('dialog',{name:ro?'Ștergi acest fișier?':'Delete this file?',exact:true});await dialog.getByRole('button',{name:deleteLabel,exact:true}).tap();await expect(dialog.getByRole('alert')).toBeVisible();await expect(dialog).toContainText('Școală în oraș.mp3');await expect(page.locator('.media-item')).toHaveCount(4);expect(f.mutations.filter(x=>x.method==='DELETE')).toHaveLength(1);
  const before=f.requested.length;await dialog.getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true}).tap();await expect(dialog).toHaveCount(0);expect(f.requested.length).toBe(before+1);expect(f.mutations.filter(x=>x.method==='DELETE')).toHaveLength(1);await expect(page.locator('.media-item')).toHaveCount(3);
 });
}
