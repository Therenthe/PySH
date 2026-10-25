// Isolated touch controls. Never reads typed values, account fields or cookies.
(() => {
  const host = document.createElement('pi-hub-return');
  const shadow = host.attachShadow({ mode: 'closed' });
  host.style.cssText = 'all:initial;position:fixed;inset:0;z-index:2147483647;display:block;pointer-events:none;';
  const styles = document.createElement('style');
  styles.textContent = `
    :host{--surface:#111d26;--raised:#20303a;--text:#f4f8fa;--muted:#b7c9cf;--line:#6d858e;--accent:#79dfbc;--accent-ink:#102820;--focus:#9cf4d2;--hover:#344b56;--accent-hover:#a2efcf;--error-bg:#472a20;--error-text:#ffe4cf;color-scheme:dark}
    *{box-sizing:border-box}button{touch-action:manipulation;cursor:pointer}button:focus-visible{outline:3px solid var(--focus);outline-offset:3px}
    .shade{position:absolute;inset:0;background:#030b1280;pointer-events:auto}
    .drawer{position:absolute;top:0;left:50%;transform:translateX(-50%);width:min(664px,calc(100% - 24px));padding:20px 24px 16px;border:0;border-radius:0 0 24px 24px;background:var(--surface);color:var(--text);font:16px/1.4 system-ui,sans-serif;box-shadow:0 20px 48px #0006;pointer-events:auto;animation:arrive .24s cubic-bezier(.16,1,.3,1)}
    .heading{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:20px}.identity{display:flex;align-items:center;gap:12px}.identity svg{width:38px;height:38px;stroke:var(--accent);fill:none;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}.title{display:block;font-size:24px;font-weight:650;line-height:1.2;letter-spacing:-.025em}.subtitle{display:block;margin-top:3px;color:var(--muted);font-size:14px;line-height:1.3}
    .actions{display:grid;grid-template-columns:1.3fr 1fr 1fr;gap:12px}
    .action{all:initial;box-sizing:border-box;min-height:104px;padding:16px 12px;border:0;border-radius:16px;background:var(--raised);color:var(--text);font:600 17px/1.3 system-ui,sans-serif;text-align:center;cursor:pointer;touch-action:manipulation;display:flex;align-items:center;justify-content:center;gap:12px;flex-direction:column;transition:background .16s ease,transform .16s ease}
    .action:first-child{background:var(--accent);color:var(--accent-ink)}.action:hover{background:var(--hover)}.action:first-child:hover{background:var(--accent-hover)}.action:active{transform:scale(.97)}.action:disabled{opacity:.65;cursor:wait;transform:none}
    .action svg{width:28px;height:28px;stroke:currentColor;fill:none;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}
    .keyboard{grid-column:1/-1;min-height:48px;margin-top:4px;padding:8px 0;flex-direction:row;justify-content:flex-start;gap:10px;border-radius:10px;background:transparent;font-size:15px;color:var(--muted)}.keyboard svg{width:22px;height:22px}.keyboard:hover{background:var(--raised)}.keyboard[aria-pressed=true]{color:var(--accent)}
    .close{all:initial;box-sizing:border-box;width:48px;height:48px;display:flex;align-items:center;justify-content:center;border:1px solid var(--line);border-radius:50%;background:transparent;color:var(--text);cursor:pointer;touch-action:manipulation;transition:background .16s ease}.close:hover,.close:active{background:var(--raised)}.close svg{width:24px;height:24px;stroke:currentColor;fill:none;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}
    .handle{all:initial;position:absolute;left:50%;top:0;transform:translateX(-50%);width:112px;height:10px;cursor:pointer;touch-action:none;pointer-events:auto;display:flex;align-items:flex-start;justify-content:center}
    .handle:focus-visible{height:48px;background:var(--surface);border:1px solid var(--line);border-radius:0 0 12px 12px}
    .handle:after{content:'';position:absolute;left:50%;top:3px;transform:translateX(-50%);display:block;width:48px;height:3px;border-radius:8px;background:#edf6f4cc;box-shadow:0 1px 3px #0008}
    .status{display:block;margin-top:12px;padding:12px 14px;border-radius:12px;background:var(--error-bg);color:var(--error-text);font:15px/1.4 system-ui,sans-serif}
    @keyframes arrive{from{transform:translate(-50%,-20px)}to{transform:translate(-50%,0)}}
    :host([data-theme=ink]){--surface:#f3f6f2;--raised:#e0e8e2;--text:#192b27;--muted:#496156;--line:#637d70;--accent:#166a52;--accent-ink:#fff;--focus:#165f4c;--hover:#cbdad1;--accent-hover:#247d62;--error-bg:#f9e5d6;--error-text:#653b20;color-scheme:light}
    @media(prefers-color-scheme:light){:host(:not([data-theme=night])){--surface:#f3f6f2;--raised:#e0e8e2;--text:#192b27;--muted:#496156;--line:#637d70;--accent:#166a52;--accent-ink:#fff;--focus:#165f4c;--hover:#cbdad1;--accent-hover:#247d62;--error-bg:#f9e5d6;--error-text:#653b20;color-scheme:light}}
    @media(max-width:480px){.drawer{padding:16px}.heading{margin-bottom:16px}.actions{gap:8px;grid-template-columns:repeat(3,minmax(0,1fr))}.action{padding:12px 5px;font-size:16px}.subtitle{max-width:220px}}
    @media(prefers-reduced-motion:reduce){.drawer{animation:none}.action,.close{transition:none}}
  `;
  const shade = document.createElement('div');shade.className='shade';shade.style.display='none';
  const controls = document.createElement('div');controls.className='drawer';controls.setAttribute('role','dialog');controls.setAttribute('aria-modal','true');controls.setAttribute('aria-label','PySH');
  const heading=document.createElement('div');heading.className='heading';
  const identity=document.createElement('div');identity.className='identity';
  const identityText=document.createElement('div');
  const title=document.createElement('span');title.className='title';title.textContent='PySH';
  const subtitle=document.createElement('span');subtitle.className='subtitle';
  identityText.append(title,subtitle);identity.append(identityText);
  const close=document.createElement('button');close.className='close';
  heading.append(identity,close);
  const actions=document.createElement('div');actions.className='actions';
  const keyboard=document.createElement('button');keyboard.className='action keyboard';
  const back=document.createElement('button');back.className='action';
  const radio=document.createElement('button');radio.className='action';
  const media=document.createElement('button');media.className='action';
  const reveal=document.createElement('button');reveal.className='handle';reveal.setAttribute('aria-expanded','false');reveal.setAttribute('aria-keyshortcuts','Alt+Shift+P');
  const hint=document.createElement('span');hint.style.display='none';
  const message=document.createElement('span');message.className='status';message.style.display='none';message.setAttribute('role','status');
  function label(button,text,path){
    button.textContent=text;
    if(document.createElementNS){const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 24 24');svg.setAttribute('aria-hidden','true');const shape=document.createElementNS('http://www.w3.org/2000/svg','path');shape.setAttribute('d',path);svg.append(shape);button.prepend(svg);}
  }
  // Brand and controls share the same restrained line icon language.
  if(document.createElementNS){const mark=document.createElementNS('http://www.w3.org/2000/svg','svg');mark.setAttribute('viewBox','0 0 40 40');mark.setAttribute('aria-hidden','true');const path=document.createElementNS('http://www.w3.org/2000/svg','path');path.setAttribute('d','M5 18 20 6l15 12v16H5ZM13 28v-7m7 7V16m7 12v-5');mark.append(path);identity.prepend(mark);}
  label(close,'','m6 6 12 12M18 6 6 18');
  let ro = false, keyboardShown = false, retractTimer, blurTimer, revealAfterFullscreen = false;
  let service='';
  try{const hostname=new URL(location.href).hostname;service=hostname==='accounts.google.com'?'Google':[['youtube.com','YouTube'],['netflix.com','Netflix'],['spotify.com','Spotify']].find(([domain])=>hostname===domain||hostname.endsWith('.'+domain))?.[1]||'';}catch{}
  let contextRequest=0, deviceControls;
  let previousFocus;
  const isolated=new Map();
  function releaseIsolation(){for(const [element,value] of isolated)element.inert=value;isolated.clear();}
  function isolate(){releaseIsolation();let branch=host;while(branch?.parentElement){for(const sibling of branch.parentElement.children)if(sibling!==branch&&'inert' in sibling){isolated.set(sibling,sibling.inert);sibling.inert=true;}branch=branch.parentElement;if(branch===document.documentElement)break;}}
  let keyboardNavigation = false;
  let returnPending = false, returnFailed = false, returnSequence = 0, returnDestination = 'home';
  function requestReturn(target = returnDestination) {
    if (returnPending || deviceControls?.busy()) return;
    returnDestination = target;
    returnPending = true; returnFailed = false;
    const sequence = ++returnSequence;
    localize();
    const finish = result => {
      if (sequence !== returnSequence || !returnPending) return;
      clearTimeout(timer);
      returnPending = false;
      returnFailed = !result?.ok;
      localize();
      showReturnResult();
    };
    const timer = setTimeout(() => finish({ ok: false }), 10000);
    try {
      chrome.runtime.sendMessage({ action: 'return-' + target }, result => {
        const failed = Boolean(chrome.runtime.lastError);
        finish(failed ? { ok: false } : result);
      });
    } catch { finish({ ok: false }); }
  }
  function showReturnResult() {
    message.textContent = returnFailed ? (ro ? 'Revenirea la PySH nu a reușit. Reîncearcă.' : 'Could not return to PySH. Try again.') : '';
    message.style.display = returnFailed ? 'block' : 'none';
    expose();
  }
  function localize() {
    back.disabled = returnPending || !!deviceControls?.busy();
    keyboard.disabled = returnPending || !!deviceControls?.busy();
    close.disabled = returnPending || !!deviceControls?.busy();
    controls.setAttribute('aria-busy',String(returnPending||!!deviceControls?.busy()));
    deviceControls?.returning(returnPending);
    deviceControls?.localize(ro);
    back.setAttribute('aria-busy', String(returnPending));
    subtitle.textContent=[service,ro?'Alege unde continui':'Choose where to continue'].filter(Boolean).join(' · ');
    label(back, returnPending ? (ro ? 'Se revine…' : 'Returning…') : returnFailed ? (ro ? 'Reîncearcă revenirea' : 'Retry return') : (ro ? 'Acasă' : 'Home'), 'M3 10 12 3l9 7v11h-6v-7H9v7H3Z');
    radio.disabled=media.disabled=returnPending||!!deviceControls?.busy();
    label(radio,'Radio','M3 8h18v13H3ZM4 8 19 3M7 12h10M7 16h2m6 0h2');
    label(media,'Media','M3 5h18v16H3Zm6 4 7 4-7 4Z');
    close.setAttribute('aria-label',ro?'Închide comenzile PySH':'Close PySH controls');
    back.title = back.textContent;
    if (returnFailed) message.textContent = ro ? 'Revenirea la PySH nu a reușit. Reîncearcă.' : 'Could not return to PySH. Try again.';
    label(keyboard,keyboardShown ? (ro ? 'Închide tastatura' : 'Hide keyboard') : (ro ? 'Tastatură' : 'Keyboard'),'M2 6h20v13H2Zm4 4h1m4 0h1m4 0h1M6 14h1m4 0h1m4 0h1M8 17h8');
    keyboard.title = keyboard.textContent;
    keyboard.setAttribute('aria-pressed',String(keyboardShown));
    reveal.setAttribute('aria-label', ro ? 'Afișează comenzile PySH' : 'Show PySH controls');
    reveal.title=ro?'Comenzi PySH · Alt+Shift+P':'PySH controls · Alt+Shift+P';
    hint.textContent = ro ? 'Trage în jos din centrul marginii de sus pentru comenzile PySH.' : 'Swipe down from the top centre for PySH controls.';
  }
  function retract(deliberate = false) {
    if (returnPending || deviceControls?.busy() || returnFailed && !deliberate || !deliberate && keyboardNavigation && controls.contains(shadow.activeElement)) return;
    controls.style.display=shade.style.display=hint.style.display=message.style.display='none';
    reveal.setAttribute('aria-expanded','false');
    reveal.style.display = 'block';
    releaseIsolation();
    clearTimeout(retractTimer);
  }
  function expose() {
    const wasClosed=controls.style.display==='none';
    controls.style.display='block';shade.style.display='block';reveal.setAttribute('aria-expanded','true');
    reveal.style.display = 'none';
    if(wasClosed){previousFocus=document.activeElement;isolate();refreshContext();deviceControls?.refresh();close.focus?.({preventScroll:true});}
    clearTimeout(retractTimer);
    retractTimer = setTimeout(retract, 8000);
  }
  function keyboardAction(show, reportError = false) {
    chrome.runtime.sendMessage({ action: show ? 'show' : 'hide' }, result => {
      const failed = Boolean(chrome.runtime.lastError || !result?.ok);
      if (!failed) keyboardShown = show;
      localize();
      if(reportError&&!failed&&show){retract(true);if(previousFocus?.isConnected)previousFocus.focus?.({preventScroll:true});return;}
      if (reportError && !returnPending && !returnFailed) {
        message.textContent = failed ? (ro ? 'Tastatura nu este disponibilă. Reîncearcă.' : 'Keyboard unavailable. Try again.') : '';
        message.style.display = failed ? 'block' : 'none';
        expose();
      }
    });
  }
  for (const button of [keyboard, back, radio, media]) button.addEventListener('pointerdown', event => event.preventDefault());
  keyboard.addEventListener('click', () => keyboardAction(!keyboardShown, true));
  back.addEventListener('click', () => { requestReturn(); expose(); });
  radio.addEventListener('click',()=>{requestReturn('radio');expose();});
  media.addEventListener('click',()=>{requestReturn('media');expose();});
  reveal.addEventListener('click',()=>{expose();close.focus?.();});
  close.addEventListener('click',()=>{retract(true);if(!returnPending)reveal.focus?.();});
  shade.addEventListener('click',()=>{retract(true);if(!returnPending)reveal.focus?.();});
  let gesture;
  reveal.addEventListener('pointerdown',event=>{gesture={id:event.pointerId,y:event.clientY};event.preventDefault();reveal.setPointerCapture?.(event.pointerId);});
  reveal.addEventListener('pointermove',event=>{if(gesture&&gesture.id===event.pointerId&&event.clientY-gesture.y>18){gesture=null;expose();}});
  reveal.addEventListener('pointerup',()=>{gesture=null;});reveal.addEventListener('pointercancel',()=>{gesture=null;});
  document.addEventListener('keydown',event=>{
    if(event.altKey&&event.shiftKey&&event.key.toLowerCase()==='p'){keyboardNavigation=true;event.preventDefault();event.stopImmediatePropagation();if(controls.style.display==='none'){expose();close.focus?.();}else retract(true);return;}
    if(controls.style.display==='none')return;
    keyboardNavigation=true;clearTimeout(retractTimer);
    event.stopImmediatePropagation();
    if(event.key==='Escape'){event.preventDefault();event.stopImmediatePropagation();retract(true);reveal.focus?.();}
    if(event.key==='Tab'){event.stopImmediatePropagation();const order=controls.querySelectorAll?[...controls.querySelectorAll('button:not(:disabled),input:not(:disabled)')].filter(element=>element.getClientRects().length):[close,back,radio,media,keyboard].filter(button=>!button.disabled);const index=order.indexOf(shadow.activeElement);const next=(index+(event.shiftKey?-1:1)+order.length)%order.length;event.preventDefault();order[next].focus?.();}
  },true);
  controls.addEventListener('pointerdown',()=>{keyboardNavigation=false;expose();});
  controls.addEventListener('focusin',()=>{if(keyboardNavigation)clearTimeout(retractTimer);});
  controls.addEventListener('focusout',()=>{clearTimeout(retractTimer);retractTimer=setTimeout(retract,8000);});
  if(typeof createPyshDeviceControls==='function'){
    deviceControls=createPyshDeviceControls({context:keyboard,onBusy:()=>{localize();if(controls.style.display!=='none')expose();},onPresentation:value=>{ro=value.language==='ro';host.setAttribute('data-theme',value.theme);localize();},onPane:open=>{actions.style.display=open?'none':'grid';}});
    actions.append(back,radio,media);controls.append(heading,actions,deviceControls.element,hint,message);styles.textContent+=deviceControls.style.textContent;
  }else{actions.append(back,radio,media,keyboard);controls.append(heading,actions,hint,message);}
  document.addEventListener('focusin',event=>{if(controls.style.display!=='none'&&event.target!==host)close.focus?.({preventScroll:true});},true);
  shadow.append(styles,shade,controls,reveal);
  function editable(element) {
    if (!element || element.disabled || element.readOnly) return false;
    if (element.isContentEditable || element.tagName === 'TEXTAREA') return true;
    return element.tagName === 'INPUT' && ['text', 'email', 'password', 'search', 'tel', 'url', 'number'].includes(element.type);
  }
  document.addEventListener('focusin', event => {
    clearTimeout(blurTimer);
    if(event.target===host)return;
    keyboardAction(editable(event.target));
  }, true);
  document.addEventListener('focusout', () => {
    clearTimeout(blurTimer);
    blurTimer = setTimeout(() => { if (document.activeElement!==host&&!editable(document.activeElement)) keyboardAction(false); }, 200);
  }, true);
  function leaveTyping() {
    clearTimeout(blurTimer);
    keyboardAction(false);
    retract();
  }
  // Submission can retain focus; navigation does not guarantee a focusout event.
  // Observe only lifecycle events, never the form or any typed value.
  document.addEventListener('submit', leaveTyping, true);
  window.addEventListener('pagehide', leaveTyping);
  function attach() {
    const parent = document.fullscreenElement || document.documentElement;
    if (parent && host.parentElement !== parent){releaseIsolation();parent.append(host);if(controls.style.display!=='none')isolate();}
  }
  let fullscreenGesture;
  const replacedFullscreen = () => ['VIDEO','AUDIO','IFRAME','IMG','CANVAS','OBJECT','EMBED'].includes(document.fullscreenElement?.tagName);
  const revealFullscreenDrawer = () => {
    if(revealAfterFullscreen)return;
    revealAfterFullscreen=true;
    document.exitFullscreen().catch(()=>{revealAfterFullscreen=false;});
  };
  let fullscreenTouch;
  // Replaced video surfaces cannot paint our handle. Cancel native panning
  // only for a gesture beginning inside the same small top-centre target.
  document.addEventListener('touchstart',event=>{
    const touch=event.touches[0];
    if(!touch||!replacedFullscreen()||Math.abs(touch.clientX-window.innerWidth/2)>56||touch.clientY<0||touch.clientY>10)return;
    fullscreenTouch={id:touch.identifier,y:touch.clientY};event.preventDefault();
  },{capture:true,passive:false});
  document.addEventListener('touchmove',event=>{
    const touch=[...event.touches].find(touch=>touch.identifier===fullscreenTouch?.id);
    if(!touch||!fullscreenTouch)return;
    event.preventDefault();
    if(touch.clientY-fullscreenTouch.y>18){event.stopImmediatePropagation();fullscreenTouch=null;revealFullscreenDrawer();}
  },{capture:true,passive:false});
  document.addEventListener('touchend',()=>{fullscreenTouch=null;},true);
  document.addEventListener('touchcancel',()=>{fullscreenTouch=null;},true);
  document.addEventListener('pointerdown', event => {
    if (!replacedFullscreen() || Math.abs(event.clientX-window.innerWidth/2)>56 || event.clientY<0 || event.clientY>10) return;
    fullscreenGesture={id:event.pointerId,y:event.clientY};event.preventDefault();
  }, true);
  document.addEventListener('pointercancel', () => {fullscreenGesture=null;}, true);
  document.addEventListener('pointerup', event => {
    // Replaced fullscreen elements do not paint appended controls. The same
    // 48px edge gesture exits only HTML fullscreen, then reveals our controls;
    // the browser app keeps its frameless panel window; the player is intact.
    const pulled=fullscreenGesture&&fullscreenGesture.id===event.pointerId&&event.clientY-fullscreenGesture.y>18;
    fullscreenGesture=null;
    if (!replacedFullscreen() || !pulled && (Math.abs(event.clientX-window.innerWidth/2)>56 || event.clientY<0 || event.clientY>10)) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    revealFullscreenDrawer();
  }, true);
  document.addEventListener('fullscreenchange', () => {
    attach();
    leaveTyping();
    if (revealAfterFullscreen && !document.fullscreenElement) {
      revealAfterFullscreen = false;
      expose();
    }
  });
  localize();
  attach();
  retract();
  function refreshContext(){
    const request=++contextRequest;
    try{chrome.runtime.sendMessage({action:'status'},result=>{
      if(request!==contextRequest||chrome.runtime.lastError)return;
      ro=result?.language==='ro';
      if(result?.theme==='ink'||result?.theme==='night')host.setAttribute('data-theme',result.theme);
      localize();
    });}catch{}
  }
  refreshContext();
})();
