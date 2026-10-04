import {expect,type Page} from '@playwright/test';
export async function settingsFixture(page:Page,language:'en'|'ro',theme:'ink'|'night',time='2026-10-03T12:04:00Z'){
 await page.clock.install({time:new Date(time)});
 const station={uuid:'11111111-1111-4111-8111-111111111111',name:'Radio retained',url:'https://radio.example.org/retained'};
 const state:any={preferences:{language,theme,setupComplete:true,nightEnabled:false,nightMode:'solar',nightStart:'22:00',nightEnd:'07:00',screensaverMinutes:0,timezone:'Europe/Bucharest',location:{name:'București · Sector 5',latitude:44.4,longitude:26.07},lastStation:station,favorites:[],accent:'sage'},network:{available:true,state:'connected'},bluetooth:{devices:[],prompts:[]},audio:{ready:true,volume:30,mute:false},player:{kind:'radio',state:'playing',url:station.url,station_name:station.name,title:'Retained song'},weather:{timezone:'Europe/Bucharest',stale:false,current:{temperature_c:13,is_day:1,weather_code:0},daily:[{date:'2026-10-03',sunrise_epoch:1791000900,sunset_epoch:1791042600}]} };
 // Provider UTC epochs: 2026-10-03 04:15Z / 15:50Z (07:15 /18:50 Bucharest).
 state.weather.daily[0].sunrise_epoch=Date.parse('2026-10-03T04:15:00Z')/1000;state.weather.daily[0].sunset_epoch=Date.parse('2026-10-03T15:50:00Z')/1000;
 const writes:any[]=[],other:any[]=[],failKeys=new Set<string>();
 await page.route('**/api/**',async route=>{const req=route.request(),path=new URL(req.url()).pathname;let json:any={ok:true};if(path==='/api/session')json={token:'fixture'};else if(path==='/api/state')json=state;else if(path==='/api/radio')json={stations:[station]};else if(path==='/api/preferences'&&req.method()==='PATCH'){const body=req.postDataJSON();writes.push(body);if(Object.keys(body).some(key=>failKeys.has(key))){await route.fulfill({status:500,json:{error:'preferences_unavailable'}});return;}Object.assign(state.preferences,body);json=state.preferences;}else if(req.method()!=='GET')other.push({path,body:req.postDataJSON()});await route.fulfill({json});});
 await page.goto('/');await page.locator('.main-nav button').nth(3).tap();await expect(page.locator('.settings-panel')).toBeVisible();return{state,writes,other,failKeys};
}
export async function retainsSettingsAndRadio(page:Page,language:'en'|'ro'){
 await expect(page.locator('.settings-page')).toBeVisible();await expect(page.locator('.settings-tabs button').first()).toHaveClass(/active/);await expect(page.locator('.settings-panel h2')).toHaveText(language==='ro'?'Aspect':'Appearance');await expect(page.locator('.now-copy b')).toHaveText('Radio retained');await expect(page.locator('.now-copy span')).toHaveText('Retained song');await expect(page.locator('.now-state')).toHaveText(language==='ro'?'Se redă':'Playing');
}
