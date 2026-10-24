import {test,expect} from '@playwright/test';

test('external destinations are applied once and stale renderer-start commands are ignored',async({page},info)=>{
 const ro=info.project.name.endsWith('ro');
 const state:any={externalNavigation:{id:'old-command',target:'media'},preferences:{language:ro?'ro':'en',theme:'night',setupComplete:true,screensaverMinutes:0,nightEnabled:false,navigationAutoHide:false},network:{},bluetooth:{devices:[],prompts:[]},audio:{ready:true,volume:30,mute:false},player:{state:'paused',kind:'radio',url:'https://radio.example/live',station_name:'Fixture station'},weather:{}};
 let commands=0;
 await page.route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(route.request().method()==='POST')commands++;
  await route.fulfill({json:path==='/api/session'?{token:'fixture'}:path==='/api/state'?state:path==='/api/media'?{path:'',roots:[],items:[]}:path==='/api/radio'?{stations:[]}:{ok:true}});
 });
 await page.goto('/');await expect(page.locator('.main-nav button').nth(0)).toHaveClass('active');
 for(const [index,target] of ['radio','media','home'].entries()){
  state.externalNavigation={id:`fresh-${index}`,target};
  await expect(page.locator('.main-nav button').nth(['home','radio','media'].indexOf(target))).toHaveClass('active',{timeout:7000});
  // A later poll of the same command must not undo the owner's own navigation.
  await page.locator('.main-nav button').nth(3).tap();
  await expect(page.locator('.main-nav button').nth(3)).toHaveClass('active');
  await page.waitForTimeout(2700);
  await expect(page.locator('.main-nav button').nth(3)).toHaveClass('active');
 }
 expect(commands).toBe(0); // Returning never starts or stops media implicitly.
});
