import {test,expect} from '@playwright/test';
for(const theme of ['ink','night'])for(const reduced of [false,true]){
 test(`metadata ${theme} reduced=${reduced}: readable long title without duplicate transport`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro'),station='Radio România Actualități · Un nume complet de post foarte lung',title='Artist cu diacritice — O piesă cu titlu foarte lung care trebuie să poată fi citit integral';
  const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,screensaverMinutes:0,timezone:'Europe/Bucharest',favorites:[],shortcuts:['radio','media']},network:{state:'connected'},bluetooth:{devices:[],prompts:[]},audio:{ready:true,volume:20,mute:false},player:{kind:'radio',state:'playing',station_name:station,title,url:'https://example.com/radio'},weather:{}};
  await page.emulateMedia({reducedMotion:reduced?'reduce':'no-preference'});
  await page.route('**/api/**',async route=>{const path=new URL(route.request().url()).pathname;let json:any=path==='/api/session'?{token:'browser-only'}:path==='/api/state'?state:{stations:[]};if(path==='/api/player'){state.player.state='paused';json={ok:true}}await route.fulfill({json})});
  await page.goto('/');const text=page.locator('.playback-metadata .marquee-text');await expect(text).toHaveText(title);await expect(text).toHaveClass(/marquee-moving/);
  const css=await text.locator('.marquee-content').evaluate(el=>({animation:getComputedStyle(el).animationName,offset:parseFloat(getComputedStyle(el.parentElement!).getPropertyValue('--marquee-offset'))}));expect(css.offset).toBeLessThan(0);expect(css.animation).toBe(reduced?'none':'metadata-read');
  if(reduced){await text.evaluate(el=>el.scrollLeft=el.scrollWidth);expect(await text.evaluate(el=>el.scrollLeft)).toBeGreaterThan(0)}
  const dock=page.locator('.ambient-dock');expect(await dock.evaluate(el=>el.scrollWidth<=el.clientWidth+1&&el.scrollHeight<=el.clientHeight+1)).toBe(true);
  await page.getByRole('button',{name:ro?'Pauză':'Pause',exact:true}).tap();await expect(text).not.toHaveClass(/marquee-moving/);await expect(text.locator('.marquee-content')).toHaveCSS('animation-name','none');
  await page.locator('.main-nav button').nth(1).tap();await expect(page.locator('.radio-station-name')).toHaveText(station);await expect(page.locator('.radio-track-name')).toHaveText(title);await expect(page.locator('.now-bar')).toHaveCount(0);
  await page.screenshot({path:info.outputPath(`metadata-${theme}-${reduced}.png`)});
 });
}
