import {test,expect} from '@playwright/test';

for(const theme of ['ink','night'])test(`one active connection and actual Wi-Fi rooftop state ${theme}`,async({page},info)=>{
 const language=info.project.name.endsWith('ro')?'ro':'en',now=new Date('2026-10-23T18:30:00Z');
 const network={available:true,state:'connected',wireless_enabled:true,active_type:'ethernet' as string|null,active_interface:'end0' as string|null,devices:[{type:'ethernet',interface:'end0',state:'connected'},{type:'wifi',interface:'wlan0',state:'connected',signal:68}]};
 const state={preferences:{language,theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,timezone:'Europe/Bucharest',homeCards:[],favorites:[],location:{latitude:44.4,longitude:26.1}},network,bluetooth:{devices:[],prompts:[]},audio:{ready:true,outputs:[]},player:{state:'idle'},weather:{current:{weather_code:45,is_day:0,temperature_c:13},daily:[],updated_at:now.toISOString(),stale:false}};
 const mutations:string[]=[];
 await page.route('**/api/**',async route=>{
  const request=route.request(),path=new URL(request.url()).pathname;
  if(request.method()!=='GET')mutations.push(path);
  await route.fulfill({json:path==='/api/state'?state:path==='/api/session'?{token:'network-city-fixture'}:{ok:true}});
 });
 await page.clock.install({time:now});await page.goto('/');
 const city=page.locator('.city-diorama'),header=page.locator('.network-status');
 await expect(city).toHaveAttribute('data-wifi','connected');await expect(city).toHaveAttribute('data-wifi-active','false');
 await expect(header.locator('[data-network-link]')).toHaveCount(1);await expect(header.locator('[data-network-link=ethernet]')).toHaveCount(1);
 await expect(page.locator('.city-wifi')).toBeVisible();
 await page.screenshot({path:info.outputPath('ethernet-wifi-standby.png')});

 network.active_type='wifi';network.active_interface='wlan0';network.devices[0].state='disconnected';
 await page.clock.runFor(2600);
 await expect(header.locator('[data-network-link]')).toHaveCount(1);await expect(header.locator('[data-network-link=wifi] svg')).toHaveAttribute('data-signal','2');
 await expect(city).toHaveAttribute('data-wifi-active','true');
 await page.screenshot({path:info.outputPath('wifi-active-building.png')});

 network.devices[0].state='connected';network.active_type='ethernet';network.active_interface='end0';
 await page.clock.runFor(2600);
 await expect(header.locator('[data-network-link=ethernet]')).toHaveCount(1);await expect(city).toHaveAttribute('data-wifi-active','false');
 network.wireless_enabled=false;network.devices[1].state='unavailable';
 await page.clock.runFor(2600);await expect(city).toHaveAttribute('data-wifi','off');
 await expect(header.locator('[data-network-link=ethernet]')).toHaveCount(1);
 await expect(header.locator('[data-network-link=wifi]')).toHaveCount(0);
 expect(mutations).toEqual([]);
});
