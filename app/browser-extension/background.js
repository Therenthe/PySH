// Only trusted extension content scripts on the explicitly supported services.
let keyboardPort;
let pending = Promise.resolve();
let generation = 0;
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
chrome.runtime.onMessage.addListener((message, sender, respond) => {
  if (!allowed(sender) || !message || typeof message !== 'object' ||
      Array.isArray(message) || Object.keys(message).length !== 1 ||
      !Object.hasOwn(message, 'action')) return;
  if (message.action === 'return') {
    generation += 1;
    keyboardPort?.disconnect();
    keyboardPort = undefined;
    chrome.windows.remove(sender.tab.windowId);
  } else if (['status', 'show', 'hide'].includes(message.action)) {
    const requestedGeneration = generation;
    pending = pending.then(() => requestedGeneration === generation
      ? keyboard(message.action) : { ok: false, error: 'keyboard_unavailable' }).then(respond).catch(() => {
      respond({ ok: false, error: 'keyboard_unavailable' });
    });
    return true;
  }
});
