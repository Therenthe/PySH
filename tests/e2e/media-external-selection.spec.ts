import {test,expect} from '@playwright/test';
for(const theme of ['ink','night'])for(const first of ['local','local-audio','external'])for(const result of ['accept','reject'])test(`media opening ownership ${theme} ${first} ${result}`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro');let release!:()=>void,pending=false;const gate=new Promise<void>(r=>release=r),actions:any[]=[];const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,screensaverMinutes:0,nightEnabled:false},network:{},bluetooth:{devices:[],prompts:[]},audio:{ready:true,volume:30,mute:false},player:{state:'idle'},weather:{}};
 await page.route('**/api/**',async route=>{const u=new URL(route.request().url());let json:any={ok:true};if(u.pathname==='/api/session')json={token:'fixture'};else if(u.pathname==='/api/state')json=state;else if(u.pathname==='/api/media')json={path:'/approved',items:[{name:'Film.webm',path:'/approved/Film.webm',kind:'video'},{name:'Music.wav',path:'/approved/Music.wav',kind:'audio'}]};else if(u.pathname==='/api/media/file')return route.fulfill({contentType:'video/webm',body:''});else if(route.request().method()==='POST'){const body=route.request().postDataJSON();actions.push({path:u.pathname,body});if(actions.length===1){pending=true;await gate;if(result==='reject')return route.fulfill({status:409,json:{error:first==='external'?'browser_unavailable':'playback_command_failed'}});}if(u.pathname==='/api/play')state.player={state:'playing',kind:'audio',url:body.path,title:body.title,duration:300,position:1};}await route.fulfill({json});});
 await page.goto('/');await page.locator('.main-nav button').nth(2).tap();await expect(page.locator('.media-item')).toHaveCount(2);
 // Each tab exposes one source. Duplicate first-source clicks still share one event turn;
 // switching the real tab then attempts the competing source while that first request is held.
 const files=()=>page.locator('.media-sections button').nth(0).tap(),services=()=>page.locator('.media-sections button').nth(1).tap();
 if(first==='external')await services();
 const firstControl=first==='external'?page.locator('.service-row').filter({hasText:'Netflix'}):page.locator('.media-item').nth(first==='local'?0:1);
 await firstControl.evaluate((button:HTMLButtonElement)=>{button.click();button.click();});
 await expect.poll(()=>pending).toBe(true);
 await services();await expect(page.locator('.service-row')).toHaveCount(3);
 if(first==='external'){await expect(page.locator('.service-panel')).toHaveAttribute('aria-busy','true');await expect(page.getByRole('status').filter({hasText:ro?'Se deschide serviciul…':'Opening service…'})).toBeVisible();}
 for(const control of await page.locator('.service-row').all()){await expect(control).toBeDisabled();await control.evaluate((button:HTMLButtonElement)=>button.click());}
 await files();await expect(page.locator('.media-item')).toHaveCount(2);
 for(const control of await page.locator('.media-item').all()){await expect(control).toBeDisabled();await control.evaluate((button:HTMLButtonElement)=>button.click());}
 await expect(page.locator('.main-nav button').first()).toBeEnabled();expect(actions).toHaveLength(1);
 expect(actions[0]).toEqual(first==='external'?{path:'/api/external',body:{service:'netflix'}}:first==='local'?{path:'/api/player',body:{action:'stop'}}:{path:'/api/play',body:{source:'local',path:'/approved/Music.wav',title:'Music.wav'}});
 release();await expect(page.locator('.media-item').first()).toBeEnabled();expect(actions).toHaveLength(1);
 if(result==='reject'){await expect(page.locator('.error-strip')).toBeVisible();await page.locator('.error-strip').getByRole('button',{name:ro?'Închide':'Close',exact:true}).tap();}else if(first==='local'){await expect(page.locator('.video-overlay')).toBeVisible();await page.locator('.video-back').tap();}else await expect(page.locator('.video-overlay')).toHaveCount(0);
 await services();await expect(page.locator('.service-row').first()).toBeEnabled();await files();await expect(page.locator('.media-item').first()).toBeEnabled();await page.getByRole('button',{name:'Music.wav',exact:false}).tap();await expect.poll(()=>actions.length).toBe(2);expect(actions[1]).toEqual({path:'/api/play',body:{source:'local',path:'/approved/Music.wav',title:'Music.wav'}});await expect(page.locator('.local-audio-bar')).toBeVisible();
});
