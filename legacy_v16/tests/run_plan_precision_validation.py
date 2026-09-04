from __future__ import annotations
import json, os, shutil, sqlite3, tempfile
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import database
from fitness_app_plan_generator_upgraded import PlanGenerator, UserProfile

fd,path=tempfile.mkstemp(suffix='.sqlite'); os.close(fd)
try:
    shutil.copy2(ROOT/'fitness_app_initial_database.sqlite',path)
    database.ensure_schema(path)
    with sqlite3.connect(path) as con:
        exercises=con.execute('SELECT COUNT(*) FROM exercises').fetchone()[0]
        linked=con.execute('SELECT COUNT(DISTINCT exercise_id) FROM exercise_muscles').fetchone()[0]
        links=con.execute('SELECT COUNT(*) FROM exercise_muscles').fetchone()[0]
        taxonomy=con.execute('SELECT COUNT(*) FROM muscle_taxonomy').fetchone()[0]
    assert exercises==215
    assert linked==exercises, (linked,exercises)
    aliases=['Overhead Dumbbell Triceps Extension','Cable Overhead Triceps Extension','Trap Bar Deadlift','Treadmill Incline Walk',"Farmer's Carry"]
    with sqlite3.connect(path) as con:
        assert not con.execute('SELECT name FROM exercises WHERE name IN (?,?,?,?,?)',aliases).fetchall()
    assert links>exercises
    assert taxonomy>=30

    gen=PlanGenerator(path)
    ppl=gen.generate_plan(UserProfile(days_per_week=6,minutes_per_workout=90,equipment=('full_gym',),workout_split='push_pull_legs',exercises_per_day=7,seed=1461))
    assert [w['name'] for w in ppl['workouts']]==['Push','Pull','Legs','Push','Pull','Legs']
    assert all(len(w['exercises'])==7 for w in ppl['workouts'])
    assert all(len({e['name'] for e in w['exercises']})==len(w['exercises']) for w in ppl['workouts'])

    custom=gen.generate_plan(UserProfile(days_per_week=3,minutes_per_workout=90,equipment=('full_gym',),workout_split='custom',exercises_per_day=6,seed=1461,custom_split=(
        {'name':'Upper Chest + Side Delts','muscles':['Chest','Shoulders'],'submuscles':{'Chest':['Upper Chest'],'Shoulders':['Side Delts']}},
        {'name':'Lats + Biceps','muscles':['Back','Biceps'],'submuscles':{'Back':['Lats']}},
        {'name':'Legs','muscles':['Quads','Hamstrings','Glutes','Calves'],'submuscles':{'Calves':['Soleus']}},
    )))
    assert all(len(w['exercises'])==6 for w in custom['workouts'])
    first_targets={t for e in custom['workouts'][0]['exercises'] for t in (e.get('muscle_targets') or [])}
    leg_targets={t for e in custom['workouts'][2]['exercises'] for t in (e.get('muscle_targets') or [])}
    assert 'Upper Chest' in first_targets and 'Side Delts' in first_targets
    assert 'Soleus' in leg_targets

    # A user-requested quota must never be filled by repeating the same exercise.
    limited=gen._eligible(UserProfile(days_per_week=2,minutes_per_workout=90,equipment=('full_gym',),workout_split='custom',exercises_per_day=10,seed=1462))[:3]
    short=gen.generate_custom_workout(UserProfile(days_per_week=2,minutes_per_workout=90,equipment=('full_gym',),workout_split='custom',exercises_per_day=10,seed=1462),{'name':'Limited','muscles':['Chest']},limited)
    assert len({e.name for e in short.exercises})==len(short.exercises)
    assert short.exercise_quota_met is False
    assert short.exercise_quota_message

    print(json.dumps({'status':'passed','exercise_directory_count':exercises,'exercises_with_muscle_links':linked,'exercise_muscle_links':links,'taxonomy_subsections':taxonomy,'ppl_names':[w['name'] for w in ppl['workouts']],'exercises_per_day':7,'precision_targets_checked':['Upper Chest','Side Delts','Lats','Soleus']},indent=2))
finally:
    try: os.unlink(path)
    except OSError: pass
