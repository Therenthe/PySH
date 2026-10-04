import {test,expect} from '@playwright/test';
for(const theme of ['ink','night'])test(`ambient pending protection, retry and independent idle guards ${theme}`,async({page},info)=>{
 test.setTimeout(60000);const ro=info.project.name.endsWith('ro');let fail=false;let gate=false;const releases:Array<()=>void>=[];let calls=0;
 const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,nightEnabled:false,screensaverMinutes:1,navigationCollapsed:false,navigationAutoHide:false,decorativeAircraft:true,decorativeLunarDust:true,homePositions:{weather:{x:0,y:0,anchorX:'right',anchorY:'bottom'}},visualizerStyle:'wave'},network:{state:'connected'},bluetooth:{devices:[],prompts:[]},audio:{ready:true,volume:30,mute:false},player:{state:'playing',kind:'radio',station_name:'Station',url:'https://example.org/stream'},weather:{current:{temperature_c:13,weather_code:0,is_day:0},daily:[],stale:false}};
 await page.addInitScript(()=>{AbortSignal.timeout=()=>new AbortController().signal;crypto.getRandomValues=((array:Uint32Array)=>{array.fill(0);return array;}) as typeof crypto.getRandomValues;});
 await page.route('**/api/**',async route=>{const path=new URL(route.request().url()).pathname;let json:any={ok:true};if(path==='/api/session')json={token:'fixture'};else if(path==='/api/state')json=state;else if(path==='/api/preferences'){calls++;const ambient=Object.keys(route.request().postDataJSON()).some(key=>key.startsWith('decorative'));if(gate&&ambient)await new Promise<void>(resolve=>releases.push(resolve));if(fail&&ambient)return route.fulfill({status:500,json:{error:'save_failed'}});Object.assign(state.preferences,route.request().postDataJSON());json=state.preferences;}else if(path==='/api/audio/visualization')json={available:true,status:'ready',waveform:Array(64).fill(.2),bars:Array(16).fill(.3),peak:.4,rms:.2,silent:false};await route.fulfill({json});});

 await page.clock.install();await page.goto('/');await page.evaluate(()=>{AbortSignal.timeout=()=>new AbortController().signal;});
 const settings=async()=>{await page.locator('.main-nav button').nth(3).tap();await page.locator('.settings-tabs button').filter({hasText:ro?'Acasă':'Home'}).tap();};await settings();
 const names=[ro?'Avioane decorative':'Decorative aircraft',ro?'Praf lunar decorativ':'Decorative lunar dust'];
 for(const name of names){
 const button=page.getByRole('button',{name,exact:true});await button.scrollIntoViewIfNeeded();const start=calls;gate=true;
 // Deliberately dispatch both before React can paint: the synchronous lock must protect this case too.
 await button.evaluate(el=>{el.dispatchEvent(new MouseEvent('click',{bubbles:true}));el.dispatchEvent(new MouseEvent('click',{bubbles:true}));});
 await expect.poll(()=>calls).toBe(start+1);await expect(button).toBeDisabled();await expect(button).toHaveAttribute('aria-busy','true');await expect(button).toHaveAttribute('aria-pressed','true');await expect(page.getByRole('status').filter({hasText:ro?'Se salvează…':'Saving…'})).toBeVisible();
 for(const other of names)await expect(page.getByRole('button',{name:other,exact:true})).toBeDisabled();
 // Complete a separate generic preference mutation, clearing global busy while ambient PATCH remains held.
 const shortcut=page.locator('.settings-panel').getByRole('button',{name:ro?'Radio':'Radio',exact:true});await shortcut.scrollIntoViewIfNeeded();await shortcut.tap();await expect.poll(()=>calls).toBe(start+2);await page.clock.runFor(65000);await expect(page.locator('.pysh-screensaver')).toHaveCount(0);
 await expect(button).toBeDisabled();await page.locator('.main-nav button').nth(0).tap();await page.clock.runFor(35000);await expect(page.locator('.app')).toHaveAttribute('data-home-phase','interactive');await expect(page.locator('.pysh-screensaver')).toHaveCount(0);
 fail=true;gate=false;releases.splice(0).forEach(resolve=>resolve());await expect(page.locator('.error-strip')).toBeVisible();await settings();await button.scrollIntoViewIfNeeded();await expect(button).toBeEnabled();await expect(button).toHaveAttribute('aria-busy','false');await expect(button).toHaveAttribute('aria-pressed','true');
 fail=false;await button.tap();await expect(button).toHaveAttribute('aria-pressed','false');await expect(button).toBeEnabled();await expect(page.getByRole('status').filter({hasText:ro?'Se salvează…':'Saving…'})).toHaveCount(0);await page.reload();await page.evaluate(()=>{AbortSignal.timeout=()=>new AbortController().signal;});await settings();await button.scrollIntoViewIfNeeded();await expect(button).toHaveAttribute('aria-pressed','false');
 }
});
