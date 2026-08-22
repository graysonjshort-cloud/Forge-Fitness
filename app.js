
const API = localStorage.getItem("forge_api_url") || (
  location.protocol==="https:" ? location.origin : `http://${location.hostname}:8000`
);
let authToken = localStorage.getItem("forge_auth_token") || "";
let account = null;
let plan = null, session = null;
const profile = {goal:"build_muscle",experience:"intermediate",days_per_week:4,minutes_per_workout:45,equipment:["full_gym"],preferred_exercises:[],excluded_exercises:[],priority_muscles:[],recovery_level:"normal",cardio_preference:"moderate",workout_split:"auto",sport:"general",core_workouts_per_week:2,cardio_workouts_per_week:2,seed:42};
const S={route:"welcome",onboardStep:0,wi:0,ei:0,set:0,restRemaining:0,restTotal:0,timer:null,feel:"Just Right",name:"Athlete",coachDraft:"",startupError:null,historyExercise:null,workoutPRs:[],exerciseRecall:null,swapOptions:[],coachMessages:[],coachAction:null,coachContext:null,coachLoaded:false,coachStatus:null,strengthTrend:null,strengthExercise:"overall",strengthRange:"90",strengthPoint:null,planTab:"overview",equipmentCatalog:[],equipmentPresets:{},equipmentLog:[],equipmentLoaded:false,equipmentReturn:"onboarding",equipmentSearch:"",equipmentCategory:"All",equipmentSelectedOnly:false,equipmentEditKey:null,exerciseDirectory:null,exerciseDirectorySearch:"",exerciseDirectoryMuscle:"All",exerciseDirectoryDifficulty:"All",exerciseDirectoryCompatible:true,exerciseDirectorySelected:null,lastSessionId:null,preferenceReturn:"preferences",timeSettings:null,calendarStatus:null,clockTimer:null,calendarPollTimer:null,cardioSwapOptions:[],selectedCardioSwap:null,nutrition:null,nutritionDate:null,nutritionEditingTargets:false,nutritionSavedFoods:[],nutritionEditEntry:null,nutritionCoachSummary:null,notifications:null,notificationSettings:null,progressIntelligence:null,bodyMetrics:null,bodyMetricRange:"90",bodyMetricModal:false,prRecords:[],prView:"exercise",prLiftFilter:"all",prCollapsedGroups:{},homeDashboard:null,adaptationPreview:null,adaptationBusy:false,pwaInstallPrompt:null,pwaInstalled:false,pwaDismissed:false};
const V=document.querySelector("#view"),toastEl=document.querySelector("#toast"),nav=document.querySelector("#bottomNav"),topbar=document.querySelector("#topbar");
const toast=t=>{toastEl.textContent=t;toastEl.classList.add("show");setTimeout(()=>toastEl.classList.remove("show"),1800)};
const esc=s=>String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]));

function isStandalonePWA(){
  return window.matchMedia?.("(display-mode: standalone)")?.matches || window.navigator.standalone===true;
}
function isIOSDevice(){
  return /iphone|ipad|ipod/i.test(navigator.userAgent||"");
}
function pwaInstallCard(){
  if(isStandalonePWA()||S.pwaInstalled)return `<div class="card pwa-install-card installed"><div class=pwa-install-icon>✓</div><div><p class=eyebrow>PHONE APP</p><h3>Forge is installed</h3><p class=muted>Forge is running as a standalone home-screen app.</p></div></div>`;
  if(isIOSDevice())return `<div class="card pwa-install-card apple-pwa-card"><div class=pwa-install-icon></div><div><p class=eyebrow>IPHONE / IPAD</p><h3>Install Forge on Apple</h3><p class=muted>Open Forge in Safari, tap <b>Share</b>, choose <b>Add to Home Screen</b>, turn on <b>Open as Web App</b>, then tap <b>Add</b>.</p><div class=apple-install-steps><span>1</span><b>Share</b><span>2</span><b>Add to Home Screen</b><span>3</span><b>Open as Web App</b></div></div></div>`;
  if(S.pwaInstallPrompt)return `<div class="card pwa-install-card"><div class=pwa-install-icon>⌂</div><div><p class=eyebrow>ANDROID APP</p><h3>Install Forge</h3><p class=muted>Add Forge to your home screen and open it like a normal app.</p><button class=btn data-a=pwa-install>Install Forge</button></div></div>`;
  return `<div class="card pwa-install-card"><div class=pwa-install-icon>⌂</div><div><p class=eyebrow>PHONE APP</p><h3>Install Forge</h3><p class=muted>Use your browser's Install app option. On iPhone/iPad, use Safari → Share → Add to Home Screen.</p></div></div>`;
}
async function installForgePWA(){
  const prompt=S.pwaInstallPrompt;
  if(!prompt){toast(isIOSDevice()?"Use Safari Share → Add to Home Screen":"Install option is not available in this browser yet");return;}
  prompt.prompt();
  const choice=await prompt.userChoice.catch(()=>({outcome:"dismissed"}));
  if(choice.outcome==="accepted")toast("Forge installation started");
  S.pwaInstallPrompt=null;
  render();
}
function setupPWA(){
  S.pwaInstalled=isStandalonePWA();
  document.documentElement.classList.toggle("ios-device",isIOSDevice());
  document.documentElement.classList.toggle("standalone-pwa",isStandalonePWA());
  window.addEventListener("beforeinstallprompt",event=>{
    event.preventDefault();
    S.pwaInstallPrompt=event;
    if(S.route==="trainingsettings")render();
  });
  window.addEventListener("appinstalled",()=>{
    S.pwaInstalled=true;S.pwaInstallPrompt=null;toast("Forge installed");
    if(S.route==="trainingsettings")render();
  });
  if("serviceWorker" in navigator){
    navigator.serviceWorker.register("/sw.js",{scope:"/"}).catch(err=>console.warn("Forge service worker registration failed",err));
  }
}


function equipmentIcon(key,name="",category=""){
  key=String(key||"").toLowerCase().replace(/[^a-z0-9_]/g,"");
  const known=new Set([
    "dumbbells",
    "barbell",
    "ez_curl_bar",
    "trap_bar",
    "weight_plates",
    "kettlebells",
    "medicine_ball",
    "bench",
    "adjustable_bench",
    "squat_rack",
    "power_rack",
    "preacher_bench",
    "dip_station",
    "pull_up_bar",
    "cable_machine",
    "lat_pulldown",
    "seated_row_machine",
    "chest_press_machine",
    "shoulder_press_machine",
    "leg_press_machine",
    "leg_extension_machine",
    "leg_curl_machine",
    "pec_deck",
    "calf_raise_machine",
    "smith_machine",
    "machine",
    "rope_attachment",
    "straight_bar_attachment",
    "lat_bar_attachment",
    "ankle_strap",
    "bands",
    "ab_wheel",
    "foam_roller",
    "yoga_mat",
    "stability_ball",
    "landmine_attachment",
    "bodyweight",
    "rings",
    "suspension_trainer",
    "treadmill",
    "bike",
    "rowing_machine",
    "elliptical",
    "stair_climber",
    "jump_rope",
    "sled",
    "safety_squat_bar",
    "swiss_bar",
    "cambered_bar",
    "axle_bar",
    "fixed_barbells",
    "sandbag",
    "weighted_vest",
    "clubs_maces",
    "deadlift_platform",
    "half_rack",
    "wall_rack",
    "glute_ham_developer",
    "roman_chair",
    "hyperextension_bench",
    "decline_bench",
    "hack_squat_machine",
    "pendulum_squat",
    "belt_squat_machine",
    "v_squat_machine",
    "hip_thrust_machine",
    "hip_abductor_machine",
    "hip_adductor_machine",
    "standing_leg_curl",
    "lying_leg_curl",
    "seated_leg_curl",
    "donkey_calf_machine",
    "tibialis_machine",
    "incline_press_machine",
    "decline_press_machine",
    "chest_supported_row_machine",
    "high_row_machine",
    "pullover_machine",
    "lateral_raise_machine",
    "rear_delt_machine",
    "biceps_curl_machine",
    "triceps_extension_machine",
    "assisted_dip_pullup",
    "v_bar_attachment",
    "single_d_handle",
    "triceps_v_bar",
    "multi_grip_lat_bar",
    "lifting_belt",
    "lifting_straps",
    "wrist_wraps",
    "knee_sleeves",
    "dip_belt",
    "fractional_plates",
    "barbell_collars",
    "blocks",
    "plyo_box",
    "parallettes",
    "pushup_handles",
    "climbing_rope",
    "monkey_bars",
    "air_bike",
    "spin_bike",
    "recumbent_bike",
    "ski_erg",
    "arc_trainer",
    "stepmill",
    "curved_treadmill",
  ]);
  const asset=known.has(key)?key:"generic";
  return `<img class="equipment-image" src="assets/equipment/${asset}.svg" alt="" aria-hidden="true" loading="lazy" onerror="this.onerror=null;this.src='assets/equipment/generic.svg'">`;
}

const w=()=>plan?.workouts?.[S.wi]||null;
async function api(path,opt={}){
  const headers={"Content-Type":"application/json",...(opt.headers||{})};
  if(authToken)headers["Authorization"]=`Bearer ${authToken}`;
  const r=await fetch(API+path,{...opt,headers});
  let d={};try{d=await r.json()}catch{}
  if(!r.ok)throw Error(d.detail||`Request failed (${r.status})`);
  return d;
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
    if(new URLSearchParams(location.search).get("return_to")==="calendar"&&plan)S.route="calendarsettings";
    if(plan)await restoreSession();
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
      if(remain>0){S.restRemaining=remain;S.restTotal=Number(s.rest_duration_seconds);S.route="timer";return;}
      try{await api("/me/session/rest/clear",{method:"POST",body:JSON.stringify({session_id:s.session_id})})}catch{}
    }
    S.route="exercise";
  }catch(e){console.warn("Session restore failed",e)}
}
async function persistPosition(){
  if(!session)return;
  try{await api("/me/session/position",{method:"POST",body:JSON.stringify({session_id:session.session_id,exercise_index:S.ei,set_index:S.set})})}catch(e){console.warn(e)}
}
function requestId(){return globalThis.crypto?.randomUUID?crypto.randomUUID():`${Date.now()}-${Math.random()}`}
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
    if(S.route==="calendarsettings")render();
  }catch(e){console.warn("Calendar settings load failed",e)}
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
<div class=spacer></div><div class="center muted">or</div><div class=spacer></div><button class="btn dark" data-a=google-mock>G&nbsp; Continue with Google</button>
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
return `${dots(2)}<h2>How many days?</h2><p class=muted>How many days per week can you train?</p><div class=big-spacer></div><div class=choice-grid>${[2,3,4,5,6].map(n=>`<button class="choice-tile ${profile.days_per_week===n?"selected":""}" data-days=${n}><span><b>${n} Days</b><small>${n===2?"Minimal":n===3?"Recommended":n===4?"Balanced":"High frequency"}</small></span></button>`).join("")}</div><div class=big-spacer></div><p class=eyebrow>SESSION LENGTH</p><div class=chips>${[20,30,45,60,90].map(n=>`<button class="chip ${profile.minutes_per_workout===n?"selected":""}" data-mins=${n}>${n} min</button>`).join("")}</div><div class=big-spacer></div><button class=btn data-a=next>Next</button>`;
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
  if(S.exerciseDirectoryCompatible)params.set("compatible_only","true");
  params.set("limit","300");
  try{
    S.exerciseDirectory=await api(`/me/exercises?${params.toString()}`);
    if(S.route==="exercisedirectory")render();
  }catch(e){toast(e.message)}
}

function exercisedirectory(){
const d=S.exerciseDirectory,rows=d?.exercises||[],filters=d?.filters||{};
return `<p class=eyebrow>LIBRARY</p><div class=row><div><h2>Exercise Directory</h2><p class=muted>${d?`${d.directory_total} exercises available`:"Loading exercises..."}</p></div><span>▤</span></div>
<div class=big-spacer></div>
<input id=exerciseDirectorySearch class=directory-search value="${esc(S.exerciseDirectorySearch)}" placeholder="Search exercises, muscles, equipment...">
<div class=directory-filter-row>
<select id=directoryMuscle><option>All</option>${(filters.muscles||[]).map(x=>`<option ${S.exerciseDirectoryMuscle===x?"selected":""}>${esc(x)}</option>`).join("")}</select>
<select id=directoryDifficulty><option>All</option>${(filters.difficulties||[]).map(x=>`<option ${S.exerciseDirectoryDifficulty===x?"selected":""}>${esc(x)}</option>`).join("")}</select>
<button class="${S.exerciseDirectoryCompatible?"active":""}" data-a=directory-compatible>${S.exerciseDirectoryCompatible?"My Equipment":"All Equipment"}</button>
</div>
<div class=spacer></div>
<p class=muted>${d?`${rows.length} matching exercise${rows.length===1?"":"s"}`:""}</p>
<div class=directory-list>${rows.map(e=>`<button class="directory-card ${e.equipment_compatible?"":"incompatible"}" data-directory-exercise=${e.id}>
<div class=row><div><p class=eyebrow>${esc(e.primary_muscle)}</p><h3>${esc(e.name)}</h3></div><span>›</span></div>
<p class=muted>${esc(e.equipment)} • ${esc(e.difficulty)} • ${e.min_reps}-${e.max_reps} reps</p>
<div class=directory-tags><span>${esc(e.movement_pattern)}</span><span>${esc(e.exercise_type)}</span>${e.beginner_suitable?"<span>Beginner Friendly</span>":""}</div>
</button>`).join("")||'<div class=card><p class=muted>No exercises match these filters.</p></div>'}</div>`;
}

function exercisedetail(){
const e=S.exerciseDirectorySelected;
if(!e)return `<h2>Exercise</h2><p class=muted>Select an exercise from the directory.</p>`;
return `<p class=eyebrow>EXERCISE</p><h2>${esc(e.name)}</h2><p class=muted>${esc(e.primary_muscle)} • ${esc(e.difficulty)}</p>
<div class=big-spacer></div>
<div class=exercise-directory-hero><div>🏋️</div><span>${e.equipment_compatible?"✓ Works with your equipment":"Not currently compatible with your equipment log"}</span></div>
<div class=spacer></div>
<div class=exercise-directory-facts>
<div><small>Sets</small><b>${e.default_sets}</b></div>
<div><small>Rep Range</small><b>${e.min_reps}-${e.max_reps}</b></div>
<div><small>Rest</small><b>${e.default_rest_seconds}s</b></div>
<div><small>Type</small><b>${esc(e.exercise_type)}</b></div>
</div>
<div class=big-spacer></div>
<div class=card><p class=eyebrow>TARGETS</p><h3>${esc(e.primary_muscle)}</h3><p class=muted>${e.secondary_muscles?`Also works: ${esc(e.secondary_muscles)}`:"Primary target exercise"}</p></div>
<div class=spacer></div>
<div class=card><p class=eyebrow>MOVEMENT</p><h3>${esc(e.movement_pattern)}</h3><p class=muted>${esc(e.equipment)} • ${esc(e.progression_method)}</p>${e.notes?`<p class=muted>${esc(e.notes)}</p>`:""}</div>
<div class=big-spacer></div><button class="btn dark" data-a=directory-history>View My History</button>`;
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
const SPLIT_OPTIONS=[["auto","Forge Recommended","Automatically choose for your schedule"],["full_body","Full Body","Train the whole body each workout"],["upper_lower","Upper / Lower","Alternate upper- and lower-body days"],["push_pull_legs","Push / Pull / Legs","Separate pushing, pulling, and leg training"],["body_part","Body Part Split","Focus on fewer muscle groups each day"],["hybrid","Hybrid","Mix full-body and focused sessions"]];
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
function splitpicker(){const allowed=SPLIT_OPTIONS.filter(x=>splitAllowed(x[0]));return `<p class=eyebrow>WORKOUT SPLIT</p><h2>Choose your training split</h2><p class=muted>Forge will build your weekly plan around this structure. You can change it later in Settings.</p><div class=big-spacer></div><div class=preference-list>${allowed.map(([v,n,d])=>`<button class="pref-row ${profile.workout_split===v?"selected":""}" data-split="${v}"><span><strong>${n}</strong><small class=muted style="display:block">${d}</small></span><span>${profile.workout_split===v?"✓":"›"}</span></button>`).join("")}</div><div class=big-spacer></div><button class=btn data-a=pref-done>Done</button>`}
function splitAllowed(v){if(v==="push_pull_legs")return profile.days_per_week>=3;if(v==="upper_lower")return profile.days_per_week>=2;return true}
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
    const [nutrition,intelligence]=await Promise.all([
      api(`/me/nutrition?date=${encodeURIComponent(forgeLocalDate())}`),
      api("/me/progress/intelligence")
    ]);
    S.homeDashboard={nutrition,intelligence};
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
  const workouts=plan?.workouts||[];
  const done=workouts.filter(x=>x.status==="completed").length;
  const adherence=S.progressIntelligence?.metrics?.adherence_percent;
  const muscles={};
  workouts.forEach(w=>(w.exercises||[]).forEach(e=>{const m=e.primary_muscle||"Other";muscles[m]=(muscles[m]||0)+Number(e.sets||0)}));
  const top=Object.entries(muscles).sort((a,b)=>b[1]-a[1]).slice(0,5),max=top[0]?.[1]||1;
  return `<div class=progress-visual-grid>
    <div class="card progress-consistency-card"><p class=eyebrow>CONSISTENCY</p><div class=consistency-value><b>${adherence==null?"—":Math.round(adherence)+"%"}</b><span>${done}/${workouts.length||0} current-plan workouts complete</span></div><div class=consistency-track><i style="width:${adherence==null?0:Math.min(100,adherence)}%"></i></div></div>
    <div class="card muscle-volume-card"><p class=eyebrow>WEEKLY MUSCLE VOLUME</p>${top.length?top.map(([m,s])=>`<div class=volume-row><span>${esc(m)}</span><b>${s} sets</b><i><u style="width:${Math.round(s/max*100)}%"></u></i></div>`).join(""):`<div class=polished-empty><b>Volume appears after your plan is built</b><span>Forge will summarize weekly set distribution here.</span></div>`}</div>
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
${S.notifications?.items?.length?`<div class=spacer></div><div class="card proactive-home-card"><div class=row><div><p class=eyebrow>FORGE COACH</p><h3>${esc(S.notifications.items[0].title)}</h3></div><button class="btn dark compact" data-a=open-notifications>View</button></div><p class=muted>${esc(S.notifications.items[0].message)}</p></div>`:""}
<div class=big-spacer></div><div class=row><h3>This Week</h3><div class=home-progress-ring style="background:conic-gradient(var(--red) 0 ${pct}%,#20252b ${pct}% 100%)"><b>${pct}%</b></div></div>
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
function workout(){
const ww=w();if(!ww)return home();
const current=ww.exercises[Math.min(S.ei,ww.exercises.length-1)];
const completedExerciseCount=session?Math.min(S.ei,ww.exercises.length):0;
const workoutPct=Math.round(completedExerciseCount/Math.max(1,ww.exercises.length)*100);
return `<div class=workout-head><div><p class=eyebrow>${session?"WORKOUT IN PROGRESS":"TODAY'S SESSION"}</p><h2>${esc(ww.name)}</h2><p class=muted>${ww.exercises.length} exercises • ${ww.estimated_minutes||profile.minutes_per_workout} min</p></div><span class=workout-percent>${workoutPct}%</span></div>
<div class=workout-progress-track><i style="width:${workoutPct}%"></i></div>
${session&&current?`<div class="card active-exercise-card"><div class=row><div><small>CURRENT EXERCISE</small><h2>${esc(current.name)}</h2><p>${current.sets} sets • ${current.min_reps}-${current.max_reps} reps • ${current.rest_seconds||60}s rest</p></div><span class=active-set-badge>Set ${S.set+1}</span></div><button class=btn data-a=openexercise>Continue Logging</button></div>`:""}
<div class=section-heading><div><p class=eyebrow>EXERCISE LIST</p><h3>${session?"Session roadmap":"What you’ll do"}</h3></div></div>
<div class=exercise-list>${ww.exercises.map((e,i)=>`<button class="exercise-item ${i===S.ei?"selected":""} ${session&&i<S.ei?"exercise-done":""}" data-ex=${i}><span class=exercise-num>${session&&i<S.ei?"✓":i+1}</span><span><strong>${esc(e.name)}</strong><small>${e.sets} sets • ${e.min_reps}-${e.max_reps} reps • ${e.primary_muscle||"Strength"}</small></span><span>›</span></button>`).join("")}</div>
${ww.cardio_included?`<div class=spacer></div><div class=card><div class=row><div><p class=eyebrow>CARDIO FINISHER</p><h3>${esc(ww.cardio_name||"Cardio")}</h3></div><button class="btn dark compact" data-a=swap-cardio>Swap</button></div><p class=muted>${ww.cardio_minutes||15} min • ${cardioLabel(ww.cardio_intensity||profile.cardio_preference)} intensity</p></div>`:""}
<div class=big-spacer></div>${session?`<button class="btn dark" data-a=abandon>End Workout Early</button>`:`<button class=btn data-a=startworkout>Start Workout</button>`}`;
}

function exercise(){
const e=w().exercises[S.ei],setPct=Math.round((S.set)/Math.max(1,e.sets)*100);
return `<div class=exercise-session-top><div><p class=eyebrow>${esc(w().name)}</p><h2>${esc(e.name)}</h2><p class=muted>Set ${S.set+1} of ${e.sets} • Target ${e.min_reps}-${e.max_reps} reps</p></div><span class=set-progress-pill>${setPct}%</span></div>
<div class=workout-progress-track><i style="width:${setPct}%"></i></div>
<div class=spacer></div><div id=recallCard class="card previous-performance-card"><p class=eyebrow>PREVIOUS PERFORMANCE</p><p class=muted>Loading your last performance and next target...</p></div>
<div class=big-spacer></div>
<div class=log-panel><div class=log-panel-head><h3>Log Set ${S.set+1}</h3><span>${e.rest_seconds||60}s rest after</span></div>
<div class=logging-grid>
<div class=logging-row><label for=weight>Weight <small>lb</small></label><input class=log-input id=weight type=number inputmode=decimal min=0 step=2.5 placeholder="0" autocomplete=off></div>
<div class=logging-row><label for=reps>Reps</label><input class=log-input id=reps type=number inputmode=numeric min=0 step=1 value="${e.min_reps}" autocomplete=off></div>
</div>
<div class=effort-section><div class=effort-heading><strong>Effort / RIR</strong><small>How many good reps were left?</small></div>
<div class=effort-options>
<button type=button class=effort-choice data-rpe=6><b>Easy</b><small>4+ left</small></button>
<button type=button class="effort-choice selected" data-rpe=7><b>Moderate</b><small>~3 left</small></button>
<button type=button class=effort-choice data-rpe=8><b>Hard</b><small>~2 left</small></button>
<button type=button class=effort-choice data-rpe=9><b>Very Hard</b><small>~1 left</small></button>
<button type=button class=effort-choice data-rpe=10><b>Limit</b><small>0 left</small></button>
</div><input id=rpe type=hidden value="7"></div>
<div class=exercise-actions><button class=btn data-a=completeset>Complete Set</button><button class="btn dark" data-a=swap-exercise>Swap Exercise</button><button class="text-action skip-set-action" data-a=skip-set>Skip this set</button></div></div>`;
}

function timer(){
const t=S.restRemaining||w().exercises[S.ei].rest_seconds||60,mm=String(Math.floor(t/60)).padStart(2,"0"),ss=String(t%60).padStart(2,"0"),e=w().exercises[S.ei];
return `<div class=center><p class=eyebrow>RECOVERY BETWEEN SETS</p><h2>Rest Timer</h2><p class=muted>Next: ${esc(e.name)} • Set ${S.set+1} of ${e.sets}</p><div class=ring><div><strong id=restClock>${mm}:${ss}</strong><span class=muted>Remaining</span></div></div><div class=timer-actions><button data-addrest=30>+30s</button><button data-addrest=60>+1m</button><button data-a=skiprest>Skip</button></div><div class=big-spacer></div><button class=btn data-a=skiprest>Start Next Set</button><div class=spacer></div><button class="btn dark" data-a=view-workout-rest>View Workout While Resting</button></div>`;
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
    el.innerHTML=S.cardioSwapOptions.map(x=>`<button class="card swap-option ${x.name===w()?.cardio_name?"selected":""}" data-cardio-swap=${x.id}>
      <div class=row><div><p class=eyebrow>${esc(x.movement_pattern)}</p><h3>${esc(x.name)}</h3><p class=muted>${esc(x.equipment)}</p></div><span>${x.name===w()?.cardio_name?"Current":"›"}</span></div>
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
return `<p class=eyebrow>SWAP EXERCISE</p><h2>Swap Exercise</h2><input class=swap-search placeholder="Search exercises"><p class=eyebrow>BEST MATCHES</p><div class=spacer></div><div id=swapList class=stack><div class=card><p class=muted>Loading substitutions…</p></div></div><div class=big-spacer></div><div class=row><button class="btn dark" style="width:48%" data-a=back-exercise>Cancel</button><button class=btn style="width:48%" data-a=swap-selected>Swap</button></div>`;
}

async function loadSwapOptions(){
  try{
    const e=w()?.exercises?.[S.ei];if(!e)return;
    const rows=await api(`/me/exercises/${e.exercise_id}/substitutions`);
    S.swapOptions=rows;S.selectedSwap=null;
    const el=document.querySelector("#swapList");if(!el)return;
    const compatible=rows.filter(x=>x.equipment_compatible);
    if(!compatible.length){el.innerHTML=`<div class=card><p class=muted>No compatible substitutions found for your equipment.</p></div>`;return}
    el.innerHTML=compatible.map(x=>`<button class="card swap-option" data-swap=${x.id}>
      <div class=row><div><p class=eyebrow>${esc(x.primary_muscle)}</p><h3>${esc(x.name)}</h3>
      <p class=muted>${esc(x.equipment)} • ${x.min_reps}-${x.max_reps} reps</p></div><span>›</span></div></button>`).join("");
    document.querySelectorAll("[data-swap]").forEach(b=>b.onclick=()=>{S.selectedSwap=Number(b.dataset.swap);document.querySelectorAll("[data-swap]").forEach(x=>x.classList.toggle("selected",x===b))});
  }catch(e){toast(e.message)}
}
async function applySwap(newId){
  const old=w().exercises[S.ei];
  await api(`/me/workouts/${w().workout_id}/swap`,{method:"POST",body:JSON.stringify({
    old_exercise_id:old.exercise_id,new_exercise_id:newId
  })});
  plan=await api("/me/plan/current");S.adaptationPreview=null;
  toast("Exercise swapped");
  go("exercise");
}

function timer(){
const t=S.restRemaining||w().exercises[S.ei].rest_seconds||60,mm=String(Math.floor(t/60)).padStart(2,"0"),ss=String(t%60).padStart(2,"0"),e=w().exercises[S.ei];
return `<div class=center><h2>Rest Timer</h2><p class=muted>Next Set<br>${esc(e.name)}<br>Set ${S.set+1} of ${e.sets}</p><div class=ring><div><strong id=restClock>${mm}:${ss}</strong><span class=muted>Remaining</span></div></div><div class=timer-actions><button data-addrest=30>+30s</button><button data-addrest=60>+1m</button><button data-a=skiprest>Skip</button></div><div class=big-spacer></div><button class=btn data-a=skiprest>End Rest</button></div>`;
}

function complete(){
const prs=S.workoutPRs||[],unique=[],seen=new Set();for(const pr of prs){const k=`${pr.exercise_name}|${pr.type}`;if(!seen.has(k)){seen.add(k);unique.push(pr)}}
return `<div class=center><div class=complete-shield>💪</div><h2>Great work, ${esc(S.name)}!</h2><p class=muted>${esc(w()?.name||"Workout")}</p><div class=spacer></div><div class=metrics><div class=metric><strong>${w()?.exercises?.length||0}</strong><span>Exercises</span></div><div class=metric><strong>${w()?.exercises?.reduce((a,e)=>a+e.sets,0)||0}</strong><span>Total Sets</span></div><div class=metric><strong>${unique.length}</strong><span>New PRs</span></div></div>${unique.length?`<div class=spacer></div>${unique.slice(0,3).map(pr=>`<div class=pr-card><p class=eyebrow>🏆 ${esc(pr.label)}</p><h3>${esc(pr.exercise_name)}</h3><strong>${pr.value} ${esc(pr.unit)}</strong></div>`).join("")}`:""}<div class=big-spacer></div><p>How was this workout?</p><div class=spacer></div><div class=feelings>${[["😟","Too Hard"],["😡","Hard"],["🙂","Just Right"],["😎","Easy"],["🔥","Too Easy"]].map(x=>`<button class="feel ${S.feel===x[1]?"selected":""}" data-feel="${x[1]}"><span>${x[0]}</span>${x[1]}</button>`).join("")}</div><div class=big-spacer></div><button class=btn data-a=finish>Finish</button></div>`;
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
<div class=big-spacer></div><div class=row><h3>Meals</h3><button class="btn dark compact" data-a=nutrition-targets>Targets</button></div><div class=spacer></div>
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


async function loadExerciseRecall(){
  try{
    const e=w()?.exercises?.[S.ei];
    if(!e)return;
    const data=await api(`/me/exercises/${e.exercise_id}/history`);
    S.exerciseRecall=data;
    const sets=data.sets||[];
    const last=sets.length?sets[sets.length-1]:null;
    const suggestion=data.progression_suggestion;
    const weight=document.querySelector("#weight");
    const reps=document.querySelector("#reps");
    const rpe=document.querySelector("#rpe");
    if(last){
      if(weight)weight.value=last.weight;
      if(reps)reps.value=last.reps;
      if(rpe&&last.rpe!=null)rpe.value=last.rpe;
    }
    const card=document.querySelector("#recallCard");
    if(card){
      if(!last){
        card.innerHTML=`<p class=eyebrow>FIRST SESSION</p><h3>No previous sets yet</h3><p class=muted>Log this exercise and Forge will remember it next time.</p>`;
      }else{
        const action=suggestion?suggestion.action.replaceAll("_"," "):"repeat";
        const recent=sets.slice(-4).reverse();
        card.innerHTML=`<div class=row><div><p class=eyebrow>LAST TIME</p><h3>${last.weight} lb × ${last.reps}</h3><p class=muted>RPE ${last.rpe??"—"}</p></div>
          <div style="text-align:right"><p class=eyebrow>NEXT TARGET</p><h3>${suggestion?suggestion.suggested_weight:last.weight} lb</h3><p class=muted>${action}</p></div></div>
          <div class=previous-set-strip>${recent.map((s,i)=>`<span class="${i===0?"latest":""}"><b>${Number(s.weight||0).toFixed(1).replace(/\.0$/,"")} lb × ${s.reps}</b><small>RPE ${s.rpe??"—"}</small></span>`).join("")}</div>`;
      }
    }
  }catch(e){
    const card=document.querySelector("#recallCard");
    if(card)card.innerHTML=`<p class=eyebrow>TRAINING HISTORY</p><p class=muted>No previous data available yet.</p>`;
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
<p class=muted>Estimated 1RM ${Number(r.best_e1rm||0).toFixed(1).replace(/\.0$/,"")} lb • Best reps ${r.best_reps}</p></div><span>›</span></div></button>`).join("");
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

function progress(){
const done=(plan?.workouts||[]).filter(x=>x.status==="completed").length;
const t=S.strengthTrend;
const summary=t?.summary||{};
const change=Number(summary.change_percent||0);
const changeText=(change>0?"+":"")+change.toFixed(1)+"%";
return `<p class=eyebrow>PROGRESS</p><h2>Your Progress</h2>
<div class=spacer></div><div class=progress-cards>
  <div class=progress-card><b>${done}</b><small>Workouts</small></div>
  <div class=progress-card><b>${summary.data_points||0}</b><small>Trend Points</small></div>
  <div class=progress-card><b class="${change>=0?"trend-positive":"trend-negative"}">${t?changeText:"—"}</b><small>Strength Progress</small></div>
</div>
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

function coach(){
const msgs=S.coachMessages||[],c=S.coachContext;
return `<div class=row><div><p class=eyebrow>FORGE COACH</p><h2>AI Coach</h2></div><button class="btn dark compact" data-a=clear-coach>Clear</button></div>
<p class=muted>Your training assistant, grounded in your Forge data.</p>
<div class="coach-model-status ${S.coachStatus?.llm_enabled?"online":"fallback"}"><span>${S.coachStatus?.llm_enabled?"● AI online":"● Smart fallback"}</span><small>${S.coachStatus?.llm_enabled?esc(S.coachStatus.model||"OpenAI"):"Set OPENAI_API_KEY to enable the LLM"}</small></div>
${c?`<div class=spacer></div><div class=coach-context><div><b>${c.recent_completed_workouts}</b><small>Recent Workouts</small></div><div><b>${Number(c.fatigue_score||0).toFixed(1)}</b><small>Fatigue</small></div><div><b>${c.week_number||1}</b><small>Week</small></div></div>`:""}
<div class=spacer></div>
<div class=coach-action-launcher>
  <button data-coachprompt="Review my readiness and adjust today's workout if needed"><span>⚙</span><b>Adjust Today</b><small>Use recovery + recent training</small></button>
  <button data-coachprompt="Find the best exercise swap for my current workout using only my equipment"><span>⇄</span><b>Smart Swap</b><small>Equipment-aware replacement</small></button>
  <button data-coachprompt="Check my calendar availability and help me place my workouts this week"><span>▦</span><b>Calendar Fit</b><small>Work around busy time</small></button>
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
function adaptationCard(){
  const a=S.adaptationPreview;
  if(!a)return `<div class="card adaptation-card"><p class=eyebrow>ADAPTIVE PROGRAMMING</p><h3>Analyzing your week…</h3><p class=muted>Forge is checking completion, recovery, strength trend, and recent effort.</p></div>`;
  const pct=Math.round(Number(a.completion_rate||0)*100);
  return `<div class="card adaptation-card ${a.recommendation}">
    <div class=row><div><p class=eyebrow>NEXT-WEEK ADAPTATION</p><h3>${esc(a.title)}</h3></div><span class=adaptation-badge>${esc(a.recommendation.toUpperCase())}</span></div>
    <p class=muted>${esc(a.reason)}</p>
    <div class=adaptation-metrics>
      <div><small>Completion</small><b>${pct}%</b></div>
      <div><small>Fatigue</small><b>${Number(a.fatigue_score||0).toFixed(1)}/10</b></div>
      <div><small>Volume</small><b>${esc(a.set_change)}</b></div>
    </div>
    <div class=adaptation-note><b>Session change</b><span>${esc(a.time_change)}</span></div>
    ${a.can_apply?`<button class=btn data-a=apply-adaptation ${S.adaptationBusy?"disabled":""}>${S.adaptationBusy?"Building next week…":`Build Week ${a.next_week_number}`}</button>`:`<div class=adaptation-lock><b>${a.unfinished_workouts} workout${a.unfinished_workouts===1?"":"s"} remaining</b><span>Complete or skip the current week before Forge builds the next adaptive week.</span></div>`}
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
  ${adaptationCard()}
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
        ${w?`<i>${w.core_included?"Core ":""}${w.cardio_included?"Cardio":""}</i>`:""}
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

  <div class=big-spacer></div>
  <div class=card>
    <p class=eyebrow>HOW YOUR PLAN ADAPTS</p>
    <h3>Built to progress with you</h3>
    <p class=muted>Forge uses your logged sets, effort, workout completion, strength progress, and recovery feedback to adjust future training.</p>
  </div>

  <div class=spacer></div>
  <button class=btn data-plan-tab=workouts>View Workouts</button><div class=spacer></div><button class="btn dark" data-a=edit-equipment-log>Manage Equipment Log</button><div class=spacer></div><button class="btn dark" data-a=open-exercise-directory>Browse Exercise Directory</button><div class=spacer></div><button class="btn dark" data-a=open-training-settings>Training Settings</button>
`:`
  <div class=week-block><div class=week-title><h3>Week 1</h3><span>⌃</span></div><div class=stack>
  ${workouts.map(x=>`<button class="workout-row ${x.is_skipped?"skipped":""}" data-w=${plan.workouts.indexOf(x)}>
    <span class=day-block>${esc((x.scheduled_day_name||"DAY").slice(0,3).toUpperCase())}</span>
    <span class=inner><strong>${esc(x.name)}${x.is_skipped?"":": "}</strong><small>${x.is_skipped?"Skipped":`${x.exercises.length} exercises • ${x.estimated_minutes||profile.minutes_per_workout} min${x.core_included?" • Core":""}${x.cardio_included?" • Cardio":""}`}</small></span>
    <span class=arrow>›</span>
  </button>`).join("")}</div></div>
`}`;
}

function trainingsettings(){return `<p class=eyebrow>SETTINGS</p><h2>Training Settings</h2><p class=muted>Change how Forge structures future plans.</p><div class=big-spacer></div>${pwaInstallCard()}<div class=big-spacer></div><div class=preference-list><button class=pref-row data-a=settings-split><span><strong>Workout Split</strong><small class=muted style="display:block">${splitLabel(profile.workout_split)}</small></span><span>›</span></button><button class=pref-row data-a=settings-cardio-frequency><span><strong>Cardio Training</strong><small class=muted style="display:block">${cardioFrequencyLabel(profile.cardio_workouts_per_week)}</small></span><span>›</span></button><button class=pref-row data-a=settings-cardio-intensity><span><strong>Cardio Intensity</strong><small class=muted style="display:block">${cardioLabel(profile.cardio_preference)}</small></span><span>›</span></button><button class=pref-row data-a=settings-sport><span><strong>Sport</strong><small class=muted style="display:block">${sportLabel(profile.sport)}</small></span><span>›</span></button><button class=pref-row data-a=settings-core><span><strong>Core Training</strong><small class=muted style="display:block">${coreFrequencyLabel(profile.core_workouts_per_week)}</small></span><span>›</span></button><button class=pref-row data-a=settings-calendar><span><strong>Calendar & Time</strong><small class=muted style="display:block">${S.calendarStatus?.connected?"Google Calendar connected":(S.calendarStatus?.configured?"Not connected":"Google OAuth not configured")}</small></span><span>›</span></button></div><div class=big-spacer></div><button class=btn data-a=settings-save>Save Settings</button>`}
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
<div class=big-spacer></div><button class=btn data-a=calendar-settings-save>Save Calendar & Time Settings</button>`;
}
function render(){const map={welcome,register,login,goal,experience,schedule,equipment,preferences,preferencepicker,cardiopicker,cardiofrequencypicker,splitpicker,sportpicker,corepicker,trainingsettings,calendarsettings,generating,yourplan,home,workout,exercise,timer,complete,progress,nutrition,nutritionadd,history,prs,exercisehistory,swapexercise,cardioswap,coach,notifications:notificationCenter,equipmentlog,equipmentdetails,exercisedirectory,exercisedetail,plan:planScreen};V.innerHTML=map[S.route]()+floatingRestTimer();const onboarding=["welcome","register","login","goal","experience","schedule","equipment","equipmentdetails","preferences","preferencepicker","cardiopicker","cardiofrequencypicker","splitpicker","sportpicker","corepicker","generating","yourplan"].includes(S.route)&&!plan;nav.classList.toggle("hidden",onboarding);document.querySelector("#backBtn").style.visibility=["welcome","home","progress","nutrition","coach"].includes(S.route)?"hidden":"visible";document.querySelectorAll("[data-plan-tab]").forEach(b=>b.onclick=()=>{S.planTab=b.dataset.planTab;render()});document.querySelectorAll("[data-coach-route]").forEach(b=>b.onclick=()=>go(b.dataset.coachRoute));
document.querySelectorAll("[data-nav]").forEach(b=>{b.classList.toggle("active",b.dataset.nav===S.route);b.onclick=()=>go(b.dataset.nav)});document.querySelectorAll("[data-a]").forEach(b=>b.onclick=()=>act(b.dataset.a));document.querySelectorAll("[data-goal]").forEach(b=>b.onclick=()=>{profile.goal=b.dataset.goal;render()});document.querySelectorAll("[data-exp]").forEach(b=>b.onclick=()=>{profile.experience=b.dataset.exp;render()});document.querySelectorAll("[data-days]").forEach(b=>b.onclick=()=>{profile.days_per_week=+b.dataset.days;profile.core_workouts_per_week=Math.min(profile.core_workouts_per_week,profile.days_per_week);profile.cardio_workouts_per_week=Math.min(profile.cardio_workouts_per_week,profile.days_per_week);render()});document.querySelectorAll("[data-mins]").forEach(b=>b.onclick=()=>{profile.minutes_per_workout=+b.dataset.mins;render()});document.querySelectorAll("[data-cardio]").forEach(b=>b.onclick=()=>{profile.cardio_preference=b.dataset.cardio;render()});document.querySelectorAll("[data-split]").forEach(b=>b.onclick=()=>{profile.workout_split=b.dataset.split;render()});document.querySelectorAll("[data-sport]").forEach(b=>b.onclick=()=>{profile.sport=b.dataset.sport;render()});document.querySelectorAll("[data-core-frequency]").forEach(b=>b.onclick=()=>{profile.core_workouts_per_week=Math.min(+b.dataset.coreFrequency,+profile.days_per_week);render()});document.querySelectorAll("[data-cardio-frequency]").forEach(b=>b.onclick=()=>{profile.cardio_workouts_per_week=Math.min(+b.dataset.cardioFrequency,+profile.days_per_week);if(!["light","moderate","high","extended"].includes(profile.cardio_preference))profile.cardio_preference="moderate";render()});const nutritionDate=document.querySelector("#nutritionDate");
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
document.querySelectorAll("[data-directory-exercise]").forEach(b=>b.onclick=async()=>{
  try{S.exerciseDirectorySelected=await api(`/me/exercises/${b.dataset.directoryExercise}/directory`);go("exercisedetail")}catch(e){toast(e.message)}
});
const equipmentSearch=document.querySelector("#equipmentSearch");
if(equipmentSearch)equipmentSearch.oninput=()=>{S.equipmentSearch=equipmentSearch.value;render();};
document.querySelectorAll("[data-equipment-category]").forEach(b=>b.onclick=()=>{S.equipmentCategory=b.dataset.equipmentCategory;render();});
document.querySelectorAll("[data-equipment-edit]").forEach(b=>b.onclick=()=>{S.equipmentReturn=S.route==="equipment"?"onboarding":(S.equipmentReturn||"plan");S.equipmentEditKey=b.dataset.equipmentEdit;go("equipmentdetails");});
document.querySelectorAll("[data-equipment-key]").forEach(b=>b.onclick=()=>toggleEquipmentKey(b.dataset.equipmentKey));
document.querySelectorAll("[data-equipment-preset]").forEach(b=>b.onclick=()=>setEquipmentPreset(b.dataset.equipmentPreset));
document.querySelectorAll("[data-remove-custom]").forEach(b=>b.onclick=()=>{S.equipmentLog=S.equipmentLog.filter(x=>x.key!==b.dataset.removeCustom);render();});document.querySelectorAll("[data-pref]").forEach(b=>b.onclick=()=>toggleArr(profile.preferred_exercises,b.dataset.pref));document.querySelectorAll("[data-avoid]").forEach(b=>b.onclick=()=>toggleArr(profile.excluded_exercises,b.dataset.avoid));document.querySelectorAll("[data-w]").forEach(b=>b.onclick=()=>{S.wi=+b.dataset.w;go("workout")});document.querySelectorAll("[data-ex]").forEach(b=>b.onclick=async()=>{S.ei=+b.dataset.ex;S.set=0;await persistPosition();go("exercise")});document.querySelectorAll("[data-feel]").forEach(b=>b.onclick=()=>{S.feel=b.dataset.feel;render()});
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
const rf=document.querySelector("#registerForm");if(rf)rf.onsubmit=submitRegister;const lf=document.querySelector("#loginForm");if(lf)lf.onsubmit=submitLogin;if(S.route==="progress"&&!S.strengthTrend)loadStrengthTrend();if(S.route==="plan"&&!S.adaptationPreview)loadAdaptationPreview();if(["equipment","equipmentlog"].includes(S.route)&&!S.equipmentLoaded)loadEquipmentLog();if(["exercisedirectory","preferences","preferencepicker"].includes(S.route)&&!S.exerciseDirectory)loadExerciseDirectory();if(S.route==="coach"&&!S.coachLoaded)loadCoach();if(S.route==="exercise")loadExerciseRecall();if(S.route==="swapexercise")loadSwapOptions();if(S.route==="cardioswap")loadCardioSwapOptions();if(S.route==="timer")startTimer();if(S.route==="history")loadHistory();if(S.route==="prs")loadPRs();if(S.route==="nutrition"&&!S.nutrition)loadNutrition();
if(S.route==="exercisehistory")loadExerciseHistory();
if(S.route==="calendarsettings"){if(!S.calendarStatus||!S.timeSettings)loadCalendarSettings();startLiveClock()}else stopLiveClock()}
function toggleArr(arr,v){const i=arr.indexOf(v);if(i>=0)arr.splice(i,1);else arr.push(v);render()}
function go(r){
  if(!S.restRemaining)stopTimer();S.route=r;render();scrollTo(0,0);
  if(r==="progress"){loadProgressIntelligence();loadBodyMetrics();}
  if(r==="home"){loadHomeDashboard();loadNotifications();}
  if(r==="notifications")loadNotifications();
  if((r==="home"||r==="plan")&&S.calendarStatus?.connected&&S.calendarStatus?.sync_enabled){
    syncCalendar({silent:true});
  }
}
async function generatePlan(){go("generating");try{if(!authToken)throw Error("Please sign in");await api("/me/profile",{method:"POST",body:JSON.stringify(profile)});plan=await api("/me/plan/generate",{method:"POST"});
if(S.calendarStatus?.connected&&S.calendarStatus?.sync_enabled)await syncCalendar({silent:true});
setTimeout(()=>go("yourplan"),800)}catch(e){toast(e.message);go("preferences")}}
async function startWorkout(){const ww=w();const s=await api(`/me/workout/${ww.workout_id}/start`,{method:"POST"});session={session_id:s.session_id};S.lastSessionId=s.session_id;S.ei=0;S.set=0;S.workoutPRs=[];await persistPosition();go("workout")}
async function saveSet(){
  if(!session)await startWorkout();
  const e=w().exercises[S.ei],weight=+document.querySelector("#weight").value,reps=+document.querySelector("#reps").value,rpe=+document.querySelector("#rpe").value;
  if(!Number.isFinite(weight)||weight<0)throw Error("Enter a valid weight");
  if(!Number.isFinite(reps)||reps<=0)throw Error("Enter valid reps");
  if(!Number.isFinite(rpe)||rpe<1||rpe>10)throw Error("RPE must be 1–10");
  const result=await api("/me/performance",{method:"POST",body:JSON.stringify({request_id:requestId(),session_id:session.session_id,exercise_id:e.exercise_id,completed_sets:1,reps:[reps],difficulty:rpe,weight,skipped:false})});
  if(result.pr_events?.length){S.workoutPRs.push(...result.pr_events);toast(`🏆 ${result.pr_events[0].label}: ${result.pr_events[0].exercise_name}`)}
  S.set++;
  if(S.set>=e.sets){
    S.set=0;S.ei++;
    if(S.ei>=w().exercises.length){
      await persistPosition();await api("/me/workout/complete",{method:"POST",body:JSON.stringify({session_id:session.session_id,completed:true})});
      S.lastSessionId=session.session_id;plan=await api("/me/plan/current");session=null;S.ei=0;S.set=0;go("complete");
    }else{await persistPosition();await beginPersistentRest(e.rest_seconds||60)}
  }else{await persistPosition();await beginPersistentRest(e.rest_seconds||60)}
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
      await api("/me/profile",{method:"POST",body:JSON.stringify(profile)});
      toast("Training settings saved");
      S.preferenceReturn="preferences";
      go(plan?"plan":"preferences");
    }
    if(a==="pref-done"){
      const dest=S.preferenceReturn==="trainingsettings"?"trainingsettings":"preferences";
      S.preferenceReturn="preferences";
      go(dest);
    }
    if(a==="generate")await generatePlan();
    if(a==="edit")go("goal");
    if(a==="startplan")go("home");
    if(a==="viewplan"){S.planTab="workouts";go("plan");}
    if(a==="gohome")go("home");
    if(a==="startworkout")await startWorkout();
    if(a==="openexercise")go("exercise");if(a==="swap-exercise")go("swapexercise");
    if(a==="swap-cardio")go("cardioswap");
    if(a==="cancel-cardio-swap")go("workout");
    if(a==="apply-cardio-swap")await applyCardioSwap();if(a==="back-exercise")go("exercise");if(a==="swap-selected"){if(S.selectedSwap)await applySwap(S.selectedSwap);else toast("Select an exercise first");}if(a==="abandon"){if(session&&confirm("Abandon this workout? Logged sets will remain in history.")){await api("/me/workout/abandon",{method:"POST",body:JSON.stringify({session_id:session.session_id})});session=null;S.ei=0;S.set=0;S.restRemaining=0;plan=await api("/me/plan/current");go("home");toast("Workout abandoned")}}
    if(a==="completeset")await saveSet();if(a==="skip-set"){S.set++;await persistPosition();toast("Set skipped");render();}
    if(a==="open-rest"){go("timer");}
    if(a==="view-workout-rest"){go("workout");startTimer();}
    if(a==="skiprest"){await clearPersistentRest();go("exercise");}
    if(a==="finish"){if(S.lastSessionId){try{await api("/me/workout/feedback",{method:"POST",body:JSON.stringify({session_id:S.lastSessionId,feedback:S.feel})})}catch(e){toast(e.message)}}S.lastSessionId=null;go("home");}
    if(a==="history")go("history");if(a==="prs")go("prs");if(a==="sendcoach")await sendCoach();
    if(a==="apply-coach")await applyCoachAction();
    if(a==="apply-adaptation")await applyAdaptiveWeek();
    if(a==="clear-coach"){await api("/me/coach/history",{method:"DELETE"});S.coachMessages=[];S.coachAction=null;render();}
  }catch(e){toast(e.message);}
}
document.querySelector("#backBtn").onclick=()=>{
  const pickerRoutes=["preferencepicker","cardiopicker","cardiofrequencypicker","splitpicker","sportpicker","corepicker"];
  if(pickerRoutes.includes(S.route)){
    const dest=S.preferenceReturn==="trainingsettings"?"trainingsettings":"preferences";
    S.preferenceReturn="preferences";
    go(dest);
    return;
  }
  const dest={register:"welcome",login:"welcome",history:"progress",prs:"history",exercisehistory:"prs",swapexercise:"exercise",cardioswap:"workout",nutritionadd:"nutrition",experience:"goal",schedule:"experience",equipment:"schedule",equipmentlog:plan?"plan":"equipment",equipmentdetails:S.equipmentReturn==="onboarding"?"equipment":"equipmentlog",exercisedirectory:plan?"plan":"preferences",exercisedetail:"exercisedirectory",preferences:"equipment",yourplan:"preferences",workout:"home",exercise:"workout",timer:"exercise",complete:"home",plan:"home",calendarsettings:"trainingsettings"}[S.route]||"home";
  go(dest);
};
document.querySelector("#moreBtn").onclick=async()=>{if(authToken&&confirm("Sign out of Forge?")){try{await api("/auth/logout",{method:"POST"})}catch{}localStorage.removeItem("forge_auth_token");authToken="";account=null;plan=null;session=null;stopCalendarPolling();S.route="welcome";render();toast("Signed out")}else if(!authToken){toast(`API: ${API}`)}};
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
    const r=await fetch(`${API_BASE}/nutrition/providers/status`);
    const d=await r.json();
    const u=d.providers?.usda||{}, o=d.providers?.openfoodfacts||{};
    alert(`Nutrition Providers\nUSDA: ${u.status||"unknown"} — ${u.detail||""}\nOpen Food Facts: ${o.status||"unknown"} — ${o.detail||""}`);
  }catch(err){ alert("Could not check nutrition provider status: "+err.message); }
});
