window.ForgeNotifications=(()=>{
const SEEN="forge_notification_seen_v1";
const seen=()=>{try{return JSON.parse(localStorage.getItem(SEEN)||"{}")}catch{return {}}};
const save=x=>localStorage.setItem(SEEN,JSON.stringify(x));
async function permission(){
 if(!("Notification" in window))return "unsupported";
 if(Notification.permission==="granted")return "granted";
 return await Notification.requestPermission();
}
async function deliver(items=[]){
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