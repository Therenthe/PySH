// Read-only provider pages. Persistent owned-window return; never observes account fields or typed values.
(() => {
 const host=document.createElement('pi-hub-documentation-return'),shadow=host.attachShadow({mode:'closed'});
 host.style.cssText='all:initial;position:fixed;right:12px;top:12px;z-index:2147483647;display:block';
 const button=document.createElement('button'),feedback=document.createElement('span');let ro=false;
 button.style.cssText='all:initial;box-sizing:border-box;display:block;min-height:48px;min-width:160px;padding:12px 16px;background:#f7f5ee;color:#18261e;border:2px solid #18261e;border-radius:12px;font:600 16px/20px system-ui;cursor:pointer;touch-action:manipulation';
 feedback.style.cssText='position:absolute;right:0;top:56px;box-sizing:border-box;display:none;width:280px;max-width:calc(100vw - 24px);padding:12px;background:#f7f5ee;color:#18261e;font:500 14px/20px system-ui';feedback.setAttribute('role','status');
 const localize=()=>{button.textContent=ro?'← Înapoi la PySH':'← Back to PySH';};
 button.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();chrome.runtime.sendMessage({action:'return'});});
 shadow.append(button,feedback);const attach=()=>{if(!host.isConnected&&document.documentElement)document.documentElement.append(host);};attach();document.addEventListener('DOMContentLoaded',attach,{once:true});
 const allowed=value=>{try{return ['https://open-meteo.com','https://creativecommons.org'].includes(new URL(value,location.href).origin);}catch{return false;}};
 const reject=()=>{feedback.textContent=ro?'Acest link nu poate fi deschis în PySH. Poți reveni la hub.':'This link cannot be opened in PySH. You can return to the hub.';feedback.style.display='block';};
 const links=event=>{const anchor=event.target.closest?.('a[href]');if(!anchor)return;event.preventDefault();event.stopImmediatePropagation();if(allowed(anchor.href))location.assign(anchor.href);else reject();};
 document.addEventListener('click',links,true);document.addEventListener('auxclick',links,true);
 document.addEventListener('submit',event=>{const form=event.target;if(!allowed(form.action)){event.preventDefault();event.stopImmediatePropagation();reject();}},true);
 localize();chrome.runtime.sendMessage({action:'status'},result=>{if(!chrome.runtime.lastError){ro=result?.language==='ro';localize();}});
})();
