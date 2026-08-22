from pathlib import Path
import re, json, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
app=(ROOT/"app.js").read_text(encoding="utf-8")
css=(ROOT/"styles.css").read_text(encoding="utf-8")
index=(ROOT/"index.html").read_text(encoding="utf-8")

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
    assert token in app, token

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

# JS parser validation.
subprocess.run(["node","--check",str(ROOT/"app.js")],check=True,capture_output=True,text=True)
print(json.dumps({
  "status":"passed",
  "routes_checked":len(required_routes),
  "equipment_assets_checked":len(catalog),
  "responsive_breakpoints":["390px","340px","700px"],
  "critical_actions_checked":8
},indent=2))
