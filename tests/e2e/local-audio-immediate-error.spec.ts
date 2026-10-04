import {test,expect} from '@playwright/test';

for(const theme of ['ink','night'])test(`immediate decoder failure keeps exact local recovery ${theme}`,async({page},info)=>{
 const ro=info.project.name.endsWith('ro'),path='/approved/invalid.mp3',attempts:any[]=[];
 const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,screensaverMinutes:0,nightEnabled:false},network:{},bluetooth:{devices:[],prompts:[]},audio:{ready:true,volume:30,mute:false},player:{state:'idle'},weather:{}};
 await page.route('**/api/**',async route=>{
  const endpoint=new URL(route.request().url()).pathname;let json:any={ok:true};
  if(endpoint==='/api/session')json={token:'fixture'};
  else if(endpoint==='/api/state')json=state;
  else if(endpoint==='/api/media')json={path:'/approved',items:[{name:'invalid.mp3',path,kind:'audio'},{name:'Healthy.wav',path:'/approved/Healthy.wav',kind:'audio'}]};
  else if(endpoint==='/api/play'){
   const body=route.request().postDataJSON();attempts.push(body);
   if(attempts.length===3)return route.fulfill({status:409,json:{error:'media_not_found'}});
   state.player=body.path===path?{state:'error',kind:'audio',url:path,title:'invalid.mp3',error:'stream_failed'}:{state:'playing',kind:'audio',url:body.path,title:body.title,position:1,duration:20};
   json=state.player;
  }
  await route.fulfill({json});
 });
 await page.goto('/');await page.locator('.main-nav button').nth(2).tap();await page.getByRole('button',{name:'invalid.mp3',exact:false}).tap();
 const notice=page.locator('.local-audio-recovery');await expect(notice).toContainText(ro?'Acest fișier nu a putut fi redat.':'This file could not be played.');await expect(page.locator('.error-strip')).toHaveCount(0);
 await notice.getByRole('button',{name:ro?'Reia redarea':'Replay',exact:true}).tap();await expect.poll(()=>attempts.length).toBe(2);expect(attempts[1]).toEqual(attempts[0]);await expect(notice).toBeVisible();await expect(page.locator('.error-strip')).toHaveCount(0);
 await page.screenshot({path:info.outputPath('immediate-decoder-error.png')});
 await notice.getByRole('button').tap();await expect(page.locator('.error-strip')).toContainText(ro?'Fișierul sau dosarul media nu este disponibil.':'This media file or folder is unavailable.');await expect(notice).toHaveCount(0);
 await page.locator('.error-strip').getByRole('button',{name:ro?'Încearcă din nou':'Try again',exact:true}).tap();await expect.poll(()=>attempts.length).toBe(4);expect(attempts[3]).toEqual(attempts[0]);await expect(notice).toBeVisible();await expect(page.locator('.error-strip')).toHaveCount(0);
 await page.getByRole('button',{name:'Healthy.wav',exact:false}).tap();await expect(notice).toHaveCount(0);await expect(page.locator('.error-strip')).toHaveCount(0);expect(state.player.state).toBe('playing');
});
