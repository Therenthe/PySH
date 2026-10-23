import {test,expect,type Page} from '@playwright/test';
import path from 'node:path';

async function fixture(page:Page){
 const entry='/@fs/'+path.resolve('tests/e2e/city-wifi.fixture.tsx').replaceAll('\\','/');
 await page.route('**/city-wifi-audit',route=>route.fulfill({contentType:'text/html',body:`<html><head><style>html,body,#root{margin:0;width:800px;height:480px;overflow:hidden}</style></head><body><div id="root"></div><script type="module">import RefreshRuntime from '/@react-refresh';RefreshRuntime.injectIntoGlobalHook(window);window.$RefreshReg$=()=>{};window.$RefreshSig$=()=>type=>type;window.__vite_plugin_react_preamble_installed__=true;</script><script type="module" src="${entry}"></script></body></html>`}));
 await page.goto('/city-wifi-audit');
 await page.waitForFunction(()=>(window as any).cityWifiFixtureReady);
}

for(const night of [false,true])test(`Blender rooftop Wi-Fi ${night?'night':'day'}: standby differs from actual route and disabled radio`,async({page},info)=>{
 await fixture(page);
 const show=(state:string,active:boolean)=>page.evaluate(({night,state,active})=>(window as any).showCityWifi(night,state,active),{night,state,active});
 await show('connected',false);
 const city=page.locator('.city-diorama'),roof=page.locator('.city-wifi'),emission=page.locator('.city-wifi-emission'),lamp=page.locator('.city-wifi-lamp');
 await expect(city).toHaveAttribute('data-wifi','connected');
 await expect(city).toHaveAttribute('data-wifi-active','false');
 await expect(roof).toBeVisible();
 await expect(emission).toHaveCSS('opacity','0');
 await expect(emission).toHaveCSS('animation-name','none');
 await expect(lamp).toHaveCSS('opacity','1');
 const images=await roof.locator('img').evaluateAll(images=>images.map(node=>({width:(node as HTMLImageElement).naturalWidth,height:(node as HTMLImageElement).naturalHeight,loaded:(node as HTMLImageElement).complete})));
 expect(images).toEqual([{width:73,height:89,loaded:true},{width:73,height:89,loaded:true}]);
 // The crop keeps the source camera's full-city proportions, without reflow
 // moving the prop off its x6.3 pitched roof when the display width changes.
 for(const width of [800,700]){
  await page.locator('.app').evaluate((node,width)=>(node as HTMLElement).style.width=`${width}px`,width);
  const architecture=await page.locator('.city-architecture').boundingBox(),r=await roof.boundingBox();
  expect(r!.x).toBeCloseTo(architecture!.x+architecture!.width*.6975,0);
  expect(r!.y).toBeCloseTo(architecture!.y+architecture!.height*.26842105,0);
  expect(r!.width).toBeCloseTo(architecture!.width*.045625,0);
  expect(r!.height).toBeCloseTo(architecture!.height*.15614035,0);
 }
 await page.locator('.app').evaluate(node=>(node as HTMLElement).style.width='800px');
 await page.screenshot({path:info.outputPath(`wifi-${night?'night':'day'}-standby.png`)});
 await show('connected',true);
 await expect(city).toHaveAttribute('data-wifi-active','true');
 await expect(emission).toHaveCSS('animation-name','city-wifi-transmission');
 await page.screenshot({path:info.outputPath(`wifi-${night?'night':'day'}-active.png`)});
 await show('connecting',true);
 await expect(city).toHaveAttribute('data-wifi-active','false');
 await expect(emission).toHaveCSS('animation-name','city-wifi-search');
 await show('disconnected',true);
 await expect(emission).toHaveCSS('opacity','0');
 await expect(emission).toHaveCSS('animation-name','none');
 await expect(lamp).not.toHaveCSS('opacity','1');
 await show('off',true);
 await expect(city).toHaveAttribute('data-wifi-active','false');
 await expect(emission).toHaveCSS('opacity','0');
 await expect(emission).toHaveCSS('animation-name','none');
 await expect(lamp).toHaveCSS('opacity','0');
 await page.screenshot({path:info.outputPath(`wifi-${night?'night':'day'}-off.png`)});
 await show('unknown',false);
 await expect(emission).toHaveCSS('opacity','0');
 await expect(lamp).toHaveCSS('opacity','0');
 await show('connected',true);
 await page.emulateMedia({reducedMotion:'reduce'});
 await expect(emission).toHaveCSS('animation-name','none');
 // Actual decorative animations pause when the document is hidden; unlike the
 // API association this presentation flag never changes network truth.
 await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'));});
 await expect(city).toHaveAttribute('data-animate','false');
 await expect(emission).toHaveCSS('animation-play-state','paused');
 await expect(city).toHaveAttribute('data-wifi-active','true');
 expect(await roof.evaluate(node=>getComputedStyle(node).pointerEvents)).toBe('none');
});
