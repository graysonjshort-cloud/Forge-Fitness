from pathlib import Path
import sys, tempfile, shutil, json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import database, training_intelligence_v14

def add_program(con,uid,status,name,eid):
    con.execute("INSERT INTO programs(user_id,status,current_week) VALUES (?,?,1)",(uid,status))
    pid=con.execute("SELECT last_insert_rowid()").fetchone()[0]
    plan={'workouts':[{'workout_id':None,'name':name,'exercises':[{'exercise_id':eid,'name':'seed','sets':3}]}]}
    con.execute("INSERT INTO program_weeks(program_id,week_number,plan_json) VALUES (?,?,?)",(pid,1,json.dumps(plan)))
    pwid=con.execute("SELECT last_insert_rowid()").fetchone()[0]
    con.execute("INSERT INTO workouts(program_week_id,name,workout_index,estimated_minutes,status) VALUES (?,?,0,45,'planned')",(pwid,name))
    wid=con.execute("SELECT last_insert_rowid()").fetchone()[0]
    con.execute("INSERT INTO workout_exercises(workout_id,exercise_id,exercise_order,sets,min_reps,max_reps,rest_seconds,progression_method) VALUES (?,?,0,3,6,10,90,'double progression')",(wid,eid))
    plan['workouts'][0]['workout_id']=wid
    con.execute("UPDATE program_weeks SET plan_json=? WHERE id=?",(json.dumps(plan),pwid))
    return pid,wid

def main():
    td=Path(tempfile.mkdtemp(prefix='forge1479_')); dbp=td/'test.sqlite'
    shutil.copy2(ROOT/'fitness_app_initial_database.sqlite',dbp)
    database.ensure_schema(dbp)
    uid=database.create_user(dbp)
    with database.session(dbp) as con:
        ids=[r['id'] for r in con.execute('SELECT id FROM exercises ORDER BY id LIMIT 2').fetchall()]
        assert len(ids)==2
        old_pid,old_wid=add_program(con,uid,'inactive','Old Workout',ids[1])
        active_pid,wid=add_program(con,uid,'active','Current Workout',ids[0])
        con.execute("INSERT INTO workout_sessions(workout_id,status,started_at) VALUES (?,'active',CURRENT_TIMESTAMP)",(old_wid,))
        stale_sid=con.execute('SELECT last_insert_rowid()').fetchone()[0]
        con.execute("INSERT OR IGNORE INTO session_state(session_id,current_exercise_index,current_set_index) VALUES (?,0,0)",(stale_sid,))
    sid=database.start_workout(uid,wid,dbp)
    database.update_session_position(uid,sid,99,99,dbp)
    sync=database.reconcile_active_session(uid,sid,dbp)
    assert sync['status']=='ok' and sync['workout_id']==wid
    assert sync['current_exercise_index']==0 and sync['current_set_index']==2
    assert sync['stale_sessions_closed']==1
    with database.session(dbp) as con:
        stale=con.execute('SELECT status FROM workout_sessions WHERE id=?',(stale_sid,)).fetchone()['status']
        assert stale=='abandoned'
    try:
        database.record_performance(uid,sid,ids[1],{'completed_sets':1,'reps':[8],'difficulty':7,'weight':20,'load_mode':'weight'},dbp)
        raise AssertionError('wrong exercise accepted')
    except ValueError as e:
        assert 'does not match the active workout session' in str(e)
    database.update_session_position(uid,sid,0,0,dbp)
    database.record_performance(uid,sid,ids[0],{'completed_sets':1,'reps':[8],'difficulty':7,'weight':20,'load_mode':'weight'},dbp)
    live=database.get_session_intelligence(uid,sid,ids[0],dbp)
    assert 'next_set' in live and 'effort_cap' in live and 'why_changed' in live
    strategy=training_intelligence_v14.progression_strategy(uid,ids[0],dbp)
    assert str(strategy['version']).startswith('4.0') and 'retention_score' in strategy and 'plateau_evidence' in strategy
    diagnostics=database.get_session_diagnostics(uid,dbp)
    assert diagnostics['stale_active_sessions']==0 and diagnostics['duplicate_active_workouts']==0
    print(json.dumps({'status':'passed','version':'14.84.0','session_reconciliation':'passed','stale_cleanup':'passed','wrong_exercise_guard':'passed','live_intelligence_2':'passed','mesocycle_progression_2':'passed','production_diagnostics':'passed'},indent=2))

if __name__=='__main__': main()
