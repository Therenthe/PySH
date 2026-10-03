// Only trusted extension content scripts on the explicitly supported services.
let keyboardPort;
let pending = Promise.resolve();
let generation = 0;
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
function allowed(sender) {
  if (!sender || sender.id !== chrome.runtime.id || sender.frameId !== 0 ||
      !Number.isInteger(sender.tab?.windowId) || sender.tab.windowId < 0) return false;
  try {
    const url = new URL(sender.url);
    return url.protocol === 'https:' && ['youtube.com', 'netflix.com', 'spotify.com'].some(
      domain => url.hostname === domain || url.hostname.endsWith(`.${domain}`)
    ) || url.protocol === 'https:' && url.hostname === 'accounts.google.com';
  } catch { return false; }
}
function keyboard(action) {
  return new Promise(resolve => {
    if (!keyboardPort) {
      keyboardPort = chrome.runtime.connectNative('org.pysh.keyboard');
      const connected = keyboardPort;
      connected.onDisconnect.addListener(() => {
        void chrome.runtime.lastError;
        if (keyboardPort === connected) keyboardPort = undefined;
        void restoreFullscreen();
      });
    }
    const port = keyboardPort;
    let finished = false;
    const finish = result => {
      if (finished) return;
      finished = true;
      clearTimeout(timer);
      port.onMessage.removeListener(reply);
      port.onDisconnect.removeListener(disconnected);
      resolve(result);
    };
    const reply = result => finish(result);
    const disconnected = () => {
      void chrome.runtime.lastError;
      if (keyboardPort === port) keyboardPort = undefined;
      finish({ ok: false, error: 'keyboard_unavailable' });
    };
    const timer = setTimeout(() => {
      if (keyboardPort === port) keyboardPort = undefined;
      finish({ ok: false, error: 'keyboard_unavailable' });
      port.disconnect();
    }, 3000);
    port.onMessage.addListener(reply);
    port.onDisconnect.addListener(disconnected);
    try {
      port.postMessage({ action });
    } catch {
      if (keyboardPort === port) keyboardPort = undefined;
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
    const result = await keyboard(action);
    if ((action === 'show' && !result?.ok) || (action === 'hide' && result?.ok)) {
      await restoreFullscreen();
    }
    return result;
  } catch {
    if (action === 'show') await restoreFullscreen();
    return { ok: false, error: 'keyboard_unavailable' };
  }
}
chrome.runtime.onMessage.addListener((message, sender, respond) => {
  if (!allowed(sender) || !message || typeof message !== 'object' ||
      Array.isArray(message) || Object.keys(message).length !== 1 ||
      !Object.hasOwn(message, 'action')) return;
  if (message.action === 'return') {
    generation += 1;
    keyboardWindow = undefined;
    keyboardPort?.disconnect();
    keyboardPort = undefined;
    chrome.windows.remove(sender.tab.windowId);
  } else if (['status', 'show', 'hide'].includes(message.action)) {
    const requestedGeneration = generation;
    pending = pending.then(() => serviceKeyboard(message.action, sender.tab.windowId, requestedGeneration)).then(respond).catch(() => {
      respond({ ok: false, error: 'keyboard_unavailable' });
    });
    return true;
  }
});
