import { expect, test, type Page, type TestInfo } from '@playwright/test';
import { readFileSync } from 'node:fs';

// Owned DOM fixtures with fake native replies: these prove browser lifecycle and
// hit testing, not Wayland keyboard visibility or external-service acceptance.
const extension = readFileSync(new URL('../../app/browser-extension/return.js', import.meta.url), 'utf8');
async function fixture(page: Page, info: TestInfo, target: 'film' | 'wrapper') {
  await page.setContent(`<button id="enter">Enter fullscreen</button>
    <div id="wrapper" style="background:black;width:800px;height:480px">
    <video id="film" style="background:black;width:800px;height:480px"></video></div>`);
  await page.evaluate(({ target, language }) => {
    const state = { actions: [] as string[], playerClicks: 0 };
    (window as any).fixtureState = state;
    (window as any).chrome = { runtime: { sendMessage(message: { action: string }, callback?: Function) {
      state.actions.push(message.action); callback?.({ ok: true, language });
    } } };
    document.querySelector('#enter')!.addEventListener('click', () => document.querySelector(`#${target}`)!.requestFullscreen());
    document.querySelector('#film')!.addEventListener('pointerup', () => { state.playerClicks++; });
  }, { target, language: info.project.name === 'touch-ro' ? 'ro' : 'en' });
  await page.addScriptTag({ content: extension });
  await page.click('#enter');
  await expect.poll(() => page.evaluate(() => document.fullscreenElement?.id)).toBe(target);
  await page.evaluate(() => new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))));
}

test('native video fullscreen edge exposes a hittable Return without swallowing player clicks', async ({ page }, info) => {
  await fixture(page, info, 'film');
  await page.touchscreen.tap(400, 240);
  expect(await page.evaluate(() => (window as any).fixtureState.playerClicks)).toBe(1);
  expect(await page.evaluate(() => document.fullscreenElement?.id)).toBe('film');
  await page.touchscreen.tap(780, 20);
  await expect.poll(() => page.evaluate(() => document.fullscreenElement === null)).toBe(true);
  await expect.poll(() => page.evaluate(() => document.querySelector('pi-hub-return')?.parentElement?.tagName)).toBe('HTML');
  await expect.poll(() => page.evaluate(() => document.elementFromPoint(700, 30)?.tagName)).toBe('PI-HUB-RETURN');
  const box = await page.locator('pi-hub-return').boundingBox();
  expect(box!.x + box!.width).toBe(800); expect(box!.y).toBe(0);
  expect(box!.width).toBeGreaterThan(300); expect(box!.height).toBeGreaterThanOrEqual(68);
  await page.touchscreen.tap(700, 30);
  expect(await page.evaluate(() => (window as any).fixtureState.actions.at(-1))).toBe('return');
});

test('container fullscreen overlay fades, reveals and preserves page interaction', async ({ page }, info) => {
  await fixture(page, info, 'wrapper');
  await page.touchscreen.tap(400, 240);
  expect(await page.evaluate(() => (window as any).fixtureState.playerClicks)).toBe(1);
  await page.touchscreen.tap(780, 20);
  await expect.poll(() => page.evaluate(() => document.elementFromPoint(700, 30)?.tagName)).toBe('PI-HUB-RETURN');
  expect(await page.evaluate(() => document.fullscreenElement?.id)).toBe('wrapper');
  await expect.poll(() => page.evaluate(() => document.elementFromPoint(700, 30)?.tagName), { timeout: 6000 }).toBe('VIDEO');
  await page.touchscreen.tap(780, 20);
  await expect.poll(() => page.evaluate(() => document.elementFromPoint(700, 30)?.tagName)).toBe('PI-HUB-RETURN');
  await page.evaluate(() => document.exitFullscreen());
  await expect.poll(() => page.evaluate(() => document.querySelector('pi-hub-return')?.parentElement?.tagName)).toBe('HTML');
});

test('Enter submission hides the keyboard despite retained input focus', async ({ page }, info) => {
  await page.setContent('<form><input type="text" name="fixture"><button>Submit</button></form>');
  await page.evaluate(language => {
    const actions: string[] = [];
    (window as any).fixtureState = { actions };
    (window as any).chrome = { runtime: { sendMessage(message: { action: string }, callback?: Function) {
      actions.push(message.action); callback?.({ ok: true, language });
    } } };
    document.querySelector('form')!.addEventListener('submit', event => event.preventDefault());
  }, info.project.name === 'touch-ro' ? 'ro' : 'en');
  await page.addScriptTag({ content: extension });
  await page.locator('input').focus();
  expect(await page.evaluate(() => (window as any).fixtureState.actions.at(-1))).toBe('show');
  await page.locator('input').press('Enter');
  expect(await page.evaluate(() => (window as any).fixtureState.actions.at(-1))).toBe('hide');
  expect(await page.evaluate(() => document.activeElement?.tagName)).toBe('INPUT');
});
