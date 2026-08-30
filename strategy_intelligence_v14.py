import database
import training_intelligence_v14 as ti

def training_strategy(user_id,db_path):
    profile=database.get_profile(user_id,db_path) or {}; dash=ti.training_dashboard(user_id,db_path); meso=dash.get('mesocycle') or {}
    saved=database.get_training_strategy_state(user_id,db_path); goal=str(profile.get('goal') or '').lower(); phase=meso.get('phase','accumulation'); fatigue=float(meso.get('fatigue_score') or 0)
    if fatigue>=8 or phase=='deload':strategy='recovery'
    elif 'strength' in goal:strategy='strength_emphasis'
    elif 'maintain' in goal:strategy='maintenance'
    else:strategy='hypertrophy_accumulation'
    if saved.get('specialization'):strategy='specialization'
    rationale=f"Strategy reflects goal={goal or 'general'}, mesocycle={phase}, fatigue={fatigue:.1f}."
    if saved.get('strategy') and saved.get('updated_at'): strategy=saved['strategy']; rationale=saved.get('rationale') or rationale
    return {'version':'1.0','strategy':strategy,'rationale':rationale,'mesocycle_phase':phase,'fatigue_score':fatigue,'specialization':saved.get('specialization',[])}

def specialization_block(user_id,db_path):
    strategy=training_strategy(user_id,db_path); muscle=ti.muscle_development_intelligence(user_id,db_path); picks=strategy.get('specialization',[])
    rows=[]
    for m in muscle.get('muscles',[]):
        name=m.get('muscle'); priority=name in picks; base=float(m.get('target_sets') or 0)
        rows.append({**m,'specialized':priority,'recommended_target_sets':round(base*1.2,1) if priority else round(base*.9,1) if picks else base})
    return {'version':'1.0','specialization':picks,'muscles':rows,'rule':'Specialization adds targeted stimulus while trimming lower-priority work to protect recoverability.'}

def stability_technique_intelligence(user_id,db_path):
    plan,exercises=ti._current_exercises(user_id,db_path); rows=[]
    for e in exercises:
        intel=database.get_exercise_intelligence(int(e['exercise_id']),db_path) or {}
        try:prog=ti.progression_strategy(user_id,int(e['exercise_id']),db_path)
        except Exception:prog={}
        stability=int(intel.get('stability_demand') or 3); skill=int(intel.get('skill_demand') or 3); fatigue=int(intel.get('fatigue_cost') or 3); joint=int(intel.get('joint_stress') or 3)
        noise=stability+skill+max(0,fatigue-3)+max(0,joint-3)
        status='high_variability' if noise>=9 and prog.get('status') in {'holding','plateauing','regressing'} else 'stable_platform'
        rows.append({'exercise_id':e['exercise_id'],'name':e.get('name'),'stability_demand':stability,'skill_demand':skill,'fatigue_cost':fatigue,'joint_stress':joint,'progression_status':prog.get('status','new'),'technique_signal':status,'recommendation':'Consider a more stable/lower-fatigue variant before assuming the target muscle is stalled.' if status=='high_variability' else 'Exercise is suitable for reliable progression tracking.'})
    return {'version':'1.0','exercises':rows}

def programming_controls(user_id,db_path):
    values=database.get_programming_authority(user_id,db_path)
    return {'version':'1.0','controls':values,'modes':['recommend_only','ask_first','auto_apply'],'rule':'Forge must consult these authority settings before applying supported programming changes.'}

def authority_for(user_id,domain,db_path):
    return database.get_programming_authority(user_id,db_path).get(domain,'recommend_only')

def strategy_dashboard(user_id,db_path):
    strategy=training_strategy(user_id,db_path); specialization=specialization_block(user_id,db_path); forecast=ti.recovery_forecast(user_id,db_path); governance=ti.decision_governance(user_id,db_path); authority=programming_controls(user_id,db_path); rotation=ti.rotation_plateau_engine(user_id,db_path); explain=ti.explainable_programming(user_id,db_path)
    return {'version':'1.0','strategy':strategy,'specialization':specialization,'recovery_forecast':forecast,'governance':governance,'authority':authority,'rotation_summary':{'rotate':sum(1 for x in rotation.get('exercises',[]) if x.get('recommendation')=='rotate'),'retain':sum(1 for x in rotation.get('exercises',[]) if x.get('recommendation')=='retain')},'recent_decisions':explain.get('cards',[])[:5]}
