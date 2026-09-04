from pathlib import Path
import sys,tempfile,shutil
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import database, training_intelligence_v14 as ti
td=Path(tempfile.mkdtemp()); dbp=td/"t.sqlite"
shutil.copy2(ROOT/"fitness_app_initial_database.sqlite",dbp); database.ensure_schema(dbp)
uid=database.create_user(dbp)
gov=ti.decision_governance(uid,dbp)
assert gov["version"]=="2.0" and gov["precedence"][0]=="safety"
week=ti.adaptive_week_plan(uid,dbp); assert week["version"]=="3.0"
rot=ti.rotation_plateau_engine(uid,dbp); assert rot["version"]=="3.0"
forecast=ti.recovery_forecast(uid,dbp); assert len(forecast["days"])==3
database.record_programming_decision(uid,decision_type="test_change",scope="session",duration="session",target_type="exercise",target_id=1,target_name="Test",old_value={"load":100},new_value={"load":95},evidence="High fatigue",confidence="high",db_path=dbp)
exp=ti.explainable_programming(uid,dbp)
assert exp["cards"] and exp["cards"][0]["why"]=="High fatigue"
print("v14.89 intelligence governance validation passed")
