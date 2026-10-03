import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { createHash } from 'node:crypto';

const directory = new URL('../app/browser-extension/', import.meta.url);
const source = name => readFileSync(new URL(name, directory), 'utf8');
const manifest = JSON.parse(source('manifest.json'));
const extensionId = createHash('sha256').update(Buffer.from(manifest.key, 'base64')).digest('hex')
  .slice(0, 32).replace(/[0-9a-f]/g, digit => String.fromCharCode(97 + parseInt(digit, 16)));
const tick = async () => { for (let i = 0; i < 30; i++) await Promise.resolve(); };
const copy = value => JSON.parse(JSON.stringify(value));
function event() {
  const listeners = new Set();
  return { addListener: fn => listeners.add(fn), removeListener: fn => listeners.delete(fn),
    emit: value => { for (const listener of [...listeners]) listener(value); }, listeners };
}
function background() {
  const ports = [], timers = new Map(), removed = [], updates = [];
  let timerId = 0, failConnect = false;
  const onMessage = event();
  const chrome = { runtime: { id: extensionId, onMessage, connectNative(name) {
    assert.equal(name, 'org.pysh.keyboard');
    if (failConnect) { failConnect = false; throw new Error('unavailable'); }
    const port = { onMessage: event(), onDisconnect: event(), sent: [], closed: false,
      postMessage(message) { if (this.failPost) throw new Error('closed'); this.sent.push(copy(message)); },
      disconnect() { this.closed = true; this.onDisconnect.emit(); } };
    ports.push(port); return port;
  } }, windows: { remove: id => removed.push(id),
    update: async (id, options) => { updates.push({ id, ...copy(options) }); } } };
  vm.runInNewContext(source('background.js'), { chrome, URL,
    setTimeout: (fn, ms) => { assert.equal(ms, 3000); timers.set(++timerId, fn); return timerId; },
    clearTimeout: id => timers.delete(id) });
  const listener = [...onMessage.listeners][0];
  const sender = (url = 'https://www.netflix.com/login') =>
    ({ id: extensionId, frameId: 0, tab: { windowId: 7 }, url });
  function request(message, from = sender()) {
    const replies = [];
    const keepAlive = listener(message, from, result => replies.push(copy(result)));
    return { replies, keepAlive };
  }
  return { ports, timers, removed, updates, chrome, sender, request, failConnection: () => { failConnect = true; } };
}

test('manifest has stable public-key ID and only native messaging permission', () => {
  assert.match(extensionId, /^[a-p]{32}$/);
  assert.deepEqual(manifest.permissions, ['nativeMessaging']);
  assert.deepEqual(manifest.content_scripts[0].matches, [
    'https://*.youtube.com/*', 'https://*.netflix.com/*', 'https://*.spotify.com/*',
    'https://accounts.google.com/*']);
  assert.deepEqual(manifest.content_scripts[0].css, ['immersive.css']);
  const host = JSON.parse(readFileSync(new URL('../os/image/assets/org.pysh.keyboard.json', import.meta.url), 'utf8'));
  assert.equal(host.name, 'org.pysh.keyboard');
  assert.equal(host.type, 'stdio');
  assert.equal(host.path, '/opt/pysh/current/scripts/service-keyboard-host.py');
  assert.deepEqual(host.allowed_origins, [`chrome-extension://${extensionId}/`]);
});

test('rejects foreign extension, child frames, lookalike origins and extra payload', async () => {
  const h = background();
  const senders = [ { ...h.sender(), id: 'foreign' }, { ...h.sender(), frameId: 1 },
    { ...h.sender(), tab: undefined }, { ...h.sender(), tab: { windowId: -1 } },
    ...['http://www.netflix.com/login', 'https://netflix.com.evil.example/',
      'https://evilnetflix.com/', 'https://accounts.google.com.evil.example/',
      'https://google.com/', 'not a URL'].map(url => h.sender(url)) ];
  for (const sender of senders) assert.equal(h.request({ action: 'show' }, sender).keepAlive, undefined);
  for (const payload of [null, [], 'show', { action: 'show', text: 'private' }, { action: 'type' },
    { action: 'SHOW' }, { other: 'show' }, { action: { command: 'show' } }]) {
    assert.equal(h.request(payload).keepAlive, undefined);
  }
  await tick(); assert.equal(h.ports.length, 0); assert.deepEqual(h.removed, []);
});

test('allows supported main frames and serializes native responses without cross-talk', async () => {
  const h = background();
  const requests = ['https://youtube.com/', 'https://music.youtube.com/', 'https://netflix.com/',
    'https://open.spotify.com/', 'https://accounts.google.com/'].map(url =>
    h.request({ action: 'status' }, h.sender(url)));
  requests.forEach(r => assert.equal(r.keepAlive, true));
  await tick(); assert.equal(h.ports.length, 1);
  for (let i = 0; i < requests.length; i++) {
    assert.equal(h.ports[0].sent.length, i + 1);
    h.ports[0].onMessage.emit({ ok: true, language: i % 2 ? 'ro' : 'en' }); await tick();
    assert.equal(requests[i].replies.length, 1);
    assert.equal(requests[i].replies[0].language, i % 2 ? 'ro' : 'en');
  }
  assert.equal(h.timers.size, 0);
  assert.equal(h.ports[0].onMessage.listeners.size, 0);
});

test('disconnect responds once and subsequent request reconnects', async () => {
  const h = background(), first = h.request({ action: 'show' }); await tick();
  h.ports[0].disconnect(); await tick();
  assert.deepEqual(first.replies, [{ ok: false, error: 'keyboard_unavailable' }]);
  const next = h.request({ action: 'show' }); await tick(); assert.equal(h.ports.length, 2);
  h.ports[1].onMessage.emit({ ok: true }); await tick(); assert.deepEqual(next.replies, [{ ok: true }]);
  assert.equal(h.timers.size, 0);
});

test('timeout closes host, removes listeners and allows reconnect', async () => {
  const h = background(), request = h.request({ action: 'hide' }); await tick();
  [...h.timers.values()][0](); await tick();
  assert.deepEqual(request.replies, [{ ok: false, error: 'keyboard_unavailable' }]);
  assert.equal(h.ports[0].closed, true); assert.equal(h.ports[0].onMessage.listeners.size, 0);
  h.request({ action: 'show' }); await tick(); assert.equal(h.ports.length, 2);
});

test('native synchronous failures recover without leaking request timers', async () => {
  const h = background(); h.failConnection();
  const failedConnect = h.request({ action: 'show' }); await tick();
  assert.deepEqual(failedConnect.replies, [{ ok: false, error: 'keyboard_unavailable' }]);
  const first = h.request({ action: 'status' }); await tick();
  h.ports[0].onMessage.emit({ ok: true }); await tick(); assert.equal(first.replies.length, 1);
  h.ports[0].failPost = true;
  const failedPost = h.request({ action: 'show' }); await tick();
  assert.deepEqual(failedPost.replies, [{ ok: false, error: 'keyboard_unavailable' }]);
  assert.equal(h.timers.size, 0); assert.equal(h.ports[0].closed, true);
  h.request({ action: 'status' }); await tick(); assert.equal(h.ports.length, 2);
});

test('Return closes owning window and cancels queued keyboard requests', async () => {
  const h = background(), first = h.request({ action: 'show' }), queued = h.request({ action: 'show' });
  await tick(); h.request({ action: 'return' }); await tick();
  assert.deepEqual(h.removed, [7]); assert.equal(h.ports.length, 1); assert.equal(h.ports[0].closed, true);
  assert.deepEqual(first.replies, [{ ok: false, error: 'keyboard_unavailable' }]);
  assert.deepEqual(queued.replies, [{ ok: false, error: 'keyboard_unavailable' }]);
  assert.equal(h.timers.size, 0);
});

test('keyboard resizes the service window before showing and restores fullscreen after hiding', async () => {
  const h = background(); h.request({ action: 'status' }); await tick();
  assert.deepEqual(h.updates, []); h.ports[0].onMessage.emit({ ok: true }); await tick();
  const show = h.request({ action: 'show' }); await tick();
  assert.deepEqual(h.updates, [{ id: 7, state: 'maximized' }]);
  assert.deepEqual(h.ports[0].sent.at(-1), { action: 'show' });
  h.ports[0].onMessage.emit({ ok: true }); await tick(); assert.deepEqual(show.replies, [{ ok: true }]);
  const hide = h.request({ action: 'hide' }); await tick();
  assert.equal(h.updates.length, 1); // Wait for native hide to finish.
  h.ports[0].onMessage.emit({ ok: true }); await tick();
  assert.deepEqual(h.updates.at(-1), { id: 7, state: 'fullscreen' });
  assert.deepEqual(hide.replies, [{ ok: true }]);
});

test('unsuccessful show and host disconnect restore fullscreen', async () => {
  const h = background(), show = h.request({ action: 'show' }); await tick();
  h.ports[0].onMessage.emit({ ok: false }); await tick();
  assert.deepEqual(show.replies, [{ ok: false }]);
  assert.deepEqual(h.updates.at(-1), { id: 7, state: 'fullscreen' });
  h.request({ action: 'show' }); await tick(); h.ports[0].onMessage.emit({ ok: true }); await tick();
  h.ports[0].disconnect(); await tick();
  assert.deepEqual(h.updates.slice(-2), [{ id: 7, state: 'maximized' }, { id: 7, state: 'fullscreen' }]);
});

test('show timeout restores fullscreen and host connection failure restores fullscreen', async () => {
  const h = background(), show = h.request({ action: 'show' }); await tick();
  [...h.timers.values()][0](); await tick();
  assert.deepEqual(show.replies, [{ ok: false, error: 'keyboard_unavailable' }]);
  assert.deepEqual(h.updates.at(-1), { id: 7, state: 'fullscreen' });
  h.failConnection(); const failed = h.request({ action: 'show' }); await tick();
  assert.deepEqual(failed.replies, [{ ok: false, error: 'keyboard_unavailable' }]);
  assert.deepEqual(h.updates.at(-1), { id: 7, state: 'fullscreen' });
});

test('Return during an awaited maximize never launches keyboard afterward', async () => {
  const h = background(); let finishResize;
  h.chrome.windows.update = () => new Promise(resolve => { finishResize = resolve; });
  const show = h.request({ action: 'show' }); await tick();
  h.request({ action: 'return' }); finishResize(); await tick();
  assert.deepEqual(h.removed, [7]); assert.equal(h.ports.length, 0);
  assert.deepEqual(show.replies, [{ ok: false, error: 'keyboard_unavailable' }]);
});

test('failed window resize attempts fullscreen recovery without starting a host', async () => {
  const h = background(), updates = [];
  h.chrome.windows.update = async (id, options) => {
    updates.push({ id, ...copy(options) }); throw new Error('window unavailable');
  };
  const show = h.request({ action: 'show' }); await tick();
  assert.deepEqual(updates, [{ id: 7, state: 'maximized' }, { id: 7, state: 'fullscreen' }]);
  assert.deepEqual(show.replies, [{ ok: false, error: 'keyboard_unavailable' }]);
  assert.equal(h.ports.length, 0);
});

test('delayed replaced-port disconnect cannot retract a newer typing window', async () => {
  const h = background(); h.request({ action: 'show' }); await tick();
  const old = h.ports[0];
  old.disconnect = () => { old.closed = true; }; // Chromium delivers disconnect later.
  [...h.timers.values()][0](); await tick();
  assert.deepEqual(h.updates.at(-1), { id: 7, state: 'fullscreen' });
  h.request({ action: 'show' }); await tick();
  const current = h.ports[1]; current.onMessage.emit({ ok: true }); await tick();
  assert.deepEqual(h.updates.at(-1), { id: 7, state: 'maximized' });
  const before = h.updates.length;
  old.onDisconnect.emit(); await tick();
  assert.equal(h.updates.length, before);
  h.request({ action: 'hide' }); await tick();
  assert.equal(h.ports.length, 2); // Old disconnect did not clear the active port.
  current.onMessage.emit({ ok: true }); await tick();
  assert.deepEqual(h.updates.at(-1), { id: 7, state: 'fullscreen' });
});

function content(language = 'en') {
  const sent = [], nodes = [], listeners = new Map(), windowListeners = new Map(), timers = new Map();
  let timerId = 0;
  function element(tag) {
    const e = { tag, tagName: tag.toUpperCase(), nodeType: 1, children: [], style: {}, events: new Map(),
      append(...children) {
        for (const child of children) {
          if (child.parentElement) child.parentElement.children = child.parentElement.children.filter(node => node !== child);
          this.children.push(child); child.parentElement = this;
        }
      },
      contains: child => e === child || e.children.some(node => node.contains(child)),
      setAttribute(name, value) { this[name] = value; },
      getAttribute(name) { return this[name] ?? null; },
      removeAttribute(name) { delete this[name]; },
      matches(selector) { return selector === ':popover-open' && Boolean(this.popoverOpen); },
      showPopover() { this.popoverOpen = true; },
      hidePopover() { this.popoverOpen = false; },
      addEventListener(name, fn) { this.events.set(name, fn); },
      attachShadow(options) { assert.equal(options.mode, 'closed'); this.shadow = element('shadow'); return this.shadow; } };
    nodes.push(e); return e;
  }
  const document = { documentElement: element('html'), createElement: element,
    activeElement: null,
    addEventListener: (name, fn) => listeners.set(name, fn) };
  const chrome = { runtime: { sendMessage(message, callback) {
    sent.push(copy(message)); if (message.action === 'status') callback({ ok: true, language });
    else if (callback) chrome.runtime.callback = callback;
  } } };
  const window = { innerWidth: 800, addEventListener: (name, fn) => windowListeners.set(name, fn) };
  vm.runInNewContext(source('return.js'), { document, chrome, window,
    setTimeout: (fn, ms) => { timers.set(++timerId, { fn, ms }); return timerId; },
    clearTimeout: id => timers.delete(id) });
  const runTimers = maxDelay => {
    for (const [id, timer] of [...timers]) {
      if (timer.ms <= maxDelay && timers.has(id)) { timers.delete(id); timer.fn(); }
    }
  };
  return { document, chrome, nodes, sent, listeners, windowListeners, timers, element, runTimers };
}

for (const language of ['en', 'ro']) test(`content controls localize ${language} and recover after unavailable keyboard`, () => {
  const h = content(language), buttons = h.nodes.filter(e => e.tag === 'button');
  const keyboard = buttons.find(e => e.textContent === (language === 'ro' ? 'Tastatură' : 'Keyboard'));
  assert.ok(keyboard); assert.equal(keyboard.title, keyboard.textContent);
  assert.match(keyboard.style.cssText, /min-height:52px/);
  keyboard.events.get('click')(); assert.deepEqual(h.sent.at(-1), { action: 'show' });
  h.chrome.runtime.callback({ ok: false });
  const message = h.nodes.find(e => e.role === 'status'); assert.equal(message.style.display, 'block');
  assert.equal(message.textContent, language === 'ro' ? 'Tastatura nu este disponibilă. Reîncearcă.' : 'Keyboard unavailable. Try again.');
  keyboard.events.get('click')(); h.chrome.runtime.callback({ ok: true });
  assert.equal(message.style.display, 'none');
  buttons.find(e => e.textContent === '← Pi Smart Hub').events.get('click')();
  assert.deepEqual(h.sent.at(-1), { action: 'return' });
});

test('content controls retract during fullscreen and remain revealable without account reads', () => {
  const h = content(), host = h.nodes.find(e => e.tag === 'pi-hub-return');
  assert.ok(h.document.documentElement.contains(host));
  h.document.fullscreenElement = { contains: () => false, append: node => { assert.equal(node, host); } };
  h.listeners.get('fullscreenchange')();
  assert.deepEqual(h.sent, [{ action: 'status' }, { action: 'hide' }]);
  const reveal = h.nodes.find(e => e['aria-label'] === 'Show PySH controls');
  assert.equal(reveal.style.display, 'block');
  reveal.events.get('click')();
  assert.equal(reveal.style.display, 'none');
});

for (const language of ['en', 'ro']) test(`immersive ${language} controls fade and remain accessible through edge target`, () => {
  const h = content(language), reveal = h.nodes.find(e => e['aria-label'] ===
    (language === 'ro' ? 'Afișează comenzile PySH' : 'Show PySH controls'));
  const controls = reveal.parentElement.children.find(e => e.tag === 'div');
  const hint = h.nodes.find(e => e.tag === 'span' && !e.role);
  assert.equal(controls.style.display, 'flex');
  assert.match(hint.textContent, language === 'ro' ? /Atinge colțul/ : /Tap the top-right corner/);
  assert.match(reveal.style.cssText, /width:48px;height:48px/);
  assert.match(reveal.style.cssText, /opacity:0/);
  h.runTimers(3999); assert.equal(controls.style.display, 'flex');
  h.runTimers(4000); assert.equal(controls.style.display, 'none');
  assert.equal(hint.style.display, 'none'); assert.equal(reveal.style.display, 'block');
  reveal.events.get('click')(); assert.equal(controls.style.display, 'flex');
  assert.equal(hint.style.display, 'none'); // Intro hint is not repeated over a film.
  let prevented = false;
  reveal.events.get('pointerdown')({ preventDefault: () => { prevented = true; } });
  assert.equal(prevented, true);
  h.runTimers(4000); assert.equal(controls.style.display, 'none');
});

for (const language of ['en', 'ro']) test(`explicit keyboard toggle ${language} shows then hides`, () => {
  const h = content(language), keyboard = h.nodes.find(e => e.tag === 'button' && e.textContent ===
    (language === 'ro' ? 'Tastatură' : 'Keyboard'));
  keyboard.events.get('click')(); assert.deepEqual(h.sent.at(-1), { action: 'show' });
  h.chrome.runtime.callback({ ok: true });
  assert.equal(keyboard.textContent, language === 'ro' ? 'Închide tastatura' : 'Hide keyboard');
  keyboard.events.get('click')(); assert.deepEqual(h.sent.at(-1), { action: 'hide' });
  h.chrome.runtime.callback({ ok: true });
  assert.equal(keyboard.textContent, language === 'ro' ? 'Tastatură' : 'Keyboard');
});

test('focus-driven keyboard accepts editable fields without inspecting typed values', () => {
  const h = content();
  const eligible = [ ...['text', 'email', 'password', 'search', 'tel', 'url', 'number']
    .map(type => Object.assign(h.element('input'), { type })), h.element('textarea'),
    Object.assign(h.element('div'), { isContentEditable: true }) ];
  for (const field of eligible) {
    // Any accidental credential/value read fails this regression.
    for (const property of ['value', 'textContent', 'innerHTML']) Object.defineProperty(field, property, {
      get() { throw new Error(`Account data accessed: ${property}`); } });
    h.document.activeElement = field; h.listeners.get('focusin')({ target: field });
    assert.deepEqual(h.sent.at(-1), { action: 'show' });
    h.chrome.runtime.callback({ ok: true });
  }
  const rejected = [ ...['checkbox', 'radio', 'submit', 'button', 'range', 'hidden', 'file', 'date']
    .map(type => Object.assign(h.element('input'), { type })),
    Object.assign(h.element('input'), { type: 'email', disabled: true }),
    Object.assign(h.element('textarea'), { readOnly: true }), h.element('div'), null ];
  for (const field of rejected) {
    h.listeners.get('focusin')({ target: field });
    assert.deepEqual(h.sent.at(-1), { action: 'hide' });
    h.chrome.runtime.callback({ ok: true });
  }
  h.sent.forEach(message => assert.deepEqual(Object.keys(message), ['action']));
});

test('blur delay preserves keyboard when switching inputs, hides only outside editable fields', () => {
  const h = content(), input = Object.assign(h.element('input'), { type: 'email' });
  h.listeners.get('focusin')({ target: input }); h.chrome.runtime.callback({ ok: true });
  h.listeners.get('focusout')(); h.document.activeElement = input;
  const before = h.sent.length; h.runTimers(200); assert.equal(h.sent.length, before);
  h.listeners.get('focusout')(); h.document.activeElement = h.element('button');
  h.runTimers(199); assert.equal(h.sent.length, before);
  h.runTimers(200); assert.deepEqual(h.sent.at(-1), { action: 'hide' });
  h.listeners.get('focusout')();
  h.listeners.get('focusin')({ target: input });
  const afterFocus = h.sent.length; h.runTimers(200); assert.equal(h.sent.length, afterFocus);
});

test('immersive styles hide scrollbars while preserving page scrolling', () => {
  const css = source('immersive.css');
  assert.match(css, /scrollbar-width\s*:\s*none/);
  assert.match(css, /::-webkit-scrollbar/);
  assert.doesNotMatch(css, /overflow(?:-x|-y)?\s*:\s*hidden/);
});

test('submit and pagehide close keyboard without reading form fields or event data', () => {
  const h = content(), input = Object.assign(h.element('input'), { type: 'password' });
  Object.defineProperty(input, 'value', { get() { throw new Error('Credential read'); } });
  const event = new Proxy({}, { get() { throw new Error('Lifecycle event data read'); } });
  h.listeners.get('focusin')({ target: input }); h.chrome.runtime.callback({ ok: true });
  h.listeners.get('focusout')(); h.listeners.get('submit')(event);
  assert.deepEqual(h.sent.at(-1), { action: 'hide' });
  assert.ok([...h.timers.values()].every(timer => timer.ms !== 200));
  h.chrome.runtime.callback({ ok: true });
  const keyboard = h.nodes.find(e => e.tag === 'button' && e.textContent === 'Keyboard'); assert.ok(keyboard);
  h.listeners.get('focusin')({ target: input }); h.chrome.runtime.callback({ ok: true });
  h.windowListeners.get('pagehide')(event);
  assert.deepEqual(h.sent.at(-1), { action: 'hide' });
});

test('replaced fullscreen edge exits only HTML fullscreen and reparents visible controls', async () => {
  const h = content(), host = h.nodes.find(e => e.tag === 'pi-hub-return'), video = h.element('video');
  h.document.documentElement.append(video);
  h.document.fullscreenElement = video; h.listeners.get('fullscreenchange')();
  assert.equal(host.parentElement, video);
  let exits = 0, prevented = 0, stopped = 0;
  h.document.exitFullscreen = async () => { exits++; };
  const click = (x, y) => h.listeners.get('pointerup')({clientX:x, clientY:y,
    preventDefault:()=>prevented++, stopImmediatePropagation:()=>stopped++});
  click(400, 240); click(751, 20); click(780, 49); click(780, -1);
  assert.equal(exits, 0); assert.equal(prevented, 0); assert.equal(stopped, 0);
  click(780, 20); assert.equal(exits, 1); assert.equal(prevented, 1); assert.equal(stopped, 1);
  h.document.fullscreenElement = null; h.listeners.get('fullscreenchange')(); await tick();
  assert.equal(host.parentElement, h.document.documentElement);
  assert.equal(video.contains(host), false);
  const controls = host.shadow.children.find(e => e.tag === 'div');
  assert.equal(controls.style.display, 'flex');
  h.runTimers(4000); assert.equal(controls.style.display, 'none');
});

test('container fullscreen uses its overlay without exiting or swallowing page events', () => {
  const h = content(), host = h.nodes.find(e => e.tag === 'pi-hub-return'), wrapper = h.element('div');
  h.document.documentElement.append(wrapper);
  h.document.fullscreenElement = wrapper; h.listeners.get('fullscreenchange')();
  assert.equal(host.parentElement, wrapper);
  h.listeners.get('pointerup')({clientX:780, clientY:20,
    preventDefault(){throw new Error('Swallowed container event');},
    stopImmediatePropagation(){throw new Error('Swallowed container event');}});
  h.document.fullscreenElement = null; h.listeners.get('fullscreenchange')();
  assert.equal(host.parentElement, h.document.documentElement);
});
