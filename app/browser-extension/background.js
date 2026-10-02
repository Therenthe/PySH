chrome.runtime.onMessage.addListener((message, sender) => {
  if (message?.action === 'return' && sender.tab?.windowId !== undefined) {
    chrome.windows.remove(sender.tab.windowId);
  }
});
