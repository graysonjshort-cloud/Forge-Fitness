from pathlib import Path
import sys,tempfile,shutil,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import database,training_intelligence_v14
from tests.run_v14_79_validation import add_program

def main():
 td=Path(tempfile.mkdtemp());dbp=td/'t.sqlite';shutil.copy2(ROOT/'fitness_app_initial_database.sqlite',dbp);database.ensure_schema(dbp);uid=database.create_user(dbp)
 with database.session(dbp) as con:
  eid=con.execute("SELECT id FROM exercises WHERE exercise_type!='timed' ORDER BY id LIMIT 1").fetchone()['id'];_,wid=add_program(con,uid,'active','P',eid)
 sid=database.start_workout(uid,wid,dbp)
 for i in range(5): database.record_performance(uid,sid,eid,{'completed_sets':i+1,'reps':[12],'difficulty':7,'weight':100,'load_mode':'weight'},dbp)
 database.save_programming_authority(uid,{'session_load':'auto_apply'},dbp)
 c=training_intelligence_v14.persistent_adaptation_candidates(uid,dbp)
 row=next(x for x in c['candidates'] if x['exercise_id']==eid)
 assert row['eligible'] and row['may_auto_apply'],row
 r=training_intelligence_v14.apply_persistent_adaptation(uid,eid,row['evidence_key'],True,dbp);assert r['applied']
 r2=training_intelligence_v14.apply_persistent_adaptation(uid,eid,row['evidence_key'],True,dbp);assert not r2['applied'] and r2['status']=='duplicate'
 t=database.get_latest_exercise_targets(uid,eid,dbp,6,10,'weight');assert t.get('persistent_target') is True
 ds=database.list_programming_decisions(uid,20,dbp);assert any(x['decision_type']=='persistent_progression' for x in ds)
 print(json.dumps({'status':'passed','version':'15.1.0','evidence_gate':'passed','authority_gate':'passed','idempotency':'passed','persistent_target':'passed'}))
if __name__=='__main__':main()
