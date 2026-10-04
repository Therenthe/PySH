// This owned page probes only browser capability. It never visits account fields.
(() => {
  const params = new URLSearchParams(location.search);
  const job = params.get('job'), attempt = params.get('attempt');
  const valid = value => typeof value === 'string' && /^[A-Za-z0-9_-]{1,100}$/.test(value);
  let language = params.get('lang') === 'ro' ? 'ro' : 'en';
  let theme = params.get('theme') === 'ink' ? 'ink' : 'night';
  let stopped = false, refreshing = false, probeAttempt, timer, token;
  const node = id => document.getElementById(id);
  const text = {
    en: {
      title:'Preparing protected playback', checking:'Checking playback support…',
      waiting_component:'Preparing this browser…', restarting:'Finishing setup…',
      ready:'Opening the service…', error:'Playback is not ready yet', cancelled:'Setup cancelled',
      description:'The service will open when this browser is ready. First setup needs internet and may take several minutes.',
      pending:'You can return to the hub at any time. Your account and settings are preserved.',
      timeout:'Preparation is taking longer. Check your internet connection, then try again.',
      failure:'This browser could not prepare protected playback. Try again or return to the hub.',
      unavailable:'The hub is unavailable. Try again when it has recovered.',
      offline:'There is no network connection. Reconnect, then try again.',
      back:'Back to hub', retry:'Try again', leaving:'Returning to hub…', invalid:'This preparation session has ended.'
    },
    ro: {
      title:'Pregătirea redării protejate', checking:'Se verifică suportul pentru redare…',
      waiting_component:'Se pregătește browserul…', restarting:'Se finalizează configurarea…',
      ready:'Se deschide serviciul…', error:'Redarea nu este încă pregătită', cancelled:'Configurare anulată',
      description:'Serviciul se va deschide când browserul este pregătit. Prima configurare necesită internet și poate dura câteva minute.',
      pending:'Poți reveni oricând în hub. Contul și setările tale sunt păstrate.',
      timeout:'Pregătirea durează mai mult. Verifică accesul la internet, apoi reîncearcă.',
      failure:'Browserul nu a putut pregăti redarea protejată. Reîncearcă sau revino în hub.',
      unavailable:'Hubul nu este disponibil. Reîncearcă după recuperarea lui.',
      offline:'Nu există conexiune la rețea. Reconectează-te, apoi reîncearcă.',
      back:'Revino în hub', retry:'Reîncearcă', leaving:'Se revine în hub…', invalid:'Această sesiune de pregătire s-a încheiat.'
    }
  };
  function render(state='checking', error) {
    document.documentElement.lang = language;
    document.documentElement.dataset.theme = theme;
    const words = text[language];
    node('heading').textContent = words[state] || words.title;
    node('description').textContent = words.description;
    node('notice').textContent = navigator.onLine === false ? words.offline : error === 'protected_playback_timeout' ? words.timeout : error === 'stale_preparation' ? words.invalid : error ? words.failure : words.pending;
    node('back').textContent = '← ' + words.back;
    node('retry').textContent = words.retry;
    node('retry').hidden = !error;
  }
  async function api(path, data) {
    if (!token) {
      const response = await fetch('/api/session', {cache:'no-store', signal:AbortSignal.timeout(5000)});
      if (!response.ok) throw Error('hub_unavailable');
      token = (await response.json()).token;
    }
    const response = await fetch(path, {method:data ? 'POST' : 'GET', cache:'no-store',
      headers:data ? {'Content-Type':'application/json','X-Hub-Token':token} : {},
      body:data ? JSON.stringify(data) : undefined, signal:AbortSignal.timeout(5000)});
    const result = await response.json();
    if (!response.ok) { if (response.status === 403) token = undefined; throw Error(result.error || 'hub_unavailable'); }
    return result;
  }
  async function capability() {
    try {
      const operation = (async () => {
        const access = await navigator.requestMediaKeySystemAccess('com.widevine.alpha', [{
          initDataTypes:['cenc'], audioCapabilities:[{contentType:'audio/mp4; codecs="mp4a.40.2"'}],
          videoCapabilities:[{contentType:'video/mp4; codecs="avc1.42E01E"'}]
        }]);
        await access.createMediaKeys();
        return true;
      })();
      return await Promise.race([operation, new Promise(resolve => setTimeout(() => resolve(false), 6000))]);
    } catch { return false; }
  }
  async function refresh() {
    if (stopped || refreshing) return;
    refreshing = true;
    clearTimeout(timer);
    try {
      const state = await api('/api/external/preparation?job=' + encodeURIComponent(job));
      if (stopped) return;
      language = state.language === 'ro' ? 'ro' : 'en';
      theme = state.theme === 'night' ? 'night' : 'ink';
      node('service').textContent = {netflix:'Netflix',spotify:'Spotify',youtube:'YouTube'}[state.service] || '';
      render(state.state, state.error);
      // A restarted browser has a new attempt. This old page cannot report for it.
      if (state.attempt !== attempt) return;
      if (state.state === 'checking' && probeAttempt !== attempt) {
        probeAttempt = attempt;
        const ready = await capability();
        if (!stopped) await api('/api/external/report', {job,attempt,ready});
      }
      if (!stopped && state.state === 'ready') {
        const allowed = {netflix:'https://www.netflix.com',spotify:'https://open.spotify.com'};
        if (allowed[state.service] !== state.url) throw Error('stale_preparation');
        stopped = true;
        location.replace(state.url);
      }
    } catch (error) {
      if (!stopped) {
        render('error', error.message);
        if (error.message !== 'protected_playback_timeout' && error.message !== 'stale_preparation') node('notice').textContent = text[language].unavailable;
      }
    } finally {
      refreshing = false;
      if (!stopped) timer = setTimeout(refresh, 1000);
    }
  }
  node('retry').addEventListener('click', async () => {
    node('retry').disabled = true;
    try { await api('/api/external/retry', {job}); probeAttempt = undefined; await refresh(); }
    catch(error) { render('error',error.message); }
    finally { node('retry').disabled = false; }
  });
  node('back').addEventListener('click', async () => {
    stopped = true; clearTimeout(timer);
    node('back').disabled = true; node('heading').textContent = text[language].leaving;
    try { await api('/api/external/cancel', {job}); }
    catch(error) { stopped = false; node('back').disabled = false; render('error',error.message); timer = setTimeout(refresh,1000); }
  });
  window.addEventListener('pagehide', () => { stopped = true; clearTimeout(timer); });
  render();
  if (valid(job) && valid(attempt)) void refresh();
  else render('error','stale_preparation');
})();
