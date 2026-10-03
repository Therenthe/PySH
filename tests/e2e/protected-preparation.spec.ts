import {expect,test,type Page,type TestInfo} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {textLegibility} from './legibility';

// Owned-page browser tests. Fake EME/API replies do not prove DRM or account playback.
async function fixture(page:Page, info:TestInfo, theme:'ink'|'night') {
  const language=info.project.name==='touch-ro'?'ro':'en';
  const f={state:'checking',error:undefined as string|undefined,attempt:'fixture-attempt',reports:[] as any[],cancelled:false,retried:false};
  const directory=new URL('../../services/backend/preparation/',import.meta.url);
  for(const [path,file,type] of [['/service-prepare','index.html','text/html'],['/service-prepare.js','prepare.js','text/javascript'],['/service-prepare.css','prepare.css','text/css']]) {
    await page.route(url=>url.pathname===path,route=>route.fulfill({contentType:type,body:readFileSync(new URL(file,directory),'utf8')}));
  }
  await page.addInitScript(()=>{
    (window as any).probe={ready:false,keys:true,calls:0};
    Object.defineProperty(navigator,'requestMediaKeySystemAccess',{value:async()=>{
      const probe=(window as any).probe;probe.calls++;
      if(!probe.ready)throw new DOMException('Fixture unavailable','NotSupportedError');
      return {createMediaKeys:async()=>{if(!probe.keys)throw new DOMException('Fixture key failure','NotSupportedError');return {};}};
    }});
  });
  await page.route('**/api/**',async route=>{
    const req=route.request(),path=new URL(req.url()).pathname;
    let data:any;
    if(path==='/api/session')data={token:'owned-fixture-token'};
    else {
      if(req.method()==='POST')expect(req.headers()['x-hub-token']).toBe('owned-fixture-token');
      const body=req.method()==='POST'?req.postDataJSON():null;
      if(path==='/api/external/report') {
        expect(Object.keys(body).sort()).toEqual(['attempt','job','ready']);
        f.reports.push(body);f.state=body.ready?'ready':'waiting_component';
      } else if(path==='/api/external/retry') {f.retried=true;f.state='checking';f.error=undefined;}
      else if(path==='/api/external/cancel') {f.cancelled=true;f.state='cancelled';}
      else expect(path).toBe('/api/external/preparation');
      data={state:f.state,service:'netflix',attempt:f.attempt,language,theme,error:f.error,...(f.state==='ready'?{url:'https://www.netflix.com'}:{})};
    }
    await route.fulfill({json:data});
  });
  await page.route('https://www.netflix.com/',route=>route.fulfill({contentType:'text/html',body:'<h1>Owned official-service boundary fixture</h1>'}));
  await page.goto(`/service-prepare?job=fixture-job&attempt=fixture-attempt&lang=${language}&theme=${theme}`);
  return {...f,model:f,language};
}

for(const theme of ['ink','night'] as const) test(`protected preparation ${theme} stays usable while waiting, offline and timed out`,async({page},info)=>{
  const f=await fixture(page,info,theme);
  await expect(page.locator('html')).toHaveAttribute('lang',f.language);
  await expect(page.locator('html')).toHaveAttribute('data-theme',theme);
  await expect(page.getByRole('heading')).toHaveText(f.language==='ro'?'Se pregătește browserul…':'Preparing this browser…');
  await expect(page.locator('#retry')).toBeHidden();
  expect(f.model.reports).toEqual([{job:'fixture-job',attempt:'fixture-attempt',ready:false}]);
  await page.evaluate(()=>Object.defineProperty(navigator,'onLine',{value:false,configurable:true}));
  await expect(page.locator('#notice')).toContainText(f.language==='ro'?'Nu există conexiune':'no network connection');
  f.model.state='error';f.model.error='protected_playback_timeout';
  await page.evaluate(()=>Object.defineProperty(navigator,'onLine',{value:true,configurable:true}));
  await expect(page.locator('#notice')).toContainText(f.language==='ro'?'durează mai mult':'taking longer');
  await expect(page.locator('#retry')).toBeVisible();
  await page.evaluate(()=>document.fonts.ready);
  expect(await textLegibility(page)).toEqual([]);
  const geometry=await page.evaluate(()=>({scroll:document.querySelector('main')!.scrollHeight,
    height:document.querySelector('main')!.clientHeight,buttons:[...document.querySelectorAll('button')].map(x=>({width:x.offsetWidth,height:x.offsetHeight,bottom:x.getBoundingClientRect().bottom}))}));
  expect(geometry.scroll).toBe(geometry.height);
  for(const button of geometry.buttons){expect(button.width).toBeGreaterThanOrEqual(48);expect(button.height).toBeGreaterThanOrEqual(48);expect(button.bottom).toBeLessThanOrEqual(480);}
  await page.screenshot({path:`.runtime/preparation-${f.language}-${theme}-timeout.png`});
  await page.getByRole('button',{name:f.language==='ro'?'Revino în hub':'Back to hub'}).tap();
  await expect.poll(()=>f.model.cancelled).toBe(true);
});

test('retry opens the official service only after EME access and key creation',async({page},info)=>{
  const f=await fixture(page,info,'ink');
  await expect(page.getByRole('heading')).toHaveText(f.language==='ro'?'Se pregătește browserul…':'Preparing this browser…');
  f.model.state='error';f.model.error='protected_playback_timeout';
  await expect(page.locator('#retry')).toBeVisible();
  await page.evaluate(()=>{(window as any).probe.ready=true;});
  await page.locator('#retry').tap();
  await expect(page).toHaveURL('https://www.netflix.com/');
  expect(f.model.retried).toBe(true);
  expect(f.model.reports.map(x=>x.ready)).toEqual([false,true]);
});

test('failed key creation and a stale attempt never open the official service',async({page},info)=>{
  const f=await fixture(page,info,'night');
  await expect(page.getByRole('heading')).toHaveText(f.language==='ro'?'Se pregătește browserul…':'Preparing this browser…');
  f.model.state='error';f.model.error='protected_playback_timeout';
  await expect(page.locator('#retry')).toBeVisible();
  await page.evaluate(()=>{(window as any).probe.ready=true;(window as any).probe.keys=false;});
  await page.locator('#retry').tap();
  await expect.poll(()=>f.model.reports.length).toBe(2);
  expect(f.model.reports[1].ready).toBe(false);
  f.model.state='checking';f.model.attempt='restarted-attempt';
  await page.waitForTimeout(1400);
  expect(f.model.reports.length).toBe(2);
  expect(page.url()).toContain('/service-prepare?');
});
