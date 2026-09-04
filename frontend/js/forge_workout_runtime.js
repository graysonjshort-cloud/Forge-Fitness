// Forge Fitness v15.11.0 — extracted moduleExerciseTarget..before nutritionDateValue
function moduleExerciseTarget(e){
return isTimedExercise(e)?`${e.min_reps}-${e.max_reps} sec`:`${e.min_reps}-${e.max_reps} reps`;
}
function coreModuleCard(ww){
const m=ww?.core_module;if(!m)return "";
return `<div class=spacer></div><div class="card training-module-card core-module-card">
<div class="module-card-header"><div><p class=eyebrow>CORE • SEPARATE MODULE</p><h3>${esc(m.name)}</h3></div><span class=module-duration>${m.estimated_minutes||8} min</span></div>
<p class="muted module-reason">${esc(m.reason||`Scheduled after ${ww.name}.`)}</p>
<div class=module-exercise-list>${(m.exercises||[]).map((e,i)=>`
<div class=module-exercise-row>
<span class=module-exercise-number>${i+1}</span>
<div class=module-exercise-copy>
<div class=module-exercise-title><b>${esc(e.name)}</b><span>${esc(e.core_region||e.primary_muscle||"Core")}</span></div>
<small>${e.sets} sets <i>•</i> ${moduleExerciseTarget(e)}${isBodyweightExercise(e)?" <i>•</i> Bodyweight":""}</small>
</div>
</div>`).join("")}</div>
<div class=spacer></div><div class=module-card-actions><button class=btn data-a=start-core-module>${ww.module_status?.core?.status==="completed"?"View Core Tracking":"Track Core Circuit"}</button>${ww.module_status?.core?.status==="completed"?"":`<button class="btn dark" data-a=move-core-module>Move Day</button>`}</div>
</div>`;
}
function cardioModuleCard(ww){
const m=ww?.cardio_module;if(!m)return "";
return `<div class=spacer></div><div class="card training-module-card cardio-module-card">
<div class=row><div><p class=eyebrow>CARDIO • SEPARATE MODULE</p><h3>${esc(m.name)}</h3></div><button class="btn dark compact" data-a=swap-cardio>Swap</button></div>
<p class=muted>${m.minutes||15} min • ${cardioLabel(m.intensity||profile.cardio_preference)} intensity</p>
<p class=muted>${esc(m.reason||`Scheduled with ${ww.name}`)}</p>
<div class=spacer></div><div class=module-card-actions><button class=btn data-a=start-cardio-module>${ww.module_status?.cardio?.status==="completed"?"View Cardio Tracking":"Track Cardio"}</button>${ww.module_status?.cardio?.status==="completed"?"":`<button class="btn dark" data-a=move-cardio-module>Move Day</button>`}</div>
</div>`;
}
function workout(){
const ww=w();if(!ww)return home();
const current=ww.exercises[Math.min(S.ei,ww.exercises.length-1)];
const completedExerciseCount=session?Math.min(S.ei,ww.exercises.length):0;
const workoutPct=Math.round(completedExerciseCount/Math.max(1,ww.exercises.length)*100);
const remainingMinutes=Math.max(1,Math.round((ww.estimated_minutes||profile.minutes_per_workout||45)*(1-workoutPct/100)));
return `${todayAdjustmentBanner()}<div class=workout-head><div><p class=eyebrow>${session?"WORKOUT IN PROGRESS":"SESSION"}</p><h2>${esc(ww.name)}</h2><p class=muted>${ww.exercises.length} exercises • ${ww.estimated_minutes||profile.minutes_per_workout} min${ww.execution_summary?` • ${ww.execution_summary.warmup_sets} warm-up sets`:""}</p></div><span class=workout-percent>${workoutPct}%${session?`<small style="display:block">~${remainingMinutes} min left</small>`:""}</span></div>
<div class=workout-progress-track><i style="width:${workoutPct}%"></i></div>
${session&&current?`<div class="card active-exercise-card"><div class=row><div><small>CURRENT EXERCISE</small><h2>${esc(current.name)}</h2><p>${effectiveSetCount(current)} sets • ${current.min_reps}-${current.max_reps} reps • ${current.rest_seconds||60}s base rest</p></div><span class=active-set-badge>Set ${S.set+1}</span></div><button class=btn data-a=openexercise>Continue</button></div>`:""}
<div class=section-heading><div><p class=eyebrow>EXERCISE LIST</p><h3>${session?"Workout map":"What you’ll do"}</h3></div></div>
<div class=exercise-list>${ww.exercises.map((e,i)=>`<button class="exercise-item ${i===S.ei?"selected":""} ${session&&i<S.ei?"exercise-done":""}" data-ex=${i}><span class=exercise-num>${session&&i<S.ei?"✓":i+1}</span><span class=exercise-item-copy><strong>${esc(e.name)}</strong><span class=exercise-meta><small>${session&&i===S.ei?effectiveSetCount(e):e.sets} sets</small><small>${e.min_reps}-${e.max_reps} reps</small><small>${esc(e.primary_muscle||"Strength")}</small>${e.superset_group?`<small>Superset ${esc(e.superset_group)}</small>`:""}</span></span><span class=exercise-chevron>›</span></button>`).join("")}</div>
${coreModuleCard(ww)}${cardioModuleCard(ww)}
<div class=big-spacer></div>${session?`<button class="btn dark" data-a=abandon>End Workout</button>`:`<button class=btn data-a=startworkout>Start Workout</button><div class=spacer></div><button class="btn dark" data-a=workout-builder>Edit Workout</button>`}`;
}
function isTimedExercise(e){
return e?.tracking_mode==="timed" || /plank|hold|wall sit/i.test(e?.name||"");
}
function isBodyweightExercise(e){
return e?.bodyweight_default===true || /(^|,|\s)bodyweight($|,|\s)/i.test(e?.equipment||"");
}
function stopExerciseTimer(){
if(S.exerciseTimer){clearInterval(S.exerciseTimer);S.exerciseTimer=null}
S.exerciseTimerRunning=false;
}
function resetExerciseTimer(){
stopExerciseTimer();S.exerciseElapsed=0;render();
}
function toggleExerciseTimer(){
if(S.exerciseTimerRunning){stopExerciseTimer();render();return}
S.exerciseTimerRunning=true;
S.exerciseTimer=setInterval(()=>{
S.exerciseElapsed++;
const el=document.querySelector("#exerciseClock");
if(el){
const mm=String(Math.floor(S.exerciseElapsed/60)).padStart(2,"0");
const ss=String(S.exerciseElapsed%60).padStart(2,"0");
el.textContent=`${mm}:${ss}`;
}
},1000);
render();
}
async function loadExerciseProgression(){const ex=w()?.exercises?.[S.ei];if(!ex)return;const exerciseId=Number(ex.exercise_id);if(S.exerciseProgressionExerciseId===exerciseId&&(S.exerciseProgression||S.exerciseProgressionLoading))return;S.exerciseProgressionLoading=true;S.exerciseProgressionExerciseId=exerciseId;S.exerciseProgression=null;try{const data=await api(`/me/exercises/${exerciseId}/progression-strategy`);if(S.exerciseProgressionExerciseId!==exerciseId)return;S.exerciseProgression=data;if(S.route==="exercise"&&Number(w()?.exercises?.[S.ei]?.exercise_id)===exerciseId)render()}catch(e){if(S.exerciseProgressionExerciseId===exerciseId)S.exerciseProgression=null}finally{if(S.exerciseProgressionExerciseId===exerciseId)S.exerciseProgressionLoading=false}}
function exerciseProgressionCard(){const p=S.exerciseProgression;if(!p||p.loading)return "";return `<div class="card progression-card"><div class=row><div><p class=eyebrow>EXERCISE PROGRESSION 4.0</p><h3>${esc(p.method)}</h3></div><b>${esc(p.status)}</b></div><p>${esc(p.target_rule)}</p><small>${esc(p.reason)}</small>${p.last_exposures?.length?`<div class=spacer></div><div class=previous-set-strip>${p.last_exposures.map(x=>`<span><b>${x}</b><small>exposure</small></span>`).join("")}</div>`:""}<div class=spacer></div><small><b>Next action:</b> ${esc(String(p.next_action||"hold").replaceAll("_"," "))}</small><div class=progression-metrics><span><b>${p.sessions_analyzed}</b><small>sessions</small></span><span><b>${p.retention_score??"—"}</b><small>retention</small></span><span><b>${p.plateau_evidence||0}</b><small>plateau evidence</small></span></div>${p.resume_cue?`<div class=spacer></div><small><b>Post-deload:</b> ${esc(p.resume_cue)}</small>`:""}</div>`}
function workoutFlowCard(e){
const ww=w(),total=(ww?.exercises||[]).length,done=Math.max(0,S.ei),remaining=Math.max(0,total-S.ei-1);
const next=remaining?(ww.exercises[S.ei+1]?.name||"Next exercise"):"Finish workout";
const recall=(S.exerciseRecall?.sets||[]).at(-1);
const last=recall?`${recall.weight!=null?`${Number(recall.weight)} lb × `:""}${recall.reps??recall.duration_seconds??"—"}${recall.duration_seconds?" sec":" reps"} • RPE ${recall.rpe??"—"}`:"No prior logged set yet";
const sessionPct=Math.round(((done+(S.set/Math.max(1,e.sets)))/Math.max(1,total))*100);
return `<div class="card workout-flow-card"><div class=row><div><p class=eyebrow>WORKOUT FLOW 4.0</p><h3>${done+1}/${total} • ${esc(e.name)}</h3></div><b>${sessionPct}%</b></div><div class=workout-progress-track><i style="width:${sessionPct}%"></i></div><div class=flow-grid><span><small>LAST LOGGED</small><b>${esc(last)}</b></span><span><small>NEXT</small><b>${esc(next)}</b></span></div></div>`;
}
function exerciseinspect(){
const ww=w(),i=Math.max(0,Math.min(Number(S.inspectEi||0),(ww?.exercises?.length||1)-1)),e=ww?.exercises?.[i];if(!e)return workout();
return `<div class=focus-workout-top><button class=focus-back data-nav=workout aria-label="Back to workout">‹</button><div><p class=eyebrow>PREVIEW • EXERCISE ${i+1} OF ${ww.exercises.length}</p><h1>${esc(e.name)}</h1><p class=focus-set>${e.sets} sets • ${e.min_reps}-${e.max_reps} reps</p></div><button class=focus-demo data-form-demo="${e.exercise_id}" data-form-return=exerciseinspect>Form</button></div><div class=card><p class=eyebrow>PLANNED</p><h3>${e.sets} sets • ${e.rest_seconds||60}s rest</h3><p class=muted>${esc(e.primary_muscle||"Strength")} • ${esc(e.equipment||"Bodyweight")}</p></div><div class=spacer></div><button class="btn dark" data-nav=workout>Back to Workout</button><p class="muted inspect-note">Preview only — workout position stays unchanged.</p>`;
}
function exercise(){
const e=w().exercises[S.ei],timed=isTimedExercise(e),bodyweight=isBodyweightExercise(e),setNum=S.set+1,totalSets=effectiveSetCount(e),nextRest=latestRestFor(e);
if(timed&&!S.exerciseTimerTarget)S.exerciseTimerTarget=Math.max(5,Math.round((Number(e.min_reps||20)+Number(e.max_reps||60))/2));
const target=timed?`${S.exerciseTimerTarget} sec`:`${e.min_reps}-${e.max_reps} reps`;
const clock=`${String(Math.floor(S.exerciseElapsed/60)).padStart(2,"0")}:${String(S.exerciseElapsed%60).padStart(2,"0")}`;
const adjustment=S.liveAdjustment?`<details class="card forge-adjustment"><summary><span><small>FORGE ADJUSTMENT</small><b>${esc(S.liveAdjustment.title)}</b></span><em>Why?</em></summary><p>${esc(S.liveAdjustment.detail)}</p>${S.sessionIntelligence?.next_set?`<div class=progression-metrics><span><b>${S.sessionIntelligence.next_set.load_adjustment_percent>0?"+":""}${S.sessionIntelligence.next_set.load_adjustment_percent}%</b><small>load</small></span><span><b>RPE ≤ ${S.sessionIntelligence.next_set.effort_cap}</b><small>cap</small></span><span><b>${S.sessionIntelligence.next_set.rest_seconds}s</b><small>rest</small></span></div>`:""}</details>`:"";
return `<div class=focus-workout-top><button class=focus-back data-nav=workout aria-label="Back to workout">‹</button><div><p class="eyebrow workout-context"><span class=workout-context-name>${esc(w().name)}</span><span class=workout-context-count>Exercise ${S.ei+1} of ${w().exercises.length}</span></p><h1>${esc(e.name)}</h1><p class=focus-set>Set ${Math.min(setNum,totalSets)} of ${totalSets}</p></div><button class=focus-demo data-form-demo="${e.exercise_id}" data-form-return=exercise>Form</button></div>
<div class=focus-prescription><div class=focus-target><small>TARGET</small><strong>${target}</strong><span>${nextRest?`${nextRest}s next rest`:`${e.rest_seconds||60}s base rest`}</span></div><div class=set-count-control><small>SETS TODAY</small><div><button type=button data-setchange=-1 aria-label="Remove one set" ${totalSets<=Math.max(1,session?S.set+1:1)?"disabled":""}>−</button><b>${totalSets}</b><button type=button data-setchange=1 aria-label="Add one set" ${totalSets>=12?"disabled":""}>+</button></div><span>Adjust sets</span></div></div>
<div id=recallCard class="focus-previous">${exerciseRecallMarkup(e)}</div>
${timed?`<div class=focus-timer><div id=exerciseClock>${clock}</div><div class=set-adjuster timed-target-adjuster><button type=button data-timer-target=-5>−5s</button><span><b>${S.exerciseTimerTarget}s</b><small>target</small></span><button type=button data-timer-target=5>+5s</button></div><div class=exercise-actions><button class=btn data-a=exercise-timer-toggle>${S.exerciseTimerRunning?"Pause":"Start Timer"}</button><button class="btn dark" data-a=exercise-timer-reset>Reset</button></div></div><input id=durationSeconds type=hidden value="${S.exerciseElapsed}">`:
`<div class="focus-inputs ${bodyweight?"bodyweight":""}">${bodyweight?`<label>Load<select class=log-input id=loadMode><option value=bodyweight selected>Bodyweight</option><option value=weight>Added Weight</option></select></label><label id=addedWeightRow style="display:none">Added weight<input class=log-input id=weight type=number inputmode=decimal min=0 step=2.5 placeholder="0"></label>`:`<label>Weight <small>lb</small><input class=log-input id=weight type=number inputmode=decimal min=0 step=2.5 placeholder="0"></label>`}<label>Reps<input class=log-input id=reps type=number inputmode=numeric min=1 step=1 value="${e.min_reps}"></label></div>`}
<div class=focus-effort><div><b>Effort</b><small>Good reps left</small></div><div class=effort-options><button type=button class=effort-choice data-rpe=6><b>Easy</b><small>4+</small></button><button type=button class="effort-choice selected" data-rpe=7><b>Moderate</b><small>3</small></button><button type=button class=effort-choice data-rpe=8><b>Hard</b><small>2</small></button><button type=button class=effort-choice data-rpe=9><b>Very Hard</b><small>1</small></button><button type=button class=effort-choice data-rpe=10><b>Limit</b><small>0</small></button></div><input id=rpe type=hidden value=7></div>
<button class="btn focus-complete" data-a=completeset>Complete ${timed?"Timed Set":"Set"}</button>${S.sessionIntelligence?.optional_extra_set&&S.set>=Number(S.sessionIntelligence?.planned_sets||e.sets)?`<button class="btn dark finish-exercise" data-a=finish-exercise>Finish Exercise</button><small class=optional-set-note>Bonus set is optional.</small>`:""}
<div class=focus-secondary>${adjustment}${exerciseProgressionCard()}<button class="btn dark" data-a=swap-exercise>Swap Exercise</button><button class="text-action skip-set-action" data-a=skip-set>Skip this set</button></div>`;
}
function stopCoreTimer(){
if(S.coreTimerInterval){clearInterval(S.coreTimerInterval);S.coreTimerInterval=null}
S.coreTimerRunning=null;
}
function startCoreTimer(index){
index=String(index);
if(S.coreTimerRunning===index){stopCoreTimer();render();return}
stopCoreTimer();
if(!Number.isFinite(S.coreTimerElapsed[index]))S.coreTimerElapsed[index]=0;
S.coreTimerRunning=index;
S.coreTimerInterval=setInterval(()=>{
S.coreTimerElapsed[index]=Number(S.coreTimerElapsed[index]||0)+1;
const clock=document.querySelector(`[data-core-clock="${index}"]`);
const input=document.querySelector(`[data-core-value="${index}"]`);
if(clock){
const t=S.coreTimerElapsed[index];
clock.textContent=`${String(Math.floor(t/60)).padStart(2,"0")}:${String(t%60).padStart(2,"0")}`;
}
if(input)input.value=S.coreTimerElapsed[index];
},1000);
render();
}
function resetCoreTimer(index){
index=String(index);
if(S.coreTimerRunning===index)stopCoreTimer();
S.coreTimerElapsed[index]=0;
render();
}
function effortChoiceHTML(selected, kind, key=""){
const rows=[[6,"Easy","4+ left"],[7,"Moderate","~3 left"],[8,"Hard","~2 left"],[9,"Very Hard","~1 left"],[10,"Limit","0 left"]];
return rows.map(([v,label,sub])=>{
const attrs=kind==="core"?`data-core-effort="${v}" data-core-effort-key="${key}"`:`data-cardio-effort="${v}"`;
return `<button type=button class="effort-choice ${Number(selected)===v?"selected":""}" ${attrs}><b>${label}</b><small>${sub}</small></button>`;
}).join("");
}
function stopCoreRest(){
if(S.coreRestTimer){clearInterval(S.coreRestTimer);S.coreRestTimer=null}
S.coreRestRemaining=0;
}
function startCoreRest(seconds){
stopCoreRest();
S.coreRestRemaining=Math.max(1,Number(seconds||30));
S.coreRestTimer=setInterval(()=>{
S.coreRestRemaining=Math.max(0,S.coreRestRemaining-1);
const el=document.querySelector("#coreRestClock");
if(el)el.textContent=`${String(Math.floor(S.coreRestRemaining/60)).padStart(2,"0")}:${String(S.coreRestRemaining%60).padStart(2,"0")}`;
if(S.coreRestRemaining<=0){stopCoreRest();render();}
},1000);
render();
}
function coreAllSetsCompleted(module){
return (module.exercises||[]).every((e,i)=>
Array.from({length:Number(e.sets||1)},(_,s)=>!!S.coreCompleted[`${i}-${s}`]).every(Boolean)
);
}
function coreSequence(module){
const exercises=module?.exercises||[];
const rounds=Math.max(1,...exercises.map(e=>Number(e.sets||1)));
const sequence=[];
for(let round=0;round<rounds;round++){
exercises.forEach((e,exerciseIndex)=>{
if(round<Number(e.sets||1)){
sequence.push({
key:`${exerciseIndex}-${round}`,
exerciseIndex,
setIndex:round,
round,
exercise:e
});
}
});
}
return sequence;
}
function nextIncompleteCoreIndex(module,start=0){
const seq=coreSequence(module);
for(let i=Math.max(0,start);i<seq.length;i++){
if(!S.coreCompleted[seq[i].key])return i;
}
for(let i=0;i<Math.max(0,start);i++){
if(!S.coreCompleted[seq[i].key])return i;
}
return seq.length;
}
function restoreCoreSequenceFromLogs(module,logs=[]){
S.coreCompleted={};
const counts={};
(logs||[]).forEach(log=>{
const exerciseId=Number(log.exercise_id);
const exerciseIndex=(module.exercises||[]).findIndex(e=>Number(e.exercise_id)===exerciseId);
if(exerciseIndex<0)return;
const setIndex=counts[exerciseId]||0;
if(setIndex<Number(module.exercises[exerciseIndex].sets||1)){
S.coreCompleted[`${exerciseIndex}-${setIndex}`]=true;
counts[exerciseId]=setIndex+1;
}
});
S.coreSequenceIndex=nextIncompleteCoreIndex(module,0);
}
function coretracker(){
const ww=plan?.workouts?.[S.moduleWorkoutIndex??S.wi],m=ww?.core_module;
if(!m)return `<h2>Core Circuit</h2><p class=muted>No core circuit selected.</p>`;
const seq=coreSequence(m),total=seq.length,completed=seq.filter(x=>S.coreCompleted[x.key]).length;
S.coreSequenceIndex=Math.min(nextIncompleteCoreIndex(m,S.coreSequenceIndex),total);
if(S.coreSequenceIndex>=total){
return `<p class=eyebrow>CORE CIRCUIT</p><h2>${esc(m.name)}</h2>
<div class="card sequential-core-complete"><div class=completion-check>✓</div><h3>All ${total} sets complete</h3><p class=muted>Your work is saved. Finish the circuit to complete the session.</p></div>
<div class=big-spacer></div><button class=btn data-a=complete-core-module>Finish Core Circuit</button>`;
}
const step=seq[S.coreSequenceIndex],e=step.exercise,key=step.key,timed=isTimedExercise(e);
const elapsed=Number(S.coreTimerElapsed[key]||0),effort=Number(S.coreEffort[key]||7);
const defaultValue=Math.round((Number(e.min_reps||10)+Number(e.max_reps||10))/2);
const clock=`${String(Math.floor(elapsed/60)).padStart(2,"0")}:${String(elapsed%60).padStart(2,"0")}`;
const roundCount=Math.max(...(m.exercises||[]).map(x=>Number(x.sets||1)),1);
const nextStep=seq[S.coreSequenceIndex+1];
return `<p class=eyebrow>CORE CIRCUIT • SEQUENTIAL</p><div class=sequential-core-top><div><h2>${esc(m.name)}</h2><p class=muted>Round ${step.round+1} of ${roundCount}</p></div><span>${completed}/${total}</span></div>
<div class=workout-progress-track><i style="width:${Math.round(completed/Math.max(1,total)*100)}%"></i></div>
<div class=big-spacer></div>
<div class="card sequential-core-current">
<div class=core-track-heading><div><p class=eyebrow>${esc(e.core_region||"CORE")}</p><h2>${esc(e.name)}</h2></div><span>Set ${step.setIndex+1}/${e.sets}</span></div>
<p class=muted>Target: ${moduleExerciseTarget(e)}${isBodyweightExercise(e)?" • Bodyweight":""}</p>
<p class="muted core-progression-note">${esc(e.progression_method||"Progress when all sets finish with good form.")}</p><button class=form-demo-inline data-form-demo="${e.exercise_id}" data-form-return=coretracker>▶ Form Demo</button>
${timed?`<div class=core-timer-panel><div class=core-timer-clock data-core-clock="${key}">${clock}</div><small>Actual hold time</small><div class=core-timer-actions><button type=button data-core-timer-start="${key}">${S.coreTimerRunning===key?"Pause":"Start Timer"}</button><button type=button data-core-timer-reset="${key}">Reset</button></div></div><input data-core-value="${key}" type=hidden value="${elapsed}">`
:`<div class=logging-row><label>Reps</label><input class=log-input data-core-value="${key}" type=number min=1 value="${defaultValue}"></div>`}
<div class=effort-section><div class=effort-heading><strong>Effort / RIR</strong><small>${timed?"How hard was it?":"Good reps left?"}</small></div><div class=effort-options>${effortChoiceHTML(effort,"core",key)}</div><input data-core-rpe="${key}" type=hidden value="${effort}"></div>
<button class="btn sequential-core-complete-set" type=button data-core-complete-set="${key}" data-core-exercise="${step.exerciseIndex}" data-core-set="${step.setIndex}">Complete Set</button>
</div>
<div class=spacer></div>
<div class="card sequential-core-next"><p class=eyebrow>NEXT</p>${nextStep?`<h3>${esc(nextStep.exercise.name)}</h3><p class=muted>Round ${nextStep.round+1} • Set ${nextStep.setIndex+1} • ${moduleExerciseTarget(nextStep.exercise)}</p>`:`<h3>Finish Circuit</h3>`}</div>
${S.coreRestRemaining>0?`<div class=core-rest-overlay><div class=core-rest-card><p class=eyebrow>${nextStep&&nextStep.round>step.round?"ROUND REST":"CORE REST"}</p><div id=coreRestClock>${String(Math.floor(S.coreRestRemaining/60)).padStart(2,"0")}:${String(S.coreRestRemaining%60).padStart(2,"0")}</div><p class=muted>${nextStep?`Next: ${esc(nextStep.exercise.name)}`:"Final recovery"}</p><button class=btn data-a=skip-core-rest>Skip Rest</button></div></div>`:""}`;
}
function cardiotracker(){
const ww=plan?.workouts?.[S.moduleWorkoutIndex??S.wi],m=ww?.cardio_module,effort=Number(S.cardioEffort||7);
if(!m)return `<h2>Cardio</h2><p class=muted>No cardio module selected.</p>`;
return `<p class=eyebrow>CARDIO TRACKING</p><h2>${esc(m.name)}</h2><p class=muted>${esc(m.reason||"Goal-aware cardio")}</p>
<div class=big-spacer></div><div class=card>
<div class=logging-grid><div class=logging-row><label>Completed Minutes</label><input class=log-input id=cardioMinutes type=number min=0 step=1 value="${m.minutes||15}"></div><div class=logging-row><label>Distance <small>optional</small></label><input class=log-input id=cardioDistance type=number min=0 step=.01 placeholder="0"></div><div class=logging-row><label>Pace <small>optional</small></label><input class=log-input id=cardioPace type=text placeholder="e.g. 10:00 / mi"></div></div>
<div class=effort-section><div class=effort-heading><strong>Effort / RIR</strong><small>Session effort</small></div><div class=effort-options>${effortChoiceHTML(effort,"cardio")}</div><input id=cardioRpe type=hidden value="${effort}"></div>
</div><div class=big-spacer></div><button class=btn data-a=complete-cardio-module>Complete Cardio</button>`;
}
function timer(){
const e=w().exercises[S.ei],t=S.restRemaining||S.restTotal||e.rest_seconds||60,mm=String(Math.floor(t/60)).padStart(2,"0"),ss=String(t%60).padStart(2,"0"),ctx=S.restContext;
const restNote=ctx&&Number(ctx.recommended)!==Number(ctx.base)?`Rest adjusted: ${ctx.base}s → ${ctx.recommended}s.`:`Rest: ${Number(ctx?.recommended||S.restTotal||e.rest_seconds||60)}s.`;
return `<div class=center><p class=eyebrow>RECOVERY BETWEEN SETS</p><h2>Rest Timer</h2><p class=muted>Next: ${esc(e.name)} • Set ${Math.min(S.set+1,effectiveSetCount(e))} of ${effectiveSetCount(e)}</p><p class="rest-explanation">${esc(restNote)}</p><div class=ring><div><strong id=restClock>${mm}:${ss}</strong><span class=muted>Remaining</span></div></div><div class=timer-actions><button data-addrest=30>+30s</button><button data-addrest=60>+1m</button><button data-a=skiprest>Skip</button></div><div class=big-spacer></div><button class=btn data-a=skiprest>Next Set</button><div class=spacer></div><button class="btn dark" data-a=view-workout-rest>View Workout</button></div>`;
}
function modulemove(){
const type=S.moduleMoveType,sourceIndex=S.moduleMoveSourceIndex,source=plan?.workouts?.[sourceIndex];
if(!type||!source)return `<h2>Move Module</h2><p class=muted>No module selected.</p>`;
const label=type==="core"?"Core Circuit":"Cardio";
const candidates=(plan.workouts||[]).map((ww,i)=>({ww,i})).filter(({i})=>i!==sourceIndex);
return `<p class=eyebrow>MOVE ${type.toUpperCase()}</p><h2>Choose a New Day</h2><p class=muted>${label} is currently attached to ${esc(source.scheduled_day_name||source.name)}. Choose any other day that has a workout. If that day already has ${type}, the two ${type} modules will swap days.</p>
<div class=big-spacer></div><div class=stack>${candidates.length?candidates.map(({ww,i})=>`<button class="card module-day-option ${S.moduleMoveTarget===ww.workout_id?"selected":""}" data-module-day="${ww.workout_id}">
<div class=row><div><p class=eyebrow>${esc(ww.scheduled_day_name||`Day ${i+1}`)}</p><h3>${esc(ww.name)}</h3><p class=muted>${ww.estimated_minutes||profile.minutes_per_workout} min strength workout${ww[`${type}_module`]?" • Existing module will swap":""}</p></div><span>${S.moduleMoveTarget===ww.workout_id?"✓":"›"}</span></div>
</button>`).join(""):`<div class=card><p class=muted>Every other workout day already has a ${type} module.</p></div>`}</div>
<div class=big-spacer></div><div class=row><button class="btn dark" style="width:48%" data-a=cancel-module-move>Cancel</button><button class=btn style="width:48%" data-a=apply-module-move ${S.moduleMoveTarget?"":"disabled"}>Move ${label}</button></div>`;
}
function cardioSwapMarkup(){
const key=String(w()?.workout_id||"");
if(S.cardioSwapKey!==key||S.cardioSwapLoading)return `<div class=card><p class=muted>Loading cardio options…</p></div>`;
if(!S.cardioSwapOptions.length)return `<div class=card><p class=muted>No compatible cardio options found for your equipment.</p></div>`;
return S.cardioSwapOptions.map(x=>`<button class="card swap-option ${Number(S.selectedCardioSwap)===Number(x.id)||(!S.selectedCardioSwap&&x.name===w()?.cardio_module?.name)?"selected":""}" data-cardio-swap=${x.id}>
<div class=row><div><p class=eyebrow>${esc(x.movement_pattern)}</p><h3>${esc(x.name)}</h3><p class=muted>${esc(x.equipment)}</p></div><span>${x.name===w()?.cardio_module?.name?"Current":"›"}</span></div>
</button>`).join("");
}
function cardioswap(){
return `<p class=eyebrow>SWAP CARDIO</p><h2>Choose Cardio Exercise</h2>
<p class=muted>Only compatible cardio options are shown.</p>
<div class=spacer></div><div id=cardioSwapList class=stack>${cardioSwapMarkup()}</div>
<div class=big-spacer></div><div class=row><button class="btn dark" style="width:48%" data-a=cancel-cardio-swap>Cancel</button><button class=btn style="width:48%" data-a=apply-cardio-swap>Swap</button></div>`;
}
async function loadCardioSwapOptions(){
const key=String(w()?.workout_id||"");if(!key)return;
if(S.cardioSwapKey===key&&(S.cardioSwapLoaded||S.cardioSwapLoading))return;
S.cardioSwapKey=key;S.cardioSwapLoading=true;S.cardioSwapLoaded=false;
try{
const rows=await api("/me/cardio/options");
if(S.cardioSwapKey!==key)return;
S.cardioSwapOptions=rows.filter(x=>x.equipment_compatible);
S.selectedCardioSwap=null;S.cardioSwapLoading=false;S.cardioSwapLoaded=true;
if(S.route==="cardioswap"&&String(w()?.workout_id||"")===key)render();
}catch(e){if(S.cardioSwapKey===key)S.cardioSwapLoaded=true;toast(e.message)}finally{if(S.cardioSwapKey===key)S.cardioSwapLoading=false}
}
async function applyCardioSwap(){
if(!S.selectedCardioSwap){toast("Choose a cardio exercise");return}
await api(`/me/workouts/${w().workout_id}/cardio/swap`,{method:"POST",body:JSON.stringify({new_exercise_id:S.selectedCardioSwap})});
plan=await api("/me/plan/current");await reconcileSession({silent:true});S.adaptationPreview=null;
toast("Cardio swapped");
go("workout");
}
function swapBonus(x,e){
const fatigue=Number(x.fatigue_cost||3),skill=Number(x.skill_demand||3);
if(S.swapReason==="discomfort")return (6-fatigue)*8+(6-skill)*3+(/machine|cable/i.test(x.equipment||"")?10:0);
if(S.swapReason==="too_hard")return (6-fatigue)*7+(6-skill)*5;
if(S.swapReason==="equipment")return x.equipment_compatible?40:-200;
if(S.swapReason==="variety")return x.movement_pattern===e?.movement_pattern?5:12;
return 0;
}
function swapOptionsMarkup(e){
const key=`${Number(e?.exercise_id||0)}:${S.swapReason}`;
if(S.swapOptionsKey!==key||S.swapOptionsLoading)return `<div class=card><p class=muted>Loading substitutions…</p></div>`;
const compatible=(S.swapOptions||[]).filter(x=>x.equipment_compatible&&x.user_preference!=="painful");
if(!compatible.length)return `<div class=card><p class=muted>No compatible swaps found.</p></div>`;
return compatible.map((x,i)=>`<button class="card swap-option smart-swap-option ${Number(S.selectedSwap)===Number(x.id)?"selected":""}" data-swap=${x.id}>
<div class=row><div><p class=eyebrow>${i===0?"BEST MATCH":esc(x.primary_muscle)}</p><h3>${esc(x.name)}</h3>
<p class=muted>${esc(x.equipment)} • ${x.min_reps}-${x.max_reps} reps</p><div class=swap-match-tags><span>${esc(x.smart_reason||"similar movement")}</span>${x.user_preference==="favorite"?"<span>★ Favorite</span>":""}</div></div><div class=swap-score><b>${Math.max(0,Math.round(Number(x.substitution_score||0)+swapBonus(x,e)))}</b><small>match</small></div></div></button>`).join("");
}
function swapexercise(){
const e=w()?.exercises?.[S.ei];
const reasons=[
["preference","Prefer something else"],
["discomfort","Pain / discomfort"],
["too_hard","Too difficult today"],
["equipment","Equipment unavailable"],
["variety","Want variety"]
];
return `${substitutionIntelligenceCard()}<div class=spacer></div><p class=eyebrow>SMART SUBSTITUTION</p><h2>Swap ${esc(e?.name||"Exercise")}</h2><p class=muted>Tell Forge why you want a swap.</p><div class=swap-reason-grid>${reasons.map(([k,l])=>`<button class="${S.swapReason===k?"selected":""}" data-swap-reason="${k}">${l}</button>`).join("")}</div><div class=spacer></div><input class=swap-search placeholder="Search alternatives"><div class=row><p class=eyebrow>BEST MATCHES</p><small class=muted>ranked for this reason</small></div><div class=spacer></div><div id=swapList class=stack>${swapOptionsMarkup(e)}</div><div class=big-spacer></div>${S.swapReason==="discomfort"?`<div class="card pain-swap-note"><b>Discomfort swap</b><span>Forge will avoid this exercise in future swaps. Stop if the movement causes pain.</span></div><div class=spacer></div>`:""}<div class=row><button class="btn dark" style="width:48%" data-a=back-exercise>Cancel</button><button class=btn style="width:48%" data-a=swap-selected>Swap</button></div>`;
}
async function loadSwapOptions(){
const e=w()?.exercises?.[S.ei];if(!e)return;
const exerciseId=Number(e.exercise_id),reason=S.swapReason,key=`${exerciseId}:${reason}`;
if(S.swapOptionsKey===key&&(S.swapOptionsLoaded||S.swapOptionsLoading))return;
S.swapOptionsKey=key;S.swapOptionsLoading=true;S.swapOptionsLoaded=false;S.swapOptions=[];S.selectedSwap=null;
try{
const rows=await api(`/me/exercises/${exerciseId}/substitutions`);
if(S.swapOptionsKey!==key)return;
S.swapOptions=[...rows].sort((a,b)=>(Number(b.substitution_score||0)+swapBonus(b,e))-(Number(a.substitution_score||0)+swapBonus(a,e)));S.swapOptionsLoading=false;S.swapOptionsLoaded=true;
if(S.route==="swapexercise"&&Number(w()?.exercises?.[S.ei]?.exercise_id)===exerciseId&&S.swapReason===reason)render();
}catch(err){if(S.swapOptionsKey===key){S.swapOptions=[];S.swapOptionsLoaded=true}toast(err.message)}
finally{if(S.swapOptionsKey===key)S.swapOptionsLoading=false}
}
async function applySwap(newId){
const old=w().exercises[S.ei];
const replacement=(S.swapOptions||[]).find(x=>Number(x.id)===Number(newId));
if(!replacement)throw Error("Selected replacement is unavailable");
await api(`/me/workouts/${w().workout_id}/swap`,{method:"POST",localFirst:true,localKind:"swap",body:JSON.stringify({
old_exercise_id:old.exercise_id,new_exercise_id:newId
})});
const localExercise={...old,...replacement,exercise_id:Number(replacement.id||replacement.exercise_id),id:Number(replacement.id||replacement.exercise_id),sets:old.sets,min_reps:old.min_reps,max_reps:old.max_reps,rest_seconds:old.rest_seconds};
w().exercises.splice(S.ei,1,localExercise);
await ForgeLocalWorkout?.cachePlan?.(plan);
if(S.swapReason==="discomfort"&&S.online){try{await api(`/me/exercises/${old.exercise_id}/preference`,{method:"PUT",body:JSON.stringify({preference:"painful",notes:"Marked during workout substitution due to discomfort"})})}catch(e){console.warn("Pain preference save failed",e)}}
if(S.online){try{plan=await api("/me/plan/current");await ForgeLocalWorkout?.cachePlan?.(plan)}catch{}S.adaptationPreview=null;if(session)await reconcileSession({silent:true});}
toast(S.online?(S.swapReason==="discomfort"?"Exercise swapped and painful movement deprioritized":"Exercise swapped"):"Exercise swapped locally — Forge will sync it when you reconnect");S.swapReason="preference";
go("exercise");
}
function complete(){
const prs=S.workoutPRs||[],unique=[],seen=new Set();for(const pr of prs){const k=`${pr.exercise_name}|${pr.type}`;if(!seen.has(k)){seen.add(k);unique.push(pr)}}
const sum=S.completedWorkoutSummary||{},duration=sum.duration_minutes??(S.sessionStartedAt?Math.max(1,Math.round((Date.now()-S.sessionStartedAt)/60000)):null),volume=sum.total_volume;
return `<div class=center><div class=complete-shield>💪</div><p class=eyebrow>SESSION COMPLETE</p><h2>${esc(w()?.name||"Workout")}</h2><p class=muted>Strong work, ${esc(S.name)}. Here’s what you accomplished.</p><div class=spacer></div><div class="metrics completion-metrics"><div class=metric><strong>${duration??"—"}</strong><span>Minutes</span></div><div class=metric><strong>${w()?.exercises?.length||0}</strong><span>Exercises</span></div><div class=metric><strong>${sum.total_sets??w()?.exercises?.reduce((a,e)=>a+e.sets,0)??0}</strong><span>Sets</span></div><div class=metric><strong>${volume!=null?Math.round(volume).toLocaleString():"—"}</strong><span>Volume lb</span></div></div>${unique.length?`<div class=spacer></div><div class=completion-prs><p class=eyebrow>NEW PERSONAL RECORDS</p>${unique.slice(0,4).map(pr=>`<div class=pr-card><p class=eyebrow>🏆 ${esc(pr.label)}</p><h3>${esc(pr.exercise_name)}</h3><strong>${pr.value} ${esc(pr.unit)}</strong></div>`).join("")}</div>`:""}<div class=spacer></div><div class="card completion-next-card"><p class=eyebrow>NEXT SESSION</p><h3>${unique.length?"Progress captured":"Consistency captured"}</h3><p class=muted>Forge uses this set to update your next target.</p></div><div class=big-spacer></div><p>How was this workout?</p><div class=spacer></div><div class=feelings>${[["😟","Too Hard"],["😡","Hard"],["🙂","Just Right"],["😎","Easy"],["🔥","Too Easy"]].map(x=>`<button class="feel ${S.feel===x[1]?"selected":""}" data-feel="${x[1]}"><span>${x[0]}</span>${x[1]}</button>`).join("")}</div><div class=big-spacer></div><button class=btn data-a=finish>Finish Workout</button><div class=spacer></div><div class=complete-secondary><button class="btn dark" data-a=finish-progress>View Progress</button><button class="btn dark" data-a=finish-nutrition>Log Nutrition</button></div></div>`;
}
async function loadCompletedWorkoutSummary(){
if(!S.lastSessionId)return;
try{const rows=await api("/me/history");const row=(rows||[]).find(x=>Number(x.session_id)===Number(S.lastSessionId));if(row){S.completedWorkoutSummary={total_sets:row.total_sets,total_volume:row.total_volume,duration_minutes:row.started_at&&row.completed_at?Math.max(1,Math.round((Date.parse(row.completed_at+"Z")-Date.parse(row.started_at+"Z"))/60000)):null};if(S.route==="complete")render()}}catch(e){console.warn("Completion summary unavailable",e)}
}
