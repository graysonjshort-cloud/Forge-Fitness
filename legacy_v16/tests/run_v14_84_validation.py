from pathlib import Path
import sys,tempfile,shutil,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import database,training_intelligence_v14
from tests.run_v14_79_validation import add_program
def main():
 td=Path(tempfile.mkdtemp());dbp=td/"t.sqlite";shutil.copy2(ROOT/"fitness_app_initial_database.sqlite",dbp);database.ensure_schema(dbp);uid=database.create_user(dbp)
 with database.session(dbp) as con:eid=con.execute("SELECT id FROM exercises ORDER BY id LIMIT 1").fetchone()["id"];_,wid=add_program(con,uid,"active","Core",eid)
 database.record_programming_decision(uid,decision_type="hold",scope="session",duration="next_set",target_type="exercise",target_id=eid,evidence="test",confidence="medium",db_path=dbp)
 core=training_intelligence_v14.intelligence_core(uid,dbp);assert core["version"]=="1.0" and core["decisions"] and core["policy"]["session_changes_do_not_rewrite_mesocycle"]
 d=core["decisions"][0];assert d["scope"]=="session" and d["duration"]=="next_set" and d["confidence"]=="medium"
 print(json.dumps({"status":"passed","version":"14.84.0","decisions":len(core["decisions"]),"core":"passed"},indent=2))
if __name__=="__main__":main()
