// Owned extension recovery page only. No account data or raw extension errors.
(() => {
 const button=document.getElementById('return');let ro=false;
 const feedback=document.createElement('p');feedback.setAttribute('role','status');feedback.hidden=true;button.after(feedback);
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
 function showReturnResult(){feedback.hidden=!returnFailed;feedback.textContent=returnFailed?(ro?'Revenirea la PySH nu a reușit. Reîncearcă.':'Could not return to PySH. Try again.'):'';}
 function localize(){button.disabled=returnPending;button.setAttribute('aria-busy',String(returnPending));button.textContent=returnPending?(ro?'Se revine…':'Returning…'):returnFailed?(ro?'Reîncearcă revenirea':'Retry return'):(ro?'Înapoi la PySH':'Back to PySH');if(returnFailed)showReturnResult();}
 button.addEventListener('click',requestReturn);
 localize();chrome.runtime.sendMessage({action:'status'},result=>{if(!chrome.runtime.lastError&&result?.language==='ro'){ro=true;document.documentElement.lang='ro';document.getElementById('title').textContent='Documentația nu este disponibilă';document.getElementById('message').textContent='Pagina nu a putut fi deschisă în siguranță. Revino la PySH sau încearcă o sursă acceptată.';localize();}});
})();
