window.ForgeNotifications=(()=>{
const SEEN="forge_notification_seen_v1";
const seen=()=>{try{return JSON.parse(localStorage.getItem(SEEN)||"{}")}catch{return {}}};
const save=x=>localStorage.setItem(SEEN,JSON.stringify(x));
async function permission(){if(window.ForgeNative?.isNative&&window.ForgeDeviceServices?.requestNotificationPermission)return ForgeDeviceServices.requestNotificationPermission();
 if(!("Notification" in window))return "unsupported";
 if(Notification.permission==="granted")return "granted";
 return await Notification.requestPermission();
}
async function deliver(items=[]){
if(window.ForgeNative?.isNative&&window.ForgeDeviceServices?.notify){
 const s=seen(); for(const n of items){if(!n?.key||s[n.key])continue;await ForgeDeviceServices.notify({id:Math.abs([...String(n.key)].reduce((a,c)=>(a*31+c.charCodeAt(0))|0,7)),title:n.title||"Forge",body:n.message||"",route:n.route||"notifications"});s[n.key]=Date.now()} save(s); return;
}
 if(!("Notification" in window)||Notification.permission!=="granted")return {shown:0};
 const map=seen(),now=Date.now();let shown=0;
 for(const n of items){
  if(map[n.key])continue;
  try{
   const reg=await navigator.serviceWorker?.ready;
   if(reg?.showNotification)await reg.showNotification(n.title,{body:n.message,tag:n.key,renotify:false,data:{route:"notifications"}});
   else new Notification(n.title,{body:n.message,tag:n.key});
   map[n.key]=now;shown++;
  }catch{}
 }
 Object.keys(map).forEach(k=>{if(now-map[k]>7*86400000)delete map[k]});
 save(map);return {shown};
}
return {permission,deliver};
})();