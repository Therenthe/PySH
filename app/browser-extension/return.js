// An isolated browser control. Never reads account fields, cookies or page content.
(() => {
  const host = document.createElement('pi-hub-return');
  const shadow = host.attachShadow({ mode: 'closed' });
  const button = document.createElement('button');
  button.textContent = '← Pi Smart Hub';
  button.title = 'Pi Smart Hub';
  button.style.cssText = 'all:initial;box-sizing:border-box;display:block;min-width:154px;min-height:52px;padding:12px 18px;background:#f7f5ee;color:#18261e;border:2px solid #18261e;border-radius:14px;font:600 16px/24px system-ui;cursor:pointer;box-shadow:0 2px 12px #0005;touch-action:manipulation;';
  button.addEventListener('click', () => chrome.runtime.sendMessage({ action: 'return' }));
  shadow.append(button);
  host.style.cssText = 'all:initial;position:fixed;right:12px;top:8px;z-index:2147483647;display:block;';
  function attach() {
    const parent = document.fullscreenElement || document.documentElement;
    if (parent && !parent.contains(host)) parent.append(host);
  }
  attach();
  document.addEventListener('fullscreenchange', attach);
})();
