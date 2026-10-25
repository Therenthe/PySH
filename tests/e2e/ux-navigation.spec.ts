import {expect, test, type Page, type TestInfo} from '@playwright/test';

// Charter: prove that common settings have a single predictable home, that a
// user can return to the task they interrupted, and that polling/write errors
// do not erase navigation. Deterministic browser fixtures only; no Pi, account,
// audio-device or network mutation is performed by this suite.
const groups = {
  home: ['home', 'visualizer', 'ambient'],
  display: ['appearance', 'rest', 'power'],
  sound: ['audio', 'bluetooth'],
  connections: ['network', 'androidControl'],
  regional: ['general', 'weather'],
  system: ['diagnostics'],
} as const;
type Group = keyof typeof groups;
type Section = typeof groups[Group][number];

async function fixture(page: Page, language: 'en' | 'ro', theme: 'ink' | 'night') {
  const writes: Record<string, unknown>[] = [];
  const other: {path: string; body: unknown}[] = [];
  const failKeys = new Set<string>();
  const state: any = {
    preferences: {
      language, theme, accent: 'sage', setupComplete: true, nightEnabled: false,
      nightMode: 'solar', nightStart: '22:00', nightEnd: '07:00',
      screensaverMinutes: 0, screensaverLayout: 'clock', visualizerStyle: 'wave',
      visualizerSize: 'compact', timezone: 'Europe/Bucharest',
      location: {name: 'București · Sector 5', latitude: 44.4, longitude: 26.07},
      homeCards: ['weather', 'forecast', 'playback'], shortcuts: ['radio', 'media'],
      navigationCollapsed: false, navigationAutoHide: false,
      decorativeAircraft: true, decorativeLunarDust: false,
      screenBrightness: 80, dailyStandbyEnabled: false, dailyStandbyTime: '23:00',
      favorites: [],
    },
    network: {available: true, state: 'connected', connection: 'Fixture Ethernet'},
    bluetooth: {
      available: true, powered: true, prompts: [],
      devices: [{address: 'AA:BB:CC:DD:EE:FF', name: 'Fixture speaker', paired: true, trusted: true, connected: true}],
    },
    audio: {
      available: true, ready: true, volume: 40, mute: false,
      outputs: [{id: 'fixture-speaker', description: 'Fixture speaker', active: true, bluetooth: true}],
    },
    player: {kind: 'radio', state: 'playing', station_name: 'Fixture Radio', url: 'https://example.org/radio', title: 'Retained song'},
    weather: {stale: false, current: {temperature_c: 13, weather_code: 2, is_day: 1}, daily: []},
    power: {standby: false, brightness: {available: true, value: 80}, timer: {remainingSeconds: 0}, daily: {enabled: false, time: '23:00'}},
    androidControl: {available: true, enabled: true, pending: [], devices: []},
  };
  await page.clock.install({time: new Date('2026-10-24T12:00:00Z')});
  await page.route('**/api/**', async route => {
    const request = route.request(), path = new URL(request.url()).pathname;
    let json: any = {ok: true};
    if (path === '/api/session') json = {token: 'fixture-only'};
    else if (path === '/api/state') json = state;
    else if (path === '/api/preferences' && request.method() === 'PATCH') {
      const body = request.postDataJSON();
      writes.push(body);
      if (Object.keys(body).some(key => failKeys.has(key))) {
        await route.fulfill({status: 503, json: {error: 'preferences_unavailable'}});
        return;
      }
      Object.assign(state.preferences, body);
      json = state.preferences;
    } else if (path === '/api/radio') json = {stations: []};
    else if (path === '/api/media') json = {path: '/library', parent: null, items: [], roots: ['/library']};
    else if (path === '/api/audio/visualization') json = {available: true, status: 'ready', waveform: Array(64).fill(.1), bars: Array(16).fill(.1), rms: .1, peak: .1};
    else if (request.method() !== 'GET') other.push({path, body: request.postData() ? request.postDataJSON() : null});
    await route.fulfill({json});
  });
  await page.goto('/');
  await expect(page.locator('.ambient-home')).toBeVisible();
  return {state, writes, other, failKeys};
}

async function openSettings(page: Page, ro: boolean) {
  await page.locator('.topbar-right').getByRole('button', {name: ro ? 'Deschide setările' : 'Open settings', exact: true}).tap();
  await expect(page.locator('.settings-page')).toBeVisible();
  await expect(page.locator('.modal-card')).toHaveCount(0);
}

async function openSection(page: Page, section: Section) {
  const group = (Object.keys(groups) as Group[]).find(id => (groups[id] as readonly string[]).includes(section))!;
  await page.locator(`.settings-tabs [data-settings-group="${group}"]`).tap();
  if (groups[group].length > 1) await page.locator(`.settings-subtabs [data-settings-section="${section}"]`).tap();
  await expect(page.locator(`.settings-tabs [data-settings-group="${group}"]`)).toHaveClass(/active/);
  if (groups[group].length > 1) await expect(page.locator(`.settings-subtabs [data-settings-section="${section}"]`)).toHaveClass(/active/);
  await expect(page.locator('.settings-panel')).toBeVisible();
}

async function capture(page: Page, info: TestInfo, label: string) {
  await page.screenshot({path: info.outputPath(`${label}.png`), animations: 'disabled'});
}

for (const theme of ['ink', 'night'] as const) {
  test(`UX gear opens complete settings directly ${theme}`, async ({page}, info) => {
    const ro = info.project.name.endsWith('ro');
    const f = await fixture(page, ro ? 'ro' : 'en', theme);
    await openSettings(page, ro);
    await expect(page.locator('.settings-tabs [data-settings-group]')).toHaveCount(6);
    await expect(page.locator('.settings-tabs .exit-tab')).toHaveCount(0);
    expect(f.writes).toHaveLength(0);
    expect(f.other).toHaveLength(0);
    await capture(page, info, 'direct-settings');
  });

  test(`UX canonical settings inventory stays reachable at 800x480 ${theme}`, async ({page}, info) => {
    const ro = info.project.name.endsWith('ro');
    await fixture(page, ro ? 'ro' : 'en', theme);
    await openSettings(page, ro);
    const reached: Section[] = [];
    const canonical: Record<string, {section: Section; name: string; observed: Section[]}> = {
      style: {section: 'visualizer', name: ro ? 'Vizualizare audio' : 'Audio visualization', observed: []},
      size: {section: 'visualizer', name: ro ? 'Dimensiune vizualizator' : 'Visualizer size', observed: []},
      timer: {section: 'rest', name: ro ? 'Ceas de repaus' : 'Clock screensaver', observed: []},
      restLayout: {section: 'rest', name: ro ? 'Aspect repaus' : 'Screensaver layout', observed: []},
      navigation: {section: 'home', name: ro ? 'Retrage după navigare' : 'Hide after navigation', observed: []},
      aircraft: {section: 'ambient', name: ro ? 'Aeronave decorative' : 'Decorative aircraft', observed: []},
      dust: {section: 'ambient', name: ro ? 'Praf lunar decorativ' : 'Decorative lunar dust', observed: []},
      setup: {section: 'diagnostics', name: ro ? 'Reia configurarea' : 'Run setup again', observed: []},
    };
    for (const [group, sections] of Object.entries(groups) as [Group, readonly Section[]][]) {
      await page.locator(`.settings-tabs [data-settings-group="${group}"]`).tap();
      const subtabs = page.locator('.settings-subtabs [data-settings-section]');
      await expect(subtabs).toHaveCount(sections.length === 1 ? 0 : sections.length);
      for (const section of sections) {
        await openSection(page, section);
        reached.push(section);
        await expect(page.locator('.settings-panel h2').first()).toBeVisible();
        for (const entry of Object.values(canonical)) {
          const controls = page.locator('.settings-panel').getByRole('button', {name: entry.name, exact: true});
          for (let count = await controls.count(); count > 0; count--) entry.observed.push(section);
        }
        expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
        const nav = await page.locator('.settings-tabs [data-settings-group]').evaluateAll(elements => elements.map(el => {
          const b = el.getBoundingClientRect();
          return {width: b.width, height: b.height, left: b.left, right: b.right, top: b.top, bottom: b.bottom};
        }));
        for (const rect of nav) {
          expect(Math.round(rect.width * 1000) / 1000).toBeGreaterThanOrEqual(48);
          expect(Math.round(rect.height * 1000) / 1000).toBeGreaterThanOrEqual(48);
          expect(rect.left).toBeGreaterThanOrEqual(0);
          expect(rect.right).toBeLessThanOrEqual(800);
          expect(rect.top).toBeGreaterThanOrEqual(0);
          expect(rect.bottom).toBeLessThanOrEqual(480);
        }
        await capture(page, info, `section-${group}-${section}`);
      }
    }
    expect(new Set(reached).size).toBe(13);
    for (const [name, entry] of Object.entries(canonical)) expect(entry.observed, name).toEqual([entry.section]);
  });

  test(`UX preferences live in the corresponding task and persist ${theme}`, async ({page}, info) => {
    const ro = info.project.name.endsWith('ro');
    const f = await fixture(page, ro ? 'ro' : 'en', theme);
    await openSettings(page, ro);
    await openSection(page, 'appearance');
    await expect(page.locator('.theme-options')).toBeVisible();
    await expect(page.locator('.settings-panel').getByRole('button', {name: ro ? 'Vizualizare audio' : 'Audio visualization', exact: true})).toHaveCount(0);
    await expect(page.locator('.settings-panel').getByRole('group', {name: ro ? 'Alege limba' : 'Choose your language', exact: true})).toHaveCount(0);
    await expect(page.locator('.settings-panel').getByRole('button', {name: ro ? 'Ceas de repaus' : 'Clock screensaver', exact: true})).toHaveCount(0);
    await openSection(page, 'visualizer');
    const size = page.locator('.settings-panel').getByRole('button', {name: ro ? 'Dimensiune vizualizator' : 'Visualizer size', exact: true});
    await size.tap();
    await page.getByRole('radio', {name: ro ? 'Echilibrat' : 'Balanced', exact: true}).tap();
    await expect(size).toContainText(ro ? 'Echilibrat' : 'Balanced');
    expect(f.state.preferences.visualizerSize).toBe('balanced');
    await openSection(page, 'home');
    await expect(page.locator('.settings-panel').getByRole('button', {name: ro ? 'Retrage după navigare' : 'Hide after navigation', exact: true})).toBeAttached();
    await openSection(page, 'rest');
    const timer = page.locator('.settings-panel').getByRole('button', {name: ro ? 'Ceas de repaus' : 'Clock screensaver', exact: true});
    await timer.tap();
    await page.getByRole('radio', {name: ro ? '10 minute' : '10 minutes', exact: true}).tap();
    expect(f.state.preferences.screensaverMinutes).toBe(10);
    await capture(page, info, 'rest-timer-saved');
    await openSection(page, 'general');
    await expect(page.locator('.settings-panel').getByRole('group', {name: ro ? 'Alege limba' : 'Choose your language', exact: true})).toBeVisible();
    await expect(page.locator('.settings-panel').getByRole('button', {name: 'Europe/Bucharest', exact: true})).toBeVisible();
    await page.reload();
    await openSettings(page, ro);
    await openSection(page, 'visualizer');
    await expect(size).toContainText(ro ? 'Echilibrat' : 'Balanced');
    await openSection(page, 'rest');
    await expect(timer).toContainText(ro ? '10 minute' : '10 minutes');
    expect(f.other).toHaveLength(0);
  });

  test(`UX settings returns to the task interrupted by the user ${theme}`, async ({page}, info) => {
    const ro = info.project.name.endsWith('ro');
    await fixture(page, ro ? 'ro' : 'en', theme);
    for (const [index, target] of [[1, '.radio-page'], [2, '.media-page']] as const) {
      await page.locator('.main-nav button').nth(index).tap();
      await expect(page.locator(target)).toBeVisible();
      await openSettings(page, ro);
      await openSection(page, 'weather');
      await page.locator('.settings-back').tap();
      await expect(page.locator(target)).toBeVisible();
      await expect(page.locator('.settings-page')).toHaveCount(0);
      await capture(page, info, `returned-${index}`);
    }
  });

  test(`UX quick controls clearly lead to complete settings ${theme}`, async ({page}, info) => {
    const ro = info.project.name.endsWith('ro');
    await fixture(page, ro ? 'ro' : 'en', theme);
    await openSettings(page, ro);
    await page.locator('.settings-quick-control').tap();
    await expect(page.locator('.quick-modal')).toBeVisible();
    await capture(page, info, 'quick-controls');
    await page.locator('.modal-card').getByRole('button', {name: ro ? 'Toate setările' : 'All settings', exact: true}).tap();
    await expect(page.locator('.modal-card')).toHaveCount(0);
    await expect(page.locator('.settings-page')).toBeVisible();
    await expect(page.locator('.settings-tabs [data-settings-group]')).toHaveCount(6);
    await capture(page, info, 'quick-to-full');
  });

  test(`UX volume and quick controls are one tap away from the current task ${theme}`, async ({page}, info) => {
    const ro = info.project.name.endsWith('ro');
    const f = await fixture(page, ro ? 'ro' : 'en', theme);
    await page.locator('.main-nav button').nth(1).tap();
    await page.locator('.quick-controls-button').tap();
    await expect(page.locator('.quick-modal')).toBeVisible();
    await expect(page.locator('.settings-page')).toHaveCount(0);
    await expect(page.locator('.quick-modal').getByRole('slider', {name: ro ? 'Volum' : 'Volume', exact: true})).toBeVisible();
    await expect(page.locator('.quick-playback')).toContainText('Fixture Radio');
    await capture(page, info, 'one-tap-quick-controls');
    await page.locator('.modal-card header').getByRole('button', {name: ro ? 'Închide' : 'Close', exact: true}).tap();
    await expect(page.locator('.radio-page')).toBeVisible();
    expect(f.other).toHaveLength(0);
  });

  test(`UX connected speaker has an explicit path to audio output ${theme}`, async ({page}, info) => {
    const ro = info.project.name.endsWith('ro');
    const f = await fixture(page, ro ? 'ro' : 'en', theme);
    await openSettings(page, ro);
    await openSection(page, 'bluetooth');
    await expect(page.locator('.settings-panel')).toContainText('Fixture speaker');
    await capture(page, info, 'bluetooth-speaker');
    await page.locator('.settings-panel .settings-context-link').tap();
    await expect(page.locator('.settings-subtabs [data-settings-section="audio"]')).toHaveClass(/active/);
    await expect(page.locator('.settings-panel .output-row')).toContainText('Fixture speaker');
    await expect(page.locator('.settings-panel').getByRole('slider', {name: ro ? 'Volum' : 'Volume', exact: true})).toBeVisible();
    expect(f.other).toHaveLength(0);
    await capture(page, info, 'speaker-audio-output');
  });

  test(`UX polling retains navigation and section changes start at the top ${theme}`, async ({page}, info) => {
    const ro = info.project.name.endsWith('ro');
    await fixture(page, ro ? 'ro' : 'en', theme);
    await openSettings(page, ro);
    await openSection(page, 'home');
    const panel = page.locator('.settings-panel');
    await panel.evaluate(el => el.scrollTop = 100);
    expect(await panel.evaluate(el => el.scrollTop)).toBe(100);
    await page.clock.runFor(6200);
    await expect(page.locator('.settings-tabs [data-settings-group="home"]')).toHaveClass(/active/);
    expect(await panel.evaluate(el => el.scrollTop)).toBe(100);
    await openSection(page, 'general');
    expect(await panel.evaluate(el => el.scrollTop)).toBe(0);
    await page.clock.runFor(6200);
    await expect(page.locator('.settings-subtabs [data-settings-section="general"]')).toHaveClass(/active/);
    await capture(page, info, 'regional-after-poll');
  });

  test(`UX failed preference save keeps a recoverable settings path ${theme}`, async ({page}, info) => {
    const ro = info.project.name.endsWith('ro');
    const f = await fixture(page, ro ? 'ro' : 'en', theme);
    await openSettings(page, ro);
    await openSection(page, 'home');
    const toggle = page.locator('.settings-panel').getByRole('button', {name: ro ? 'Retrage după navigare' : 'Hide after navigation', exact: true});
    f.failKeys.add('navigationAutoHide');
    await toggle.tap();
    await expect(page.locator('.error-strip')).toBeVisible();
    expect(f.state.preferences.navigationAutoHide).toBe(false);
    await capture(page, info, 'rejected-save');
    await openSection(page, 'general');
    await expect(page.locator('.settings-panel').getByRole('group', {name: ro ? 'Alege limba' : 'Choose your language', exact: true})).toBeVisible();
    f.failKeys.clear();
    await openSection(page, 'home');
    await toggle.tap();
    expect(f.state.preferences.navigationAutoHide).toBe(true);
    await expect(toggle).toHaveAttribute('aria-pressed', 'true');
    await capture(page, info, 'save-recovered');
  });

  test(`UX Radio clears text filters with one deliberate action ${theme}`, async ({page}, info) => {
    const ro = info.project.name.endsWith('ro');
    const f = await fixture(page, ro ? 'ro' : 'en', theme);
    const queries: URL[] = [];
    await page.route('**/api/radio?**', async route => {
      queries.push(new URL(route.request().url()));
      await route.fulfill({json: {stations: []}});
    });
    await page.locator('.main-nav button').nth(1).tap();
    for (const [selector, value] of [['.search-field', 'jazz'], ['.filter-button:first-child', 'romania']] as const) {
      await page.locator(`.radio-toolbar ${selector}`).tap();
      for (const letter of value) await page.locator('.keyboard-card .keys').getByRole('button', {name: letter, exact: true}).tap();
      await page.locator('.final-row').getByRole('button', {name: ro ? 'Aplică' : 'Apply', exact: true}).tap();
    }
    await expect(page.locator('.radio-clear-filters')).toBeVisible();
    await capture(page, info, 'radio-active-filters');
    await page.locator('.radio-clear-filters').tap();
    await expect(page.locator('.radio-clear-filters')).toHaveCount(0);
    await expect(page.locator('.radio-toolbar .search-field')).toContainText(ro ? 'Caută un post' : 'Find a station');
    await expect(page.locator('.radio-filter-pills .filter-button').first()).toContainText(ro ? 'Țară' : 'Country');
    await expect.poll(() => queries.at(-1)?.searchParams.get('q') || '').toBe('');
    expect(queries.at(-1)?.searchParams.get('country') || '').toBe('');
    expect(f.writes).toHaveLength(0);
    expect(f.other).toHaveLength(0);
    await capture(page, info, 'radio-filters-cleared');
  });

  test(`UX Radio without audio routes to speaker settings and returns ${theme}`, async ({page}, info) => {
    const ro = info.project.name.endsWith('ro');
    const f = await fixture(page, ro ? 'ro' : 'en', theme);
    f.state.audio.ready = false;
    f.state.audio.outputs = [];
    f.state.player.state = 'idle';
    await page.clock.runFor(2600);
    await page.locator('.main-nav button').nth(1).tap();
    const choose = page.getByRole('button', {name: ro ? 'Alege boxa' : 'Choose speaker', exact: true});
    await expect(choose).toBeVisible();
    const rect = await choose.boundingBox();
    expect(rect!.height).toBeGreaterThanOrEqual(48);
    expect(rect!.y).toBeGreaterThanOrEqual(0);
    expect(rect!.y + rect!.height).toBeLessThanOrEqual(480);
    expect(await choose.evaluate(el => {
      const b = el.getBoundingClientRect();
      return el.contains(document.elementFromPoint(b.x + b.width / 2, b.y + b.height / 2));
    })).toBe(true);
    await choose.tap();
    await expect(page.locator('.settings-panel')).toHaveAttribute('data-settings-section', 'audio');
    await expect(page.locator('.settings-panel .bluetooth-setup-link')).toBeVisible();
    await page.locator('.settings-panel .bluetooth-setup-link').tap();
    await expect(page.locator('.settings-panel')).toHaveAttribute('data-settings-section', 'bluetooth');
    await capture(page, info, 'radio-to-speaker-setup');
    await page.locator('.settings-back').tap();
    await expect(page.locator('.radio-page')).toBeVisible();
    expect(f.other).toHaveLength(0);
    await capture(page, info, 'speaker-settings-return-to-radio');
  });

  test(`UX keyboard clears a whole search and respects cancel ${theme}`, async ({page}, info) => {
    const ro = info.project.name.endsWith('ro');
    await fixture(page, ro ? 'ro' : 'en', theme);
    await page.locator('.main-nav button').nth(1).tap();
    const search = page.locator('.radio-toolbar .search-field');
    await search.tap();
    const clear = page.getByRole('button', {name: ro ? 'Șterge tot textul' : 'Clear all text', exact: true});
    await expect(clear).toBeDisabled();
    for (const letter of 'jazz') await page.locator('.keyboard-card .keys').getByRole('button', {name: letter, exact: true}).tap();
    await page.locator('.final-row').getByRole('button', {name: ro ? 'Aplică' : 'Apply', exact: true}).tap();
    await expect(search).toContainText('jazz');
    await search.tap();
    await expect(clear).toBeEnabled();
    await clear.tap();
    await expect(clear).toBeDisabled();
    await capture(page, info, 'keyboard-cleared');
    await page.locator('.keyboard-card header').getByRole('button', {name: ro ? 'Închide' : 'Close', exact: true}).tap();
    await expect(search).toContainText('jazz');
    await search.tap();
    await clear.tap();
    await page.locator('.final-row').getByRole('button', {name: ro ? 'Aplică' : 'Apply', exact: true}).tap();
    await expect(search).toContainText(ro ? 'Caută un post' : 'Find a station');
    await expect(page.locator('.radio-clear-filters')).toHaveCount(0);
    await capture(page, info, 'keyboard-clear-applied');
  });
}
