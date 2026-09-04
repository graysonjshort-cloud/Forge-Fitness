from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import database
from fitness_app_plan_generator_upgraded import PlanGenerator, UserProfile, TrainingState
import fitness_backend_api_v2_connected as api

g=PlanGenerator(ROOT/'fitness_app_initial_database.sqlite')
base=UserProfile(days_per_week=4,minutes_per_workout=60,exercises_per_day=5,exercises_per_workout=(5,5,5,5),seed=4660)
plan=g.generate_plan(base)
assert api._normalize_exercise_targets([None,7,None],4,5)==[5,7,5,5]
assert api._generated_plan_invariants(plan,base)==[]
# Duplicate guard must fail a deliberately corrupted workout.
bad=json.loads(json.dumps(plan))
first=bad['workouts'][0]['exercises'][0]
bad['workouts'][0]['exercises'].append(dict(first))
errs=api._generated_plan_invariants(bad,base)
assert any('duplicate exercise' in x.lower() for x in errs)
# Detailed diff includes exercise counts and set changes.
changed=json.loads(json.dumps(plan))
changed['workouts'][0]['exercises'][0]['sets']+=1
diff=api._plan_diff(plan,changed)
assert diff[0]['exercise_count_before']==diff[0]['exercise_count_after']
assert diff[0]['set_changes']
# Adaptive Programming 2.0 must materially influence scoring and set targets.
candidates=g._eligible(base)
ex=candidates[0]
neutral=UserProfile(days_per_week=4,minutes_per_workout=60,training_state=TrainingState(exercise_history={}),seed=1)
progress=UserProfile(days_per_week=4,minutes_per_workout=60,training_state=TrainingState(exercise_history={ex['name']:{'adaptive_action':'progress','difficulty':7,'reps':[10,10,10]}}),seed=1)
rotate=UserProfile(days_per_week=4,minutes_per_workout=60,training_state=TrainingState(exercise_history={ex['name']:{'adaptive_action':'rotate','difficulty':7,'reps':[10,10,10]}}),seed=1)
assert g._adaptive_score(ex,progress)>g._adaptive_score(ex,neutral)
assert g._adaptive_score(ex,rotate)<g._adaptive_score(ex,neutral)
assert g._intelligent_sets(ex,progress)>=g._intelligent_sets(ex,neutral)
print(json.dumps({
  'status':'passed',
  'version':'14.66.0',
  'plan_invariants':'passed',
  'sparse_target_normalization':[5,7,5,5],
  'detailed_diff':'passed',
  'adaptive_actions_checked':['progress','rotate'],
  'workouts_generated':len(plan['workouts'])
},indent=2))
