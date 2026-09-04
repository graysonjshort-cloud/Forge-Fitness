from pathlib import Path
import re
r=Path(__file__).resolve().parents[1]
app=(r/"app.js").read_text()
gen=(r/"fitness_app_plan_generator_upgraded.py").read_text()
api=(r/"fitness_backend_api_v2_connected.py").read_text()
modules="\n".join(x.read_text() for x in (r/"js").glob("*.js")); all_frontend=app+"\n"+modules

# 1) Browsing during rest cannot reset/persist active set position.
handler=re.search(r'document\.querySelectorAll\("\[data-ex\]"\).*?document\.querySelectorAll\("\[data-feel\]"',app,re.S).group(0)
assert 'S.set=0;await persistPosition()' not in handler
assert 'exerciseinspect' in handler and 'targetIndex!==S.ei' in handler
assert 'Preview only' in all_frontend

# 2) Auto-added set has stable session target + opt-out finish path.
for token in ['effectiveSetCount','saveAutoSetTarget','optional_extra_set','data-a=finish-exercise','a==="finish-exercise"']:
    assert token in all_frontend,token
assert 'S.set>=setGoal' in all_frontend
assert 'e.sets=Number(si.recommended_total_sets)' not in all_frontend

# 3) Rest display and timer use the same dynamic recommendation.
assert 'latestRestFor(e)' in all_frontend
assert 'next rest' in all_frontend and 'base rest' in all_frontend
assert 'Rest adjusted:' in all_frontend
assert 'recommended_rest_seconds||e.rest_seconds||60' in all_frontend

# 4) Generator receives exact equipment-log keys and does not generalize specific machines/bars.
assert 'exact_equipment' in api and 'generator_equipment' in api
assert '_exercise_equipment_available' in gen
assert '"hack_squat_machine"' in gen and '"leg_press_machine"' in gen
assert 'EZ/trap bars are not treated' in (r/"database.py").read_text()

assert (r/"app.js").stat().st_size < 250000
print("v15.10.4 reported-workout-issues regression passed")
