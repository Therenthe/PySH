import {test,expect,type Page,type TestInfo} from '@playwright/test';
import {readFileSync,mkdirSync} from 'node:fs';

// Owned API/service fixtures verify PySH UI behaviour, never subscription/DRM playback.
const evidence='.runtime/tv-services-uat-20261107';mkdirSync(evidence,{recursive:true});
const copy=<T,>(value:T):T=>JSON.parse(JSON.stringify(value));
async function capture(page:Page,info:TestInfo,name:string){await page.screenshot({path:`${evidence}/${info.project.name}-${name}.png`,animations:'disabled'});}
async function fixture(page:Page,ro:boolean,theme:string,old=false){
 const state:any={externalNavigation:old?{id:'old-tv-command',target:'tv'}:null,preferences:{language:ro?'ro':'en',theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,navigationCollapsed:false,navigationAutoHide:false,homeCards:[],shortcuts:[],visualizerStyle:'off'},network:{available:true,state:'connected'},bluetooth:{available:true,powered:true,devices:[],prompts:[]},audio:{available:true,ready:true,volume:30,mute:false,outputs:[]},player:{state:'idle',kind:'radio'},weather:{}};
 const calls:any[]=[],control={hold:false,fail:false},library={channels:[{id:'fixture-channel',name:'Fixture TV',favorite:true}],sources:{playlists:[],xmltv:[]},favorite_requests:[],refreshing:false};let release=()=>{};
 await page.route('**/api/**',async route=>{
  const request=route.request(),path=new URL(request.url()).pathname,body=request.postData()?request.postDataJSON():undefined;let json:any={ok:true};
  if(request.method()!=='GET')calls.push({path,method:request.method(),body});
  if(path==='/api/session')json={token:'owned-tv-services-fixture'};
  else if(path==='/api/state')json=copy(state);
  else if(path==='/api/media')json={path:'',items:[]};
  else if(path==='/api/media/continue')json={items:[]};
  else if(path==='/api/iptv')json=library;
  else if(path==='/api/iptv/recordings')json={items:[],service:{active:true,service_active:true}};
  else if(path.startsWith('/api/iptv/guide/'))json={programmes:[],current:null,upcoming:[],stale:false};
  else if(path==='/api/preferences'){Object.assign(state.preferences,body);json=copy(state.preferences);}
  else if(path==='/api/external'){
   if(control.hold)await new Promise<void>(r=>release=r);
   if(control.fail){control.fail=false;return route.fulfill({status:409,json:{error:'browser_unavailable'}});}
   json={opened:true,service:body.service,preparing:true};
  }
  await route.fulfill({json});
 });
 await page.goto('/');await expect(page.locator('.main-nav button').first()).toHaveClass(/active/);
 return{state,calls,control,release:()=>{control.hold=false;release();}};
}
const channels=(page:Page,ro:boolean)=>page.locator('.iptv-tabs').getByRole('button',{name:ro?'Canale':'Channels',exact:true});
async function services(page:Page,ro:boolean){await page.locator('.main-nav button').nth(2).tap();await page.locator('.media-sections').getByRole('button',{name:ro?'Servicii':'Services',exact:true}).tap();}
async function openTV(page:Page,ro:boolean){await services(page,ro);await page.locator('.service-row').filter({hasText:ro?'Live, ghid și înregistrări':'Live, guide & recordings'}).tap();await expect(channels(page,ro)).toHaveAttribute('aria-pressed','true');}
async function targetGeometry(page:Page,selector:string){
 const boxes=await page.locator(selector).evaluateAll(nodes=>nodes.map(node=>{const r=node.getBoundingClientRect();return{label:node.textContent,width:r.width,height:r.height,x:r.x,y:r.y,right:r.right,bottom:r.bottom};}));
 for(const b of boxes){expect(Math.round(b.width*1000)/1000,b.label||'width').toBeGreaterThanOrEqual(48);expect(Math.round(b.height*1000)/1000,b.label||'height').toBeGreaterThanOrEqual(48);expect(b.x).toBeGreaterThanOrEqual(0);expect(b.y).toBeGreaterThanOrEqual(0);expect(b.right).toBeLessThanOrEqual(800.5);expect(b.bottom).toBeLessThanOrEqual(480.5);}
}
async function serviceRowsVisible(page:Page){
 const rows=await page.locator('.service-row').evaluateAll(nodes=>nodes.map(node=>{const r=node.getBoundingClientRect(),panel=node.closest('.service-panel')!.getBoundingClientRect();return{label:node.textContent,inside:r.top>=panel.top-.5&&r.bottom<=panel.bottom+.5,hit:node.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))};}));
 expect(rows).toHaveLength(5);for(const row of rows){expect(row.inside,row.label||'inside service panel').toBe(true);expect(row.hit,row.label||'hit target').toBe(true);}
}

for(const theme of ['ink','night']){
 test(`TV services ${theme}: direct Channels return applies once, resets tabs and never replays stale command`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme,true);
  await page.waitForTimeout(2700);await expect(page.locator('.main-nav button').first()).toHaveClass(/active/);
  f.state.externalNavigation={id:'first-return-tv',target:'tv'};
  await expect(channels(page,ro)).toHaveAttribute('aria-pressed','true',{timeout:7000});await capture(page,info,theme+'-01-home-to-channels');
  for(const [index,label]of [ro?'Înregistrări':'Recordings',ro?'Surse':'Sources'].entries()){
   const tab=page.locator('.iptv-tabs').getByRole('button',{name:label,exact:true});await tab.tap();await expect(tab).toHaveAttribute('aria-pressed','true');
   await page.waitForTimeout(2700);await expect(tab).toHaveAttribute('aria-pressed','true');
   f.state.externalNavigation={id:'refresh-return-tv-'+index,target:'tv'};await expect(channels(page,ro)).toHaveAttribute('aria-pressed','true',{timeout:7000});await capture(page,info,theme+'-02-tab-reset-'+index);
  }
  await page.locator('.main-nav button').first().tap();await expect(page.locator('.main-nav button').first()).toHaveClass(/active/);await page.waitForTimeout(2700);await expect(page.locator('.main-nav button').first()).toHaveClass(/active/);
  await page.locator('.main-nav button').nth(2).tap();await expect(page.locator('.media-sections')).toBeVisible();await expect(page.locator('.iptv-page')).toHaveCount(0);await capture(page,info,theme+'-03-media-no-replay');
  f.state.externalNavigation={id:'fresh-return-after-unmount',target:'tv'};await expect(channels(page,ro)).toHaveAttribute('aria-pressed','true',{timeout:7000});
  expect(f.calls.filter(c=>['/api/player','/api/play','/api/iptv/view','/api/external'].includes(c.path))).toEqual([]);
 });

 test(`TV services ${theme}: Orange official launch, pending single ownership and localized recovery`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme);await services(page,ro);
  const orange=page.locator('.service-row').filter({hasText:'Orange TV Go'});await expect(orange).toBeVisible();await expect(orange).toBeEnabled();await serviceRowsVisible(page);await targetGeometry(page,'.service-row');await capture(page,info,theme+'-04-orange-available');
  f.control.hold=true;f.control.fail=true;await orange.tap();await expect(page.locator('.service-panel')).toHaveAttribute('aria-busy','true');await expect(orange).toBeDisabled();
  await orange.evaluate((button:HTMLButtonElement)=>{button.click();button.click();});for(const row of await page.locator('.service-row').all())await expect(row).toBeDisabled();
  await expect.poll(()=>f.calls.filter(c=>c.path==='/api/external').length).toBe(1);expect(f.calls.find(c=>c.path==='/api/external')!.body).toEqual({service:'orangetv'});await capture(page,info,theme+'-05-orange-pending');f.release();
  await expect(orange).toBeEnabled();await expect(page.locator('.error-strip')).toBeVisible();await capture(page,info,theme+'-06-orange-unavailable');
  await page.locator('.error-strip').getByRole('button',{name:ro?'Închide':'Close',exact:true}).tap();await orange.tap();await expect.poll(()=>f.calls.filter(c=>c.path==='/api/external').length).toBe(2);await expect(page.locator('.service-panel')).toHaveAttribute('aria-busy','false');await expect(orange).toBeEnabled();
  await expect(page.locator('.error-strip')).toHaveCount(0);await capture(page,info,theme+'-07-orange-retry-accepted');
 });

 test(`TV services ${theme}: Digi emblem loads locally and official handoff preserves TV catalogue`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await fixture(page,ro,theme);await openTV(page,ro);
  const digi=page.getByRole('button',{name:ro?'Digi Sport 1 · Player oficial':'Digi Sport 1 · Official player',exact:true});await expect(digi).toBeVisible();
  const logo=digi.locator('img');await expect(logo).toBeVisible();await expect.poll(()=>logo.evaluate((img:HTMLImageElement)=>img.complete&&img.naturalWidth>0)).toBe(true);expect(new URL(await logo.getAttribute('src')||'',page.url()).origin).toBe(new URL(page.url()).origin);
  await targetGeometry(page,'.iptv-official-channel');await capture(page,info,theme+'-08-digi-real-emblem');await digi.tap();await expect.poll(()=>f.calls.filter(c=>c.path==='/api/external').length).toBe(1);expect(f.calls.find(c=>c.path==='/api/external')!.body).toEqual({service:'digisport'});await expect(channels(page,ro)).toHaveAttribute('aria-pressed','true');
 });
}

async function drawerFixture(page:Page,ro:boolean,theme:string,service:'digi'|'orange'){
 const address=service==='digi'?'https://www.digisport.ro/live/digisport-1':'https://tvgo.orange.ro/';
 await page.route('**/*',route=>route.fulfill({contentType:'text/html',body:'<!doctype html><html><head><style>body{margin:0;background:#16222b;color:white;font:16px system-ui}header{display:flex;justify-content:space-between;padding:18px}button,input{min-width:48px;min-height:48px}main{margin:50px}input{width:300px}</style></head><body><header><b>Owned service fixture</b><button id="account">Account</button></header><main><label>Account name <input aria-label="Fixture account name"></label></main></body></html>'}));
 await page.goto(address);
 await page.evaluate(({language,theme})=>{
  const state={language,theme,actions:[]as string[],returnCallbacks:[]as Function[],accountClicks:0};(window as any).tvDrawerFixture=state;
  (window as any).chrome={runtime:{sendMessage(message:{action:string},callback?:Function){state.actions.push(message.action);if(message.action.startsWith('return-'))state.returnCallbacks.push(callback!);else if(message.action==='controls-status')callback?.({ok:true,controls:{language,theme,busy:false,audio:{available:true,ready:true,volume:30,mute:false,outputs:[]},brightness:{available:true,value:10}}});else callback?.({ok:true,language,theme});}}};
  document.querySelector('#account')!.addEventListener('click',()=>state.accountClicks++);const original=Element.prototype.attachShadow;Element.prototype.attachShadow=function(options){const shadow=original.call(this,options);if(this.tagName==='PI-HUB-RETURN')(window as any).tvDrawerShadow=shadow;return shadow;};
 },{language:ro?'ro':'en',theme});
 for(const file of ['command-controls.js','return.js'])await page.addScriptTag({content:readFileSync(new URL('../../app/browser-extension/'+file,import.meta.url),'utf8')});
}
async function drawerButton(page:Page,text:string){
 const point=await page.evaluate(text=>{const button=[...(window as any).tvDrawerShadow.querySelectorAll('button')].find((node:any)=>node.textContent.trim()===text)as HTMLButtonElement;if(!button)throw new Error('No drawer button: '+text);const r=button.getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2};},text);await page.touchscreen.tap(point.x,point.y);
}
async function drawerVisible(page:Page){return page.evaluate(()=>getComputedStyle((window as any).tvDrawerShadow.querySelector('.drawer')).display!=='none');}
for(const theme of ['ink','night'])for(const service of ['digi','orange'] as const)test(`TV official drawer ${service} ${theme}: controls preserve account access, explicit return and keyboard`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro');await drawerFixture(page,ro,theme,service);await page.locator('#account').tap();expect(await page.evaluate(()=>(window as any).tvDrawerFixture.accountClicks)).toBe(1);await page.getByRole('textbox',{name:'Fixture account name'}).tap();await page.keyboard.type('owned-fixture');await expect(page.getByRole('textbox')).toHaveValue('owned-fixture');await page.getByRole('textbox').evaluate((el:HTMLInputElement)=>el.blur());
 await page.keyboard.press('Alt+Shift+P');await expect.poll(()=>drawerVisible(page)).toBe(true);
 const geometry=await page.evaluate(()=>{const shadow=(window as any).tvDrawerShadow;return{subtitle:shadow.querySelector('.subtitle').textContent,bottom:shadow.querySelector('.drawer').getBoundingClientRect().bottom,buttons:[...shadow.querySelectorAll('button')].filter((node:any)=>node.getClientRects().length).map((node:any)=>{const r=node.getBoundingClientRect();return{label:node.textContent,x:r.x,right:r.right,bottom:r.bottom,width:r.width,height:r.height};})};});
 expect(geometry.subtitle).toContain(service==='digi'?'Digi Sport 1':'Orange TV Go');expect(geometry.bottom).toBeLessThanOrEqual(480);for(const b of geometry.buttons){expect(Math.round(b.width*1000)/1000,b.label).toBeGreaterThanOrEqual(48);expect(Math.round(b.height*1000)/1000,b.label).toBeGreaterThanOrEqual(48);expect(b.x).toBeGreaterThanOrEqual(0);expect(b.right).toBeLessThanOrEqual(800);expect(b.bottom).toBeLessThanOrEqual(480);}
 await capture(page,info,theme+'-09-'+service+'-drawer');
 if(service==='digi'){
  await drawerButton(page,ro?'Canale':'Channels');const pending=await page.evaluate(()=>(window as any).tvDrawerFixture.actions.filter((action:string)=>action.startsWith('return-')));expect(pending).toEqual(['return-tv']);await capture(page,info,theme+'-10-digi-return-pending');
  await page.evaluate(()=>(window as any).tvDrawerFixture.returnCallbacks.at(-1)({ok:false}));await expect.poll(()=>page.evaluate(()=>(window as any).tvDrawerShadow.querySelector('.status').textContent)).toContain(ro?'Revenirea':'Could not return');await capture(page,info,theme+'-11-digi-return-failed');
  await drawerButton(page,ro?'Reîncearcă revenirea':'Retry return');expect(await page.evaluate(()=>(window as any).tvDrawerFixture.actions.filter((action:string)=>action.startsWith('return-')))).toEqual(['return-tv','return-tv']);await page.evaluate(()=>(window as any).tvDrawerFixture.returnCallbacks.at(-1)({ok:true}));
 }else{
  // Focusing the owned input above already requested the native keyboard.
  await drawerButton(page,ro?'Închide tastatura':'Hide keyboard');expect(await page.evaluate(()=>(window as any).tvDrawerFixture.actions.at(-1))).toBe('hide');
  await drawerButton(page,ro?'Tastatură':'Keyboard');expect(await page.evaluate(()=>(window as any).tvDrawerFixture.actions.at(-1))).toBe('show');await expect.poll(()=>drawerVisible(page)).toBe(false);
  await page.keyboard.press('Alt+Shift+P');await expect.poll(()=>drawerVisible(page)).toBe(true);await drawerButton(page,ro?'Închide tastatura':'Hide keyboard');expect(await page.evaluate(()=>(window as any).tvDrawerFixture.actions.at(-1))).toBe('hide');
  await expect.poll(()=>drawerVisible(page)).toBe(true);await drawerButton(page,'Media');expect(await page.evaluate(()=>(window as any).tvDrawerFixture.actions.at(-1))).toBe('return-media');await page.evaluate(()=>(window as any).tvDrawerFixture.returnCallbacks.at(-1)({ok:true}));
 }
 await page.keyboard.press('Escape');await expect.poll(()=>drawerVisible(page)).toBe(false);await page.locator('#account').tap();expect(await page.evaluate(()=>(window as any).tvDrawerFixture.accountClicks)).toBe(2);await capture(page,info,theme+'-12-'+service+'-restored');
});

for(const theme of ['ink','night'])test(`Orange preparation ${theme}: EME and key creation gate the exact official URL`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro'),model={state:'checking',error:undefined as string|undefined,url:'https://tvgo.orange.ro.evil.example/',reports:[]as boolean[]};
 const directory=new URL('../../services/backend/preparation/',import.meta.url);
 for(const [path,file,type]of [['/service-prepare','index.html','text/html'],['/service-prepare.js','prepare.js','text/javascript'],['/service-prepare.css','prepare.css','text/css']])await page.route(url=>url.pathname===path,route=>route.fulfill({contentType:type,body:readFileSync(new URL(file,directory),'utf8')}));
 await page.addInitScript(()=>{(window as any).orangeProbe={ready:false,keys:true,calls:0};Object.defineProperty(navigator,'requestMediaKeySystemAccess',{value:async()=>{const probe=(window as any).orangeProbe;probe.calls++;if(!probe.ready)throw new DOMException('Owned unavailable fixture','NotSupportedError');return{createMediaKeys:async()=>{if(!probe.keys)throw new DOMException('Owned key failure fixture','NotSupportedError');return{};}};}});});
 await page.route('**/api/**',async route=>{
  const request=route.request(),path=new URL(request.url()).pathname;let json:any={token:'owned-orange-prepare'};
  if(path!=='/api/session'){
   if(request.method()==='POST'){expect(request.headers()['x-hub-token']).toBe('owned-orange-prepare');const body=request.postDataJSON();if(path==='/api/external/report'){expect(body.job).toBe('orange-job');expect(body.attempt).toBe('orange-attempt');model.reports.push(body.ready);model.state=body.ready?'ready':'waiting_component';}else if(path==='/api/external/retry'){model.state='checking';model.error=undefined;}}
   json={state:model.state,error:model.error,service:'orangetv',attempt:'orange-attempt',language:ro?'ro':'en',theme,...(model.state==='ready'?{url:model.url}:{})};
  }
  await route.fulfill({json});
 });
 await page.route('https://tvgo.orange.ro/',route=>route.fulfill({contentType:'text/html',body:'<h1>Owned Orange official boundary fixture</h1>'}));
 await page.goto(`/service-prepare?job=orange-job&attempt=orange-attempt&lang=${ro?'ro':'en'}&theme=${theme}`);await expect(page.locator('#service')).toHaveText('Orange TV Go');await expect.poll(()=>model.reports).toEqual([false]);await capture(page,info,theme+'-13-orange-eme-unavailable');
 model.state='error';model.error='protected_playback_timeout';await expect(page.locator('#retry')).toBeVisible();await page.evaluate(()=>{(window as any).orangeProbe.ready=true;(window as any).orangeProbe.keys=false;});await page.locator('#retry').tap();await expect.poll(()=>model.reports).toEqual([false,false]);expect(page.url()).toContain('/service-prepare?');await capture(page,info,theme+'-14-orange-key-creation-failed');
 model.state='error';model.error='protected_playback_timeout';await expect(page.locator('#retry')).toBeVisible();await page.evaluate(()=>(window as any).orangeProbe.keys=true);await page.locator('#retry').tap();await expect.poll(()=>model.reports).toEqual([false,false,true]);await expect(page.locator('#notice')).toHaveText(ro?'Această sesiune de pregătire s-a încheiat.':'This preparation session has ended.');expect(page.url()).toContain('/service-prepare?');await capture(page,info,theme+'-15-orange-invalid-target-rejected');
 model.url='https://tvgo.orange.ro/';await expect(page).toHaveURL('https://tvgo.orange.ro/');await expect(page.getByRole('heading')).toHaveText('Owned Orange official boundary fixture');await capture(page,info,theme+'-16-orange-official-boundary');expect(model.reports).toEqual([false,false,true]);
});
