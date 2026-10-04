import {expect,test,type Locator,type Page} from '@playwright/test';

// Synthetic long-output recovery fixture; not hardware pairing or audio evidence.
async function setupRecovery(page:Page,ro:boolean,theme:string){
 const name='OUTPUT_'+('W'.repeat(400)),state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0},network:{available:true,state:'connected',connection:'Ethernet'},bluetooth:{available:true,devices:[],prompts:[]},player:{state:'idle'},weather:{},audio:{available:true,ready:true,volume:30,mute:false,outputs:[{id:11,description:'Existing',active:true},{id:22,description:name,active:false}]}};
 let release!:()=>void;const gate=new Promise<void>(r=>release=r),writes:any[]=[],preferenceWrites:any[]=[];
 await page.route('**/api/**',async route=>{const path=new URL(route.request().url()).pathname;if(path==='/api/audio'){writes.push(route.request().postDataJSON());await gate;await route.fulfill({status:503,json:{error:'audio_unavailable'}});return;}if(path==='/api/preferences'){const body=route.request().postDataJSON();preferenceWrites.push(body);Object.assign(state.preferences,body);await route.fulfill({json:state.preferences});return;}await route.fulfill({json:path==='/api/session'?{token:'fixture'}:path==='/api/state'?state:{ok:true}});});
 await page.goto('/');await page.locator('.rail-bottom button').last().tap();const dialog=page.getByRole('dialog',{name:'Audio',exact:true});await dialog.locator('.modal-list button').last().tap();await expect(dialog.getByRole('status')).toBeVisible();await dialog.locator('header').getByRole('button',{name:ro?'Închide':'Close',exact:true}).tap();await page.locator('.main-nav button').nth(3).tap();const rerun=ro?'Reia configurarea':'Run setup again';await page.getByRole('button',{name:rerun,exact:true}).tap();await page.locator('.dialog-actions').getByRole('button',{name:rerun,exact:true}).tap();release();await expect(page.locator('.setup-audio-recovery').getByRole('alert')).toBeVisible();return{state,writes,preferenceWrites};
}
async function hit(control:Locator){
 const b=(await control.boundingBox())!;expect(b.width).toBeGreaterThanOrEqual(48);expect(b.height).toBeGreaterThanOrEqual(48);expect(b.x).toBeGreaterThanOrEqual(0);expect(b.y).toBeGreaterThanOrEqual(0);expect(b.x+b.width).toBeLessThanOrEqual(800);expect(b.y+b.height).toBeLessThanOrEqual(480);
 // Check top and bottom of the target too: center alone wrongly accepts half-clipped buttons.
 expect(await control.evaluate(el=>{const b=el.getBoundingClientRect();return [.1,.5,.9].every(f=>el.contains(document.elementFromPoint(b.x+b.width/2,b.y+b.height*f)));})).toBe(true);
}
async function pan(page:Page,card:Locator){
 const b=(await card.boundingBox())!,x=b.x+b.width/2,y=b.y+b.height-70,cdp=await page.context().newCDPSession(page);let ended=false;
 try{await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]});for(let i=1;i<=8;i++){await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x,y:y-i*10}]});await page.evaluate(()=>new Promise<void>(r=>requestAnimationFrame(()=>r())));}await expect.poll(()=>card.evaluate(el=>el.scrollTop)).toBeGreaterThan(0);
  expect(await card.evaluate(async el=>{let prior=el.scrollTop,stable=0;for(let i=0;i<120;i++){await new Promise<void>(r=>requestAnimationFrame(()=>r()));const current=el.scrollTop;stable=Math.abs(prior-current)<.1?stable+1:0;prior=current;if(stable>=8)return true;}return false;})).toBe(true);await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});ended=true;
 }finally{if(!ended)await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]}).catch(()=>{});await cdp.detach();}
}
for(const theme of ['ink','night']){
 test(`Setup recovery ${theme}: outer-card touch scroll exposes full Continue and Back without losing notice`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),f=await setupRecovery(page,ro,theme),card=page.locator('.setup-card'),next=card.locator('.setup-actions').getByRole('button',{name:ro?'Continuă':'Continue',exact:false});
  await pan(page,card);await hit(next);await page.screenshot({path:info.outputPath('setup-continue-scrolled.png')});await next.tap();await expect(card).toContainText(ro?'Conectivitate':'Connectivity');await expect(card.locator('[data-recovery=audio][role=alert]')).toBeVisible();
  const back=card.locator('.setup-actions').getByRole('button',{name:ro?'Înapoi':'Back',exact:true});await back.scrollIntoViewIfNeeded();await hit(back);await back.tap();await expect(card).toContainText(ro?'Alege limba':'Choose your language');await expect(card.locator('[data-recovery=audio][role=alert]')).toBeVisible();expect(f.state.preferences.language).toBe(ro?'ro':'en');expect(f.preferenceWrites).toEqual([]);expect(f.writes).toEqual([{output:22}]);
 });
 test(`Setup recovery ${theme}: primary footer is entirely visible before scrolling and on revisit`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro');await setupRecovery(page,ro,theme);const card=page.locator('.setup-card'),next=card.locator('.setup-actions').getByRole('button',{name:ro?'Continuă':'Continue',exact:false});await hit(next);await next.tap();const back=card.locator('.setup-actions').getByRole('button',{name:ro?'Înapoi':'Back',exact:true});await hit(back);await back.tap();await hit(next);await page.screenshot({path:info.outputPath('setup-sticky-primary.png')});
 });
}
