import {test,expect,type Page} from '@playwright/test';

// Isolated production component fixture: does not assert Home phase integration.
async function mount(page:Page,start='2026-10-04T12:59:59Z',enabled=true,timezone='UTC'){
 await page.route('**/api/**',route=>route.fulfill({json:{preferences:{language:'en',theme:'night',setupComplete:true,nightEnabled:false,screensaverMinutes:0,timezone:'UTC',favorites:[],shortcuts:[]},network:{available:false,devices:[],saved:[]},bluetooth:{available:false,devices:[],prompts:[]},audio:{available:false,outputs:[]},player:{state:'idle'},weather:{}}}));
 await page.clock.install({time:new Date(start)});
 await page.goto('/');
 await page.evaluate(async({start,enabled,timezone})=>{
  const source=await (await fetch('/src/HeartConfetti.tsx')).text();const main=await (await fetch('/src/main.tsx')).text();
  const ReactModule=await import(source.match(/from "([^"]*\/react\.js[^"]*)"/)![1]);const React=ReactModule.default||ReactModule;
  const rootModule=await import(main.match(/from "([^"]*\/react-dom_client\.js[^"]*)"/)![1]);const {createRoot}=rootModule.default||rootModule;
  const {HeartConfetti}=await import('/src/HeartConfetti.tsx');
  const fixture=document.createElement('div');fixture.id='heart-fixture';fixture.style.cssText='position:fixed;inset:0;z-index:9999;background:#172530';document.body.appendChild(fixture);
  function Harness(){const [model,setModel]=React.useState({now:new Date(start),enabled,timezone});const [clicks,setClicks]=React.useState(0);(window as any).heartFixture={set:(update:any)=>setModel((m:any)=>({...m,...update,...(update.now?{now:new Date(update.now)}:{})})),clicks};return React.createElement(React.Fragment,null,React.createElement('button',{id:'heart-touch-probe',style:{position:'absolute',left:320,top:220,width:64,height:64},onClick:()=>setClicks((n:number)=>n+1)},'Touch'),React.createElement(HeartConfetti,model))}
  createRoot(fixture).render(React.createElement(Harness));
 },{start,enabled,timezone});
 await expect(page.locator('#heart-touch-probe')).toBeVisible();
}
async function set(page:Page,update:Record<string,unknown>){await page.evaluate(update=>(window as any).heartFixture.set(update),update)}

test('whole-hour and repeated-digit boundaries trigger, disappear within five seconds and retain touch',async({page})=>{
 await mount(page);
 await set(page,{now:'2026-10-04T13:00:00Z'});
 await expect(page.getByTestId('heart-confetti')).toBeVisible();
 const count=await page.locator('.confetti-heart').count();expect(count).toBeGreaterThanOrEqual(14);expect(count).toBeLessThanOrEqual(20);
 await expect(page.getByTestId('heart-confetti')).toHaveAttribute('aria-hidden','true');
 expect(await page.getByTestId('heart-confetti').evaluate(el=>getComputedStyle(el).pointerEvents)).toBe('none');
 await page.locator('#heart-touch-probe').tap();expect(await page.evaluate(()=>(window as any).heartFixture.clicks)).toBe(1);
 await page.clock.fastForward(5000);await expect(page.getByTestId('heart-confetti')).toHaveCount(0);
 await set(page,{now:'2026-10-04T13:12:59Z'});await set(page,{now:'2026-10-04T13:13:00Z'});await expect(page.getByTestId('heart-confetti')).toBeVisible();
});

test('mounting or enabling in an eligible minute never catches up',async({page})=>{
 await mount(page,'2026-10-04T12:12:00Z');await expect(page.getByTestId('heart-confetti')).toHaveCount(0);
 await set(page,{now:'2026-10-04T12:12:01Z'});await expect(page.getByTestId('heart-confetti')).toHaveCount(0);
 await set(page,{enabled:false,now:'2026-10-04T12:59:59Z'});await set(page,{enabled:true,now:'2026-10-04T13:00:00Z'});await expect(page.getByTestId('heart-confetti')).toHaveCount(0);
});

test('ordinary minutes, long clock jumps and repeated events do not trigger',async({page})=>{
 await mount(page,'2026-10-04T12:13:59Z');await set(page,{now:'2026-10-04T12:14:00Z'});await expect(page.getByTestId('heart-confetti')).toHaveCount(0);
 await set(page,{now:'2026-10-04T13:00:00Z'});await expect(page.getByTestId('heart-confetti')).toHaveCount(0);
 await set(page,{now:'2026-10-04T13:59:59Z'});await set(page,{now:'2026-10-04T14:00:00Z'});await expect(page.getByTestId('heart-confetti')).toBeVisible();await page.clock.fastForward(5000);
 await set(page,{now:'2026-10-04T13:59:59Z'});await set(page,{now:'2026-10-04T14:00:00Z'});await expect(page.getByTestId('heart-confetti')).toHaveCount(0);
});

test('page exit and reduced-motion change clear a running burst immediately',async({page})=>{
 await mount(page);await set(page,{now:'2026-10-04T13:00:00Z'});await expect(page.getByTestId('heart-confetti')).toBeVisible();await set(page,{enabled:false});await expect(page.getByTestId('heart-confetti')).toHaveCount(0);
 await set(page,{enabled:true,now:'2026-10-04T13:59:59Z'});await set(page,{now:'2026-10-04T14:00:00Z'});await expect(page.getByTestId('heart-confetti')).toBeVisible();await page.emulateMedia({reducedMotion:'reduce'});await expect(page.getByTestId('heart-confetti')).toHaveCount(0);
 await set(page,{now:'2026-10-04T14:59:59Z'});await set(page,{now:'2026-10-04T15:00:00Z'});await expect(page.getByTestId('heart-confetti')).toHaveCount(0);
});

test('hidden state cancels and visibility restoration never catches up',async({page})=>{
 await mount(page);await set(page,{now:'2026-10-04T13:00:00Z'});await expect(page.getByTestId('heart-confetti')).toBeVisible();
 await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'))});await expect(page.getByTestId('heart-confetti')).toHaveCount(0);
 await set(page,{now:'2026-10-04T13:59:59Z'});await set(page,{now:'2026-10-04T14:00:00Z'});await expect(page.getByTestId('heart-confetti')).toHaveCount(0);
 await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:false});document.dispatchEvent(new Event('visibilitychange'))});await set(page,{now:'2026-10-04T14:00:01Z'});await expect(page.getByTestId('heart-confetti')).toHaveCount(0);
});

test('matching digits use configured zone rather than host time and invalid zone is inert',async({page})=>{
 await mount(page,'2026-10-04T09:11:59Z',true,'Europe/Bucharest');await set(page,{now:'2026-10-04T09:12:00Z'});await expect(page.getByTestId('heart-confetti')).toBeVisible();await set(page,{timezone:'Invalid/Zone'});await expect(page.getByTestId('heart-confetti')).toHaveCount(0);
});



async function mainHome(page:Page,start:string,theme:string,language:string){
 const actions:any[]=[];
 const state={preferences:{language,theme,setupComplete:true,nightEnabled:false,screensaverMinutes:0,visualizerStyle:'off',homeCards:['weather','forecast','playback'],decorativeAircraft:false,decorativeLunarDust:false,timezone:'UTC',location:{name:'Fixture city',latitude:44.4,longitude:26.1},favorites:[],shortcuts:['radio','media']},network:{available:true,state:'connected',devices:[],saved:[]},bluetooth:{available:true,devices:[],prompts:[]},audio:{available:true,ready:true,volume:30,mute:false,outputs:[]},player:{state:'idle'},weather:{stale:false,current:{temperature_c:18,feels_like_c:17,weather_code:0,is_day:1},daily:Array.from({length:5},(_,i)=>({date:`2026-10-0${i+4}`,weather_code:0,max_c:20,min_c:10}))}};
 await page.route('**/api/**',route=>{const request=route.request(),path=new URL(request.url()).pathname;if(request.method()!=='GET')actions.push({path,body:request.postDataJSON()});return route.fulfill({json:path==='/api/session'?{token:'heart-home-fixture'}:path==='/api/state'?state:path==='/api/radio'?{stations:[]}:{ok:true}})});
 await page.clock.install({time:new Date(start)});await page.goto('/');await expect(page.locator('.ambient-home')).toBeVisible();await expect(page.locator('.app')).toHaveAttribute('data-home-phase','interactive');
 return actions;
}
for(const theme of ['ink','night']) for(const event of ['hour','matching']){
 test(`main Home ${theme} ${event}: ambient-only confetti above sky, below controls and wake cancels`,async({page},info)=>{
  const start=event==='hour'?'2026-10-04T12:59:29Z':'2026-10-04T12:11:29Z';
  const actions=await mainHome(page,start,theme,info.project.name.endsWith('ro')?'ro':'en');
  await expect(page.getByTestId('heart-confetti')).toHaveCount(0);
  await page.clock.fastForward(30000);await expect(page.locator('.app')).toHaveAttribute('data-home-phase','ambient');
  await page.clock.runFor(1100);await expect(page.getByTestId('heart-confetti')).toBeVisible();
  const stack=await page.evaluate(()=>{
   const heart=document.querySelector('.app>.heart-confetti')!,sky=document.querySelector('.app>.ambient-sky')!,controls=document.querySelector('.app>.main-area')!;
   return {aboveSky:Number(getComputedStyle(heart).zIndex)>Number(getComputedStyle(sky).zIndex),belowControls:Number(getComputedStyle(heart).zIndex)<=Number(getComputedStyle(controls).zIndex)&&!!(heart.compareDocumentPosition(controls)&Node.DOCUMENT_POSITION_FOLLOWING),pointer:getComputedStyle(heart).pointerEvents};
  });expect(stack).toEqual({aboveSky:true,belowControls:true,pointer:'none'});
  await page.clock.runFor(900);
  await expect.poll(()=>page.locator('.confetti-heart').evaluateAll(hearts=>hearts.some(el=>Number(getComputedStyle(el).opacity)>.1))).toBe(true);
  await page.screenshot({path:info.outputPath(`home-hearts-${theme}-${event}.png`)});
  const before=actions.length;await page.touchscreen.tap(400,240);await expect(page.locator('.app')).toHaveAttribute('data-home-phase','interactive');await expect(page.getByTestId('heart-confetti')).toHaveCount(0);expect(actions.length).toBe(before);
 });
}

test('main Home eligible boundary remains quiet while interactive and entry mid-minute cannot catch up',async({page},info)=>{
 await mainHome(page,'2026-10-04T12:59:59Z','night',info.project.name.endsWith('ro')?'ro':'en');
 await page.clock.runFor(1100);await expect(page.locator('.app')).toHaveAttribute('data-home-phase','interactive');await expect(page.getByTestId('heart-confetti')).toHaveCount(0);
 await page.clock.fastForward(31000);await expect(page.locator('.app')).toHaveAttribute('data-home-phase','ambient');await expect(page.getByTestId('heart-confetti')).toHaveCount(0);
});
