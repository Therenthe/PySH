import {test,expect} from '@playwright/test';
import {effectiveTheme} from '../../app/ui/src/themeSchedule';

test('solar switching uses exact boundaries and survives missing/stale previous-day data',()=>{
 const prefs:any={nightEnabled:true,nightMode:'solar',theme:'ink',timezone:'Europe/Bucharest'};
 const sunrise=Date.parse('2026-10-03T04:15:00Z')/1000,sunset=Date.parse('2026-10-03T15:50:00Z')/1000;
 const weather={timezone:'Europe/Bucharest',daily:[{date:'2026-10-03',sunrise_epoch:sunrise,sunset_epoch:sunset}]};
 expect(effectiveTheme(new Date((sunrise-1)*1000),prefs,weather)).toBe('night');
 expect(effectiveTheme(new Date(sunrise*1000),prefs,weather)).toBe('ink');
 expect(effectiveTheme(new Date(sunset*1000),prefs,weather)).toBe('night');
 expect(effectiveTheme(new Date('2026-10-04T18:00:00Z'),prefs,weather)).toBe('ink');
 expect(effectiveTheme(new Date(sunset*1000),{...prefs,nightEnabled:false},weather)).toBe('ink');
});
for(const theme of ['ink','night'])test(`touch choices persist across clock/poll and full-screen saver ${theme}`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro');
 const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,nightEnabled:false,screensaverMinutes:5,visualizerStyle:'off',screensaverLayout:'clock',timezone:'Europe/Bucharest',favorites:[],shortcuts:[]},network:{},bluetooth:{devices:[],prompts:[]},audio:{ready:true,volume:40},player:{state:'playing',kind:'radio',station_name:'Radio Test'},weather:{}};
 await page.route('**/api/**',async route=>{const path=new URL(route.request().url()).pathname;let json:any={ok:true};if(path==='/api/state')json=state;else if(path==='/api/session')json={token:'test-only'};else if(path==='/api/preferences'){Object.assign(state.preferences,route.request().postDataJSON());json=state.preferences;}else if(path==='/api/audio/visualization')json={available:true,status:'ready',waveform:Array(64).fill(.2),bars:Array(16).fill(.4),peak:.4,rms:.2,silent:false};await route.fulfill({json});});
 await page.clock.install();await page.goto('/');await page.locator('.rail button').filter({hasText:ro?'Setări':'Settings'}).click();
 const trigger=page.getByRole('button',{name:ro?'Vizualizare audio':'Audio visualization',exact:true});await trigger.scrollIntoViewIfNeeded();await trigger.tap();
 const dialog=page.getByRole('dialog');await expect(dialog).toBeVisible();
 const old=await dialog.elementHandle();await page.clock.runFor(6200);await expect(dialog).toBeVisible();expect(await old?.evaluate(node=>node.isConnected)).toBe(true);
 await dialog.getByRole('radio',{name:ro?'Undă':'Wave',exact:true}).tap();await expect(dialog).toBeHidden();expect(state.preferences.visualizerStyle).toBe('wave');
 const timer=page.getByRole('button',{name:ro?'Ceas de repaus':'Clock screensaver',exact:true});await timer.scrollIntoViewIfNeeded();await timer.tap();await page.clock.runFor(3200);await dialog.getByRole('radio',{name:ro?'10 minute':'10 minutes',exact:true}).tap();expect(state.preferences.screensaverMinutes).toBe(10);
 const layout=page.getByRole('button',{name:ro?'Aspect repaus':'Screensaver layout',exact:true});await layout.scrollIntoViewIfNeeded();await layout.tap();await dialog.getByRole('radio',{name:ro?'Doar vizualizator':'Visualizer only'}).tap();
 const preview=page.getByRole('button',{name:ro?'Previzualizează repausul':'Preview screensaver'});await preview.scrollIntoViewIfNeeded();await preview.tap();
 await expect(page.locator('.saver-full-signal .audio-visualizer svg')).toBeVisible();await expect(page.locator('.saver-clock')).toBeHidden();await expect(page.locator('.saver-home')).toBeHidden();
 await page.locator('.saver-full-signal').tap({position:{x:400,y:180}});await expect(page.locator('.saver-home')).toBeVisible();
 await page.clock.runFor(250);await page.screenshot({path:info.outputPath(`saver-controls-${theme}.png`),animations:'disabled'});
 await page.clock.runFor(6500);await expect(page.locator('.saver-home')).toBeHidden();await page.screenshot({path:info.outputPath(`saver-full-${theme}.png`)});
 await page.locator('.saver-full-signal').tap({position:{x:400,y:180}});await page.locator('.saver-home').tap();await expect(page.locator('.pysh-screensaver')).toBeHidden();
});
