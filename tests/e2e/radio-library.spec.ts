import {test,expect,type Page,type Locator} from '@playwright/test';
import {textLegibility} from './legibility';

// Browser-only catalog/artwork fixtures. No real station, weather or device is contacted.
const artworkOrigin='https://radio-artwork.pysh-uat.org';
const logo=artworkOrigin+'/station.svg',brokenLogo=artworkOrigin+'/broken.svg';
const unsafeLogos=['http://radio-artwork.pysh-uat.org/insecure.svg','https://127.0.0.1/private.svg','https://192.168.100.1/private.svg'];
const station={uuid:'11111111-1111-4111-8111-111111111111',name:'Radio România Cultural',url:'https://stream.pysh-uat.org/cultural',favicon:logo,country:'România',language:'Română',codec:'MP3'};
const second={uuid:'22222222-2222-4222-8222-222222222222',name:'City Jazz',url:'https://stream.pysh-uat.org/jazz',favicon:logo,country:'United Kingdom',language:'English',codec:'AAC'};
const normalize=(value:string)=>value.normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
type Options={catalog?:any[];favorites?:any[];current?:any;playerState?:string;title?:string};
async function fixture(page:Page,ro:boolean,theme:string,options:Options={}){
 const current=options.current??station,catalog=options.catalog??[station,second];
 const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,visualizerStyle:'off',navigationCollapsed:false,navigationAutoHide:false,homeCards:[],shortcuts:[],favorites:options.favorites??[station],lastStation:{...current}},network:{available:true,state:'connected',active_type:'ethernet',devices:[]},bluetooth:{available:true,powered:false,devices:[],prompts:[]},audio:{available:true,ready:true,volume:40,mute:false,output:'fixture-speaker',outputs:[{id:'fixture-speaker',description:'Fixture speaker',active:true}]},player:{kind:'radio',state:options.playerState??'playing',url:current.url||current.url_resolved,station_name:current.name,title:options.title??'Fixture artist — Fixture song'},weather:{}};
 const actions:{path:string;body:any}[]=[],queries:{q:string;country:string;language:string}[]=[],errors:string[]=[],assetRequests:string[]=[],unsafeRequests:string[]=[];
 page.on('pageerror',error=>errors.push(String(error)));
 await page.route(url=>unsafeLogos.includes(url.href),async route=>{unsafeRequests.push(route.request().url());await route.abort('blockedbyclient');});
 await page.route(artworkOrigin+'/**',async route=>{
  assetRequests.push(route.request().url());
  if(route.request().url()===brokenLogo){await route.fulfill({contentType:'image/svg+xml',body:'This fixture intentionally is not an image.'});return;}
  await route.fulfill({contentType:'image/svg+xml',body:'<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128"><rect width="128" height="128" rx="20" fill="#244b43"/><circle cx="64" cy="64" r="30" fill="#e4ede5"/></svg>'});
 });
 await page.route('**/api/**',async route=>{
  const request=route.request(),url=new URL(request.url()),path=url.pathname;let json:any={ok:true};
  if(path==='/api/session')json={token:'isolated-radio-library'};
  else if(path==='/api/state')json=state;
  else if(path==='/api/radio'){
   const filters={q:url.searchParams.get('q')??'',country:url.searchParams.get('country')??'',language:url.searchParams.get('language')??''};queries.push(filters);
   json={stations:catalog.filter(item=>normalize(item.name??'').includes(normalize(filters.q))&&normalize(item.country??'').includes(normalize(filters.country))&&normalize(item.language??'').includes(normalize(filters.language)))};
  }else if(path==='/api/media')json={items:[],roots:[]};
  if(request.method()!=='GET'){
   const body=request.postDataJSON();actions.push({path,body});
   if(path==='/api/audio'){Object.assign(state.audio,body);json=state.audio;}
   else if(path==='/api/preferences'){Object.assign(state.preferences,body);json=state.preferences;}
   else if(path==='/api/player'){state.player.state=body.action==='pause'?'paused':body.action==='stop'?'idle':'playing';json=state.player;}
  }
  await route.fulfill({json});
 });
 await page.clock.install({time:new Date('2026-10-25T10:00:00Z')});
 await page.goto('/');await expect(page.locator('.ambient-home')).toBeVisible();
 await page.locator('.main-nav button').nth(1).tap();await expect(page.locator('.radio-page')).toBeVisible();
 await expect(page.locator('.station-row')).toHaveCount(catalog.length);
 return{state,actions,queries,errors,assetRequests,unsafeRequests};
}
const favorites=(page:Page)=>page.locator('.favorites-filter');
const discover=(page:Page)=>page.locator('.discover-filter');
const row=(page:Page,name:string)=>page.locator('.station-row').filter({hasText:name});
async function hit48(control:Locator){
 const box=await control.boundingBox();expect(box).not.toBeNull();
 expect(box!.width).toBeGreaterThanOrEqual(47.999);expect(box!.height).toBeGreaterThanOrEqual(47.999);
 expect(box!.x).toBeGreaterThanOrEqual(-.001);expect(box!.y).toBeGreaterThanOrEqual(-.001);
 expect(box!.x+box!.width).toBeLessThanOrEqual(800.001);expect(box!.y+box!.height).toBeLessThanOrEqual(480.001);
 expect(await control.evaluate(node=>{const r=node.getBoundingClientRect();return node.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2));})).toBe(true);
}
async function filter(page:Page,selector:string,value:string,ro:boolean){
 await page.locator(selector).tap();const keyboard=page.locator('.keyboard-card');await expect(keyboard).toBeVisible();
 const clear=keyboard.locator('.keyboard-clear');if(await clear.isEnabled())await clear.tap();let caps=false;
 for(const character of value){
  if(character===' '){await keyboard.locator('.space-key').tap();continue;}
  const upper=character.toUpperCase()===character&&character.toLowerCase()!==character;
  if(upper!==caps){await keyboard.locator('.final-row [aria-pressed]').tap();caps=upper;}
  await keyboard.locator('.keys').getByRole('button',{name:character,exact:true}).tap();
 }
 await keyboard.getByRole('button',{name:ro?'Aplică':'Apply',exact:true}).tap();
 await expect(keyboard).toHaveCount(0);
}
async function decoded(image:Locator){
 await image.scrollIntoViewIfNeeded();await image.evaluate(node=>(node as HTMLImageElement).decode());
 expect(await image.evaluate(node=>{const image=node as HTMLImageElement;return image.complete&&image.naturalWidth===128&&image.naturalHeight===128;})).toBe(true);
 await expect(image).toHaveAttribute('referrerpolicy','no-referrer');
}

for(const theme of ['ink','night'] as const){
 test(`Radio library ${theme}: a resolved stream still selects its catalog station`,async({page},info)=>{
  const resolved='https://stream.pysh-uat.org/final-stream',catalogStation={...station,url:'https://stream.pysh-uat.org/redirect',url_resolved:resolved};
  const f=await fixture(page,info.project.name.endsWith('ro'),theme,{catalog:[catalogStation,second],current:{...catalogStation,url:resolved},favorites:[]});
  await expect(page.locator('.radio-station-name')).toHaveText(station.name);
  await expect(row(page,station.name)).toHaveClass(/\bselected\b/);
  expect(f.actions).toEqual([]);expect(f.errors).toEqual([]);
  await page.screenshot({path:info.outputPath('radio-resolved-selected.png')});
 });

 test(`Radio library ${theme}: explicit collections retain all filters and selected-tab taps do nothing`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme),player=JSON.stringify(f.state.player);
  await expect(discover(page)).toHaveAccessibleName(ro?'Descoperă':'Discover');await expect(favorites(page)).toHaveAccessibleName(ro?'Favorite':'Favorites');
  await hit48(discover(page));await hit48(favorites(page));await expect(discover(page)).toHaveAttribute('aria-pressed','true');
  const initialReads=f.queries.length;await discover(page).tap();await expect(discover(page)).toHaveAttribute('aria-pressed','true');expect(f.queries).toHaveLength(initialReads);
  await filter(page,'.radio-search-row .search-field','rOmÂnIa',ro);
  await filter(page,'.radio-filter-pills .filter-button:first-child','rOmÂnIa',ro);
  await filter(page,'.radio-filter-pills .filter-button:nth-child(2)','rOmÂnĂ',ro);
  await expect(page.locator('.station-row')).toHaveCount(1);
  const selectedFilters={q:'rOmÂnIa',country:'rOmÂnIa',language:'rOmÂnĂ'};await expect.poll(()=>f.queries.at(-1)).toEqual(selectedFilters);
  await favorites(page).tap();await expect(favorites(page)).toHaveAttribute('aria-pressed','true');await expect(row(page,station.name)).toBeVisible();
  const reads=f.queries.length;await favorites(page).tap();await expect(favorites(page)).toHaveAttribute('aria-pressed','true');await expect(page.locator('.station-row')).toHaveCount(1);
  await discover(page).tap();await expect(discover(page)).toHaveAttribute('aria-pressed','true');await discover(page).tap();
  await expect(page.locator('.radio-search-row .search-field')).toContainText(selectedFilters.q);
  await expect(page.locator('.radio-filter-pills .filter-button').first()).toContainText(selectedFilters.country);
  await expect(page.locator('.radio-filter-pills .filter-button').nth(1)).toContainText(selectedFilters.language);
  expect(f.queries).toHaveLength(reads);expect(JSON.stringify(f.state.player)).toBe(player);expect(f.actions).toEqual([]);expect(f.errors).toEqual([]);
  await page.screenshot({path:info.outputPath('radio-explicit-collections.png')});
 });

 test(`Radio library ${theme}: genuinely empty Favorites offers Discover without resetting a search`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,{favorites:[]});
  await filter(page,'.radio-search-row .search-field','cultural',ro);await expect(page.locator('.station-row')).toHaveCount(1);
  await favorites(page).tap();await expect(page.locator('.favorites-empty b')).toHaveText(ro?'Posturile salvate vor apărea aici.':'Your saved stations appear here.');
  expect((await textLegibility(page)).filter(issue=>/^text contrast (?:Favorites|Favorite|Discover|Descoperă)(?:\s|:)/.test(issue))).toEqual([]);
  const action=page.getByRole('button',{name:ro?'Descoperă posturi':'Discover stations',exact:true});await hit48(action);await info.attach('collection-paint',{body:JSON.stringify(await page.locator('.radio-library-tab').evaluateAll(nodes=>nodes.map(node=>{const css=getComputedStyle(node);return{selected:node.getAttribute('aria-pressed'),classes:node.className,background:css.backgroundColor,backgroundImage:css.backgroundImage,color:css.color,opacity:css.opacity,hover:node.matches(':hover'),focus:node===document.activeElement};}))),contentType:'application/json'});await page.screenshot({path:info.outputPath('radio-empty-favorites-settled.png')});await action.tap();
  await expect(discover(page)).toHaveAttribute('aria-pressed','true');await expect(page.locator('.search-field')).toContainText('cultural');await expect(row(page,station.name)).toBeVisible();
  expect(f.state.preferences.favorites).toEqual([]);expect(f.actions).toEqual([]);expect(f.errors).toEqual([]);
  await page.screenshot({path:info.outputPath('radio-empty-favorites-discover.png')});
 });

 test(`Radio library ${theme}: filtered saved stations show no-results and Clear restores the collection`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme),saved=JSON.stringify(f.state.preferences.favorites),player=JSON.stringify(f.state.player);
  await filter(page,'.radio-search-row .search-field','missing',ro);await favorites(page).tap();
  await expect(page.locator('.station-row')).toHaveCount(0);await expect(page.locator('.favorites-empty b')).toHaveText(ro?'Nu am găsit posturi':'No stations found');
  await expect(page.locator('.radio-discover-action')).toHaveCount(0);await expect(favorites(page).locator('small')).toHaveText('1');
  const clear=page.getByRole('button',{name:ro?'Șterge căutarea și filtrele':'Clear search and filters',exact:true});await hit48(clear);await clear.tap();
  await expect(favorites(page)).toHaveAttribute('aria-pressed','true');await expect(row(page,station.name)).toBeVisible();await expect(clear).toHaveCount(0);
  await expect.poll(()=>f.queries.at(-1)).toEqual({q:'',country:'',language:''});
  expect(JSON.stringify(f.state.preferences.favorites)).toBe(saved);expect(JSON.stringify(f.state.player)).toBe(player);expect(f.actions).toEqual([]);expect(f.errors).toEqual([]);
  await page.screenshot({path:info.outputPath('radio-filtered-favorites-recovered.png')});
 });

 test(`Radio library ${theme}: actual decoded HTTPS artwork adapts to panel width with safe fallbacks`,async({page},info)=>{
  const invalid=[{...second,name:'Broken Radio',favicon:brokenLogo},...unsafeLogos.map((favicon,index)=>({...second,uuid:'unsafe-'+index,name:['Insecure Radio','Loopback Radio','Private Radio'][index],favicon}))];
  const f=await fixture(page,info.project.name.endsWith('ro'),theme,{catalog:[station,...invalid]});
  const large=page.locator('.radio-player-heading .radio-artwork-large'),small=row(page,station.name).locator('.radio-artwork');
  await decoded(large.locator('img'));await decoded(small.locator('img'));
  expect(await large.evaluate(node=>{const r=node.getBoundingClientRect();return[r.width,r.height];})).toEqual([64,64]);
  expect(await small.evaluate(node=>{const r=node.getBoundingClientRect();return[r.width,r.height];})).toEqual([56,56]);
  const broken=row(page,'Broken Radio');await broken.scrollIntoViewIfNeeded();await expect(broken.locator('.radio-monogram')).toHaveText('BR');await expect(broken.locator('img')).toHaveCount(0);
  for(const name of ['Insecure Radio','Loopback Radio','Private Radio']){await expect(row(page,name).locator('.radio-monogram')).toBeAttached();await expect(row(page,name).locator('img')).toHaveCount(0);}
  await page.locator('.navigation-toggle').tap();await expect.poll(()=>f.state.preferences.navigationCollapsed).toBe(true);await expect.poll(()=>large.evaluate(node=>{const r=node.getBoundingClientRect();return[r.width,r.height];})).toEqual([96,96]);
  expect(f.assetRequests).toContain(logo);expect(f.assetRequests).toContain(brokenLogo);expect(f.unsafeRequests).toEqual([]);expect(f.actions).toEqual([{path:'/api/preferences',body:{navigationCollapsed:true}}]);expect(f.errors).toEqual([]);
  await page.screenshot({path:info.outputPath('radio-decoded-artwork-fallbacks.png')});
 });

 test(`Radio library ${theme}: paused identity wraps once and transport fits with navigation open`,async({page},info)=>{
  const name='Radio România Cultural — povești și programe pentru toți',metadata='Artist unic — Melodie unică',current={...station,name};
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,{current,catalog:[current,second],favorites:[current,second],playerState:'paused',title:metadata});
  await expect(page.locator('.rail')).not.toHaveClass(/rail-retracted/);
  const player=page.locator('.mini-player'),heading=player.locator('.radio-station-name');
  await expect(heading).toHaveText(name);await expect(player.locator('.radio-track-name')).toHaveText(metadata);await expect(player.locator('.state-text')).toHaveText(ro?'În pauză':'Paused');
  const content=await player.textContent();expect(content!.split(name)).toHaveLength(2);expect(content!.split(metadata)).toHaveLength(2);
  const wrapped=await heading.evaluate(node=>({height:node.getBoundingClientRect().height,line:parseFloat(getComputedStyle(node).lineHeight),client:node.clientWidth,scroll:node.scrollWidth}));
  expect(wrapped.height).toBeGreaterThan(wrapped.line*1.5);expect(wrapped.scroll).toBeLessThanOrEqual(wrapped.client+1);const track=await player.locator('.radio-track-name').evaluate(node=>({client:node.clientWidth,scroll:node.scrollWidth,whiteSpace:getComputedStyle(node).whiteSpace}));expect(track.scroll).toBeLessThanOrEqual(track.client+1);expect(track.whiteSpace).toBe('normal');
  const side=page.locator('.radio-side');expect((await side.boundingBox())!.width).toBeGreaterThanOrEqual(257.999);
  await page.screenshot({path:info.outputPath('radio-paused-wrapped-identity.png')});
  const buttons=player.locator('.player-controls button');expect(await buttons.count()).toBe(4);
  for(const button of await buttons.all()){
   await button.scrollIntoViewIfNeeded();await hit48(button);
   const inside=await button.evaluate(node=>{const b=node.getBoundingClientRect(),p=node.closest('.radio-side')!.getBoundingClientRect();return b.x>=p.x-.001&&b.right<=p.right+.001&&b.y>=p.y-.001&&b.bottom<=p.bottom+.001;});expect(inside).toBe(true);
  }
  expect(f.actions).toEqual([]);expect(f.errors).toEqual([]);
  await page.screenshot({path:info.outputPath('radio-open-navigation-transport.png')});
 });

 test(`Radio library ${theme}: mute state uses crossed speaker and pressed state with one callback per tap`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme),player=JSON.stringify(f.state.player);
  const button=page.locator('.radio-volume button');await expect(button).toHaveAccessibleName(ro?'Fără sunet':'Mute');await expect(button).toHaveAttribute('aria-pressed','false');await hit48(button);
  const ordinary=await button.locator('svg path').first().getAttribute('d'),surface=await button.evaluate(node=>getComputedStyle(node).backgroundColor);
  await button.tap();await expect(button).toHaveAccessibleName(ro?'Activează sunetul':'Unmute');await expect(button).toHaveAttribute('aria-pressed','true');
  await expect(button).toBeEnabled();expect(f.actions).toEqual([{path:'/api/audio',body:{mute:true}}]);
  // Structural icon evidence complements the captured visual state; it is not contrast proof.
  expect(await button.locator('svg path').first().getAttribute('d')).toMatch(/M17 9l5 6m0-6-5 6/);
  await expect.poll(()=>button.evaluate(node=>getComputedStyle(node).backgroundColor)).not.toBe(surface);
  await page.screenshot({path:info.outputPath('radio-muted-crossed-speaker.png')});
  await button.tap();await expect(button).toHaveAttribute('aria-pressed','false');await expect(button).toHaveAccessibleName(ro?'Fără sunet':'Mute');await expect(button).toBeEnabled();
  expect(await button.locator('svg path').first().getAttribute('d')).toBe(ordinary);expect(f.actions).toEqual([{path:'/api/audio',body:{mute:true}},{path:'/api/audio',body:{mute:false}}]);
  expect(JSON.stringify(f.state.player)).toBe(player);expect(f.errors).toEqual([]);
 });
}
