import { expect, test, type Page, type TestInfo } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { mkdirSync } from 'node:fs';

// Owned service fixtures: no remote service, account, native keyboard or DRM.
const deviceControls = readFileSync(new URL('../../app/browser-extension/command-controls.js', import.meta.url), 'utf8');
const extension = readFileSync(new URL('../../app/browser-extension/return.js', import.meta.url), 'utf8');
const evidence = '.runtime/ui-global-20261023/drawer';
mkdirSync(evidence, { recursive: true });
async function fixture(page: Page, info: TestInfo, scheme: 'dark'|'light', service='YouTube') {
  await page.emulateMedia({colorScheme:scheme});
  const address=service==='Netflix'?'https://www.netflix.com/fixture':'https://www.youtube.com/fixture';
  await page.route('**/*',route=>route.fulfill({contentType:'text/html',body:`<!doctype html><html><head><style>
  body{margin:0;background:${scheme==='dark'?'#14171a':'#fafafa'};font:16px system-ui;color:${scheme==='dark'?'white':'#182027'}}header{display:flex;align-items:center;gap:20px;height:64px;padding:0 24px}input{margin:auto;width:300px;height:32px;border-radius:20px;border:1px solid #717b80;background:transparent;color:inherit;padding:0 16px}#profile{height:48px;width:48px;border-radius:50%;background:#497e71;color:white;border:0}main{margin:28px;border-radius:12px;background:${scheme==='dark'?'#272c31':'#e1e7e8'};height:270px;padding:20px}h1{font-size:22px}p{opacity:.7}</style></head><body><header><strong>${service} fixture</strong><input placeholder="Search" aria-label="Service search"><button id=profile>TH</button></header><main><h1>Owned video surface</h1><p>No account or remote service is loaded.</p></main></body></html>`}));
  await page.goto(address);
  await page.evaluate(theme=>document.documentElement.dataset.fixtureTheme=theme,scheme==='light'?'ink':'night');
  await page.evaluate(language=>{
    const state={language,theme:document.documentElement.dataset.fixtureTheme,actions:[] as string[],profileClicks:0,returnCallbacks:[] as Function[],keyboardError:false};
    (window as any).drawerFixture=state;
    (window as any).chrome={runtime:{sendMessage(message:{action:string},callback?:Function){state.actions.push(message.action);if(message.action.startsWith('return-'))state.returnCallbacks.push(callback!);else if(message.action==='controls-status')callback?.({ok:true,controls:{language,theme:state.theme,busy:false,audio:{available:true,ready:true,volume:40,mute:false,outputs:[{id:'fixture',label:'Fixture speaker',active:true}]},brightness:{available:true,value:80}}});else callback?.({ok:!state.keyboardError,language,theme:state.theme});}}};
    document.querySelector('#profile')!.addEventListener('click',()=>state.profileClicks++);
    const original=Element.prototype.attachShadow;Element.prototype.attachShadow=function(options){const shadow=original.call(this,options);if(this.tagName==='PI-HUB-RETURN')(window as any).drawerShadow=shadow;return shadow;};
  },info.project.name==='touch-ro'?'ro':'en');
  await page.addScriptTag({content:deviceControls});
  await page.addScriptTag({content:extension});
}
async function visible(page:Page){return page.evaluate(()=>getComputedStyle((window as any).drawerShadow.querySelector('.drawer')).display!=='none');}
async function press(page:Page,selector:string){const rect=await page.evaluate(selector=>{const r=(window as any).drawerShadow.querySelector(selector).getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2};},selector);await page.touchscreen.tap(rect.x,rect.y);}
async function capture(page:Page,info:TestInfo,name:string){await page.screenshot({animations:'disabled',path:`${evidence}/${name}-${info.project.name}.png`});}
async function reveal(page:Page){await press(page,'.handle');await expect.poll(()=>visible(page)).toBe(true);}

for(const scheme of ['dark','light'] as const){
 test(`drawer ${scheme}: hierarchy, service context, targets and unobstructed account/search`,async({page},info)=>{
  const errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));await fixture(page,info,scheme);
  await expect.poll(()=>visible(page)).toBe(false);await page.locator('#profile').tap();expect(await page.evaluate(()=>(window as any).drawerFixture.profileClicks)).toBe(1);
  await page.locator('input').tap();await page.keyboard.type('Fixture search');await expect(page.locator('input')).toHaveValue('Fixture search');await page.locator('input').evaluate((input:HTMLInputElement)=>input.blur());
  await capture(page,info,`closed-${scheme}`);await reveal(page);
  const geometry=await page.evaluate(()=>{const shadow=(window as any).drawerShadow;return{subtitle:shadow.querySelector('.subtitle').textContent,buttons:[...shadow.querySelectorAll('.action,.close')].map((e:any)=>{const r=e.getBoundingClientRect();return{width:r.width,height:r.height,left:r.left,right:r.right,bottom:r.bottom};}),panel:shadow.querySelector('.drawer').getBoundingClientRect().toJSON(),overflow:document.documentElement.scrollWidth>innerWidth};});
  expect(geometry.subtitle).toContain('YouTube');expect(geometry.overflow).toBe(false);expect(geometry.panel.bottom).toBeLessThan(480);
  // Translated DOMRects may report 47.999996px for an exact 48px CSS target.
  // Quantize only that floating-point noise; the product threshold remains 48px.
  for(const button of geometry.buttons){expect(Math.round(button.width*1000)/1000).toBeGreaterThanOrEqual(48);expect(Math.round(button.height*1000)/1000).toBeGreaterThanOrEqual(48);expect(button.left).toBeGreaterThanOrEqual(0);expect(button.right).toBeLessThanOrEqual(800);expect(button.bottom).toBeLessThanOrEqual(480);}
  expect(geometry.buttons[1].width).toBeGreaterThan(geometry.buttons[2].width);await capture(page,info,`open-${scheme}`);
  await press(page,'.close');expect(await visible(page)).toBe(false);await page.locator('#profile').tap();expect(await page.evaluate(()=>(window as any).drawerFixture.profileClicks)).toBe(2);expect(errors).toEqual([]);
 });
 test(`drawer ${scheme}: pending, localized failure and retry keep trusted destination`,async({page},info)=>{
  await fixture(page,info,scheme,'Netflix');await page.clock.install();await reveal(page);await press(page,'.actions button:nth-child(2)');
  expect(await page.evaluate(()=>(window as any).drawerFixture.actions.at(-1))).toBe('return-radio');
  expect(await page.evaluate(()=>(window as any).drawerShadow.querySelector('.action').getAttribute('aria-busy'))).toBe('true');await capture(page,info,`pending-${scheme}`);
  await page.clock.runFor(11000);expect(await visible(page)).toBe(true);
  const text=await page.evaluate(()=>(window as any).drawerShadow.querySelector('.status').textContent);expect(text).toContain(info.project.name==='touch-ro'?'Revenirea':'Could not return');await capture(page,info,`error-${scheme}`);
  await page.clock.runFor(9000);expect(await visible(page)).toBe(true);await press(page,'.action:first-child');
  expect(await page.evaluate(()=>(window as any).drawerFixture.actions.at(-1))).toBe('return-radio');
  await page.evaluate(()=>(window as any).drawerFixture.returnCallbacks.at(-1)({ok:true}));
  expect(await page.evaluate(()=>getComputedStyle((window as any).drawerShadow.querySelector('.status')).display)).toBe('none');
 });
 test(`drawer ${scheme}: keyboard toggles and unavailable state are explicit`,async({page},info)=>{
  await fixture(page,info,scheme);await reveal(page);await page.evaluate(()=>(window as any).drawerFixture.keyboardError=true);await press(page,'.keyboard');
  expect(await page.evaluate(()=>getComputedStyle((window as any).drawerShadow.querySelector('.status')).display)).toBe('block');await capture(page,info,`keyboard-error-${scheme}`);
  await page.evaluate(()=>(window as any).drawerFixture.keyboardError=false);await press(page,'.keyboard');
  expect(await page.evaluate(()=>(window as any).drawerShadow.querySelector('.keyboard').getAttribute('aria-pressed'))).toBe('true');await capture(page,info,`keyboard-on-${scheme}`);
  await reveal(page);await press(page,'.keyboard');expect(await page.evaluate(()=>(window as any).drawerFixture.actions.at(-1))).toBe('hide');expect(await page.evaluate(()=>(window as any).drawerShadow.querySelector('.keyboard').getAttribute('aria-pressed'))).toBe('false');
 });
 test(`drawer ${scheme}: keyboard focus remains inside open sheet, reduced motion and Escape`,async({page},info)=>{
  await fixture(page,info,scheme);await page.clock.install();await page.emulateMedia({reducedMotion:'reduce'});await page.keyboard.press('Alt+Shift+P');
  expect(await page.evaluate(()=>(window as any).drawerShadow.activeElement.className)).toBe('close');await page.clock.runFor(9000);expect(await visible(page)).toBe(true);
  await page.keyboard.press('Shift+Tab');expect(await page.evaluate(()=>(window as any).drawerShadow.activeElement.className)).toBe('action keyboard');
  await page.keyboard.press('Tab');expect(await page.evaluate(()=>(window as any).drawerShadow.activeElement.className)).toBe('close');
  expect(await page.evaluate(()=>getComputedStyle((window as any).drawerShadow.querySelector('.drawer')).animationName)).toBe('none');await capture(page,info,`focus-reduced-${scheme}`);
  await page.keyboard.press('Escape');expect(await visible(page)).toBe(false);expect(await page.evaluate(()=>(window as any).drawerShadow.activeElement.className)).toBe('handle');
 });
 test(`drawer ${scheme}: touch auto-retract remains distinct from deliberate keyboard use`,async({page},info)=>{
  await fixture(page,info,scheme);await page.clock.install();await reveal(page);await page.clock.runFor(8100);expect(await visible(page)).toBe(false);
  await page.keyboard.press('Alt+Shift+P');await page.clock.runFor(8100);expect(await visible(page)).toBe(true);await page.keyboard.press('Escape');expect(await visible(page)).toBe(false);
 });
 test(`drawer ${scheme}: native PySH theme wins over the service and OS palette`,async({page},info)=>{
  await fixture(page,info,scheme);await page.emulateMedia({colorScheme:scheme==='dark'?'light':'dark'});await reveal(page);
  const state=await page.evaluate(()=>({theme:document.querySelector('pi-hub-return')!.getAttribute('data-theme'),background:getComputedStyle((window as any).drawerShadow.querySelector('.drawer')).backgroundColor}));
  expect(state.theme).toBe(scheme==='dark'?'night':'ink');expect(state.background).toBe(scheme==='dark'?'rgb(17, 29, 38)':'rgb(243, 246, 242)');await capture(page,info,`native-theme-${scheme}`);
 });
 test(`drawer ${scheme}: every destination and duplicate pending action retain ownership`,async({page},info)=>{
  for(const [selector,destination] of [['.action:first-child','home'],['.actions button:nth-child(2)','radio'],['.actions button:nth-child(3)','media']]){
   await fixture(page,info,scheme);await reveal(page);await press(page,selector);await press(page,selector);
   const returns=await page.evaluate(()=>(window as any).drawerFixture.actions.filter((action:string)=>action.startsWith('return-')));expect(returns).toEqual(['return-'+destination]);
   await page.evaluate(()=>(window as any).drawerFixture.returnCallbacks.at(-1)({ok:true}));
   expect(await page.evaluate(()=>(window as any).drawerShadow.querySelector('.action').getAttribute('aria-busy'))).toBe('false');
  }
 });

 test(`drawer ${scheme}: reopening refreshes the hub theme without perpetual polling`,async({page},info)=>{
  await fixture(page,info,scheme);await reveal(page);await press(page,'.close');
  await page.evaluate(theme=>(window as any).drawerFixture.theme=theme,scheme==='dark'?'ink':'night');
  await reveal(page);expect(await page.evaluate(()=>document.querySelector('pi-hub-return')!.getAttribute('data-theme'))).toBe(scheme==='dark'?'ink':'night');
  const statuses=await page.evaluate(()=>(window as any).drawerFixture.actions.filter((action:string)=>action==='status').length);expect(statuses).toBe(3);
 });

}
