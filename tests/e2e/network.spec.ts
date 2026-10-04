import { expect, test, type Locator, type Page } from '@playwright/test';
import { textLegibility } from './legibility';

// These responses exercise the real UI, never a production hardware adapter.
async function networkFixture(page: Page, language: 'en' | 'ro', theme: 'ink' | 'night') {
  const forgotten: unknown[] = [];
  const unexpected: string[] = [];
  const state: any = {
    preferences: { language, theme, setupComplete: true, nightEnabled: false, screensaverMinutes: 0 },
    network: { available: true, state: 'connected', connection: 'Ethernet', devices: [], saved: [{ id: 'saved-profile-id', ssid: 'Saved Wi-Fi' }] },
    bluetooth: { available: false, powered: false, devices: [], prompts: [] },
    audio: { available: false, ready: false, outputs: [], volume: 0 },
    player: { state: 'idle' }, weather: { available: false },
  };
  const f={state,forgotten,unexpected,connected:[] as any[],connectError:false};
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
    else if (path === '/api/network/connect' && request.method() === 'POST') {
      f.connected.push(request.postDataJSON());
      if(f.connectError){await route.fulfill({status:409,json:{error:'authentication_failed'}});return;}
      json={connected:true};
    }
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
  return f;
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

async function enterTestPassword(page:Page,ro:boolean){
 const keyboard=page.locator('.keyboard-card');await expect(keyboard).toBeVisible();
 for(const key of 'testpass')await keyboard.locator('.keys').getByRole('button',{name:key,exact:true}).tap();
 await expect(keyboard.locator('.keyboard-value')).toHaveText('••••••••');
 await keyboard.locator('.final-row').getByRole('button',{name:ro?'Aplică':'Apply',exact:true}).tap();
}

for(const theme of ['ink','night'] as const){
 test(`saved Wi-Fi password uses explicit UUID and survives failure or cancellation ${theme}`,async({page},info)=>{
  const ro=info.project.name==='touch-ro',f=await networkFixture(page,ro?'ro':'en',theme);
  const profile={id:'00000000-0000-4000-8000-000000000001',name:'Family Wi-Fi',ssid:'Protected Wi-Fi',type:'802-11-wireless',security:'secured',active:false};
  f.state.network.saved=[profile];await page.goto('/');
  await page.locator('.main-nav button').nth(3).tap();await page.locator('.settings-tabs button').nth(2).tap();
  const change=page.locator('.settings-panel').getByRole('button',{name:`${ro?'Schimbă parola':'Change password'}: Family Wi-Fi`,exact:true});
  await change.tap();await withinViewport(page.locator('.keyboard-card'));await page.locator('.keyboard-card header button').tap();expect(f.connected).toEqual([]);
  f.connectError=true;await change.tap();await enterTestPassword(page,ro);
  await expect(page.locator('.error-strip')).toContainText(ro?'Autentificarea a eșuat':'Authentication failed');
  expect(f.connected).toEqual([{ssid:profile.ssid,password:'testpass',profile_id:profile.id}]);expect(f.state.network.saved).toEqual([profile]);
  f.connectError=false;await change.tap();await enterTestPassword(page,ro);await expect(page.locator('.toast')).toContainText(profile.ssid);
  expect(f.connected).toHaveLength(2);expect(f.connected[1].profile_id).toBe(profile.id);expect(f.state.network.saved).toHaveLength(1);
  await page.screenshot({path:info.outputPath('saved-password-success.png')});expect(f.unexpected).toEqual([]);
  expect(await textLegibility(page)).toEqual([]);
 });
 test(`same SSID requires saved-profile selection and Forget confirmation ${theme}`,async({page},info)=>{
  const ro=info.project.name==='touch-ro',f=await networkFixture(page,ro?'ro':'en',theme);
  f.state.network.saved=['First profile','Second profile'].map((name,i)=>({id:`00000000-0000-4000-8000-00000000000${i+1}`,name,ssid:'Protected Wi-Fi',type:'802-11-wireless',security:'secured'}));
  await page.goto('/');await page.getByRole('button',{name:ro?'Deschide setările':'Open settings',exact:true}).tap();
  await page.locator('.quick-modal').getByRole('button',{name:`${ro?'Rețea':'Network'} Ethernet`,exact:true}).tap();
  await page.locator('.modal-card .network-row').filter({hasText:'Protected Wi-Fi'}).tap();
  await expect(page.locator('.profile-choices button')).toHaveCount(2);expect(f.connected).toEqual([]);
  await withinViewport(page.locator('.modal-card'));await page.screenshot({path:info.outputPath('saved-profile-choice.png')});
  expect(await textLegibility(page)).toEqual([]);
  await page.locator('.profile-choices button').filter({hasText:'Second profile'}).tap();await enterTestPassword(page,ro);
  expect(f.connected[0]).toEqual({ssid:'Protected Wi-Fi',password:'testpass',profile_id:'00000000-0000-4000-8000-000000000002'});
  await page.getByRole('button',{name:ro?'Deschide setările':'Open settings',exact:true}).tap();await page.locator('.quick-modal').getByRole('button',{name:`${ro?'Rețea':'Network'} Ethernet`,exact:true}).tap();
  await page.locator('.modal-card').getByRole('button',{name:`${ro?'Uită rețeaua':'Forget network'}: First profile`,exact:true}).tap();
  expect(f.forgotten).toEqual([]);await page.locator('.dialog-actions').getByRole('button',{name:ro?'Anulează':'Cancel',exact:true}).tap();
  await expect(page.locator('.saved-network')).toHaveCount(2);expect(f.forgotten).toEqual([]);expect(f.unexpected).toEqual([]);
 });
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
    await modal.locator('.dialog-actions').getByRole('button',{name:labels.forget,exact:true}).tap();
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
