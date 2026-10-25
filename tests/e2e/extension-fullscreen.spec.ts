import { expect, test, type Page, type TestInfo } from '@playwright/test';
import { readFileSync } from 'node:fs';

// Owned DOM fixtures with fake native replies: these prove browser lifecycle and
// hit testing, not Wayland keyboard visibility or external-service acceptance.
const extension = readFileSync(new URL('../../app/browser-extension/return.js', import.meta.url), 'utf8');
async function fixture(page: Page, info: TestInfo, target: 'film' | 'wrapper') {
  await page.setContent(`<button id="enter">Enter fullscreen</button>
    <div id="wrapper" style="background:black;width:800px;height:480px">
    <video id="film" style="background:black;width:800px;height:480px"></video></div>`);
  await page.evaluate(({ target, language }) => {
    const state = { actions: [] as string[], playerClicks: 0 };
    (window as any).fixtureState = state;
    (window as any).chrome = { runtime: { sendMessage(message: { action: string }, callback?: Function) {
      state.actions.push(message.action); callback?.({ ok: true, language });
    } } };
    document.querySelector('#enter')!.addEventListener('click', () => document.querySelector(`#${target}`)!.requestFullscreen());
    document.querySelector('#film')!.addEventListener('pointerup', () => { state.playerClicks++; });
  }, { target, language: info.project.name === 'touch-ro' ? 'ro' : 'en' });
  await page.evaluate(()=>{const original=Element.prototype.attachShadow;Element.prototype.attachShadow=function(options){const shadow=original.call(this,options);if(this.tagName==='PI-HUB-RETURN')(window as any).fixtureShadow=shadow;return shadow;};});
  await page.addScriptTag({ content: extension });
  await page.click('#enter');
  await expect.poll(() => page.evaluate(() => document.fullscreenElement?.id)).toBe(target);
  await page.evaluate(() => new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))));
}

async function control(page: Page, selector: string) {
  const point=await page.evaluate(selector=>{
    const element=(window as any).fixtureShadow.querySelector(selector);const rect=element.getBoundingClientRect();
    return{x:rect.x+rect.width/2,y:rect.y+rect.height/2};
  },selector);await page.touchscreen.tap(point.x,point.y);
}
async function drawerVisible(page: Page) {return page.evaluate(()=>getComputedStyle((window as any).fixtureShadow.querySelector('.drawer')).display!=='none');}

test('native video fullscreen central gesture reveals drawer and trusted destination',async({page},info)=>{
 await fixture(page,info,'film');await page.touchscreen.tap(400,240);
 expect(await page.evaluate(()=>(window as any).fixtureState.playerClicks)).toBe(1);
 await page.touchscreen.tap(780,20);expect(await page.evaluate(()=>document.fullscreenElement?.id)).toBe('film');
 const input=await page.context().newCDPSession(page);
 await input.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:400,y:8}]});
 await input.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:400,y:84}]});
 await input.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await input.detach();
 await expect.poll(()=>page.evaluate(()=>document.fullscreenElement===null)).toBe(true);
 await expect.poll(()=>drawerVisible(page)).toBe(true);
 await expect.poll(()=>page.evaluate(()=>getComputedStyle((window as any).fixtureShadow.querySelector('.drawer')).opacity)).toBe('1');
 await control(page,'.actions button:nth-child(2)');
 await expect.poll(()=>page.evaluate(()=>(window as any).fixtureState.actions.filter((action:string)=>action.startsWith('return')).at(-1))).toBe('return-radio');
});

test('drawer leaves service profile usable, opens by downward gesture, closes without clickthrough',async({page},info)=>{
 await fixture(page,info,'wrapper');
 await page.evaluate(()=>{const profile=document.createElement('button');profile.id='profile';profile.textContent='Account';profile.style.cssText='position:fixed;right:8px;top:8px;width:48px;height:48px';profile.onclick=()=>{(window as any).fixtureState.profileClicks=((window as any).fixtureState.profileClicks||0)+1;};document.querySelector('#wrapper')!.append(profile);});
 await page.evaluate(()=>{const input=document.createElement('input');input.id='service-search';input.placeholder='Search';input.style.cssText='position:fixed;left:50%;top:12px;transform:translateX(-50%);width:300px;height:40px';document.querySelector('#wrapper')!.append(input);});
 await expect.poll(()=>drawerVisible(page)).toBe(false);
 await page.touchscreen.tap(400,32);await expect(page.locator('#service-search')).toBeFocused();await page.keyboard.type('Owner search');await expect(page.locator('#service-search')).toHaveValue('Owner search');
 await page.locator('#service-search').evaluate((input:HTMLInputElement)=>input.blur());
 await page.screenshot({path:`.runtime/drawer-closed-${info.project.name}.png`});
 await page.touchscreen.tap(768,32);expect(await page.evaluate(()=>(window as any).fixtureState.profileClicks)).toBe(1);
 await page.evaluate(()=>{const handle=(window as any).fixtureShadow.querySelector('.handle');handle.dispatchEvent(new PointerEvent('pointerdown',{pointerId:9,clientY:3,bubbles:true}));handle.dispatchEvent(new PointerEvent('pointermove',{pointerId:9,clientY:50,bubbles:true}));});
 await expect.poll(()=>drawerVisible(page)).toBe(true);
 const boxes=await page.evaluate(()=>[...(window as any).fixtureShadow.querySelectorAll('button.action,.close')].map((element:any)=>{const r=element.getBoundingClientRect();return{width:r.width,height:r.height,bottom:r.bottom,text:element.textContent};}));
 for(const box of boxes){expect(box.width).toBeGreaterThanOrEqual(48);expect(box.height).toBeGreaterThanOrEqual(48);expect(box.bottom).toBeLessThanOrEqual(480);}
 await expect.poll(()=>page.evaluate(()=>getComputedStyle((window as any).fixtureShadow.querySelector('.drawer')).opacity)).toBe('1');
 await page.screenshot({path:`.runtime/drawer-${info.project.name}.png`});
 await control(page,'.close');await expect.poll(()=>drawerVisible(page)).toBe(false);
 const before=await page.evaluate(()=>(window as any).fixtureState.playerClicks);
 await page.touchscreen.tap(400,5);await expect.poll(()=>drawerVisible(page)).toBe(true);
 await page.touchscreen.tap(400,420);await expect.poll(()=>drawerVisible(page)).toBe(false);
 expect(await page.evaluate(()=>(window as any).fixtureState.playerClicks)).toBe(before);
 await page.keyboard.press('Alt+Shift+P');await expect.poll(()=>drawerVisible(page)).toBe(true);await page.keyboard.press('Escape');await expect.poll(()=>drawerVisible(page)).toBe(false);
 await page.touchscreen.tap(768,32);expect(await page.evaluate(()=>(window as any).fixtureState.profileClicks)).toBe(2);
});

test('Enter submission hides the keyboard despite retained input focus', async ({ page }, info) => {
  await page.setContent('<form><input type="text" name="fixture"><button>Submit</button></form>');
  await page.evaluate(language => {
    const actions: string[] = [];
    (window as any).fixtureState = { actions };
    (window as any).chrome = { runtime: { sendMessage(message: { action: string }, callback?: Function) {
      actions.push(message.action); callback?.({ ok: true, language });
    } } };
    document.querySelector('form')!.addEventListener('submit', event => event.preventDefault());
  }, info.project.name === 'touch-ro' ? 'ro' : 'en');
  await page.evaluate(()=>{const original=Element.prototype.attachShadow;Element.prototype.attachShadow=function(options){const shadow=original.call(this,options);if(this.tagName==='PI-HUB-RETURN')(window as any).fixtureShadow=shadow;return shadow;};});
  await page.addScriptTag({ content: extension });
  await page.locator('input').focus();
  expect(await page.evaluate(() => (window as any).fixtureState.actions.at(-1))).toBe('show');
  await page.locator('input').press('Enter');
  expect(await page.evaluate(() => (window as any).fixtureState.actions.at(-1))).toBe('hide');
  expect(await page.evaluate(() => document.activeElement?.tagName)).toBe('INPUT');
});
