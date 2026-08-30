from __future__ import annotations
from collections import defaultdict
from datetime import datetime
import math
import database

BROAD_MUSCLES=("Chest","Back","Shoulders","Biceps","Triceps","Quads","Hamstrings","Glutes","Calves","Core","Forearms")

def _e1rm(weight,reps):
    try:
        w=float(weight or 0); r=int(reps or 0)
        return w*(1+r/30.0) if w>0 and r>0 else 0.0
    except Exception:return 0.0

def _current_exercises(user_id,db_path):
    plan=database.get_current_plan(user_id,db_path) or {"workouts":[]}
    out=[]
    for wi,w in enumerate(plan.get("workouts") or []):
        for ei,e in enumerate(w.get("exercises") or []):
            x=dict(e); x["workout_index"]=wi; x["workout_name"]=w.get("name"); x["exercise_index"]=ei
            x["exercise_id"]=int(x.get("exercise_id") or x.get("id") or 0)
            out.append(x)
    return plan,out

def _muscle_map(db_path):
    with database.session(db_path) as con:
        rows=con.execute("""SELECT exercise_id, muscle_group AS parent_muscle, sub_muscle AS submuscle, role
                            FROM exercise_muscles""").fetchall()
    d=defaultdict(list)
    for r in rows:d[int(r['exercise_id'])].append(dict(r))
    return d

def training_dashboard(user_id,db_path):
    plan, exercises=_current_exercises(user_id,db_path)
    state=database.get_training_state(user_id,db_path)
    history=database.get_workout_history(user_id,80,db_path)
    intelligence=database.get_progress_intelligence(user_id,db_path)
    week=max(1,int(state.get('week_number',1) or 1)); block_len=6; win=((week-1)%block_len)+1
    fatigue=float((intelligence.get('metrics') or {}).get('fatigue_score',state.get('fatigue_score',0)) or 0)
    phase='deload' if win>=6 or fatigue>=8 else 'intensification' if win>=4 else 'accumulation'
    completed=sum(1 for w in plan.get('workouts',[]) if w.get('status')=='completed')
    planned=len([w for w in plan.get('workouts',[]) if not w.get('is_skipped')])
    mmap=_muscle_map(db_path)
    targets=defaultdict(float); actual=defaultdict(float); subs=defaultdict(lambda:[0.0,0.0])
    profile=database.get_profile(user_id,db_path) or {}
    priorities=set(profile.get('priority_muscles') or [])
    for e in exercises:
        sets=float(e.get('sets') or 0)
        links=mmap.get(e['exercise_id'],[])
        seen=set()
        for m in links:
            broad=m.get('parent_muscle') or ''
            if broad and broad not in seen:
                weight=1.0 if m.get('role')=='primary' else .5
                targets[broad]+=sets*weight; seen.add(broad)
            sub=m.get('submuscle')
            if sub:
                weight=1.0 if m.get('role')=='primary' else .5
                subs[sub][0]+=sets*weight
    # actual effective sets from completed history this week, using same direct/indirect weighting
    current_week=max([int(h.get('week_number') or 0) for h in history] or [0])
    for h in history:
        if h.get('status')!='completed' or int(h.get('week_number') or 0)!=current_week: continue
        for ex in h.get('exercises') or []:
            good=sum(1 for s in ex.get('sets') or [] if not s.get('skipped'))
            for m in mmap.get(int(ex.get('exercise_id') or 0),[]):
                weight=1.0 if m.get('role')=='primary' else .5
                broad=m.get('parent_muscle') or ''
                if broad: actual[broad]+=good*weight
                sub=m.get('submuscle')
                if sub: subs[sub][1]+=good*weight
    muscles=[]
    for m in BROAD_MUSCLES:
        t=round(targets[m],1); a=round(actual[m],1)
        if not t and not a: continue
        muscles.append({'muscle':m,'target_sets':t,'actual_sets':a,'percent':round(min(150,a/max(t,1)*100)),'priority':m in priorities,'status':'complete' if t and a>=t else 'on_track' if t and a>=t*.6 else 'building'})
    subrows=[{'muscle':k,'target_sets':round(v[0],1),'actual_sets':round(v[1],1),'percent':round(min(150,v[1]/max(v[0],1)*100))} for k,v in subs.items() if v[0] or v[1]]
    subrows.sort(key=lambda x:(-x['target_sets'],x['muscle']))
    prs=database.get_personal_records(user_id,20,db_path)
    recent_prs=prs[:5]
    return {'version':'3.0','mesocycle':{'block_number':((week-1)//block_len)+1,'week_in_block':win,'block_length':block_len,'phase':phase,'fatigue_score':round(fatigue,1)},'week':{'completed':completed,'planned':planned,'adherence_percent':round(completed/max(planned,1)*100)},'muscles':muscles,'submuscles':subrows[:24],'recent_prs':recent_prs,'progression_mode':'deload' if phase=='deload' else 'progress' if fatigue<6 else 'maintain'}

def progression_strategy(user_id,exercise_id,db_path):
    hist=database.get_exercise_history(user_id,exercise_id,100,db_path)
    with database.session(db_path) as con:
        ex=con.execute('SELECT * FROM exercises WHERE id=?',(exercise_id,)).fetchone()
    if not ex: raise ValueError('Exercise not found')
    ex=dict(ex); sets=hist.get('sets') or []
    timed=any((s.get('duration_seconds') or 0)>0 for s in sets[-8:]) or str(ex.get('progression_method','')).lower().startswith('time')
    body=all((s.get('load_mode')=='bodyweight' or not s.get('weight')) for s in sets[-6:]) if sets else ex.get('equipment')=='Bodyweight'
    method='time progression' if timed else 'bodyweight rep progression' if body else 'double progression'
    recent=sets[-12:]
    valid=[s for s in recent if not s.get('duration_seconds') and s.get('reps')]
    best=max([_e1rm(s.get('weight'),s.get('reps')) for s in valid] or [0])
    old=[_e1rm(s.get('weight'),s.get('reps')) for s in (sets[-24:-12] if len(sets)>12 else []) if s.get('reps')]
    baseline=max(old or [0])
    trend=((best-baseline)/baseline*100) if baseline else None
    rpes=[float(s['rpe']) for s in recent if s.get('rpe') is not None]
    avg_rpe=sum(rpes)/len(rpes) if rpes else None
    sessions=[]
    for s in recent:
        key=s.get('recorded_at','')[:10]
        if key and key not in sessions:sessions.append(key)
    plateau=len(sessions)>=3 and trend is not None and abs(trend)<1.5
    poor=avg_rpe is not None and avg_rpe>=9.2
    if timed:
        target='Add 5–10 seconds once all working sets are controlled.'
    elif body:
        target='Add 1–2 reps per set; add external load only after the rep range is owned.'
    else:
        target=f"Reach {ex.get('max_reps',12)} reps across working sets, then add the smallest practical load increase."
    if poor: status='reduce'; note='Recent effort is very high; hold or reduce load before adding reps.'
    elif plateau: status='plateau'; note='Performance has been flat across multiple exposures; consider a small rep-range or exercise change.'
    elif trend is not None and trend>2: status='progressing'; note='Estimated strength is trending upward; keep the current progression method.'
    else: status='building'; note='Keep accumulating consistent exposures before changing the progression method.'
    return {'version':'3.0','exercise_id':exercise_id,'name':hist.get('name'),'method':method,'status':status,'target_rule':target,'sessions_analyzed':len(sessions),'avg_rpe':round(avg_rpe,1) if avg_rpe is not None else None,'strength_change_percent':round(trend,1) if trend is not None else None,'plateau':plateau,'reason':note,'prs':hist.get('prs') or {}}

def substitution_rankings(user_id,exercise_id,db_path):
    base=database.get_substitutions_for_user(user_id,exercise_id,db_path)
    original=progression_strategy(user_id,exercise_id,db_path)
    mmap=_muscle_map(db_path); orig_targets={m['submuscle'] for m in mmap.get(exercise_id,[]) if m.get('submuscle')}
    out=[]
    for item in base:
        x=dict(item); eid=int(x['id']); targets={m['submuscle'] for m in mmap.get(eid,[]) if m.get('submuscle')}
        overlap=len(orig_targets & targets)/max(1,len(orig_targets))
        same_prog=str(x.get('progression_method','')).split()[0].lower()==str(original.get('method','')).split()[0].lower()
        score=float(x.get('substitution_score') or 0)+overlap*35+(10 if same_prog else 0)
        hist=database.get_exercise_history(user_id,eid,20,db_path)
        exposure=len({s.get('recorded_at','')[:10] for s in hist.get('sets') or [] if s.get('recorded_at')})
        if exposure: score+=min(12,exposure*2)
        x['submuscle_overlap_percent']=round(overlap*100); x['progression_compatible']=same_prog; x['prior_sessions']=exposure; x['rank_score']=round(score,1)
        x['tradeoffs']={'joint_stress':x.get('joint_stress'),'stability_demand':x.get('stability_demand'),'fatigue_cost':x.get('fatigue_cost'),'skill_demand':x.get('skill_demand')}
        x['explanation']=f"{x['submuscle_overlap_percent']}% detailed target overlap; {'similar' if same_prog else 'different'} progression profile; {exposure} prior session{'s' if exposure!=1 else ''}."
        out.append(x)
    out.sort(key=lambda x:(x['equipment_compatible'],x['rank_score']),reverse=True)
    return {'version':'2.0','exercise_id':exercise_id,'original_progression':original,'options':out[:12]}

def training_records(user_id,db_path):
    history=database.get_workout_history(user_id,120,db_path)
    with database.session(db_path) as con:
        exrows=con.execute('SELECT id,name FROM exercises ORDER BY name').fetchall()
    cards=[]
    for er in exrows:
        h=database.get_exercise_history(user_id,int(er['id']),100,db_path)
        sets=h.get('sets') or []
        if not sets: continue
        dates=[]; points=[]
        for s in sets:
            d=(s.get('recorded_at') or '')[:10]
            if not d: continue
            val=s.get('duration_seconds') or _e1rm(s.get('weight'),s.get('reps')) or s.get('reps') or 0
            if d not in dates: dates.append(d); points.append({'date':d,'value':round(float(val),1)})
            elif val>points[-1]['value']:points[-1]['value']=round(float(val),1)
        first=points[0]['value']; last=points[-1]['value']; change=((last-first)/first*100) if first else 0
        cards.append({'exercise_id':int(er['id']),'name':er['name'],'sessions':len(dates),'first':first,'current':last,'change_percent':round(change,1),'best_weight':h['prs'].get('max_weight'),'best_e1rm':h['prs'].get('best_e1rm'),'best_reps':h['prs'].get('best_reps'),'points':points[-12:]})
    cards.sort(key=lambda x:(x['sessions'],x['current']),reverse=True)
    weeks=defaultdict(lambda:{'workouts':0,'sets':0,'volume':0.0})
    for h in history:
        if h.get('status')!='completed':continue
        wk=int(h.get('week_number') or 0); weeks[wk]['workouts']+=1; weeks[wk]['sets']+=int(h.get('total_sets') or 0); weeks[wk]['volume']+=float(h.get('total_volume') or 0)
    week_rows=[{'week':k,**{'workouts':v['workouts'],'sets':v['sets'],'volume':round(v['volume'],1)}} for k,v in sorted(weeks.items())]
    mesocycles=[]
    grouped=defaultdict(lambda:{'workouts':0,'sets':0,'volume':0.0})
    for row in week_rows:
        b=((row['week']-1)//6)+1 if row['week'] else 0; grouped[b]['workouts']+=row['workouts']; grouped[b]['sets']+=row['sets']; grouped[b]['volume']+=row['volume']
    for b,v in sorted(grouped.items()): mesocycles.append({'block':b,'workouts':v['workouts'],'sets':v['sets'],'volume':round(v['volume'],1)})
    return {'version':'3.0','exercise_cards':cards[:40],'weekly_history':week_rows[-16:],'mesocycle_history':mesocycles[-8:],'personal_records':database.get_personal_records(user_id,50,db_path)}

def coach_context_v4(user_id,db_path):
    dash=training_dashboard(user_id,db_path); records=training_records(user_id,db_path); intel=database.get_progress_intelligence(user_id,db_path)
    plan, exercises=_current_exercises(user_id,db_path)
    progression=[]
    for e in exercises[:12]:
        try: progression.append(progression_strategy(user_id,e['exercise_id'],db_path))
        except Exception:pass
    profile=database.get_profile(user_id,db_path) or {}
    readiness={'fatigue_score':(intel.get('metrics') or {}).get('fatigue_score'),'signals':intel.get('signals') or []}
    return {'version':'4.0','mesocycle':dash['mesocycle'],'readiness':readiness,'muscle_status':dash['muscles'],'exercise_progression':progression,'recent_records':records['exercise_cards'][:8],'schedule':database.get_workout_schedule(user_id,db_path),'nutrition_goal':profile.get('goal'),'coaching_rules':['Explain why a programming decision changed.','Prefer the smallest effective change.','Preserve successful exercises unless plateau, pain/avoidance, equipment, or recovery requires rotation.','Use mesocycle phase and readiness before increasing stress.']}
