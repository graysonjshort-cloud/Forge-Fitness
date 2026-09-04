(()=>{
const KEY="forge_active_workout_state_v3";
const num=v=>Number.isFinite(Number(v))?Number(v):0;
const sid=v=>{const s=String(v??"");return /^\d+$/.test(s)?Number(s):s};
function read(){try{return JSON.parse(localStorage.getItem(KEY)||"null")}catch{return null}}
function write(x){try{localStorage.setItem(KEY,JSON.stringify({...x,saved_at:Date.now()}));return true}catch{return false}}
function clear(){try{localStorage.removeItem(KEY);localStorage.removeItem("forge_active_workout_state_v2")}catch{}}
function snapshot({sessionId,workoutId,exerciseId,exerciseIndex,setIndex,setGoal,restRemaining=0,restTotal=0,restContext=null}){
 if(!sessionId||!workoutId)return false;
 return write({session_id:sid(sessionId),workout_id:num(workoutId),exercise_id:num(exerciseId),exercise_index:Math.max(0,num(exerciseIndex)),set_index:Math.max(0,num(setIndex)),set_goal:Math.max(1,num(setGoal)||1),rest_remaining:Math.max(0,num(restRemaining)),rest_total:Math.max(0,num(restTotal)),rest_context:restContext||null});
}
function sameImmutable(x,{sessionId,workoutId}){return !!x&&String(x.session_id)===String(sid(sessionId))&&num(x.workout_id)===num(workoutId)}
function clampSet(setIndex,setGoal){return Math.max(0,Math.min(num(setIndex),Math.max(0,num(setGoal)-1)))}
function recoverContext({sessionId,workoutId,exerciseId}){
 const x=read(); if(!sameImmutable(x,{sessionId,workoutId}))return null;
 if(exerciseId&&num(x.exercise_id)!==num(exerciseId))return null;
 return x;
}
window.ForgeWorkoutState={read,clear,snapshot,sameImmutable,clampSet,recoverContext};
})();