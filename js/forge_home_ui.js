// Forge Fitness v15.11.0 — extracted loadNotifications..before moduleExerciseTarget
async function loadNotifications(force=false){if(!force&&S.notifications)return;try{const d=await api("/me/notifications");S.notifications=d;S.notificationSettings=d.settings;if(d.settings?.browser_notifications)ForgeNotifications.deliver(d.items||[]).catch(()=>{});if(["home","notifications"].includes(S.route))render()}catch(e){}}
function notificationCenter(){return ForgeNotificationUI.center(S.notifications,S.notificationSettings,esc)}
function forgeLocalDate(){
const d=new Date();
return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
}
async function loadHomeDashboard(){
if(!authToken)return;if(S.homeDashboard&&ForgeCache.fresh("home",30000))return;
try{
const [nutrition,intelligence,history]=await Promise.all([
api(`/me/nutrition?date=${encodeURIComponent(forgeLocalDate())}`),
api("/me/progress/intelligence"),
api("/me/history")
]);
S.homeDashboard={nutrition,intelligence,history};ForgeCache.mark("home");
if(S.route==="home")render();
}catch(e){console.warn("Home dashboard load failed",e)}
}
function readinessInfo(){
const fatigue=Number(S.homeDashboard?.intelligence?.metrics?.fatigue_score??S.coachContext?.fatigue_score??0);
if(fatigue>=7)return {label:"Recover",tone:"recover",detail:`Fatigue ${fatigue.toFixed(1)}/10 • keep intensity controlled`};
if(fatigue>=4.5)return {label:"Moderate",tone:"moderate",detail:`Fatigue ${fatigue.toFixed(1)}/10 • train, but watch effort`};
return {label:"Ready",tone:"ready",detail:`Fatigue ${fatigue.toFixed(1)}/10 • good day to execute the plan`};
}
function homeNutritionSnapshot(){
const n=S.homeDashboard?.nutrition;if(!n)return `<div class="home-mini-card skeleton-card"><small>NUTRITION</small><b>Loading…</b></div>`;
const r=n.remaining||{},t=n.targets||{},v=n.totals||{};
const pct=t.calories?Math.min(100,Math.round((v.calories||0)/t.calories*100)):0;
return `<button class=home-mini-card data-nav=nutrition><span class=mini-card-icon>◔</span><span><small>NUTRITION</small><b>${Math.max(0,Math.round(r.calories||0))} kcal left</b><em>${Math.max(0,Math.round(r.protein_g||0))}g protein remaining</em><i><u style="width:${pct}%"></u></i></span></button>`;
}
function floatingRestTimer(){
if(!session||!S.restRemaining||S.route==="timer")return "";
const mm=String(Math.floor(S.restRemaining/60)).padStart(2,"0"),ss=String(S.restRemaining%60).padStart(2,"0");
return `<button class=floating-rest data-a=open-rest><span>REST</span><b id=floatingRestClock>${mm}:${ss}</b><small>tap to manage</small></button>`;
}
function coachMessageHTML(m){
const text=esc(m.text||m.message||"");
if(m.role==="user")return `<div class="bubble user">${text}</div>`;
const low=String(m.text||m.message||"").toLowerCase();
const actions=[];
if(/protein|calorie|macro|meal|food|nutrition/.test(low))actions.push(["nutrition","Open Nutrition"]);
if(/workout|exercise|set|training|move|swap/.test(low))actions.push(["workout","View Workout"]);
if(/progress|strength|plateau|pr\b/.test(low))actions.push(["progress","View Progress"]);
if(/schedule|calendar|day|time/.test(low))actions.push(["plan","View Plan"]);
return `<div class="bubble ai coach-rich-response"><div>${text}</div>${actions.length?`<div class=coach-response-actions>${actions.slice(0,2).map(([r,l])=>`<button data-coach-route="${r}">${l}</button>`).join("")}</div>`:""}</div>`;
}
function progressVisualSummary(){
const workouts=plan?.workouts||[],ms=S.moduleSummary||{},done=workouts.filter(x=>x.status==="completed").length;
const adherence=S.progressIntelligence?.metrics?.adherence_percent;
const muscles={};
workouts.forEach(w=>(w.exercises||[]).forEach(e=>{
const raw=String(e.primary_muscle||"Other");
raw.split(",").map(x=>x.trim()).filter(Boolean).forEach(m=>muscles[m]=(muscles[m]||0)+Number(e.sets||0));
}));
const allMuscles=Object.entries(muscles).sort((a,b)=>b[1]-a[1]),max=allMuscles[0]?.[1]||1;
const coreDone=Number(ms.core_sessions_completed||0),cardioDone=Number(ms.cardio_sessions_completed||0),cardioMin=Number(ms.cardio_minutes_completed||0);
const plannedCore=workouts.filter(w=>w.core_module).length,plannedCardio=workouts.filter(w=>w.cardio_module).length;
return `<div class=progress-visual-grid>
<div class="card progress-consistency-card"><p class=eyebrow>CONSISTENCY</p><div class=consistency-value><b>${adherence==null?"—":Math.round(adherence)+"%"}</b><span>${done}/${workouts.length||0} current-plan workouts complete</span></div><div class=consistency-track><i style="width:${adherence==null?0:Math.min(100,adherence)}%"></i></div></div>
<div class="card module-progress-card"><p class=eyebrow>CORE</p><div class=module-progress-value><b>${coreDone}</b><span>circuits completed</span></div><div class=consistency-track><i style="width:${plannedCore?Math.min(100,coreDone/plannedCore*100):0}%"></i></div><small>${plannedCore} core circuit${plannedCore===1?"":"s"} currently scheduled</small></div>
<div class="card module-progress-card"><p class=eyebrow>CARDIO</p><div class=module-progress-value><b>${cardioDone}</b><span>sessions completed</span></div><div class=consistency-track><i style="width:${plannedCardio?Math.min(100,cardioDone/plannedCardio*100):0}%"></i></div><small>${Math.round(cardioMin)} total cardio min • ${plannedCardio} currently scheduled</small></div>
<div class="card muscle-volume-card expanded-muscle-volume"><div class=muscle-volume-head><div><p class=eyebrow>WEEKLY MUSCLE VOLUME</p><h3>${allMuscles.length} trained muscle groups</h3></div><span>${Object.values(muscles).reduce((a,b)=>a+b,0)} total sets</span></div>
${allMuscles.length?allMuscles.map(([muscle,sets])=>`<div class=volume-row><span>${esc(muscle)}</span><b>${sets} sets</b><i><u style="width:${Math.round(sets/max*100)}%"></u></i></div>`).join(""):`<div class=polished-empty><b>Volume appears after plan generation</b><span>Weekly set distribution will appear here.</span></div>`}
</div>
</div>`;
}
function nutritionMealGroups(entries){
const order=["Breakfast","Lunch","Dinner","Snack","Pre-Workout","Post-Workout","Meal"];
const groups={};(entries||[]).forEach(x=>(groups[x.meal_type||"Meal"]??=[]).push(x));
const keys=[...order.filter(k=>groups[k]),...Object.keys(groups).filter(k=>!order.includes(k))];
if(!keys.length)return `<div class="card polished-empty"><b>Nothing logged yet</b><span>Log a meal to start today’s nutrition.</span><button class="btn dark compact" data-a=nutrition-add>Log Food</button></div>`;
return keys.map(k=>{
const rows=groups[k],cal=rows.reduce((a,x)=>a+Number(x.calories||0),0);
return `<section class=meal-section><div class=meal-section-head><h3>${esc(k)}</h3><span>${Math.round(cal)} kcal</span></div>
${rows.map(x=>`<div class="card nutrition-entry"><div><h3>${esc(x.food_name)}</h3><p class=muted>${x.calories} kcal • P ${Math.round(x.protein_g)}g • C ${Math.round(x.carbs_g)}g • F ${Math.round(x.fat_g)}g</p>${x.source?`<small class=nutrition-source>${esc(x.source)}</small>`:""}</div><div class=nutrition-entry-actions><button data-nutrition-edit="${x.id}">✎</button><button class=nutrition-delete data-nutrition-delete="${x.id}">×</button></div></div>`).join("")}</section>`;
}).join("");
}
function readinessCheckin(){
const ww=w();
if(!ww)return `<h2>Readiness Check-In</h2><p class=muted>No workout selected.</p>`;
const c=S.readinessCheckin||{energy:3,soreness:2,motivation:3,sleep:3,minutes:Number(ww.estimated_minutes||profile.minutes_per_workout||45)};
S.readinessCheckin=c;
const scale=(key,label,low,high)=>`<div class=readiness-field><div class=row><b>${label}</b><span>${c[key]}/5</span></div><div class=readiness-scale>${[1,2,3,4,5].map(v=>`<button class="${Number(c[key])===v?"selected":""}" data-readiness-key="${key}" data-readiness-value="${v}">${v}</button>`).join("")}</div><small>${low} → ${high}</small></div>`;
const planned=Number(ww.estimated_minutes||profile.minutes_per_workout||45);
return `<p class=eyebrow>15-SECOND CHECK-IN</p><h2>How ready are you today?</h2><p class=muted>Forge uses this check-in to adjust today’s session without changing your whole training block.</p><div class=big-spacer></div>
<div class="card readiness-checkin-card">${scale("energy","Energy","Drained","Excellent")}${scale("soreness","Soreness","None","Very sore")}${scale("motivation","Motivation","Low","High")}${scale("sleep","Sleep quality","Poor","Great")}
<div class=readiness-field><div class=row><b>Time available</b><span>${c.minutes} min</span></div><div class=time-choice-grid>${[20,30,45,planned].filter((v,i,a)=>a.indexOf(v)===i).sort((a,b)=>a-b).map(v=>`<button class="${Number(c.minutes)===v?"selected":""}" data-readiness-minutes="${v}">${v===planned?`${v} min • full`:`${v} min`}</button>`).join("")}</div></div></div>
<div class=big-spacer></div><button class=btn data-a=readiness-apply>Adjust Today’s Workout</button><div class=spacer></div><button class="btn dark" data-a=readiness-skip>Run Original Workout</button>`;
}
function computeReadinessAdjustment(){
const ww=w(),c=S.readinessCheckin||{}; if(!ww)return null;
const energy=Number(c.energy||3),soreness=Number(c.soreness||2),motivation=Number(c.motivation||3),sleep=Number(c.sleep||3);
const score=Math.max(1,Math.min(5,((energy+motivation+sleep+(6-soreness))/4)));
const planned=Number(ww.estimated_minutes||profile.minutes_per_workout||45),available=Number(c.minutes||planned);
let mode="normal",setReduction=0,loadCue="Run the planned loads and use your normal RIR targets.";
if(score<2.4){mode="recovery";setReduction=1;loadCue="Keep 2–3 good reps in reserve and avoid grinding today."}
else if(score<3.25){mode="controlled";loadCue="Keep the planned work, but cap effort around RPE 8."}
else if(score>=4.3){mode="push";loadCue="Readiness is high. Execute the plan and progress only if technique stays clean."}
const keepRatio=Math.min(1,available/Math.max(1,planned));
const keepExercises=keepRatio<.95?Math.max(2,Math.ceil((ww.exercises||[]).length*keepRatio)):null;
const reasons=[];
if(score<3.25)reasons.push(`readiness ${score.toFixed(1)}/5`);
if(available<planned)reasons.push(`${available} min available vs ${planned} planned`);
if(!reasons.length)reasons.push(`readiness ${score.toFixed(1)}/5 supports the original session`);
return {score:Number(score.toFixed(1)),mode,setReduction,keepExercises,available,planned,loadCue,reason:reasons.join(" • ")};
}
function applyTodayAdjustment(adj){
const ww=w(); if(!ww||!adj)return;
S.todayAdjustment=adj; S.liveAdjustment=null;
if(adj.keepExercises&&ww.exercises.length>adj.keepExercises)ww.exercises=ww.exercises.slice(0,adj.keepExercises);
if(adj.setReduction>0)ww.exercises.forEach((e,i)=>{ if(i>0)e.sets=Math.max(1,Number(e.sets||1)-adj.setReduction); });
}
function todayAdjustmentBanner(){
const a=S.todayAdjustment;if(!a)return "";
const tone=a.mode==="recovery"?"recover":a.mode==="push"?"ready":"moderate";
return `<div class="card today-adjustment ${tone}"><div class=row><div><p class=eyebrow>TODAY’S ADJUSTMENT</p><h3>${a.mode==="normal"?"Original session":a.mode==="recovery"?"Recovery-biased session":a.mode==="push"?"High-readiness session":"Controlled session"}</h3></div><b>${a.score}/5</b></div><p class=muted>${esc(a.reason)}</p>${a.proposed_changes?.length?`<div class=program-change-preview><p class=eyebrow>PROPOSED CHANGES</p>${a.proposed_changes.map(c=>`<div class=adaptation-note><span><b>${esc(c.area)}</b><small>${esc(c.reason)}</small></span><strong>${esc(c.proposed)}</strong></div>`).join("")}</div>`:""}<small>${esc(a.loadCue)}</small></div>`;
}
async function loadTrainingDashboard(){if(S.trainingDashboard?.loading)return;S.trainingDashboard={loading:true};try{S.trainingDashboard=await api("/me/training-dashboard");if(["home","progress"].includes(S.route))render()}catch(e){console.warn("Training dashboard failed",e)}}
async function loadMuscleDevelopment(){if(S.muscleDevelopmentLoading||S.muscleDevelopment)return;S.muscleDevelopmentLoading=true;try{S.muscleDevelopment=await api("/me/training/muscle-development");if(S.route==="progress")render()}catch(e){console.warn("Muscle development failed",e)}finally{S.muscleDevelopmentLoading=false}}
function muscleDevelopmentCard(){const d=S.muscleDevelopment;if(!d)return "";const rows=(d.muscles||[]).slice(0,8);return `<div class="card muscle-development-card"><div class=row><div><p class=eyebrow>MUSCLE DEVELOPMENT</p><h3>Stimulus + progression</h3></div><b>${d.summary?.needs_review||0} review</b></div><p class=muted>Compares weekly volume with actual exercise progress.</p><div class=muscle-status-grid>${rows.map(x=>`<div><span><b>${esc(x.muscle)}</b><small>${x.actual_sets}/${x.target_sets} sets • ${esc(x.development_status.replaceAll("_"," "))}</small></span><i><u style="width:${Math.min(100,x.percent||0)}%"></u></i><small>${esc(x.recommendation)}</small></div>`).join("")}</div></div>`}
function trainingDashboardCard(){const d=S.trainingDashboard;if(!d||d.loading)return `<div class=card><p class=eyebrow>TRAINING BLOCK</p><h3>Loading block intelligence…</h3></div>`;const m=d.mesocycle||{},top=(d.muscles||[]).slice(0,8);return `<div class="card training-command-card"><div class=row><div><p class=eyebrow>TRAINING DASHBOARD 3.0</p><h3>Block ${m.block_number} • Week ${m.week_in_block}/${m.block_length}</h3></div><b>${esc(String(m.phase||""))}</b></div><p class=muted>${d.week.completed}/${d.week.planned} workouts • ${d.week.adherence_percent}% complete • ${m.fatigue_score}/10 fatigue</p><div class=muscle-status-grid>${top.map(x=>`<div><span><b>${esc(x.muscle)}</b><small>${x.actual_sets}/${x.target_sets} effective sets</small></span><i><u style="width:${Math.min(100,x.percent)}%"></u></i></div>`).join("")}</div><div class=spacer></div><small>Current direction <b>${esc(d.progression_mode)}</b></small></div>`}
function weeklyInsightsCard(){
const workouts=plan?.workouts||[],done=workouts.filter(x=>x.status==="completed").length;
const history=S.homeDashboard?.history||[],intel=S.homeDashboard?.intelligence||{};
const currentWeek=Math.max(1,...history.map(x=>Number(x.week_number||1)));
const weekRows=history.filter(x=>Number(x.week_number||1)===currentWeek&&x.status==="completed");
const volume=Math.round(weekRows.reduce((a,x)=>a+Number(x.total_volume||0),0));
const sets=weekRows.reduce((a,x)=>a+Number(x.total_sets||0),0);
const adherence=intel?.metrics?.adherence_percent;
const strength=(intel.signals||[]).find(x=>x.type==="strength");
const recommendation=(intel.recommendations||[])[0]|| (done>=workouts.length&&workouts.length?"Training week complete — prioritize recovery and nutrition before the next week.":"Keep executing the plan and log every working set so Forge can make better adjustments.");
const last=history.find(x=>x.status==="completed");
return `<div class="card weekly-insights-card"><div class=row><div><p class=eyebrow>THIS WEEK</p><h3>${done>=workouts.length&&workouts.length?"Week complete":"Your training at a glance"}</h3></div><button class="btn dark compact" data-nav=progress>Details</button></div>
<div class=weekly-insight-metrics><span><b>${done}/${workouts.length||0}</b><small>workouts</small></span><span><b>${sets}</b><small>logged sets</small></span><span><b>${volume?volume.toLocaleString():"—"}</b><small>volume lb</small></span><span><b>${adherence==null?"—":Math.round(adherence)+"%"}</b><small>adherence</small></span></div>
${strength?`<div class=insight-signal><span>Strength trend</span><b>${esc(strength.value||"Not enough data")}</b></div>`:""}
<div class=weekly-next-action><small>NEXT BEST ACTION</small><p>${esc(recommendation)}</p></div>${last?`<small class=muted>Last session: ${esc(last.workout_name||"Workout")} • ${Number(last.total_sets||0)} sets</small>`:""}</div>`;
}
function homeQuickActions(todayWorkout){
return `<div class=home-quick-actions><button data-nav=progress><span>↗</span><b>Progress</b><small>See trends & PRs</small></button><button data-nav=nutrition><span>◔</span><b>Nutrition</b><small>Log food quickly</small></button><button data-coach-route=coach><span>✦</span><b>Coach</b><small>Ask or adjust</small></button>${todayWorkout&&todayWorkout.status!=="completed"?`<button data-a=startworkout><span>▶</span><b>Train</b><small>Start check-in</small></button>`:""}</div>`;
}
function home(){
const workouts=plan?.workouts||[];
if(!workouts.length)return yourplan();
const today=(new Date().getDay()+6)%7;
const todayWorkout=workouts.find(w=>Number(w.scheduled_day)===today&&!w.is_skipped)||null;
if(todayWorkout)S.wi=workouts.indexOf(todayWorkout);
const done=workouts.filter(w=>w.status==="completed").length;
const pct=Math.round(done/Math.max(1,workouts.length)*100);
const dayNames=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"];
const readiness=readinessInfo();
const upcoming=workouts.filter(w=>!w.is_skipped&&w.status!=="completed"&&Number(w.scheduled_day)>today).sort((a,b)=>a.scheduled_day-b.scheduled_day).slice(0,2);
const card=todayWorkout?`<div class="card hero-workout ${todayWorkout.status==="completed"?"completed-today":""}">
<div class=copy>
${todayWorkout.status==="completed"
?`<p class=eyebrow>WORKOUT COMPLETE</p><h2>${esc(todayWorkout.name)} finished</h2><p class=muted>Workout complete. Recover and refuel.</p><div class=spacer></div><div class=home-complete-badge>✓ Completed</div>`
:`<p class=eyebrow>PRIMARY ACTION</p><h2>${esc(todayWorkout.name)}</h2><p class=muted>${todayWorkout.exercises.length} exercises • ${esc(todayWorkout.scheduled_time||S.timeSettings?.default_workout_time||"17:00")} • ${todayWorkout.estimated_minutes||profile.minutes_per_workout} min${todayWorkout.core_included?" • Core":""}</p><div class=spacer></div><button class="btn hero-start" data-a=startworkout>Start Today’s Workout</button>`}
${todayWorkout.core_module?`<div class=spacer></div><small>Core: ${todayWorkout.module_status?.core?.status==="completed"?"✓ Complete":"Scheduled"}</small>`:""}${todayWorkout.cardio_module?`<small>Cardio: ${todayWorkout.module_status?.cardio?.status==="completed"?"✓ Complete":"Scheduled"}</small>`:""}
</div>
<div class="workout-status-mark ${todayWorkout.status==="completed"?"done":""}">${todayWorkout.status==="completed"?"✓":"▶"}</div>
</div>`:`<div class="card hero-workout recovery-home"><div class=copy><p class=eyebrow>RECOVERY DAY</p><h2>No workout scheduled today</h2><p class=muted>Recover, refuel, or move a workout here.</p><div class=spacer></div><button class="btn dark" data-coach-route=coach>Ask Forge Coach</button></div></div>`;
return `<div class=row><div><p class=muted>Welcome back,</p><h2>${esc(S.name)}!</h2></div><button class=notification-bell data-a=open-notifications>🔔${S.notifications?.unread_count?`<b>${S.notifications.unread_count}</b>`:""}</button></div>
<div class=spacer></div><div class=row><p class=eyebrow>TODAY</p><small class=muted>${new Date().toLocaleDateString([], {weekday:"long",month:"short",day:"numeric"})}</small></div>
<div class=spacer></div>${card}
<div class=spacer></div>
<div class=home-dashboard-grid>
<button class="home-mini-card readiness-${readiness.tone}" data-coach-route=coach><span class=readiness-dot></span><span><small>READINESS</small><b>${readiness.label}</b><em>${esc(readiness.detail)}</em></span></button>
${homeNutritionSnapshot()}
</div>
<div class=spacer></div>${homeQuickActions(todayWorkout)}
${S.notifications?.items?.length?`<div class=spacer></div><div class="card proactive-home-card"><div class=row><div><p class=eyebrow>FORGE RECOMMENDATION</p><h3>${esc(S.notifications.items[0].title)}</h3></div><button class="btn dark compact" data-a=open-notifications>View</button></div><p class=muted>${esc(S.notifications.items[0].message)}</p></div>`:`<div class=spacer></div><div class="card proactive-home-card"><p class=eyebrow>FORGE RECOMMENDATION</p><h3>Stay on plan</h3><p class=muted>${esc((S.homeDashboard?.intelligence?.recommendations||[])[0]||"Complete today's planned work and log every working set.")}</p></div>`}
<div class=big-spacer></div>${weeklyInsightsCard()}<div class=big-spacer></div><div class=row><h3>This Week</h3><div class=home-progress-ring style="background:conic-gradient(var(--red) 0 ${pct}%,#20252b ${pct}% 100%)"><b>${pct}%</b></div></div>
<div class=spacer></div><div class=week-strip>${dayNames.map((d,i)=>{
const ww=workouts.find(w=>Number(w.scheduled_day)===i&&!w.is_skipped);
const completed=ww?.status==="completed";
return `<div class="day-dot ${completed?"done":i===today?"today":""}">${d}<b>${completed?"✓":ww?(i===today?"▶":"•"):"—"}</b></div>`;
}).join("")}</div>
<div class=big-spacer></div><div class=row><h3>Coming Up</h3><button class="text-action" data-nav=plan>Full plan</button></div><div class=spacer></div>
${upcoming.length?`<div class=upcoming-list>${upcoming.map(x=>`<button class=upcoming-workout data-w=${workouts.indexOf(x)}><span><small>${esc(x.scheduled_day_name||"Upcoming")} • ${esc(x.scheduled_time||S.timeSettings?.default_workout_time||"17:00")}</small><b>${esc(x.name)}</b></span><em>${x.estimated_minutes||profile.minutes_per_workout} min</em></button>`).join("")}</div>`:`<div class=polished-empty><b>Training week complete</b><span>Recover and get ready for next week.</span></div>`}
<div class=spacer></div><div class=home-completion-summary><div class=home-completion-count><strong>${done}/${workouts.length}</strong><span class=muted>Workouts Completed</span></div>
<div class=home-completed-list>${done?workouts.filter(w=>w.status==="completed").map(w=>`<div class=home-completed-workout><span class=completed-check>✓</span><span><strong>${esc(w.name)}</strong><small>${esc(w.scheduled_day_name||"Completed")}</small></span></div>`).join(""):`<div class=polished-empty compact-empty><b>Completed workouts appear here</b><span>Complete a workout to build your history.</span></div>`}</div></div>`;
}
