
const API = localStorage.getItem("forge_api_url") || (
  location.protocol==="https:" ? location.origin : `http://${location.hostname}:8000`
);
let authToken = localStorage.getItem("forge_auth_token") || "";
let account = null;
let plan = null, session = null;
const profile = {goal:"build_muscle",experience:"intermediate",days_per_week:4,minutes_per_workout:45,equipment:["full_gym"],preferred_exercises:[],excluded_exercises:[],priority_muscles:[],recovery_level:"normal",cardio_preference:"moderate",workout_split:"auto",sport:"general",core_workouts_per_week:2,cardio_workouts_per_week:2,custom_split:[],exercises_per_day:6,exercises_per_workout:[],seed:42};
const S={route:"welcome",onboardStep:0,wi:0,ei:0,set:0,restRemaining:0,restTotal:0,timer:null,feel:"Just Right",name:"Athlete",coachDraft:"",startupError:null,historyExercise:null,workoutPRs:[],exerciseRecall:null,exerciseRecallExerciseId:null,exerciseRecallLoading:false,swapOptions:[],coachMessages:[],coachAction:null,coachContext:null,coachLoaded:false,coachStatus:null,coachBriefing:null,coachStack:null,systemHealth:null,progressHub:null,strengthTrend:null,strengthExercise:"overall",strengthRange:"90",strengthPoint:null,planTab:"overview",equipmentCatalog:[],equipmentPresets:{},equipmentLog:[],equipmentLoaded:false,equipmentReturn:"onboarding",equipmentSearch:"",equipmentCategory:"All",equipmentSelectedOnly:false,equipmentEditKey:null,exerciseDirectory:null,exerciseDirectorySearch:"",exerciseDirectoryMuscle:"All",exerciseDirectoryDifficulty:"All",exerciseDirectoryCompatible:true,exerciseDirectorySelected:null,lastSessionId:null,sessionStartedAt:null,completedWorkoutSummary:null,preferenceReturn:"preferences",timeSettings:null,calendarStatus:null,calendarIntelligence:null,clockTimer:null,calendarPollTimer:null,cardioSwapOptions:[],selectedCardioSwap:null,nutrition:null,nutritionDate:null,nutritionEditingTargets:false,nutritionSavedFoods:[],nutritionEditEntry:null,nutritionCoachSummary:null,notifications:null,notificationSettings:null,progressIntelligence:null,bodyMetrics:null,bodyMetricRange:"90",bodyMetricModal:false,prRecords:[],prView:"exercise",prLiftFilter:"all",prCollapsedGroups:{},homeDashboard:null,adaptationPreview:null,mesocycle:null,adaptationBusy:false,planAdjusting:false,preferredDays:[],pwaInstallPrompt:null,pwaInstalled:false,pwaDismissed:false,moreOpen:false,online:navigator.onLine,updateReady:false,exerciseElapsed:0,exerciseTimer:null,exerciseTimerRunning:false,exerciseTimerTarget:0,moduleSession:null,moduleWorkoutIndex:null,moduleSummary:null,coreTimerElapsed:{},coreTimerRunning:null,coreTimerInterval:null,coreEffort:{},cardioEffort:7,coreCompleted:{},coreRestRemaining:0,coreRestTimer:null,moduleMoveType:null,moduleMoveSourceIndex:null,moduleMoveTarget:null,coreSequenceIndex:0,formDemo:null,formDemoExercise:null,formDemoReturn:"exercise",formDemoTab:"demo",demoOfflineStatus:null,demoAudit:null,demoReview:null,demoReviewExercise:null,demoReviewQueue:[],demoReviewQueueIndex:0,demoAngle:"primary",readinessCheckin:null,todayAdjustment:null,liveAdjustment:null,sessionIntelligence:null,planPreview:null,planDiagnostics:null,planLocks:{},readinessReturn:"home",swapReason:"preference",recoveryIntelligence:null,trainingDashboard:null,exerciseProgression:null,exerciseProgressionExerciseId:null,exerciseProgressionLoading:false,substitutionIntelligence:null,trainingRecords:null,coach4:null,exerciseDirectoryEquipment:"All",exerciseDirectoryMovement:"All",exerciseDirectoryFavorites:false,workoutBuilderExercise:null};
const V=document.querySelector("#view"),toastEl=document.querySelector("#toast"),nav=document.querySelector("#bottomNav"),topbar=document.querySelector("#topbar");
const toast=t=>{toastEl.textContent=t;toastEl.classList.add("show");setTimeout(()=>toastEl.classList.remove("show"),1800)};
const esc=ForgeCore.esc;
const requestId=ForgeCore.requestId;

const PWA=ForgePWA.create({state:S,toast,render:()=>render()});
const {isStandalonePWA,isIOSDevice,pwaInstallCard,installForgePWA,setupPWA}=PWA;

function networkBanner(){
  if(S.online)return "";
  return `<div class=network-banner role=status><b>Offline</b><span>Some Forge features need an internet connection. Your current screen stays available.</span></div>`;
}
function updateBanner(){
  return S.updateReady?`<div class=update-banner><span><b>Forge update ready</b><small>Reload to use the latest version.</small></span><button data-a=reload-app>Reload</button></div>`:"";
}
function moreSheet(){
  if(!S.moreOpen||!authToken)return "";
  return `<div class=more-backdrop data-a=close-more>
    <div class=more-sheet onclick="event.stopPropagation()">
      <div class=more-sheet-handle></div>
      <div class=more-account><div class=more-avatar>${esc((S.name||"F").slice(0,1).toUpperCase())}</div><div><small>FORGE ACCOUNT</small><h3>${esc(S.name)}</h3><span>${esc(account?.email||"Signed in")}</span></div></div>
      <button data-a=open-training-settings><span>⚙</span><div><b>Training Settings</b><small>Plan, cardio, core, app install</small></div><em>›</em></button>
      <button data-a=open-equipment-log><span>▣</span><div><b>Equipment Log</b><small>Manage available gym equipment</small></div><em>›</em></button>
      <button data-a=open-calendar-settings><span>▦</span><div><b>Calendar & Time</b><small>${S.calendarStatus?.connected?"Google Calendar connected":"Schedule and timezone"}</small></div><em>›</em></button>
      <button class=more-signout data-a=signout><span>↪</span><div><b>Sign Out</b><small>Your Forge data stays saved</small></div></button>
      <div class=more-version>Forge Fitness v14.61.0</div>
    </div>
  </div>`;
}
function finalPolishSettingsCard(){
  return `<div class="card final-settings-card"><div class=row><div><p class=eyebrow>FORGE APP</p><h3>App & account</h3></div><span class=version-pill>v14.61.0</span></div>
    <div class=settings-status-row><span>Connection</span><b>${S.online?"Online":"Offline"}</b></div>
    <div class=settings-status-row><span>Install mode</span><b>${isStandalonePWA()?"Installed app":"Browser"}</b></div>
    <div class=settings-status-row><span>Calendar</span><b>${S.calendarStatus?.connected?"Connected":"Not connected"}</b></div>
  </div>`;
}


function equipmentIcon(key,name="",category=""){return ForgeEquipment.icon(key,name,category)}


const w=()=>plan?.workouts?.[S.wi]||null;
async function api(path,opt={}){return ForgeApi.request(API,()=>authToken,S,path,opt)}
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
    if(plan)await restoreSession();
    // App launches always land on Home. An active workout remains resumable,
    // but it no longer hijacks startup and opens a random exercise/rest screen.
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
    S.wi=Number(s.workout_index||0);S.ei=Number(s.current_exercise_index||0);S.set=Number(s.current_set_index||0);
    if(s.rest_started_at&&s.rest_duration_seconds){
      const elapsed=Math.max(0,Math.floor((Date.now()-Date.parse(s.rest_started_at+"Z"))/1000));
      const remain=Math.max(0,Number(s.rest_duration_seconds)-elapsed);
      if(remain>0){S.restRemaining=remain;S.restTotal=Number(s.rest_duration_seconds);return;}
      try{await api("/me/session/rest/clear",{method:"POST",body:JSON.stringify({session_id:s.session_id})})}catch{}
    }
    // Preserve the active session/position only. Startup routing is handled by loadExisting().
  }catch(e){console.warn("Session restore failed",e)}
}
async function persistPosition(){
  if(!session)return;
  try{await api("/me/session/position",{method:"POST",body:JSON.stringify({session_id:session.session_id,exercise_index:S.ei,set_index:S.set})})}catch(e){console.warn(e)}
}
async function beginPersistentRest(seconds){
  S.restRemaining=seconds;S.restTotal=seconds;
  if(session){try{await api("/me/session/rest/start",{method:"POST",body:JSON.stringify({session_id:session.session_id,duration_seconds:seconds})})}catch(e){console.warn(e)}}
  go("timer");
}
async function clearPersistentRest(){
  if(session){try{await api("/me/session/rest/clear",{method:"POST",body:JSON.stringify({session_id:session.session_id})})}catch{}}
  S.restRemaining=0;
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
  if(!authToken)return;
  try{
    const [meta,log]=await Promise.all([api("/me/equipment/catalog"),api("/me/equipment")]);
    S.equipmentCatalog=meta.catalog||[];
    S.equipmentPresets=meta.presets||{};
    S.equipmentLog=log.items||[];
    profile.equipment=log.legacy_equipment||[];
    S.equipmentLoaded=true;
    if(["equipment","equipmentlog"].includes(S.route))render();
  }catch(e){console.warn("Equipment log load failed",e)}
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
function welcome(){
return `<div class="center welcome-screen welcome-v2">
  <div class=welcome-kicker>PERSONALIZED TRAINING</div>
  <div class=brand-lockup>FORGE<small>FITNESS</small></div>

  <div class=forge-hero aria-label="Athlete lifting a barbell">
    <div class=forge-hero-grid></div>
    <div class=forge-hero-glow></div>

    <svg class=forge-hero-art viewBox="0 0 360 220" aria-hidden="true">
      <defs>
        <linearGradient id="forgeMetal2" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="#f0f2f5"/>
          <stop offset=".42" stop-color="#89919c"/>
          <stop offset="1" stop-color="#343a43"/>
        </linearGradient>
        <linearGradient id="forgeRed2" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#ff3347"/>
          <stop offset="1" stop-color="#c01426"/>
        </linearGradient>
        <radialGradient id="forgeGlow2" cx=".5" cy=".5" r=".5">
          <stop offset="0" stop-color="#ef233c" stop-opacity=".32"/>
          <stop offset=".55" stop-color="#ef233c" stop-opacity=".08"/>
          <stop offset="1" stop-color="#ef233c" stop-opacity="0"/>
        </radialGradient>
      </defs>

      <ellipse cx="180" cy="112" rx="120" ry="82" fill="url(#forgeGlow2)"/>

      <!-- barbell: plates ordered biggest to smallest from inside to outside -->
      <g class=forge-barbell>
        <path d="M67 55h226" stroke="#d9dde2" stroke-width="5"/>

        <!-- left sleeve -->
        <rect x="54" y="35" width="10" height="40" rx="4" fill="url(#forgeMetal2)"/>
        <rect x="44" y="39" width="9" height="32" rx="3" fill="#59616b"/>
        <rect x="36" y="43" width="7" height="24" rx="3" fill="#343a42"/>
        <rect x="31" y="47" width="4" height="16" rx="2" fill="#7b838d"/>

        <!-- right sleeve -->
        <rect x="296" y="35" width="10" height="40" rx="4" fill="url(#forgeMetal2)"/>
        <rect x="307" y="39" width="9" height="32" rx="3" fill="#59616b"/>
        <rect x="317" y="43" width="7" height="24" rx="3" fill="#343a42"/>
        <rect x="325" y="47" width="4" height="16" rx="2" fill="#7b838d"/>
      </g>

      <!-- detailed athlete -->
      <g class=forge-athlete>
        <!-- head / neck -->
        <circle cx="180" cy="91" r="13" fill="#e8edf1"/>
        <path d="M174 102v8h12v-8" fill="#cbd2d8"/>
        <path d="M171 87c3-7 15-9 20-1" fill="none" stroke="#8b949e" stroke-width="3" stroke-linecap="round"/>

        <!-- muscular torso / shirt -->
        <path d="M159 111
                 C164 106 170 105 180 109
                 C190 105 196 106 201 111
                 L211 148
                 C202 154 194 157 180 157
                 C166 157 158 154 149 148z"
              fill="url(#forgeRed2)"/>
        <path d="M161 116c7 4 12 5 19 5s12-1 19-5" fill="none" stroke="#ff6675" stroke-width="2" opacity=".7"/>
        <path d="M180 121v28" stroke="#a80f20" stroke-width="2" opacity=".65"/>

        <!-- shoulders and arms: overhead press position -->
        <path d="M160 114
                 C153 111 148 106 144 100
                 L128 78
                 C125 74 125 70 129 67
                 C133 64 137 66 140 70
                 L158 91
                 C162 96 167 99 171 102"
              fill="#e8edf1"/>
        <path d="M200 114
                 C207 111 212 106 216 100
                 L232 78
                 C235 74 235 70 231 67
                 C227 64 223 66 220 70
                 L202 91
                 C198 96 193 99 189 102"
              fill="#e8edf1"/>

        <!-- forearms to bar -->
        <path d="M129 68L119 56" stroke="#dce2e7" stroke-width="10" stroke-linecap="round"/>
        <path d="M231 68L241 56" stroke="#dce2e7" stroke-width="10" stroke-linecap="round"/>
        <circle cx="119" cy="56" r="6" fill="#f0f3f5"/>
        <circle cx="241" cy="56" r="6" fill="#f0f3f5"/>

        <!-- arm definition -->
        <path d="M144 99c5-1 9-4 12-8M216 99c-5-1-9-4-12-8" fill="none" stroke="#aeb7bf" stroke-width="2" opacity=".8"/>
        <path d="M128 78c4 1 8 0 11-3M232 78c-4 1-8 0-11-3" fill="none" stroke="#aeb7bf" stroke-width="2" opacity=".7"/>

        <!-- shorts -->
        <path d="M153 148c8 5 17 7 27 7s19-2 27-7l3 20-23 2-7-9-7 9-23-2z" fill="#242a31"/>
        <path d="M180 155v9" stroke="#59616b" stroke-width="2"/>

        <!-- thighs / lower legs -->
        <path d="M166 164
                 C161 168 157 177 153 188
                 L144 199
                 C141 203 135 201 137 196
                 L149 166z"
              fill="#e8edf1"/>
        <path d="M194 164
                 C199 168 203 177 207 188
                 L216 199
                 C219 203 225 201 223 196
                 L211 166z"
              fill="#e8edf1"/>
        <!-- clean legs: no decorative strokes crossing the shin/thigh shapes -->

        <!-- shoes -->
        <path d="M139 195h18l7 5c2 2 1 5-2 5h-26c-4 0-5-5-1-7z" fill="#dce2e7"/>
        <path d="M221 195h-18l-7 5c-2 2-1 5 2 5h26c4 0 5-5 1-7z" fill="#dce2e7"/>
        <path d="M140 202h20M200 202h20" stroke="#717a84" stroke-width="1.5" stroke-linecap="round"/>

        <!-- chest anvil mark -->
        <g class=forge-shirt-anvil fill="#fff">
          <path d="M169 126h20c2 0 3 1 3 3v2h-7c-1 3-4 5-8 5h-5l2-5h-5z"/>
          <path d="M176 136h8v4h4v3h-16v-3h4z"/>
        </g>
      </g>

      <!-- stage: kept below the shoes so it never intersects the athlete -->
      <path d="M112 210h136" stroke="#353b43" stroke-width="3" stroke-linecap="round"/>
      <path d="M142 216h76" stroke="#1a1e23" stroke-width="5" stroke-linecap="round"/>
    </svg>

    <div class=forge-hero-caption>
      <span>TRAIN</span><i></i><span>TRACK</span><i></i><span>PROGRESS</span>
    </div>
  </div>

  <div class=welcome-copy>
    <h2>Train with purpose.<br>Progress with proof.</h2>
    <p>Adaptive workouts, nutrition, progress tracking, and coaching — all in one place.</p>
  </div>

  <div class=welcome-actions>
    <button class=btn data-a=register-screen>Get Started</button>
    <button class="btn dark" data-a=login-screen>Log In</button>
  </div>

  <p class=welcome-footnote>Built around your schedule, equipment, and goals.</p>
</div>`;
}

function register(){
return `<p class=eyebrow>CREATE ACCOUNT</p><h2>Create Account</h2><div class=big-spacer></div><form id=registerForm class=form>
<label class=field>Full Name<input name=display_name autocomplete=name placeholder="John Doe" required></label>
<label class=field>Email<input name=email type=email autocomplete=email placeholder="john.doe@email.com" required></label>
<label class=field>Password<input name=password type=password minlength=8 autocomplete=new-password placeholder="••••••••" required></label>
<label class=field>Confirm Password<input name=confirm_password type=password minlength=8 placeholder="••••••••" required></label>
<label class=muted><input name=terms type=checkbox required> I agree to the Terms of Service and Privacy Policy</label>
<button class=btn type=submit>Create Account</button></form><div class=spacer></div><div class=auth-link>Already have an account? <b data-a=login-screen>Log In</b></div>`;
}
function login(){
return `<p class=eyebrow>WELCOME BACK</p><h2>Welcome Back</h2><div class=big-spacer></div><form id=loginForm class=form>
<label class=field>Email<input name=email type=email autocomplete=email placeholder="john.doe@email.com" required></label>
<label class=field>Password<input name=password type=password autocomplete=current-password placeholder="••••••••" required></label>
<div style="text-align:right;color:var(--red2);font-size:10px">Forgot Password?</div><button class=btn type=submit>Log In</button></form>
<div class=spacer></div><div class=auth-help><b>Google Calendar connects after sign-in.</b><span>Your Forge account and Calendar connection stay separate.</span></div>
<div class=spacer></div><div class=auth-link>Don't have an account? <b data-a=register-screen>Register</b></div>`;
}

async function submitRegister(ev){
  ev.preventDefault();const f=new FormData(ev.target);
  if(f.get("password")!==f.get("confirm_password"))throw Error("Passwords do not match");
  const d=await api("/auth/register",{method:"POST",body:JSON.stringify({display_name:f.get("display_name"),email:f.get("email"),password:f.get("password")})});
  authToken=d.token;account=d.user;localStorage.setItem("forge_auth_token",authToken);S.name=account.display_name;go("goal");toast("Account created");
}
async function submitLogin(ev){
  ev.preventDefault();const f=new FormData(ev.target);
  const d=await api("/auth/login",{method:"POST",body:JSON.stringify({email:f.get("email"),password:f.get("password")})});
  authToken=d.token;account=d.user;localStorage.setItem("forge_auth_token",authToken);S.name=account.display_name;
  try{plan=await api("/me/plan/current");go("home")}catch{plan=null;go("goal")}toast("Signed in");
}

function goal(){
const opts=[["Build Muscle","Build size and strength","build_muscle"],["Lose Weight","Reduce body fat","lose_fat"],["Improve Strength","Lift heavier over time","get_stronger"],["Improve Endurance","Build work capacity","improve_fitness"],["General Fitness","Stay active and capable","general_fitness"]];
return `${dots(0)}<h2>What's your goal?</h2><p class=muted>Select the primary goal you want to achieve.</p><div class=big-spacer></div><div class=stack>${opts.map(o=>`<button class="choice-card ${profile.goal===o[2]?"selected":""}" data-goal=${o[2]}><div><strong>${o[0]}</strong><small>${o[1]}</small></div></button>`).join("")}</div><div class=big-spacer></div><button class=btn data-a=next>Next</button>`;
}

function experience(){
const opts=[["Beginner","New to training","beginner"],["Intermediate","1–3 years training","intermediate"],["Advanced","3+ years training","advanced"]];
return `${dots(1)}<h2>Your experience level?</h2><p class=muted>This helps us tailor your plan to your level.</p><div class=big-spacer></div><div class=stack>${opts.map(o=>`<button class="choice-card ${profile.experience===o[2]?"selected":""}" data-exp=${o[2]}><div><strong>${o[0]}</strong><small>${o[1]}</small></div></button>`).join("")}</div><div class=big-spacer></div><button class=btn data-a=next>Next</button>`;
}

function schedule(){
return `${dots(2)}<h2>How many days?</h2><p class=muted>How many days per week can you train?</p><div class=big-spacer></div><div class=choice-grid>${[2,3,4,5,6].map(n=>`<button class="choice-tile ${profile.days_per_week===n?"selected":""}" data-days=${n}><span><b>${n} Days</b><small>${n===2?"Minimal":n===3?"Recommended":n===4?"Balanced":"High frequency"}</small></span></button>`).join("")}</div><div class=big-spacer></div><p class=eyebrow>SESSION LENGTH</p><div class=chips>${[20,30,45,60,90].map(n=>`<button class="chip ${profile.minutes_per_workout===n?"selected":""}" data-mins=${n}>${n} min</button>`).join("")}</div><div class=big-spacer></div><p class=eyebrow>EXERCISES PER WORKOUT</p><p class=muted>Choose how many strength exercises Forge should target each training day.</p><div class=chips>${[3,4,5,6,7,8,9,10].map(n=>`<button class="chip ${Number(profile.exercises_per_day||6)===n?"selected":""}" data-exercise-count=${n}>${n}</button>`).join("")}</div><div class=big-spacer></div><button class=btn data-a=next>Next</button>`;
}

function equipmentLogView(onboarding=true){
const selected=S.equipmentLog;
const q=(S.equipmentSearch||"").trim().toLowerCase();
const categories=["All",...new Set(S.equipmentCatalog.map(x=>x.category))];
let catalog=S.equipmentCatalog.filter(c=>
  (!q||c.name.toLowerCase().includes(q)||c.category.toLowerCase().includes(q)) &&
  (S.equipmentCategory==="All"||c.category===S.equipmentCategory) &&
  (!S.equipmentSelectedOnly||equipmentSelected(c.key))
);
const groups={};for(const c of catalog){(groups[c.category]??=[]).push(c)}
return `${onboarding?dots(3):'<p class=eyebrow>PROFILE</p>'}
<h2>${onboarding?"Build your equipment log":"Equipment Log"}</h2>
<p class=muted>Forge uses this log to choose exercises, substitutions, and AI Coach recommendations.</p>

<div class=big-spacer></div><p class=eyebrow>QUICK SETUP</p>
<div class=equipment-presets>
  <button data-equipment-preset=full_gym>Full Gym</button>
  <button data-equipment-preset=home_gym>Home Gym</button>
  <button data-equipment-preset=bodyweight>Bodyweight</button>
</div>

<div class=big-spacer></div>
<div class=equipment-log-toolbar>
  <input id=equipmentSearch class=equipment-search value="${esc(S.equipmentSearch)}" placeholder="Search equipment...">
  <button class="equipment-selected-toggle ${S.equipmentSelectedOnly?"active":""}" data-a=toggle-selected-equipment>${selected.length} Added</button>
</div>
<div class=equipment-category-chips>
  ${categories.map(c=>`<button class="${S.equipmentCategory===c?"active":""}" data-equipment-category="${esc(c)}">${esc(c)}</button>`).join("")}
</div>

<div class=big-spacer></div>
<div class=row><div><p class=eyebrow>YOUR EQUIPMENT</p><span class=muted>${selected.length} logged • ${S.equipmentCatalog.length} available</span></div><button class="btn dark compact" data-a=add-custom-equipment>+ Custom</button></div>

${!S.equipmentLoaded?'<div class=card><p class=muted>Loading equipment log...</p></div>':
Object.keys(groups).length?Object.entries(groups).map(([category,items])=>`<div class=equipment-log-group><h3>${esc(category)}</h3>
<div class=equipment-log-list>${items.map(c=>{const on=equipmentSelected(c.key),logged=S.equipmentLog.find(x=>x.key===c.key);const details=logged?.details||{};const detailCount=Object.values(details).filter(v=>v!==""&&v!==null&&v!==false).length;return `<div class="equipment-log-row-wrap ${on?"selected":""}">
<button class="equipment-log-row ${on?"selected":""}" data-equipment-key="${c.key}">
<span class=equipment-log-icon>${equipmentIcon(c.key,c.name,c.category)}</span><span><strong>${esc(c.name)}</strong><small>${on?(detailCount?`${detailCount} detail${detailCount===1?"":"s"} saved`:"In your equipment log"):"Tap to add"}</small></span><span class=equipment-log-check>${on?"✓":"+"}</span></button>
${on?`<button class=equipment-edit-btn data-equipment-edit="${c.key}" title="Edit details">Edit</button>`:""}
</div>`}).join("")}</div></div>`).join(""):`<div class=card><p class=muted>No equipment matches this filter.</p></div>`}

${selected.filter(x=>x.is_custom).length?`<div class=equipment-log-group><h3>Custom</h3><div class=equipment-log-list>${selected.filter(x=>x.is_custom).map(x=>`<div class="equipment-log-row-wrap selected"><button class="equipment-log-row selected" data-remove-custom="${esc(x.key)}"><span class=equipment-log-icon>${equipmentIcon(x.key,x.name,x.category)}</span><span><strong>${esc(x.name)}</strong><small>${esc(x.category||"Other")} • custom equipment</small></span><span class=equipment-log-check>×</span></button><button class=equipment-edit-btn data-equipment-edit="${esc(x.key)}">Edit</button></div>`).join("")}</div></div>`:""}

<div class=big-spacer></div>
<button class=btn data-a="${onboarding?"equipment-next":"equipment-save"}">${onboarding?"Save & Continue":"Save Equipment Log"}</button>`;
}
function equipment(){return equipmentLogView(true)}
function equipmentlog(){return equipmentLogView(false)}

function equipmentdetails(){
const item=S.equipmentLog.find(x=>x.key===S.equipmentEditKey);
if(!item)return `<h2>Equipment Details</h2><p class=muted>Equipment not found.</p>`;
const c=S.equipmentCatalog.find(x=>x.key===item.key);
const schema=c?.detail_schema||{};
const fields=Object.entries(schema);
return `<p class=eyebrow>EQUIPMENT DETAILS</p><h2>${esc(item.name)}</h2><p class=muted>Add useful limits or features so Forge can make better recommendations.</p>
<div class=big-spacer></div>
<div class=equipment-detail-form>
${fields.length?fields.map(([key,type])=>{
  const label=key.replaceAll("_"," ").replace(/\b\w/g,m=>m.toUpperCase());
  const val=item.details?.[key];
  if(type==="boolean")return `<label class=equipment-bool><span>${esc(label)}</span><input type=checkbox data-equipment-detail="${key}" ${val?"checked":""}></label>`;
  return `<label class=field>${esc(label)}<input type=number step=any min=0 data-equipment-detail="${key}" value="${val??""}" placeholder="Optional"></label>`;
}).join(""):`<div class=card><p class=muted>No structured fields are required for this item.</p></div>`}
<label class=field>Notes<input id=equipmentNotes value="${esc(item.details?.notes||"")}" placeholder="Optional notes"></label>
</div>
<div class=big-spacer></div><button class=btn data-a=equipment-detail-save>Save Details</button>`;
}

async function loadExerciseDirectory(){
  if(!authToken)return;
  const params=new URLSearchParams();
  if(S.exerciseDirectorySearch)params.set("search",S.exerciseDirectorySearch);
  if(S.exerciseDirectoryMuscle!=="All")params.set("muscle",S.exerciseDirectoryMuscle);
  if(S.exerciseDirectoryDifficulty!=="All")params.set("difficulty",S.exerciseDirectoryDifficulty);
  if(S.exerciseDirectoryEquipment!=="All")params.set("equipment",S.exerciseDirectoryEquipment);
  if(S.exerciseDirectoryMovement!=="All")params.set("movement",S.exerciseDirectoryMovement);
  if(S.exerciseDirectoryCompatible)params.set("compatible_only","true");
  params.set("limit","300");
  try{
    S.exerciseDirectory=await api(`/me/exercises?${params.toString()}`);
    if(S.route==="exercisedirectory")render();
  }catch(e){toast(e.message)}
}

function exercisedirectory(){
const d=S.exerciseDirectory,allRows=d?.exercises||[],rows=S.exerciseDirectoryFavorites?allRows.filter(x=>x.user_preference==="favorite"):allRows,filters=d?.filters||{};
return `<p class=eyebrow>LIBRARY</p><div class=row><div><h2>Expanded Exercise Directory</h2><p class=muted>${d?`${d.directory_total} exercises available`:"Loading exercises..."}</p></div><span>▤</span></div>
<div class=big-spacer></div>
<input id=exerciseDirectorySearch class=directory-search value="${esc(S.exerciseDirectorySearch)}" placeholder="Search exercises, muscles, equipment...">
<div class=directory-filter-row>
<select id=directoryMuscle><option>All</option>${(filters.muscles||[]).map(x=>`<option ${S.exerciseDirectoryMuscle===x?"selected":""}>${esc(x)}</option>`).join("")}</select>
<select id=directoryDifficulty><option>All</option>${(filters.difficulties||[]).map(x=>`<option ${S.exerciseDirectoryDifficulty===x?"selected":""}>${esc(x)}</option>`).join("")}</select>
<select id=directoryEquipment><option>All</option>${(filters.equipment||[]).map(x=>`<option ${S.exerciseDirectoryEquipment===x?"selected":""}>${esc(x)}</option>`).join("")}</select>
<select id=directoryMovement><option>All</option>${(filters.movements||[]).map(x=>`<option ${S.exerciseDirectoryMovement===x?"selected":""}>${esc(x)}</option>`).join("")}</select>
<button class="${S.exerciseDirectoryFavorites?"active":""}" data-a=directory-favorites>★ Favorites</button>
<button class="${S.exerciseDirectoryCompatible?"active":""}" data-a=directory-compatible>${S.exerciseDirectoryCompatible?"My Equipment":"All Equipment"}</button>
</div>
<div class=spacer></div>
<p class=muted>${d?`${rows.length} matching exercise${rows.length===1?"":"s"}`:""}</p>
<div class=directory-list>${rows.map(e=>`<button class="directory-card ${e.equipment_compatible?"":"incompatible"}" data-directory-exercise=${e.id}>
<div class=row><div><p class=eyebrow>${esc(e.primary_muscle)}</p><h3>${esc(e.name)}</h3></div><span>›</span></div>
<p class=muted>${esc(e.equipment)} • ${esc(e.difficulty)} • ${e.min_reps}-${e.max_reps} reps</p>
<div class=directory-tags><span>${esc(e.movement_pattern)}</span><span>${esc(e.exercise_type)}</span>${e.beginner_suitable?"<span>Beginner Friendly</span>":""}${e.user_preference==="favorite"?"<span>★ Favorite</span>":e.user_preference==="avoid"?"<span>Avoid</span>":e.user_preference==="painful"?"<span>Painful</span>":""}</div>
</button>`).join("")||'<div class=card><p class=muted>No exercises match these filters.</p></div>'}</div>`;
}

async function cacheCurrentPlanDemos(silent=false){
  if(!("serviceWorker" in navigator)){if(!silent)toast("Offline demos are not supported in this browser");return}
  try{
    const data=await api("/me/exercise-demos/current-plan");
    const urls=(data.assets||[]).map(x=>x.url).filter(Boolean);
    const reg=await navigator.serviceWorker.ready;
    const target=reg.active||reg.waiting||reg.installing;
    if(!target)throw Error("Service worker is not ready");
    const channel=new MessageChannel();
    const result=new Promise((resolve,reject)=>{
      const timer=setTimeout(()=>reject(Error("Demo cache request timed out")),20000);
      channel.port1.onmessage=e=>{clearTimeout(timer);resolve(e.data||{})};
    });
    target.postMessage({type:"CACHE_DEMO_ASSETS",urls},[channel.port2]);
    const status=await result;
    S.demoOfflineStatus={...status,requested:urls.length};
    if(!silent)toast(urls.length?`${status.cached||0}/${urls.length} demos ready offline`:"Current plan has no animation assets yet");
    return S.demoOfflineStatus;
  }catch(e){S.demoOfflineStatus={error:e.message};if(!silent)toast(e.message)}
}
async function getDemoOfflineStatus(){
  if(!("serviceWorker" in navigator))return null;
  try{
    const reg=await navigator.serviceWorker.ready,target=reg.active||reg.waiting||reg.installing;
    if(!target)return null;
    const channel=new MessageChannel();
    const result=new Promise(resolve=>{const timer=setTimeout(()=>resolve(null),4000);channel.port1.onmessage=e=>{clearTimeout(timer);resolve(e.data||null)}});
    target.postMessage({type:"DEMO_CACHE_STATUS"},[channel.port2]);
    S.demoOfflineStatus=await result;return S.demoOfflineStatus;
  }catch{return null}
}
function exerciseDemoPlayer(demo){
 if(!demo)return `<div class="exercise-demo-player demo-placeholder"><strong>Loading 3D form guide…</strong></div>`;
 const reduced=window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)").matches;
 const td=demo.three_d||null;
 if(td&&td.ready&&td.primary_webm){
   const secondary=td.secondary_webm||null;
   const selected=(S.demoAngle==="secondary"&&secondary)?secondary:td.primary_webm;
   const viewName=(S.demoAngle==="secondary"&&secondary)?(td.secondary_view||"Front"):(td.primary_view||"Side");
   return `<div class="exercise-demo-player three-d-demo-player">
     <video src="${esc(selected)}" poster="${esc(td.poster_asset||"")}" ${reduced?"":"autoplay"} loop muted playsinline controls preload=metadata></video>
     <span class=demo-quality-badge>${td.status==="reviewed"?"3D • Reviewed":"3D • Asset Ready"}</span>
     ${secondary?`<div class=demo-angle-switch><button class="${S.demoAngle==="primary"?"active":""}" data-demo-angle=primary>${esc(td.primary_view||"Side")}</button><button class="${S.demoAngle==="secondary"?"active":""}" data-demo-angle=secondary>${esc(td.secondary_view||"Front")}</button></div>`:""}
     <small class=three-d-view-label>${esc(viewName)} view</small>
   </div>`;
 }
 return `<div class="exercise-demo-player demo-placeholder three-d-pending">
   <div class=three-d-pending-mark>3D</div>
   <strong>${esc(demo.name)}</strong>
   <small>High-quality 3D demo in production</small>
   <p>Forge has retired the SVG diagram for this exercise. Setup, form cues, breathing, and mistakes remain available while the 3D loop is produced and reviewed.</p>
 </div>`;
}
async function openFormDemo(id,ret="exercise"){S.formDemoExercise=Number(id);S.formDemoReturn=ret;S.formDemo=null;S.formDemoTab="demo";S.demoAngle="primary";go("formdemo");try{S.formDemo=await api(`/me/exercises/${id}/form-demo`);if(S.route==="formdemo")render()}catch(e){toast(e.message)}}
async function openDemoAudit(){
  S.demoAudit=null;go("demoaudit");
  try{const d=await api("/me/exercise-demos/audit");S.demoAudit=d.items||[];if(S.route==="demoaudit")render()}catch(e){toast(e.message)}
}
async function openDemoReview(id){
 const ready=(S.demoAudit||[]).filter(x=>x.has_3d&&!x.reviewed);
 S.demoReviewQueue=ready.map(x=>Number(x.id));
 S.demoReviewQueueIndex=Math.max(0,S.demoReviewQueue.indexOf(Number(id)));
 S.demoReviewExercise=Number(id);S.demoReview=null;go("demoreview");
 try{S.demoReview=await api(`/me/exercises/${id}/demo-review`);if(S.route==="demoreview")render()}catch(e){toast(e.message)}
}
async function moveDemoReviewQueue(delta){
 if(!S.demoReviewQueue.length)return;
 const next=Math.max(0,Math.min(S.demoReviewQueue.length-1,S.demoReviewQueueIndex+delta));
 if(next===S.demoReviewQueueIndex)return;
 S.demoReviewQueueIndex=next;S.demoReviewExercise=S.demoReviewQueue[next];S.demoReview=null;render();
 try{S.demoReview=await api(`/me/exercises/${S.demoReviewExercise}/demo-review`);render()}catch(e){toast(e.message)}
}
function demoreview(){
 const r=S.demoReview;if(!r)return `<p class=eyebrow>DEMO REVIEW</p><h2>Loading checklist…</h2>`;
 const auditItem=(S.demoAudit||[]).find(x=>Number(x.id)===Number(S.demoReviewExercise));
 const reviewPreview=auditItem?.demo_asset?`<div class=exercise-demo-player><img src="${esc(auditItem.demo_asset)}" alt="${esc(r.exercise_name)} review animation"></div><div class=spacer></div>`:"";
 const fields=[["correct_exercise","Correct exercise"],["setup","Setup & equipment"],["range_of_motion","Range of motion"],["joint_alignment","Joint alignment"],["loop_quality","Loop quality"],["mobile_tested","Tested on phone"]];
 return `<p class=eyebrow>DEMO REVIEW</p><h2>${esc(r.exercise_name)}</h2><p class=muted>Only mark items passed after checking the actual animation.</p>
 <div class=demo-review-queue-bar><button data-a=demo-review-prev ${S.demoReviewQueueIndex<=0?"disabled":""}>‹ Previous</button><span>${S.demoReviewQueue.length?`${S.demoReviewQueueIndex+1}/${S.demoReviewQueue.length}`:"Review"}</span><button data-a=demo-review-next ${S.demoReviewQueueIndex>=S.demoReviewQueue.length-1?"disabled":""}>Next ›</button></div>
 ${reviewPreview}<div class=card>${fields.map(([k,n])=>`<label class=demo-review-item><input type=checkbox data-demo-review="${k}" ${r[k]?"checked":""}><span><b>${n}</b><small>${r[k]?"Passed":"Needs review"}</small></span></label>`).join("")}</div>
 <div class=spacer></div><label class=field>Review notes<textarea data-demo-review-notes rows=4 placeholder="Record anything that should be corrected…">${esc(r.notes||"")}</textarea></label>
 <button class=btn data-a=save-demo-review>Save Review</button>
 ${r.complete?`<div class="card demo-reviewed-banner"><b>✓ Reviewed</b><p>All six checks passed. Forge can display this demo as reviewed.</p></div>`:`<p class="muted demo-review-warning">This demo remains Asset Ready until every check passes.</p>`}`;
}
function demoaudit(){
  const rows=S.demoAudit;
  if(!rows)return `<p class=eyebrow>DEMO LIBRARY</p><h2>Checking exercise coverage…</h2>`;
  const total=rows.length,animated=rows.filter(x=>x.has_animation).length,reviewed=rows.filter(x=>x.reviewed).length;
  return `<p class=eyebrow>EXERCISE DEMOS</p><h2>3D Demo Coverage</h2>
  ${rows.some(x=>x.has_3d&&!x.reviewed)?`<button class=btn data-a=start-demo-review-queue>Review Asset-Ready Queue</button><div class=spacer></div>`:""}
  <div class=demo-audit-stats><div><b>${animated}/${total}</b><span>3D Ready</span></div><div><b>${reviewed}/${total}</b><span>Reviewed</span></div><div><b>${total?Math.round(animated/total*100):0}%</b><span>Coverage</span></div></div>
  <div class=spacer></div><div class=demo-audit-list>${rows.map(x=>`<div class=demo-audit-row>
    <div><strong>${esc(x.name)}</strong><small>${esc(x.primary_muscle)} • ${esc(x.equipment)}</small></div>
    <span class="${x.reviewed?"ok":x.has_animation?"ready":"missing"}" ${x.has_3d?`data-demo-review-open="${x.id}"`:""}>${x.reviewed?"Reviewed":x.has_3d?"Review →":"Needs 3D demo"}</span>
  </div>`).join("")}</div>`;
}
function formdemo(){
 const d=S.formDemo;if(!d)return `<p class=eyebrow>FORM DEMO</p><h2>Loading exercise form…</h2>${exerciseDemoPlayer(null)}`;
 let body=S.formDemoTab==="setup"?`<div class=card><p class=eyebrow>SETUP</p>${d.setup_cues.map((x,i)=>`<div class=form-cue-row><b>${i+1}</b><span>${esc(x)}</span></div>`).join("")}</div>`:
 S.formDemoTab==="mistakes"?`<div class=card><p class=eyebrow>COMMON MISTAKES</p>${d.common_mistakes.map(x=>`<div class="form-cue-row mistake"><b>!</b><span>${esc(x)}</span></div>`).join("")}</div>`:
 `${exerciseDemoPlayer(d)}<div class=spacer></div><div class=card><p class=eyebrow>FORM CUES</p>${d.form_cues.map((x,i)=>`<div class=form-cue-row><b>${i+1}</b><span>${esc(x)}</span></div>`).join("")}</div>`;
 return `<p class=eyebrow>EXERCISE FORM</p><h2>${esc(d.name)}</h2><p class=muted>${esc(d.primary_muscle)} • ${esc(d.equipment)}</p><button class="form-demo-offline-btn" data-a=cache-plan-demos>↓ Make This Week's Demos Available Offline</button><button class="form-demo-audit-btn" data-a=open-demo-audit>View Demo Library Coverage</button><div class=form-demo-tabs>${[["demo","Demo"],["setup","Setup"],["mistakes","Mistakes"]].map(([v,n])=>`<button class="${S.formDemoTab===v?"active":""}" data-form-demo-tab="${v}">${n}</button>`).join("")}</div>${body}<div class=spacer></div><div class=card><p class=eyebrow>BREATHING</p><p>${esc(d.breathing_cue)}</p></div><div class=spacer></div><div class="card form-safety"><p class=eyebrow>CONTROL</p><p>${esc(d.safety_note)}</p></div>`;
}

async function loadSubstitutionIntelligence(){const ex=w()?.exercises?.[S.ei];if(!ex||S.substitutionIntelligence?.loading)return;S.substitutionIntelligence={loading:true};try{S.substitutionIntelligence=await api(`/me/exercises/${ex.exercise_id}/substitution-intelligence`);if(S.route==="swapexercise")render()}catch(e){S.substitutionIntelligence=null}}
function substitutionIntelligenceCard(){const d=S.substitutionIntelligence;if(!d?.options?.length)return "";return `<div class=card><p class=eyebrow>SUBSTITUTION INTELLIGENCE 2.0</p><h3>Best-fit replacements</h3><div class=sub-intel-list>${d.options.slice(0,5).map((x,i)=>`<div><b>${i+1}. ${esc(x.name)}</b><span>${x.submuscle_overlap_percent}% target overlap • ${x.progression_compatible?"similar":"different"} progression</span><small>${esc(x.explanation)}</small></div>`).join("")}</div></div>`}

function exercisedetail(){
const e=S.exerciseDirectorySelected;
if(!e)return `<h2>Exercise</h2><p class=muted>Select an exercise from the directory.</p>`;
const pref=e.user_preference||"neutral";
const lvl=n=>["","Low","Low","Moderate","High","Very High"][Math.max(1,Math.min(5,Number(n||1)))];
return `<p class=eyebrow>EXERCISE INTELLIGENCE</p><h2>${esc(e.name)}</h2><p class=muted>${esc(e.primary_muscle)} • ${esc(e.difficulty)}</p>
<div class=big-spacer></div>
<button class=exercise-directory-hero data-form-demo="${e.id}" data-form-return=exercisedetail><div class=form-demo-icon>▶</div><strong>Open Form Guide</strong><span>Technique • setup • common mistakes</span></button>
<div class=spacer></div>
<div class=exercise-directory-facts>
<div><small>Sets</small><b>${e.default_sets}</b></div>
<div><small>Rep Range</small><b>${e.min_reps}-${e.max_reps}</b></div>
<div><small>Fatigue</small><b>${lvl(e.fatigue_cost)}</b></div>
<div><small>Skill</small><b>${lvl(e.skill_demand)}</b></div>
</div>
<div class=big-spacer></div>
<div class=card><p class=eyebrow>FORGE RATING</p>
<div class=settings-status-row><span>Hypertrophy</span><b>${e.hypertrophy_score}/5</b></div>
<div class=settings-status-row><span>Strength</span><b>${e.strength_score}/5</b></div>
<div class=settings-status-row><span>Stability demand</span><b>${e.stability_demand}/5</b></div>
<div class=settings-status-row><span>Joint stress</span><b>${e.joint_stress}/5</b></div>
</div>
<div class=spacer></div>
<div class=card><p class=eyebrow>MY PREFERENCE</p><p class=muted>Forge uses this when generating and rebuilding your plan.</p>
<div class=chips>
<button class="chip ${pref==="favorite"?"selected":""}" data-exercise-pref=favorite>★ Favorite</button>
<button class="chip ${pref==="avoid"?"selected":""}" data-exercise-pref=avoid>Avoid</button>
<button class="chip ${pref==="painful"?"selected":""}" data-exercise-pref=painful>Painful</button>
<button class="chip ${pref==="neutral"?"selected":""}" data-exercise-pref=neutral>Neutral</button>
</div></div>
<div class=spacer></div>
<div class=card><p class=eyebrow>DETAILED MUSCLE TARGETS</p><h3>${esc(e.primary_muscle)}</h3><p class=muted>${e.secondary_muscles?`Also works: ${esc(e.secondary_muscles)}`:"Primary target exercise"}</p>${(e.muscle_links||[]).length?`<div class=directory-tags style="margin-top:10px">${e.muscle_links.map(x=>`<span>${esc(x.sub_muscle)} • ${x.role}</span>`).join("")}</div>`:""}</div>
<div class=spacer></div>
<div class=card><p class=eyebrow>MOVEMENT</p><h3>${esc(e.movement_pattern)}</h3><p class=muted>${esc(e.equipment)} • ${esc(e.progression_method)}</p>${e.notes?`<p class=muted>${esc(e.notes)}</p>`:""}</div>
<div class=big-spacer></div>${w()?`<button class=btn data-a=directory-add-current>Add to ${esc(w().name)}</button><div class=spacer></div>`:""}<button class="btn dark" data-a=directory-history>View My History</button>`;
}

const exerciseNames=["Bench Press","Squats","Deadlifts","Pull Ups","Overhead Press","Rows","Lunges","Leg Press","Dips","Bicep Curls","Tricep Pushdowns","Hip Thrusts"];
function preferences(){
return `${dots(4)}<h2>Any preferences?</h2><p class=muted>Help us customize your plan.</p><div class=big-spacer></div><div class=preference-list>
<button class=pref-row data-a=pref-avoid><span><strong>Avoid These Exercises</strong><small class=muted style="display:block">${profile.excluded_exercises.length} selected</small></span><span>›</span></button>
<button class=pref-row data-a=pref-focus><span><strong>Focus Areas</strong><small class=muted style="display:block">${profile.priority_muscles.length} selected</small></span><span>›</span></button>
<button class=pref-row data-a=pref-cardio-frequency><span><strong>Cardio Training</strong><small class=muted style="display:block">${cardioFrequencyLabel(profile.cardio_workouts_per_week)}</small></span><span>›</span></button>
<button class=pref-row data-a=pref-cardio-intensity><span><strong>Cardio Intensity</strong><small class=muted style="display:block">${cardioLabel(profile.cardio_preference)}</small></span><span>›</span></button>
<button class=pref-row data-a=pref-split><span><strong>Workout Split</strong><small class=muted style="display:block">${splitLabel(profile.workout_split)}</small></span><span>›</span></button>
<button class=pref-row data-a=pref-sport><span><strong>Sport</strong><small class=muted style="display:block">${sportLabel(profile.sport)}</small></span><span>›</span></button>
<button class=pref-row data-a=pref-core><span><strong>Core Training</strong><small class=muted style="display:block">${coreFrequencyLabel(profile.core_workouts_per_week)}</small></span><span>›</span></button>
</div><div class=big-spacer></div><button class=btn data-a=generate>Next</button>`;
}
function coreFrequencyLabel(v){
  const n=Math.max(0,Math.min(Number(v||0),Number(profile.days_per_week||0)));
  return n===0?"No Direct Core":n===1?"1 workout / week":`${n} workouts / week`;
}
function corepicker(){
  const max=Number(profile.days_per_week||4);
  const values=Array.from({length:max+1},(_,i)=>i);
  return `<p class=eyebrow>CORE TRAINING</p><h2>How often do you want direct core work?</h2>
  <p class=muted>Core training will be added to your regular workouts instead of becoming its own training day.</p>
  <div class=big-spacer></div><div class=preference-list>
  ${values.map(v=>`<button class="pref-row ${Number(profile.core_workouts_per_week)===v?"selected":""}" data-core-frequency="${v}">
    <span><strong>${v===0?"No Direct Core":v===1?"1 Core Add-On":`${v} Core Add-Ons`}</strong>
    <small class=muted style="display:block">${v===0?"No dedicated core exercises":v===1?"Added to 1 regular workout each week":`Spread across ${v} regular workouts each week`}</small></span>
    <span>${Number(profile.core_workouts_per_week)===v?"✓":"›"}</span></button>`).join("")}
  </div><div class=big-spacer></div><button class=btn data-a=pref-done>Done</button>`;
}
const SPORT_OPTIONS=[
["general","General Fitness","No sport-specific bias"],["football","Football","Power, strength, acceleration and contact resilience"],
["basketball","Basketball","Jumping, lower-body strength and repeated sprint ability"],["soccer","Soccer","Running capacity, legs, change of direction and durability"],
["baseball","Baseball","Rotational power, shoulders, back and lower body"],["hockey","Hockey","Leg strength, power, core and conditioning"],
["tennis","Tennis","Rotation, lateral movement, shoulder health and conditioning"],["volleyball","Volleyball","Jumping, shoulders, legs and core"],
["wrestling","Wrestling","Full-body strength, pulling, grip and conditioning"],["combat_sports","Combat Sports","Rotation, full-body power and conditioning"],
["track_sprint","Track / Sprinting","Posterior chain, power and sprint support"],["distance_running","Distance Running","Running durability, calves, hips and core"],
["swimming","Swimming","Lats, shoulders, upper back and core"],["lacrosse","Lacrosse","Power, rotation, running and shoulder strength"]];
function sportLabel(v){return (SPORT_OPTIONS.find(x=>x[0]===v)||SPORT_OPTIONS[0])[1]}
function sportpicker(){return `<p class=eyebrow>SPORT</p><h2>What are you training for?</h2><p class=muted>Forge will adjust exercise selection, training split, rep emphasis, and conditioning around your sport.</p><div class=big-spacer></div><div class=preference-list>${SPORT_OPTIONS.map(([v,n,d])=>`<button class="pref-row ${profile.sport===v?"selected":""}" data-sport="${v}"><span><strong>${n}</strong><small class=muted style="display:block">${d}</small></span><span>${profile.sport===v?"✓":"›"}</span></button>`).join("")}</div><div class=big-spacer></div><button class=btn data-a=pref-done>Done</button>`}
const CARDIO_OPTIONS=[["light","Light","10 min • Easy pace focused on recovery and aerobic base"],["moderate","Moderate","15 min • A balanced training pace"],["high","High","20 min • Harder conditioning with more interval work"],["extended","Intense","25+ min • Longer aerobic conditioning sessions"]];
const SPLIT_OPTIONS=[["auto","Forge Recommended","Automatically choose for your schedule"],["full_body","Full Body","Train the whole body each workout"],["upper_lower","Upper / Lower","Alternate upper- and lower-body days"],["push_pull_legs","Push / Pull / Legs","Separate pushing, pulling, and leg training"],["body_part","Body Part Split","Focus on fewer muscle groups each day"],["hybrid","Hybrid","Mix full-body and focused sessions"],["custom","Custom Split","Choose the muscle groups trained on each day"]];
const CUSTOM_SPLIT_MUSCLES=["Chest","Back","Shoulders","Biceps","Triceps","Quads","Hamstrings","Glutes","Calves","Core","Forearms"];
const MUSCLE_SUBSECTIONS={"Chest":["Upper Chest","Mid Chest","Lower Chest"],"Back":["Lats","Upper Back","Traps","Spinal Erectors"],"Shoulders":["Front Delts","Side Delts","Rear Delts"],"Biceps":["Biceps Long Head","Biceps Short Head","Brachialis"],"Triceps":["Triceps Long Head","Triceps Lateral/Medial Heads"],"Quads":["Rectus Femoris","Vastus Lateralis","Vastus Medialis"],"Hamstrings":["Biceps Femoris","Semitendinosus/Semimembranosus"],"Glutes":["Glute Max","Glute Med/Min","Adductors"],"Calves":["Gastrocnemius","Soleus"],"Core":["Rectus Abdominis","Obliques","Deep Core","Hip Flexors"],"Forearms":["Wrist Flexors","Wrist Extensors","Grip"]};
function customDayName(muscles,i){return muscles?.length?muscles.join(" + "):`Custom Day ${i+1}`}
function ensureCustomSplit(){
  const days=Math.max(2,Math.min(6,Number(profile.days_per_week||4)));
  const existing=Array.isArray(profile.custom_split)?profile.custom_split:[];
  const defaults=[["Chest","Shoulders","Triceps"],["Back","Biceps"],["Quads","Hamstrings","Glutes","Calves"],["Chest","Back"],["Shoulders","Biceps","Triceps"],["Quads","Hamstrings","Glutes","Calves"]];
  profile.custom_split=Array.from({length:days},(_,i)=>{const muscles=Array.isArray(existing[i]?.muscles)&&existing[i].muscles.length?[...new Set(existing[i].muscles.filter(x=>CUSTOM_SPLIT_MUSCLES.includes(x)))]:defaults[i%defaults.length];const submuscles={};const oldSubs=existing[i]?.submuscles||{};for(const m of muscles){const allowed=MUSCLE_SUBSECTIONS[m]||[];const chosen=Array.isArray(oldSubs[m])?oldSubs[m].filter(x=>allowed.includes(x)):[];if(chosen.length)submuscles[m]=[...new Set(chosen)]}return {name:customDayName(muscles,i),muscles,submuscles}});
  profile.priority_muscles=[...new Set((profile.priority_muscles||[]).filter(x=>CUSTOM_SPLIT_MUSCLES.includes(x)))];
}
function customMuscleFrequency(m){ensureCustomSplit();return profile.custom_split.reduce((n,d)=>n+(d.muscles.includes(m)?1:0),0)}
function customSplitCalendarDays(){
  const defaults={2:[0,3],3:[0,2,4],4:[0,1,3,4],5:[0,1,2,4,5],6:[0,1,2,3,4,5]};
  const current=(plan?.workouts||[]).filter(w=>Number.isFinite(Number(w.scheduled_day))).sort((a,b)=>(a.workout_index??0)-(b.workout_index??0)).map(w=>Number(w.scheduled_day));
  const preferred=(S.preferredDays||[]).length===Number(profile.days_per_week)?[...S.preferredDays].sort((a,b)=>a-b):[];
  return preferred.length?preferred:(current.length===Number(profile.days_per_week)?current:(defaults[Number(profile.days_per_week)]||[]));
}
function customSplitWeekday(i){return ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"][customSplitCalendarDays()[i]??i]||`Day ${i+1}`}
function customSplitInsights(){
  ensureCustomSplit();
  const major=["Chest","Back","Shoulders","Quads","Hamstrings","Glutes"],warnings=[];
  const frequency=Object.fromEntries(CUSTOM_SPLIT_MUSCLES.map(m=>[m,customMuscleFrequency(m)]));
  const missing=major.filter(m=>frequency[m]===0);
  if(missing.length)warnings.push(`No weekly work assigned to ${missing.join(", ")}.`);
  for(const m of CUSTOM_SPLIT_MUSCLES){
    const idx=profile.custom_split.map((d,i)=>d.muscles.includes(m)?i:-1).filter(i=>i>=0);
    if(idx.some((v,j)=>j&&v-idx[j-1]===1))warnings.push(`${m} is assigned to back-to-back training sessions.`);
    if((profile.priority_muscles||[]).includes(m)&&frequency[m]===0)warnings.push(`${m} is marked high priority but is not assigned to a training day.`);
    else if((profile.priority_muscles||[]).includes(m)&&profile.days_per_week>=3&&frequency[m]<2)warnings.push(`${m} is high priority but only trained once weekly.`);
  }
  return {frequency,warnings:[...new Set(warnings)]};
}
function adjustCustomMuscleFrequency(m,delta){
  ensureCustomSplit();const current=[];profile.custom_split.forEach((d,i)=>{if(d.muscles.includes(m))current.push(i)});
  if(delta>0){
    if(current.length>=profile.custom_split.length){toast(`${m} is already trained every session`);return}
    const candidates=profile.custom_split.map((d,i)=>i).filter(i=>!current.includes(i));
    let best=candidates[0];
    if(current.length){best=candidates.sort((a,b)=>Math.min(...current.map(i=>Math.abs(b-i)))-Math.min(...current.map(i=>Math.abs(a-i)))||profile.custom_split[a].muscles.length-profile.custom_split[b].muscles.length)[0]}
    else best=candidates.sort((a,b)=>profile.custom_split[a].muscles.length-profile.custom_split[b].muscles.length)[0];
    profile.custom_split[best].muscles.push(m);profile.custom_split[best].name=customDayName(profile.custom_split[best].muscles,best);
  }else{
    if(!current.length)return;
    const removable=current.filter(i=>profile.custom_split[i].muscles.length>1);
    if(!removable.length){toast(`Keep at least one muscle group on each day`);return}
    const target=removable.sort((a,b)=>profile.custom_split[b].muscles.length-profile.custom_split[a].muscles.length)[0];
    profile.custom_split[target].muscles=profile.custom_split[target].muscles.filter(x=>x!==m);profile.custom_split[target].name=customDayName(profile.custom_split[target].muscles,target);
  }
}
function cardioLabel(v){return (CARDIO_OPTIONS.find(x=>x[0]===v)||CARDIO_OPTIONS[1])[1]}
function splitLabel(v){return (SPLIT_OPTIONS.find(x=>x[0]===v)||SPLIT_OPTIONS[0])[1]}
function cardioFrequencyLabel(v){
  const n=Math.max(0,Math.min(Number(v||0),Number(profile.days_per_week||0)));
  return n===0?"No Cardio":n===1?"1 workout / week":`${n} workouts / week`;
}
function cardiofrequencypicker(){
  const max=Number(profile.days_per_week||4);
  const values=Array.from({length:max+1},(_,i)=>i);
  return `<p class=eyebrow>CARDIO TRAINING</p><h2>How often do you want cardio?</h2>
  <p class=muted>Cardio will be added to your regular workouts instead of becoming a separate training day.</p>
  <div class=big-spacer></div><div class=preference-list>
  ${values.map(v=>`<button class="pref-row ${Number(profile.cardio_workouts_per_week)===v?"selected":""}" data-cardio-frequency="${v}">
    <span><strong>${v===0?"No Cardio":v===1?"1 Cardio Add-On":`${v} Cardio Add-Ons`}</strong>
    <small class=muted style="display:block">${v===0?"No dedicated cardio work":v===1?"Added to 1 regular workout each week":`Spread across ${v} regular workouts each week`}</small></span>
    <span>${Number(profile.cardio_workouts_per_week)===v?"✓":"›"}</span></button>`).join("")}
  </div><div class=big-spacer></div><button class=btn data-a=pref-done>Done</button>`;
}
function cardiopicker(){return `<p class=eyebrow>CARDIO INTENSITY</p><h2>How hard should cardio feel?</h2><p class=muted>This changes cardio duration and whether Forge favors steady-state or interval work.</p><div class=big-spacer></div><div class=preference-list>${CARDIO_OPTIONS.map(([v,n,d])=>`<button class="pref-row ${profile.cardio_preference===v?"selected":""}" data-cardio="${v}"><span><strong>${n}</strong><small class=muted style="display:block">${d}</small></span><span>${profile.cardio_preference===v?"✓":"›"}</span></button>`).join("")}</div><div class=big-spacer></div><button class=btn data-a=pref-done>Done</button>`}
function splitpicker(){return `<p class=eyebrow>WORKOUT SPLIT</p><h2>Choose your training split</h2><p class=muted>Forge rebuilds the whole plan when a saved split changes.</p><div class=big-spacer></div><div class=preference-list>${SPLIT_OPTIONS.map(([v,n,d])=>{const allowed=splitAllowed(v);return `<button class="pref-row ${profile.workout_split===v?"selected":""}" data-split="${v}" ${allowed?"":"disabled"}><span><strong>${n}</strong><small class=muted style="display:block">${allowed?d:"Requires at least 3 training days"}</small></span><span>${profile.workout_split===v?"✓":"›"}</span></button>`}).join("")}</div>${profile.workout_split==="custom"?`<div class=spacer></div><button class="btn dark" data-a=edit-custom-split>Configure Custom Days</button>`:""}<div class=big-spacer></div><button class=btn data-a=pref-done>Done</button>`}
function splitAllowed(v){if(v==="push_pull_legs")return profile.days_per_week>=3;return true}
function customsplit(){ensureCustomSplit();const intel=customSplitInsights();return `<p class=eyebrow>CUSTOM SPLIT 3.0</p><h2>Build a precise training week</h2><p class=muted>Keep the broad muscle groups, then optionally target specific sections inside each one. If no subsection is selected, Forge trains the whole muscle group.</p><div class=big-spacer></div><div class=card><p class=eyebrow>WEEKLY MUSCLE TARGETS</p><h3>Frequency & priority</h3><p class=muted>Use + / − to change weekly frequency. Priority increases selection and volume emphasis.</p>${CUSTOM_SPLIT_MUSCLES.map(m=>`<div class=row style="padding:10px 0;border-bottom:1px solid var(--border)"><div><strong>${m}</strong><small class=muted style="display:block">${intel.frequency[m]}× / week • ${(profile.priority_muscles||[]).includes(m)?"High priority":"Standard priority"}</small></div><div class=row style="gap:6px"><button class=chip data-custom-frequency="${m}:-1">−</button><button class="chip ${(profile.priority_muscles||[]).includes(m)?"selected":""}" data-custom-priority="${m}">Priority</button><button class=chip data-custom-frequency="${m}:1">+</button></div></div>`).join("")}</div><div class=spacer></div>${intel.warnings.length?`<div class=card><p class=eyebrow>PLAN CHECK</p><h3>${intel.warnings.length} item${intel.warnings.length===1?"":"s"} to review</h3>${intel.warnings.map(x=>`<p class=muted>• ${esc(x)}</p>`).join("")}</div><div class=spacer></div>`:`<div class=card><p class=eyebrow>PLAN CHECK</p><h3>Split looks balanced</h3><p class=muted>Major muscle coverage and recovery spacing look reasonable.</p></div><div class=spacer></div>`}${profile.custom_split.map((day,i)=>`<div class=card><div class=row><div><p class=eyebrow>${esc(customSplitWeekday(i))} • DAY ${i+1}</p><h3>${esc(customDayName(day.muscles,i))}</h3></div><span class=muted>${day.muscles.length} group${day.muscles.length===1?"":"s"}</span></div><div class=chips>${CUSTOM_SPLIT_MUSCLES.map(m=>`<button class="chip ${day.muscles.includes(m)?"selected":""}" data-custom-muscle="${i}:${m}">${m}</button>`).join("")}</div>${day.muscles.map(m=>`<div style="margin-top:12px"><small class=muted>${m} focus • ${(day.submuscles?.[m]||[]).length?"specific sections":"whole group"}</small><div class=chips style="margin-top:6px">${(MUSCLE_SUBSECTIONS[m]||[]).map(sub=>`<button class="chip ${(day.submuscles?.[m]||[]).includes(sub)?"selected":""}" data-custom-submuscle="${i}:${m}:${sub}">${sub}</button>`).join("")}</div></div>`).join("")}</div><div class=spacer></div>`).join("")}<button class=btn data-a=custom-split-done>Use Custom Split</button>`}
function preferencepicker(){
const avoid=S.prefMode==="avoid",vals=avoid?(S.exerciseDirectory?.exercises?.map(x=>x.name)||exerciseNames):["Chest","Back","Shoulders","Arms","Quads","Hamstrings","Glutes","Core"],arr=avoid?profile.excluded_exercises:profile.priority_muscles;
return `<p class=eyebrow>${avoid?"AVOID EXERCISES":"FOCUS AREAS"}</p><h2>${avoid?"Exercises to avoid":"Choose focus areas"}</h2><div class=big-spacer></div><div class=chips>${vals.map(x=>`<button class="chip ${arr.includes(x)?"selected":""}" data-prefpick="${x}">${x}</button>`).join("")}</div><div class=big-spacer></div><button class=btn data-a=pref-done>Done</button>`;
}

function generating(){
return `<div class=generating><div class=forge-loader></div><h2>Forging Your Plan</h2><p class=muted>Analyzing your answers...</p><div class=gen-list><div class=done>Building your program</div><div class=done>Optimizing exercises</div><div class=done>Personalizing progression</div><div class=current>Almost ready...</div></div></div>`;
}

function yourplan(){
const count=plan?.workouts?.length||profile.days_per_week;
return `<p class=eyebrow>YOUR PLAN IS READY!</p><h2>Your Plan is Ready!</h2><div class=big-spacer></div><div class=plan-summary><div class=center><div class=big>${count} Day</div><div class=muted>${plan?.workout_names?.slice(0,2).join(" • ")||plan?.split?.join(" / ")||"Personalized Training"}</div></div><div class=plan-facts><div class=plan-fact><b>${count}</b><small>Workouts / Week</small></div><div class=plan-fact><b>8 Weeks</b><small>Program Length</small></div><div class=plan-fact><b>${["Mon","Tue","Thu","Fri"].slice(0,count).join(", ")}</b><small>Training Days</small></div><div class=plan-fact><b>${profile.minutes_per_workout} min</b><small>Est. Time / Day</small></div></div></div><div class=big-spacer></div><button class=btn data-a=viewplan>View Plan</button><div class=spacer></div><button class="btn dark" data-a=gohome>Go to Home</button>`;
}

async function loadNotifications(){try{const d=await api("/me/notifications");S.notifications=d;S.notificationSettings=d.settings;if(["home","notifications"].includes(S.route))render()}catch(e){}}
function notificationCenter(){const d=S.notifications||{items:[]},items=d.items||[];return `<div class=row><div><p class=eyebrow>PROACTIVE COACHING</p><h2>Notifications</h2></div><span class=notification-count>${items.length}</span></div><p class=muted>Workout, nutrition, and calendar alerts from Forge Coach.</p><div class=spacer></div>${items.length?items.map(n=>`<div class="card notification-card ${n.priority}"><div><p class=eyebrow>${esc(n.type.replaceAll("_"," "))}</p><h3>${esc(n.title)}</h3><p class=muted>${esc(n.message)}</p>${n.action_prompt?`<button class="btn dark compact" data-notification-coach="${esc(n.action_prompt)}">Ask Coach</button>`:""}</div><button class=notification-dismiss data-notification-dismiss="${esc(n.key)}">×</button></div>`).join(""):`<div class=card><h3>You're caught up</h3><p class=muted>No proactive alerts right now.</p></div>`}<div class=big-spacer></div><div class=card><p class=eyebrow>SETTINGS</p><h3>Proactive Coaching</h3>${[["workout_reminders","Workout reminders"],["nutrition_reminders","Nutrition reminders"],["calendar_conflict_alerts","Calendar conflict alerts"],["morning_brief","Morning brief"]].map(([k,l])=>`<label class=notification-toggle><span>${l}</span><input type=checkbox data-notification-setting="${k}" ${S.notificationSettings?.[k]!==false?"checked":""}></label>`).join("")}<label class=notification-toggle><span>Reminder lead time</span><select id=notificationLead>${[[30,"30 min"],[60,"1 hour"],[90,"90 min"],[120,"2 hours"]].map(([v,l])=>`<option value=${v} ${Number(S.notificationSettings?.reminder_minutes_before||90)===v?"selected":""}>${l}</option>`).join("")}</select></label></div>`}

function forgeLocalDate(){
  const d=new Date();
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
}
async function loadHomeDashboard(){
  if(!authToken)return;
  try{
    const [nutrition,intelligence,history]=await Promise.all([
      api(`/me/nutrition?date=${encodeURIComponent(forgeLocalDate())}`),
      api("/me/progress/intelligence"),
      api("/me/history")
    ]);
    S.homeDashboard={nutrition,intelligence,history};
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
      ${allMuscles.length?allMuscles.map(([muscle,sets])=>`<div class=volume-row><span>${esc(muscle)}</span><b>${sets} sets</b><i><u style="width:${Math.round(sets/max*100)}%"></u></i></div>`).join(""):`<div class=polished-empty><b>Volume appears after your plan is built</b><span>Forge will summarize weekly set distribution here.</span></div>`}
    </div>
  </div>`;
}
function nutritionMealGroups(entries){
  const order=["Breakfast","Lunch","Dinner","Snack","Pre-Workout","Post-Workout","Meal"];
  const groups={};(entries||[]).forEach(x=>(groups[x.meal_type||"Meal"]??=[]).push(x));
  const keys=[...order.filter(k=>groups[k]),...Object.keys(groups).filter(k=>!order.includes(k))];
  if(!keys.length)return `<div class="card polished-empty"><b>Nothing logged yet</b><span>Log your first meal to start tracking today’s calories and macros.</span><button class="btn dark compact" data-a=nutrition-add>Log Food</button></div>`;
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
  return `<p class=eyebrow>15-SECOND CHECK-IN</p><h2>How ready are you today?</h2><p class=muted>Recovery Intelligence 2.0 combines this check-in with recent fatigue and today’s available time. It adapts the session without unnecessarily rewriting your training block.</p><div class=big-spacer></div>
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
  return `<div class="card today-adjustment ${tone}"><div class=row><div><p class=eyebrow>TODAY’S ADJUSTMENT</p><h3>${a.mode==="normal"?"Original session":a.mode==="recovery"?"Recovery-biased session":a.mode==="push"?"High-readiness session":"Controlled session"}</h3></div><b>${a.score}/5</b></div><p class=muted>${esc(a.reason)}</p>${a.proposed_changes?.length?`<div class=program-change-preview><p class=eyebrow>PROPOSED CHANGES — REVIEW BEFORE APPLYING</p>${a.proposed_changes.map(c=>`<div class=adaptation-note><span><b>${esc(c.area)}</b><small>${esc(c.reason)}</small></span><strong>${esc(c.proposed)}</strong></div>`).join("")}</div>`:""}<small>${esc(a.loadCue)}</small></div>`;
}


async function loadTrainingDashboard(){if(S.trainingDashboard?.loading)return;S.trainingDashboard={loading:true};try{S.trainingDashboard=await api("/me/training-dashboard");if(["home","progress"].includes(S.route))render()}catch(e){console.warn("Training dashboard failed",e)}}
function trainingDashboardCard(){const d=S.trainingDashboard;if(!d||d.loading)return `<div class=card><p class=eyebrow>TRAINING BLOCK</p><h3>Loading block intelligence…</h3></div>`;const m=d.mesocycle||{},top=(d.muscles||[]).slice(0,8);return `<div class="card training-command-card"><div class=row><div><p class=eyebrow>TRAINING DASHBOARD 3.0</p><h3>Block ${m.block_number} • Week ${m.week_in_block}/${m.block_length}</h3></div><b>${esc(String(m.phase||""))}</b></div><p class=muted>${d.week.completed}/${d.week.planned} workouts • ${d.week.adherence_percent}% complete • ${m.fatigue_score}/10 fatigue</p><div class=muscle-status-grid>${top.map(x=>`<div><span><b>${esc(x.muscle)}</b><small>${x.actual_sets}/${x.target_sets} effective sets</small></span><i><u style="width:${Math.min(100,x.percent)}%"></u></i></div>`).join("")}</div><div class=spacer></div><small>Current programming direction: <b>${esc(d.progression_mode)}</b></small></div>`}

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
  return `<div class="card weekly-insights-card"><div class=row><div><p class=eyebrow>WEEKLY INSIGHTS</p><h3>${done>=workouts.length&&workouts.length?"Week complete":"Your training at a glance"}</h3></div><button class="btn dark compact" data-nav=progress>Details</button></div>
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
      ?`<p class=eyebrow>WORKOUT COMPLETE</p><h2>${esc(todayWorkout.name)} finished</h2><p class=muted>Training is done for today. Recovery and nutrition are the next priority.</p><div class=spacer></div><div class=home-complete-badge>✓ Completed</div>`
      :`<p class=eyebrow>PRIMARY ACTION</p><h2>${esc(todayWorkout.name)}</h2><p class=muted>${todayWorkout.exercises.length} exercises • ${esc(todayWorkout.scheduled_time||S.timeSettings?.default_workout_time||"17:00")} • ${todayWorkout.estimated_minutes||profile.minutes_per_workout} min${todayWorkout.core_included?" • Core":""}</p><div class=spacer></div><button class="btn hero-start" data-a=startworkout>Start Today’s Workout</button>`}
${todayWorkout.core_module?`<div class=spacer></div><small>Core: ${todayWorkout.module_status?.core?.status==="completed"?"✓ Complete":"Scheduled"}</small>`:""}${todayWorkout.cardio_module?`<small>Cardio: ${todayWorkout.module_status?.cardio?.status==="completed"?"✓ Complete":"Scheduled"}</small>`:""}
  </div>
  <div class="workout-status-mark ${todayWorkout.status==="completed"?"done":""}">${todayWorkout.status==="completed"?"✓":"▶"}</div>
</div>`:`<div class="card hero-workout recovery-home"><div class=copy><p class=eyebrow>RECOVERY DAY</p><h2>No workout scheduled today</h2><p class=muted>Recover, stay on top of nutrition, or ask Forge Coach to move a workout here.</p><div class=spacer></div><button class="btn dark" data-coach-route=coach>Ask Forge Coach</button></div></div>`;
return `<div class=row><div><p class=muted>Welcome back,</p><h2>${esc(S.name)}!</h2></div><button class=notification-bell data-a=open-notifications>🔔${S.notifications?.unread_count?`<b>${S.notifications.unread_count}</b>`:""}</button></div>
<div class=spacer></div><div class=row><p class=eyebrow>TODAY</p><small class=muted>${new Date().toLocaleDateString([], {weekday:"long",month:"short",day:"numeric"})}</small></div>
<div class=spacer></div>${card}
<div class=spacer></div>
<div class=home-dashboard-grid>
  <button class="home-mini-card readiness-${readiness.tone}" data-coach-route=coach><span class=readiness-dot></span><span><small>READINESS</small><b>${readiness.label}</b><em>${esc(readiness.detail)}</em></span></button>
  ${homeNutritionSnapshot()}
</div>
<div class=spacer></div>${homeQuickActions(todayWorkout)}
${S.notifications?.items?.length?`<div class=spacer></div><div class="card proactive-home-card"><div class=row><div><p class=eyebrow>FORGE COACH</p><h3>${esc(S.notifications.items[0].title)}</h3></div><button class="btn dark compact" data-a=open-notifications>View</button></div><p class=muted>${esc(S.notifications.items[0].message)}</p></div>`:""}
<div class=big-spacer></div>${trainingDashboardCard()}<div class=big-spacer></div>${weeklyInsightsCard()}<div class=big-spacer></div><div class=row><h3>This Week</h3><div class=home-progress-ring style="background:conic-gradient(var(--red) 0 ${pct}%,#20252b ${pct}% 100%)"><b>${pct}%</b></div></div>
<div class=spacer></div><div class=week-strip>${dayNames.map((d,i)=>{
  const ww=workouts.find(w=>Number(w.scheduled_day)===i&&!w.is_skipped);
  const completed=ww?.status==="completed";
  return `<div class="day-dot ${completed?"done":i===today?"today":""}">${d}<b>${completed?"✓":ww?(i===today?"▶":"•"):"—"}</b></div>`;
}).join("")}</div>
<div class=big-spacer></div><div class=row><h3>Coming Up</h3><button class="text-action" data-nav=plan>Full plan</button></div><div class=spacer></div>
${upcoming.length?`<div class=upcoming-list>${upcoming.map(x=>`<button class=upcoming-workout data-w=${workouts.indexOf(x)}><span><small>${esc(x.scheduled_day_name||"Upcoming")} • ${esc(x.scheduled_time||S.timeSettings?.default_workout_time||"17:00")}</small><b>${esc(x.name)}</b></span><em>${x.estimated_minutes||profile.minutes_per_workout} min</em></button>`).join("")}</div>`:`<div class=polished-empty><b>No more workouts scheduled this week</b><span>Finish strong, recover, and your next training week will be ready.</span></div>`}
<div class=spacer></div><div class=home-completion-summary><div class=home-completion-count><strong>${done}/${workouts.length}</strong><span class=muted>Workouts Completed</span></div>
<div class=home-completed-list>${done?workouts.filter(w=>w.status==="completed").map(w=>`<div class=home-completed-workout><span class=completed-check>✓</span><span><strong>${esc(w.name)}</strong><small>${esc(w.scheduled_day_name||"Completed")}</small></span></div>`).join(""):`<div class=polished-empty compact-empty><b>Your completed workouts will appear here</b><span>Complete the first session to start building your consistency history.</span></div>`}</div></div>`;
}
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
return `${todayAdjustmentBanner()}<div class=workout-head><div><p class=eyebrow>${session?"WORKOUT IN PROGRESS":"TODAY'S SESSION"}</p><h2>${esc(ww.name)}</h2><p class=muted>${ww.exercises.length} exercises • ${ww.estimated_minutes||profile.minutes_per_workout} min${ww.execution_summary?` • ${ww.execution_summary.warmup_sets} warm-up sets`:""}</p></div><span class=workout-percent>${workoutPct}%${session?`<small style="display:block">~${remainingMinutes} min left</small>`:""}</span></div>
<div class=workout-progress-track><i style="width:${workoutPct}%"></i></div>
${session&&current?`<div class="card active-exercise-card"><div class=row><div><small>CURRENT EXERCISE</small><h2>${esc(current.name)}</h2><p>${current.sets} sets • ${current.min_reps}-${current.max_reps} reps • ${current.rest_seconds||60}s rest</p></div><span class=active-set-badge>Set ${S.set+1}</span></div><button class=btn data-a=openexercise>Continue Logging</button></div>`:""}
<div class=section-heading><div><p class=eyebrow>EXERCISE LIST</p><h3>${session?"Session roadmap":"What you’ll do"}</h3></div></div>
<div class=exercise-list>${ww.exercises.map((e,i)=>`<button class="exercise-item ${i===S.ei?"selected":""} ${session&&i<S.ei?"exercise-done":""}" data-ex=${i}><span class=exercise-num>${session&&i<S.ei?"✓":i+1}</span><span><strong>${esc(e.name)}</strong><small>${e.sets} working sets • ${e.min_reps}-${e.max_reps} reps • ${e.primary_muscle||"Strength"}${e.superset_group?` • Superset ${esc(e.superset_group)}`:""}</small></span><span>›</span></button>`).join("")}</div>
${coreModuleCard(ww)}${cardioModuleCard(ww)}
<div class=big-spacer></div>${session?`<button class="btn dark" data-a=abandon>End Workout Early</button>`:`<button class=btn data-a=startworkout>Start Workout</button><div class=spacer></div><button class="btn dark" data-a=workout-builder>Edit Workout</button>`}`;
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

async function loadExerciseProgression(){const ex=w()?.exercises?.[S.ei];if(!ex)return;const exerciseId=Number(ex.exercise_id);if(S.exerciseProgressionExerciseId===exerciseId&&(S.exerciseProgression||S.exerciseProgressionLoading))return;if(S.exerciseProgressionLoading)return;S.exerciseProgressionLoading=true;S.exerciseProgressionExerciseId=exerciseId;S.exerciseProgression=null;try{const data=await api(`/me/exercises/${exerciseId}/progression-strategy`);if(S.exerciseProgressionExerciseId!==exerciseId)return;S.exerciseProgression=data;if(S.route==="exercise"&&Number(w()?.exercises?.[S.ei]?.exercise_id)===exerciseId)render()}catch(e){if(S.exerciseProgressionExerciseId===exerciseId)S.exerciseProgression=null}finally{if(S.exerciseProgressionExerciseId===exerciseId)S.exerciseProgressionLoading=false}}
function exerciseProgressionCard(){const p=S.exerciseProgression;if(!p||p.loading)return "";return `<div class="card progression-card"><div class=row><div><p class=eyebrow>PROGRESSION ENGINE 3.0</p><h3>${esc(p.method)}</h3></div><b>${esc(p.status)}</b></div><p>${esc(p.target_rule)}</p><small>${esc(p.reason)}</small><div class=progression-metrics><span><b>${p.sessions_analyzed}</b><small>sessions</small></span><span><b>${p.avg_rpe??"—"}</b><small>avg RPE</small></span><span><b>${p.strength_change_percent==null?"—":`${p.strength_change_percent>0?"+":""}${p.strength_change_percent}%`}</b><small>strength</small></span></div></div>`}

function exercise(){
const e=w().exercises[S.ei],setPct=Math.round((S.set)/Math.max(1,e.sets)*100),timed=isTimedExercise(e),bodyweight=isBodyweightExercise(e);
if(timed&&!S.exerciseTimerTarget)S.exerciseTimerTarget=Math.max(5,Math.round((Number(e.min_reps||20)+Number(e.max_reps||60))/2));
const target=timed?`${S.exerciseTimerTarget} sec`:`${e.min_reps}-${e.max_reps} reps`;
const clock=`${String(Math.floor(S.exerciseElapsed/60)).padStart(2,"0")}:${String(S.exerciseElapsed%60).padStart(2,"0")}`;
return `${exerciseProgressionCard()}<div class=spacer></div><div class=exercise-session-top><div><p class=eyebrow>${esc(w().name)}</p><h2>${esc(e.name)}</h2><p class=muted>Set ${S.set+1} of ${e.sets} • Target ${target}</p><div class=set-adjuster><button type=button data-setchange=-1 aria-label="Remove a set">−</button><span><b>${e.sets}</b><small>planned sets</small></span><button type=button data-setchange=1 aria-label="Add a set">+</button></div></div><span class=set-progress-pill>${setPct}%</span></div>
<div class=workout-progress-track><i style="width:${setPct}%"></i></div>
${e.warmup_sets?.length?`<div class="card warmup-card"><p class=eyebrow>WARM-UP SETS</p><h3>${e.warmup_sets.length} ramp-up sets before working weight</h3><p class=muted>${e.warmup_sets.map(x=>`${x.percent}% × ${x.reps}`).join(" • ")} • Warm-ups are not counted as working sets.</p></div><div class=spacer></div>`:""}<div class=spacer></div><button class=form-demo-workout-button data-form-demo="${e.exercise_id}" data-form-return=exercise><span class=form-demo-play>▶</span><span><b>Form Demo</b><small>Technique • setup • common mistakes</small></span><i>›</i></button><div class=spacer></div><div id=recallCard class="card previous-performance-card">${exerciseRecallMarkup(e)}</div>
<div class=big-spacer></div>${S.liveAdjustment?`<div class="card live-adjustment"><p class=eyebrow>LIVE ADJUSTMENT</p><h3>${esc(S.liveAdjustment.title)}</h3><p class=muted>${esc(S.liveAdjustment.detail)}</p></div><div class=spacer></div>`:""}
<div class=log-panel><div class=log-panel-head><h3>Log Set ${S.set+1}</h3><span>${e.rest_seconds||60}s rest after</span></div>
${timed?`
<div class="card timed-exercise-card"><p class=eyebrow>TIMED SET</p><div id=exerciseClock class=timer-big>${clock}</div>
<p class=muted>Target ${target}. Adjust the target, then start when you begin the hold.</p>
<div class=set-adjuster timed-target-adjuster><button type=button data-timer-target=-5 aria-label="Reduce target five seconds">−5s</button><span><b>${S.exerciseTimerTarget}s</b><small>target time</small></span><button type=button data-timer-target=5 aria-label="Add five seconds">+5s</button></div>
<div class=exercise-actions><button class="btn ${S.exerciseTimerRunning?"dark":""}" data-a=exercise-timer-toggle>${S.exerciseTimerRunning?"Pause":"Start Timer"}</button><button class="btn dark" data-a=exercise-timer-reset>Reset</button></div></div>
<input id=durationSeconds type=hidden value="${S.exerciseElapsed}">
`:`
<div class=logging-grid>
${bodyweight?`<div class=logging-row><label for=loadMode>Load</label><select class=log-input id=loadMode><option value=bodyweight selected>Bodyweight</option><option value=weight>Added Weight</option></select></div>
<div class=logging-row id=addedWeightRow style="display:none"><label for=weight>Added Weight <small>lb</small></label><input class=log-input id=weight type=number inputmode=decimal min=0 step=2.5 placeholder="0" autocomplete=off></div>`:
`<div class=logging-row><label for=weight>Weight <small>lb</small></label><input class=log-input id=weight type=number inputmode=decimal min=0 step=2.5 placeholder="0" autocomplete=off></div>`}
<div class=logging-row><label for=reps>Reps</label><input class=log-input id=reps type=number inputmode=numeric min=1 step=1 value="${e.min_reps}" autocomplete=off></div>
</div>`}
<div class=effort-section><div class=effort-heading><strong>Effort / RIR</strong><small>${timed?"How hard was the hold?":"How many good reps were left?"}</small></div>
<div class=effort-options>
<button type=button class=effort-choice data-rpe=6><b>Easy</b><small>4+ left</small></button>
<button type=button class="effort-choice selected" data-rpe=7><b>Moderate</b><small>~3 left</small></button>
<button type=button class=effort-choice data-rpe=8><b>Hard</b><small>~2 left</small></button>
<button type=button class=effort-choice data-rpe=9><b>Very Hard</b><small>~1 left</small></button>
<button type=button class=effort-choice data-rpe=10><b>Limit</b><small>0 left</small></button>
</div><input id=rpe type=hidden value="7"></div>
<div class=exercise-actions><button class=btn data-a=completeset>Complete ${timed?"Timed Set":"Set"}</button><button class="btn dark" data-a=swap-exercise>Swap Exercise</button><button class="text-action skip-set-action" data-a=skip-set>Skip this set</button></div></div>`;
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
  <div class="card sequential-core-complete"><div class=completion-check>✓</div><h3>All ${total} sets complete</h3><p class=muted>Your reps, hold times, and effort are saved. Finish the circuit to store this session for progression.</p></div>
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
  <div class=effort-section><div class=effort-heading><strong>Effort / RIR</strong><small>${timed?"How hard was the hold?":"How many good reps were left?"}</small></div><div class=effort-options>${effortChoiceHTML(effort,"core",key)}</div><input data-core-rpe="${key}" type=hidden value="${effort}"></div>
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
<div class=effort-section><div class=effort-heading><strong>Effort / RIR</strong><small>How hard did the session feel?</small></div><div class=effort-options>${effortChoiceHTML(effort,"cardio")}</div><input id=cardioRpe type=hidden value="${effort}"></div>
</div><div class=big-spacer></div><button class=btn data-a=complete-cardio-module>Complete Cardio</button>`;
}
function timer(){
const t=S.restRemaining||w().exercises[S.ei].rest_seconds||60,mm=String(Math.floor(t/60)).padStart(2,"0"),ss=String(t%60).padStart(2,"0"),e=w().exercises[S.ei];
return `<div class=center><p class=eyebrow>RECOVERY BETWEEN SETS</p><h2>Rest Timer</h2><p class=muted>Next: ${esc(e.name)} • Set ${S.set+1} of ${e.sets}</p><div class=ring><div><strong id=restClock>${mm}:${ss}</strong><span class=muted>Remaining</span></div></div><div class=timer-actions><button data-addrest=30>+30s</button><button data-addrest=60>+1m</button><button data-a=skiprest>Skip</button></div><div class=big-spacer></div><button class=btn data-a=skiprest>Start Next Set</button><div class=spacer></div><button class="btn dark" data-a=view-workout-rest>View Workout While Resting</button></div>`;
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
function cardioswap(){
const ww=w();
return `<p class=eyebrow>SWAP CARDIO</p><h2>Choose Cardio Exercise</h2>
<p class=muted>Only cardio options that work with your Equipment Log are shown.</p>
<div class=spacer></div><div id=cardioSwapList class=stack><div class=card><p class=muted>Loading cardio options…</p></div></div>
<div class=big-spacer></div><div class=row><button class="btn dark" style="width:48%" data-a=cancel-cardio-swap>Cancel</button><button class=btn style="width:48%" data-a=apply-cardio-swap>Swap</button></div>`;
}
async function loadCardioSwapOptions(){
  try{
    const rows=await api("/me/cardio/options");
    S.cardioSwapOptions=rows.filter(x=>x.equipment_compatible);
    S.selectedCardioSwap=null;
    const el=document.querySelector("#cardioSwapList");if(!el)return;
    if(!S.cardioSwapOptions.length){el.innerHTML=`<div class=card><p class=muted>No compatible cardio options found for your equipment.</p></div>`;return}
    el.innerHTML=S.cardioSwapOptions.map(x=>`<button class="card swap-option ${x.name===w()?.cardio_module?.name?"selected":""}" data-cardio-swap=${x.id}>
      <div class=row><div><p class=eyebrow>${esc(x.movement_pattern)}</p><h3>${esc(x.name)}</h3><p class=muted>${esc(x.equipment)}</p></div><span>${x.name===w()?.cardio_module?.name?"Current":"›"}</span></div>
    </button>`).join("");
    document.querySelectorAll("[data-cardio-swap]").forEach(b=>b.onclick=()=>{S.selectedCardioSwap=Number(b.dataset.cardioSwap);document.querySelectorAll("[data-cardio-swap]").forEach(x=>x.classList.toggle("selected",x===b))});
  }catch(e){toast(e.message)}
}
async function applyCardioSwap(){
  if(!S.selectedCardioSwap){toast("Choose a cardio exercise");return}
  await api(`/me/workouts/${w().workout_id}/cardio/swap`,{method:"POST",body:JSON.stringify({new_exercise_id:S.selectedCardioSwap})});
  plan=await api("/me/plan/current");S.adaptationPreview=null;
  toast("Cardio swapped");
  go("workout");
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
return `${substitutionIntelligenceCard()}<div class=spacer></div><p class=eyebrow>SMART SUBSTITUTION</p><h2>Swap ${esc(e?.name||"Exercise")}</h2><p class=muted>Tell Forge why you’re swapping so the best matches rise to the top.</p><div class=swap-reason-grid>${reasons.map(([k,l])=>`<button class="${S.swapReason===k?"selected":""}" data-swap-reason="${k}">${l}</button>`).join("")}</div><div class=spacer></div><input class=swap-search placeholder="Search alternatives"><div class=row><p class=eyebrow>BEST MATCHES</p><small class=muted>ranked for this reason</small></div><div class=spacer></div><div id=swapList class=stack><div class=card><p class=muted>Loading substitutions…</p></div></div><div class=big-spacer></div>${S.swapReason==="discomfort"?`<div class="card pain-swap-note"><b>Discomfort swap</b><span>Forge will mark the current exercise as painful so it is strongly deprioritized in future substitutions. This is not a diagnosis; stop the movement if it causes pain.</span></div><div class=spacer></div>`:""}<div class=row><button class="btn dark" style="width:48%" data-a=back-exercise>Cancel</button><button class=btn style="width:48%" data-a=swap-selected>Swap</button></div>`;
}

async function loadSwapOptions(){
  try{
    const e=w()?.exercises?.[S.ei];if(!e)return;
    const rows=await api(`/me/exercises/${e.exercise_id}/substitutions`);
    const bonus=x=>{
      const fatigue=Number(x.fatigue_cost||3),skill=Number(x.skill_demand||3);
      if(S.swapReason==="discomfort")return (6-fatigue)*8+(6-skill)*3+(/machine|cable/i.test(x.equipment||"")?10:0);
      if(S.swapReason==="too_hard")return (6-fatigue)*7+(6-skill)*5;
      if(S.swapReason==="equipment")return x.equipment_compatible?40:-200;
      if(S.swapReason==="variety")return x.movement_pattern===e.movement_pattern?5:12;
      return 0;
    };
    S.swapOptions=[...rows].sort((a,b)=>(Number(b.substitution_score||0)+bonus(b))-(Number(a.substitution_score||0)+bonus(a)));S.selectedSwap=null;
    const el=document.querySelector("#swapList");if(!el)return;
    const compatible=S.swapOptions.filter(x=>x.equipment_compatible&&x.user_preference!=="painful");
    if(!compatible.length){el.innerHTML=`<div class=card><p class=muted>No compatible substitutions found for your equipment and preferences.</p></div>`;return}
    el.innerHTML=compatible.map((x,i)=>`<button class="card swap-option smart-swap-option" data-swap=${x.id}>
      <div class=row><div><p class=eyebrow>${i===0?"BEST MATCH":esc(x.primary_muscle)}</p><h3>${esc(x.name)}</h3>
      <p class=muted>${esc(x.equipment)} • ${x.min_reps}-${x.max_reps} reps</p><div class=swap-match-tags><span>${esc(x.smart_reason||"similar movement")}</span>${x.user_preference==="favorite"?"<span>★ Favorite</span>":""}</div></div><div class=swap-score><b>${Math.max(0,Math.round(Number(x.substitution_score||0)+bonus(x)))}</b><small>match</small></div></div></button>`).join("");
    document.querySelectorAll("[data-swap]").forEach(b=>b.onclick=()=>{S.selectedSwap=Number(b.dataset.swap);document.querySelectorAll("[data-swap]").forEach(x=>x.classList.toggle("selected",x===b))});
  }catch(e){toast(e.message)}
}

async function applySwap(newId){
  const old=w().exercises[S.ei];
  await api(`/me/workouts/${w().workout_id}/swap`,{method:"POST",body:JSON.stringify({
    old_exercise_id:old.exercise_id,new_exercise_id:newId
  })});
  if(S.swapReason==="discomfort"){try{await api(`/me/exercises/${old.exercise_id}/preference`,{method:"PUT",body:JSON.stringify({preference:"painful",notes:"Marked during workout substitution due to discomfort"})})}catch(e){console.warn("Pain preference save failed",e)}}
  plan=await api("/me/plan/current");S.adaptationPreview=null;
  toast(S.swapReason==="discomfort"?"Exercise swapped and painful movement deprioritized":"Exercise swapped");S.swapReason="preference";
  go("exercise");
}

function timer(){
const t=S.restRemaining||w().exercises[S.ei].rest_seconds||60,mm=String(Math.floor(t/60)).padStart(2,"0"),ss=String(t%60).padStart(2,"0"),e=w().exercises[S.ei];
return `<div class=center><h2>Rest Timer</h2><p class=muted>Next Set<br>${esc(e.name)}<br>Set ${S.set+1} of ${e.sets}</p><div class=ring><div><strong id=restClock>${mm}:${ss}</strong><span class=muted>Remaining</span></div></div><div class=timer-actions><button data-addrest=30>+30s</button><button data-addrest=60>+1m</button><button data-a=skiprest>Skip</button></div><div class=big-spacer></div><button class=btn data-a=skiprest>End Rest</button></div>`;
}

function complete(){
const prs=S.workoutPRs||[],unique=[],seen=new Set();for(const pr of prs){const k=`${pr.exercise_name}|${pr.type}`;if(!seen.has(k)){seen.add(k);unique.push(pr)}}
const sum=S.completedWorkoutSummary||{},duration=sum.duration_minutes??(S.sessionStartedAt?Math.max(1,Math.round((Date.now()-S.sessionStartedAt)/60000)):null),volume=sum.total_volume;
return `<div class=center><div class=complete-shield>💪</div><p class=eyebrow>SESSION COMPLETE</p><h2>${esc(w()?.name||"Workout")}</h2><p class=muted>Strong work, ${esc(S.name)}. Here’s what you accomplished.</p><div class=spacer></div><div class="metrics completion-metrics"><div class=metric><strong>${duration??"—"}</strong><span>Minutes</span></div><div class=metric><strong>${w()?.exercises?.length||0}</strong><span>Exercises</span></div><div class=metric><strong>${sum.total_sets??w()?.exercises?.reduce((a,e)=>a+e.sets,0)??0}</strong><span>Sets</span></div><div class=metric><strong>${volume!=null?Math.round(volume).toLocaleString():"—"}</strong><span>Volume lb</span></div></div>${unique.length?`<div class=spacer></div><div class=completion-prs><p class=eyebrow>NEW PERSONAL RECORDS</p>${unique.slice(0,4).map(pr=>`<div class=pr-card><p class=eyebrow>🏆 ${esc(pr.label)}</p><h3>${esc(pr.exercise_name)}</h3><strong>${pr.value} ${esc(pr.unit)}</strong></div>`).join("")}</div>`:""}<div class=spacer></div><div class="card completion-next-card"><p class=eyebrow>NEXT SESSION</p><h3>${unique.length?"Progress captured":"Consistency captured"}</h3><p class=muted>Forge will use your logged reps, load, and effort to set the next progression target.</p></div><div class=big-spacer></div><p>How was this workout?</p><div class=spacer></div><div class=feelings>${[["😟","Too Hard"],["😡","Hard"],["🙂","Just Right"],["😎","Easy"],["🔥","Too Easy"]].map(x=>`<button class="feel ${S.feel===x[1]?"selected":""}" data-feel="${x[1]}"><span>${x[0]}</span>${x[1]}</button>`).join("")}</div><div class=big-spacer></div><button class=btn data-a=finish>Finish Workout</button><div class=spacer></div><div class=complete-secondary><button class="btn dark" data-a=finish-progress>View Progress</button><button class="btn dark" data-a=finish-nutrition>Log Nutrition</button></div></div>`;
}

async function loadCompletedWorkoutSummary(){
  if(!S.lastSessionId)return;
  try{const rows=await api("/me/history");const row=(rows||[]).find(x=>Number(x.session_id)===Number(S.lastSessionId));if(row){S.completedWorkoutSummary={total_sets:row.total_sets,total_volume:row.total_volume,duration_minutes:row.started_at&&row.completed_at?Math.max(1,Math.round((Date.parse(row.completed_at+"Z")-Date.parse(row.started_at+"Z"))/60000)):null};if(S.route==="complete")render()}}catch(e){console.warn("Completion summary unavailable",e)}
}



function nutritionDateValue(){
  if(S.nutritionDate)return S.nutritionDate;
  const d=new Date();S.nutritionDate=`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
  return S.nutritionDate;
}
async function loadNutrition(){
  if(!authToken)return;
  try{
    const [day,saved]=await Promise.all([api(`/me/nutrition?date=${encodeURIComponent(nutritionDateValue())}`),api("/me/nutrition/saved-foods?limit=10")]);
    S.nutrition=day;S.nutritionSavedFoods=saved;
    if(S.route==="nutrition")render();
  }catch(e){toast(e.message)}
}
function nutritionProgress(value,target){
  if(!target)return 0;
  return Math.min(100,Math.round(Number(value||0)/Number(target)*100));
}
function nutrition(){
const n=S.nutrition,t=n?.targets||{calories:2200,protein_g:150,carbs_g:250,fat_g:70},v=n?.totals||{calories:0,protein_g:0,carbs_g:0,fat_g:0},r=n?.remaining||{};
const calPct=nutritionProgress(v.calories,t.calories);
return `<div class=row><div><p class=eyebrow>NUTRITION</p><h2>Nutrition</h2></div><input id=nutritionDate type=date value="${nutritionDateValue()}" class=nutrition-date></div>
<p class=muted>Fuel training and recovery without losing sight of the daily target.</p>
<div class=big-spacer></div>
<div class=nutrition-dashboard-hero>
  <div class=nutrition-ring-large style="--p:${calPct}"><div><b>${Math.max(0,Math.round(r.calories??(t.calories-v.calories)))}</b><small>kcal remaining</small></div></div>
  <div class=nutrition-hero-copy><small>${Math.round(v.calories||0)} OF ${t.calories} KCAL</small><h3>${calPct<85?"Room left today":calPct<=105?"Right around target":"Over today’s target"}</h3><p>Protein remaining: <b>${Math.max(0,Math.round(r.protein_g??(t.protein_g-v.protein_g)))}g</b></p><button class=btn data-a=nutrition-add>+ Log Food</button></div>
</div>
<div class=spacer></div><div class=nutrition-macros>
${[["Protein","protein_g","g"],["Carbs","carbs_g","g"],["Fat","fat_g","g"]].map(([label,key,unit])=>`<div class=macro-card><div class=row><small>${label}</small><b>${Math.round(v[key]||0)}/${t[key]}${unit}</b></div><div class=macro-track><i style="width:${nutritionProgress(v[key],t[key])}%"></i></div><em>${Math.max(0,Math.round((r[key]??(t[key]-v[key]))||0))}${unit} left</em></div>`).join("")}</div>
${(S.nutritionSavedFoods||[]).length?`<div class=big-spacer></div><div class=row><h3>Quick Log</h3><small class=muted>Recent & saved foods</small></div><div class=nutrition-saved-strip>${S.nutritionSavedFoods.map(x=>`<div class="card nutrition-saved-card"><button class=nutrition-favorite data-nutrition-favorite="${x.id}" data-favorite="${x.is_favorite?0:1}">${x.is_favorite?"★":"☆"}</button><h3>${esc(x.food_name)}</h3><p class=muted>${x.calories} kcal • P ${Math.round(x.protein_g)}g</p><button class="btn dark compact" data-nutrition-quicklog="${x.id}">+ Log</button></div>`).join("")}</div>`:""}
<div class=big-spacer></div><div class="card nutrition-training-card"><p class=eyebrow>TRAINING + NUTRITION</p><h3>Fuel around today’s training</h3><p class=muted>Forge Coach can use your workout and remaining macros together.</p><div class=row><button class="btn dark compact" data-nutrition-coach="How should I eat for my workout today?">Pre-workout</button><button class="btn dark compact" data-nutrition-coach="What should I eat after my workout today?">Recovery</button></div></div>
<div class=big-spacer></div><div class=row><h3>Meals</h3><button class="btn dark compact" data-a=nutrition-targets>Targets</button></div><div class=spacer></div><div class=nutrition-tools><button class="btn dark compact" data-a=nutrition-copy-yesterday>Copy Yesterday</button><button class="btn dark compact" data-a=nutrition-favorites-only>Favorites</button></div><div class=spacer></div>
<div class=nutrition-entry-list>${nutritionMealGroups(n?.entries||[])}</div>
${S.nutritionEditingTargets?`<div class=nutrition-modal><div class=nutrition-dialog><p class=eyebrow>DAILY TARGETS</p><h2>Nutrition Targets</h2><div class=nutrition-form><label>Calories<input id=targetCalories type=number min=0 value="${t.calories}"></label><label>Protein (g)<input id=targetProtein type=number min=0 value="${t.protein_g}"></label><label>Carbs (g)<input id=targetCarbs type=number min=0 value="${t.carbs_g}"></label><label>Fat (g)<input id=targetFat type=number min=0 value="${t.fat_g}"></label></div><div class=spacer></div><button class=btn data-a=nutrition-save-targets>Save Targets</button><div class=spacer></div><button class="btn dark" data-a=nutrition-close-modal>Cancel</button></div></div>`:""}`;
}
function nutritionadd(){
return `<p class=eyebrow>NUTRITION</p><h2>Add Food</h2><p class=muted>${nutritionDateValue()}</p>
<div class=big-spacer></div><div class=nutrition-form>
<label>Meal<select id=mealType><option>Breakfast</option><option>Lunch</option><option>Dinner</option><option>Snack</option><option>Pre-Workout</option><option>Post-Workout</option></select></label>
<label>Food<input id=foodName placeholder="e.g. Chicken and rice"></label>
<label>Calories<input id=foodCalories type=number min=0 placeholder="0"></label>
<div class=nutrition-form-grid><label>Protein (g)<input id=foodProtein type=number min=0 step=.1 placeholder="0"></label><label>Carbs (g)<input id=foodCarbs type=number min=0 step=.1 placeholder="0"></label><label>Fat (g)<input id=foodFat type=number min=0 step=.1 placeholder="0"></label></div>
</div><div class=big-spacer></div><button class=btn data-a=nutrition-save-food>Save Food</button>`;
}
function workoutbuilder(){
 const ww=w();if(!ww)return home();
 return `<p class=eyebrow>WORKOUT BUILDER</p><h2>${esc(ww.name)}</h2><p class=muted>Edit exercise order, sets, reps, and rest. Forge keeps the current program synchronized.</p><div class=big-spacer></div>
 <div class=stack>${ww.exercises.map((e,i)=>`<div class="card builder-row"><div class=row><div><small>${i+1}</small><h3>${esc(e.name)}</h3></div><div><button data-builder-move="${i}:-1">↑</button><button data-builder-move="${i}:1">↓</button></div></div><div class=builder-fields><label>Sets<input data-builder-sets=${e.exercise_id} type=number min=1 max=12 value=${e.sets}></label><label>Min reps<input data-builder-min=${e.exercise_id} type=number min=1 value=${e.min_reps}></label><label>Max reps<input data-builder-max=${e.exercise_id} type=number min=1 value=${e.max_reps}></label><label>Rest<input data-builder-rest=${e.exercise_id} type=number min=15 step=15 value=${e.rest_seconds||60}></label></div><div class=row><button class="text-action" data-builder-lock="${S.wi}:${e.exercise_id}">${(S.planLocks?.[S.wi]||[]).includes(Number(e.exercise_id))?"🔒 Locked":"Lock exercise"}</button><button class="text-action" data-builder-exclude="${e.exercise_id}:${encodeURIComponent(e.name)}">Never include</button><button class="text-action" data-builder-remove=${e.exercise_id}>Remove</button></div></div>`).join("")}</div>
 <div class=big-spacer></div><button class=btn data-a=builder-add>Add Exercise</button>`;
}
function history(){
return `<div class=row><div><p class=eyebrow>HISTORY</p><h2>Workout History</h2></div><select class=history-filter><option>All</option></select></div><div class=spacer></div><div id=historyList class=stack><div class=card><p class=muted>Loading history…</p></div></div>`;
}

function prs(){
return `<p class=eyebrow>PERSONAL RECORDS</p><h2>Personal Records</h2>
<div class=spacer></div><div class=pr-tabs>
<button class="${S.prView==="exercise"?"active":""}" data-pr-view=exercise>By Exercise</button>
<button class="${S.prView==="lift"?"active":""}" data-pr-view=lift>By Lift Type</button></div>
${S.prView==="lift"?`<div class=spacer></div><p class=muted>View your records grouped by movement type.</p>
<div class=pr-lift-filters>${[["all","All"],["lower","Lower Body"],["upper","Upper Body"],["core","Core"],["conditioning","Conditioning"]].map(([v,l])=>`<button class="${S.prLiftFilter===v?"active":""}" data-pr-lift-filter="${v}">${l}</button>`).join("")}</div>`:""}
<div class=spacer></div><div id=prList class=stack><div class=card><p class=muted>Loading PRs…</p></div></div>`;
}

function exercisehistory(){
return `<p class=eyebrow>EXERCISE HISTORY</p><h2 id=ehTitle>Exercise</h2><div class=spacer></div><div class=tabs><button class="tab active">History</button><button class=tab>About</button></div><div id=ehBody class=stack><div class=card><p class=muted>Loading…</p></div></div>`;
}


function exerciseRecallMarkup(e){
  if(S.exerciseRecallExerciseId!==e.exercise_id){
    return `<p class=eyebrow>PREVIOUS PERFORMANCE</p><p class=muted>Loading your last performance and next target...</p>`;
  }
  const data=S.exerciseRecall;
  if(!data){
    return S.exerciseRecallLoading
      ? `<p class=eyebrow>PREVIOUS PERFORMANCE</p><p class=muted>Loading your last performance and next target...</p>`
      : `<p class=eyebrow>TRAINING HISTORY</p><p class=muted>No previous data available yet.</p>`;
  }
  const sets=data.sets||[];
  const last=sets.length?sets[sets.length-1]:null;
  const suggestion=data.progression_suggestion;
  if(!last)return `<p class=eyebrow>FIRST SESSION</p><h3>No previous sets yet</h3><p class=muted>Log this exercise and Forge will remember it next time.</p>`;
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
  if(S.exerciseRecallLoading)return;
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
      if(card)card.innerHTML=`<p class=eyebrow>TRAINING HISTORY</p><p class=muted>No previous data available yet.</p>`;
    }
  }finally{
    if(S.exerciseRecallExerciseId===exerciseId)S.exerciseRecallLoading=false;
  }
}

async function loadHistory(){
  try{
    const rows=await api("/me/history");
    const el=document.querySelector("#historyList");if(!el)return;
    if(!rows.length){el.innerHTML=`<div class=card><p class=muted>No completed workout history yet.</p></div>`;return}
    el.innerHTML=rows.map(r=>`<button class=card data-session=${r.session_id} style="width:100%;color:white;text-align:left">
      <div class=row><div><p class=eyebrow>WEEK ${r.week_number}</p><h3>${esc(r.workout_name)}</h3>
      <p class=muted>${r.total_sets} sets • ${Math.round(r.total_volume)} lb volume</p></div>
      <span>${r.status==="completed"?"✓":"○"}</span></div></button>`).join("");
  }catch(e){toast(e.message)}
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
if(!rows.length)return `<div class=card><p class=muted>No PRs yet. Log some workouts first.</p></div>`;
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
if(!groups.length)return `<div class=card><h3>No records in this lift type yet</h3><p class=muted>Complete exercises in this category to build records.</p></div>`;
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
try{S.prRecords=await api("/me/prs");renderPRList()}catch(e){toast(e.message)}
}

async function loadExerciseHistory(){
  try{
    const data=await api(`/me/exercises/${S.historyExercise}/history`);
    const t=document.querySelector("#ehTitle"),b=document.querySelector("#ehBody");if(!t||!b)return;
    t.textContent=data.name;
    const prs=data.prs||{},suggestion=data.progression_suggestion;
    const all=data.sets||[],recent=all.slice(-12);
    const max=Math.max(1,...recent.map(x=>Number(x.e1rm||0)));
    b.innerHTML=`<div class=metrics>
      <div class=metric><strong>${prs.max_weight||0}</strong><span>MAX LB</span></div>
      <div class=metric><strong>${prs.best_e1rm||0}</strong><span>EST. 1RM</span></div>
      <div class=metric><strong>${prs.best_reps||0}</strong><span>BEST REPS</span></div></div>
      <div class=spacer></div>
      ${recent.length?`<div class=card><p class=eyebrow>ESTIMATED 1RM TREND</p><div class=trend-chart>${recent.map((x,i)=>`<div class=trend-col title="${x.weight} lb × ${x.reps}"><i style="height:${Math.max(8,(Number(x.e1rm||0)/max)*100)}%"></i><small>${i+1}</small></div>`).join("")}</div></div>`:""}
      <div class=spacer></div>
      ${suggestion?`<div class=card><p class=eyebrow>NEXT TARGET</p><h3>${suggestion.action.replaceAll("_"," ")}</h3><p class=muted>Suggested weight: ${suggestion.suggested_weight} lb • Recent avg RPE ${suggestion.recent_average_rpe}</p></div>`:""}
      <div class=spacer></div><div class=stack>${recent.slice().reverse().map(x=>`<div class=card><div class=row><div><strong>${x.weight} lb × ${x.reps}</strong><p class=muted>${x.workout_name} • RPE ${x.rpe??"—"}</p></div><span>${x.e1rm} e1RM</span></div></div>`).join("")}</div>`;
  }catch(e){toast(e.message)}
}


async function loadProgressHub(){
  if(!authToken)return;
  try{S.progressHub=await api("/me/progress/hub");if(S.route==="progress")render()}catch(e){console.warn("Progress hub load failed",e)}
}
function progressHubOverview(){
  const h=S.progressHub;if(!h)return `<div class="card progress-hub-card"><p class=eyebrow>PROGRESS HUB</p><h3>Connecting your training data…</h3></div>`;
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
  try{
    S.progressIntelligence=await api("/me/progress/intelligence");
    if(S.route==="progress")render();
  }catch(e){console.warn("Progress intelligence failed",e)}
}
function progressIntelligenceCard(){
  const x=S.progressIntelligence;
  if(!x)return `<div class="card progress-intelligence-card"><p class=eyebrow>PROGRESS INTELLIGENCE</p><h3>Analyzing your training...</h3><p class=muted>Forge is combining your recent training, strength, recovery, and nutrition data.</p></div>`;
  const score=x.score==null?"—":x.score;
  return `<div class="card progress-intelligence-card ${esc(x.status)}">
    <div class=row><div><p class=eyebrow>PROGRESS INTELLIGENCE</p><h3>${esc(x.headline)}</h3></div><div class=progress-score><b>${score}</b><small>/100</small></div></div>
    <div class=progress-signal-grid>${(x.signals||[]).slice(0,4).map(s=>`<div class="progress-signal ${s.status}"><small>${esc(s.label)}</small><b>${esc(s.value)}</b></div>`).join("")}</div>
    <div class=spacer></div><p class=muted>${esc((x.recommendations||[])[0]||"Keep logging training so Forge can identify meaningful trends.")}</p>
    <div class=spacer></div><button class="btn dark" data-progress-coach="Analyze my progress and tell me what is limiting me">Ask Coach About My Progress</button>
  </div>`;
}

async function loadBodyMetrics(){
  try{
    S.bodyMetrics=await api(`/me/body-metrics?range_days=${encodeURIComponent(S.bodyMetricRange)}`);
    if(S.route==="progress")render();
  }catch(e){console.warn("Body metrics load failed",e)}
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
  return `<div class=nutrition-modal><div class=nutrition-dialog><p class=eyebrow>BODY CHECK-IN</p><h2>Log Measurements</h2><p class=muted>Only fill in what you measured today.</p>
  <div class=nutrition-form><label>Date<input id=bodyDate type=date value="${today}"></label><label>Weight (lb)<input id=bodyWeight type=number min=0 step=.1 placeholder="e.g. 185.4"></label>
  <div class=body-measure-grid><label>Body Fat (%)<input id=bodyFat type=number min=0 step=.1></label><label>Waist (in)<input id=bodyWaist type=number min=0 step=.1></label><label>Chest (in)<input id=bodyChest type=number min=0 step=.1></label><label>Hips (in)<input id=bodyHips type=number min=0 step=.1></label><label>Arm (in)<input id=bodyArm type=number min=0 step=.1></label><label>Thigh (in)<input id=bodyThigh type=number min=0 step=.1></label></div><label>Notes<input id=bodyNotes maxlength=500 placeholder="Optional"></label></div>
  <div class=spacer></div><button class=btn data-a=body-metric-save>Save Check-In</button><div class=spacer></div><button class="btn dark" data-a=body-metric-close>Cancel</button></div></div>`;
}


async function loadTrainingRecords(){if(S.trainingRecords?.loading)return;S.trainingRecords={loading:true};try{S.trainingRecords=await api("/me/training-records");if(S.route==="progress")render()}catch(e){console.warn("Training records failed",e)}}
function trainingRecordsCard(){const d=S.trainingRecords;if(!d||d.loading)return "";const cards=(d.exercise_cards||[]).slice(0,6),blocks=d.mesocycle_history||[];return `<div class="card records3-card"><div class=row><div><p class=eyebrow>TRAINING HISTORY 3.0</p><h3>Exercise progression records</h3></div><b>${d.exercise_cards.length}</b></div><div class=record-card-grid>${cards.map(x=>`<div><b>${esc(x.name)}</b><span>${x.sessions} sessions</span><strong>${x.change_percent>0?"+":""}${x.change_percent}%</strong><small>Best e1RM ${Math.round(x.best_e1rm||0)} lb • ${x.best_reps||0} rep PR</small></div>`).join("")}</div>${blocks.length?`<div class=spacer></div><p class=eyebrow>MESOCYCLE COMPARISON</p><div class=block-history>${blocks.slice(-4).map(x=>`<span><b>Block ${x.block}</b><small>${x.workouts} workouts • ${x.sets} sets • ${Math.round(x.volume).toLocaleString()} lb</small></span>`).join("")}</div>`:""}</div>`}

function progress(){
const done=(plan?.workouts||[]).filter(x=>x.status==="completed").length;
const t=S.strengthTrend;
const summary=t?.summary||{};
const change=Number(summary.change_percent||0);
const changeText=(change>0?"+":"")+change.toFixed(1)+"%";
return `${trainingRecordsCard()}<div class=big-spacer></div>${trainingDashboardCard()}<div class=big-spacer></div><p class=eyebrow>PROGRESS</p><h2>Your Progress</h2>
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
  if(!pts.length)return `<div class=chart-empty>Log working sets to build your strength progress.</div>`;
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
  if(!authToken)return;
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
  }
}


async function loadCoachBriefing(){
  if(!authToken)return;
  try{S.coachBriefing=await api("/me/coach/briefing");if(S.route==="coach")render()}catch(e){console.warn("Coach briefing failed",e)}
}
function coachBriefingCard(){
  const b=S.coachBriefing;if(!b)return `<div class="card coach-briefing"><p class=eyebrow>WHOLE-DAY CONTEXT</p><h3>Building your training picture…</h3></div>`;
  const chips=[
    ["Readiness",b.readiness?.label||"Unknown"],
    ["Recovery",b.recovery?.level||"Unknown"],
    ["Progress",b.progress?.headline||"Building data"],
    ["Calendar",b.calendar?.conflicts?`${b.calendar.conflicts} conflict${b.calendar.conflicts===1?"":"s"}`:"Clear"],
    ["Nutrition",b.nutrition?.summary||"No data"]
  ];
  return `<div class="card coach-briefing"><div class=row><div><p class=eyebrow>COACH 3.0 • WHOLE-DAY CONTEXT</p><h3>${esc(b.headline||"Your training picture")}</h3></div><b>${b.score==null?"—":b.score}/100</b></div>
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
function coach4ContextCard(){const c=S.coach4;if(!c||c.loading)return "";const m=c.mesocycle||{},muscles=(c.muscle_status||[]).slice(0,4),prog=(c.exercise_progression||[]).slice(0,3);return `<div class="card coach4-context"><div class=row><div><p class=eyebrow>COACH 4.0 • PROGRAMMING CONTEXT</p><h3>Block ${m.block_number} • Week ${m.week_in_block}/${m.block_length}</h3></div><b>${esc(m.phase||"")}</b></div><p class=muted>Forge can now explain decisions from your block phase, readiness, muscle volume, progression history, schedule, and nutrition context.</p><div class=coach4-grid>${muscles.map(x=>`<span><b>${esc(x.muscle)}</b><small>${x.actual_sets}/${x.target_sets} sets</small></span>`).join("")}</div>${prog.length?`<div class=spacer></div>${prog.map(x=>`<div class=coach4-prog><b>${esc(x.name)}</b><span>${esc(x.status)} • ${esc(x.method)}</span></div>`).join("")}`:""}</div>`}

function coach(){
const msgs=S.coachMessages||[],c=S.coachContext;
return `${coach4ContextCard()}<div class=spacer></div><div class=row><div><p class=eyebrow>FORGE COACH</p><h2>AI Coach</h2></div><button class="btn dark compact" data-a=clear-coach>Clear</button></div>
<p class=muted>Your training assistant, grounded in your Forge data.</p>
<div class="coach-model-status ${S.coachStatus?.llm_enabled?"online":"fallback"}"><span>${S.coachStatus?.llm_enabled?"● AI online":"● Smart fallback"}</span><small>${S.coachStatus?.llm_enabled?esc(S.coachStatus.model||"OpenAI"):"Set OPENAI_API_KEY to enable the LLM"}</small></div>
${c?`<div class=spacer></div><div class=coach-context><div><b>${c.recent_completed_workouts}</b><small>Recent Workouts</small></div><div><b>${Number(c.fatigue_score||0).toFixed(1)}</b><small>Fatigue</small></div><div><b>${c.week_number||1}</b><small>Week</small></div></div>`:""}
<div class=spacer></div>${coachBriefingCard()}
<div class=spacer></div>
<div class=coach-action-launcher>
  <button data-coachprompt="Review my readiness, recovery, calendar, nutrition, and recent progress together, then propose the best changes for today"><span>⚙</span><b>Adjust Today</b><small>Use recovery + recent training</small></button>
  <button data-coachprompt="Find the best exercise swap for my current workout using only my equipment"><span>⇄</span><b>Smart Swap</b><small>Equipment-aware replacement</small></button>
  <button data-coachprompt="Check my calendar availability, recovery spacing, and propose the best workout placement this week"><span>▦</span><b>Calendar Intelligence</b><small>Conflicts + recovery spacing</small></button>
  <button data-coachprompt="Review my progress and tell me whether next week should progress, maintain, or recover"><span>↗</span><b>Next Week</b><small>Adaptive plan recommendation</small></button>
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
${msgs.length?msgs.map(coachMessageHTML).join(""):`<div class="bubble ai coach-rich-response"><div>Ask me about training, recovery, progress, nutrition goals, or tell me what you ate and where you got it.</div><div class=coach-response-actions><button data-coach-route=workout>Today’s Workout</button><button data-coach-route=nutrition>Nutrition</button></div></div>`}
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
  if(!authToken)return;
  try{
    const [messages,context,status]=await Promise.all([api("/me/coach/history"),api("/me/coach/context"),api("/me/coach/status")]);
    S.coachMessages=(messages||[]).map(x=>({role:x.role==="assistant"?"ai":"user",text:x.message}));
    S.coachContext=context;S.coachStatus=status;S.coachLoaded=true;
    if(S.route==="coach")render();
  }catch(e){console.warn("Coach load failed",e)}
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


async function loadRecoveryIntelligence(){try{S.recoveryIntelligence=await api("/me/recovery-intelligence");if(S.route==="plan")render()}catch(e){console.warn("Recovery intelligence failed",e)}}
async function loadAdaptationPreview(){
  if(!authToken||!plan)return;
  try{
    S.adaptationPreview=await api("/me/program/adaptation-preview");
    if(S.route==="plan")render();
  }catch(e){console.warn("Adaptation preview failed",e)}
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
function recoveryCard(){const r=S.recoveryIntelligence;if(!r)return `<div class="card"><p class=eyebrow>RECOVERY</p><p class=muted>Analyzing recovery…</p></div>`;return `<div class="card recovery-card ${r.level}"><p class=eyebrow>RECOVERY + DELOAD INTELLIGENCE</p><h3>${esc(r.title)}</h3><p class=muted>${esc(r.recommendation||"")}</p>${(r.flags||[]).length?`<div class=stack>${r.flags.map(x=>`<small>• ${esc(x)}</small>`).join("")}</div>`:""}<div class=adaptation-metrics><div><small>Fatigue</small><b>${Number(r.fatigue_score||0).toFixed(1)}/10</b></div><div><small>Avg effort</small><b>${r.average_rpe==null?"—":Number(r.average_rpe).toFixed(1)}</b></div><div><small>Adherence</small><b>${r.adherence_percent==null?"—":Math.round(r.adherence_percent)+"%"}</b></div></div></div>`}
function adaptationCard(){
  const a=S.adaptationPreview;
  if(!a)return `<div class="card adaptation-card"><p class=eyebrow>ADAPTIVE PROGRAMMING</p><h3>Analyzing your week…</h3><p class=muted>Forge is checking completion, recovery, strength trend, and recent effort.</p></div>`;
  const pct=Math.round(Number(a.completion_rate||0)*100);
  return `<div class="card adaptation-card ${a.recommendation}">
    <div class=row><div><p class=eyebrow>NEXT-WEEK ADAPTATION</p><h3>${esc(a.title)}</h3></div><span class=adaptation-badge>${esc(a.recommendation.toUpperCase())}</span></div>
    <p class=muted>${esc(a.reason)}</p>${a.proposed_changes?.length?`<div class=program-change-preview><p class=eyebrow>PROPOSED CHANGES — REVIEW BEFORE APPLYING</p>${a.proposed_changes.map(c=>`<div class=adaptation-note><span><b>${esc(c.area)}</b><small>${esc(c.reason)}</small></span><strong>${esc(c.proposed)}</strong></div>`).join("")}</div>`:""}
    ${a.exercise_decisions?.length?`<div class=program-change-preview><p class=eyebrow>EXERCISE-LEVEL ADAPTATION</p>${a.exercise_decisions.slice(0,6).map(x=>`<div class=adaptation-note><span><b>${esc(x.exercise)}</b><small>${esc(x.reason)}</small></span><strong>${esc(String(x.action||"hold").toUpperCase())}</strong></div>`).join("")}</div>`:""}
    <div class=adaptation-metrics>
      <div><small>Completion</small><b>${pct}%</b></div>
      <div><small>Fatigue</small><b>${Number(a.fatigue_score||0).toFixed(1)}/10</b></div>
      <div><small>Volume</small><b>${esc(a.set_change)}</b></div>
    </div>
    <div class=adaptation-note><b>Session change</b><span>${esc(a.time_change)}</span></div>
    ${a.can_apply?`<button class=btn data-a=apply-adaptation ${S.adaptationBusy?"disabled":""}>${S.adaptationBusy?"Building next week…":`Approve & Build Week ${a.next_week_number}`}</button>`:`<div class=adaptation-lock><b>${a.unfinished_workouts} workout${a.unfinished_workouts===1?"":"s"} remaining</b><span>Complete or skip the current week before Forge builds the next adaptive week.</span></div>`}
  </div>`;
}
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
  }).join("")}</div>`:`<div class=card><p class=muted>Training focus will appear after your plan is generated.</p></div>`}

  ${plan?.mesocycle?`<div class=big-spacer></div><div class="card mesocycle-card"><p class=eyebrow>TRAINING BLOCK</p><div class=row><h3>Block ${plan.mesocycle.block_number} · Week ${plan.mesocycle.week_in_block}/${plan.mesocycle.block_length_weeks}</h3><b>${esc(String(plan.mesocycle.phase||"training").toUpperCase())}</b></div><p class=muted>${esc(plan.mesocycle.intensity_cue||"")}</p><small>${plan.mesocycle.deload_recommended?"Deload pressure is active this week.":"Forge is progressing this block without unnecessary exercise rotation."}</small></div>`:""}
  <div class=big-spacer></div>
  <div class=card>
    <p class=eyebrow>HOW YOUR PLAN ADAPTS</p>
    <h3>Built to progress with you</h3>
    <p class=muted>Forge uses your logged sets, effort, workout completion, strength progress, and recovery feedback to adjust future training.</p>
  </div>

  <div class=spacer></div>
  <button class=btn data-a=adjust-plan>Adjust Plan</button><div class=spacer></div><button class=btn data-plan-tab=workouts>View Workouts</button><div class=spacer></div><button class="btn dark" data-a=edit-equipment-log>Manage Equipment Log</button><div class=spacer></div><button class="btn dark" data-a=open-exercise-directory>Browse Exercise Directory</button><div class=spacer></div><button class="btn dark" data-a=open-training-settings>Training Settings</button>
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
 return `<p class=eyebrow>PLAN CUSTOMIZATION</p><h2>Adjust Your Plan</h2><p class=muted>Change your weekly availability without starting over manually. Forge will rebuild the plan around these constraints.</p><div class=big-spacer></div>
 <div class=card><h3>Workouts per week</h3><div class=chips>${[2,3,4,5,6].map(n=>`<button class="chip ${profile.days_per_week===n?"selected":""}" data-adjust-days=${n}>${n} days</button>`).join("")}</div><div class=spacer></div><h3>Session length</h3><div class=chips>${[20,30,45,60,75,90].map(n=>`<button class="chip ${profile.minutes_per_workout===n?"selected":""}" data-adjust-mins=${n}>${n} min</button>`).join("")}</div></div><div class=spacer></div><h3>Exercises per workout</h3><p class=muted>Forge targets this many strength exercises each training day.</p><div class=chips>${[3,4,5,6,7,8,9,10].map(n=>`<button class="chip ${Number(profile.exercises_per_day||6)===n?"selected":""}" data-adjust-exercises=${n}>${n}</button>`).join("")}</div>
 <div class=spacer></div><div class=card><h3>Exercises by workout</h3><p class=muted>Override the global target for individual training days.</p><div class=stack>${Array.from({length:profile.days_per_week},(_,i)=>`<div class=row><b>Day ${i+1}${plan?.workouts?.[i]?.name?` · ${esc(plan.workouts[i].name)}`:""}</b><select data-day-exercises=${i}>${[3,4,5,6,7,8,9,10].map(n=>`<option value=${n} ${Number((profile.exercises_per_workout||[])[i]||profile.exercises_per_day||6)===n?"selected":""}>${n}</option>`).join("")}</select></div>`).join("")}</div></div>${S.planPreview?`<div class=spacer></div><div class="card accent-card"><p class=eyebrow>PLAN PREVIEW + VALIDATION</p><h3>Review before replacing your plan</h3><p class=muted>${(S.planPreview.changes||[]).reduce((n,x)=>n+x.added.length,0)} exercises added · ${(S.planPreview.changes||[]).reduce((n,x)=>n+x.removed.length,0)} removed. Generator invariants: ${esc(S.planPreview.diagnostics?.generator_invariants||"passed")}.</p>${S.planPreview.diagnostics?.warnings?.length?`<div class=adaptation-lock><b>Plan warnings</b><span>${S.planPreview.diagnostics.warnings.map(esc).join(" • ")}</span></div>`:""}<div class=stack>${(S.planPreview.changes||[]).map(x=>`<div><b>${esc(x.name||`Day ${x.workout_index+1}`)} · ${x.exercise_count_before??0} → ${x.exercise_count_after??0} exercises</b><small class=muted style="display:block">+ ${x.added.map(esc).join(", ")||"None"}</small><small class=muted style="display:block">− ${x.removed.map(esc).join(", ")||"None"}</small>${x.set_changes?.length?`<small class=muted style="display:block">Sets: ${x.set_changes.map(c=>`${esc(c.exercise)} ${c.before}→${c.after}`).join(" • ")}</small>`:""}</div>`).join("")}</div><div class=row><button class=btn data-a=apply-plan-preview>Apply New Plan</button><button class="btn dark" data-a=cancel-plan-preview>Keep Current Plan</button></div></div>`:""}<div class=spacer></div><div class=card><h3>Preferred training days</h3><p class=muted>Choose ${profile.days_per_week} days. Forge will use these exact days when possible.</p><div class=day-picker>${days.map((d,i)=>`<button type=button class="${S.preferredDays.includes(i)?"selected":""}" data-preferred-day=${i}>${d.slice(0,3)}</button>`).join("")}</div></div>
 <div class=spacer></div><div class=card><p class=eyebrow>WHAT FORGE PRESERVES</p><p class=muted>Priority movements, muscle balance, recovery spacing, equipment compatibility, and useful weekly volume are considered when the plan is rebuilt.</p></div>
 <div class=big-spacer></div><button class=btn data-a=save-plan-adjust ${S.planAdjusting?"disabled":""}>${S.planAdjusting?"Rebuilding…":"Rebuild Plan"}</button>`;
}


async function loadSystemHealth(){
  if(!authToken)return;
  try{S.systemHealth=await api("/me/system/health");if(S.route==="trainingsettings")render()}catch(e){S.systemHealth={status:"degraded",checks:{api:false},message:e.message};if(S.route==="trainingsettings")render()}
}
function systemHealthCard(){
  const h=S.systemHealth;if(!h)return `<div class=card><p class=eyebrow>SYSTEM HEALTH</p><h3>Checking Forge…</h3></div>`;
  const checks=Object.entries(h.checks||{});
  return `<div class="card system-health ${h.status}"><div class=row><div><p class=eyebrow>PRODUCTION HEALTH</p><h3>${h.status==="ok"?"All core systems operational":"Forge needs attention"}</h3></div><b>${h.status==="ok"?"✓":"!"}</b></div><div class=system-check-grid>${checks.map(([k,v])=>`<span><i>${v===true?"✓":v===false?"!":"•"}</i>${esc(k.replaceAll("_"," "))}</span>`).join("")}</div>${h.persistence?`<small>Persistence: ${esc(h.persistence)}</small>`:""}</div>`;
}

function trainingsettings(){return `<p class=eyebrow>SETTINGS</p><h2>Training Settings</h2><p class=muted>Change how Forge structures future plans.</p><div class=big-spacer></div>${finalPolishSettingsCard()}<div class=spacer></div>${systemHealthCard()}<div class=spacer></div>${pwaInstallCard()}<div class=big-spacer></div><div class=preference-list><button class=pref-row data-a=adjust-plan><span><strong>Schedule & Workout Size</strong><small class=muted style="display:block">${profile.days_per_week} days • ${profile.minutes_per_workout} min • ${profile.exercises_per_day||6} exercises</small></span><span>›</span></button><button class=pref-row data-a=settings-split><span><strong>Workout Split</strong><small class=muted style="display:block">${splitLabel(profile.workout_split)}</small></span><span>›</span></button><button class=pref-row data-a=settings-cardio-frequency><span><strong>Cardio Training</strong><small class=muted style="display:block">${cardioFrequencyLabel(profile.cardio_workouts_per_week)}</small></span><span>›</span></button><button class=pref-row data-a=settings-cardio-intensity><span><strong>Cardio Intensity</strong><small class=muted style="display:block">${cardioLabel(profile.cardio_preference)}</small></span><span>›</span></button><button class=pref-row data-a=settings-sport><span><strong>Sport</strong><small class=muted style="display:block">${sportLabel(profile.sport)}</small></span><span>›</span></button><button class=pref-row data-a=settings-core><span><strong>Core Training</strong><small class=muted style="display:block">${coreFrequencyLabel(profile.core_workouts_per_week)}</small></span><span>›</span></button><button class=pref-row data-a=settings-calendar><span><strong>Calendar & Time</strong><small class=muted style="display:block">${S.calendarStatus?.connected?"Google Calendar connected":(S.calendarStatus?.configured?"Not connected":"Google OAuth not configured")}</small></span><span>›</span></button></div><div class=big-spacer></div><button class=btn data-a=settings-save>Save Settings</button>`}
function calendarsettings(){
const ts=S.timeSettings||{},cs=S.calendarStatus||{};
const connected=!!cs.connected,configured=!!cs.configured;
return `<p class=eyebrow>CALENDAR & TIME</p><h2>Calendar & Time</h2>
<p class=muted>Forge uses your device timezone and can keep workout events synchronized with Google Calendar.</p>
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
<label class=calendar-toggle><span><strong>Sync workouts to Google Calendar</strong><small>Forge and Google can move workouts in either direction.</small></span>
<input id=calendarSyncToggle type=checkbox ${ts.calendar_sync_enabled!==false?"checked":""}></label>
<div class=big-spacer></div>
<div class="card google-calendar-card simplified-calendar-card">
<div class=calendar-provider-row>
  <div class=google-provider-mark>G</div>
  <div><p class=eyebrow>GOOGLE CALENDAR</p><h3>${connected?"Google Calendar connected":configured?"Connect Google Calendar":"Google Calendar unavailable"}</h3></div>
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
     <p class=calendar-privacy-note>Forge only asks for Calendar access needed to schedule workouts and check availability.</p>`
   :`<div class=calendar-unavailable-note><b>No action needed</b><span>The Forge server owner needs to enable Google Calendar before accounts can connect.</span></div>`}
</div>
<div class=big-spacer></div>${calendarIntelligenceCard()}
<div class=big-spacer></div><button class=btn data-a=calendar-settings-save>Save Calendar & Time Settings</button>`;
}
window.ForgeLegacyViews=Object.assign(window.ForgeLegacyViews||{},{nutrition:()=>nutrition(),nutritionadd:()=>nutritionadd()});
window.ForgeLegacyViews=Object.assign(window.ForgeLegacyViews||{},{workout:()=>workout(),exercise:()=>exercise(),timer:()=>timer(),complete:()=>complete(),swapexercise:()=>swapexercise(),cardioswap:()=>cardioswap(),modulemove:()=>modulemove(),coretracker:()=>coretracker(),cardiotracker:()=>cardiotracker()});
window.ForgeLegacyViews=Object.assign(window.ForgeLegacyViews||{},{planScreen:()=>planScreen(),adjustplan:()=>adjustplan(),trainingsettings:()=>trainingsettings(),calendarsettings:()=>calendarsettings()});
window.ForgeLegacyViews=Object.assign(window.ForgeLegacyViews||{},{progress:()=>progress(),history:()=>history(),prs:()=>prs(),exercisehistory:()=>exercisehistory()});
window.ForgeLegacyViews=Object.assign(window.ForgeLegacyViews||{},{coach:()=>coach(),notifications:()=>notificationCenter()});
function render(){const map={welcome,register,login,goal,experience,schedule,equipment,preferences,preferencepicker,cardiopicker,cardiofrequencypicker,splitpicker,customsplit,sportpicker,corepicker,trainingsettings,adjustplan,calendarsettings,generating,yourplan,home,readiness:readinessCheckin,workout,exercise,timer,complete,progress,nutrition,nutritionadd,workoutbuilder,history,prs,exercisehistory,swapexercise,cardioswap,modulemove,coretracker,cardiotracker,coach,notifications:notificationCenter,equipmentlog,equipmentdetails,exercisedirectory,exercisedetail,formdemo,demoaudit,demoreview,plan:planScreen};V.innerHTML=networkBanner()+updateBanner()+(ForgeFeatures.has(S.route)?ForgeFeatures.view(S.route):map[S.route]())+floatingRestTimer()+moreSheet();const onboarding=["welcome","register","login","goal","experience","schedule","equipment","equipmentdetails","preferences","preferencepicker","cardiopicker","cardiofrequencypicker","splitpicker","sportpicker","corepicker","customsplit","generating","yourplan"].includes(S.route)&&!plan;nav.classList.toggle("hidden",onboarding);document.querySelector("#backBtn").style.visibility=["welcome","home","progress","nutrition","coach"].includes(S.route)?"hidden":"visible";document.querySelectorAll("[data-plan-tab]").forEach(b=>b.onclick=()=>{S.planTab=b.dataset.planTab;render()});document.querySelectorAll("[data-coach-route]").forEach(b=>b.onclick=()=>go(b.dataset.coachRoute));
document.querySelectorAll("[data-readiness-key]").forEach(b=>b.onclick=()=>{S.readinessCheckin=S.readinessCheckin||{};S.readinessCheckin[b.dataset.readinessKey]=Number(b.dataset.readinessValue);render()});
document.querySelectorAll("[data-readiness-minutes]").forEach(b=>b.onclick=()=>{S.readinessCheckin=S.readinessCheckin||{};S.readinessCheckin.minutes=Number(b.dataset.readinessMinutes);render()});
document.querySelectorAll("[data-swap-reason]").forEach(b=>b.onclick=()=>{S.swapReason=b.dataset.swapReason;render();loadSwapOptions()});
document.body.dataset.route=S.route;document.querySelectorAll("[data-nav]").forEach(b=>{const active=b.dataset.nav===S.route;b.classList.toggle("active",active);if(active)b.setAttribute("aria-current","page");else b.removeAttribute("aria-current");b.onclick=()=>go(b.dataset.nav)});document.querySelectorAll("[data-a]").forEach(b=>b.onclick=()=>act(b.dataset.a));document.querySelectorAll("[data-goal]").forEach(b=>b.onclick=()=>{profile.goal=b.dataset.goal;render()});document.querySelectorAll("[data-exp]").forEach(b=>b.onclick=()=>{profile.experience=b.dataset.exp;render()});document.querySelectorAll("[data-days]").forEach(b=>b.onclick=()=>{profile.days_per_week=+b.dataset.days;profile.core_workouts_per_week=Math.min(profile.core_workouts_per_week,profile.days_per_week);profile.cardio_workouts_per_week=Math.min(profile.cardio_workouts_per_week,profile.days_per_week);if(profile.workout_split==="custom")ensureCustomSplit();render()});document.querySelectorAll("[data-mins]").forEach(b=>b.onclick=()=>{profile.minutes_per_workout=+b.dataset.mins;render()});document.querySelectorAll("[data-exercise-count]").forEach(b=>b.onclick=()=>{profile.exercises_per_day=+b.dataset.exerciseCount;render()});document.querySelectorAll("[data-setchange]").forEach(b=>b.onclick=async()=>{const ex=w()?.exercises?.[S.ei];if(!ex)return;const next=Math.max(S.set+1,Math.min(12,Number(ex.sets)+Number(b.dataset.setchange)));if(next===ex.sets)return;try{await api(`/me/workouts/${w().workout_id}/exercise-sets`,{method:"PUT",body:JSON.stringify({exercise_id:ex.exercise_id,sets:next})});ex.sets=next;toast(`${next} sets planned`);render()}catch(e){toast(e.message)}});document.querySelectorAll("[data-adjust-days]").forEach(b=>b.onclick=()=>{profile.days_per_week=+b.dataset.adjustDays;profile.core_workouts_per_week=Math.min(profile.core_workouts_per_week,profile.days_per_week);profile.cardio_workouts_per_week=Math.min(profile.cardio_workouts_per_week,profile.days_per_week);if(profile.workout_split==="custom")ensureCustomSplit();S.preferredDays=S.preferredDays.slice(0,profile.days_per_week);render()});document.querySelectorAll("[data-adjust-mins]").forEach(b=>b.onclick=()=>{profile.minutes_per_workout=+b.dataset.adjustMins;render()});document.querySelectorAll("[data-adjust-exercises]").forEach(b=>b.onclick=()=>{profile.exercises_per_day=+b.dataset.adjustExercises;render()});document.querySelectorAll("[data-day-exercises]").forEach(el=>el.onchange=()=>{profile.exercises_per_workout=profile.exercises_per_workout||[];profile.exercises_per_workout[+el.dataset.dayExercises]=+el.value;S.planPreview=null;render()});document.querySelectorAll("[data-preferred-day]").forEach(b=>b.onclick=()=>{const d=+b.dataset.preferredDay,i=S.preferredDays.indexOf(d);if(i>=0)S.preferredDays.splice(i,1);else if(S.preferredDays.length<profile.days_per_week)S.preferredDays.push(d);else{toast(`Choose ${profile.days_per_week} days`);return}render()});document.querySelectorAll("[data-cardio]").forEach(b=>b.onclick=()=>{profile.cardio_preference=b.dataset.cardio;render()});document.querySelectorAll("[data-split]").forEach(b=>b.onclick=()=>{profile.workout_split=b.dataset.split;if(profile.workout_split==="custom"){ensureCustomSplit();go("customsplit")}else render()});document.querySelectorAll("[data-custom-muscle]").forEach(b=>b.onclick=()=>{const [raw,m]=b.dataset.customMuscle.split(":");const i=Number(raw);ensureCustomSplit();const day=profile.custom_split[i],arr=day.muscles,at=arr.indexOf(m);if(at>=0){if(arr.length===1){toast("Each custom day needs at least one muscle group");return}arr.splice(at,1);if(day.submuscles)delete day.submuscles[m]}else arr.push(m);day.name=customDayName(arr,i);render()});document.querySelectorAll("[data-custom-submuscle]").forEach(b=>b.onclick=()=>{const [raw,m,sub]=b.dataset.customSubmuscle.split(":");const i=Number(raw);ensureCustomSplit();const day=profile.custom_split[i];day.submuscles=day.submuscles||{};const arr=day.submuscles[m]||[];const at=arr.indexOf(sub);if(at>=0)arr.splice(at,1);else arr.push(sub);if(arr.length)day.submuscles[m]=arr;else delete day.submuscles[m];render()});document.querySelectorAll("[data-custom-frequency]").forEach(b=>b.onclick=()=>{const [m,raw]=b.dataset.customFrequency.split(":");adjustCustomMuscleFrequency(m,Number(raw));render()});document.querySelectorAll("[data-custom-priority]").forEach(b=>b.onclick=()=>{const m=b.dataset.customPriority;profile.priority_muscles=profile.priority_muscles||[];const i=profile.priority_muscles.indexOf(m);if(i>=0)profile.priority_muscles.splice(i,1);else profile.priority_muscles.push(m);render()});
document.querySelectorAll("[data-sport]").forEach(b=>b.onclick=()=>{profile.sport=b.dataset.sport;render()});document.querySelectorAll("[data-core-frequency]").forEach(b=>b.onclick=()=>{profile.core_workouts_per_week=Math.min(+b.dataset.coreFrequency,+profile.days_per_week);render()});document.querySelectorAll("[data-cardio-frequency]").forEach(b=>b.onclick=()=>{profile.cardio_workouts_per_week=Math.min(+b.dataset.cardioFrequency,+profile.days_per_week);if(!["light","moderate","high","extended"].includes(profile.cardio_preference))profile.cardio_preference="moderate";render()});const nutritionDate=document.querySelector("#nutritionDate");
if(nutritionDate)nutritionDate.onchange=()=>{S.nutritionDate=nutritionDate.value;S.nutrition=null;loadNutrition();};
document.querySelectorAll("[data-nutrition-delete]").forEach(b=>b.onclick=async()=>{if(confirm("Delete this food entry?")){await api(`/me/nutrition/entries/${b.dataset.nutritionDelete}`,{method:"DELETE"});S.nutrition=null;await loadNutrition();}});
document.querySelectorAll("[data-nutrition-edit]").forEach(b=>b.onclick=async()=>{const x=(S.nutrition?.entries||[]).find(v=>String(v.id)===String(b.dataset.nutritionEdit));if(!x)return;const food=prompt("Food name",x.food_name);if(food===null)return;const calories=prompt("Calories",x.calories);if(calories===null)return;const protein=prompt("Protein (g)",x.protein_g);if(protein===null)return;const carbs=prompt("Carbs (g)",x.carbs_g);if(carbs===null)return;const fat=prompt("Fat (g)",x.fat_g);if(fat===null)return;await api(`/me/nutrition/entries/${x.id}`,{method:"PUT",body:JSON.stringify({entry_date:x.entry_date,meal_type:x.meal_type,food_name:food.trim()||x.food_name,calories:Math.max(0,+calories||0),protein_g:Math.max(0,+protein||0),carbs_g:Math.max(0,+carbs||0),fat_g:Math.max(0,+fat||0),source:x.source||null,source_url:x.source_url||null})});S.nutrition=null;await loadNutrition();toast("Food updated");});
document.querySelectorAll("[data-nutrition-quicklog]").forEach(b=>b.onclick=async()=>{await api(`/me/nutrition/saved-foods/${b.dataset.nutritionQuicklog}/quick-log`,{method:"POST",body:JSON.stringify({entry_date:nutritionDateValue(),meal_type:"Meal"})});S.nutrition=null;await loadNutrition();toast("Saved food logged");});
document.querySelectorAll("[data-notification-dismiss]").forEach(b=>b.onclick=async()=>{await api("/me/notifications/dismiss",{method:"POST",body:JSON.stringify({notification_key:b.dataset.notificationDismiss})});await loadNotifications()});
document.querySelectorAll("[data-pr-view]").forEach(b=>b.onclick=()=>{S.prView=b.dataset.prView;render();});
document.querySelectorAll("[data-pr-lift-filter]").forEach(b=>b.onclick=()=>{S.prLiftFilter=b.dataset.prLiftFilter;render();});
document.querySelectorAll("[data-body-range]").forEach(b=>b.onclick=()=>{S.bodyMetricRange=b.dataset.bodyRange;loadBodyMetrics()});
document.querySelectorAll("[data-body-delete]").forEach(b=>b.onclick=async()=>{if(confirm("Delete this body check-in?")){await api(`/me/body-metrics/${b.dataset.bodyDelete}`,{method:"DELETE"});await loadBodyMetrics();loadProgressIntelligence();toast("Check-in deleted")}});

document.querySelectorAll("[data-progress-coach]").forEach(b=>b.onclick=()=>{S.coachDraft=b.dataset.progressCoach;go("coach")});
document.querySelectorAll("[data-notification-coach]").forEach(b=>b.onclick=()=>{S.coachDraft=b.dataset.notificationCoach;go("coach")});
document.querySelectorAll("[data-notification-setting]").forEach(b=>b.onchange=async()=>{const body={};body[b.dataset.notificationSetting]=b.checked;await api("/me/notifications/settings",{method:"PUT",body:JSON.stringify(body)});await loadNotifications()});
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
document.querySelectorAll("[data-remove-custom]").forEach(b=>b.onclick=()=>{S.equipmentLog=S.equipmentLog.filter(x=>x.key!==b.dataset.removeCustom);render();});document.querySelectorAll("[data-pref]").forEach(b=>b.onclick=()=>toggleArr(profile.preferred_exercises,b.dataset.pref));document.querySelectorAll("[data-avoid]").forEach(b=>b.onclick=()=>toggleArr(profile.excluded_exercises,b.dataset.avoid));document.querySelectorAll("[data-w]").forEach(b=>b.onclick=()=>{S.wi=+b.dataset.w;go("workout")});document.querySelectorAll("[data-ex]").forEach(b=>b.onclick=async()=>{stopExerciseTimer();S.exerciseElapsed=0;S.exerciseTimerTarget=0;S.ei=+b.dataset.ex;S.set=0;await persistPosition();go("exercise")});document.querySelectorAll("[data-feel]").forEach(b=>b.onclick=()=>{S.feel=b.dataset.feel;render()});
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
if(S.route==="exercisehistory")loadExerciseHistory();
if(S.route==="calendarsettings"){if(!S.calendarStatus||!S.timeSettings)loadCalendarSettings();startLiveClock()}else stopLiveClock()}
function toggleArr(arr,v){const i=arr.indexOf(v);if(i>=0)arr.splice(i,1);else arr.push(v);render()}
function go(r){
  if(!S.restRemaining)stopTimer();S.route=r;render();scrollTo(0,0);
  if(r==="progress"){loadTrainingDashboard();loadTrainingRecords();loadProgressIntelligence();loadBodyMetrics();api("/me/modules/summary").then(x=>{S.moduleSummary=x;render()}).catch(()=>{});}
  if(r==="home"){loadHomeDashboard();loadNotifications();loadTrainingDashboard();}
  if(r==="notifications")loadNotifications();
  if((r==="home"||r==="plan")&&S.calendarStatus?.connected&&S.calendarStatus?.sync_enabled){
    syncCalendar({silent:true});
  }
}
async function generatePlan(){go("generating");try{if(!authToken)throw Error("Please sign in");await api("/me/profile",{method:"POST",body:JSON.stringify(profile)});plan=await api("/me/plan/generate",{method:"POST"});
if(S.calendarStatus?.connected&&S.calendarStatus?.sync_enabled)await syncCalendar({silent:true});
setTimeout(()=>go("yourplan"),800)}catch(e){toast(e.message);go("preferences")}}
async function startWorkout(){const ww=w();const s=await api(`/me/workout/${ww.workout_id}/start`,{method:"POST"});session={session_id:s.session_id};S.lastSessionId=s.session_id;S.sessionStartedAt=Date.now();S.completedWorkoutSummary=null;S.ei=0;S.set=0;S.workoutPRs=[];await persistPosition();go("workout")}
async function saveSet(){
  if(!session)await startWorkout();
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
  const result=await api("/me/performance",{method:"POST",body:JSON.stringify(payload)});
  S.exerciseRecall=null;S.exerciseRecallExerciseId=null;S.exerciseRecallLoading=false;S.exerciseProgression=null;S.exerciseProgressionExerciseId=null;S.exerciseProgressionLoading=false;
  S.sessionIntelligence=result.session_intelligence||null;
  if(S.sessionIntelligence){
    const si=S.sessionIntelligence;
    const rest=si.recommended_rest_seconds?` • Rest ${Math.round(si.recommended_rest_seconds)}s`:"";
    const volume=si.recommended_total_sets!==si.planned_sets?` • ${si.recommended_total_sets} sets today`:"";
    S.liveAdjustment={title:si.title||"Session adjustment",detail:`${si.reason||"Forge adjusted the session from your latest set."}${rest}${volume}`};
    if(Number.isFinite(Number(si.recommended_total_sets))&&Number(si.recommended_total_sets)>=Number(si.completed_sets||0))e.sets=Number(si.recommended_total_sets);
  }else if(result.next_target){const t=result.next_target;const target=t.load_mode==="timed"?`${t.suggested_duration_seconds}s`:t.load_mode==="bodyweight"?`${t.suggested_reps} reps`:`${Number(t.suggested_weight||0).toFixed(1).replace(/\.0$/,'')} lb × ${t.suggested_reps||e.min_reps}`;S.liveAdjustment={title:`Next target: ${target}`,detail:t.reason||"Forge adjusted the next target from your latest set."};} else if(rpe>=9)S.liveAdjustment={title:"Protect the next sets",detail:"That set was very hard. Hold the load, stay inside the rep target, and stop the set before technique breaks."}; else if(rpe<=6)S.liveAdjustment={title:"You have room today",detail:"That set moved easily. Keep the programmed reps; if the next set is equally clean, Forge will have strong evidence for progression."}; else S.liveAdjustment=null;
  if(result.pr_events?.length){S.workoutPRs.push(...result.pr_events);toast(`🏆 ${result.pr_events[0].label}: ${result.pr_events[0].exercise_name}`)}
  S.exerciseElapsed=0;stopExerciseTimer();
  S.set++;
  if(S.set>=e.sets){
    S.set=0;S.ei++;
    if(S.ei>=w().exercises.length){
      await persistPosition();await api("/me/workout/complete",{method:"POST",body:JSON.stringify({session_id:session.session_id,completed:true})});
      S.lastSessionId=session.session_id;plan=await api("/me/plan/current");session=null;S.ei=0;S.set=0;go("complete");loadCompletedWorkoutSummary();
    }else{await persistPosition();await beginPersistentRest(Number(S.sessionIntelligence?.recommended_rest_seconds||e.rest_seconds||60))}
  }else{await persistPosition();await beginPersistentRest(Number(S.sessionIntelligence?.recommended_rest_seconds||e.rest_seconds||60))}
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
    if(a==="repeat-last-set"){const last=(S.exerciseRecall?.sets||[]).at(-1);if(last){const weight=document.querySelector("#weight"),reps=document.querySelector("#reps"),rpe=document.querySelector("#rpe");if(weight&&last.weight!=null)weight.value=last.weight;if(reps&&last.reps!=null)reps.value=last.reps;if(rpe&&last.rpe!=null)rpe.value=last.rpe;toast("Last set copied")}return}
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
    if(a==="open-notifications"){S.route="notifications";await loadNotifications();render();return;}
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
document.querySelector("#moreBtn").onclick=()=>{if(authToken){S.moreOpen=!S.moreOpen;render()}else toast("Forge Fitness v14.61.0")};
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
        toast(calendarSyncWarning?"Google Calendar connected — initial sync needs attention":"Google Calendar connected");
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

// v14.39.0: keep current-week form media warm without blocking the workout UI.
window.addEventListener("online",()=>{if(authToken&&plan)cacheCurrentPlanDemos(true)});
