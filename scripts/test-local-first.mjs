globalThis.window=globalThis;
globalThis.localStorage={
  _x:new Map(),
  getItem(k){return this._x.has(k)?this._x.get(k):null},
  setItem(k,v){this._x.set(k,String(v))},
  removeItem(k){this._x.delete(k)}
};
Object.defineProperty(globalThis,"navigator",{value:{onLine:false},writable:true,configurable:true});
await import("../frontend/js/forge_local_workout.js");
const F=globalThis.ForgeLocalWorkout;
const calls=[];
const send=async(path,opt)=>{
  const body=JSON.parse(opt.body||"{}");calls.push({path,body});
  if(path.includes("/start"))return {session_id:77,status:"active"};
  return {status:"ok"};
};
const started=await F.start(send,{workoutId:12,workoutIndex:1,workoutSnapshot:{workout_id:12,name:"Pull"}});
if(!F.isLocalOnly(started.session))throw new Error("Offline start did not create provisional session");
await F.mutate(send,"/me/performance",{method:"POST",body:JSON.stringify({request_id:"set-1",session_id:F.sessionRef(started.session),exercise_id:4,completed_sets:1,difficulty:8,reps:[8],weight:100,load_mode:"weight"})},{local_session_id:F.sessionRef(started.session),workout_id:12,kind:"set"});
await F.mutate(send,"/me/session/position",{method:"POST",body:JSON.stringify({session_id:F.sessionRef(started.session),exercise_index:0,set_index:1})},{local_session_id:F.sessionRef(started.session),workout_id:12,kind:"position"});
if(await F.pendingCount()!==3)throw new Error("Expected start/set/position to be persisted offline");
navigator.onLine=true;
const result=await F.sync(send);
if(result.status!=="synced"||result.pending!==0)throw new Error("Replay did not fully sync");
if(calls.length!==3)throw new Error(`Expected 3 server calls, got ${calls.length}`);
if(calls[1].body.session_id!==77||calls[2].body.session_id!==77)throw new Error("Dependent operations did not map provisional session ID");
const active=await F.activeSession();
if(active.server_session_id!==77)throw new Error("Local session was not mapped to server session");
console.log("Local-first offline start → set → position → reconnect replay passed.");
