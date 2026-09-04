(function () {
  "use strict";
  const DB_NAME="forge_local_workout";
  const DB_VERSION=1;
  const FALLBACK_KEY="forge_local_workout_fallback_v1";

  const uid=()=>globalThis.crypto?.randomUUID?.()||`local-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const clone=x=>x==null?x:JSON.parse(JSON.stringify(x));

  function fallbackLoad(){
    try{return JSON.parse(localStorage.getItem(FALLBACK_KEY)||'{"kv":{},"journal":[]}')}catch{return {kv:{},journal:[]}}
  }
  function fallbackSave(x){localStorage.setItem(FALLBACK_KEY,JSON.stringify(x))}
  function openDB(){
    return new Promise((resolve,reject)=>{
      if(!("indexedDB" in globalThis)){resolve(null);return}
      const req=indexedDB.open(DB_NAME,DB_VERSION);
      req.onupgradeneeded=()=>{
        const db=req.result;
        if(!db.objectStoreNames.contains("kv"))db.createObjectStore("kv",{keyPath:"key"});
        if(!db.objectStoreNames.contains("journal"))db.createObjectStore("journal",{keyPath:"id"});
      };
      req.onsuccess=()=>resolve(req.result);
      req.onerror=()=>reject(req.error);
    });
  }
  async function kvGet(key){
    try{
      const db=await openDB(); if(!db){return fallbackLoad().kv[key]??null}
      return await new Promise((resolve,reject)=>{
        const r=db.transaction("kv","readonly").objectStore("kv").get(key);
        r.onsuccess=()=>resolve(r.result?.value??null);r.onerror=()=>reject(r.error);
      });
    }catch{return fallbackLoad().kv[key]??null}
  }
  async function kvSet(key,value){
    try{
      const db=await openDB(); if(!db)throw 0;
      await new Promise((resolve,reject)=>{
        const r=db.transaction("kv","readwrite").objectStore("kv").put({key,value:clone(value)});
        r.onsuccess=()=>resolve();r.onerror=()=>reject(r.error);
      }); return;
    }catch{
      const f=fallbackLoad();f.kv[key]=clone(value);fallbackSave(f);
    }
  }
  async function journalAll(){
    try{
      const db=await openDB(); if(!db)return fallbackLoad().journal||[];
      return await new Promise((resolve,reject)=>{
        const r=db.transaction("journal","readonly").objectStore("journal").getAll();
        r.onsuccess=()=>resolve((r.result||[]).sort((a,b)=>a.sequence-b.sequence));r.onerror=()=>reject(r.error);
      });
    }catch{return (fallbackLoad().journal||[]).sort((a,b)=>a.sequence-b.sequence)}
  }
  async function journalPut(item){
    try{
      const db=await openDB(); if(!db)throw 0;
      await new Promise((resolve,reject)=>{
        const r=db.transaction("journal","readwrite").objectStore("journal").put(clone(item));
        r.onsuccess=()=>resolve();r.onerror=()=>reject(r.error);
      }); return;
    }catch{
      const f=fallbackLoad(),i=f.journal.findIndex(x=>x.id===item.id);
      if(i>=0)f.journal[i]=clone(item);else f.journal.push(clone(item));fallbackSave(f);
    }
  }
  async function journalDelete(id){
    try{
      const db=await openDB(); if(!db)throw 0;
      await new Promise((resolve,reject)=>{
        const r=db.transaction("journal","readwrite").objectStore("journal").delete(id);
        r.onsuccess=()=>resolve();r.onerror=()=>reject(r.error);
      }); return;
    }catch{
      const f=fallbackLoad();f.journal=(f.journal||[]).filter(x=>x.id!==id);fallbackSave(f);
    }
  }
  async function pendingCount(){return (await journalAll()).length}

  async function cacheBootstrap({account,profile,plan}={}){
    if(account)await kvSet("account",account);
    if(profile)await kvSet("profile",profile);
    if(plan)await kvSet("plan",plan);
  }
  async function bootstrapSnapshot(){
    return {account:await kvGet("account"),profile:await kvGet("profile"),plan:await kvGet("plan"),session:await kvGet("active_session")};
  }
  async function cachePlan(plan){if(plan)await kvSet("plan",plan)}
  async function activeSession(){return await kvGet("active_session")}
  async function saveActive(s){await kvSet("active_session",s)}
  async function clearActive(){await kvSet("active_session",null)}

  async function mapping(){
    return (await kvGet("session_map"))||{};
  }
  async function mapSession(localId,serverId){
    const m=await mapping();m[localId]=Number(serverId);await kvSet("session_map",m);
    const a=await activeSession();
    if(a&&a.local_session_id===localId){a.server_session_id=Number(serverId);a.session_id=Number(serverId);await saveActive(a)}
  }
  async function resolveSession(ref){
    if(ref==null)return ref;
    if(typeof ref==="number"||/^\d+$/.test(String(ref)))return Number(ref);
    const m=await mapping();return m[ref]||null;
  }

  async function append(path,opt={},meta={}){
    const body=typeof opt.body==="string"?(opt.body||"{}"):JSON.stringify(opt.body||{});
    let parsed={};try{parsed=JSON.parse(body)}catch{}
    const requestKey=parsed.request_id||meta.request_id||null;
    const existing=await journalAll();
    if(requestKey){
      const dup=existing.find(x=>x.request_key===requestKey);
      if(dup)return dup;
    }
    const item={
      id:uid(), sequence:Date.now()*1000+Math.floor(Math.random()*1000),
      path,method:(opt.method||"POST").toUpperCase(),body,
      local_session_id:meta.local_session_id||null,
      workout_id:Number(meta.workout_id||0)||null,
      kind:meta.kind||"mutation",request_key:requestKey,created_at:Date.now()
    };
    await journalPut(item);return item;
  }

  async function sync(send){
    if(navigator.onLine===false)return {status:"offline",replayed:0,pending:await pendingCount(),responses:{}};
    const items=await journalAll(),responses={},m=await mapping();let replayed=0;
    for(const item of items){
      let body={};try{body=JSON.parse(item.body||"{}")}catch{}
      if(item.kind==="start"){
        try{
          const result=await send(item.path,{method:item.method,body:item.body,__localReplay:true});
          if(!result?.session_id)throw Error("Workout start did not return a session ID");
          if(item.local_session_id){m[item.local_session_id]=Number(result.session_id);await kvSet("session_map",m);await mapSession(item.local_session_id,result.session_id)}
          responses[item.id]=result;await journalDelete(item.id);replayed++;continue;
        }catch(e){return {status:"paused",replayed,pending:(await pendingCount()),error:e?.message||String(e),responses}}
      }
      if(body.session_id!=null && typeof body.session_id!=="number"){
        const sid=m[body.session_id]||await resolveSession(body.session_id);
        if(!sid)return {status:"blocked",replayed,pending:await pendingCount(),reason:"session_mapping_missing",responses};
        body.session_id=sid;
      }
      try{
        const result=await send(item.path,{method:item.method,body:JSON.stringify(body),__localReplay:true});
        responses[item.id]=result;await journalDelete(item.id);replayed++;
      }catch(e){
        return {status:"paused",replayed,pending:await pendingCount(),error:e?.message||String(e),responses};
      }
    }
    return {status:"synced",replayed,pending:0,responses};
  }

  async function start(send,{workoutId,workoutIndex=0,workoutSnapshot=null}){
    const localId=`local:${uid()}`;
    const session={
      session_id:localId,local_session_id:localId,server_session_id:null,
      workout_id:Number(workoutId),workout_index:Number(workoutIndex)||0,
      exercise_index:0,set_index:0,status:"active",started_at:new Date().toISOString(),
      workout_snapshot:clone(workoutSnapshot)
    };
    await saveActive(session);
    const item=await append(`/me/workout/${workoutId}/start`,{method:"POST",body:"{}"},{local_session_id:localId,workout_id:workoutId,kind:"start"});
    if(navigator.onLine!==false){
      const r=await sync(send),result=r.responses[item.id];
      const active=await activeSession();
      return {session:active||session,result:result||{queued:true,local:true},sync:r};
    }
    return {session,result:{queued:true,local:true},sync:{status:"offline"}};
  }

  async function mutate(send,path,opt={},meta={}){
    const item=await append(path,opt,meta);
    if(navigator.onLine===false)return {queued:true,local:true,operation_id:item.id,pending:await pendingCount()};
    const r=await sync(send);
    return r.responses[item.id] ?? {queued:true,local:true,operation_id:item.id,pending:r.pending,status:r.status};
  }

  async function updatePosition({exerciseIndex,setIndex,restRemaining,restTotal,restContext}){
    const a=await activeSession();if(!a)return;
    a.exercise_index=Math.max(0,Number(exerciseIndex)||0);
    a.set_index=Math.max(0,Number(setIndex)||0);
    if(restRemaining!=null)a.rest_remaining=Math.max(0,Number(restRemaining)||0);
    if(restTotal!=null)a.rest_total=Math.max(0,Number(restTotal)||0);
    if(restContext!==undefined)a.rest_context=clone(restContext);
    await saveActive(a);
  }
  async function markComplete(){
    const a=await activeSession();if(a){a.status="completed_local";a.completed_at=new Date().toISOString();await saveActive(a)}
  }
  async function adoptServerSession({sessionId,workoutId,workoutIndex=0,exerciseIndex=0,setIndex=0,workoutSnapshot=null}){
    const localId=`server:${Number(sessionId)}`;
    const s={session_id:Number(sessionId),local_session_id:localId,server_session_id:Number(sessionId),workout_id:Number(workoutId),workout_index:Number(workoutIndex)||0,exercise_index:Number(exerciseIndex)||0,set_index:Number(setIndex)||0,status:"active",started_at:new Date().toISOString(),workout_snapshot:clone(workoutSnapshot)};
    await mapSession(localId,sessionId);await saveActive(s);return s;
  }
  function sessionRef(session){return session?.local_session_id||session?.session_id||null}
  function isLocalOnly(session){return !!session&&typeof session.session_id==="string"&&session.session_id.startsWith("local:")&&!session.server_session_id}

  window.ForgeLocalWorkout={DB_NAME,DB_VERSION,cacheBootstrap,bootstrapSnapshot,cachePlan,activeSession,clearActive,start,mutate,sync,pendingCount,updatePosition,markComplete,adoptServerSession,mapSession,resolveSession,sessionRef,isLocalOnly};
})(globalThis);
