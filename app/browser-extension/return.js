// Isolated touch controls. Never reads typed values, account fields or cookies.
(() => {
  const host = document.createElement('pi-hub-return');
  const shadow = host.attachShadow({ mode: 'closed' });
  host.style.cssText = 'all:initial;position:fixed;right:0;top:0;z-index:2147483647;display:block;';
  const controls = document.createElement('div');
  controls.style.cssText = 'display:flex;gap:8px;padding:8px 12px;';
  const buttonStyle = 'all:initial;box-sizing:border-box;display:block;min-width:154px;min-height:52px;padding:12px 18px;background:#f7f5ee;color:#18261e;border:2px solid #18261e;border-radius:14px;font:600 16px/24px system-ui;cursor:pointer;box-shadow:0 2px 12px #0005;touch-action:manipulation;';
  const keyboard = document.createElement('button');
  const back = document.createElement('button');
  keyboard.style.cssText = back.style.cssText = buttonStyle;
  back.textContent = '← Pi Smart Hub';
  back.title = 'Pi Smart Hub';
  const reveal = document.createElement('button');
  // Invisible edge target: no persistent overlay during a film.
  reveal.style.cssText = 'all:initial;position:absolute;right:0;top:0;width:48px;height:48px;background:transparent;opacity:0;touch-action:manipulation;cursor:pointer;';
  const hint = document.createElement('span');
  const message = document.createElement('span');
  hint.style.cssText = message.style.cssText = 'font:600 16px/20px system-ui;background:#f7f5ee;color:#18261e;max-width:320px;padding:8px 12px;border-radius:8px;display:block;';
  message.style.display = 'none';
  message.setAttribute('role', 'status');
  let ro = false, keyboardShown = false, retractTimer, blurTimer, revealAfterFullscreen = false;
  let returnPending = false, returnFailed = false, returnSequence = 0;
  function requestReturn() {
    if (returnPending) return;
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
    const timer = setTimeout(() => finish({ ok: false }), 5000);
    try {
      chrome.runtime.sendMessage({ action: 'return' }, result => {
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
    back.setAttribute('aria-busy', String(returnPending));
    back.style.opacity = returnPending ? '0.65' : '1';
    back.textContent = returnPending ? (ro ? 'Se revine…' : 'Returning…') : returnFailed ? (ro ? 'Reîncearcă revenirea' : 'Retry return') : '← Pi Smart Hub';
    back.title = back.textContent;
    if (returnFailed) message.textContent = ro ? 'Revenirea la PySH nu a reușit. Reîncearcă.' : 'Could not return to PySH. Try again.';
    keyboard.textContent = keyboardShown ? (ro ? 'Închide tastatura' : 'Hide keyboard') : (ro ? 'Tastatură' : 'Keyboard');
    keyboard.title = keyboard.textContent;
    reveal.setAttribute('aria-label', ro ? 'Afișează comenzile PySH' : 'Show PySH controls');
    hint.textContent = ro ? 'Atinge colțul din dreapta sus pentru comenzi.' : 'Tap the top-right corner for controls.';
  }
  function retract() {
    if (returnPending || returnFailed) return;
    controls.style.display = hint.style.display = message.style.display = 'none';
    reveal.style.display = 'block';
    clearTimeout(retractTimer);
  }
  function expose() {
    controls.style.display = 'flex';
    reveal.style.display = 'none';
    clearTimeout(retractTimer);
    retractTimer = setTimeout(retract, 4000);
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
  for (const button of [keyboard, back, reveal]) button.addEventListener('pointerdown', event => event.preventDefault());
  keyboard.addEventListener('click', () => keyboardAction(!keyboardShown, true));
  back.addEventListener('click', () => { requestReturn(); expose(); });
  reveal.addEventListener('click', expose);
  controls.addEventListener('pointerdown', expose);
  controls.append(keyboard, back);
  shadow.append(controls, hint, message, reveal);
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
  document.addEventListener('pointerup', event => {
    // Replaced fullscreen elements do not paint appended controls. The same
    // 48px edge gesture exits only HTML fullscreen, then reveals our controls;
    // the browser app keeps its frameless panel window; the player is intact.
    if (!['VIDEO', 'AUDIO', 'IFRAME', 'IMG', 'CANVAS', 'OBJECT', 'EMBED'].includes(document.fullscreenElement?.tagName) ||
        event.clientX < window.innerWidth - 48 || event.clientX > window.innerWidth ||
        event.clientY < 0 || event.clientY > 48) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    revealAfterFullscreen = true;
    document.exitFullscreen().catch(() => { revealAfterFullscreen = false; });
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
  expose();
  chrome.runtime.sendMessage({ action: 'status' }, result => {
    if (chrome.runtime.lastError) return;
    ro = result?.language === 'ro';
    localize();
  });
})();
