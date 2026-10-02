import type { Page } from '@playwright/test';

export async function textLegibility(page:Page) {
  return page.evaluate(()=> {
    const defects:string[]=[];
    const color=(s:string)=>{const m=s.match(/[\d.]+/g)||[];return [Number(m[0]),Number(m[1]),Number(m[2]),m[3]===undefined?1:Number(m[3])];};
    const over=(f:number[],b:number[])=>[0,1,2].map(i=>f[i]*f[3]+b[i]*(1-f[3]));
    const lum=(c:number[])=>c.slice(0,3).map(x=>x/255).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4).reduce((a,x,i)=>a+x*[.2126,.7152,.0722][i],0);
    const bg=(el:Element)=>{const chain:Element[]=[];for(let x:Element|null=el;x;x=x.parentElement)chain.unshift(x);return chain.reduce((b,x)=>over(color(getComputedStyle(x).backgroundColor),b),[255,255,255]);};
    for(const el of document.querySelectorAll('main *')){
      const text=[...el.childNodes].filter(n=>n.nodeType===Node.TEXT_NODE).map(n=>n.textContent).join('').trim();
      const r=el.getBoundingClientRect(),s=getComputedStyle(el);
      if(!text||!r.width||!r.height||r.bottom<=0||r.top>=480||r.right<=0||r.left>=800||s.visibility==='hidden'||el.closest('[aria-hidden=true],button:disabled'))continue;
      const size=parseFloat(s.fontSize);if(size<14)defects.push(`small text ${text.slice(0,40)}: ${size}px`);
      const background=bg(el),foreground=over(color(s.color),background),a=lum(foreground),b=lum(background),ratio=(Math.max(a,b)+.05)/(Math.min(a,b)+.05);
      const large=size>=24||(size>=18.66&&parseFloat(s.fontWeight)>=700);
      if(ratio<(large?3:4.5)-.05)defects.push(`text contrast ${text.slice(0,40)}: ${ratio.toFixed(2)}`);
    }
    for(const el of document.querySelectorAll('.favorite-button span,.error-dot,.service-logo')){
      const r=el.getBoundingClientRect();if(!r.width||!r.height||r.bottom<=0||r.top>=480)continue;
      const background=bg(el),foreground=over(color(getComputedStyle(el).color),background),a=lum(foreground),b=lum(background),ratio=(Math.max(a,b)+.05)/(Math.min(a,b)+.05);
      if(ratio<2.95)defects.push(`symbol contrast ${el.textContent}: ${ratio.toFixed(2)}`);
    }
    return defects;
  });
}
