// Forge Fitness v15.11.0 — extracted loadCoachBriefing..before planScreen
async function loadCoachBriefing(){
if(!authToken||S.coachBriefingLoading||S.coachBriefing)return;
S.coachBriefingLoading=true;
try{S.coachBriefing=await api("/me/coach/briefing");if(S.route==="coach")render()}catch(e){console.warn("Coach briefing failed",e)}finally{S.coachBriefingLoading=false}
}
function coachBriefingCard(){
const b=S.coachBriefing;if(!b)return `<div class="card coach-briefing"><p class=eyebrow>WHOLE-DAY CONTEXT</p><h3>Building your training summary…</h3></div>`;
const chips=[
["Readiness",b.readiness?.label||"Unknown"],
["Recovery",b.recovery?.level||"Unknown"],
["Progress",b.progress?.headline||"Building data"],
["Calendar",b.calendar?.conflicts?`${b.calendar.conflicts} conflict${b.calendar.conflicts===1?"":"s"}`:"Clear"],
["Nutrition",b.nutrition?.summary||"No data"]
];
return `<div class="card coach-briefing"><div class=row><div><p class=eyebrow>TODAY’S COACHING</p><h3>${esc(b.headline||"Your training picture")}</h3></div><b>${b.score==null?"—":b.score}/100</b></div>
<div class=coach-context-chips>${chips.map(([k,v])=>`<span><small>${k}</small><b>${esc(String(v))}</b></span>`).join("")}</div>
<div class=spacer></div><p class=muted>${esc(b.recommendation||"Keep logging so Forge can connect more signals.")}</p>
${(b.actions||[]).length?`<div class=coach-stack-preview><p class=eyebrow>CONNECTED ACTIONS</p>${b.actions.map((a,i)=>`<div><span>${i+1}</span><p><b>${esc(a.title)}</b><small>${esc(a.reason)}</small></p></div>`).join("")}</div>`:""}</div>`;
}
function coachActionTitle(a){
if(!a)return "";
if(a.action_type==="shorten_workout")return `Shorten workout to ${a.target_minutes} minutes`;
if(a.action_type==="move_workout")return "Move workout";
if(a.action_type==="swap_workouts")return "Swap workout days";
if(a.action_type==="skip_workout")return "Skip workout";
if(a.action_type==="restore_workout")return "Restore workout";
if(a.action_type==="set_nutrition_targets")return "Set nutrition targets";
if(a.action_type==="log_nutrition_meal")return "Log meal";
if(a.action_type==="swap_exercise")return "Swap exercise";
return "Update";
}
async function loadCoach4(){if(S.coach4?.loading)return;S.coach4={loading:true};try{S.coach4=await api("/me/coach/context-v4");if(S.route==="coach")render()}catch(e){console.warn("Coach 4 context failed",e)}}
function coach4ContextCard(){const c=S.coach4;if(!c||c.loading)return "";const m=c.mesocycle||{},muscles=(c.muscle_status||[]).slice(0,4),prog=(c.exercise_progression||[]).slice(0,3);return `<div class="card coach4-context"><div class=row><div><p class=eyebrow>PROGRAMMING COACH</p><h3>Block ${m.block_number} • Week ${m.week_in_block}/${m.block_length}</h3></div><b>${esc(m.phase||"")}</b></div><p class=muted>Forge explains decisions using your training, recovery, schedule, and nutrition.</p><div class=coach4-grid>${muscles.map(x=>`<span><b>${esc(x.muscle)}</b><small>${x.actual_sets}/${x.target_sets} sets</small></span>`).join("")}</div>${prog.length?`<div class=spacer></div>${prog.map(x=>`<div class=coach4-prog><b>${esc(x.name)}</b><span>${esc(x.status)} • ${esc(x.method)}</span></div>`).join("")}`:""}</div>`}
function coach(){
const msgs=S.coachMessages||[],c=S.coachContext;
return `${strategyDashboardCard()}<div class=spacer></div>${explainableProgrammingCard()}<div class=spacer></div>${intelligenceCoreCard()}<div class=spacer></div>${coach4ContextCard()}<div class=spacer></div><div class=row><div><p class=eyebrow>FORGE COACH</p><h2>AI Coach</h2></div><button class="btn dark compact" data-a=clear-coach>Clear</button></div>
<p class=muted>Coaching based on your Forge data.</p>
<div class="coach-model-status ${S.coachStatus?.llm_enabled?"online":"fallback"}"><span>${S.coachStatus?.llm_enabled?"● AI online":"● Smart fallback"}</span><small>${S.coachStatus?.llm_enabled?esc(S.coachStatus.model||"OpenAI"):"Set OPENAI_API_KEY to enable the LLM"}</small></div>
${c?`<div class=spacer></div><div class=coach-context><div><b>${c.recent_completed_workouts}</b><small>Recent Workouts</small></div><div><b>${Number(c.fatigue_score||0).toFixed(1)}</b><small>Fatigue</small></div><div><b>${c.week_number||1}</b><small>Week</small></div></div>`:""}
<div class=spacer></div>${coachBriefingCard()}
<div class=spacer></div>
<div class=coach-action-launcher>
<button data-coachprompt="Review my readiness, recovery, calendar, nutrition, and recent progress together, then propose the best changes for today"><span>⚙</span><b>Adjust Today</b><small>Use recovery + training</small></button>
<button data-coachprompt="Find the best exercise swap for my current workout using only my equipment"><span>⇄</span><b>Smart Swap</b><small>Equipment-aware replacement</small></button>
<button data-coachprompt="Check my calendar availability, recovery spacing, and propose the best workout placement this week"><span>▦</span><b>Calendar Intelligence</b><small>Conflicts + recovery</small></button>
<button data-coachprompt="Review my progress and tell me whether next week should progress, maintain, or recover"><span>↗</span><b>Next Week</b><small>Plan recommendation</small></button>
</div>
<div class=spacer></div><div class=coach-prompts>
<button data-coachprompt="What am I doing today?">Today's workout</button>
<button data-coachprompt="I'm sore and tired today. What should I do?">I'm sore</button>
<button data-coachprompt="Am I making progress?">My progress</button>
<button data-coachprompt="What are my personal records?">My PRs</button>
<button data-coachprompt="I only have 25 minutes today">25-minute workout</button><button data-coachprompt="Move my Thursday workout to Saturday">Move a workout</button>
<button data-coachprompt="Set nutrition goals based on my fitness goal">Nutrition goals</button>
<button data-coachprompt="How am I doing on nutrition today?">Today's nutrition</button>
<button data-coachprompt="What should I eat to fit my remaining macros?">Meal idea</button>
<button data-coachprompt="How should I eat for my workout today?">Training fuel</button>
<button data-coachprompt="I had a large chicken sandwich and fries from Chick-fil-A for lunch">Log restaurant food</button><button id=nutritionProviderStatusBtn>Provider status</button>
</div><div class=big-spacer></div><div class=chat id=coachChat>
${msgs.length?msgs.map(coachMessageHTML).join(""):`<div class="bubble ai coach-rich-response"><div>Ask about training, recovery, progress, nutrition, or log a meal.</div><div class=coach-response-actions><button data-coach-route=workout>Today’s Workout</button><button data-coach-route=nutrition>Nutrition</button></div></div>`}
${S.coachAction?`<div class=coach-plan><p class=eyebrow>SUGGESTED CHANGE</p>
<h3>${esc(S.coachAction.preview?.title||coachActionTitle(S.coachAction))}</h3>
${S.coachAction.preview?.from?`<div class=coach-change-row><span>${esc(S.coachAction.preview.from)}</span><b>→</b><span>${esc(S.coachAction.preview.to)}</span></div>`:""}
${(S.coachAction.preview?.components||[]).length?`<div class=coach-nutrition-components>${S.coachAction.preview.components.map(x=>`<span>${esc(x)}</span>`).join("")}</div>`:""}
${S.coachAction.preview?.source?`<p class=coach-food-source>Source: ${esc(S.coachAction.preview.source)}</p>`:""}
${(S.coachAction.preview?.warnings||[]).map(x=>`<p class=coach-warning>⚠ ${esc(x)}</p>`).join("")}
<div class=spacer></div><button class=btn data-a=apply-coach>${S.coachAction.action_type==="log_nutrition_meal"?"Log Meal":S.coachAction.action_type==="set_nutrition_targets"?"Set Targets":"Apply Change"}</button></div>`:""}
</div><div class=coach-composer-wrap><div class=composer><input id=coachInput placeholder="Ask Forge Coach..."><button data-a=sendcoach>➤</button></div></div>`;
}
async function loadCoach(){
if(!authToken||S.coachLoading||S.coachLoaded)return;
S.coachLoading=true;
try{
const [messages,context,status]=await Promise.all([api("/me/coach/history"),api("/me/coach/context"),api("/me/coach/status")]);
S.coachMessages=(messages||[]).map(x=>({role:x.role==="assistant"?"ai":"user",text:x.message}));
S.coachContext=context;S.coachStatus=status;S.coachLoaded=true;
if(S.route==="coach")render();
}catch(e){console.warn("Coach load failed",e)}finally{S.coachLoading=false}
}
async function sendCoach(textOverride=null){
const input=document.querySelector("#coachInput");
const text=(textOverride||input?.value||"").trim();if(!text)return;
S.coachMessages.push({role:"user",text});S.coachAction=null;render();
try{
const payload={message:text,workout_id:w()?.workout_id||plan?.workouts?.[0]?.workout_id||null};
const data=await api("/me/coach",{method:"POST",body:JSON.stringify(payload)});
S.coachMessages.push({role:"ai",text:data.reply});S.coachAction=data.action||null;
if(S.coachContext){
S.coachContext.fatigue_score=data.context?.fatigue_score??S.coachContext.fatigue_score;
S.coachContext.week_number=data.context?.week_number??S.coachContext.week_number;
S.coachContext.recent_completed_workouts=data.context?.recent_completed_workouts??S.coachContext.recent_completed_workouts;
}
}catch(e){S.coachMessages.push({role:"ai",text:`I couldn't process that request: ${e.message}`})}
render();
}
async function applyCoachAction(){
if(!S.coachAction)return;
const actionType=S.coachAction.action_type;
const result=await api("/me/coach/apply",{method:"POST",body:JSON.stringify(S.coachAction)});
try{plan=await api("/me/plan/current")}catch{}
if(["set_nutrition_targets","log_nutrition_meal"].includes(actionType)){
S.nutrition=null;
}
S.coachMessages.push({role:"ai",text:result.reply||"Done."});
S.coachAction=null;
toast(actionType==="log_nutrition_meal"?"Meal logged":actionType==="set_nutrition_targets"?"Nutrition targets updated":actionType==="swap_exercise"?"Exercise swapped":"Plan updated");
render();
}
async function loadRecoveryIntelligence(){if(S.recoveryIntelligenceLoading||S.recoveryIntelligence)return;S.recoveryIntelligenceLoading=true;try{S.recoveryIntelligence=await api("/me/recovery-intelligence");if(S.route==="plan")render()}catch(e){console.warn("Recovery intelligence failed",e)}finally{S.recoveryIntelligenceLoading=false}}
async function loadAdaptationPreview(){
if(!authToken||!plan||S.adaptationPreviewLoading||S.adaptationPreview)return;
S.adaptationPreviewLoading=true;
try{
S.adaptationPreview=await api("/me/program/adaptation-preview");
if(S.route==="plan")render();
}catch(e){console.warn("Adaptation preview failed",e)}finally{S.adaptationPreviewLoading=false}
}
async function applyAdaptiveWeek(){
if(S.adaptationBusy)return;
S.adaptationBusy=true;render();
try{
const data=await api("/me/program/apply-adaptation",{method:"POST"});
plan=data.plan;S.adaptationPreview=data.adaptation||null;
S.planTab="overview";
toast(`Week ${data.state?.week_number||""} generated`);
}catch(e){toast(e.message)}
S.adaptationBusy=false;render();
}
function recoveryCard(){const r=S.recoveryIntelligence;if(!r)return `<div class="card"><p class=eyebrow>RECOVERY</p><p class=muted>Analyzing recovery…</p></div>`;return `<div class="card recovery-card ${r.level}"><p class=eyebrow>RECOVERY + DELOAD</p><h3>${esc(r.title)}</h3><p class=muted>${esc(r.recommendation||"")}</p>${(r.flags||[]).length?`<div class=stack>${r.flags.map(x=>`<small>• ${esc(x)}</small>`).join("")}</div>`:""}<div class=adaptation-metrics><div><small>Fatigue</small><b>${Number(r.fatigue_score||0).toFixed(1)}/10</b></div><div><small>Avg effort</small><b>${r.average_rpe==null?"—":Number(r.average_rpe).toFixed(1)}</b></div><div><small>Adherence</small><b>${r.adherence_percent==null?"—":Math.round(r.adherence_percent)+"%"}</b></div></div></div>`}
function adaptationCard(){
const a=S.adaptationPreview;if(!a)return `<div class="card adaptation-card"><p class=eyebrow>ADAPTIVE PROGRAMMING</p><h3>Analyzing your week…</h3><p class=muted>Checking training, recovery, and recent effort.</p></div>`;
const pct=Math.round(Number(a.completion_rate||0)*100),changes=a.proposed_changes||[],exercise=a.exercise_decisions||[],remaining=Number(a.workouts_remaining||0);
return `<div class="card adaptation-card ${a.recommendation}"><div class=adaptation-head><div><p class=eyebrow>NEXT-WEEK ADAPTATION</p><h2>${esc(a.title)}</h2></div><span class=adaptation-badge>${esc(String(a.recommendation||"review").replaceAll("_"," "))}</span></div><p class=adaptation-summary>${esc(a.reason)}</p><div class=adaptation-review><b>Review before applying</b><span>Nothing changes until you approve it.</span></div>${changes.length?`<section class=adaptation-section><div class=adaptation-section-head><div><p class=eyebrow>PROGRAM CHANGES</p><h3>What Forge recommends</h3></div><small>${changes.length} change${changes.length===1?"":"s"}</small></div><div class=adaptation-decisions>${changes.map(c=>`<article class=adaptation-decision><div><b>${esc(c.area)}</b><p>${esc(c.reason)}</p></div><span>${esc(c.proposed)}</span></article>`).join("")}</div></section>`:""}${exercise.length?`<section class=adaptation-section><div class=adaptation-section-head><div><p class=eyebrow>EXERCISE CHANGES</p><h3>Exercise-specific changes</h3></div><small>${exercise.length} reviewed</small></div><div class=adaptation-decisions>${exercise.slice(0,8).map(x=>`<article class=adaptation-decision><div><b>${esc(x.exercise)}</b><p>${esc(x.reason)}</p></div><span>${esc(String(x.action||"hold").replaceAll("_"," "))}</span></article>`).join("")}</div></section>`:""}<div class=adaptation-metrics><div><small>Week completed</small><b>${pct}%</b></div><div><small>Fatigue</small><b>${Number(a.fatigue_score||0).toFixed(1)}/10</b></div><div><small>Volume direction</small><b>${esc(a.volume_signal||"Use recent performance")}</b></div></div><section class=adaptation-section><div class=adaptation-section-head><div><p class=eyebrow>SESSION PLAN</p><h3>${esc(a.session_change||"Keep normal session length")}</h3></div></div></section><div class=adaptation-next><p class=eyebrow>NEXT STEP</p><h3>${remaining} workout${remaining===1?"":"s"} remaining</h3><p>${remaining>0?"Finish or skip the remaining workouts before Forge builds next week.":"Your week is ready for final review."}</p>${remaining===0?`<button class="btn primary adaptation-apply" data-a=apply-adaptation>Apply Next Week</button>`:""}</div></div>`;
}
