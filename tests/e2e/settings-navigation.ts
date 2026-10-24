import {expect, type Page} from '@playwright/test';

const groups: Record<string, string[]> = {
  home: ['home', 'visualizer', 'ambient'],
  display: ['appearance', 'rest', 'power'],
  sound: ['audio', 'bluetooth'],
  connections: ['network', 'androidControl'],
  regional: ['general', 'weather'],
  system: ['diagnostics'],
};

export async function openSettingsSection(page: Page, section: string) {
  const group = Object.keys(groups).find(key => groups[key].includes(section));
  if (!group) throw new Error(`Unknown settings destination: ${section}`);
  await page.locator(`.settings-tabs [data-settings-group="${group}"]`).tap();
  if (groups[group].length > 1) await page.locator(`.settings-subtabs [data-settings-section="${section}"]`).tap();
  await expect(page.locator('.settings-panel')).toHaveAttribute('data-settings-section', section);
}

export async function openQuickControls(page: Page) {
  await page.locator('.quick-controls-button').tap();
  await expect(page.locator('.quick-modal')).toBeVisible();
}
