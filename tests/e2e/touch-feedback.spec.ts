import {test,expect} from '@playwright/test';
for(const theme of ['ink','night']){
 test(`touch feedback ${theme}: down, up, cancellation and scrolling`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro');
  const state={preferences:{language:ro?'ro':'en',theme,setupComplete:true,screensaverMinutes:0,favorites:[],shortcuts:['radio','media'],lastStation:{name:'Radio remembered',url:'https://example.com/radio'}},network:{},bluetooth:{devices:[],prompts:[]},audio:{ready:true,volume:20},player:{kind:'radio',state:'idle',url:''},weather:{}};
  await page.route('**/api/**',route=>route.fulfill({json:new URL(route.request().url()).pathname==='/api/state'?state:{token:'browser-only',stations:[]}}));await page.goto('/');
  const button=page.locator('.main-nav button').first(),box=(await button.boundingBox())!,cdp=await page.context().newCDPSession(page),point={x:box.x+box.width/2,y:box.y+box.height/2};
  for(const end of ['up','cancel','move','blur']){
   await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[point]});await expect(button).toHaveAttribute('data-pressed','true');expect(await button.evaluate(el=>getComputedStyle(el).boxShadow)).not.toBe('none');
   if(end==='move')await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:point.x,y:point.y+25}]});
   if(end==='blur')await page.evaluate(()=>window.dispatchEvent(new Event('blur')));
   await cdp.send('Input.dispatchTouchEvent',{type:end==='cancel'?'touchCancel':'touchEnd',touchPoints:[]});await expect(button).not.toHaveAttribute('data-pressed','true');
  }
  await page.locator('.main-nav button').nth(1).tap();await expect(page.locator('.radio-station-name')).toHaveText('Radio remembered');await expect(page.locator('.radio-side .eyebrow')).toHaveText(ro?'Ultimul post':'Last station');await expect(page.locator('.radio-track-name')).toHaveCount(0);
 });
}
