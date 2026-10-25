importScripts('documentation-navigation.js');
// Only trusted extension content scripts on the explicitly supported services.
let keyboardPort;
let activeNative;
let pending = Promise.resolve();
let generation = 0;
const returns = new Map();
const committedReturns = new Map();
let keyboardWindow;
let windowRecovery = Promise.resolve();
function restoreFullscreen() {
  const windowId = keyboardWindow;
  keyboardWindow = undefined;
  if (windowId !== undefined) {
    windowRecovery = windowRecovery.then(() => chrome.windows.update(windowId, { state: 'fullscreen' })).catch(() => {});
  }
  return windowRecovery;
}
function forgetPort(port) {
  // A delayed disconnect from a replaced host must not retract a newer keyboard.
  if (keyboardPort !== port) return;
  keyboardPort = undefined;
  void restoreFullscreen();
}
function allowed(sender) {
  if (!sender || sender.id !== chrome.runtime.id || sender.frameId !== 0 ||
      !Number.isInteger(sender.tab?.windowId) || sender.tab.windowId < 0) return false;
  try {
    const url = new URL(sender.url);
    return documentationURL(url.href) || documentationRecoveryURL(url.href) || url.protocol === 'https:' && ['youtube.com', 'netflix.com', 'spotify.com'].some(
      domain => url.hostname === domain || url.hostname.endsWith(`.${domain}`)
    ) || url.protocol === 'https:' && url.hostname === 'accounts.google.com';
  } catch { return false; }
}
function keyboard(action, windowId) {
  const payload = typeof action === 'string' ? { action } : action;
  return new Promise(resolve => {
    if (!keyboardPort) {
      keyboardPort = chrome.runtime.connectNative('org.pysh.keyboard');
      const connected = keyboardPort;
      connected.onDisconnect.addListener(() => {
        void chrome.runtime.lastError;
        forgetPort(connected);
      });
    }
    const port = keyboardPort;
    let request;
    let finished = false;
    const finish = result => {
      if (finished) return;
      finished = true;
      clearTimeout(timer);
      port.onMessage.removeListener(reply);
      port.onDisconnect.removeListener(disconnected);
      if (activeNative === request) activeNative = undefined;
      resolve(result);
    };
    const reply = result => finish(result);
    const disconnected = () => {
      void chrome.runtime.lastError;
      forgetPort(port);
      finish({ ok: false, error: 'keyboard_unavailable' });
    };
    const timer = setTimeout(() => {
      forgetPort(port);
      finish({ ok: false, error: 'keyboard_unavailable' });
      port.disconnect();
    }, payload.action.startsWith('controls-') ? 10000 : 3000);
    port.onMessage.addListener(reply);
    port.onDisconnect.addListener(disconnected);
    request = { action: payload.action, windowId, cancel() {
      finish({ ok: false, error: 'keyboard_unavailable' });
      try { port.disconnect(); } catch {}
    } };
    activeNative = request;
    try {
      port.postMessage(payload);
    } catch {
      forgetPort(port);
      finish({ ok: false, error: 'keyboard_unavailable' });
      port.disconnect();
    }
  });
}
async function serviceKeyboard(action, windowId, requestedGeneration) {
  await windowRecovery;
  if (requestedGeneration !== generation) return { ok: false, error: 'keyboard_unavailable' };
  try {
    if (action === 'show') {
      // wvkbd 0.15 occupies Wayland's TOP layer, below a fullscreen surface.
      // Maximizing allows its exclusive zone to resize the official service page.
      keyboardWindow = windowId;
      await chrome.windows.update(windowId, { state: 'maximized' });
      if (requestedGeneration !== generation) return { ok: false, error: 'keyboard_unavailable' };
    }
    const result = await keyboard(action, windowId);
    if ((action === 'show' && !result?.ok) || (action === 'hide' && result?.ok)) {
      await restoreFullscreen();
    }
    return result;
  } catch {
    if (action === 'show') await restoreFullscreen();
    return { ok: false, error: 'keyboard_unavailable' };
  }
}
function removeOwnedWindow(windowId) {
  return new Promise(resolve => {
    let finished = false;
    const finish = result => {
      if (finished) return;
      finished = true;
      clearTimeout(timer);
      resolve(result);
    };
    const timer = setTimeout(() => finish({ ok: false, error: 'return_unavailable' }), 4000);
    try {
      chrome.windows.remove(windowId, () => {
        const failed = Boolean(chrome.runtime.lastError);
        finish(failed ? { ok: false, error: 'return_unavailable' } : { ok: true });
      });
    } catch { finish({ ok: false, error: 'return_unavailable' }); }
  });
}
function returnToHub(target, windowId) {
  const committed = committedReturns.get(windowId);
  if (committed && committed.target !== target) return Promise.resolve({ ok: false, error: 'return_unavailable' });
  if (committed?.closed) return Promise.resolve({ ok: true });
  const existing = returns.get(windowId);
  if (existing) {
    if (existing.target !== target) {
      if (existing.phase !== 'queued') return Promise.resolve({ ok: false, error: 'return_unavailable' });
      existing.target = target;
      existing.generation = ++generation;
      if (!target) cancelOwnedKeyboard(windowId);
    }
    return existing.promise;
  }
  const operation = { target, generation: ++generation, phase: 'queued', promise: undefined };
  if (!target) cancelOwnedKeyboard(windowId);
  returns.set(windowId, operation);
  operation.promise = pending.then(async () => {
    if (operation.generation !== generation) return { ok: false, error: 'return_unavailable' };
    operation.phase = 'dispatching';
    if (operation.target && !committed) {
      const destination = await keyboard(operation.target, windowId);
      if (!destination?.ok) return { ok: false, error: 'return_unavailable' };
    }
    if (operation.generation !== generation) return { ok: false, error: 'return_unavailable' };
    operation.phase = 'closing';
    operation.generation = ++generation;
    // Once removal starts, retries may repeat only removal, never owner navigation.
    const closure = { target: operation.target, closed: false };
    committedReturns.set(windowId, closure);
    keyboardWindow = undefined;
    const oldPort = keyboardPort;
    keyboardPort = undefined;
    try { oldPort?.disconnect(); } catch {}
    const result = await removeOwnedWindow(windowId);
    closure.closed = result.ok === true;
    return result;
  }).catch(() => ({ ok: false, error: 'return_unavailable' })).finally(() => {
    // Invalidate messages admitted while asynchronous window removal was pending.
    if (operation.phase === 'closing' && operation.generation === generation) generation += 1;
    if (returns.get(windowId) === operation) returns.delete(windowId);
  });
  pending = operation.promise.then(() => undefined);
  return operation.promise;
}
function cancelOwnedKeyboard(windowId) {
  if (activeNative?.windowId !== windowId || !['status', 'show', 'hide'].includes(activeNative.action)) return;
  keyboardWindow = undefined;
  keyboardPort = undefined;
  activeNative.cancel();
}
function controlMessage(message) {
  const keys = Object.keys(message);
  if (message.action === 'controls-status') return keys.length === 1;
  if (!['controls-volume','controls-mute','controls-brightness','controls-output'].includes(message.action) || keys.length !== 2 || !Object.hasOwn(message,'value')) return false;
  const value=message.value;
  if(message.action==='controls-mute') return typeof value==='boolean';
  if(message.action==='controls-output') return typeof value==='string'&&value.length>=1&&value.length<=200&&!/[\x00-\x1f\x7f]/.test(value);
  return Number.isInteger(value)&&value>=(message.action==='controls-brightness'?1:0)&&value<=100;
}
function streamingSender(sender) {
  try { const url=new URL(sender.url);return url.protocol==='https:'&&['youtube.com','netflix.com','spotify.com'].some(domain=>url.hostname===domain||url.hostname.endsWith('.'+domain)); }
  catch { return false; }
}
chrome.runtime.onMessage.addListener((message, sender, respond) => {
  if (!allowed(sender) || !message || typeof message !== 'object' || Array.isArray(message) || !Object.hasOwn(message,'action') || typeof message.action !== 'string') return;
  if (message.action.startsWith('controls-')) {
    // Documentation/authentication pages remain read-only; no generic owner API.
    if (!streamingSender(sender) || !controlMessage(message)) return;
    const requestedGeneration=generation;
    pending=pending.then(()=>requestedGeneration===generation?keyboard(message,sender.tab.windowId):{ok:false,error:'controls_unavailable'})
      .then(respond).catch(()=>respond({ok:false,error:'controls_unverified',uncertain:true}));
    return true;
  }
  if (Object.keys(message).length !== 1 || !Object.hasOwn(message,'action')) return;
  if (['return', 'return-home', 'return-radio', 'return-media'].includes(message.action)) {
    returnToHub(message.action.slice(7), sender.tab.windowId).then(respond).catch(() => respond({ ok: false, error: 'return_unavailable' }));
    return true;
  } else if (['status', 'show', 'hide'].includes(message.action)) {
    const requestedGeneration = generation;
    pending = pending.then(() => serviceKeyboard(message.action, sender.tab.windowId, requestedGeneration)).then(respond).catch(() => {
      respond({ ok: false, error: 'keyboard_unavailable' });
    });
    return true;
  }
});
