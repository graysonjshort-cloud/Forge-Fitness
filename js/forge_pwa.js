(function(global){
  "use strict";
  function create({state,toast,render}){
    const isStandalonePWA=()=>global.matchMedia?.("(display-mode: standalone)")?.matches || global.navigator.standalone===true;
    const isIOSDevice=()=>/iphone|ipad|ipod/i.test(global.navigator.userAgent||"");
    function pwaInstallCard(){
      if(isStandalonePWA()||state.pwaInstalled)return `<div class="card pwa-install-card installed"><div class=pwa-install-icon>✓</div><div><p class=eyebrow>PHONE APP</p><h3>Forge is installed</h3><p class=muted>Forge is running as a standalone home-screen app.</p></div></div>`;
      if(isIOSDevice())return `<div class="card pwa-install-card apple-pwa-card"><div class=pwa-install-icon></div><div><p class=eyebrow>IPHONE / IPAD</p><h3>Install Forge on Apple</h3><p class=muted>Open Forge in Safari, tap <b>Share</b>, choose <b>Add to Home Screen</b>, turn on <b>Open as Web App</b>, then tap <b>Add</b>.</p><div class=apple-install-steps><span>1</span><b>Share</b><span>2</span><b>Add to Home Screen</b><span>3</span><b>Open as Web App</b></div></div></div>`;
      if(state.pwaInstallPrompt)return `<div class="card pwa-install-card"><div class=pwa-install-icon>⌂</div><div><p class=eyebrow>ANDROID APP</p><h3>Install Forge</h3><p class=muted>Add Forge to your home screen and open it like a normal app.</p><button class=btn data-a=pwa-install>Install Forge</button></div></div>`;
      return `<div class="card pwa-install-card"><div class=pwa-install-icon>⌂</div><div><p class=eyebrow>PHONE APP</p><h3>Install Forge</h3><p class=muted>Use your browser's Install app option. On iPhone/iPad, use Safari → Share → Add to Home Screen.</p></div></div>`;
    }
    async function installForgePWA(){
      const prompt=state.pwaInstallPrompt;
      if(!prompt){toast(isIOSDevice()?"Use Safari Share → Add to Home Screen":"Install option is not available in this browser yet");return;}
      prompt.prompt();
      const choice=await prompt.userChoice.catch(()=>({outcome:"dismissed"}));
      if(choice.outcome==="accepted")toast("Forge installation started");
      state.pwaInstallPrompt=null;render();
    }
    function setupPWA(){
      state.pwaInstalled=isStandalonePWA();
      document.documentElement.classList.toggle("ios-device",isIOSDevice());
      document.documentElement.classList.toggle("standalone-pwa",isStandalonePWA());
      global.addEventListener("beforeinstallprompt",event=>{event.preventDefault();state.pwaInstallPrompt=event;if(state.route==="trainingsettings")render();});
      global.addEventListener("appinstalled",()=>{state.pwaInstalled=true;state.pwaInstallPrompt=null;toast("Forge installed");if(state.route==="trainingsettings")render();});
      if("serviceWorker" in navigator){
        navigator.serviceWorker.register("/sw.js",{scope:"/"}).then(reg=>{
          reg.addEventListener("updatefound",()=>{
            const worker=reg.installing;if(!worker)return;
            worker.addEventListener("statechange",()=>{if(worker.state==="installed"&&navigator.serviceWorker.controller){state.updateReady=true;render();}});
          });
        }).catch(err=>console.warn("Forge service worker registration failed",err));
      }
      global.addEventListener("online",()=>{state.online=true;render();toast("Forge is back online")});
      global.addEventListener("offline",()=>{state.online=false;render()});
    }
    return Object.freeze({isStandalonePWA,isIOSDevice,pwaInstallCard,installForgePWA,setupPWA});
  }
  global.ForgePWA=Object.freeze({create});
})(globalThis);
