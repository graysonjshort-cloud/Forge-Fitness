from pathlib import Path
import sys,tempfile,shutil,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import database,training_intelligence_v14
from tests.run_v14_79_validation import add_program
def main():
 td=Path(tempfile.mkdtemp());dbp=td/"t.sqlite";shutil.copy2(ROOT/"fitness_app_initial_database.sqlite",dbp);database.ensure_schema(dbp);uid=database.create_user(dbp)
 with database.session(dbp) as con:
  ids=[r["id"] for r in con.execute("SELECT id FROM exercises ORDER BY id LIMIT 3")];_,w1=add_program(con,uid,"active","One",ids[0]);
  pw=con.execute("SELECT program_week_id FROM workouts WHERE id=?",(w1,)).fetchone()["program_week_id"];con.execute("INSERT INTO workouts(program_week_id,name,workout_index,estimated_minutes,status) VALUES (?,'Two',1,45,'planned')",(pw,));w2=con.execute("SELECT last_insert_rowid()").fetchone()[0];con.execute("INSERT INTO workout_exercises(workout_id,exercise_id,exercise_order,sets,min_reps,max_reps,rest_seconds,progression_method) VALUES (?,?,0,3,6,10,90,'double progression')",(w2,ids[1]));con.execute("INSERT INTO workout_exercises(workout_id,exercise_id,exercise_order,sets,min_reps,max_reps,rest_seconds,progression_method) VALUES (?,?,1,3,6,10,90,'double progression')",(w1,ids[2]));plan=json.loads(con.execute("SELECT plan_json FROM program_weeks WHERE id=?",(pw,)).fetchone()["plan_json"]);plan["workouts"].append({"workout_id":w2,"name":"Two","exercises":[]});con.execute("UPDATE program_weeks SET plan_json=? WHERE id=?",(json.dumps(plan),pw))
 prev=database.preview_move_workout_exercise(uid,w1,ids[2],w2,dbp);assert prev["weekly_volume_change"]==0
 moved=database.move_workout_exercise(uid,w1,ids[2],w2,dbp);assert moved["status"]=="moved"
 snap=training_intelligence_v14.plan_editor_snapshot(uid,dbp);assert len(snap["workouts"])==2
 print(json.dumps({"status":"passed","version":"14.84.0","move":"passed","workouts":len(snap["workouts"])},indent=2))
if __name__=="__main__":main()
