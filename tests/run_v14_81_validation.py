from pathlib import Path
import sys,tempfile,shutil,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import database,training_intelligence_v14
from tests.run_v14_79_validation import add_program
def main():
 td=Path(tempfile.mkdtemp());dbp=td/"t.sqlite";shutil.copy2(ROOT/"fitness_app_initial_database.sqlite",dbp);database.ensure_schema(dbp);uid=database.create_user(dbp)
 with database.session(dbp) as con:eid=con.execute("SELECT id FROM exercises ORDER BY id LIMIT 1").fetchone()["id"];_,wid=add_program(con,uid,"active","P",eid)
 sid=database.start_workout(uid,wid,dbp)
 database.record_performance(uid,sid,eid,{"completed_sets":1,"reps":[8],"difficulty":7,"weight":100,"load_mode":"weight"},dbp)
 x=training_intelligence_v14.progression_strategy(uid,eid,dbp);saved=database.get_exercise_progression_state(uid,eid,dbp)
 assert x["version"]=="4.0" and x["status"] in {"new","holding","progressing","plateauing","regressing","returning_after_deload"};assert saved and saved["status"]==x["status"]
 print(json.dumps({"status":"passed","version":"14.84.0","progression_status":x["status"]},indent=2))
if __name__=="__main__":main()
