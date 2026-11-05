import {test,expect} from '@playwright/test';
import {settingsFixture} from './settings-fixture';

for(const theme of ['ink','night'] as const){
 test(`recovery warning stays circular with navigation present ${theme}`,async({page},info)=>{
  const language=info.project.name==='touch-ro'?'ro':'en';await settingsFixture(page,language,theme);
  await page.route('**/api/radio?**',route=>route.fulfill({status:503,json:{error:'network_unavailable'}}));
  await page.locator('.main-nav button').nth(1).tap();await expect(page.locator('.error-strip')).toBeVisible();
  const warning=await page.locator('.error-dot').boundingBox();expect(warning!.width).toBeLessThanOrEqual(21);expect(warning!.height).toBeGreaterThanOrEqual(18);
  const navigation=await page.locator('.error-strip .recovery-navigation').boundingBox();expect(navigation!.width).toBeGreaterThanOrEqual(48);expect(navigation!.height).toBeGreaterThanOrEqual(48);
  await page.screenshot({path:info.outputPath('recovery.png')});
 });
 test(`service badges retain their recognizable colored backing ${theme}`,async({page},info)=>{
  const language=info.project.name==='touch-ro'?'ro':'en';await settingsFixture(page,language,theme);
  await page.locator('.main-nav button').nth(2).tap();await page.locator('.media-sections button').nth(1).tap();
  await expect(page.locator('.service-row')).toHaveCount(4);
  await expect(page.locator('.service-panel>.muted')).toHaveText(language==='ro'?'TV rulează în PySH. Celelalte servicii deschid site-urile oficiale.':'Watch TV in PySH. Other services open their official websites.');
  const soft=await page.locator('.service-iptv').evaluate(el=>{const sample=document.createElement('span');sample.style.backgroundColor='var(--soft)';el.append(sample);const value=getComputedStyle(sample).backgroundColor;sample.remove();return value;});
  await expect(page.locator('.service-logo.service-iptv')).toHaveCSS('background-color',soft);
  await expect(page.locator('.service-logo.service-youtube')).toHaveCSS('background-color','rgb(215, 62, 50)');
  await expect(page.locator('.service-logo.service-spotify')).toHaveCSS('background-color','rgb(42, 155, 88)');
  await expect(page.locator('.service-logo.service-youtube')).toHaveCSS('color','rgb(255, 255, 255)');
  await page.screenshot({path:info.outputPath('services.png')});
 });
}
