// Forge Fitness v15.11.0 — extracted planScreen..before render
function planScreen(){
const workouts=[...(plan?.workouts||[])].sort((a,b)=>(a.scheduled_day??a.workout_index)-(b.scheduled_day??b.workout_index));
const totalExercises=workouts.reduce((n,w)=>n+(w.exercises?.length||0),0);
const totalMinutes=workouts.reduce((n,w)=>n+Number(w.estimated_minutes||profile.minutes_per_workout||0),0);
const totalSets=workouts.reduce((n,w)=>n+(w.exercises||[]).reduce((a,e)=>a+Number(e.sets||0),0),0);
const muscles={};
for(const w of workouts){
for(const e of (w.exercises||[])){
const m=e.primary_muscle||"Other";
muscles[m]=(muscles[m]||0)+Number(e.sets||0);
}
}
const topMuscles=Object.entries(muscles).sort((a,b)=>b[1]-a[1]).slice(0,4);
const goalLabels={build_muscle:"Build Muscle",lose_fat:"Lose Fat",get_stronger:"Get Stronger",improve_fitness:"Improve Fitness",general_fitness:"General Fitness"};
const expLabels={beginner:"Beginner",intermediate:"Intermediate",advanced:"Advanced"};
const tab=S.planTab||"overview";
return `<div class=row><div><p class=eyebrow>YOUR PLAN</p><h2>Your Plan</h2></div><span>▣</span></div><div class=spacer></div>
<div class=full-plan-tabs>
<button class="${tab==="overview"?"active":""}" data-plan-tab=overview>Overview</button>
<button class="${tab==="workouts"?"active":""}" data-plan-tab=workouts>Workouts</button>
</div>
${tab==="overview"?`
<div class=big-spacer></div>
<div class=plan-overview-hero>
<p class=eyebrow>CURRENT PROGRAM</p>
<h2>${workouts.length}-Day Training Plan</h2>
<p class=muted>${esc(goalLabels[profile.goal]||"Personalized Fitness")} • ${esc(expLabels[profile.experience]||"Custom Level")}</p>
</div>
<div class=spacer></div>
${recoveryCard()}<div class=spacer></div>${adaptationCard()}
<div class=spacer></div>
<div class=plan-overview-stats>
<div><b>${workouts.length}</b><small>Days / Week</small></div>
<div><b>${totalExercises}</b><small>Exercises</small></div>
<div><b>${totalSets}</b><small>Weekly Sets</small></div>
<div><b>${totalMinutes}</b><small>Est. Minutes</small></div>
</div>
<div class=big-spacer></div>
<div class=row><h3>Weekly Schedule</h3><span class=muted>${workouts.filter(x=>!x.is_skipped).length} active days</span></div>
<div class=spacer></div>
<div class=plan-week-calendar>
${["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"].map((day,di)=>{
const w=workouts.find(x=>x.scheduled_day_name===day);
const today=((new Date().getDay()+6)%7)===di;
return `<div class="calendar-day-card ${w?"scheduled":""} ${w?.is_skipped?"skipped":""} ${today?"today":""}">
<div class=calendar-day-top><small>${day.slice(0,3).toUpperCase()}</small>${today?"<em>TODAY</em>":""}</div>
<b>${w?esc(w.name):"Recovery"}</b>
<span>${w?`${esc(w.scheduled_time||S.timeSettings?.default_workout_time||"17:00")} • ${w.estimated_minutes||profile.minutes_per_workout} min`:"No workout"}</span>
${w&&(w.core_module||w.cardio_module)?`<i>${w.core_module?"Core Circuit ":""}${w.cardio_module?"Cardio":""}</i>`:""}
</div>`;
}).join("")}
</div>
<div class=big-spacer></div>
<h3>Training Focus</h3>
<div class=spacer></div>
${topMuscles.length?`<div class=focus-list>${topMuscles.map(([name,sets])=>{
const max=topMuscles[0][1]||1;
const pct=Math.max(8,Math.round(sets/max*100));
return `<div class=focus-row><div class=row><span>${esc(name)}</span><small>${sets} sets</small></div><div class=focus-track><i style="width:${pct}%"></i></div></div>`;
}).join("")}</div>`:`<div class=card><p class=muted>Training focus appears after plan generation.</p></div>`}
${plan?.mesocycle?`<div class=big-spacer></div><div class="card mesocycle-card"><p class=eyebrow>TRAINING BLOCK</p><div class=row><h3>Block ${plan.mesocycle.block_number} · Week ${plan.mesocycle.week_in_block}/${plan.mesocycle.block_length_weeks}</h3><b>${esc(String(plan.mesocycle.phase||"training").toUpperCase())}</b></div><p class=muted>${esc(plan.mesocycle.intensity_cue||"")}</p><small>${plan.mesocycle.deload_recommended?"Deload pressure is active this week.":"Forge is progressing this block without unnecessary exercise rotation."}</small></div>`:""}
<div class=big-spacer></div>
<div class=card>
<p class=eyebrow>HOW YOUR PLAN ADAPTS</p>
<h3>Built to progress with you</h3>
<p class=muted>Forge uses your training and recovery data to adjust future weeks.</p>
</div>
<div class=spacer></div>
<button class=btn data-a=adjust-plan>Adjust Plan</button><div class=spacer></div><button class=btn data-plan-tab=workouts>View Workouts</button><div class=spacer></div><button class="btn dark" data-a=edit-equipment-log>Manage Equipment Log</button><div class=spacer></div><button class="btn dark" data-a=open-exercise-directory>Browse Exercise Directory</button><div class=spacer></div><button class="btn dark" data-a=open-training-settings>Settings</button>
`:`
<div class=week-block><div class=week-title><h3>Week 1</h3><span>⌃</span></div><div class=stack>
${workouts.map(x=>`<button class="workout-row ${x.is_skipped?"skipped":""}" data-w=${plan.workouts.indexOf(x)}>
<span class=day-block>${esc((x.scheduled_day_name||"DAY").slice(0,3).toUpperCase())}</span>
<span class=inner><strong>${esc(x.name)}${x.is_skipped?"":": "}</strong><small>${x.is_skipped?"Skipped":`${x.exercises.length} exercises${x.exercise_quota_met===false?` • ${esc(x.exercise_quota_message||"Not enough unique exercises to meet your requested quota")}`:""} • ${x.estimated_minutes||profile.minutes_per_workout} min${x.core_included?" • Core":""}${x.cardio_included?" • Cardio":""}`}</small></span>
<span class=arrow>›</span>
</button>`).join("")}</div></div>
`}`;
}
function adjustplan(){
const days=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"];
if(!S.preferredDays.length){const current=(plan?.workouts||[]).map(x=>Number(x.scheduled_day)).filter(Number.isFinite);S.preferredDays=[...new Set(current)].slice(0,profile.days_per_week)}
return `<p class=eyebrow>PLAN CUSTOMIZATION</p><h2>Adjust Your Plan</h2><p class=muted>Update your availability and rebuild around it.</p><div class=big-spacer></div>
<div class=card><h3>Workouts per week</h3><div class=chips>${[2,3,4,5,6].map(n=>`<button class="chip ${profile.days_per_week===n?"selected":""}" data-adjust-days=${n}>${n} days</button>`).join("")}</div><div class=spacer></div><h3>Session length</h3><div class=chips>${[20,30,45,60,75,90].map(n=>`<button class="chip ${profile.minutes_per_workout===n?"selected":""}" data-adjust-mins=${n}>${n} min</button>`).join("")}</div></div><div class=spacer></div><h3>Exercises per workout</h3><p class=muted>Target exercises per workout.</p><div class=chips>${[3,4,5,6,7,8,9,10].map(n=>`<button class="chip ${Number(profile.exercises_per_day||6)===n?"selected":""}" data-adjust-exercises=${n}>${n}</button>`).join("")}</div>
<div class=spacer></div><div class=card><h3>Exercises by workout</h3><p class=muted>Override individual workout targets.</p><div class=stack>${Array.from({length:profile.days_per_week},(_,i)=>`<div class=row><b>Day ${i+1}${plan?.workouts?.[i]?.name?` · ${esc(plan.workouts[i].name)}`:""}</b><select data-day-exercises=${i}>${[3,4,5,6,7,8,9,10].map(n=>`<option value=${n} ${Number((profile.exercises_per_workout||[])[i]||profile.exercises_per_day||6)===n?"selected":""}>${n}</option>`).join("")}</select></div>`).join("")}</div></div>${S.planPreview?`<div class=spacer></div><div class="card accent-card"><p class=eyebrow>PLAN PREVIEW + VALIDATION</p><h3>Review before replacing the plan</h3><p class=muted>${(S.planPreview.changes||[]).reduce((n,x)=>n+x.added.length,0)} exercises added · ${(S.planPreview.changes||[]).reduce((n,x)=>n+x.removed.length,0)} removed. Generator invariants: ${esc(S.planPreview.diagnostics?.generator_invariants||"passed")}.</p>${S.planPreview.diagnostics?.warnings?.length?`<div class=adaptation-lock><b>Plan warnings</b><span>${S.planPreview.diagnostics.warnings.map(esc).join(" • ")}</span></div>`:""}<div class=stack>${(S.planPreview.changes||[]).map(x=>`<div><b>${esc(x.name||`Day ${x.workout_index+1}`)} · ${x.exercise_count_before??0} → ${x.exercise_count_after??0} exercises</b><small class=muted style="display:block">+ ${x.added.map(esc).join(", ")||"None"}</small><small class=muted style="display:block">− ${x.removed.map(esc).join(", ")||"None"}</small>${x.set_changes?.length?`<small class=muted style="display:block">Sets: ${x.set_changes.map(c=>`${esc(c.exercise)} ${c.before}→${c.after}`).join(" • ")}</small>`:""}</div>`).join("")}</div><div class=row><button class=btn data-a=apply-plan-preview>Apply New Plan</button><button class="btn dark" data-a=cancel-plan-preview>Keep Current Plan</button></div></div>`:""}<div class=spacer></div><div class=card><h3>Preferred training days</h3><p class=muted>Choose ${profile.days_per_week} days. Forge will use these exact days when possible.</p><div class=day-picker>${days.map((d,i)=>`<button type=button class="${S.preferredDays.includes(i)?"selected":""}" data-preferred-day=${i}>${d.slice(0,3)}</button>`).join("")}</div></div>
<div class=spacer></div><div class=card><p class=eyebrow>WHAT FORGE PRESERVES</p><p class=muted>Forge preserves priorities, balance, recovery, equipment, and useful volume.</p></div>
<div class=big-spacer></div><button class=btn data-a=save-plan-adjust ${S.planAdjusting?"disabled":""}>${S.planAdjusting?"Rebuilding…":"Rebuild Plan"}</button>`;
}
async function loadSystemHealth(){
if(!authToken||S.systemHealthLoading||S.systemHealth)return;
S.systemHealthLoading=true;
try{S.systemHealth=await api("/me/system/health");if(S.route==="trainingsettings")render()}catch(e){S.systemHealth={status:"degraded",checks:{api:false},message:e.message};if(S.route==="trainingsettings")render()}finally{S.systemHealthLoading=false}
}
function systemHealthCard(){return S.systemHealth?ForgeHealthUI.system(S.systemHealth,esc):ForgeMobile.loading("Checking Forge health")}
async function loadSessionDiagnostics(){if(S.sessionDiagnosticsLoading)return;S.sessionDiagnosticsLoading=true;try{S.sessionDiagnostics=await api("/me/system/session-diagnostics");if(S.route==="trainingsettings")render()}catch(e){console.warn("Session diagnostics failed",e)}finally{S.sessionDiagnosticsLoading=false}}
function sessionDiagnosticsCard(){return ForgeHealthUI.session(S.sessionDiagnostics,esc)}
function integrityCard(){return S.integrityReport?ForgeHealthUI.integrity(S.integrityReport,esc):ForgeMobile.loading("Checking data integrity")}
async function loadIntegrity(){if(S.integrityLoading)return;S.integrityLoading=true;try{S.integrityReport=await api("/me/system/integrity");if(S.route==="trainingsettings")render()}catch(e){console.warn("Integrity check failed",e)}finally{S.integrityLoading=false}}

function trainingsettings(){return `${integrityCard()}<div class=spacer></div>${sessionDiagnosticsCard()}<div class=spacer></div><p class=eyebrow>SETTINGS</p><h2>Settings</h2><p class=muted>Change future plan settings.</p><div class=big-spacer></div>${finalPolishSettingsCard()}<div class=spacer></div>${systemHealthCard()}<div class=spacer></div>${pwaInstallCard()}<div class=big-spacer></div><div class=preference-list><button class=pref-row data-a=adjust-plan><span><strong>Schedule & Workout Size</strong><small class=muted style="display:block">${profile.days_per_week} days • ${profile.minutes_per_workout} min • ${profile.exercises_per_day||6} exercises</small></span><span>›</span></button><button class=pref-row data-a=settings-split><span><strong>Split</strong><small class=muted style="display:block">${splitLabel(profile.workout_split)}</small></span><span>›</span></button><button class=pref-row data-a=settings-cardio-frequency><span><strong>Cardio</strong><small class=muted style="display:block">${cardioFrequencyLabel(profile.cardio_workouts_per_week)}</small></span><span>›</span></button><button class=pref-row data-a=settings-cardio-intensity><span><strong>Cardio effort</strong><small class=muted style="display:block">${cardioLabel(profile.cardio_preference)}</small></span><span>›</span></button><button class=pref-row data-a=settings-sport><span><strong>Sport</strong><small class=muted style="display:block">${sportLabel(profile.sport)}</small></span><span>›</span></button><button class=pref-row data-a=settings-core><span><strong>Core</strong><small class=muted style="display:block">${coreFrequencyLabel(profile.core_workouts_per_week)}</small></span><span>›</span></button><button class=pref-row data-a=settings-calendar><span><strong>Calendar</strong><small class=muted style="display:block">${S.calendarStatus?.connected?"Calendar connected":(S.calendarStatus?.configured?"Not connected":"Google OAuth not configured")}</small></span><span>›</span></button></div><div class=big-spacer></div><button class=btn data-a=settings-save>Save Settings</button>`}
function calendarsettings(){
const ts=S.timeSettings||{},cs=S.calendarStatus||{};
const connected=!!cs.connected,configured=!!cs.configured;
return `<p class=eyebrow>CALENDAR & TIME</p><h2>Calendar</h2>
<p class=muted>Uses your device timezone and syncs workouts with Google Calendar.</p>
<div class=big-spacer></div>
<div class=calendar-clock-card><small>LOCAL TIME</small><b id=liveClock>${formatLocalClock()}</b><span>${esc(ts.timezone||deviceTimePayload().timezone)}</span></div>
<div class=spacer></div>
<div class=card><p class=eyebrow>TIMEZONE</p><h3>${esc(ts.timezone||deviceTimePayload().timezone)}</h3>
<p class=muted>Detected automatically from this device. UTC offset: ${Number(ts.utc_offset_minutes??deviceTimePayload().utc_offset_minutes)>=0?"+":""}${Number(ts.utc_offset_minutes??deviceTimePayload().utc_offset_minutes)} minutes.</p>
<button class="btn dark compact" data-a=refresh-timezone>Refresh Timezone</button></div>
<div class=spacer></div>
<label class=field>Default workout time
<input id=defaultWorkoutTime type=time value="${esc(ts.default_workout_time||"17:00")}"></label>
<div class=spacer></div>
<label class=calendar-toggle><span><strong>Sync workouts with Google Calendar</strong><small>Workout changes can sync both ways.</small></span>
<input id=calendarSyncToggle type=checkbox ${ts.calendar_sync_enabled!==false?"checked":""}></label>
<div class=big-spacer></div>
<div class="card google-calendar-card simplified-calendar-card">
<div class=calendar-provider-row>
<div class=google-provider-mark>G</div>
<div><p class=eyebrow>GOOGLE CALENDAR</p><h3>${connected?"Calendar connected":configured?"Connect Google Calendar":"Google Calendar unavailable"}</h3></div>
</div>
<p class=muted>${connected
?`Your workouts can sync automatically and Forge Coach can use your calendar availability when planning training.`
:configured
?`Connect once with Google. Forge will handle workout syncing and availability automatically.`
:`Calendar connection is not available on this Forge server yet. No setup is required from your account.`}</p>
${connected
?`<div class=calendar-connected-status><span>✓</span><div><b>Connected</b><small>${cs.linked_workouts||0} workout event${Number(cs.linked_workouts||0)===1?"":"s"} synced</small></div></div>
<button class=btn data-a=calendar-sync-now>Sync Now</button>
<div class=spacer></div>
<button class="btn dark" data-a=calendar-disconnect>Disconnect</button>`
:configured
?`<button class="btn google-connect-btn" data-a=calendar-connect><span>G</span>Continue with Google</button>
<p class=calendar-privacy-note>Forge requests only the Calendar access it needs.</p>`
:`<div class=calendar-unavailable-note><b>No action needed</b><span>Google Calendar must be enabled on the server first.</span></div>`}
</div>
<div class=big-spacer></div>${calendarIntelligenceCard()}
<div class=big-spacer></div><button class=btn data-a=calendar-settings-save>Save Calendar Settings</button>`;
}
window.ForgeLegacyViews=Object.assign(window.ForgeLegacyViews||{},{nutrition:()=>nutrition(),nutritionadd:()=>nutritionadd()});
window.ForgeLegacyViews=Object.assign(window.ForgeLegacyViews||{},{workout:()=>workout(),exercise:()=>exercise(),timer:()=>timer(),complete:()=>complete(),swapexercise:()=>swapexercise(),cardioswap:()=>cardioswap(),modulemove:()=>modulemove(),coretracker:()=>coretracker(),cardiotracker:()=>cardiotracker()});
window.ForgeLegacyViews=Object.assign(window.ForgeLegacyViews||{},{planScreen:()=>planScreen(),adjustplan:()=>adjustplan(),trainingsettings:()=>trainingsettings(),calendarsettings:()=>calendarsettings()});
window.ForgeLegacyViews=Object.assign(window.ForgeLegacyViews||{},{progress:()=>progress(),history:()=>history(),prs:()=>prs(),exercisehistory:()=>exercisehistory()});
window.ForgeLegacyViews=Object.assign(window.ForgeLegacyViews||{},{coach:()=>coach(),notifications:()=>notificationCenter()});
