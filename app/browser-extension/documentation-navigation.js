const DOC_ORIGINS = new Set(['https://open-meteo.com', 'https://creativecommons.org']);
const documentTabs = new Map();
function documentationURL(value) {
  try { return DOC_ORIGINS.has(new URL(value).origin); } catch { return false; }
}
function documentationRecoveryURL(value) {
  try { const expected = new URL(chrome.runtime.getURL('documentation-return.html')), url = new URL(value); return url.protocol === expected.protocol && url.hostname === expected.hostname && url.pathname === expected.pathname; } catch { return false; }
}
function recoverDocument(tabId) {
  if (!documentTabs.has(tabId)) return;
  void chrome.tabs.update(tabId, {url: chrome.runtime.getURL('documentation-return.html')}).catch(() => {});
}
// Observes navigation only to protect already-owned documentation tabs. No URLs or page contents are logged.
chrome.webNavigation?.onBeforeNavigate.addListener(details => {
  if (details.frameId !== 0) return;
  if (documentationURL(details.url) || documentationRecoveryURL(details.url)) documentTabs.set(details.tabId, true);
  else recoverDocument(details.tabId);
});
chrome.webNavigation?.onCommitted.addListener(details => {
  if (details.frameId === 0 && documentTabs.has(details.tabId) && !documentationURL(details.url) && !documentationRecoveryURL(details.url)) recoverDocument(details.tabId);
});
chrome.webNavigation?.onErrorOccurred.addListener(details => {
  if (details.frameId === 0 && !documentationRecoveryURL(details.url)) recoverDocument(details.tabId);
});
chrome.webNavigation?.onCreatedNavigationTarget.addListener(details => {
  if (!documentTabs.has(details.sourceTabId)) return;
  documentTabs.set(details.tabId, true);
  if (!documentationURL(details.url)) recoverDocument(details.tabId);
});
chrome.tabs?.onRemoved.addListener(tabId => documentTabs.delete(tabId));
