import {expect, test} from '@playwright/test';

// Touch end produces a compatibility click. Pending/retry feedback must not
// move another action underneath that same gesture and navigate accidentally.
for (const theme of ['ink', 'night'] as const) {
  for (const mode of ['immediate', 'held', 'rejected'] as const) {
    test(`Quick volume retains its dialog during ${mode} update ${theme}`, async ({page}, info) => {
      const ro = info.project.name.endsWith('ro');
      const state: any = {
        preferences: {language: ro ? 'ro' : 'en', theme, setupComplete: true, nightEnabled: false, screensaverMinutes: 0},
        network: {available: true, state: 'connected', connection: 'Fixture Ethernet'},
        bluetooth: {available: true, devices: [], prompts: []},
        audio: {available: true, ready: true, volume: 40, mute: false, outputs: [{id: 'fixture', description: 'Fixture speaker', active: true}]},
        player: {kind: 'radio', state: 'playing', station_name: 'Fixture Radio', url: 'https://example.org/radio'},
        weather: {},
        power: {standby: false, brightness: {available: true, value: 80}, timer: {}, daily: {enabled: false, time: '23:00'}},
      };
      const writes: any[] = [];
      let release = () => {};
      const gate = new Promise<void>(resolve => { release = resolve; });
      await page.route('**/api/**', async route => {
        const request = route.request(), path = new URL(request.url()).pathname;
        let json: any = {ok: true};
        if (path === '/api/session') json = {token: 'fixture-only'};
        else if (path === '/api/state') json = state;
        else if (path === '/api/audio' && request.method() === 'POST') {
          const body = request.postDataJSON();
          writes.push(body);
          if (mode === 'held') await gate;
          if (mode === 'rejected' && writes.length === 1) {
            await route.fulfill({status: 503, json: {error: 'audio_unavailable'}});
            return;
          }
          Object.assign(state.audio, body);
          json = state.audio;
        }
        await route.fulfill({json});
      });
      await page.goto('/');
      await page.locator('.quick-controls-button').tap();
      const quick = page.getByRole('dialog', {name: ro ? 'Comenzi rapide' : 'Quick controls', exact: true});
      await expect(quick).toBeVisible();
      const slider = quick.getByRole('slider', {name: ro ? 'Volum' : 'Volume', exact: true});
      const allSettings = quick.getByRole('button', {name: ro ? 'Toate setările' : 'All settings', exact: true});
      const before = (await slider.boundingBox())!;
      expect(before.y).toBeGreaterThanOrEqual(0);
      expect(before.y + before.height).toBeLessThanOrEqual(480);
      await page.screenshot({path: info.outputPath('01-before-volume.png')});
      await page.evaluate(() => {
        (window as any).__quickTouchEvents = [];
        for (const type of ['pointerdown', 'pointerup', 'click']) {
          document.addEventListener(type, event => {
            const el = event.target as HTMLElement;
            (window as any).__quickTouchEvents.push({type, tag: el.tagName, label: el.getAttribute('aria-label'), text: el.closest('button')?.textContent?.trim(), trusted: event.isTrusted});
          }, true);
        }
      });
      try {
        await slider.tap({position: {x: before.width * .65, y: before.height / 2}});
        await expect.poll(() => writes.length).toBe(1);
        expect(writes).toEqual([{volume: 65}]);
        await page.evaluate(() => new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))));
        await expect(quick).toBeVisible();
        await expect(allSettings).toBeVisible();
        await expect(page.locator('.quick-modal')).toBeVisible();
        const after = (await slider.boundingBox())!;
        expect(Math.abs(after.y - before.y)).toBeLessThan(1);
        if (mode === 'held') {
          await expect(slider).toBeDisabled();
          expect(state.audio.volume).toBe(40);
          await page.screenshot({path: info.outputPath('02-held-volume.png')});
          release();
        } else if (mode === 'rejected') {
          const alert = quick.getByRole('alert');
          await expect(alert).toBeVisible();
          expect(state.audio.volume).toBe(40);
          const bodyClip = (await quick.locator('.modal-body').boundingBox())!;
          // Inspect the targets before Playwright's tap can auto-scroll them.
          for (const name of [ro ? 'Încearcă din nou' : 'Try again', ro ? 'Închide' : 'Close']) {
            const control = alert.getByRole('button', {name, exact: true});
            const rect = (await control.boundingBox())!;
            expect(Math.round(rect.width * 1000) / 1000).toBeGreaterThanOrEqual(48);
            expect(Math.round(rect.height * 1000) / 1000).toBeGreaterThanOrEqual(48);
            expect(rect.x).toBeGreaterThanOrEqual(0);
            expect(rect.y).toBeGreaterThanOrEqual(0);
            expect(rect.x + rect.width).toBeLessThanOrEqual(800);
            expect(rect.y + rect.height).toBeLessThanOrEqual(480);
            expect(Math.round((bodyClip.x - rect.x) * 1000) / 1000).toBeLessThanOrEqual(0);
            expect(Math.round((bodyClip.y - rect.y) * 1000) / 1000).toBeLessThanOrEqual(0);
            expect(Math.round((rect.x + rect.width - bodyClip.x - bodyClip.width) * 1000) / 1000).toBeLessThanOrEqual(0);
            expect(Math.round((rect.y + rect.height - bodyClip.y - bodyClip.height) * 1000) / 1000).toBeLessThanOrEqual(0);
            expect(await control.evaluate(el => {
              const b = el.getBoundingClientRect();
              return [.1, .5, .9].every(fraction => el.contains(document.elementFromPoint(b.x + b.width / 2, b.y + b.height * fraction)));
            })).toBe(true);
          }
          await page.screenshot({path: info.outputPath('02-rejected-volume.png')});
          await quick.getByRole('button', {name: ro ? 'Încearcă din nou' : 'Try again', exact: true}).tap();
        }
        await expect(slider).toBeEnabled();
        await expect(slider).toHaveValue('65');
        await expect(quick).toBeVisible();
        await expect(allSettings).toBeVisible();
        expect(state.audio.volume).toBe(65);
        expect(writes).toEqual(mode === 'rejected' ? [{volume: 65}, {volume: 65}] : [{volume: 65}]);
        await page.screenshot({path: info.outputPath('03-volume-saved-in-quick.png')});
      } finally {
        release();
        await info.attach('quick-volume-events', {body: JSON.stringify({mode, theme, writes, events: await page.evaluate(() => (window as any).__quickTouchEvents), dialogs: await page.getByRole('dialog').allTextContents()}, null, 2), contentType: 'application/json'});
      }
    });
  }

  test(`Quick retains long output recovery carried from Audio ${theme}`, async ({page}, info) => {
    const ro = info.project.name.endsWith('ro');
    const longName = 'Fixture output ' + 'W'.repeat(400);
    const state: any = {
      preferences: {language: ro ? 'ro' : 'en', theme, setupComplete: true, nightEnabled: false, screensaverMinutes: 0},
      network: {available: true, state: 'connected', connection: 'Fixture Ethernet'},
      bluetooth: {available: true, devices: [], prompts: []},
      audio: {available: true, ready: true, volume: 40, mute: false, outputs: [{id: 'existing', description: 'Existing speaker', active: true}, {id: 'long-output', description: longName, active: false}]},
      player: {kind: 'radio', state: 'playing', station_name: 'Fixture Radio', url: 'https://example.org/radio'},
      weather: {},
      power: {standby: false, brightness: {available: true, value: 80}, timer: {}, daily: {enabled: false, time: '23:00'}},
    };
    const writes: unknown[] = [];
    await page.route('**/api/**', async route => {
      const request = route.request(), path = new URL(request.url()).pathname;
      let json: any = {ok: true};
      if (path === '/api/session') json = {token: 'fixture-only'};
      else if (path === '/api/state') json = state;
      else if (path === '/api/audio' && request.method() === 'POST') {
        writes.push(request.postDataJSON());
        if (writes.length === 1) {
          await route.fulfill({status: 503, json: {error: 'audio_unavailable'}});
          return;
        }
        state.audio.outputs.forEach((output: any) => { output.active = output.id === 'long-output'; });
        json = state.audio;
      }
      await route.fulfill({json});
    });
    await page.goto('/');
    await page.locator('.quick-controls-button').tap();
    await page.locator('.quick-modal>button').nth(2).tap();
    const audio = page.getByRole('dialog', {name: 'Audio', exact: true});
    await expect(audio).toBeVisible();
    await audio.locator('.modal-list button').last().tap();
    await expect(audio.getByRole('alert')).toContainText(longName);
    await audio.locator('header').getByRole('button', {name: ro ? 'Închide' : 'Close', exact: true}).tap();
    // The persistent recovery banner replaces the header; Settings remains an
    // available user route to Quick controls without dismissing the error.
    await page.locator('.main-nav button').nth(3).tap();
    await page.locator('.settings-quick-control').tap();
    const quick = page.getByRole('dialog', {name: ro ? 'Comenzi rapide' : 'Quick controls', exact: true});
    const alert = quick.getByRole('alert');
    await expect(alert).toContainText(longName);
    const bodyClip = (await quick.locator('.modal-body').boundingBox())!;
    for (const name of [ro ? 'Încearcă din nou' : 'Try again', ro ? 'Închide' : 'Close']) {
      const control = alert.getByRole('button', {name, exact: true});
      const rect = (await control.boundingBox())!;
      expect(Math.round(rect.width * 1000) / 1000).toBeGreaterThanOrEqual(48);
      expect(Math.round(rect.height * 1000) / 1000).toBeGreaterThanOrEqual(48);
      expect(rect.x).toBeGreaterThanOrEqual(0);
      expect(rect.y).toBeGreaterThanOrEqual(0);
      expect(rect.x + rect.width).toBeLessThanOrEqual(800);
      expect(rect.y + rect.height).toBeLessThanOrEqual(480);
      expect(Math.round((bodyClip.x - rect.x) * 1000) / 1000).toBeLessThanOrEqual(0);
      expect(Math.round((bodyClip.y - rect.y) * 1000) / 1000).toBeLessThanOrEqual(0);
      expect(Math.round((rect.x + rect.width - bodyClip.x - bodyClip.width) * 1000) / 1000).toBeLessThanOrEqual(0);
      expect(Math.round((rect.y + rect.height - bodyClip.y - bodyClip.height) * 1000) / 1000).toBeLessThanOrEqual(0);
      expect(await control.evaluate(el => {
        const b = el.getBoundingClientRect();
        return [.1, .5, .9].every(fraction => el.contains(document.elementFromPoint(b.x + b.width / 2, b.y + b.height * fraction)));
      })).toBe(true);
    }
    await page.screenshot({path: info.outputPath('long-output-recovery-before-scroll.png')});
    await alert.getByRole('button', {name: ro ? 'Încearcă din nou' : 'Try again', exact: true}).tap();
    await expect(alert).toHaveCount(0);
    await expect(quick).toBeVisible();
    await expect(quick.getByRole('button', {name: ro ? 'Toate setările' : 'All settings', exact: true})).toBeVisible();
    expect(writes).toEqual([{output: 'long-output'}, {output: 'long-output'}]);
    expect(state.audio.outputs.find((output: any) => output.id === 'long-output').active).toBe(true);
    await page.screenshot({path: info.outputPath('long-output-retry-retains-quick.png')});
  });
}
