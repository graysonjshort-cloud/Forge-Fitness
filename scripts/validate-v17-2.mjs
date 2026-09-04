import fs from "node:fs";
const must=[
 "frontend/js/forge_local_workout.js","frontend/js/forge_workout_state.js",
 "frontend/app.js","frontend/js/forge_workout_runtime.js","frontend/index.html"
];
for(const f of must)if(!fs.existsSync(f))throw new Error(`Missing ${f}`);
const local=fs.readFileSync("frontend/js/forge_local_workout.js","utf8");
for(const token of ["indexedDB.open","session_map","kind===\"start\"","request_key","bootstrapSnapshot","mutate(send","markComplete"])
 if(!local.includes(token))throw new Error(`Local runtime missing ${token}`);
const app=fs.readFileSync("frontend/app.js","utf8");
for(const token of ["localFirst:true","syncLocalWorkoutWrites","ForgeLocalWorkout.start","bootstrapSnapshot","ForgeLocalWorkout?.sessionRef"])
 if(!app.includes(token))throw new Error(`App integration missing ${token}`);
if(app.includes('api("/me/performance",{method:"POST",queueable:true'))throw new Error("Performance still uses legacy offline-only queue");
const runtime=fs.readFileSync("frontend/js/forge_workout_runtime.js","utf8");
if(!runtime.includes('localKind:"swap"'))throw new Error("Workout swap is not local-first");
const html=fs.readFileSync("frontend/index.html","utf8");
if(html.indexOf("forge_local_workout.js")<0||html.indexOf("forge_local_workout.js")>html.indexOf("forge_native_bootstrap.js"))throw new Error("Local runtime startup order invalid");
console.log("Forge v17.2 Local-First Workout Runtime validation passed.");
