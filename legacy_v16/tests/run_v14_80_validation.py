from pathlib import Path
import sys,tempfile,shutil,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import database
from tests.run_v14_79_validation import add_program
def main():
 td=Path(tempfile.mkdtemp(prefix="forge1480_"));dbp=td/"t.sqlite";shutil.copy2(ROOT/"fitness_app_initial_database.sqlite",dbp);database.ensure_schema(dbp);uid=database.create_user(dbp)
 with database.session(dbp) as con:
  eid=con.execute("SELECT id FROM exercises WHERE default_sets>=3 ORDER BY id LIMIT 1").fetchone()["id"];pid,wid=add_program(con,uid,"active","Auto",eid)
 sid=database.start_workout(uid,wid,dbp)
 database.record_performance(uid,sid,eid,{"completed_sets":1,"reps":[8],"difficulty":9.7,"weight":100,"load_mode":"weight"},dbp)
 x=database.get_session_intelligence(uid,sid,eid,dbp);a=x["autoregulation"]
 assert a["version"]=="3.0" and a["scope"]=="session" and a["persistent_change"] is False
 assert a["recommended"]["rest_seconds"]>=a["planned"]["rest_seconds"] and x["next_set"]["recommended_weight"]<=100
 print(json.dumps({"status":"passed","version":"14.84.0","autoregulation":a["action"]},indent=2))
if __name__=="__main__":main()
