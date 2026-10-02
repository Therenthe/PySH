import { expect, test, type Locator, type Page } from '@playwright/test';

// These responses exercise the real UI, never a production hardware adapter.
async function networkFixture(page: Page, language: 'en' | 'ro', theme: 'ink' | 'night') {
  const forgotten: unknown[] = [];
  const unexpected: string[] = [];
  const state = {
    preferences: { language, theme, setupComplete: true, nightEnabled: false, screensaverMinutes: 0 },
    network: { available: true, state: 'connected', connection: 'Ethernet', devices: [], saved: [{ id: 'saved-profile-id', ssid: 'Saved Wi-Fi' }] },
    bluetooth: { available: false, powered: false, devices: [], prompts: [] },
    audio: { available: false, ready: false, outputs: [], volume: 0 },
    player: { state: 'idle' }, weather: { available: false },
  };
  await page.route('**/api/**', async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    let json: unknown;
    if (path === '/api/session' && request.method() === 'GET') json = { token: 'test-only-token' };
    else if (path === '/api/state' && request.method() === 'GET') json = state;
    else if (path === '/api/radio' && request.method() === 'GET') json = { stations: [] };
    else if (path === '/api/network/scan' && request.method() === 'POST') json = { networks: [
      { ssid: 'Open Wi-Fi', security: 'open', signal: 80 },
      { ssid: 'Protected Wi-Fi', security: 'secured', signal: 65 },
    ] };
    else if (path === '/api/network/forget' && request.method() === 'POST') {
      forgotten.push(request.postDataJSON());
      state.network.saved = [];
      json = { ok: true };
    } else {
      unexpected.push(`${request.method()} ${path}`);
      await route.fulfill({ status: 500, json: { error: 'unexpected_test_request' } });
      return;
    }
    await route.fulfill({ json });
  });
  return { forgotten, unexpected };
}

async function withinViewport(locator: Locator) {
  await expect(locator).toBeVisible();
  const box = await locator.boundingBox();
  expect(box).not.toBeNull();
  expect(box!.x).toBeGreaterThanOrEqual(0);
  expect(box!.y).toBeGreaterThanOrEqual(0);
  expect(box!.x + box!.width).toBeLessThanOrEqual(800);
  expect(box!.y + box!.height).toBeLessThanOrEqual(480);
}

for (const theme of ['ink', 'night'] as const) {
  test(`network settings and saved connection actions in ${theme}`, async ({ page }, testInfo) => {
    const ro = testInfo.project.name === 'touch-ro';
    const language = ro ? 'ro' : 'en';
    const labels = ro ? { settings: 'Setări', network: 'Rețea', scan: 'Scanează', open: 'Rețea deschisă', secured: 'Rețea securizată', quick: 'Deschide setările', forget: 'Uită rețeaua', close: 'Închide' }
      : { settings: 'Settings', network: 'Network', scan: 'Scan nearby', open: 'Open network', secured: 'Secured network', quick: 'Open settings', forget: 'Forget network', close: 'Close' };
    const fixture = await networkFixture(page, language, theme);
    const browserErrors: string[] = [];
    page.on('pageerror', error => browserErrors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') browserErrors.push(message.text()); });
    await page.goto('/');
    await expect(page.locator('.app')).toHaveAttribute('data-theme', theme);
    await expect(page.locator('html')).toHaveAttribute('lang', language);
    await page.screenshot({ path: testInfo.outputPath('home.png') });
    await page.locator('.main-nav').getByRole('button', { name: labels.settings, exact: true }).tap();
    await page.locator('.settings-tabs').getByRole('button', { name: labels.network, exact: true }).tap();
    await page.locator('.settings-panel').getByRole('button', { name: labels.scan, exact: true }).tap();
    const choices = page.locator('.network-choices');
    await expect(choices.getByRole('button', { name: `Open Wi-Fi ${labels.open} · 80%`, exact: true })).toBeVisible();
    await expect(choices.getByRole('button', { name: `Protected Wi-Fi ${labels.secured} · 65%`, exact: true })).toBeVisible();
    await page.screenshot({ path: testInfo.outputPath('network-settings.png') });
    await page.getByRole('button', { name: labels.quick, exact: true }).tap();
    await page.locator('.quick-modal').getByRole('button', { name: `${labels.network} Ethernet`, exact: true }).tap();
    const modal = page.locator('.modal-card');
    await withinViewport(modal);
    await expect(modal.locator('.network-row').filter({ hasText: 'Open Wi-Fi' })).toContainText(labels.open);
    await expect(modal.locator('.network-row').filter({ hasText: 'Protected Wi-Fi' })).toContainText(labels.secured);
    await expect(modal.locator('button button')).toHaveCount(0);
    const forget = modal.getByRole('button', { name: `${labels.forget}: Saved Wi-Fi`, exact: true });
    await withinViewport(forget);
    await page.screenshot({ path: testInfo.outputPath('network-modal.png') });
    await forget.tap();
    await expect.poll(() => fixture.forgotten).toEqual([{ id: 'saved-profile-id' }]);
    await expect(modal.getByText('Saved Wi-Fi', { exact: true })).toHaveCount(0);
    await modal.getByRole('button', { name: labels.close, exact: true }).tap();
    await expect(modal).toHaveCount(0);
    await page.locator('.main-nav').getByRole('button', { name: 'Radio', exact: true }).tap();
    await expect(page.getByText(ro ? 'Nu am găsit posturi' : 'No stations found', { exact: true })).toBeVisible();
    await page.screenshot({ path: testInfo.outputPath('radio-empty.png') });
    expect(fixture.unexpected).toEqual([]);
    expect(browserErrors).toEqual([]);
  });
}
