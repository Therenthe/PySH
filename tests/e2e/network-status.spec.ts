import {test,expect,type Page} from '@playwright/test';
import path from 'node:path';
import {textLegibility} from './legibility';

async function fixture(page:Page){
 const entry='/@fs/'+path.resolve('tests/e2e/network-status.fixture.tsx').replaceAll('\\','/');
 await page.route('**/network-status-audit',route=>route.fulfill({contentType:'text/html',body:`<html><body><div id="root"></div><script type="module">import RefreshRuntime from '/@react-refresh';RefreshRuntime.injectIntoGlobalHook(window);window.$RefreshReg$=()=>{};window.$RefreshSig$=()=>type=>type;window.__vite_plugin_react_preamble_installed__=true;</script><script type="module" src="${entry}"></script></body></html>`}));
 await page.goto('/network-status-audit');
 await page.waitForFunction(()=>(window as any).networkFixtureReady);
}
async function show(page:Page,network:unknown,language:string,theme:string){
 await page.evaluate(({network,language,theme})=>(window as any).showNetworkStatus(network,language,theme),{network,language,theme});
 await expect(page.locator('.network-status')).toBeVisible();
}
for(const theme of ['ink','night']){
 test(`actual header retains clock, Android presence and network touch targets ${theme}`,async({page},info)=>{
  const language=info.project.name==='touch-ro'?'ro':'en';
  const network={available:true,state:'connected',connection:'Ethernet',devices:[{type:'wifi',interface:'wlan0',state:'connected',ssid:'Test AP',signal:72},{type:'ethernet',interface:'end0',state:'connected'}],networks:[{ssid:'Test AP',in_use:true,signal:38}]};
  await page.route('**/api/**',route=>{
   const p=new URL(route.request().url()).pathname;
   const json=p==='/api/session'?{token:'test-only-token'}:p==='/api/state'?{
    preferences:{language,theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,homeAutoHideNavigation:false},network,
    bluetooth:{available:false,powered:false,devices:[],prompts:[]},audio:{available:false,ready:false,outputs:[],volume:0},player:{state:'idle'},weather:{available:false},remote:{connected:true,count:1},
   }:p==='/api/radio'?{stations:[]}:p==='/api/network/scan'?{networks:network.networks}:{};
   return route.fulfill({json});
  });
  await page.goto('/');
  const button=page.locator('.top-network.network-status');await expect(button).toBeVisible();
  await expect(button).toHaveAccessibleName(new RegExp(language==='ro'?'Semnal 72%':'Signal 72%'));
  await expect(page.locator('.remote-presence')).toBeVisible();
  const clock=await page.locator('.topbar-time').boundingBox(),networkBox=await button.boundingBox();
  expect(clock!.x+clock!.width).toBeLessThanOrEqual(networkBox!.x);
  const controls=await page.locator('.topbar-right button').all();
  for(const control of controls){const b=await control.boundingBox();expect(b!.height).toBeGreaterThanOrEqual(48);expect(b!.width).toBeGreaterThanOrEqual(48);expect(b!.y+b!.height).toBeLessThanOrEqual(58);expect(b!.x+b!.width).toBeLessThanOrEqual(800);}
  await page.screenshot({path:info.outputPath('actual-network-header.png')});
  await button.tap();await expect(page.locator('.modal-card .network-links')).toBeVisible();
  await expect(page.locator('.modal-card .network-links [data-network-type=wifi]')).toContainText(language==='ro'?'Conectat':'Connected');
 });
 test(`independent network identity, truthful signal and touch action ${theme}`,async({page},info)=>{
  const language=info.project.name==='touch-ro'?'ro':'en',ro=language==='ro';await fixture(page);
  const network={available:true,state:'connected',devices:[{type:'ethernet',interface:'end0',state:'connected'},{type:'wifi',interface:'wlan0',state:'connected',ssid:'Test AP'}],networks:[{ssid:'Neighbour',signal:100,in_use:false},{ssid:'Test AP',signal:38,in_use:true}]};
  await show(page,network,language,theme);
  const status=page.locator('.network-status');
  await expect(status).toHaveAccessibleName(new RegExp(`Wi-Fi: ${ro?'Conectat':'Connected'}, ${ro?'Semnal':'Signal'} 38%; Ethernet: ${ro?'Conectat':'Connected'}`));
  await expect(status.locator('[data-network-link=wifi] svg')).toHaveAttribute('data-signal','1');
  await expect(status.locator('[data-network-link=ethernet]')).toHaveAttribute('data-link-state','connected');
  await status.tap();expect(await page.evaluate(()=>(window as any).networkOpens)).toBe(1);
  const box=await status.boundingBox();expect(box!.height).toBeGreaterThanOrEqual(48);expect(box!.width).toBeGreaterThanOrEqual(48);
  await expect(page.locator('.date-label')).toBeVisible();
  expect(await page.locator('.topbar').evaluate(e=>e.scrollWidth<=e.clientWidth)).toBe(true);
  expect(await textLegibility(page)).toEqual([]);
  await page.screenshot({path:info.outputPath('network-both-connected.png')});

  network.devices[1].state='disconnected';await show(page,network,language,theme);
  await expect(status.locator('[data-network-link=wifi]')).toHaveAttribute('data-link-state','disconnected');
  await expect(status.locator('[data-network-link=wifi] svg')).toHaveAttribute('data-signal','unknown');
  await expect(status).toHaveAccessibleName(new RegExp(`Wi-Fi: ${ro?'Neconectat':'Not connected'}; Ethernet: ${ro?'Conectat':'Connected'}`));
  await page.screenshot({path:info.outputPath('network-wired-wifi-disconnected.png')});

  network.devices[1].state='connected';network.networks[1].in_use=false;await show(page,network,language,theme);
  await expect(status.locator('[data-network-link=wifi] svg')).toHaveAttribute('data-signal','unknown');
  await expect(status).toHaveAccessibleName(new RegExp(ro?'Puterea semnalului indisponibilă':'Signal strength unavailable'));
  const direct={...network,devices:[{type:'wifi',state:'connected',ssid:'Test AP',signal:82}],networks:[{ssid:'Test AP',in_use:true,signal:12}]};
  await show(page,direct,language,theme);
  await expect(status).toHaveAccessibleName(new RegExp(ro?'Semnal 82%':'Signal 82%'));
  await expect(status.locator('svg')).toHaveAttribute('data-signal','3');
  direct.devices[0].signal=-1;direct.networks[0].in_use=false;await show(page,direct,language,theme);
  await expect(status.locator('svg')).toHaveAttribute('data-signal','unknown');
 });
 test(`offline, joining, radio off and unknown are distinct ${theme}`,async({page},info)=>{
  const language=info.project.name==='touch-ro'?'ro':'en',ro=language==='ro';await fixture(page);
  const status=page.locator('.network-status');
  await show(page,{available:true,state:'connecting',devices:[{type:'wifi',state:'ip_config'}]},language,theme);
  await expect(status).toHaveAccessibleName(new RegExp(ro?'Se conectează':'Connecting'));
  await expect(status.locator('[data-network-link=wifi]')).toHaveAttribute('data-link-state','connecting');
  await show(page,{available:true,wireless_enabled:false,devices:[{type:'wifi',state:'unavailable'}]},language,theme);
  await expect(status).toHaveAccessibleName(new RegExp(ro?'Oprit':'Off'));
  await show(page,{available:true,devices:[{type:'wifi',state:'unavailable'}]},language,theme);
  await expect(status).toHaveAccessibleName(new RegExp(ro?'Indisponibil':'Unavailable'));
  await show(page,{available:false,state:'unavailable',devices:[]},language,theme);
  await expect(status.locator('[data-network-link=network]')).toHaveAttribute('data-link-state','unavailable');
  await show(page,{available:true,state:'connected',devices:[]},language,theme);
  await expect(status.locator('[data-network-link=wifi]')).toHaveCount(0);
  await expect(status.locator('[data-network-link=ethernet]')).toHaveCount(0);
  await expect(status).toHaveAccessibleName(new RegExp(`${ro?'Rețea':'Network'}: ${ro?'Conectat':'Connected'}`));
  await show(page,{available:true,devices:[{type:'wifi',state:'unknown'}]},language,theme);
  await expect(status).toHaveAccessibleName(new RegExp(ro?'Stare necunoscută':'Status unknown'));
  expect(await textLegibility(page)).toEqual([]);
 });
}
