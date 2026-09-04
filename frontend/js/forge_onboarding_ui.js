// Forge Fitness v15.11.0 — extracted welcome..before loadNotifications
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
<p>Training, nutrition, progress, and coaching in one place.</p>
</div>
<div class=welcome-actions>
<button class=btn data-a=register-screen>Get Started</button>
<button class="btn dark" data-a=login-screen>Log In</button>
</div>
<p class=welcome-footnote>Built around your goals and schedule.</p>
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
<div class=spacer></div><div class=auth-help><b>Connect Google Calendar after sign-in.</b><span>Your Forge and Google accounts stay separate.</span></div>
<div class=spacer></div><div class=auth-link>Don't have an account? <b data-a=register-screen>Register</b></div>`;
}
async function submitRegister(ev){
ev.preventDefault();const f=new FormData(ev.target);
if(f.get("password")!==f.get("confirm_password"))throw Error("Passwords do not match");
const d=await api("/auth/register",{method:"POST",body:JSON.stringify({display_name:f.get("display_name"),email:f.get("email"),password:f.get("password")})});
authToken=d.token;account=d.user;await ForgeDeviceServices?.setAuthToken?.(authToken);if(!window.ForgeNative?.isNative)localStorage.setItem("forge_auth_token",authToken);S.name=account.display_name;go("goal");toast("Account created");
}
async function submitLogin(ev){
ev.preventDefault();const f=new FormData(ev.target);
const d=await api("/auth/login",{method:"POST",body:JSON.stringify({email:f.get("email"),password:f.get("password")})});
authToken=d.token;account=d.user;await ForgeDeviceServices?.setAuthToken?.(authToken);if(!window.ForgeNative?.isNative)localStorage.setItem("forge_auth_token",authToken);S.name=account.display_name;
try{plan=await api("/me/plan/current");go("home")}catch{plan=null;go("goal")}toast("Signed in");
}
function goal(){
const opts=[["Build Muscle","Build size and strength","build_muscle"],["Lose Weight","Reduce body fat","lose_fat"],["Improve Strength","Lift heavier over time","get_stronger"],["Improve Endurance","Build work capacity","improve_fitness"],["General Fitness","Stay active and capable","general_fitness"]];
return `${dots(0)}<h2>What's your goal?</h2><p class=muted>Choose your main training goal.</p><div class=big-spacer></div><div class=stack>${opts.map(o=>`<button class="choice-card ${profile.goal===o[2]?"selected":""}" data-goal=${o[2]}><div><strong>${o[0]}</strong><small>${o[1]}</small></div></button>`).join("")}</div><div class=big-spacer></div><button class=btn data-a=next>Next</button>`;
}
function experience(){
const opts=[["Beginner","New to training","beginner"],["Intermediate","1–3 years training","intermediate"],["Advanced","3+ years training","advanced"]];
return `${dots(1)}<h2>Your experience level?</h2><p class=muted>This sets your starting difficulty.</p><div class=big-spacer></div><div class=stack>${opts.map(o=>`<button class="choice-card ${profile.experience===o[2]?"selected":""}" data-exp=${o[2]}><div><strong>${o[0]}</strong><small>${o[1]}</small></div></button>`).join("")}</div><div class=big-spacer></div><button class=btn data-a=next>Next</button>`;
}
function schedule(){
return `${dots(2)}<h2>How many days?</h2><p class=muted>How many days can you train?</p><div class=big-spacer></div><div class=choice-grid>${[2,3,4,5,6].map(n=>`<button class="choice-tile ${profile.days_per_week===n?"selected":""}" data-days=${n}><span><b>${n} Days</b><small>${n===2?"Minimal":n===3?"Recommended":n===4?"Balanced":"High frequency"}</small></span></button>`).join("")}</div><div class=big-spacer></div><p class=eyebrow>SESSION LENGTH</p><div class=chips>${[20,30,45,60,90].map(n=>`<button class="chip ${profile.minutes_per_workout===n?"selected":""}" data-mins=${n}>${n} min</button>`).join("")}</div><div class=big-spacer></div><p class=eyebrow>EXERCISES PER WORKOUT</p><p class=muted>Choose a target number of exercises per workout.</p><div class=chips>${[3,4,5,6,7,8,9,10].map(n=>`<button class="chip ${Number(profile.exercises_per_day||6)===n?"selected":""}" data-exercise-count=${n}>${n}</button>`).join("")}</div><div class=big-spacer></div><button class=btn data-a=next>Next</button>`;
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
<p class=muted>Forge uses this to choose exercises and swaps.</p>
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
return `<p class=eyebrow>EQUIPMENT DETAILS</p><h2>${esc(item.name)}</h2><p class=muted>Add anything Forge should know about this item.</p>
<div class=big-spacer></div>
<div class=equipment-detail-form>
${fields.length?fields.map(([key,type])=>{
const label=key.replaceAll("_"," ").replace(/\b\w/g,m=>m.toUpperCase());
const val=item.details?.[key];
if(type==="boolean")return `<label class=equipment-bool><span>${esc(label)}</span><input type=checkbox data-equipment-detail="${key}" ${val?"checked":""}></label>`;
return `<label class=field>${esc(label)}<input type=number step=any min=0 data-equipment-detail="${key}" value="${val??""}" placeholder="Optional"></label>`;
}).join(""):`<div class=card><p class=muted>Optional details only.</p></div>`}
<label class=field>Notes<input id=equipmentNotes value="${esc(item.details?.notes||"")}" placeholder="Optional notes"></label>
</div>
<div class=big-spacer></div><button class=btn data-a=equipment-detail-save>Save Details</button>`;
}
async function loadExerciseDirectory(){
if(!authToken||S.exerciseDirectoryLoading)return;
S.exerciseDirectoryLoading=true;
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
}catch(e){toast(e.message)}finally{S.exerciseDirectoryLoading=false}
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
if(!silent)toast(urls.length?`${status.cached||0}/${urls.length} demos ready offline`:"No animation assets in this plan");
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
<p>Form cues remain available while the 3D demo is being prepared.</p>
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
return `<p class=eyebrow>DEMO REVIEW</p><h2>${esc(r.exercise_name)}</h2><p class=muted>Mark each item only after reviewing the animation.</p>
<div class=demo-review-queue-bar><button data-a=demo-review-prev ${S.demoReviewQueueIndex<=0?"disabled":""}>‹ Previous</button><span>${S.demoReviewQueue.length?`${S.demoReviewQueueIndex+1}/${S.demoReviewQueue.length}`:"Review"}</span><button data-a=demo-review-next ${S.demoReviewQueueIndex>=S.demoReviewQueue.length-1?"disabled":""}>Next ›</button></div>
${reviewPreview}<div class=card>${fields.map(([k,n])=>`<label class=demo-review-item><input type=checkbox data-demo-review="${k}" ${r[k]?"checked":""}><span><b>${n}</b><small>${r[k]?"Passed":"Needs review"}</small></span></label>`).join("")}</div>
<div class=spacer></div><label class=field>Review notes<textarea data-demo-review-notes rows=4 placeholder="Record anything that should be corrected…">${esc(r.notes||"")}</textarea></label>
<button class=btn data-a=save-demo-review>Save Review</button>
${r.complete?`<div class="card demo-reviewed-banner"><b>✓ Reviewed</b><p>All checks passed. This demo is ready.</p></div>`:`<p class="muted demo-review-warning">This demo stays pending until every check passes.</p>`}`;
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
return `<p class=eyebrow>EXERCISE FORM</p><h2>${esc(d.name)}</h2><p class=muted>${esc(d.primary_muscle)} • ${esc(d.equipment)}</p><button class="form-demo-offline-btn" data-a=cache-plan-demos>Save This Week’s Demos Offline</button><button class="form-demo-audit-btn" data-a=open-demo-audit>View Demo Library Coverage</button><div class=form-demo-tabs>${[["demo","Demo"],["setup","Setup"],["mistakes","Mistakes"]].map(([v,n])=>`<button class="${S.formDemoTab===v?"active":""}" data-form-demo-tab="${v}">${n}</button>`).join("")}</div>${body}<div class=spacer></div><div class=card><p class=eyebrow>BREATHING</p><p>${esc(d.breathing_cue)}</p></div><div class=spacer></div><div class="card form-safety"><p class=eyebrow>CONTROL</p><p>${esc(d.safety_note)}</p></div>`;
}
async function loadSubstitutionIntelligence(){
const ex=w()?.exercises?.[S.ei];if(!ex)return;
const exerciseId=Number(ex.exercise_id);
if(S.substitutionIntelligenceExerciseId===exerciseId&&(S.substitutionIntelligence||S.substitutionIntelligenceLoading))return;
S.substitutionIntelligenceExerciseId=exerciseId;S.substitutionIntelligenceLoading=true;S.substitutionIntelligence=null;
try{
const data=await api(`/me/exercises/${exerciseId}/substitution-intelligence`);
if(S.substitutionIntelligenceExerciseId!==exerciseId)return;
S.substitutionIntelligence=data;
if(S.route==="swapexercise"&&Number(w()?.exercises?.[S.ei]?.exercise_id)===exerciseId)render();
}catch(e){if(S.substitutionIntelligenceExerciseId===exerciseId)S.substitutionIntelligence={options:[],error:true}}
finally{if(S.substitutionIntelligenceExerciseId===exerciseId)S.substitutionIntelligenceLoading=false}
}
function substitutionIntelligenceCard(){const d=S.substitutionIntelligence;if(!d?.options?.length)return "";return `<div class=card><p class=eyebrow>SUBSTITUTION INTELLIGENCE 2.0</p><h3>Best-fit replacements</h3><div class=sub-intel-list>${d.options.slice(0,5).map((x,i)=>`<div><b>${i+1}. ${esc(x.name)}</b><span>${x.submuscle_overlap_percent}% target overlap • ${x.progression_compatible?"similar":"different"} progression</span><small>${esc(x.explanation)}</small></div>`).join("")}</div></div>`}
function exercisedetail(){
const e=S.exerciseDirectorySelected;
if(!e)return `<h2>Exercise</h2><p class=muted>Select an exercise from the directory.</p>`;
const pref=e.user_preference||"neutral";
const lvl=n=>["","Low","Low","Moderate","High","Very High"][Math.max(1,Math.min(5,Number(n||1)))];
return `<p class=eyebrow>EXERCISE INTELLIGENCE</p><h2>${esc(e.name)}</h2><p class=muted>${esc(e.primary_muscle)} • ${esc(e.difficulty)}</p>
<div class=big-spacer></div>
<button class=exercise-directory-hero data-form-demo="${e.id}" data-form-return=exercisedetail><div class=form-demo-icon>▶</div><strong>Open Form Guide</strong><span>Setup • technique • mistakes</span></button>
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
<div class=card><p class=eyebrow>MY PREFERENCE</p><p class=muted>Used when Forge builds your plan.</p>
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
return `${dots(4)}<h2>Any preferences?</h2><p class=muted>Customize your plan.</p><div class=big-spacer></div><div class=preference-list>
<button class=pref-row data-a=pref-avoid><span><strong>Avoid These Exercises</strong><small class=muted style="display:block">${profile.excluded_exercises.length} selected</small></span><span>›</span></button>
<button class=pref-row data-a=pref-focus><span><strong>Focus Areas</strong><small class=muted style="display:block">${profile.priority_muscles.length} selected</small></span><span>›</span></button>
<button class=pref-row data-a=pref-cardio-frequency><span><strong>Cardio</strong><small class=muted style="display:block">${cardioFrequencyLabel(profile.cardio_workouts_per_week)}</small></span><span>›</span></button>
<button class=pref-row data-a=pref-cardio-intensity><span><strong>Cardio effort</strong><small class=muted style="display:block">${cardioLabel(profile.cardio_preference)}</small></span><span>›</span></button>
<button class=pref-row data-a=pref-split><span><strong>Split</strong><small class=muted style="display:block">${splitLabel(profile.workout_split)}</small></span><span>›</span></button>
<button class=pref-row data-a=pref-sport><span><strong>Sport</strong><small class=muted style="display:block">${sportLabel(profile.sport)}</small></span><span>›</span></button>
<button class=pref-row data-a=pref-core><span><strong>Core</strong><small class=muted style="display:block">${coreFrequencyLabel(profile.core_workouts_per_week)}</small></span><span>›</span></button>
</div><div class=big-spacer></div><button class=btn data-a=generate>Next</button>`;
}
function coreFrequencyLabel(v){
const n=Math.max(0,Math.min(Number(v||0),Number(profile.days_per_week||0)));
return n===0?"No Direct Core":n===1?"1 workout / week":`${n} workouts / week`;
}
function corepicker(){
const max=Number(profile.days_per_week||4);
const values=Array.from({length:max+1},(_,i)=>i);
return `<p class=eyebrow>CORE TRAINING</p><h2>Core sessions per week</h2>
<p class=muted>Core is added to your existing workout days.</p>
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
function sportpicker(){return `<p class=eyebrow>SPORT</p><h2>What are you training for?</h2><p class=muted>Forge will tune training around your sport.</p><div class=big-spacer></div><div class=preference-list>${SPORT_OPTIONS.map(([v,n,d])=>`<button class="pref-row ${profile.sport===v?"selected":""}" data-sport="${v}"><span><strong>${n}</strong><small class=muted style="display:block">${d}</small></span><span>${profile.sport===v?"✓":"›"}</span></button>`).join("")}</div><div class=big-spacer></div><button class=btn data-a=pref-done>Done</button>`}
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
return `<p class=eyebrow>CARDIO TRAINING</p><h2>Cardio sessions per week</h2>
<p class=muted>Cardio is added to your existing workout days.</p>
<div class=big-spacer></div><div class=preference-list>
${values.map(v=>`<button class="pref-row ${Number(profile.cardio_workouts_per_week)===v?"selected":""}" data-cardio-frequency="${v}">
<span><strong>${v===0?"No Cardio":v===1?"1 Cardio Add-On":`${v} Cardio Add-Ons`}</strong>
<small class=muted style="display:block">${v===0?"No dedicated cardio work":v===1?"Added to 1 regular workout each week":`Spread across ${v} regular workouts each week`}</small></span>
<span>${Number(profile.cardio_workouts_per_week)===v?"✓":"›"}</span></button>`).join("")}
</div><div class=big-spacer></div><button class=btn data-a=pref-done>Done</button>`;
}
function cardiopicker(){return `<p class=eyebrow>CARDIO INTENSITY</p><h2>Cardio intensity</h2><p class=muted>Controls duration and steady-state vs. intervals.</p><div class=big-spacer></div><div class=preference-list>${CARDIO_OPTIONS.map(([v,n,d])=>`<button class="pref-row ${profile.cardio_preference===v?"selected":""}" data-cardio="${v}"><span><strong>${n}</strong><small class=muted style="display:block">${d}</small></span><span>${profile.cardio_preference===v?"✓":"›"}</span></button>`).join("")}</div><div class=big-spacer></div><button class=btn data-a=pref-done>Done</button>`}
function splitpicker(){return `<p class=eyebrow>WORKOUT SPLIT</p><h2>Choose your training split</h2><p class=muted>Changing your split rebuilds the plan.</p><div class=big-spacer></div><div class=preference-list>${SPLIT_OPTIONS.map(([v,n,d])=>{const allowed=splitAllowed(v);return `<button class="pref-row ${profile.workout_split===v?"selected":""}" data-split="${v}" ${allowed?"":"disabled"}><span><strong>${n}</strong><small class=muted style="display:block">${allowed?d:"Requires at least 3 training days"}</small></span><span>${profile.workout_split===v?"✓":"›"}</span></button>`}).join("")}</div>${profile.workout_split==="custom"?`<div class=spacer></div><button class="btn dark" data-a=edit-custom-split>Configure Custom Days</button>`:""}<div class=big-spacer></div><button class=btn data-a=pref-done>Done</button>`}
function splitAllowed(v){if(v==="push_pull_legs")return profile.days_per_week>=3;return true}
function customsplit(){ensureCustomSplit();const intel=customSplitInsights();return `<p class=eyebrow>CUSTOM SPLIT 3.0</p><h2>Build your training week</h2><p class=muted>Choose broad muscles, then add specific sections only if needed.</p><div class=big-spacer></div><div class=card><p class=eyebrow>WEEKLY MUSCLE TARGETS</p><h3>Frequency & priority</h3><p class=muted>Adjust weekly frequency and mark priorities.</p>${CUSTOM_SPLIT_MUSCLES.map(m=>`<div class=row style="padding:10px 0;border-bottom:1px solid var(--border)"><div><strong>${m}</strong><small class=muted style="display:block">${intel.frequency[m]}× / week • ${(profile.priority_muscles||[]).includes(m)?"High priority":"Standard priority"}</small></div><div class=row style="gap:6px"><button class=chip data-custom-frequency="${m}:-1">−</button><button class="chip ${(profile.priority_muscles||[]).includes(m)?"selected":""}" data-custom-priority="${m}">Priority</button><button class=chip data-custom-frequency="${m}:1">+</button></div></div>`).join("")}</div><div class=spacer></div>${intel.warnings.length?`<div class=card><p class=eyebrow>PLAN CHECK</p><h3>${intel.warnings.length} item${intel.warnings.length===1?"":"s"} to review</h3>${intel.warnings.map(x=>`<p class=muted>• ${esc(x)}</p>`).join("")}</div><div class=spacer></div>`:`<div class=card><p class=eyebrow>PLAN CHECK</p><h3>Split looks balanced</h3><p class=muted>Coverage and recovery spacing look good.</p></div><div class=spacer></div>`}${profile.custom_split.map((day,i)=>`<div class=card><div class=row><div><p class=eyebrow>${esc(customSplitWeekday(i))} • DAY ${i+1}</p><h3>${esc(customDayName(day.muscles,i))}</h3></div><span class=muted>${day.muscles.length} group${day.muscles.length===1?"":"s"}</span></div><div class=chips>${CUSTOM_SPLIT_MUSCLES.map(m=>`<button class="chip ${day.muscles.includes(m)?"selected":""}" data-custom-muscle="${i}:${m}">${m}</button>`).join("")}</div>${day.muscles.map(m=>`<div style="margin-top:12px"><small class=muted>${m} focus • ${(day.submuscles?.[m]||[]).length?"specific sections":"whole group"}</small><div class=chips style="margin-top:6px">${(MUSCLE_SUBSECTIONS[m]||[]).map(sub=>`<button class="chip ${(day.submuscles?.[m]||[]).includes(sub)?"selected":""}" data-custom-submuscle="${i}:${m}:${sub}">${sub}</button>`).join("")}</div></div>`).join("")}</div><div class=spacer></div>`).join("")}<button class=btn data-a=custom-split-done>Use Custom Split</button>`}
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
