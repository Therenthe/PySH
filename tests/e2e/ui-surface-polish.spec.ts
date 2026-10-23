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
  await expect(page.locator('.service-row')).toHaveCount(3);
  const badges=await page.locator('.service-logo').evaluateAll(elements=>elements.map(el=>({background:getComputedStyle(el).backgroundColor,foreground:getComputedStyle(el).color})));
  expect(badges[0].background).toBe('rgb(215, 62, 50)');expect(badges[2].background).toBe('rgb(42, 155, 88)');
  expect(badges[0].foreground).toBe('rgb(255, 255, 255)');
  await page.screenshot({path:info.outputPath('services.png')});
 });
}
