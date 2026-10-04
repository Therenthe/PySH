import {test,expect} from '@playwright/test';
test('open settings choice blocks idle and explains failed saves without losing selection',async({page},info)=>{
 const ro=info.project.name.endsWith('ro');
 const state={preferences:{language:ro?'ro':'en',theme:'night',setupComplete:true,nightEnabled:false,screensaverMinutes:1,visualizerStyle:'wave',timezone:'Europe/Bucharest'},network:{},bluetooth:{devices:[],prompts:[]},audio:{},player:{},weather:{}};
 await page.route('**/api/**',async route=>{const path=new URL(route.request().url()).pathname;if(path==='/api/preferences'){await route.fulfill({status:500,json:{error:'preferences_unavailable'}});return;}await route.fulfill({json:path==='/api/state'?state:path==='/api/session'?{token:'test-only'}:{ok:true}});});
 await page.clock.install();await page.goto('/');await page.locator('.main-nav button').nth(3).tap();
 const button=page.getByRole('button',{name:ro?'Vizualizare audio':'Audio visualization',exact:true});await button.scrollIntoViewIfNeeded();await button.tap();
 await page.clock.runFor(65000);await expect(page.getByRole('dialog')).toBeVisible();await expect(page.locator('.pysh-screensaver')).toHaveCount(0);
 await page.getByRole('radio',{name:ro?'Niveluri':'Levels',exact:true}).tap();await expect(page.getByRole('dialog').getByRole('alert')).toBeVisible();await expect(page.getByRole('radio',{name:ro?'Undă':'Wave',exact:true})).toHaveAttribute('aria-checked','true');
 await page.getByRole('dialog').getByRole('button',{name:ro?'Închide':'Close',exact:true}).tap();await expect(page.getByRole('dialog')).toBeHidden();
});
