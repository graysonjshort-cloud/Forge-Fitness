from pathlib import Path
import sys,tempfile,shutil
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import database, strategy_intelligence_v14 as si
td=Path(tempfile.mkdtemp());dbp=td/'t.sqlite';shutil.copy2(ROOT/'fitness_app_initial_database.sqlite',dbp);database.ensure_schema(dbp)
uid=database.create_user(dbp)
assert si.training_strategy(uid,dbp)['version']=='1.0'
database.save_training_strategy_state(uid,'specialization','Priority block',['Chest','Back'],dbp)
sp=si.specialization_block(uid,dbp);assert sp['specialization']==['Chest','Back']
a=database.save_programming_authority(uid,{'session_load':'auto_apply','exercise_substitutions':'ask_first'},dbp);assert a['session_load']=='auto_apply' and a['exercise_substitutions']=='ask_first'
ctrl=si.programming_controls(uid,dbp);assert ctrl['controls']['session_load']=='auto_apply'
stab=si.stability_technique_intelligence(uid,dbp);assert stab['version']=='1.0'
dash=si.strategy_dashboard(uid,dbp);assert dash['version']=='1.0' and 'authority' in dash and 'recovery_forecast' in dash
print('v14.94 strategy + authority validation passed')
