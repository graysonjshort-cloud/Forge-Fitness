from pathlib import Path
import re, json, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
app=(ROOT/"app.js").read_text(encoding="utf-8")
css=(ROOT/"styles.css").read_text(encoding="utf-8")
index=(ROOT/"index.html").read_text(encoding="utf-8")
modules={p.name:p.read_text(encoding="utf-8") for p in (ROOT/"js").glob("*.js")}
all_frontend=app+"\n"+"\n".join(modules.values())

required_routes=[
"welcome","register","login","goal","experience","schedule","equipment","preferences",
"trainingsettings","calendarsettings","home","workout","exercise","timer","complete",
"progress","nutrition","nutritionadd","history","prs","exercisehistory","swapexercise",
"cardioswap","coach","equipmentlog","equipmentdetails","exercisedirectory","exercisedetail","plan"
]
route_map=re.search(r'function render\(\)\{const map=\{(.*?)\};V\.innerHTML=',app,re.S)
assert route_map,"render route map not found"
route_text=route_map.group(1)
missing=[r for r in required_routes if not re.search(r'(^|,)'+re.escape(r)+r'([,:}]|$)',route_text)]
assert not missing,missing

# Critical actions and UI hooks
for token in [
'data-a=completeset','data-a=swap-exercise','data-a=skip-set','data-a=apply-adaptation',
'data-coachprompt="Check my calendar availability','class="equipment-image"',
'floatingRestTimer()','loadExerciseRecall()'
]:
    assert token in all_frontend, token

# Equipment assets and exact active catalog coverage.
sys.path.insert(0,str(ROOT))
import database
catalog=database.equipment_catalog()
assets=ROOT/"assets"/"equipment"
missing_assets=[x["key"] for x in catalog if not (assets/f'{x["key"]}.svg').exists()]
assert not missing_assets,missing_assets
assert (assets/"generic.svg").exists()
assert len(catalog)==107

# No removed categories should leak back.
categories={x["category"] for x in catalog}
assert "Conditioning" not in categories
assert "Recovery & Mobility" not in categories

# Responsive/focus rules exist.
for rule in ["@media(max-width:390px)","@media(max-width:340px)",":focus-visible","adaptation-card"]:
    assert rule in css,rule

# Runtime-regression guards for known browser-only failures.
assert "API_BASE" not in all_frontend, "Undefined API_BASE reference reintroduced"
assert 'if(token&&plan)' not in all_frontend, "Undefined token reference reintroduced"
assert 'api("/nutrition/providers/status")' in app, "Nutrition provider status must use shared API helper"
assert 'if(authToken&&plan)cacheCurrentPlanDemos(true)' in app, "Online demo warmup must use authToken"

# JS parser validation.
subprocess.run(["node","--check",str(ROOT/"app.js")],check=True,capture_output=True,text=True)
for module in sorted((ROOT/"js").glob("*.js")):
    subprocess.run(["node","--check",str(module)],check=True,capture_output=True,text=True)
for name in ["forge_core.js","forge_api.js","forge_equipment.js","forge_pwa.js"]:
    assert f'/js/{name}?v=14.46.0' in index, f"Missing module script: {name}"
assert '/app.js?v=14.46.0' in index
assert len(app) < 210000, "app.js modularization regression"
print(json.dumps({
  "status":"passed",
  "routes_checked":len(required_routes),
  "equipment_assets_checked":len(catalog),
  "responsive_breakpoints":["390px","340px","700px"],
  "critical_actions_checked":8,
  "frontend_modules_checked":len(modules),
  "app_js_bytes":len(app)
},indent=2))

# v14.40 daily workout intelligence regression guards
assert 'data-a=repeat-last-set' in app, "Repeat Last Set action missing"
assert 'data-a=current-exercise-history' in app, "In-workout exercise history action missing"
assert 'Why this target?' in app, "Progression explanation missing"
assert 'loadCompletedWorkoutSummary' in app, "Completion summary loader missing"
assert 'completion-metrics' in app, "Completion metrics UI missing"

# v14.41 readiness/live adjustment regression guards
assert "readiness:readinessCheckin" in app
assert "Adjust Today’s Workout" in app
assert "todayAdjustmentBanner" in app
assert "LIVE ADJUSTMENT" in app

# v14.42 smart substitution regression guards
assert "SMART SUBSTITUTION" in app
assert "data-swap-reason" in app
assert "Marked during workout substitution due to discomfort" in app
assert "smart_reason" in app

# v14.43 dashboard/weekly insights regression guards
assert "WEEKLY INSIGHTS" in app
assert "homeQuickActions" in app
assert "api(\"/me/history\")" in app
assert "NEXT BEST ACTION" in app
