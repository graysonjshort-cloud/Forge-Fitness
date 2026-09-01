window.ForgeProduction=(()=>{
const VERSION="15.10.1";
function boot(){
 document.documentElement.dataset.forgeVersion=VERSION;
 addEventListener("error",e=>console.error("Forge runtime error",e.error||e.message));
 addEventListener("unhandledrejection",e=>console.error("Forge async error",e.reason));
 if("serviceWorker" in navigator)navigator.serviceWorker.ready.then(r=>{
  if(r.waiting)document.documentElement.dataset.updateReady="true";
 }).catch(()=>{});
}
function status(){return {version:VERSION,online:navigator.onLine,standalone:window.ForgeMobile?.standalone?.()||false,pending_offline:window.ForgeOffline?.count?.()||0}}
return {boot,status};
})();
document.readyState==="loading"?document.addEventListener("DOMContentLoaded",ForgeProduction.boot,{once:true}):ForgeProduction.boot();