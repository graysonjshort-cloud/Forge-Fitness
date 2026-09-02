const API = localStorage.getItem("forge_api_url") || (
location.protocol==="https:" ? location.origin : `http://${location.hostname}:8000`
);
let authToken = localStorage.getItem("forge_auth_token") || "";
let account = null;
let plan = null, session = null;
const profile = {goal:"build_muscle",experience:"intermediate",days_per_week:4,minutes_per_workout:45,equipment:["full_gym"],preferred_exercises:[],excluded_exercises:[],priority_muscles:[],recovery_level:"normal",cardio_preference:"moderate",workout_split:"auto",sport:"general",core_workouts_per_week:2,cardio_workouts_per_week:2,custom_split:[],exercises_per_day:6,exercises_per_workout:[],seed:42};
const S={route:"welcome",onboardStep:0,wi:0,ei:0,set:0,restRemaining:0,restTotal:0,timer:null,feel:"Just Right",name:"Athlete",coachDraft:"",startupError:null,historyExercise:null,workoutPRs:[],exerciseRecall:null,exerciseRecallExerciseId:null,exerciseRecallLoading:false,swapOptions:[],swapOptionsKey:null,swapOptionsLoading:false,swapOptionsLoaded:false,substitutionIntelligenceExerciseId:null,substitutionIntelligenceLoading:false,cardioSwapKey:null,cardioSwapLoading:false,cardioSwapLoaded:false,coachMessages:[],coachAction:null,coachContext:null,coachLoaded:false,coachStatus:null,coachBriefing:null,coachStack:null,systemHealth:null,systemHealthLoading:false,sessionDiagnostics:null,sessionDiagnosticsLoading:false,integrityReport:null,integrityLoading:false,progressHub:null,progressHubLoading:false,strengthTrend:null,strengthTrendLoading:false,strengthExercise:"overall",strengthRange:"90",strengthPoint:null,planTab:"overview",equipmentCatalog:[],equipmentPresets:{},equipmentLog:[],equipmentLoaded:false,equipmentLoading:false,equipmentReturn:"onboarding",equipmentSearch:"",equipmentCategory:"All",equipmentSelectedOnly:false,equipmentEditKey:null,exerciseDirectory:null,exerciseDirectoryLoading:false,exerciseDirectorySearch:"",exerciseDirectoryMuscle:"All",exerciseDirectoryDifficulty:"All",exerciseDirectoryCompatible:true,exerciseDirectorySelected:null,lastSessionId:null,sessionStartedAt:null,completedWorkoutSummary:null,preferenceReturn:"preferences",timeSettings:null,calendarStatus:null,calendarIntelligence:null,clockTimer:null,calendarPollTimer:null,cardioSwapOptions:[],selectedCardioSwap:null,nutrition:null,nutritionLoading:false,nutritionDate:null,nutritionEditingTargets:false,nutritionSavedFoods:[],nutritionFavoritesOnly:false,nutritionEditEntry:null,nutritionCoachSummary:null,notifications:null,notificationSettings:null,progressIntelligence:null,progressIntelligenceLoading:false,bodyMetrics:null,bodyMetricsLoading:false,bodyMetricRange:"90",bodyMetricModal:false,prRecords:[],prLoading:false,prLoaded:false,historyRows:null,historyLoading:false,historyLoaded:false,exerciseHistoryData:null,exerciseHistoryExerciseId:null,exerciseHistoryLoading:false,prView:"exercise",prLiftFilter:"all",prCollapsedGroups:{},homeDashboard:null,adaptationPreview:null,mesocycle:null,adaptationBusy:false,planAdjusting:false,preferredDays:[],pwaInstallPrompt:null,pwaInstalled:false,pwaDismissed:false,moreOpen:false,online:navigator.onLine,updateReady:false,exerciseElapsed:0,exerciseTimer:null,exerciseTimerRunning:false,exerciseTimerTarget:0,moduleSession:null,moduleWorkoutIndex:null,moduleSummary:null,coreTimerElapsed:{},coreTimerRunning:null,coreTimerInterval:null,coreEffort:{},cardioEffort:7,coreCompleted:{},coreRestRemaining:0,coreRestTimer:null,moduleMoveType:null,moduleMoveSourceIndex:null,moduleMoveTarget:null,coreSequenceIndex:0,formDemo:null,formDemoExercise:null,formDemoReturn:"exercise",formDemoTab:"demo",demoOfflineStatus:null,demoAudit:null,demoReview:null,demoReviewExercise:null,demoReviewQueue:[],demoReviewQueueIndex:0,demoAngle:"primary",readinessCheckin:null,todayAdjustment:null,liveAdjustment:null,sessionIntelligence:null,sessionSync:null,sessionSyncLoading:false,planPreview:null,planDiagnostics:null,planLocks:{},readinessReturn:"home",swapReason:"preference",recoveryIntelligence:null,recoveryIntelligenceLoading:false,adaptationPreviewLoading:false,trainingDashboard:null,muscleDevelopment:null,muscleDevelopmentLoading:false,exerciseProgression:null,exerciseProgressionExerciseId:null,exerciseProgressionLoading:false,substitutionIntelligence:null,trainingRecords:null,coach4:null,coachLoading:false,coachBriefingLoading:false,exerciseDirectoryEquipment:"All",exerciseDirectoryMovement:"All",exerciseDirectoryFavorites:false,workoutBuilderExercise:null,planEditorSnapshot:null,planEditorLoading:false,intelligenceCore:null,intelligenceCoreLoading:false,explainableProgramming:null,explainableProgrammingLoading:false,strategyDashboard:null,strategyDashboardLoading:false};
const V=document.querySelector("#view"),toastEl=document.querySelector("#toast"),nav=document.querySelector("#bottomNav"),topbar=document.querySelector("#topbar");
const toast=t=>{toastEl.textContent=t;toastEl.classList.add("show");setTimeout(()=>toastEl.classList.remove("show"),1800)};
const esc=ForgeCore.esc;
const requestId=ForgeCore.requestId;
const PWA=ForgePWA.create({state:S,toast,render:()=>render()});
const {isStandalonePWA,isIOSDevice,pwaInstallCard,installForgePWA,setupPWA}=PWA;
function networkBanner(){return S.online?"":ForgeOffline.banner()}
function updateBanner(){
return S.updateReady?`<div class=update-banner><span><b>Update ready</b><small>Reload for latest version.</small></span><button data-a=reload-app>Reload</button></div>`:"";
}
function moreSheet(){
if(!S.moreOpen||!authToken)return "";
return `<div class=more-backdrop data-a=close-more>
<div class=more-sheet onclick="event.stopPropagation()">
<div class=more-sheet-handle></div>
<div class=more-account><div class=more-avatar>${esc((S.name||"F").slice(0,1).toUpperCase())}</div><div><small>FORGE ACCOUNT</small><h3>${esc(S.name)}</h3><span>${esc(account?.email||"Signed in")}</span></div></div>
<button data-a=open-training-settings><span>⚙</span><div><b>Settings</b><small>Plan, cardio, core, app install</small></div><em>›</em></button>
<button data-a=open-equipment-log><span>▣</span><div><b>Equipment Log</b><small>Manage gym equipment</small></div><em>›</em></button>
<button data-a=open-calendar-settings><span>▦</span><div><b>Calendar</b><small>${S.calendarStatus?.connected?"Calendar connected":"Schedule & timezone"}</small></div><em>›</em></button>
<button class=more-signout data-a=signout><span>↪</span><div><b>Sign Out</b><small>Your data stays saved</small></div></button>
<div class=more-version>Forge Fitness v15.10.1</div>
</div>
</div>`;
}
function finalPolishSettingsCard(){
return `<div class="card final-settings-card"><div class=row><div><p class=eyebrow>FORGE APP</p><h3>App</h3></div><span class=version-pill>v15.10.1</span></div>
<div class=settings-status-row><span>Connection</span><b>${S.online?"Online":"Offline"}</b></div>
<div class=settings-status-row><span>Install mode</span><b>${isStandalonePWA()?"Installed app":"Browser"}</b></div>
<div class=settings-status-row><span>Calendar</span><b>${S.calendarStatus?.connected?"Connected":"Not connected"}</b></div>
</div>`;
}
function equipmentIcon(key,name="",category=""){return ForgeEquipment.icon(key,name,category)}
const w=()=>plan?.workouts?.[S.wi]||null;
async function api(path,opt={}){return ForgeOffline.request(ForgeApi.request,API,()=>authToken,S,path,opt,{workout_id:w()?.workout_id,session_id:session?.session_id})}
async function replayOfflineWorkoutWrites(){
if(!authToken||!S.online||!ForgeOffline.count())return;
const r=await ForgeOffline.replay((p,o)=>api(p,o),{validate:async x=>!x.meta?.session_id||!!(await reconcileSession({silent:true}))&&Number(w()?.workout_id)===Number(x.meta.workout_id)&&Number(session?.session_id)===Number(x.meta.session_id)});
if(r.status==="synced"&&r.replayed){toast(`${r.replayed} offline change${r.replayed===1?"":"s"} synced`);try{plan=await api("/me/plan/current")}catch{}render()}else if(r.status==="blocked")toast("Recover the workout before syncing offline changes");
}
function normalizedExerciseTargets(){
const globalTarget=Math.max(3,Math.min(10,Number(profile.exercises_per_day)||6));
const per=Array.isArray(profile.exercises_per_workout)?profile.exercises_per_workout:[];
return Array.from({length:Number(profile.days_per_week)||0},(_,i)=>{
const raw=per[i];
const n=(raw===null||raw===undefined||raw==="")?globalTarget:Number(raw);
return Number.isFinite(n)?Math.max(3,Math.min(10,Math.round(n))):globalTarget;
});
}
async function loadExisting(){
if(!authToken)return;
try{
account=await api("/auth/me");
S.name=account.display_name||"Athlete";
try{const p=await api("/me/profile");Object.assign(profile,p)}catch{}
try{plan=await api("/me/plan/current")}catch{plan=null}
await syncDeviceTime();
try{
S.calendarStatus=await api("/me/calendar/status");
if(plan&&S.calendarStatus.connected&&S.calendarStatus.sync_enabled)await syncCalendar({silent:true});
startCalendarPolling();
}catch{}
S.route=plan?"home":"goal";
if(plan){await restoreSession();await reconcileSession({silent:true});}
if(plan)S.route="home";
if(new URLSearchParams(location.search).get("return_to")==="calendar"&&plan)S.route="calendarsettings";
}catch{
localStorage.removeItem("forge_auth_token");authToken="";account=null;plan=null;
}
}
async function restoreSession(){
if(!authToken)return;
try{
const s=await api("/me/session/resume");if(!s)return;
session={session_id:s.session_id};S.lastSessionId=s.session_id;
const resumedWorkoutIndex=(plan?.workouts||[]).findIndex(x=>Number(x.workout_id)===Number(s.workout_id));
if(resumedWorkoutIndex<0){
console.warn("Ignoring stale session from an old plan",s.workout_id);
session=null;S.lastSessionId=null;return;
}
S.wi=resumedWorkoutIndex;S.ei=Number(s.current_exercise_index||0);S.set=Number(s.current_set_index||0);
if(s.rest_started_at&&s.rest_duration_seconds){
const elapsed=Math.max(0,Math.floor((Date.now()-Date.parse(s.rest_started_at+"Z"))/1000));
const remain=Math.max(0,Number(s.rest_duration_seconds)-elapsed);
if(remain>0){S.restRemaining=remain;S.restTotal=Number(s.rest_duration_seconds);return;}
try{await api("/me/session/rest/clear",{method:"POST",body:JSON.stringify({session_id:s.session_id})})}catch{}
}
}catch(e){console.warn("Session restore failed",e)}
}
async function reconcileSession({silent=false}={}){
if(!authToken||S.sessionSyncLoading)return S.sessionSync;
S.sessionSyncLoading=true;
try{
const q=session?.session_id?`?session_id=${session.session_id}`:"";
const syncPath="/me/session/reconcile"+q;const sync=await api(syncPath);S.sessionSync=sync;
if(sync?.status==="none"||sync?.action==="session_closed"){session=null;return sync}
if(sync?.session_id){
session={session_id:sync.session_id};S.lastSessionId=sync.session_id;
const wi=(plan?.workouts||[]).findIndex(x=>Number(x.workout_id)===Number(sync.workout_id));
if(wi<0){session=null;return {...sync,status:"plan_mismatch"}}
S.wi=wi;
const list=plan.workouts[wi]?.exercises||[];
let ei=list.findIndex(x=>Number(x.exercise_id)===Number(sync.current_exercise_id));
if(ei<0)ei=Math.max(0,Math.min(Number(sync.current_exercise_index||0),list.length-1));
S.ei=ei;S.set=Math.max(0,Number(sync.current_set_index||0));
}
if(!silent&&sync?.stale_sessions_closed)toast("Recovered workout session");
return sync;
}catch(e){console.warn("Session reconciliation failed",e);if(!silent)toast("Could not verify workout");return null}
finally{S.sessionSyncLoading=false}
}
async function persistPosition(){
if(!session)return;
try{await api("/me/session/position",{method:"POST",queueable:true,body:JSON.stringify({session_id:session.session_id,exercise_index:S.ei,set_index:S.set})})}catch(e){console.warn(e)}
}
async function beginPersistentRest(seconds,context=null){
S.restRemaining=seconds;S.restTotal=seconds;S.restContext=context||S.restContext||null;
if(session){try{await api("/me/session/rest/start",{method:"POST",queueable:true,body:JSON.stringify({session_id:session.session_id,duration_seconds:seconds})})}catch(e){console.warn(e)}}
go("timer");
}
async function clearPersistentRest(){
if(session){try{await api("/me/session/rest/clear",{method:"POST",queueable:true,body:JSON.stringify({session_id:session.session_id})})}catch{}}
S.restRemaining=0;S.restContext=null;
}
function deviceTimePayload(){
const tz=Intl.DateTimeFormat().resolvedOptions().timeZone||"UTC";
return {timezone:tz,utc_offset_minutes:-new Date().getTimezoneOffset()};
}
function formatLocalClock(){
const now=new Date();
return now.toLocaleTimeString([], {hour:"numeric",minute:"2-digit",second:"2-digit"});
}
async function syncDeviceTime(){
if(!authToken)return;
try{
const payload=deviceTimePayload();
const data=await api("/me/time",{method:"PUT",body:JSON.stringify(payload)});
S.timeSettings=data.settings;
}catch(e){console.warn("Time sync failed",e)}
}
async function loadCalendarSettings(){
if(!authToken)return;
try{
await syncDeviceTime();
const [time,status]=await Promise.all([api("/me/time"),api("/me/calendar/status")]);
S.timeSettings=time.settings;S.calendarStatus=status;
if(S.route==="trainingsettings"&&!S.systemHealth)loadSystemHealth();if(S.route==="calendarsettings")render();
}catch(e){console.warn("Calendar settings load failed",e)}
}
async function loadCalendarIntelligence(){
if(!authToken)return;
try{S.calendarIntelligence=await api("/me/calendar/intelligence");if(S.route==="calendarsettings")render()}catch(e){console.warn("Calendar intelligence load failed",e)}
}
function calendarIntelligenceCard(){
const x=S.calendarIntelligence;if(!x)return `<div class="card"><p class=eyebrow>CALENDAR INTELLIGENCE</p><p class=muted>Analyzing schedule and recovery spacing...</p></div>`;
return `<div class="card calendar-intelligence-card"><div class=row><div><p class=eyebrow>CALENDAR INTELLIGENCE 2.0</p><h3>${x.conflicts?`${x.conflicts} schedule conflict${x.conflicts===1?"":"s"}`:"Week layout"}</h3></div><b>${x.connected?"LIVE":"PLAN"}</b></div><p class=muted>${esc(x.recommendation)}</p><div class=spacer></div>${(x.workouts||[]).map(w=>`<div class=adaptation-note><span><b>${esc(w.day_name)} • ${esc(w.name)}</b><small>${w.minutes} min • recovery ${esc(w.recovery_spacing)}${w.available===false?" • calendar conflict":w.available===true?" • available":""}</small></span><strong>${w.available===false?"Adjust":w.recovery_spacing==="tight"?"Watch":"Good"}</strong></div>`).join("")}</div>`;
}
async function syncCalendar({silent=false}={}){
if(!authToken)return;
try{
const status=S.calendarStatus||await api("/me/calendar/status");
if(!status.connected||!status.sync_enabled)return;
const data=await api("/me/calendar/sync",{method:"POST"});
if(data.plan)plan=data.plan;
if(!silent)toast(`Calendar synced${data.pulled?` • ${data.pulled} change${data.pulled===1?"":"s"} imported`:""}`);
S.calendarStatus=await api("/me/calendar/status");startCalendarPolling();
if(S.route==="calendarsettings")render();
}catch(e){
if(!silent)toast(e.message);
else console.warn("Calendar sync failed",e);
}
}
function startCalendarPolling(){
if(S.calendarPollTimer)clearInterval(S.calendarPollTimer);
if(!S.calendarStatus?.connected||!S.calendarStatus?.sync_enabled)return;
S.calendarPollTimer=setInterval(()=>syncCalendar({silent:true}),120000);
}
function stopCalendarPolling(){if(S.calendarPollTimer){clearInterval(S.calendarPollTimer);S.calendarPollTimer=null}}
function startLiveClock(){
if(S.clockTimer)clearInterval(S.clockTimer);
const tick=()=>{const el=document.querySelector("#liveClock");if(el)el.textContent=formatLocalClock()};
tick();S.clockTimer=setInterval(tick,1000);
}
function stopLiveClock(){if(S.clockTimer){clearInterval(S.clockTimer);S.clockTimer=null}}
async function loadEquipmentLog(){
if(!authToken||S.equipmentLoading||S.equipmentLoaded)return;
S.equipmentLoading=true;
try{
const [meta,log]=await Promise.all([api("/me/equipment/catalog"),api("/me/equipment")]);
S.equipmentCatalog=meta.catalog||[];
S.equipmentPresets=meta.presets||{};
S.equipmentLog=log.items||[];
profile.equipment=log.legacy_equipment||[];
S.equipmentLoaded=true;
if(["equipment","equipmentlog"].includes(S.route))render();
}catch(e){console.warn("Equipment log load failed",e)}finally{S.equipmentLoading=false}
}
function equipmentSelected(key){return S.equipmentLog.some(x=>x.key===key)}
function equipmentItemFromCatalog(key){
const c=S.equipmentCatalog.find(x=>x.key===key);
return c?{key:c.key,name:c.name,category:c.category,details:{},is_custom:false}:null;
}
function setEquipmentPreset(name){
const keys=S.equipmentPresets[name]||[];
S.equipmentLog=keys.map(equipmentItemFromCatalog).filter(Boolean);
render();
}
function toggleEquipmentKey(key){
const i=S.equipmentLog.findIndex(x=>x.key===key);
if(i>=0)S.equipmentLog.splice(i,1);
else{const x=equipmentItemFromCatalog(key);if(x)S.equipmentLog.push(x)}
render();
}
async function saveEquipmentLog(){
if(!S.equipmentLog.length)throw Error("Add at least one piece of equipment");
const saved=await api("/me/equipment",{method:"PUT",body:JSON.stringify({items:S.equipmentLog})});
S.equipmentLog=saved.items||[];
profile.equipment=saved.legacy_equipment||[];
if(saved.regenerated_plan)plan=saved.regenerated_plan;
return saved;
}
function addCustomEquipment(){
const name=prompt("Equipment name");
if(!name?.trim())return;
const key=`custom_${name.toLowerCase().replace(/[^a-z0-9]+/g,"_").replace(/^_|_$/g,"")}_${Date.now()}`;
S.equipmentLog.push({key,name:name.trim(),category:"Other",details:{},is_custom:true});
render();
}
function dots(n){return `<div class=progress-dots>${[0,1,2,3,4,5].map(i=>`<i class="${i<=n?"on":""}"></i>`).join("")}</div>`}
function render(){const map={welcome,register,login,goal,experience,schedule,equipment,preferences,preferencepicker,cardiopicker,cardiofrequencypicker,splitpicker,customsplit,sportpicker,corepicker,trainingsettings,adjustplan,calendarsettings,generating,yourplan,home,readiness:readinessCheckin,workout,exercise,exerciseinspect,timer,complete,progress,nutrition,nutritionadd,workoutbuilder,history,prs,exercisehistory,swapexercise,cardioswap,modulemove,coretracker,cardiotracker,coach,notifications:notificationCenter,equipmentlog,equipmentdetails,exercisedirectory,exercisedetail,formdemo,demoaudit,demoreview,plan:planScreen};V.innerHTML=networkBanner()+updateBanner()+(ForgeFeatures.has(S.route)?ForgeFeatures.view(S.route):map[S.route]())+floatingRestTimer()+moreSheet();V.setAttribute("aria-busy","false");const onboarding=["welcome","register","login","goal","experience","schedule","equipment","equipmentdetails","preferences","preferencepicker","cardiopicker","cardiofrequencypicker","splitpicker","sportpicker","corepicker","customsplit","generating","yourplan"].includes(S.route)&&!plan;nav.classList.toggle("hidden",onboarding);document.querySelector("#backBtn").style.visibility=["welcome","home","progress","nutrition","coach"].includes(S.route)?"hidden":"visible";document.querySelectorAll("[data-plan-tab]").forEach(b=>b.onclick=()=>{S.planTab=b.dataset.planTab;render()});document.querySelectorAll("[data-coach-route]").forEach(b=>b.onclick=()=>go(b.dataset.coachRoute));
document.querySelectorAll("[data-readiness-key]").forEach(b=>b.onclick=()=>{S.readinessCheckin=S.readinessCheckin||{};S.readinessCheckin[b.dataset.readinessKey]=Number(b.dataset.readinessValue);render()});
document.querySelectorAll("[data-readiness-minutes]").forEach(b=>b.onclick=()=>{S.readinessCheckin=S.readinessCheckin||{};S.readinessCheckin.minutes=Number(b.dataset.readinessMinutes);render()});
document.querySelectorAll("[data-swap-reason]").forEach(b=>b.onclick=()=>{if(S.swapReason===b.dataset.swapReason)return;S.swapReason=b.dataset.swapReason;S.swapOptionsKey=null;S.swapOptionsLoaded=false;S.swapOptions=[];S.selectedSwap=null;render();loadSwapOptions()});document.querySelectorAll("[data-swap]").forEach(b=>b.onclick=()=>{S.selectedSwap=Number(b.dataset.swap);document.querySelectorAll("[data-swap]").forEach(x=>x.classList.toggle("selected",x===b))});document.querySelectorAll("[data-cardio-swap]").forEach(b=>b.onclick=()=>{S.selectedCardioSwap=Number(b.dataset.cardioSwap);document.querySelectorAll("[data-cardio-swap]").forEach(x=>x.classList.toggle("selected",x===b))});
document.body.dataset.route=S.route;document.querySelectorAll("[data-nav]").forEach(b=>{const active=b.dataset.nav===S.route;b.classList.toggle("active",active);if(active)b.setAttribute("aria-current","page");else b.removeAttribute("aria-current");b.onclick=()=>go(b.dataset.nav)});document.querySelectorAll("[data-a]").forEach(b=>b.onclick=()=>act(b.dataset.a));document.querySelectorAll("[data-goal]").forEach(b=>b.onclick=()=>{profile.goal=b.dataset.goal;render()});document.querySelectorAll("[data-exp]").forEach(b=>b.onclick=()=>{profile.experience=b.dataset.exp;render()});document.querySelectorAll("[data-days]").forEach(b=>b.onclick=()=>{profile.days_per_week=+b.dataset.days;profile.core_workouts_per_week=Math.min(profile.core_workouts_per_week,profile.days_per_week);profile.cardio_workouts_per_week=Math.min(profile.cardio_workouts_per_week,profile.days_per_week);if(profile.workout_split==="custom")ensureCustomSplit();render()});document.querySelectorAll("[data-mins]").forEach(b=>b.onclick=()=>{profile.minutes_per_workout=+b.dataset.mins;render()});document.querySelectorAll("[data-exercise-count]").forEach(b=>b.onclick=()=>{profile.exercises_per_day=+b.dataset.exerciseCount;render()});document.querySelectorAll("[data-setchange]").forEach(b=>b.onclick=()=>adjustCurrentSets(Number(b.dataset.setchange)));document.querySelectorAll("[data-adjust-days]").forEach(b=>b.onclick=()=>{profile.days_per_week=+b.dataset.adjustDays;profile.core_workouts_per_week=Math.min(profile.core_workouts_per_week,profile.days_per_week);profile.cardio_workouts_per_week=Math.min(profile.cardio_workouts_per_week,profile.days_per_week);if(profile.workout_split==="custom")ensureCustomSplit();S.preferredDays=S.preferredDays.slice(0,profile.days_per_week);render()});document.querySelectorAll("[data-adjust-mins]").forEach(b=>b.onclick=()=>{profile.minutes_per_workout=+b.dataset.adjustMins;render()});document.querySelectorAll("[data-adjust-exercises]").forEach(b=>b.onclick=()=>{profile.exercises_per_day=+b.dataset.adjustExercises;render()});document.querySelectorAll("[data-day-exercises]").forEach(el=>el.onchange=()=>{profile.exercises_per_workout=profile.exercises_per_workout||[];profile.exercises_per_workout[+el.dataset.dayExercises]=+el.value;S.planPreview=null;render()});document.querySelectorAll("[data-preferred-day]").forEach(b=>b.onclick=()=>{const d=+b.dataset.preferredDay,i=S.preferredDays.indexOf(d);if(i>=0)S.preferredDays.splice(i,1);else if(S.preferredDays.length<profile.days_per_week)S.preferredDays.push(d);else{toast(`Choose ${profile.days_per_week} days`);return}render()});document.querySelectorAll("[data-cardio]").forEach(b=>b.onclick=()=>{profile.cardio_preference=b.dataset.cardio;render()});document.querySelectorAll("[data-split]").forEach(b=>b.onclick=()=>{profile.workout_split=b.dataset.split;if(profile.workout_split==="custom"){ensureCustomSplit();go("customsplit")}else render()});document.querySelectorAll("[data-custom-muscle]").forEach(b=>b.onclick=()=>{const [raw,m]=b.dataset.customMuscle.split(":");const i=Number(raw);ensureCustomSplit();const day=profile.custom_split[i],arr=day.muscles,at=arr.indexOf(m);if(at>=0){if(arr.length===1){toast("Each custom day needs at least one muscle group");return}arr.splice(at,1);if(day.submuscles)delete day.submuscles[m]}else arr.push(m);day.name=customDayName(arr,i);render()});document.querySelectorAll("[data-custom-submuscle]").forEach(b=>b.onclick=()=>{const [raw,m,sub]=b.dataset.customSubmuscle.split(":");const i=Number(raw);ensureCustomSplit();const day=profile.custom_split[i];day.submuscles=day.submuscles||{};const arr=day.submuscles[m]||[];const at=arr.indexOf(sub);if(at>=0)arr.splice(at,1);else arr.push(sub);if(arr.length)day.submuscles[m]=arr;else delete day.submuscles[m];render()});document.querySelectorAll("[data-custom-frequency]").forEach(b=>b.onclick=()=>{const [m,raw]=b.dataset.customFrequency.split(":");adjustCustomMuscleFrequency(m,Number(raw));render()});document.querySelectorAll("[data-custom-priority]").forEach(b=>b.onclick=()=>{const m=b.dataset.customPriority;profile.priority_muscles=profile.priority_muscles||[];const i=profile.priority_muscles.indexOf(m);if(i>=0)profile.priority_muscles.splice(i,1);else profile.priority_muscles.push(m);render()});
document.querySelectorAll("[data-sport]").forEach(b=>b.onclick=()=>{profile.sport=b.dataset.sport;render()});document.querySelectorAll("[data-core-frequency]").forEach(b=>b.onclick=()=>{profile.core_workouts_per_week=Math.min(+b.dataset.coreFrequency,+profile.days_per_week);render()});document.querySelectorAll("[data-cardio-frequency]").forEach(b=>b.onclick=()=>{profile.cardio_workouts_per_week=Math.min(+b.dataset.cardioFrequency,+profile.days_per_week);if(!["light","moderate","high","extended"].includes(profile.cardio_preference))profile.cardio_preference="moderate";render()});const nutritionDate=document.querySelector("#nutritionDate");
if(nutritionDate)nutritionDate.onchange=()=>{S.nutritionDate=nutritionDate.value;S.nutrition=null;loadNutrition();};
document.querySelectorAll("[data-nutrition-delete]").forEach(b=>b.onclick=async()=>{if(confirm("Delete this food entry?")){await api(`/me/nutrition/entries/${b.dataset.nutritionDelete}`,{method:"DELETE"});S.nutrition=null;await loadNutrition();}});
document.querySelectorAll("[data-nutrition-edit]").forEach(b=>b.onclick=async()=>{const x=(S.nutrition?.entries||[]).find(v=>String(v.id)===String(b.dataset.nutritionEdit));if(!x)return;const food=prompt("Food name",x.food_name);if(food===null)return;const calories=prompt("Calories",x.calories);if(calories===null)return;const protein=prompt("Protein (g)",x.protein_g);if(protein===null)return;const carbs=prompt("Carbs (g)",x.carbs_g);if(carbs===null)return;const fat=prompt("Fat (g)",x.fat_g);if(fat===null)return;await api(`/me/nutrition/entries/${x.id}`,{method:"PUT",body:JSON.stringify({entry_date:x.entry_date,meal_type:x.meal_type,food_name:food.trim()||x.food_name,calories:Math.max(0,+calories||0),protein_g:Math.max(0,+protein||0),carbs_g:Math.max(0,+carbs||0),fat_g:Math.max(0,+fat||0),source:x.source||null,source_url:x.source_url||null})});S.nutrition=null;await loadNutrition();toast("Food updated");});
document.querySelectorAll("[data-nutrition-quicklog]").forEach(b=>b.onclick=async()=>{await api(`/me/nutrition/saved-foods/${b.dataset.nutritionQuicklog}/quick-log`,{method:"POST",body:JSON.stringify({entry_date:nutritionDateValue(),meal_type:"Meal"})});S.nutrition=null;await loadNutrition();toast("Saved food logged");});
document.querySelectorAll("[data-notification-dismiss]").forEach(b=>b.onclick=async()=>{await api("/me/notifications/dismiss",{method:"POST",body:JSON.stringify({notification_key:b.dataset.notificationDismiss})});await loadNotifications()});
document.querySelectorAll("[data-pr-view]").forEach(b=>b.onclick=()=>{S.prView=b.dataset.prView;render();});
document.querySelectorAll("[data-pr-lift-filter]").forEach(b=>b.onclick=()=>{S.prLiftFilter=b.dataset.prLiftFilter;render();});document.querySelectorAll("[data-exhist]").forEach(b=>b.onclick=()=>{S.historyExercise=Number(b.dataset.exhist);go("exercisehistory")});document.querySelectorAll("[data-pr-group]").forEach(b=>b.onclick=()=>{const k=b.dataset.prGroup;S.prCollapsedGroups[k]=!S.prCollapsedGroups[k];render()});
document.querySelectorAll("[data-body-range]").forEach(b=>b.onclick=()=>{S.bodyMetricRange=b.dataset.bodyRange;loadBodyMetrics()});
document.querySelectorAll("[data-body-delete]").forEach(b=>b.onclick=async()=>{if(confirm("Delete this body check-in?")){await api(`/me/body-metrics/${b.dataset.bodyDelete}`,{method:"DELETE"});await loadBodyMetrics();loadProgressIntelligence();toast("Check-in deleted")}});
document.querySelectorAll("[data-progress-coach]").forEach(b=>b.onclick=()=>{S.coachDraft=b.dataset.progressCoach;go("coach")});
document.querySelectorAll("[data-notification-coach]").forEach(b=>b.onclick=()=>{S.coachDraft=b.dataset.notificationCoach;go("coach")});
document.querySelectorAll("[data-notification-setting]").forEach(b=>b.onchange=async()=>{
const key=b.dataset.notificationSetting;
if(key==="browser_notifications"&&b.checked){const p=await ForgeNotifications.permission();if(p!=="granted"){b.checked=false;toast(p==="unsupported"?"Device notifications are not supported here":"Notification permission was not granted");return}}
const body={};body[key]=b.checked;await api("/me/notifications/settings",{method:"PUT",body:JSON.stringify(body)});await loadNotifications()
});
const notificationLead=document.querySelector("#notificationLead");if(notificationLead)notificationLead.onchange=async()=>{await api("/me/notifications/settings",{method:"PUT",body:JSON.stringify({reminder_minutes_before:+notificationLead.value})});await loadNotifications()};
document.querySelectorAll("[data-nutrition-favorite]").forEach(b=>b.onclick=async()=>{await api(`/me/nutrition/saved-foods/${b.dataset.nutritionFavorite}/favorite`,{method:"PUT",body:JSON.stringify({favorite:b.dataset.favorite==="1"})});
document.querySelectorAll("[data-nutrition-coach]").forEach(b=>b.onclick=()=>{const q=b.dataset.nutritionCoach;go("coach");setTimeout(()=>sendCoach(q),50);});S.nutrition=null;await loadNutrition();});
const directorySearch=document.querySelector("#exerciseDirectorySearch");
if(directorySearch)directorySearch.onchange=()=>{S.exerciseDirectorySearch=directorySearch.value;S.exerciseDirectory=null;loadExerciseDirectory();};
const dirMuscle=document.querySelector("#directoryMuscle");
if(dirMuscle)dirMuscle.onchange=()=>{S.exerciseDirectoryMuscle=dirMuscle.value;S.exerciseDirectory=null;loadExerciseDirectory();};
const dirDifficulty=document.querySelector("#directoryDifficulty");
if(dirDifficulty)dirDifficulty.onchange=()=>{S.exerciseDirectoryDifficulty=dirDifficulty.value;S.exerciseDirectory=null;loadExerciseDirectory();};
const dirEquipment=document.querySelector("#directoryEquipment");if(dirEquipment)dirEquipment.onchange=()=>{S.exerciseDirectoryEquipment=dirEquipment.value;S.exerciseDirectory=null;loadExerciseDirectory();};
const dirMovement=document.querySelector("#directoryMovement");if(dirMovement)dirMovement.onchange=()=>{S.exerciseDirectoryMovement=dirMovement.value;S.exerciseDirectory=null;loadExerciseDirectory();};
document.querySelectorAll("[data-builder-exclude]").forEach(b=>b.onclick=async()=>{const parts=b.dataset.builderExclude.split(":");const name=decodeURIComponent(parts.slice(1).join(":"));if(!profile.excluded_exercises.includes(name))profile.excluded_exercises.push(name);const d=await api("/me/profile",{method:"POST",body:JSON.stringify(profile)});if(d?.plan)plan=d.plan;toast(`${name} excluded and plan regenerated`);});
document.querySelectorAll("[data-builder-lock]").forEach(b=>b.onclick=async()=>{const [wi,eid]=b.dataset.builderLock.split(":").map(Number);const locked=(S.planLocks?.[wi]||[]).includes(eid);await api(`/me/plan/locks/${wi}/${eid}?locked=${locked?"false":"true"}`,{method:"POST"});S.planLocks=await api("/me/plan/locks");render();});
document.querySelectorAll("[data-builder-remove]").forEach(b=>b.onclick=async()=>{await api(`/me/workouts/${w().workout_id}/exercises/${b.dataset.builderRemove}`,{method:"DELETE"});plan=await api("/me/plan/current");render();});
document.querySelectorAll("[data-builder-transfer]").forEach(b=>b.onclick=async()=>{const eid=Number(b.dataset.builderTransfer),sel=document.querySelector(`[data-builder-target="${eid}"]`),target=Number(sel?.value);if(!target)return;try{const preview=await api(`/me/workouts/${w().workout_id}/exercises/${eid}/move-preview`,{method:"POST",body:JSON.stringify({target_workout_id:target})});if(!confirm(`${preview.exercise.name}: ${preview.source.name} → ${preview.target.name}. ${preview.warning} Continue?`))return;await api(`/me/workouts/${w().workout_id}/exercises/${eid}/move`,{method:"POST",body:JSON.stringify({target_workout_id:target})});plan=await api("/me/plan/current");S.planEditorSnapshot=null;await loadPlanEditorSnapshot();toast("Exercise moved");render()}catch(e){toast(e.message)}});
document.querySelectorAll("[data-builder-move]").forEach(b=>b.onclick=async()=>{const [i,d]=b.dataset.builderMove.split(":").map(Number);const j=i+d;if(j<0||j>=w().exercises.length)return;const ids=w().exercises.map(x=>x.exercise_id);[ids[i],ids[j]]=[ids[j],ids[i]];await api(`/me/workouts/${w().workout_id}/exercises/reorder`,{method:"PUT",body:JSON.stringify({exercise_ids:ids})});plan=await api("/me/plan/current");render();});
document.querySelectorAll("[data-builder-sets]").forEach(el=>el.onchange=async()=>{const id=el.dataset.builderSets;const body={sets:+el.value,min_reps:+document.querySelector(`[data-builder-min="${id}"]`).value,max_reps:+document.querySelector(`[data-builder-max="${id}"]`).value,rest_seconds:+document.querySelector(`[data-builder-rest="${id}"]`).value};await api(`/me/workouts/${w().workout_id}/exercises/${id}`,{method:"PUT",body:JSON.stringify(body)});plan=await api("/me/plan/current");toast("Workout updated");});
document.querySelectorAll("[data-demo-review-open]").forEach(b=>b.onclick=()=>openDemoReview(b.dataset.demoReviewOpen));
document.querySelectorAll("[data-form-demo]").forEach(b=>b.onclick=()=>openFormDemo(b.dataset.formDemo,b.dataset.formReturn||S.route));
document.querySelectorAll("[data-form-demo-tab]").forEach(b=>b.onclick=()=>{S.formDemoTab=b.dataset.formDemoTab;render()});
document.querySelectorAll("[data-demo-angle]").forEach(b=>b.onclick=()=>{S.demoAngle=b.dataset.demoAngle;render()});
document.querySelectorAll("[data-directory-exercise]").forEach(b=>b.onclick=async()=>{
try{S.exerciseDirectorySelected=await api(`/me/exercises/${b.dataset.directoryExercise}/directory`);go("exercisedetail")}catch(e){toast(e.message)}
});
document.querySelectorAll("[data-exercise-pref]").forEach(b=>b.onclick=async()=>{
if(!S.exerciseDirectorySelected)return;
try{
const d=await api(`/me/exercises/${S.exerciseDirectorySelected.id}/preference`,{method:"PUT",body:JSON.stringify({preference:b.dataset.exercisePref})});
S.exerciseDirectorySelected=d.exercise;
S.exerciseDirectory=null;
toast(b.dataset.exercisePref==="neutral"?"Exercise preference cleared":"Exercise preference saved");
render();
}catch(e){toast(e.message)}
});
const equipmentSearch=document.querySelector("#equipmentSearch");
if(equipmentSearch)equipmentSearch.oninput=()=>{S.equipmentSearch=equipmentSearch.value;render();};
document.querySelectorAll("[data-equipment-category]").forEach(b=>b.onclick=()=>{S.equipmentCategory=b.dataset.equipmentCategory;render();});
document.querySelectorAll("[data-equipment-edit]").forEach(b=>b.onclick=()=>{S.equipmentReturn=S.route==="equipment"?"onboarding":(S.equipmentReturn||"plan");S.equipmentEditKey=b.dataset.equipmentEdit;go("equipmentdetails");});
document.querySelectorAll("[data-equipment-key]").forEach(b=>b.onclick=()=>toggleEquipmentKey(b.dataset.equipmentKey));
document.querySelectorAll("[data-equipment-preset]").forEach(b=>b.onclick=()=>setEquipmentPreset(b.dataset.equipmentPreset));
document.querySelectorAll("[data-remove-custom]").forEach(b=>b.onclick=()=>{S.equipmentLog=S.equipmentLog.filter(x=>x.key!==b.dataset.removeCustom);render();});document.querySelectorAll("[data-pref]").forEach(b=>b.onclick=()=>toggleArr(profile.preferred_exercises,b.dataset.pref));document.querySelectorAll("[data-avoid]").forEach(b=>b.onclick=()=>toggleArr(profile.excluded_exercises,b.dataset.avoid));document.querySelectorAll("[data-w]").forEach(b=>b.onclick=()=>{S.wi=+b.dataset.w;go("workout")});document.querySelectorAll("[data-ex]").forEach(b=>b.onclick=async()=>{
const targetIndex=Number(b.dataset.ex);
if(session&&targetIndex!==S.ei){S.inspectEi=targetIndex;go("exerciseinspect");return}
stopExerciseTimer();S.exerciseElapsed=0;S.exerciseTimerTarget=0;
if(!session){S.ei=targetIndex;S.set=0}
go("exercise")
});document.querySelectorAll("[data-feel]").forEach(b=>b.onclick=()=>{S.feel=b.dataset.feel;render()});
document.querySelectorAll("[data-timer-target]").forEach(b=>b.onclick=()=>{S.exerciseTimerTarget=Math.max(5,Math.min(600,Number(S.exerciseTimerTarget||30)+Number(b.dataset.timerTarget)));render();});
document.querySelectorAll("[data-core-timer-start]").forEach(b=>b.onclick=()=>startCoreTimer(b.dataset.coreTimerStart));
document.querySelectorAll("[data-core-timer-reset]").forEach(b=>b.onclick=()=>resetCoreTimer(b.dataset.coreTimerReset));
document.querySelectorAll("[data-core-effort]").forEach(b=>b.onclick=()=>{S.coreEffort[b.dataset.coreEffortKey]=Number(b.dataset.coreEffort);render();});
document.querySelectorAll("[data-cardio-effort]").forEach(b=>b.onclick=()=>{S.cardioEffort=Number(b.dataset.cardioEffort);render();});
document.querySelectorAll("[data-module-day]").forEach(b=>b.onclick=()=>{S.moduleMoveTarget=Number(b.dataset.moduleDay);render();});
document.querySelectorAll("[data-core-complete-set]").forEach(b=>b.onclick=async()=>{
const ww=plan.workouts[S.moduleWorkoutIndex],m=ww.core_module,seq=coreSequence(m);
const active=seq[S.coreSequenceIndex];
if(!active||b.dataset.coreCompleteSet!==active.key){toast("Complete the current core set first");return}
const i=active.exerciseIndex,setIndex=active.setIndex,key=active.key,e=active.exercise;
const value=Number(document.querySelector(`[data-core-value="${key}"]`)?.value||0);
const rpe=Number(document.querySelector(`[data-core-rpe="${key}"]`)?.value||7);
if(value<=0){toast(isTimedExercise(e)?`Run the timer for ${e.name}`:`Enter reps for ${e.name}`);return}
try{
await api(`/me/modules/${S.moduleSession.id}/core/log`,{method:"POST",body:JSON.stringify({
exercise_id:e.exercise_id,sets_completed:1,reps:isTimedExercise(e)?[]:[value],
duration_seconds:isTimedExercise(e)?value:null,weight:null,
load_mode:isTimedExercise(e)?"timed":(isBodyweightExercise(e)?"bodyweight":"weight"),rpe
})});
S.coreCompleted[key]=true;
if(S.coreTimerRunning===key)stopCoreTimer();
const oldRound=active.round;
S.coreSequenceIndex=nextIncompleteCoreIndex(m,S.coreSequenceIndex+1);
const next=seq[S.coreSequenceIndex];
if(next){
const rest=next.round>oldRound?Number(m.round_rest_seconds||60):Number(e.rest_seconds||m.between_exercise_rest_seconds||35);
startCoreRest(rest);
}else render();
}catch(err){toast(err.message)}
});
const loadMode=document.querySelector("#loadMode");
if(loadMode)loadMode.onchange=()=>{const row=document.querySelector("#addedWeightRow");if(row)row.style.display=loadMode.value==="weight"?"":"none";};
const strengthSelect=document.querySelector("#strengthExercise");
if(strengthSelect)strengthSelect.onchange=()=>{S.strengthExercise=strengthSelect.value;S.strengthPoint=null;S.strengthTrend=null;render();};
document.querySelectorAll("[data-strength-range]").forEach(b=>b.onclick=()=>{S.strengthRange=b.dataset.strengthRange;S.strengthPoint=null;S.strengthTrend=null;render();});
document.querySelectorAll("[data-strength-point]").forEach(b=>b.onclick=()=>{S.strengthPoint=Number(b.dataset.strengthPoint);render();});
document.querySelectorAll("[data-coachprompt]").forEach(b=>b.onclick=()=>sendCoach(b.dataset.coachprompt));
document.querySelectorAll("[data-rpe]").forEach(b=>b.onclick=()=>{
const input=document.querySelector("#rpe");
if(input) input.value=b.dataset.rpe;
document.querySelectorAll("[data-rpe]").forEach(x=>x.classList.toggle("selected",x===b));
});
document.querySelectorAll("[data-addrest]").forEach(b=>b.onclick=()=>{S.restRemaining+=Number(b.dataset.addrest);S.restTotal=Math.max(S.restTotal,S.restRemaining);render()});
document.querySelectorAll("[data-prefpick]").forEach(b=>b.onclick=()=>{const arr=S.prefMode==="avoid"?profile.excluded_exercises:profile.priority_muscles,v=b.dataset.prefpick,i=arr.indexOf(v);if(i>=0)arr.splice(i,1);else arr.push(v);render()});
const rf=document.querySelector("#registerForm");if(rf)rf.onsubmit=submitRegister;const lf=document.querySelector("#loginForm");if(lf)lf.onsubmit=submitLogin;if(S.route==="progress"&&!S.strengthTrend)loadStrengthTrend();if(S.route==="progress"&&!S.progressHub)loadProgressHub();if(S.route==="progress"&&!S.trainingRecords)loadTrainingRecords();if(["home","progress"].includes(S.route)&&!S.trainingDashboard)loadTrainingDashboard();if(S.route==="plan"&&!S.adaptationPreview)loadAdaptationPreview();if(S.route==="plan"&&!S.recoveryIntelligence)loadRecoveryIntelligence();if(["equipment","equipmentlog"].includes(S.route)&&!S.equipmentLoaded)loadEquipmentLog();if(["exercisedirectory","preferences","preferencepicker"].includes(S.route)&&!S.exerciseDirectory)loadExerciseDirectory();if(S.route==="coach"&&!S.coachLoaded)loadCoach();if(S.route==="coach"&&!S.coachBriefing)loadCoachBriefing();if(S.route==="coach"&&!S.coach4)loadCoach4();if(S.route==="exercise"){loadExerciseRecall();loadExerciseProgression();}if(S.route==="swapexercise"){loadSwapOptions();loadSubstitutionIntelligence();}if(S.route==="cardioswap")loadCardioSwapOptions();if(S.route==="timer")startTimer();if(S.route==="history")loadHistory();if(S.route==="prs")loadPRs();if(S.route==="nutrition"&&!S.nutrition)loadNutrition();
if(["home","progress","coach"].includes(S.route)&&!S.strategyDashboard)loadStrategyDashboard();document.querySelectorAll("[data-authority]").forEach(x=>x.onchange=()=>saveAuthority(x.dataset.authority,x.value));
if(S.route==="exercisehistory")loadExerciseHistory();
if(S.route==="trainingsettings"){if(!S.sessionDiagnostics)loadSessionDiagnostics();if(!S.integrityReport)loadIntegrity();}
if(S.route==="calendarsettings"){if(!S.calendarStatus||!S.timeSettings)loadCalendarSettings();startLiveClock()}else stopLiveClock()}
function toggleArr(arr,v){const i=arr.indexOf(v);if(i>=0)arr.splice(i,1);else arr.push(v);render()}
function go(r){
if(!S.restRemaining)stopTimer();S.route=r;render();scrollTo(0,0);
if(r==="workoutbuilder")loadPlanEditorSnapshot();
if(r==="progress"){loadIntelligenceCore();loadExplainableProgramming();loadTrainingDashboard();loadMuscleDevelopment();loadTrainingRecords();loadProgressIntelligence();loadBodyMetrics();api("/me/modules/summary").then(x=>{S.moduleSummary=x;render()}).catch(()=>{});}
if(r==="home"){loadHomeDashboard();loadNotifications();}
if(r==="notifications")loadNotifications(true);
if((r==="home"||r==="plan")&&S.calendarStatus?.connected&&S.calendarStatus?.sync_enabled){
syncCalendar({silent:true});
}
}
async function generatePlan(){go("generating");try{if(!authToken)throw Error("Sign in first");await api("/me/profile",{method:"POST",body:JSON.stringify(profile)});plan=await api("/me/plan/generate",{method:"POST"});
if(S.calendarStatus?.connected&&S.calendarStatus?.sync_enabled)await syncCalendar({silent:true});
setTimeout(()=>go("yourplan"),800)}catch(e){toast(e.message);go("preferences")}}
async function startWorkout(){ForgeCache.invalidate("home");const ww=w();const s=await api(`/me/workout/${ww.workout_id}/start`,{method:"POST"});session={session_id:s.session_id};S.lastSessionId=s.session_id;S.sessionStartedAt=Date.now();S.completedWorkoutSummary=null;S.ei=0;S.set=0;S.workoutPRs=[];await persistPosition();await reconcileSession({silent:true});go("workout")}
function setOverrideKey(e){return `forge-set-override:${session?.session_id||"plan"}:${w()?.workout_id||0}:${e?.exercise_id||0}`}
function autoSetTargetKey(e){return `forge-auto-set-target:${session?.session_id||"plan"}:${w()?.workout_id||0}:${e?.exercise_id||0}`}
function storedSetCount(key){try{const v=Number(sessionStorage.getItem(key));return Number.isFinite(v)&&v>0?v:null}catch{return null}}
function effectiveSetCount(e){return storedSetCount(setOverrideKey(e))||storedSetCount(autoSetTargetKey(e))||Math.max(1,Number(e?.sets||1))}
function saveAutoSetTarget(e,count){try{sessionStorage.setItem(autoSetTargetKey(e),String(Math.max(1,Math.min(12,Number(count||e.sets||1)))))}catch{}}
function clearAutoSetTarget(e){try{sessionStorage.removeItem(autoSetTargetKey(e))}catch{}}
function latestRestFor(e){const same=Number(S.sessionIntelligence?.exercise_id||0)===Number(e?.exercise_id||0);return same&&Number(S.sessionIntelligence?.recommended_rest_seconds)>0?Number(S.sessionIntelligence.recommended_rest_seconds):null}

async function adjustCurrentSets(delta){
const e=w()?.exercises?.[S.ei];if(!e)return;
if(!S.online){toast("Reconnect to change sets");return}
const minSets=Math.max(1,session?S.set+1:1),current=effectiveSetCount(e),next=Math.max(minSets,Math.min(12,current+Number(delta||0)));
if(next===current)return;
await api(`/me/workouts/${w().workout_id}/exercise-sets`,{method:"PUT",body:JSON.stringify({exercise_id:e.exercise_id,sets:next})});
e.sets=next;clearAutoSetTarget(e);try{sessionStorage.setItem(setOverrideKey(e),String(next))}catch{}
ForgeCache.invalidate("home");toast(`${next} sets planned`);render();
}
function hasManualSetOverride(e){try{return sessionStorage.getItem(setOverrideKey(e))!==null}catch{return false}}
async function saveSet(){ForgeCache.invalidate("home");
if(!session)await startWorkout();
const sync=await reconcileSession({silent:true});
if(!session||sync?.status==="plan_mismatch"||sync?.status==="none")throw Error("Workout resynced. Reopen and retry.");
const e=w().exercises[S.ei],timed=isTimedExercise(e),rpe=+document.querySelector("#rpe").value;
if(!Number.isFinite(rpe)||rpe<1||rpe>10)throw Error("RPE must be 1–10");
let payload={request_id:requestId(),session_id:session.session_id,exercise_id:e.exercise_id,completed_sets:1,difficulty:rpe,skipped:false};
if(timed){
stopExerciseTimer();
const duration=Math.max(0,Number(S.exerciseElapsed||0));
if(duration<1)throw Error("Run the timer before completing this set");
payload.reps=[];
payload.weight=null;
payload.duration_seconds=Math.round(duration);
payload.load_mode="timed";
}else{
const reps=+document.querySelector("#reps").value;
if(!Number.isFinite(reps)||reps<=0)throw Error("Enter valid reps");
const bodyweight=isBodyweightExercise(e);
const mode=bodyweight?(document.querySelector("#loadMode")?.value||"bodyweight"):"weight";
let weight=null;
if(mode==="weight"){
weight=+document.querySelector("#weight").value;
if(!Number.isFinite(weight)||weight<0)throw Error("Enter a valid weight");
}
payload.reps=[reps];
payload.weight=weight;
payload.duration_seconds=null;
payload.load_mode=mode;
}
const result=await api("/me/performance",{method:"POST",queueable:true,body:JSON.stringify(payload)});
S.exerciseRecall=null;S.exerciseRecallExerciseId=null;S.exerciseRecallLoading=false;S.exerciseProgression=null;S.exerciseProgressionExerciseId=null;S.exerciseProgressionLoading=false;
if(result?.queued){S.sessionIntelligence=null;S.liveAdjustment={title:"Saved offline",detail:"This set is queued with an idempotent request ID and will sync when Forge reconnects."};}
else S.sessionIntelligence=result.session_intelligence||null;
if(result?.queued){}else if(S.sessionIntelligence){
const si=S.sessionIntelligence;
const rest=si.recommended_rest_seconds?` • Rest ${Math.round(si.recommended_rest_seconds)}s`:"";
const volume=si.recommended_total_sets!==si.planned_sets?` • ${si.recommended_total_sets} sets today`:"";
S.liveAdjustment={title:si.title||"Session adjustment",detail:`${si.why_changed||si.reason||"Adjusted from your latest set."}${rest}${volume}${si.estimated_remaining_minutes?` • ~${si.estimated_remaining_minutes} min left`:""}`};
if(!hasManualSetOverride(e)&&Number.isFinite(Number(si.recommended_total_sets))&&Number(si.recommended_total_sets)>=Number(si.completed_sets||0))saveAutoSetTarget(e,Number(si.recommended_total_sets));
}else if(result.next_target){const t=result.next_target;const target=t.load_mode==="timed"?`${t.suggested_duration_seconds}s`:t.load_mode==="bodyweight"?`${t.suggested_reps} reps`:`${Number(t.suggested_weight||0).toFixed(1).replace(/\.0$/,'')} lb × ${t.suggested_reps||e.min_reps}`;S.liveAdjustment={title:`Target: ${target}`,detail:t.reason||"Adjusted from your latest set."};} else if(rpe>=9)S.liveAdjustment={title:"Protect next sets",detail:"Very hard set. Hold load and stop before technique breaks."}; else if(rpe<=6)S.liveAdjustment={title:"You have room today",detail:"Easy set. Keep the target; another clean set supports progression."}; else S.liveAdjustment=null;
if(result.pr_events?.length){S.workoutPRs.push(...result.pr_events);toast(`🏆 ${result.pr_events[0].label}: ${result.pr_events[0].exercise_name}`)}
S.exerciseElapsed=0;stopExerciseTimer();
S.set++;
const setGoal=effectiveSetCount(e);
if(S.set>=setGoal){
clearAutoSetTarget(e);S.set=0;S.ei++;S.sessionIntelligence=null;S.liveAdjustment=null;
if(S.ei>=w().exercises.length){
await persistPosition();await api("/me/workout/complete",{method:"POST",queueable:true,body:JSON.stringify({session_id:session.session_id,completed:true})});
S.lastSessionId=session.session_id;plan=await api("/me/plan/current");session=null;S.ei=0;S.set=0;go("complete");loadCompletedWorkoutSummary();
}else{await persistPosition();await beginPersistentRest(Number(S.sessionIntelligence?.recommended_rest_seconds||e.rest_seconds||60),{exercise:e.name,base:Number(e.rest_seconds||60),recommended:Number(S.sessionIntelligence?.recommended_rest_seconds||e.rest_seconds||60)})}
}else{await persistPosition();await beginPersistentRest(Number(S.sessionIntelligence?.recommended_rest_seconds||e.rest_seconds||60),{exercise:e.name,base:Number(e.rest_seconds||60),recommended:Number(S.sessionIntelligence?.recommended_rest_seconds||e.rest_seconds||60)})}
}
function stopTimer(){if(S.timer){clearInterval(S.timer);S.timer=null}}function startTimer(){stopTimer();const update=()=>{const mm=String(Math.floor(S.restRemaining/60)).padStart(2,"0"),ss=String(S.restRemaining%60).padStart(2,"0");const el=document.querySelector("#restClock");if(el)el.textContent=`${mm}:${ss}`;const floating=document.querySelector("#floatingRestClock");if(floating)floating.textContent=`${mm}:${ss}`;const ring=document.querySelector(".ring");if(ring&&S.restTotal)ring.style.setProperty("--rest-pct",`${S.restRemaining/S.restTotal*100}%`)};update();S.timer=setInterval(()=>{S.restRemaining=Math.max(0,S.restRemaining-1);update();if(S.restRemaining<=0){stopTimer();clearPersistentRest();toast("Rest complete");if(S.route==="timer")go("exercise");else render()}},1000)}
function saveEquipmentDetailForm(){
const item=S.equipmentLog.find(x=>x.key===S.equipmentEditKey);if(!item)return;
item.details=item.details||{};
document.querySelectorAll("[data-equipment-detail]").forEach(el=>{
const k=el.dataset.equipmentDetail;
if(el.type==="checkbox")item.details[k]=el.checked;
else if(el.value==="")delete item.details[k];
else item.details[k]=Number(el.value);
});
const notes=document.querySelector("#equipmentNotes")?.value?.trim();
if(notes)item.details.notes=notes;else delete item.details.notes;
}
async function act(a){
try{
if(a==="repeat-last-set"){const last=(S.exerciseRecall?.sets||[]).at(-1);if(last){const weight=document.querySelector("#weight"),reps=document.querySelector("#reps"),rpe=document.querySelector("#rpe");if(weight&&last.weight!=null)weight.value=last.weight;if(reps&&last.reps!=null)reps.value=last.reps;if(rpe&&last.rpe!=null){rpe.value=last.rpe;document.querySelectorAll("[data-rpe]").forEach(x=>x.classList.toggle("selected",Number(x.dataset.rpe)===Number(last.rpe)))}toast("Last set copied")}return}
if(a==="current-exercise-history"){const e=w()?.exercises?.[S.ei];if(e){S.historyExercise=e.exercise_id;go("exercisehistory")}return}
if(a==="skip-core-rest"){stopCoreRest();render();return}
if(a==="exercise-timer-toggle"){toggleExerciseTimer();return}
if(a==="exercise-timer-reset"){resetExerciseTimer();return}
if(a==="register-screen")go("register");if(a==="google-mock")toast("Google sign-in is not connected yet");
if(a==="login-screen")go("login");
if(a==="next"){S.route={goal:"experience",experience:"schedule",schedule:"equipment"}[S.route];render();}
if(a==="equipment-next"){await saveEquipmentLog();go("preferences");}
if(a==="toggle-selected-equipment"){S.equipmentSelectedOnly=!S.equipmentSelectedOnly;render();}
if(a==="equipment-detail-save"){saveEquipmentDetailForm();go(S.equipmentReturn==="onboarding"?"equipment":"equipmentlog");toast("Equipment details saved");}
if(a==="equipment-save"){await saveEquipmentLog();toast("Equipment log saved");go(S.equipmentReturn==="plan"?"plan":"home");}
if(a==="edit-equipment-log"){S.equipmentReturn="plan";S.equipmentLoaded=false;go("equipmentlog");}
if(a==="open-exercise-directory"){S.exerciseDirectory=null;go("exercisedirectory");}
if(a==="directory-compatible"){S.exerciseDirectoryCompatible=!S.exerciseDirectoryCompatible;S.exerciseDirectory=null;loadExerciseDirectory();}
if(a==="directory-history"){if(S.exerciseDirectorySelected){S.historyExercise=S.exerciseDirectorySelected.id;go("exercisehistory");}}
if(a==="add-custom-equipment")addCustomEquipment();
if(a==="pref-avoid"){S.prefMode="avoid";S.preferenceReturn="preferences";go("preferencepicker");}
if(a==="pref-focus"){S.prefMode="focus";S.preferenceReturn="preferences";go("preferencepicker");}
if(a==="pref-cardio-frequency"){S.preferenceReturn="preferences";go("cardiofrequencypicker");}
if(a==="pref-cardio-intensity"){S.preferenceReturn="preferences";go("cardiopicker");}
if(a==="pref-split"){S.preferenceReturn="preferences";go("splitpicker");}
if(a==="pref-sport"){S.preferenceReturn="preferences";go("sportpicker");}
if(a==="pref-core"){S.preferenceReturn="preferences";go("corepicker");}
if(a==="open-training-settings")go("trainingsettings");
if(a==="settings-split"){S.preferenceReturn="trainingsettings";go("splitpicker");}
if(a==="edit-custom-split"){ensureCustomSplit();go("customsplit");}
if(a==="custom-split-done"){ensureCustomSplit();profile.workout_split="custom";go(S.preferenceReturn==="trainingsettings"?"trainingsettings":"preferences");}
if(a==="settings-cardio-frequency"){S.preferenceReturn="trainingsettings";go("cardiofrequencypicker");}
if(a==="settings-cardio-intensity"){S.preferenceReturn="trainingsettings";go("cardiopicker");}
if(a==="settings-sport"){S.preferenceReturn="trainingsettings";go("sportpicker");}
if(a==="settings-core"){S.preferenceReturn="trainingsettings";go("corepicker");}
if(a==="settings-calendar"){go("calendarsettings");}
if(a==="pwa-install"){await installForgePWA();}
if(a==="refresh-timezone"){await syncDeviceTime();S.timeSettings=(await api("/me/time")).settings;toast("Timezone refreshed");render();}
if(a==="calendar-settings-save"){
const time=document.querySelector("#defaultWorkoutTime")?.value||"17:00";
const enabled=!!document.querySelector("#calendarSyncToggle")?.checked;
const payload={...deviceTimePayload(),default_workout_time:time,calendar_sync_enabled:enabled};
const data=await api("/me/time",{method:"PUT",body:JSON.stringify(payload)});
S.timeSettings=data.settings;S.calendarStatus=await api("/me/calendar/status");startCalendarPolling();
if(enabled&&S.calendarStatus.connected)await syncCalendar({silent:true});
toast("Calendar & time settings saved");render();
}
if(a==="calendar-recheck"){
S.calendarStatus=await api("/me/calendar/status");
toast(S.calendarStatus.configured?"Google setup detected":"Google credentials are still missing");
render();
}
if(a==="calendar-connect"){
try{
const returnUrl=location.origin+location.pathname+"?return_to=calendar";
const data=await api(`/me/calendar/google/start?return_url=${encodeURIComponent(returnUrl)}`);
if(!data.authorization_url)throw Error("Google authorization URL was not returned");
location.href=data.authorization_url;
}catch(e){
toast(e.message||"Could not start Google Calendar connection");
S.calendarStatus=await api("/me/calendar/status").catch(()=>S.calendarStatus);
render();
}
}
if(a==="calendar-sync-now"){await syncCalendar();}
if(a==="calendar-disconnect"){
if(confirm("Disconnect Google Calendar from Forge?")){
await api("/me/calendar/disconnect",{method:"POST"});S.calendarStatus=await api("/me/calendar/status");stopCalendarPolling();toast("Google Calendar disconnected");render();
}
}
if(a==="nutrition-add")go("nutritionadd");
if(a==="workout-builder"){try{S.planLocks=await api("/me/plan/locks")}catch{}go("workoutbuilder");}
if(a==="builder-add"){S.exerciseDirectorySearch="";S.exerciseDirectoryCompatible=true;S.exerciseDirectory=null;go("exercisedirectory");loadExerciseDirectory();toast("Choose an exercise, then add it from its detail page");}
if(a==="directory-favorites"){S.exerciseDirectoryFavorites=!S.exerciseDirectoryFavorites;render();}
if(a==="directory-add-current"&&S.exerciseDirectorySelected&&w()){await api(`/me/workouts/${w().workout_id}/exercises`,{method:"POST",body:JSON.stringify({exercise_id:S.exerciseDirectorySelected.id})});plan=await api("/me/plan/current");toast("Exercise added");go("workoutbuilder");}
if(a==="nutrition-copy-yesterday"){await api("/me/nutrition/copy-yesterday",{method:"POST",body:JSON.stringify({entry_date:nutritionDateValue()})});S.nutrition=null;await loadNutrition();toast("Yesterday copied");}
if(a==="body-metric-add"){S.bodyMetricModal=true;render();}
if(a==="body-metric-close"){S.bodyMetricModal=false;render();}
if(a==="body-metric-save"){
const val=id=>{const el=document.querySelector(id);return el&&el.value!==""?+el.value:null};
const body={entry_date:document.querySelector("#bodyDate").value,weight_lb:val("#bodyWeight"),body_fat_pct:val("#bodyFat"),waist_in:val("#bodyWaist"),chest_in:val("#bodyChest"),hips_in:val("#bodyHips"),arm_in:val("#bodyArm"),thigh_in:val("#bodyThigh"),notes:document.querySelector("#bodyNotes").value.trim()||null};
await api("/me/body-metrics",{method:"POST",body:JSON.stringify(body)});
S.bodyMetricModal=false;await loadBodyMetrics();await loadProgressIntelligence();toast("Body check-in saved");
}
if(a==="open-notifications"){S.route="notifications";await loadNotifications(true);render();return;}
if(a==="nutrition-targets"){S.nutritionEditingTargets=true;render();}
if(a==="nutrition-close-modal"){S.nutritionEditingTargets=false;render();}
if(a==="nutrition-save-targets"){
const body={calories:+document.querySelector("#targetCalories").value||0,protein_g:+document.querySelector("#targetProtein").value||0,carbs_g:+document.querySelector("#targetCarbs").value||0,fat_g:+document.querySelector("#targetFat").value||0};
await api("/me/nutrition/targets",{method:"PUT",body:JSON.stringify(body)});
S.nutritionEditingTargets=false;S.nutrition=null;await loadNutrition();toast("Nutrition targets saved");
}
if(a==="nutrition-save-food"){
const food=document.querySelector("#foodName").value.trim();if(!food){toast("Enter a food name");return}
const body={entry_date:nutritionDateValue(),meal_type:document.querySelector("#mealType").value,food_name:food,calories:+document.querySelector("#foodCalories").value||0,protein_g:+document.querySelector("#foodProtein").value||0,carbs_g:+document.querySelector("#foodCarbs").value||0,fat_g:+document.querySelector("#foodFat").value||0};
await api("/me/nutrition/entries",{method:"POST",body:JSON.stringify(body)});
S.nutrition=null;toast("Food added");go("nutrition");
}
if(a==="repair-integrity"){try{const r=await api("/me/system/integrity/repair",{method:"POST",body:"{}"});S.integrityReport=r.report;S.sessionDiagnostics=await api("/me/system/session-diagnostics");toast("Forge repaired safe data issues");render()}catch(e){toast(e.message||"Repair failed")}return}
if(a==="settings-save"){
const saved=await api("/me/profile",{method:"POST",body:JSON.stringify(profile)});
const regenerated=!!saved.plan_regenerated;
if(saved.regenerated_plan)plan=saved.regenerated_plan;
for(const k of Object.keys(profile)){if(saved[k]!==undefined)profile[k]=saved[k]}
toast(regenerated?"Settings saved • full plan regenerated":"Training settings saved");
S.preferenceReturn="preferences";
go(plan?"plan":"preferences");
}
if(a==="pref-done"){
const dest=S.preferenceReturn==="trainingsettings"?"trainingsettings":"preferences";
S.preferenceReturn="preferences";
go(dest);
}
if(a==="adjust-plan"){S.preferredDays=[];S.planPreview=null;S.planDiagnostics=null;try{S.planLocks=await api("/me/plan/locks")}catch{}go("adjustplan");return;}
if(a==="cancel-plan-preview"){S.planPreview=null;S.planDiagnostics=null;toast("Current plan kept");render();return;}
if(a==="apply-plan-preview"){const d=await api("/me/plan/reconfigure",{method:"POST",body:JSON.stringify({days_per_week:profile.days_per_week,minutes_per_workout:profile.minutes_per_workout,exercises_per_day:profile.exercises_per_day||6,exercises_per_workout:normalizedExerciseTargets(),preferred_days:[...S.preferredDays].sort((a,b)=>a-b),custom_split:profile.workout_split==="custom"?(profile.custom_split||[]):[]})});plan=d.plan;Object.assign(profile,d.profile||{});S.planPreview=null;toast("New plan applied");S.planTab="overview";go("plan");return;}
if(a==="save-plan-adjust"){
if(S.preferredDays.length!==profile.days_per_week)throw Error(`Choose exactly ${profile.days_per_week} training days`);
S.planAdjusting=true;render();
try{const rebuildBody={days_per_week:profile.days_per_week,minutes_per_workout:profile.minutes_per_workout,exercises_per_day:profile.exercises_per_day||6,exercises_per_workout:normalizedExerciseTargets(),preferred_days:[...S.preferredDays].sort((a,b)=>a-b),custom_split:profile.workout_split==="custom"?(profile.custom_split||[]):[]};S.planDiagnostics=await api("/me/plan/validate",{method:"POST",body:JSON.stringify(rebuildBody)});if(S.planDiagnostics.errors?.length)throw Error(S.planDiagnostics.errors.join(" • "));S.planPreview=await api("/me/plan/preview",{method:"POST",body:JSON.stringify(rebuildBody)});toast("Preview ready — validation passed");render();}finally{S.planAdjusting=false}
return;
}
if(a==="readiness-skip"){S.todayAdjustment=null;await startWorkout();return}
if(a==="readiness-apply"){const local=computeReadinessAdjustment();let adj=local;try{const c=S.readinessCheckin||{},ww=w();const remote=await api("/me/readiness/evaluate",{method:"POST",body:JSON.stringify({energy:Number(c.energy||3),soreness:Number(c.soreness||2),motivation:Number(c.motivation||3),sleep:Number(c.sleep||3),minutes_available:Number(c.minutes||local.planned),planned_minutes:Number(ww?.estimated_minutes||profile.minutes_per_workout||45)})});adj={...local,...remote,setReduction:Number(remote.set_reduction??local.setReduction),keepExercises:remote.keep_ratio<.95?Math.max(2,Math.ceil((ww?.exercises||[]).length*remote.keep_ratio)):null,loadCue:`Keep effort at or below RPE ${remote.effort_cap}.`};}catch(e){console.warn("Recovery Intelligence 2.0 fallback",e)}applyTodayAdjustment(adj);await startWorkout();toast(adj.mode==="normal"?"Workout kept as planned":"Today’s workout adjusted");return}
if(a==="generate")await generatePlan();
if(a==="edit")go("goal");
if(a==="startplan")go("home");
if(a==="viewplan"){S.planTab="workouts";go("plan");}
if(a==="gohome")go("home");
if(a==="startworkout"){S.readinessCheckin=null;S.todayAdjustment=null;S.liveAdjustment=null;S.sessionIntelligence=null;S.readinessReturn=S.route;go("readiness");return}
if(a==="openexercise")go("exercise");if(a==="swap-exercise")go("swapexercise");
if(a==="start-demo-review-queue"){
const ready=(S.demoAudit||[]).filter(x=>x.has_3d&&!x.reviewed);
if(!ready.length){toast("No asset-ready demos need review");return}
await openDemoReview(ready[0].id);return
}
if(a==="demo-review-prev"){await moveDemoReviewQueue(-1);return}
if(a==="demo-review-next"){await moveDemoReviewQueue(1);return}
if(a==="save-demo-review"){
const payload={};
document.querySelectorAll("[data-demo-review]").forEach(x=>payload[x.dataset.demoReview]=x.checked);
payload.notes=document.querySelector("[data-demo-review-notes]")?.value||"";
try{
S.demoReview=await api(`/me/exercises/${S.demoReviewExercise}/demo-review`,{method:"PUT",body:JSON.stringify(payload)});
toast(S.demoReview.complete?"Demo marked Reviewed":"Review saved");
if(S.demoReview.complete&&S.demoReviewQueueIndex<S.demoReviewQueue.length-1){
await moveDemoReviewQueue(1);
}else render();
}catch(e){toast(e.message)}
return
}
if(a==="open-demo-audit"){await openDemoAudit();return}
if(a==="cache-plan-demos"){await cacheCurrentPlanDemos(false);render();return}
if(a==="move-core-module"){S.moduleMoveType="core";S.moduleMoveSourceIndex=S.wi;S.moduleMoveTarget=null;go("modulemove");return}
if(a==="move-cardio-module"){S.moduleMoveType="cardio";S.moduleMoveSourceIndex=S.wi;S.moduleMoveTarget=null;go("modulemove");return}
if(a==="cancel-module-move"){S.moduleMoveType=null;S.moduleMoveTarget=null;go("workout");return}
if(a==="apply-module-move"){
if(!S.moduleMoveTarget)throw Error("Choose a training day");
const source=plan.workouts[S.moduleMoveSourceIndex];
const result=await api(`/me/workouts/${source.workout_id}/modules/${S.moduleMoveType}/move`,{method:"POST",body:JSON.stringify({target_workout_id:S.moduleMoveTarget})});
plan=result.plan;S.wi=plan.workouts.findIndex(x=>x.workout_id===S.moduleMoveTarget);S.moduleMoveType=null;S.moduleMoveTarget=null;toast("Module moved");go("workout");return;
}
if(a==="start-core-module"){
stopCoreTimer();stopCoreRest();S.coreTimerElapsed={};S.coreEffort={};S.coreCompleted={};
S.moduleWorkoutIndex=S.wi;
const d=await api(`/me/workouts/${w().workout_id}/modules/core/start`,{method:"POST"});
S.moduleSession=d.session;restoreCoreSequenceFromLogs(d.module,d.logs||[]);go("coretracker");return;
}
if(a==="start-cardio-module"){
S.cardioEffort=7;S.moduleWorkoutIndex=S.wi;
const d=await api(`/me/workouts/${w().workout_id}/modules/cardio/start`,{method:"POST"});
S.moduleSession=d.session;go("cardiotracker");return;
}
if(a==="complete-core-module"){
stopCoreTimer();stopCoreRest();
const ww=plan.workouts[S.moduleWorkoutIndex],m=ww.core_module;
if(!coreAllSetsCompleted(m))throw Error("Complete every programmed core set first");
const effortValues=Object.values(S.coreEffort).map(Number).filter(Number.isFinite);
const avgEffort=effortValues.length?effortValues.reduce((a,b)=>a+b,0)/effortValues.length:7;
await api(`/me/modules/${S.moduleSession.id}/complete`,{method:"POST",body:JSON.stringify({completed_minutes:m.estimated_minutes||8,rpe:avgEffort})});
plan=await api("/me/plan/current");S.moduleSession=null;S.moduleSummary=await api("/me/modules/summary");
toast("Core circuit completed — progression saved");go("workout");return;
}
if(a==="complete-cardio-module"){
const mins=Number(document.querySelector("#cardioMinutes")?.value||0),rpe=Number(document.querySelector("#cardioRpe")?.value||7),distance=Number(document.querySelector("#cardioDistance")?.value||0),pace=document.querySelector("#cardioPace")?.value?.trim()||null;
if(mins<=0)throw Error("Enter completed cardio minutes");
await api(`/me/modules/${S.moduleSession.id}/complete`,{method:"POST",body:JSON.stringify({completed_minutes:mins,rpe,distance:distance||null,pace})});
plan=await api("/me/plan/current");S.moduleSession=null;S.moduleSummary=await api("/me/modules/summary");toast("Cardio completed");go("workout");return;
}
if(a==="swap-cardio")go("cardioswap");
if(a==="cancel-cardio-swap")go("workout");
if(a==="apply-cardio-swap")await applyCardioSwap();if(a==="back-exercise")go("exercise");if(a==="swap-selected"){if(S.selectedSwap)await applySwap(S.selectedSwap);else toast("Select an exercise first");}if(a==="abandon"){if(session&&confirm("Abandon this workout? Logged sets will remain in history.")){await api("/me/workout/abandon",{method:"POST",body:JSON.stringify({session_id:session.session_id})});session=null;S.ei=0;S.set=0;S.restRemaining=0;plan=await api("/me/plan/current");go("home");toast("Workout abandoned")}}
if(a==="finish-exercise"){
if(!session)return;
const e=w()?.exercises?.[S.ei];if(!e)return;
clearAutoSetTarget(e);S.set=0;S.ei++;S.sessionIntelligence=null;S.liveAdjustment=null;
if(S.ei>=w().exercises.length){await persistPosition();await api("/me/workout/complete",{method:"POST",queueable:true,body:JSON.stringify({session_id:session.session_id,completed:true})});S.lastSessionId=session.session_id;plan=await api("/me/plan/current");session=null;S.ei=0;go("complete");loadCompletedWorkoutSummary();return}
await persistPosition();go("exercise");return
}
if(a==="nutrition-favorites-only"){S.nutritionFavoritesOnly=!S.nutritionFavoritesOnly;render();return}
if(a==="completeset")await saveSet();if(a==="skip-set"){S.set++;await persistPosition();toast("Set skipped");render();}
if(a==="open-rest"){go("timer");}
if(a==="view-workout-rest"){go("workout");startTimer();}
if(a==="skiprest"){await clearPersistentRest();go("exercise");}
if(a==="finish"||a==="finish-progress"||a==="finish-nutrition"){
if(S.lastSessionId){try{await api("/me/workout/feedback",{method:"POST",body:JSON.stringify({session_id:S.lastSessionId,feedback:S.feel})})}catch(e){toast(e.message)}}
S.lastSessionId=null;
go(a==="finish-progress"?"progress":a==="finish-nutrition"?"nutrition":"home");
}
if(a==="reload-app"){location.reload();}
if(a==="close-more"){S.moreOpen=false;render();}
if(a==="open-training-settings"){S.moreOpen=false;go("trainingsettings");}
if(a==="open-equipment-log"){S.moreOpen=false;S.equipmentReturn="settings";go("equipmentlog");}
if(a==="open-calendar-settings"){loadCalendarIntelligence();S.moreOpen=false;go("calendarsettings");}
if(a==="signout"){
if(confirm("Sign out of Forge? Your saved data will remain on your account.")){
try{await api("/auth/logout",{method:"POST"})}catch{}
localStorage.removeItem("forge_auth_token");authToken="";account=null;plan=null;session=null;stopCalendarPolling();S.moreOpen=false;S.route="welcome";render();toast("Signed out");
}
}
if(a==="history")go("history");if(a==="prs")go("prs");if(a==="sendcoach")await sendCoach();
if(a==="apply-coach")await applyCoachAction();
if(a==="apply-adaptation")await applyAdaptiveWeek();
if(a==="clear-coach"){await api("/me/coach/history",{method:"DELETE"});S.coachMessages=[];S.coachAction=null;render();}
}catch(e){toast(e.message);}
}
document.querySelector("#backBtn").onclick=()=>{
if(S.route==="equipmentlog"&&S.equipmentReturn==="settings"){S.equipmentReturn="onboarding";go("trainingsettings");return;}
const pickerRoutes=["preferencepicker","cardiopicker","cardiofrequencypicker","splitpicker","sportpicker","corepicker"];
if(pickerRoutes.includes(S.route)){
const dest=S.preferenceReturn==="trainingsettings"?"trainingsettings":"preferences";
S.preferenceReturn="preferences";
go(dest);
return;
}
const dest=S.route==="demoreview"?"demoaudit":S.route==="demoaudit"?"formdemo":S.route==="formdemo"?(S.formDemoReturn||"exercise"):{register:"welcome",login:"welcome",history:"progress",prs:"history",exercisehistory:"prs",swapexercise:"exercise",cardioswap:"workout",modulemove:"workout",coretracker:"workout",cardiotracker:"workout",nutritionadd:"nutrition",experience:"goal",schedule:"experience",equipment:"schedule",equipmentlog:plan?"plan":"equipment",equipmentdetails:S.equipmentReturn==="onboarding"?"equipment":"equipmentlog",exercisedirectory:plan?"plan":"preferences",exercisedetail:"exercisedirectory",preferences:"equipment",yourplan:"preferences",readiness:S.readinessReturn||"home",workout:"home",exercise:"workout",timer:"exercise",complete:"home",plan:"home",calendarsettings:"trainingsettings",adjustplan:"plan"}[S.route]||"home";
go(dest);
};
document.querySelector("#moreBtn").onclick=()=>{if(authToken){S.moreOpen=!S.moreOpen;render()}else toast("Forge Fitness v15.10.1")};
const calendarParams=new URLSearchParams(location.search);
const calendarJustConnected=calendarParams.get("calendar_connected")==="1";
const calendarSyncWarning=calendarParams.get("calendar_sync_warning")==="1";
if(calendarJustConnected){
history.replaceState({},document.title,location.pathname);
S.calendarStatus=null;
}
setupPWA();
loadExisting().then(async()=>{
const pwaRoute=new URLSearchParams(location.search).get("pwa_route");
if(plan&&["workout","nutrition","coach","plan","progress","home"].includes(pwaRoute||""))S.route=pwaRoute;
render();
if(calendarJustConnected){
try{
S.calendarStatus=await api("/me/calendar/status");
if(S.calendarStatus.connected){
toast(calendarSyncWarning?"Calendar connected — initial sync needs attention":"Calendar connected");
if(S.route==="calendarsettings")render();
}
}catch{}
}
});
document.addEventListener("click",async(e)=>{
if(e.target?.id!=="nutritionProviderStatusBtn")return;
try{
const d=await api("/nutrition/providers/status");
const u=d.providers?.usda||{}, o=d.providers?.openfoodfacts||{};
alert(`Nutrition Providers\nUSDA: ${u.status||"unknown"} — ${u.detail||""}\nOpen Food Facts: ${o.status||"unknown"} — ${o.detail||""}`);
}catch(err){ alert("Could not check nutrition provider status: "+err.message); }
});
window.addEventListener("online",()=>{if(authToken&&plan)cacheCurrentPlanDemos(true)});
window.addEventListener("online",()=>{S.online=true;replayOfflineWorkoutWrites().catch(e=>console.warn("Offline replay",e));});
