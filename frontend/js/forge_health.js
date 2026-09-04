window.ForgeHealthUI=(()=>{
function system(h,esc){
 if(!h)return `<div class=card><p class=eyebrow>SYSTEM HEALTH</p><h3>Checking Forge…</h3></div>`;
 const checks=Object.entries(h.checks||{});
 return `<div class="card system-health ${h.status}"><div class=row><div><p class=eyebrow>PRODUCTION HEALTH</p><h3>${h.status==="ok"?"All core systems operational":"Forge needs attention"}</h3></div><b>${h.status==="ok"?"✓":"!"}</b></div><div class=system-check-grid>${checks.map(([k,v])=>`<span><i>${v===true?"✓":v===false?"!":"•"}</i>${esc(k.replaceAll("_"," "))}</span>`).join("")}</div>${h.persistence?`<small>Persistence: ${esc(h.persistence)}</small>`:""}</div>`;
}
function session(d,esc){
 if(!d)return "";
 const x=d.active_session||{};
 return `<div class=card><p class=eyebrow>PRODUCTION DIAGNOSTICS</p><h3>${d.status==="ok"?"Workout state healthy":"Workout state needs review"}</h3><p class=muted>${d.stale_active_sessions} stale sessions • ${d.duplicate_active_workouts} duplicate active workouts</p><small>${x.status==="ok"?`Active: ${esc(x.workout_name||"Workout")} • exercise ${Number(x.current_exercise_index||0)+1}`:"No active session mismatch detected."}</small></div>`;
}
function integrity(d,esc){
 if(!d)return `<div class=card><p class=eyebrow>FORGE HEALTH CHECK</p><h3>Checking data…</h3></div>`;
 const n=(d.issues||[]).reduce((a,x)=>a+x.count,0);
 return `<div class=card><div class=row><div><p class=eyebrow>FORGE HEALTH CHECK</p><h3>${d.status==="healthy"?"Data integrity healthy":`${n} issue${n===1?"":"s"} detected`}</h3></div>${d.repairable_count?`<button class="btn dark compact" data-a=repair-integrity>Repair Safe Issues</button>`:""}</div><p class=muted>${d.review_count?`${d.review_count} item${d.review_count===1?"":"s"} require review. `:""}Forge never rewrites training history or chooses between conflicting valid programs automatically.</p>${(d.issues||[]).map(x=>`<div class=health-row><b>${esc(x.code.replaceAll("_"," "))}</b><span>${x.count} • ${x.repairable?"safe repair":"review"}</span></div>`).join("")}</div>`;
}
return {system,session,integrity};
})();