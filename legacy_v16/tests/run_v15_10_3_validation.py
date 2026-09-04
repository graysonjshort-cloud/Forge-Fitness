from pathlib import Path
import re,collections
r=Path(__file__).resolve().parents[1]
app=(r/"app.js").read_text(); css=(r/"styles.css").read_text(); idx=(r/"index.html").read_text()
runtime_modules="\n".join((r/"js"/x).read_text() for x in ['forge_onboarding_ui.js','forge_home_ui.js','forge_workout_runtime.js','forge_nutrition_ui.js','forge_progress_runtime.js','forge_coach_runtime.js','forge_plan_runtime.js']); modules="\n".join(x.read_text() for x in (r/"js").glob("*.js")); all_frontend=app+"\n"+modules; duplicate_scope=app+"\n"+runtime_modules

# Release and size guard.
assert "16.0.1" in idx
assert (r/"app.js").stat().st_size < 250000

# Concise copy / readable adaptation language.
for token in ["PROGRAM CHANGES","EXERCISE CHANGES","Nothing changes until you approve it.","NEXT STEP"]:
    assert token in all_frontend,token
for old in [
    "Forge can now explain decisions from your block phase",
    "Keep the broad muscle groups, then optionally target specific sections",
    "Forge will mark the current exercise as painful so it is strongly deprioritized",
]:
    assert old not in all_frontend,old

# Narrow-screen text protection and rhythm.
for token in [
    "workout-context-name","-webkit-line-clamp:2","overflow-wrap:break-word",
    ".row>*{min-width:0}",".btn{white-space:normal","@media(max-width:340px)"
]:
    assert token in all_frontend+css,token

# Core pathways still have handlers.
actions=set(re.findall(r'data-a=([A-Za-z0-9_-]+)',all_frontend))|set(re.findall(r'data-a="([A-Za-z0-9_-]+)"',all_frontend))
handlers=set(re.findall(r'a==="([A-Za-z0-9_-]+)"',app))
assert not (actions-handlers),sorted(actions-handlers)

# No duplicate named functions.
names=re.findall(r'(?m)^(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(',duplicate_scope)
assert not [n for n,c in collections.Counter(names).items() if c>1]

print("v15.10.4 UI copy/spacing polish validation passed")
