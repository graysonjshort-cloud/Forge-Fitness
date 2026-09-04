from pathlib import Path
import sys,tempfile,shutil,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import database
from tests.run_v14_79_validation import add_program

def main():
 td=Path(tempfile.mkdtemp());dbp=td/'t.sqlite';shutil.copy2(ROOT/'fitness_app_initial_database.sqlite',dbp);database.ensure_schema(dbp);uid=database.create_user(dbp)
 with database.session(dbp) as con:
  ids=[r['id'] for r in con.execute("SELECT id FROM exercises ORDER BY id").fetchall()]
 chosen=None
 for eid in ids:
  subs=database.get_substitutions_for_user(uid,eid,dbp)
  good=[x for x in subs if x.get('equipment_compatible')]
  if good: chosen=(eid,int(good[0]['id']));break
 assert chosen, 'no substitution pair';old,new=chosen
 with database.session(dbp) as con: _,wid=add_program(con,uid,'active','Swap Workout',old)
 sid=database.start_workout(uid,wid,dbp)
 for i in range(2): database.record_performance(uid,sid,old,{'completed_sets':i+1,'reps':[8],'difficulty':8,'weight':50,'load_mode':'weight'},dbp)
 database.update_session_position(uid,sid,0,2,dbp)
 before=database.get_exercise_performance_for_session(sid,old,dbp);assert len(before)==2
 out=database.swap_workout_exercise(uid,wid,old,new,dbp);tr=out.get('session_transition');assert tr and tr['carried_completed_sets']==2 and tr['historical_rows_rewritten'] is False
 after=database.get_exercise_performance_for_session(sid,old,dbp);assert len(after)==2
 sync=database.reconcile_active_session(uid,sid,dbp);assert sync['workout_id']==wid and sync['current_exercise_id']==new and sync['current_set_index']==2
 database.record_performance(uid,sid,new,{'completed_sets':3,'reps':[8],'difficulty':8,'weight':50,'load_mode':'weight'},dbp)
 try:
  database.record_performance(uid,sid,old,{'completed_sets':3,'reps':[8],'difficulty':8,'weight':50,'load_mode':'weight'},dbp);raise AssertionError('old exercise accepted after swap')
 except ValueError: pass
 plan=database.get_current_plan(uid,dbp);sync2=database.reconcile_active_session(uid,sid,dbp);assert sync2['current_exercise_id']==new
 live=database.get_session_intelligence(uid,sid,new,dbp);assert live['carried_completed_sets']==2 and live['completed_sets_on_replacement']==1 and live['completed_sets']==3
 print(json.dumps({'status':'passed','version':'15.2.0','start_log_swap_reload_resume_continue':'passed','historical_rows_preserved':'passed','immutable_workout_id':'passed','set_position_carry':'passed'}))
if __name__=='__main__':main()
