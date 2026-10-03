import {test,expect} from '@playwright/test';
import {textLegibility} from './legibility';
for(const theme of ['ink','night'])for(const style of ['wave','bars','orbit','ribbon','mirror','rings']){
 test(`real output visualizer ${theme} ${style}: signal, pause, station controls and saver`,async({page},info)=>{
  const ro=info.project.name.endsWith('ro');
  const stations=[{uuid:'one',name:'Radio One',url:'https://example.com/one'},{uuid:'two',name:'Radio Two',url:'https://example.com/two'}];
  const state:any={preferences:{language:ro?'ro':'en',theme,setupComplete:true,screensaverMinutes:1,visualizerStyle:style,timezone:'Europe/Bucharest',favorites:stations,shortcuts:['radio','media']},network:{state:'connected'},bluetooth:{devices:[],prompts:[]},audio:{ready:true,volume:20,mute:false,outputs:[]},player:{state:'playing',kind:'radio',station_name:'Radio One',title:'Artist · Song',url:stations[0].url},weather:{}};
  const actions:any[]=[];let signalValid=true;
  await page.route('**/api/**',async route=>{
   const request=route.request(),path=new URL(request.url()).pathname,body=request.method()==='GET'?{}:request.postDataJSON();let json:any={ok:true};
   if(path==='/api/session')json={token:'browser-only'};
   else if(path==='/api/state')json=state;
   else if(path==='/api/radio')json={stations};
   else if(path==='/api/audio/visualization')json=signalValid?{available:true,status:'ready',waveform:Array.from({length:64},(_,i)=>Math.sin(i)*.5),bars:Array(16).fill(.3),peak:.5,rms:.3,silent:false}:{available:true,waveform:[]};
   else {actions.push({path,body});if(path==='/api/player')state.player.state=body.action==='pause'?'paused':'playing';if(path==='/api/play')state.player={state:'playing',kind:'radio',station_name:body.title,title:'New song',url:body.url};if(path==='/api/audio')Object.assign(state.audio,body);}
   await route.fulfill({json});
  });
  await page.clock.install();await page.goto('/');
  await expect(page.locator('.audio-visualizer svg')).toBeVisible();
  if(style==='wave')expect(await page.locator('.audio-visualizer svg').evaluate(svg=>svg.querySelector('path')!.getBoundingClientRect().width/svg.getBoundingClientRect().width)).toBeGreaterThan(.95);
  signalValid=false;await page.clock.runFor(1200);await expect(page.locator('.audio-visualizer')).toContainText(ro?'indisponibil':'unavailable');
  signalValid=true;await page.clock.runFor(1200);await expect(page.locator('.audio-visualizer svg')).toBeVisible();
  await page.locator('.main-nav button').nth(1).tap();
  await expect(page.locator('.radio-station-name')).toHaveText('Radio One');
  await expect(page.locator('.radio-track-name')).toHaveText('Artist · Song');
  await page.getByRole('button',{name:ro?'Postul următor':'Next station',exact:true}).tap();
  expect(actions.at(-1)).toEqual({path:'/api/play',body:{source:'radio',url:stations[1].url,title:'Radio Two'}});
  await page.locator('.radio-filter-pills .favorites-filter').tap();await expect(page.locator('.radio-favorites .station-row')).toHaveCount(2);
  await page.getByRole('button',{name:ro?'Fără sunet':'Mute',exact:true}).tap();await expect(page.locator('.radio-side .audio-visualizer svg')).toHaveCount(0);
  await page.getByRole('button',{name:ro?'Activează sunetul':'Unmute',exact:true}).tap();
  await page.clock.fastForward(61000);await expect(page.locator('.saver-visualizer')).toBeVisible();await page.clock.runFor(1200);
  await expect(page.locator('.saver-visualizer svg')).toBeVisible();
  const bad=await page.locator('.pysh-screensaver button,.pysh-screensaver svg').evaluateAll(elements=>elements.filter(el=>{const r=el.getBoundingClientRect();return r.right>800||r.bottom>480||r.left<0||r.top<0}).map(el=>el.className.toString()));expect(bad).toEqual([]);
  expect(await textLegibility(page)).toEqual([]);
  await page.screenshot({path:info.outputPath(`signal-${theme}-${style}.png`)});
 });
}
