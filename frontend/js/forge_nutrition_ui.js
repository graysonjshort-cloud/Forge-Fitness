// Forge Fitness v15.11.0 — extracted nutritionDateValue..before historyRowsMarkup
function nutritionDateValue(){
if(S.nutritionDate)return S.nutritionDate;
const d=new Date();S.nutritionDate=`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
return S.nutritionDate;
}
async function loadNutrition(){
if(!authToken||S.nutritionLoading)return;
S.nutritionLoading=true;
try{
const [day,saved]=await Promise.all([api(`/me/nutrition?date=${encodeURIComponent(nutritionDateValue())}`),api("/me/nutrition/saved-foods?limit=10")]);
S.nutrition=day;S.nutritionSavedFoods=saved;
if(S.route==="nutrition")render();
}catch(e){toast(e.message)}finally{S.nutritionLoading=false}
}
function nutritionProgress(value,target){
if(!target)return 0;
return Math.min(100,Math.round(Number(value||0)/Number(target)*100));
}
function nutrition(){
const n=S.nutrition,t=n?.targets||{calories:2200,protein_g:150,carbs_g:250,fat_g:70},v=n?.totals||{calories:0,protein_g:0,carbs_g:0,fat_g:0},r=n?.remaining||{};
const calPct=nutritionProgress(v.calories,t.calories);
return `<div class=row><div><p class=eyebrow>NUTRITION</p><h2>Nutrition</h2></div><input id=nutritionDate type=date value="${nutritionDateValue()}" class=nutrition-date></div>
<p class=muted>Fuel training while staying on target.</p>
<div class=big-spacer></div>
<div class=nutrition-dashboard-hero>
<div class=nutrition-ring-large style="--p:${calPct}"><div><b>${Math.max(0,Math.round(r.calories??(t.calories-v.calories)))}</b><small>kcal remaining</small></div></div>
<div class=nutrition-hero-copy><small>${Math.round(v.calories||0)} OF ${t.calories} KCAL</small><h3>${calPct<85?"Room left today":calPct<=105?"Right around target":"Over today’s target"}</h3><p>Protein remaining: <b>${Math.max(0,Math.round(r.protein_g??(t.protein_g-v.protein_g)))}g</b></p><button class=btn data-a=nutrition-add>+ Log Food</button></div>
</div>
<div class=spacer></div><div class=nutrition-macros>
${[["Protein","protein_g","g"],["Carbs","carbs_g","g"],["Fat","fat_g","g"]].map(([label,key,unit])=>`<div class=macro-card><div class=row><small>${label}</small><b>${Math.round(v[key]||0)}/${t[key]}${unit}</b></div><div class=macro-track><i style="width:${nutritionProgress(v[key],t[key])}%"></i></div><em>${Math.max(0,Math.round((r[key]??(t[key]-v[key]))||0))}${unit} left</em></div>`).join("")}</div>
${(S.nutritionSavedFoods||[]).filter(x=>!S.nutritionFavoritesOnly||x.is_favorite).length?`<div class=big-spacer></div><div class=row><h3>Quick Log</h3><small class=muted>${S.nutritionFavoritesOnly?"Favorites":"Recent & saved foods"}</small></div><div class=nutrition-saved-strip>${S.nutritionSavedFoods.filter(x=>!S.nutritionFavoritesOnly||x.is_favorite).map(x=>`<div class="card nutrition-saved-card"><button class=nutrition-favorite data-nutrition-favorite="${x.id}" data-favorite="${x.is_favorite?0:1}">${x.is_favorite?"★":"☆"}</button><h3>${esc(x.food_name)}</h3><p class=muted>${x.calories} kcal • P ${Math.round(x.protein_g)}g</p><button class="btn dark compact" data-nutrition-quicklog="${x.id}">+ Log</button></div>`).join("")}</div>`:""}
<div class=big-spacer></div><div class="card nutrition-training-card"><p class=eyebrow>TRAINING + NUTRITION</p><h3>Fuel today’s training</h3><p class=muted>Coach can use your workout and remaining macros.</p><div class=row><button class="btn dark compact" data-nutrition-coach="How should I eat for my workout today?">Pre-workout</button><button class="btn dark compact" data-nutrition-coach="What should I eat after my workout today?">Recovery</button></div></div>
<div class=big-spacer></div><div class=row><h3>Meals</h3><button class="btn dark compact" data-a=nutrition-targets>Targets</button></div><div class=spacer></div><div class=nutrition-tools><button class="btn dark compact" data-a=nutrition-copy-yesterday>Copy Yesterday</button><button class="btn dark compact ${S.nutritionFavoritesOnly?"selected":""}" data-a=nutrition-favorites-only>${S.nutritionFavoritesOnly?"All Saved":"Favorites"}</button></div><div class=spacer></div>
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
return `<p class=eyebrow>PLAN EDITOR 2.0</p><h2>${esc(ww.name)}</h2><p class=muted>Edit exercises, sets, reps, rest, locks, and workout days.</p>${S.planEditorSnapshot?.warnings?.length?`<div class=spacer></div><div class="card"><p class=eyebrow>PROGRAM WARNINGS</p>${S.planEditorSnapshot.warnings.slice(0,3).map(x=>`<small>${esc(x)}</small>`).join("<br>")}</div>`:""}<div class=big-spacer></div>
<div class=stack>${ww.exercises.map((e,i)=>`<div class="card builder-row"><div class=row><div><small>${i+1}</small><h3>${esc(e.name)}</h3></div><div><button data-builder-move="${i}:-1">↑</button><button data-builder-move="${i}:1">↓</button></div></div><div class=builder-fields><label>Sets<input data-builder-sets=${e.exercise_id} type=number min=1 max=12 value=${e.sets}></label><label>Min reps<input data-builder-min=${e.exercise_id} type=number min=1 value=${e.min_reps}></label><label>Max reps<input data-builder-max=${e.exercise_id} type=number min=1 value=${e.max_reps}></label><label>Rest<input data-builder-rest=${e.exercise_id} type=number min=15 step=15 value=${e.rest_seconds||60}></label></div><div class=row><button class="text-action" data-builder-lock="${S.wi}:${e.exercise_id}">${(S.planLocks?.[S.wi]||[]).includes(Number(e.exercise_id))?"🔒 Locked":"Lock exercise"}</button><button class="text-action" data-builder-exclude="${e.exercise_id}:${encodeURIComponent(e.name)}">Never include</button><button class="text-action" data-builder-remove=${e.exercise_id}>Remove</button></div><div class=spacer></div><div class=row><select data-builder-target="${e.exercise_id}">${(plan.workouts||[]).map((x,j)=>j===S.wi?"":`<option value="${x.workout_id}">Move to ${esc(x.name)}</option>`).join("")}</select><button class="btn dark compact" data-builder-transfer="${e.exercise_id}">Move</button></div></div>`).join("")}</div>
<div class=big-spacer></div><button class=btn data-a=builder-add>Add Exercise</button>`;
}
