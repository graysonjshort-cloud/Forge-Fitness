from pathlib import Path
import sys,tempfile,shutil,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import database,training_intelligence_v14
from tests.run_v14_79_validation import add_program
def main():
 td=Path(tempfile.mkdtemp());dbp=td/"t.sqlite";shutil.copy2(ROOT/"fitness_app_initial_database.sqlite",dbp);database.ensure_schema(dbp);uid=database.create_user(dbp)
 with database.session(dbp) as con:eid=con.execute("SELECT id FROM exercises ORDER BY id LIMIT 1").fetchone()["id"];_,wid=add_program(con,uid,"active","M",eid)
 x=training_intelligence_v14.muscle_development_intelligence(uid,dbp)
 assert x["version"]=="1.0" and "muscles" in x and "summary" in x
 print(json.dumps({"status":"passed","version":"14.84.0","muscles":len(x["muscles"]),"needs_review":x["summary"]["needs_review"]},indent=2))
if __name__=="__main__":main()
