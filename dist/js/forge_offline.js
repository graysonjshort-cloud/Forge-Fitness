// Forge Fitness v15.3 — idempotent offline workout write queue.
window.ForgeOffline=(()=>{
const KEY="forge_offline_workout_queue_v1";
const load=()=>{try{return JSON.parse(localStorage.getItem(KEY)||"[]")}catch{return []}};
const save=q=>localStorage.setItem(KEY,JSON.stringify(q));
const count=()=>load().length;
function enqueue(path,opt={},meta={}){
 const q=load(), body=typeof opt.body==="string"?opt.body:JSON.stringify(opt.body||{});
 let parsed={};try{parsed=JSON.parse(body||"{}")}catch{}
 const key=parsed.request_id||`${path}:${parsed.session_id||""}:${meta.sequence||Date.now()}`;
 if(q.some(x=>x.key===key))return {queued:true,key,pending:q.length};
 q.push({key,path,method:(opt.method||"POST").toUpperCase(),body,created_at:Date.now(),meta});
 save(q);return {queued:true,key,pending:q.length};
}
async function replay(send,{validate}={}){
 let q=load(),done=0;
 while(q.length){
  const item=q[0];
  if(validate){
   const ok=await validate(item);
   if(!ok)return {status:"blocked",replayed:done,pending:q.length,reason:"session_changed"};
  }
  try{
   await send(item.path,{method:item.method,body:item.body,__offlineReplay:true});
   q.shift();save(q);done++;
  }catch(e){
   return {status:"paused",replayed:done,pending:q.length,error:e?.message||String(e)};
  }
 }
 return {status:"synced",replayed:done,pending:0};
}
function clear(){save([])}
async function request(baseRequest,API,tokenFn,state,path,opt={},meta={}){
 const method=(opt.method||"GET").toUpperCase();
 if(method!=="GET"&&opt.queueable&&navigator.onLine===false&&!opt.__offlineReplay)return enqueue(path,opt,meta);
 try{return await baseRequest(API,tokenFn,state,path,opt)}catch(e){
  if(method==="GET"&&navigator.onLine!==false&&!opt.__retried){await new Promise(r=>setTimeout(r,180));return baseRequest(API,tokenFn,state,path,{...opt,__retried:true})}
  if(method!=="GET"&&opt.queueable&&!opt.__offlineReplay&&(!navigator.onLine||/network|fetch|offline/i.test(e?.message||"")))return enqueue(path,opt,meta);
  throw e;
 }
}
function banner(){const n=count();return `<div class=network-banner role=status><b>Offline — workout is still being saved</b><span>${n?`${n} change${n===1?"":"s"} waiting to sync.`:"Set logging will queue safely until you reconnect."}</span></div>`}
return {enqueue,replay,request,banner,count,clear,items:load};
})();