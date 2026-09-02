// Forge Fitness v15.11.0 — extracted historyRowsMarkup..before loadCoachBriefing
function historyRowsMarkup(){
if(S.historyLoading&&!S.historyLoaded)return `<div class=card><p class=muted>Loading history…</p></div>`;
const rows=S.historyRows||[];
if(!rows.length)return `<div class=card><p class=muted>No completed workout history yet.</p></div>`;
return rows.map(r=>`<button class=card data-session=${r.session_id} style="width:100%;color:white;text-align:left"><div class=row><div><p class=eyebrow>WEEK ${r.week_number}</p><h3>${esc(r.workout_name)}</h3><p class=muted>${r.total_sets} sets • ${Math.round(r.total_volume)} lb volume</p></div><span>${r.status==="completed"?"✓":"○"}</span></div></button>`).join("");
}
function history(){
return `<div class=row><div><p class=eyebrow>HISTORY</p><h2>Workout History</h2></div><select class=history-filter><option>All</option></select></div><div class=spacer></div><div id=historyList class=stack>${historyRowsMarkup()}</div>`;
}
function prs(){
return `<p class=eyebrow>PERSONAL RECORDS</p><h2>Personal Records</h2>
<div class=spacer></div><div class=pr-tabs>
<button class="${S.prView==="exercise"?"active":""}" data-pr-view=exercise>By Exercise</button>
<button class="${S.prView==="lift"?"active":""}" data-pr-view=lift>By Lift Type</button></div>
${S.prView==="lift"?`<div class=spacer></div><p class=muted>Browse records by movement type.</p>
<div class=pr-lift-filters>${[["all","All"],["lower","Lower Body"],["upper","Upper Body"],["core","Core"],["conditioning","Conditioning"]].map(([v,l])=>`<button class="${S.prLiftFilter===v?"active":""}" data-pr-lift-filter="${v}">${l}</button>`).join("")}</div>`:""}
<div class=spacer></div><div id=prList class=stack>${S.prLoaded?(S.prView==="lift"?renderPRLiftGroups(S.prRecords||[]):renderPRExerciseList(S.prRecords||[])):`<div class=card><p class=muted>Loading PRs…</p></div>`}</div>`;
}
function exerciseHistoryMarkup(){
const data=S.exerciseHistoryData;
if(!data||Number(S.exerciseHistoryExerciseId)!==Number(S.historyExercise))return {title:"Exercise",body:`<div class=card><p class=muted>Loading…</p></div>`};
const prs=data.prs||{},suggestion=data.progression_suggestion,all=data.sets||[],recent=all.slice(-12),max=Math.max(1,...recent.map(x=>Number(x.e1rm||0)));
return {title:data.name,body:`<div class=metrics><div class=metric><strong>${prs.max_weight||0}</strong><span>MAX LB</span></div><div class=metric><strong>${prs.best_e1rm||0}</strong><span>EST. 1RM</span></div><div class=metric><strong>${prs.best_reps||0}</strong><span>BEST REPS</span></div></div><div class=spacer></div>${recent.length?`<div class=card><p class=eyebrow>ESTIMATED 1RM TREND</p><div class=trend-chart>${recent.map((x,i)=>`<div class=trend-col title="${x.weight} lb × ${x.reps}"><i style="height:${Math.max(8,(Number(x.e1rm||0)/max)*100)}%"></i><small>${i+1}</small></div>`).join("")}</div></div>`:""}<div class=spacer></div>${suggestion?`<div class=card><p class=eyebrow>NEXT TARGET</p><h3>${suggestion.action.replaceAll("_"," ")}</h3><p class=muted>Suggested weight: ${suggestion.suggested_weight} lb • Recent avg RPE ${suggestion.recent_average_rpe}</p></div>`:""}<div class=spacer></div><div class=stack>${recent.slice().reverse().map(x=>`<div class=card><div class=row><div><strong>${x.weight} lb × ${x.reps}</strong><p class=muted>${x.workout_name} • RPE ${x.rpe??"—"}</p></div><span>${x.e1rm} e1RM</span></div></div>`).join("")}</div>`};
}
function exercisehistory(){
const v=exerciseHistoryMarkup();return `<p class=eyebrow>EXERCISE HISTORY</p><h2 id=ehTitle>${esc(v.title)}</h2><div class=spacer></div><div class=tabs><button class="tab active">History</button><button class=tab>About</button></div><div id=ehBody class=stack>${v.body}</div>`;
}
function exerciseRecallMarkup(e){
if(S.exerciseRecallExerciseId!==e.exercise_id){
return `<p class=eyebrow>PREVIOUS PERFORMANCE</p><p class=muted>Loading last performance…</p>`;
}
const data=S.exerciseRecall;
if(!data){
return S.exerciseRecallLoading
? `<p class=eyebrow>PREVIOUS PERFORMANCE</p><p class=muted>Loading last performance…</p>`
: `<p class=eyebrow>TRAINING HISTORY</p><p class=muted>No previous data yet.</p>`;
}
const sets=data.sets||[];
const last=sets.length?sets[sets.length-1]:null;
const suggestion=data.progression_suggestion;
if(!last)return `<p class=eyebrow>FIRST SESSION</p><h3>No previous sets yet</h3><p class=muted>Log this exercise to build its history.</p>`;
const action=suggestion?suggestion.action.replaceAll("_"," "):"repeat";
const targetLabel=suggestion?.load_mode==="timed"?`${suggestion.suggested_duration_seconds} sec`:suggestion?.load_mode==="bodyweight"?`${suggestion.suggested_reps} reps`:suggestion?`${Number(suggestion.suggested_weight||0).toFixed(1).replace(/\.0$/,'')} lb × ${suggestion.suggested_reps||e.min_reps}`:`${last.weight??0} lb`;
const recent=sets.slice(-4).reverse();
return `<div class=row><div><p class=eyebrow>LAST TIME</p><h3>${last.weight} lb × ${last.reps}</h3><p class=muted>RPE ${last.rpe??"—"}</p></div>
<div style="text-align:right"><p class=eyebrow>ADAPTIVE TARGET</p><h3>${targetLabel}</h3><p class=muted>${action}${suggestion?.confidence?` • ${suggestion.confidence} confidence`:""}</p></div></div>
<div class=previous-set-strip>${recent.map((x,i)=>`<span class="${i===0?"latest":""}"><b>${Number(x.weight||0).toFixed(1).replace(/\.0$/,'')} lb × ${x.reps}</b><small>RPE ${x.rpe??"—"}</small></span>`).join("")}</div><div class=recall-actions><button class="btn dark compact" data-a=repeat-last-set>Repeat Last Set</button><button class="btn dark compact" data-a=current-exercise-history>Full History</button></div>${suggestion?`<div class=progression-why><b>Why this target?</b><span>${esc(suggestion.reason||`Recent effort averaged RPE ${suggestion.recent_average_rpe}.`)}</span><small class=muted>Based on ${suggestion.sample_count||1} recent logged set${Number(suggestion.sample_count||1)===1?"":"s"}.</small></div>`:""}</div>`;
}
function hydrateExerciseRecallInputs(e){
if(S.exerciseRecallExerciseId!==e.exercise_id||!S.exerciseRecall)return;
const sets=S.exerciseRecall.sets||[];
const last=sets.length?sets[sets.length-1]:null;
const suggestion=S.exerciseRecall.progression_suggestion;
if(!last)return;
const weight=document.querySelector("#weight");
const reps=document.querySelector("#reps");
const rpe=document.querySelector("#rpe");
if(weight)weight.value=(suggestion?.suggested_weight??last.weight??"");
if(reps)reps.value=(suggestion?.suggested_reps??last.reps??e.min_reps??"");
if(suggestion?.suggested_duration_seconds)S.exerciseTimerTarget=suggestion.suggested_duration_seconds;
if(rpe&&last.rpe!=null)rpe.value=last.rpe;
}
async function loadExerciseRecall(){
const e=w()?.exercises?.[S.ei];
if(!e)return;
const exerciseId=Number(e.exercise_id);
if(S.exerciseRecallExerciseId===exerciseId){
hydrateExerciseRecallInputs(e);
return;
}
S.exerciseRecallLoading=true;
S.exerciseRecallExerciseId=exerciseId;
S.exerciseRecall=null;
try{
const recallMode=isTimedExercise(e)?"timed":(isBodyweightExercise(e)?"bodyweight":"weight");
const data=await api(`/me/exercises/${exerciseId}/history?min_reps=${encodeURIComponent(e.min_reps||6)}&max_reps=${encodeURIComponent(e.max_reps||12)}&load_mode=${recallMode}`);
if(S.exerciseRecallExerciseId!==exerciseId)return;
S.exerciseRecall=data;
hydrateExerciseRecallInputs(e);
const card=document.querySelector("#recallCard");
if(card&&S.route==="exercise"&&Number(w()?.exercises?.[S.ei]?.exercise_id)===exerciseId)card.innerHTML=exerciseRecallMarkup(e);
}catch(err){
if(S.exerciseRecallExerciseId===exerciseId){
S.exerciseRecall=null;
const card=document.querySelector("#recallCard");
if(card)card.innerHTML=`<p class=eyebrow>TRAINING HISTORY</p><p class=muted>No previous data yet.</p>`;
}
}finally{
if(S.exerciseRecallExerciseId===exerciseId)S.exerciseRecallLoading=false;
}
}
async function loadHistory(){
if(S.historyLoading||S.historyLoaded)return;S.historyLoading=true;
try{S.historyRows=await api("/me/history");S.historyLoaded=true;if(S.route==="history")render()}catch(e){S.historyLoaded=true;toast(e.message)}finally{S.historyLoading=false}
}
const PR_LIFT_GROUPS=[
{key:"squat",label:"Squat Patterns",scope:"lower",patterns:["Squat"],icon:"🏋"},
{key:"hinge",label:"Hinge Patterns",scope:"lower",patterns:["Hinge","Hip Extension"],icon:"↘"},
{key:"lunge",label:"Lunge & Single-Leg",scope:"lower",patterns:["Lunge"],icon:"🦵"},
{key:"leg_iso",label:"Leg Isolation",scope:"lower",patterns:["Knee Extension","Knee Flexion","Calf Raise"],icon:"◒"},
{key:"push",label:"Push Patterns",scope:"upper",patterns:["Horizontal Push","Vertical Push"],icon:"↗"},
{key:"pull",label:"Pull Patterns",scope:"upper",patterns:["Horizontal Pull","Vertical Pull"],icon:"↙"},
{key:"arms",label:"Arms",scope:"upper",patterns:["Elbow Flexion","Elbow Extension"],icon:"💪"},
{key:"shoulders",label:"Shoulder Isolation",scope:"upper",patterns:["Shoulder Isolation"],icon:"◇"},
{key:"core",label:"Core",scope:"core",patterns:["Anti-Extension","Spinal Flexion","Rotation","Anti-Rotation","Anti-Lateral Flexion","Hip Flexion"],icon:"◎"},
{key:"carry",label:"Loaded Carries",scope:"core",patterns:["Loaded Carry"],icon:"▣"},
{key:"conditioning",label:"Conditioning",scope:"conditioning",patterns:["Steady-State Cardio","Interval Cardio"],icon:"♥"}
];
function prRecordValue(r){
const e=Number(r.best_e1rm||0),w=Number(r.max_weight||0),reps=Number(r.best_reps||0);
return e>0?`${e.toFixed(1).replace(/\.0$/,"")} lb est. 1RM`:w>0?`${w.toFixed(1).replace(/\.0$/,"")} lb max`:`${reps} reps`;
}
function renderPRExerciseList(rows){
if(!rows.length)return `<div class=card><p class=muted>No PRs yet.</p></div>`;
return rows.map(r=>`<button class="card pr-exercise-card" data-exhist="${r.exercise_id}">
<div class=row><div><p class=eyebrow>${esc(r.name)}</p><h3>${Number(r.max_weight||0).toFixed(1).replace(/\.0$/,"")} lb max</h3>
<p class=muted>Estimated 1RM ${Number(r.best_e1rm||0).toFixed(1).replace(/\.0$/,"")} lb • Rep PR ${r.best_reps} • Set-volume PR ${Number(r.best_volume_set||0).toFixed(0)} lb</p><small>${esc((r.trend||"steady").toUpperCase())}</small></div><span>›</span></div></button>`).join("");
}
function renderPRLiftGroups(rows){
let groups=PR_LIFT_GROUPS.map(g=>({...g,records:rows.filter(r=>g.patterns.includes(r.movement_pattern))}));
const other=rows.filter(r=>!PR_LIFT_GROUPS.some(g=>g.patterns.includes(r.movement_pattern)));
if(other.length)groups.push({key:"other",label:"Other",scope:"all",icon:"•",records:other});
if(S.prLiftFilter!=="all")groups=groups.filter(g=>g.scope===S.prLiftFilter);
groups=groups.filter(g=>g.records.length);
if(!groups.length)return `<div class=card><h3>No records in this category</h3><p class=muted>Complete these exercises to build records.</p></div>`;
return groups.map(g=>{
const sorted=g.records.slice().sort((a,b)=>Number(b.best_e1rm||b.max_weight||0)-Number(a.best_e1rm||a.max_weight||0));
const top=sorted[0],collapsed=!!S.prCollapsedGroups[g.key];
return `<div class="card pr-lift-group">
<button class=pr-lift-header data-pr-group="${g.key}">
<span class=pr-lift-icon>${g.icon}</span><span class=pr-lift-title><strong>${esc(g.label)}</strong><small>${sorted.length} exercise${sorted.length===1?"":"s"}</small></span>
<span class=pr-lift-best><small>Best</small><b>${esc(prRecordValue(top))}</b></span><span class=pr-lift-chevron>${collapsed?"⌄":"⌃"}</span></button>
${collapsed?"":`<div class=pr-lift-exercises>${sorted.map(r=>`<button class=pr-lift-row data-exhist="${r.exercise_id}"><span><b>${esc(r.name)}</b><small>${esc(r.movement_pattern||"Other")}</small></span><span class=pr-lift-row-value><b>${esc(prRecordValue(r))}</b><small>${Number(r.best_reps||0)} best reps</small></span><i>›</i></button>`).join("")}</div>`}
</div>`;
}).join("");
}
function renderPRList(){
const el=document.querySelector("#prList");if(!el)return;
el.innerHTML=S.prView==="lift"?renderPRLiftGroups(S.prRecords||[]):renderPRExerciseList(S.prRecords||[]);
document.querySelectorAll("[data-exhist]").forEach(b=>b.onclick=()=>{S.historyExercise=Number(b.dataset.exhist);go("exercisehistory")});
document.querySelectorAll("[data-pr-group]").forEach(b=>b.onclick=()=>{const k=b.dataset.prGroup;S.prCollapsedGroups[k]=!S.prCollapsedGroups[k];renderPRList()});
}
async function loadPRs(){
if(S.prLoading||S.prLoaded)return;S.prLoading=true;
try{S.prRecords=await api("/me/prs");S.prLoaded=true;if(S.route==="prs")render()}catch(e){S.prLoaded=true;toast(e.message)}finally{S.prLoading=false}
}
async function loadExerciseHistory(){
const exerciseId=Number(S.historyExercise||0);if(!exerciseId)return;
if(Number(S.exerciseHistoryExerciseId)===exerciseId&&(S.exerciseHistoryData||S.exerciseHistoryLoading))return;
S.exerciseHistoryExerciseId=exerciseId;S.exerciseHistoryLoading=true;S.exerciseHistoryData=null;
try{
const data=await api(`/me/exercises/${exerciseId}/history`);
if(Number(S.exerciseHistoryExerciseId)!==exerciseId)return;
S.exerciseHistoryData=data;S.exerciseHistoryLoading=false;
if(S.route==="exercisehistory"&&Number(S.historyExercise)===exerciseId)render();
}catch(e){if(Number(S.exerciseHistoryExerciseId)===exerciseId)S.exerciseHistoryData={name:"Exercise",prs:{},sets:[],progression_suggestion:null};toast(e.message)}
finally{if(Number(S.exerciseHistoryExerciseId)===exerciseId)S.exerciseHistoryLoading=false}
}
async function loadProgressHub(){
if(!authToken||S.progressHubLoading||S.progressHub)return;
S.progressHubLoading=true;
try{S.progressHub=await api("/me/progress/hub");if(S.route==="progress")render()}catch(e){console.warn("Progress hub load failed",e)}finally{S.progressHubLoading=false}
}
function progressHubOverview(){
const h=S.progressHub;if(!h)return `<div class="card progress-hub-card"><p class=eyebrow>PROGRESS HUB</p><h3>Loading training data…</h3></div>`;
const k=h.kpis||{};
return `<div class="card progress-hub-card"><div class=row><div><p class=eyebrow>PROGRESS HUB 2.0</p><h3>${esc(h.headline||"Your long-term picture")}</h3></div><b>${h.score==null?"—":h.score}/100</b></div>
<div class=progress-hub-kpis>
<span><small>ADHERENCE</small><b>${k.adherence_percent==null?"—":Math.round(k.adherence_percent)+"%"}</b></span>
<span><small>STRENGTH</small><b>${k.strength_change_percent==null?"—":`${k.strength_change_percent>0?"+":""}${Number(k.strength_change_percent).toFixed(1)}%`}</b></span>
<span><small>TRAINING VOLUME</small><b>${Math.round(k.total_volume||0).toLocaleString()} lb</b></span>
<span><small>PRs</small><b>${k.pr_count||0}</b></span>
</div>
<div class=progress-hub-signals>${(h.signals||[]).map(x=>`<div class="${x.status||"neutral"}"><span>${esc(x.label)}</span><b>${esc(String(x.value))}</b><small>${esc(x.detail||"")}</small></div>`).join("")}</div>
<div class=spacer></div><p class=muted>${esc(h.next_action||"Keep logging consistently to strengthen the trend model.")}</p></div>`;
}
async function loadProgressIntelligence(){
if(S.progressIntelligenceLoading)return;
S.progressIntelligenceLoading=true;
try{
S.progressIntelligence=await api("/me/progress/intelligence");
if(S.route==="progress")render();
}catch(e){console.warn("Progress intelligence failed",e)}finally{S.progressIntelligenceLoading=false}
}
function progressIntelligenceCard(){
const x=S.progressIntelligence;
if(!x)return `<div class="card progress-intelligence-card"><p class=eyebrow>PROGRESS INTELLIGENCE</p><h3>Analyzing your training...</h3><p class=muted>Combining training, recovery, and nutrition.</p></div>`;
const score=x.score==null?"—":x.score;
return `<div class="card progress-intelligence-card ${esc(x.status)}">
<div class=row><div><p class=eyebrow>PROGRESS INTELLIGENCE</p><h3>${esc(x.headline)}</h3></div><div class=progress-score><b>${score}</b><small>/100</small></div></div>
<div class=progress-signal-grid>${(x.signals||[]).slice(0,4).map(s=>`<div class="progress-signal ${s.status}"><small>${esc(s.label)}</small><b>${esc(s.value)}</b></div>`).join("")}</div>
<div class=spacer></div><p class=muted>${esc((x.recommendations||[])[0]||"Keep logging training so Forge can identify meaningful trends.")}</p>
<div class=spacer></div><button class="btn dark" data-progress-coach="Analyze my progress and tell me what is limiting me">Ask Coach About My Progress</button>
</div>`;
}
async function loadBodyMetrics(){
if(S.bodyMetricsLoading)return;
S.bodyMetricsLoading=true;
try{
S.bodyMetrics=await api(`/me/body-metrics?range_days=${encodeURIComponent(S.bodyMetricRange)}`);
if(S.route==="progress")render();
}catch(e){console.warn("Body metrics load failed",e)}finally{S.bodyMetricsLoading=false}
}
function bodyMetricChart(metric,label,unit){
const pts=S.bodyMetrics?.metrics?.[metric]?.points||[];
if(!pts.length)return `<div class=body-chart-empty>No ${esc(label.toLowerCase())} data yet.</div>`;
const W=320,H=105,P=13;
const vals=pts.map(x=>Number(x.value)),min0=Math.min(...vals),max0=Math.max(...vals);
let min=min0,max=max0;if(min===max){min-=1;max+=1}
const pad=Math.max((max-min)*.15,.25);min-=pad;max+=pad;
const coords=pts.map((p,i)=>({x:pts.length===1?W/2:P+i*(W-P*2)/(pts.length-1),y:P+(max-p.value)/(max-min)*(H-P*2),p}));
return `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none"><polyline class=body-metric-line points="${coords.map(c=>`${c.x},${c.y}`).join(" ")}"/>${coords.map(c=>`<circle class=body-metric-dot cx="${c.x}" cy="${c.y}" r=3.5><title>${c.p.date}: ${c.p.value} ${unit}</title></circle>`).join("")}</svg>`;
}
function bodyTrackingCard(){
const b=S.bodyMetrics,m=b?.metrics||{},w=m.weight_lb||{};
const latest=(b?.entries||[])[0];
const delta=w.change;
return `<div class=card><div class=row><div><p class=eyebrow>BODY TRACKING</p><h3>${w.current!=null?`${Number(w.current).toFixed(1)} lb`:"Add your first check-in"}</h3><p class=muted>${delta!=null&&w.points?.length>=2?`${delta>0?"+":""}${Number(delta).toFixed(1)} lb over this range`:"Track weight and optional measurements over time."}</p></div><button class="btn dark compact" data-a=body-metric-add>+ Check-In</button></div>
<div class=body-range>${[["30","30D"],["90","90D"],["365","1Y"],["all","ALL"]].map(x=>`<button class="${S.bodyMetricRange===x[0]?"active":""}" data-body-range="${x[0]}">${x[1]}</button>`).join("")}</div>
<div class=body-chart>${bodyMetricChart("weight_lb","Bodyweight","lb")}</div>
${latest?`<div class=body-latest-grid>${[["body_fat_pct","Body Fat","%"],["waist_in","Waist","in"],["chest_in","Chest","in"],["arm_in","Arm","in"]].map(([k,l,u])=>`<div><small>${l}</small><b>${latest[k]!=null?`${Number(latest[k]).toFixed(1)} ${u}`:"—"}</b></div>`).join("")}</div>`:""}
${b?.entries?.length?`<div class=spacer></div><div class=body-history>${b.entries.slice(0,5).map(x=>`<div class=body-history-row><div><b>${esc(x.entry_date)}</b><small>${x.weight_lb!=null?`${Number(x.weight_lb).toFixed(1)} lb`:"Measurements"}</small></div><button data-body-delete="${x.id}">×</button></div>`).join("")}</div>`:""}
</div>
${S.bodyMetricModal?bodyMetricModal():""}`;
}
function bodyMetricModal(){
const today=new Date().toISOString().slice(0,10);
return `<div class=nutrition-modal><div class=nutrition-dialog><p class=eyebrow>BODY CHECK-IN</p><h2>Log Measurements</h2><p class=muted>Enter only what you measured.</p>
<div class=nutrition-form><label>Date<input id=bodyDate type=date value="${today}"></label><label>Weight (lb)<input id=bodyWeight type=number min=0 step=.1 placeholder="e.g. 185.4"></label>
<div class=body-measure-grid><label>Body Fat (%)<input id=bodyFat type=number min=0 step=.1></label><label>Waist (in)<input id=bodyWaist type=number min=0 step=.1></label><label>Chest (in)<input id=bodyChest type=number min=0 step=.1></label><label>Hips (in)<input id=bodyHips type=number min=0 step=.1></label><label>Arm (in)<input id=bodyArm type=number min=0 step=.1></label><label>Thigh (in)<input id=bodyThigh type=number min=0 step=.1></label></div><label>Notes<input id=bodyNotes maxlength=500 placeholder="Optional"></label></div>
<div class=spacer></div><button class=btn data-a=body-metric-save>Save Check-In</button><div class=spacer></div><button class="btn dark" data-a=body-metric-close>Cancel</button></div></div>`;
}
async function loadIntelligenceCore(){if(S.intelligenceCoreLoading||S.intelligenceCore)return;S.intelligenceCoreLoading=true;try{S.intelligenceCore=await api("/me/intelligence/core");if(["coach","progress"].includes(S.route))render()}catch(e){console.warn("Intelligence Core failed",e)}finally{S.intelligenceCoreLoading=false}}
async function loadExplainableProgramming(){if(S.explainableProgrammingLoading||S.explainableProgramming)return;S.explainableProgrammingLoading=true;try{S.explainableProgramming=await api("/me/intelligence/explain");if(["coach","progress"].includes(S.route))render()}catch(e){console.warn("Explainable programming failed",e)}finally{S.explainableProgrammingLoading=false}}
function explainableProgrammingCard(){const x=S.explainableProgramming;if(!x)return "";const cards=(x.cards||[]).slice(0,5),g=x.governance?.winner;return `<div class="card"><div class=row><div><p class=eyebrow>WHY FORGE CHANGED IT</p><h3>Explainable programming</h3></div>${g?`<b>${esc(String(g.action||"hold").toUpperCase())}</b>`:""}</div><p class=muted>${g?esc(g.reason):"Every meaningful programming change includes its evidence, confidence, scope, and duration."}</p>${cards.length?cards.map(d=>`<div class=coach4-prog><b>${esc(d.title)}${d.target?` • ${esc(d.target)}`:""}</b><span>${esc(d.confidence||"medium")} confidence • ${esc(d.scope||"program")} • ${esc(d.duration||"persistent")}</span><small>${esc(d.why||"Programming evidence")}</small></div>`).join(""):`<small>No programming changes yet.</small>`}</div>`}
function intelligenceCoreCard(){const c=S.intelligenceCore;if(!c)return "";const ds=(c.decisions||[]).slice(0,5);return `<div class="card intelligence-core-card"><div class=row><div><p class=eyebrow>FORGE INTELLIGENCE CORE</p><h3>Programming decisions</h3></div><b>${c.decision_counts?.applied||0}</b></div><p class=muted>See what changed, why, and for how long.</p>${ds.length?`<div class=stack>${ds.map(d=>`<div class=coach4-prog><b>${esc(String(d.decision_type).replaceAll("_"," "))}</b><span>${esc(d.scope)} • ${esc(d.duration)} • ${esc(d.confidence)} confidence</span><small>${esc(d.evidence)}</small></div>`).join("")}</div>`:`<small>No programming changes recorded yet.</small>`}</div>`}
async function loadStrategyDashboard(){if(S.strategyDashboardLoading||S.strategyDashboard)return;S.strategyDashboardLoading=true;try{S.strategyDashboard=await api("/me/training/strategy-dashboard");if(["home","progress","coach"].includes(S.route))render()}catch(e){console.warn("Strategy dashboard failed",e)}finally{S.strategyDashboardLoading=false}}
function strategyDashboardCard(){const d=S.strategyDashboard;if(!d)return "";const st=d.strategy||{},sp=st.specialization||[],rf=d.recovery_forecast||{},a=d.authority?.controls||{},modes={recommend_only:"Recommend",ask_first:"Ask first",auto_apply:"Auto"};return `<div class="card strategy-dashboard"><div class=row><div><p class=eyebrow>TRAINING STRATEGY</p><h3>${esc(String(st.strategy||"hypertrophy_accumulation").replaceAll("_"," "))}</h3></div><b>${esc(st.mesocycle_phase||"")}</b></div><p class=muted>${esc(st.rationale||"")}</p>${sp.length?`<p><b>Specialization:</b> ${sp.map(esc).join(", ")}</p>`:""}<div class=coach4-grid><span><b>${esc(rf.next_session_mode||"normal")}</b><small>Recovery forecast</small></span><span><b>${d.rotation_summary?.retain||0}</b><small>Exercises retained</small></span><span><b>${d.rotation_summary?.rotate||0}</b><small>Rotation candidates</small></span></div><div class=spacer></div><p class=eyebrow>FORGE AUTHORITY</p>${Object.entries(a).map(([k,v])=>`<label class=row><span>${esc(k.replaceAll("_"," "))}</span><select data-authority="${esc(k)}"><option value="recommend_only" ${v==="recommend_only"?"selected":""}>Recommend only</option><option value="ask_first" ${v==="ask_first"?"selected":""}>Ask first</option><option value="auto_apply" ${v==="auto_apply"?"selected":""}>Auto-apply</option></select></label>`).join("")}<small>Choose what Forge may change automatically.</small></div>`}
async function saveAuthority(domain,mode){try{const current={...(S.strategyDashboard?.authority?.controls||{}),[domain]:mode};await api("/me/programming/authority",{method:"PUT",body:JSON.stringify({controls:current})});S.strategyDashboard=null;await loadStrategyDashboard()}catch(e){toast(e.message)}}
async function loadPlanEditorSnapshot(){if(S.planEditorLoading)return;S.planEditorLoading=true;try{S.planEditorSnapshot=await api("/me/plan/editor-snapshot");if(S.route==="workoutbuilder")render()}catch(e){console.warn("Plan editor snapshot failed",e)}finally{S.planEditorLoading=false}}
async function loadTrainingRecords(){if(S.trainingRecords?.loading)return;S.trainingRecords={loading:true};try{S.trainingRecords=await api("/me/training-records");if(S.route==="progress")render()}catch(e){console.warn("Training records failed",e)}}
function trainingRecordsCard(){const d=S.trainingRecords;if(!d||d.loading)return "";const cards=(d.exercise_cards||[]).slice(0,6),blocks=d.mesocycle_history||[];return `<div class="card records3-card"><div class=row><div><p class=eyebrow>TRAINING HISTORY 3.0</p><h3>Exercise progress</h3></div><b>${d.exercise_cards.length}</b></div><div class=record-card-grid>${cards.map(x=>`<div><b>${esc(x.name)}</b><span>${x.sessions} sessions</span><strong>${x.change_percent>0?"+":""}${x.change_percent}%</strong><small>Best e1RM ${Math.round(x.best_e1rm||0)} lb • ${x.best_reps||0} rep PR</small></div>`).join("")}</div>${blocks.length?`<div class=spacer></div><p class=eyebrow>MESOCYCLE COMPARISON</p><div class=block-history>${blocks.slice(-4).map(x=>`<span><b>Block ${x.block}</b><small>${x.workouts} workouts • ${x.sets} sets • ${Math.round(x.volume).toLocaleString()} lb</small></span>`).join("")}</div>`:""}</div>`}
function progress(){
const done=(plan?.workouts||[]).filter(x=>x.status==="completed").length;
const t=S.strengthTrend;
const summary=t?.summary||{};
const change=Number(summary.change_percent||0);
const changeText=(change>0?"+":"")+change.toFixed(1)+"%";
return `${strategyDashboardCard()}<div class=big-spacer></div>${explainableProgrammingCard()}<div class=big-spacer></div>${intelligenceCoreCard()}<div class=big-spacer></div>${trainingRecordsCard()}<div class=big-spacer></div>${muscleDevelopmentCard()}<div class=big-spacer></div>${trainingDashboardCard()}<div class=big-spacer></div><p class=eyebrow>PROGRESS</p><h2>Your Progress</h2>
<div class=spacer></div><div class=progress-cards>
<div class=progress-card><b>${done}</b><small>Workouts</small></div>
<div class=progress-card><b>${summary.data_points||0}</b><small>Trend Points</small></div>
<div class=progress-card><b class="${change>=0?"trend-positive":"trend-negative"}">${t?changeText:"—"}</b><small>Strength Progress</small></div>
</div>
<div class=big-spacer></div>
${progressHubOverview()}
<div class=big-spacer></div>
${progressIntelligenceCard()}
<div class=big-spacer></div>
${progressVisualSummary()}
<div class=big-spacer></div>
${bodyTrackingCard()}
<div class=big-spacer></div>
<div class=row><div><h3>Strength Progress</h3><p class=muted>${t?(t.mode==="overall"?"Change in your estimated strength since you started":esc(t.title)):"Loading your logged strength data..."}</p></div><button class="btn dark compact" data-a=history>History</button></div>
<div class=spacer></div>
<div class=strength-controls>
<select id=strengthExercise class=strength-select>
<option value=overall ${S.strengthExercise==="overall"?"selected":""}>Overall Progress</option>
${(t?.exercises||[]).map(e=>`<option value="${e.exercise_id}" ${String(S.strengthExercise)===String(e.exercise_id)?"selected":""}>${esc(e.name)}</option>`).join("")}
</select>
<div class=strength-ranges>
${[["30","30D"],["90","90D"],["365","1Y"],["all","ALL"]].map(x=>`<button class="${S.strengthRange===x[0]?"active":""}" data-strength-range=${x[0]}>${x[1]}</button>`).join("")}
</div>
</div>
<div class=spacer></div>
<div id=strengthChart class="line-chart interactive-chart">
${t?renderStrengthChart(t):`<div class=chart-empty>Loading...</div>`}
</div>
<div id=strengthPointDetail class=strength-point-detail>
${renderStrengthPointDetail(t,S.strengthPoint)}
</div>
<div class=spacer></div>
${t&&summary.data_points?`<div class=strength-summary>
${t.mode==="overall"
?`<div><small>Since You Started</small><b class="${change>=0?"trend-positive":"trend-negative"}">${changeText}</b></div>
<div><small>Best Progress</small><b>${(Number(summary.best||0)>0?"+":"")}${Number(summary.best||0).toFixed(1)}%</b></div>
<div><small>Baseline</small><b>0%</b></div>`
:`<div><small>Current Est. Strength</small><b>${formatStrengthValue(summary.current,t.unit)}</b></div>
<div><small>Best Est. Strength</small><b>${formatStrengthValue(summary.best,t.unit)}</b></div>
<div><small>Since You Started</small><b class="${change>=0?"trend-positive":"trend-negative"}">${changeText}</b></div>`}
</div>`:""}
<div class=big-spacer></div><button class="btn dark" data-a=prs>View Personal Records</button>`;
}
function formatStrengthValue(v,unit){
const n=Number(v||0);
if(unit==="lb")return `${Math.round(n)} lb`;
if(unit==="percent")return `${n>0?"+":""}${n.toFixed(1)}%`;
return n.toFixed(1);
}
function renderStrengthChart(data){
const pts=data?.points||[];
if(!pts.length)return `<div class=chart-empty>Log working sets to build progress.</div>`;
const W=320,H=145,PX=13,PY=18;
let values=pts.map(p=>Number(data.mode==="overall"?(p.progress_percent??p.value):p.value));
let min=Math.min(...values),max=Math.max(...values);
if(data.mode==="overall"){min=Math.min(min,0);max=Math.max(max,0)}
if(max===min){max+=1;min-=1}
const pad=Math.max((max-min)*.12,.5);min-=pad;max+=pad;
const coords=pts.map((p,i)=>{
const val=Number(data.mode==="overall"?(p.progress_percent??p.value):p.value);
const x=pts.length===1?W/2:PX+i*(W-PX*2)/(pts.length-1);
const y=PY+(max-val)/(max-min)*(H-PY*2);
return {x,y,p,i};
});
const path=coords.map(c=>`${c.x.toFixed(1)},${c.y.toFixed(1)}`).join(" ");
const baselineY=data.mode==="overall"
?PY+(max-0)/(max-min)*(H-PY*2)
:H-PY;
const area=`${coords[0].x.toFixed(1)},${baselineY.toFixed(1)} ${path} ${coords[coords.length-1].x.toFixed(1)},${baselineY.toFixed(1)}`;
return `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-label="Strength progress chart">
<defs><linearGradient id=strengthFill x1=0 y1=0 x2=0 y2=1><stop offset=0 stop-color="#e52a36" stop-opacity=".23"/><stop offset=1 stop-color="#e52a36" stop-opacity="0"/></linearGradient></defs>
<line x1="${PX}" y1="${baselineY}" x2="${W-PX}" y2="${baselineY}" class="chart-grid baseline-grid" />
<line x1="${PX}" y1="${H/2}" x2="${W-PX}" y2="${H/2}" class=chart-grid />
<polygon points="${area}" fill="url(#strengthFill)"/>
<polyline points="${path}" class=strength-line />
${coords.map(c=>`<circle class="strength-dot ${S.strengthPoint===c.i?"selected":""}" cx="${c.x}" cy="${c.y}" r="${S.strengthPoint===c.i?5:3.6}" data-strength-point=${c.i}></circle>`).join("")}
</svg>`;
}
function renderStrengthPointDetail(data,index){
const pts=data?.points||[];
if(!pts.length)return "";
const i=index==null?pts.length-1:Math.max(0,Math.min(Number(index),pts.length-1));
const p=pts[i];
const date=new Date(`${p.date}T12:00:00`).toLocaleDateString(undefined,{month:"short",day:"numeric",year:"numeric"});
if(data.mode==="exercise"){
const pct=Number(p.progress_percent||0);
return `<div><span><b>${formatStrengthValue(p.value,data.unit)}</b><small>Estimated Strength</small></span><span><b class="${pct>=0?"trend-positive":"trend-negative"}">${pct>0?"+":""}${pct.toFixed(1)}%</b><small>Since You Started • ${date}</small></span></div>`;
}
const pct=Number(p.progress_percent??p.value??0);
return `<div><span><b class="${pct>=0?"trend-positive":"trend-negative"}">${pct>0?"+":""}${pct.toFixed(1)}%</b><small>Strength Progress</small></span><span><b>${date}</b><small>Since permanent baseline</small></span></div>`;
}
async function loadStrengthTrend(){
if(!authToken||S.strengthTrendLoading)return;
S.strengthTrendLoading=true;
const exercise=S.strengthExercise==="overall"?"":`&exercise_id=${encodeURIComponent(S.strengthExercise)}`;
try{
const data=await api(`/me/strength-trend?range_days=${encodeURIComponent(S.strengthRange)}${exercise}`);
S.strengthTrend=data;
const maxIndex=Math.max(0,(data.points||[]).length-1);
if(S.strengthPoint==null||S.strengthPoint>maxIndex)S.strengthPoint=maxIndex;
if(S.route==="progress")render();
}catch(e){
console.warn("Strength trend load failed",e);
S.strengthTrend={points:[],exercises:[],summary:{data_points:0,change_percent:0,current:0,best:0},title:"Strength Progress",unit:"percent",mode:"overall"};
if(S.route==="progress")render();
}finally{S.strengthTrendLoading=false}
}
