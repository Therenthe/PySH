// Isolated touch controls. Never reads typed values, account fields or cookies.
(() => {
  const host = document.createElement('pi-hub-return');
  const shadow = host.attachShadow({ mode: 'closed' });
  host.style.cssText = 'all:initial;position:fixed;inset:0;z-index:2147483647;display:block;pointer-events:none;';
  const styles = document.createElement('style');
  styles.textContent = `
    *{box-sizing:border-box}button{touch-action:manipulation;cursor:pointer}button:focus-visible{outline:3px solid #70d7b3;outline-offset:3px}
    .shade{position:absolute;inset:0;background:#030b1233;pointer-events:auto}
    .drawer{position:absolute;top:8px;left:50%;transform:translateX(-50%);width:min(620px,calc(100% - 24px));padding:12px 16px 16px;border:1px solid #ffffff26;border-radius:0 0 24px 24px;background:#101c27fa;color:#f3f6fa;font:16px/1.4 system-ui;box-shadow:0 16px 48px #0006;pointer-events:auto;animation:arrive .2s ease-out}
    .heading{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px}.heading span{font:600 16px system-ui;letter-spacing:.04em}
    .actions{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}
    .action{all:initial;box-sizing:border-box;min-height:80px;padding:12px 10px;border:1px solid #789198;border-radius:16px;background:#ffffff0b;color:#f3f6fa;font:600 16px/1.3 system-ui;text-align:center;cursor:pointer;touch-action:manipulation;display:flex;align-items:center;justify-content:center;gap:7px;flex-direction:column}
    .action:hover,.action:active{background:#72d4b125;border-color:#72d4b1}.action:disabled{opacity:.6;cursor:wait}
    .action svg{width:24px;height:24px;stroke:currentColor;fill:none;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}
    .keyboard{grid-column:1/-1;min-height:48px;flex-direction:row;background:transparent}
    .close{all:initial;box-sizing:border-box;width:48px;height:48px;border:1px solid #789198;border-radius:14px;text-align:center;background:#ffffff10;color:#f3f6fa;font:24px/48px system-ui;cursor:pointer}
    .handle{all:initial;position:absolute;left:50%;top:0;transform:translateX(-50%);width:112px;height:10px;cursor:pointer;touch-action:none;pointer-events:auto;display:flex;align-items:flex-start;justify-content:center}
    .handle:focus-visible{height:48px;background:#101c27;border:1px solid #789198;border-radius:0 0 12px 12px}
    .handle:after{content:'';position:absolute;left:50%;top:3px;transform:translateX(-50%);display:block;width:48px;height:3px;border-radius:8px;background:#edf6f4cc;box-shadow:0 1px 3px #0008}
    .status{display:block;margin-top:10px;font:15px/1.4 system-ui;color:#ffdbbd}
    @keyframes arrive{from{opacity:0;transform:translate(-50%,-16px)}to{opacity:1;transform:translate(-50%,0)}}
    @media(prefers-reduced-motion:reduce){.drawer{animation:none}}
  `;
  const shade = document.createElement('div');shade.className='shade';shade.style.display='none';
  const controls = document.createElement('div');controls.className='drawer';controls.setAttribute('role','dialog');controls.setAttribute('aria-modal','true');controls.setAttribute('aria-label','PySH');
  const heading=document.createElement('div');heading.className='heading';
  const title=document.createElement('span');title.textContent='PI SMART HUB';
  const close=document.createElement('button');close.className='close';close.textContent='×';heading.append(title,close);
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
  let ro = false, keyboardShown = false, retractTimer, blurTimer, revealAfterFullscreen = false;
  let returnPending = false, returnFailed = false, returnSequence = 0, returnDestination = 'home';
  function requestReturn(target = returnDestination) {
    if (returnPending) return;
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
    back.disabled = returnPending;
    keyboard.disabled = returnPending;
    back.setAttribute('aria-busy', String(returnPending));
    back.style.opacity = returnPending ? '0.65' : '1';
    label(back, returnPending ? (ro ? 'Se revine…' : 'Returning…') : returnFailed ? (ro ? 'Reîncearcă revenirea' : 'Retry return') : (ro ? 'Acasă' : 'Home'), 'M3 10 12 3l9 7v11h-6v-7H9v7H3Z');
    radio.disabled=media.disabled=returnPending;
    label(radio,'Radio','M3 8h18v13H3ZM4 8 19 3M7 12h10M7 16h2m6 0h2');
    label(media,'Media','M3 5h18v16H3Zm6 4 7 4-7 4Z');
    close.setAttribute('aria-label',ro?'Închide comenzile PySH':'Close PySH controls');
    back.title = back.textContent;
    if (returnFailed) message.textContent = ro ? 'Revenirea la PySH nu a reușit. Reîncearcă.' : 'Could not return to PySH. Try again.';
    label(keyboard,keyboardShown ? (ro ? 'Închide tastatura' : 'Hide keyboard') : (ro ? 'Tastatură' : 'Keyboard'),'M2 6h20v13H2Zm4 4h1m4 0h1m4 0h1M6 14h1m4 0h1m4 0h1M8 17h8');
    keyboard.title = keyboard.textContent;
    reveal.setAttribute('aria-label', ro ? 'Afișează comenzile PySH' : 'Show PySH controls');
    reveal.title=ro?'Comenzi PySH · Alt+Shift+P':'PySH controls · Alt+Shift+P';
    hint.textContent = ro ? 'Trage în jos din centrul marginii de sus pentru comenzile PySH.' : 'Swipe down from the top centre for PySH controls.';
  }
  function retract(deliberate = false) {
    if (returnPending || returnFailed && !deliberate) return;
    controls.style.display=shade.style.display=hint.style.display=message.style.display='none';
    reveal.setAttribute('aria-expanded','false');
    reveal.style.display = 'block';
    clearTimeout(retractTimer);
  }
  function expose() {
    controls.style.display='block';shade.style.display='block';reveal.setAttribute('aria-expanded','true');
    reveal.style.display = 'none';
    clearTimeout(retractTimer);
    retractTimer = setTimeout(retract, 8000);
  }
  function keyboardAction(show, reportError = false) {
    chrome.runtime.sendMessage({ action: show ? 'show' : 'hide' }, result => {
      const failed = Boolean(chrome.runtime.lastError || !result?.ok);
      if (!failed) keyboardShown = show;
      localize();
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
  shade.addEventListener('click',()=>{retract(true);});
  let gesture;
  reveal.addEventListener('pointerdown',event=>{gesture={id:event.pointerId,y:event.clientY};event.preventDefault();reveal.setPointerCapture?.(event.pointerId);});
  reveal.addEventListener('pointermove',event=>{if(gesture&&gesture.id===event.pointerId&&event.clientY-gesture.y>18){gesture=null;expose();}});
  reveal.addEventListener('pointerup',()=>{gesture=null;});reveal.addEventListener('pointercancel',()=>{gesture=null;});
  document.addEventListener('keydown',event=>{
    if(event.altKey&&event.shiftKey&&event.key.toLowerCase()==='p'){event.preventDefault();event.stopImmediatePropagation();if(controls.style.display==='none'){expose();close.focus?.();}else retract(true);return;}
    if(controls.style.display==='none')return;
    if(event.key==='Escape'){event.preventDefault();event.stopImmediatePropagation();retract(true);reveal.focus?.();}
    if(event.key==='Tab'){const order=[close,back,radio,media,keyboard].filter(button=>!button.disabled);const index=order.indexOf(shadow.activeElement);const next=(index+(event.shiftKey?-1:1)+order.length)%order.length;event.preventDefault();order[next].focus?.();}
  },true);
  controls.addEventListener('pointerdown', expose);
  actions.append(back,radio,media,keyboard);controls.append(heading,actions,hint,message);
  shadow.append(styles,shade,controls,reveal);
  function editable(element) {
    if (!element || element.disabled || element.readOnly) return false;
    if (element.isContentEditable || element.tagName === 'TEXTAREA') return true;
    return element.tagName === 'INPUT' && ['text', 'email', 'password', 'search', 'tel', 'url', 'number'].includes(element.type);
  }
  document.addEventListener('focusin', event => {
    clearTimeout(blurTimer);
    keyboardAction(editable(event.target));
  }, true);
  document.addEventListener('focusout', () => {
    clearTimeout(blurTimer);
    blurTimer = setTimeout(() => { if (!editable(document.activeElement)) keyboardAction(false); }, 200);
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
    if (parent && host.parentElement !== parent) parent.append(host);
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
  chrome.runtime.sendMessage({ action: 'status' }, result => {
    if (chrome.runtime.lastError) return;
    ro = result?.language === 'ro';
    localize();
  });
})();
