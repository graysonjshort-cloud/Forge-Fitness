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
    hist=database.get_exercise_history(user_id,exercise_id,160,db_path)
    with database.session(db_path) as con:
        ex=con.execute('SELECT * FROM exercises WHERE id=?',(exercise_id,)).fetchone()
    if not ex: raise ValueError('Exercise not found')
    ex=dict(ex); sets=hist.get('sets') or []
    timed=any((x.get('duration_seconds') or 0)>0 for x in sets[-12:]) or str(ex.get('progression_method','')).lower().startswith('time')
    body=(all((x.get('load_mode')=='bodyweight' or not x.get('weight')) for x in sets[-8:]) if sets else ex.get('equipment')=='Bodyweight')
    assisted='assist' in str(ex.get('name','')).lower()
    method='timed progression' if timed else 'assisted progression' if assisted else 'bodyweight progression' if body else 'double progression'
    by_session=defaultdict(list)
    for x in sets:
        key=(x.get('recorded_at') or '')[:10]
        if key: by_session[key].append(x)
    exposures=[]
    for d,rows in sorted(by_session.items()):
        if timed:
            score=max([float(x.get('duration_seconds') or 0) for x in rows] or [0])
        elif body or assisted:
            score=max([float(x.get('reps') or 0) for x in rows] or [0])
        else:
            score=max([_e1rm(x.get('weight'),x.get('reps')) for x in rows] or [0])
        rpes=[float(x['rpe']) for x in rows if x.get('rpe') is not None]
        exposures.append({'date':d,'score':round(score,1),'rpe':round(sum(rpes)/len(rpes),1) if rpes else None})
    recent=exposures[-6:]
    arrows=[]
    for i,x in enumerate(recent[-4:]):
        if i==0 and len(recent)>4: prev=recent[-5]['score']
        elif i>0: prev=recent[-4:][i-1]['score']
        else: prev=x['score']
        arrows.append('↑' if x['score']>prev*1.01 else '↓' if x['score']<prev*.99 else '→')
    scores=[x['score'] for x in recent if x['score']>0]
    trend=((scores[-1]-scores[0])/scores[0]*100) if len(scores)>=2 and scores[0] else None
    recent_rpes=[x['rpe'] for x in recent if x.get('rpe') is not None]
    avg_rpe=sum(recent_rpes)/len(recent_rpes) if recent_rpes else None
    flat=sum(1 for i in range(1,len(scores)) if abs(scores[i]-scores[i-1])/max(scores[i-1],1)<.01)
    regress=sum(1 for i in range(1,len(scores)) if scores[i] < scores[i-1]*.985)
    plateau_evidence=max(0,flat-1) if len(scores)>=3 else 0
    state=database.get_training_state(user_id,db_path); week=max(1,int(state.get('week_number',1) or 1)); win=((week-1)%6)+1
    returning=win==1 and week>1
    if len(exposures)<2: status='new'
    elif returning: status='returning_after_deload'
    elif regress>=2: status='regressing'
    elif plateau_evidence>=2: status='plateauing'
    elif trend is not None and trend>1.5: status='progressing'
    else: status='holding'
    retention_score=max(0,min(100,round(82 + (10 if status=='progressing' else 0) - (15 if status=='plateauing' else 0) - (20 if status=='regressing' else 0) - (8 if avg_rpe and avg_rpe>=9.2 else 0))))
    hi=int(ex.get('max_reps') or 12); lo=int(ex.get('min_reps') or max(1,hi-4)); default_sets=int(ex.get('default_sets') or 3)
    if timed: threshold=f'Complete {default_sets} sets at the top of the time range with controlled effort, then add 5–10 seconds.'
    elif body: threshold=f'Reach {hi} reps across all {default_sets} working sets before adding external load.'
    elif assisted: threshold=f'Reach {hi} reps across working sets, then reduce assistance by the smallest available step.'
    else: threshold=f'Reach {hi} reps across all {default_sets} working sets at RPE ≤ 9, then add the smallest practical load increase.'
    action='reduce' if status=='regressing' and avg_rpe and avg_rpe>=9 else 'rotate_review' if status=='plateauing' else 'progress' if status=='progressing' else 'resume_conservative' if returning else 'hold'
    reason={'new':'Establish at least two comparable exposures before judging the trend.','returning_after_deload':'Resume conservatively after the deload before rebuilding progression pressure.','regressing':'Multiple recent exposures declined; reduce stress before forcing progression.','plateauing':'Performance has stayed essentially flat across several exposures.','progressing':'Recent exposure quality and performance are trending upward.','holding':'Performance is stable but has not earned a persistent load increase yet.'}[status]
    result={'version':'4.0','exercise_id':exercise_id,'name':hist.get('name'),'method':method,'status':status,'target_rule':threshold,'next_load_threshold':threshold,'next_action':action,'sessions_analyzed':len(exposures),'avg_rpe':round(avg_rpe,1) if avg_rpe is not None else None,'strength_change_percent':round(trend,1) if trend is not None else None,'plateau':status=='plateauing','plateau_evidence':plateau_evidence,'retention_score':retention_score,'post_deload_resume':returning,'resume_cue':'Use the final pre-deload load with 2–3 reps in reserve on the first return exposure.' if returning else None,'last_exposures':arrows,'exposure_history':recent,'reason':reason,'prs':hist.get('prs') or {}}
    database.save_exercise_progression_state(user_id,exercise_id,result,db_path)
    return result

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


def muscle_development_intelligence(user_id,db_path):
    dash=training_dashboard(user_id,db_path)
    plan, exercises=_current_exercises(user_id,db_path)
    mmap=_muscle_map(db_path)
    linked=defaultdict(list)
    for e in exercises:
        try: prog=progression_strategy(user_id,e['exercise_id'],db_path)
        except Exception: continue
        parents={m.get('parent_muscle') for m in mmap.get(e['exercise_id'],[]) if m.get('parent_muscle')}
        subs={m.get('submuscle') for m in mmap.get(e['exercise_id'],[]) if m.get('submuscle')}
        for m in parents|subs: linked[m].append(prog)
    fatigue=float((dash.get('mesocycle') or {}).get('fatigue_score') or 0)
    def classify(row):
        t=float(row.get('target_sets') or 0); a=float(row.get('actual_sets') or 0); ratio=(a/max(t,1)) if t else 0
        progs=linked.get(row['muscle'],[])
        statuses=[p.get('status') for p in progs]
        progressing=sum(1 for x in statuses if x=='progressing')
        stalled=sum(1 for x in statuses if x in {'plateauing','regressing'})
        if fatigue>=8 and ratio>=.7:
            status='recovery_limited'; rec='Keep volume stable or reduce it temporarily; recovery pressure is already high.'
        elif ratio<.6:
            status='underexposed'; rec='Complete more of the planned weekly stimulus before adding or rotating exercises.'
        elif ratio>=.85 and stalled and not progressing:
            status='stimulus_not_progressing'; rec='Volume is present but performance is not improving. Review exercise selection, rep targets, and recovery before adding more sets.'
        elif progressing:
            status='progressing'; rec='Keep the current exercise mix and volume while performance is moving up.'
        elif ratio>=.85:
            status='on_track'; rec='Weekly stimulus is on target. Hold steady until progression evidence changes.'
        else:
            status='building'; rec='Continue the current week and reassess once more planned volume is completed.'
        return {**row,'development_status':status,'linked_exercises':len(progs),'progressing_exercises':progressing,'stalled_exercises':stalled,'recommendation':rec}
    broad=[classify(x) for x in dash.get('muscles',[])]
    sub=[classify(x) for x in dash.get('submuscles',[])]
    priority={'recovery_limited':0,'stimulus_not_progressing':1,'underexposed':2,'building':3,'on_track':4,'progressing':5}
    broad.sort(key=lambda x:(priority.get(x['development_status'],9),-float(x.get('target_sets') or 0)))
    return {'version':'1.0','fatigue_score':fatigue,'mesocycle':dash.get('mesocycle'),'muscles':broad,'submuscles':sub,'summary':{
        'progressing':sum(1 for x in broad if x['development_status']=='progressing'),
        'needs_review':sum(1 for x in broad if x['development_status'] in {'recovery_limited','stimulus_not_progressing','underexposed'}),
        'on_track':sum(1 for x in broad if x['development_status'] in {'on_track','building'})}}


def plan_editor_snapshot(user_id,db_path):
    plan, exercises=_current_exercises(user_id,db_path); mmap=_muscle_map(db_path); workouts=[]; weekly=defaultdict(float)
    for wi,w in enumerate(plan.get('workouts') or []):
        muscles=defaultdict(float)
        for e in w.get('exercises') or []:
            sets=float(e.get('sets') or 0)
            for m in mmap.get(int(e.get('exercise_id') or 0),[]):
                weight=1.0 if m.get('role')=='primary' else .5
                muscles[m.get('parent_muscle')]+=sets*weight; weekly[m.get('parent_muscle')]+=sets*weight
        workouts.append({'workout_id':w.get('workout_id'),'workout_index':wi,'name':w.get('name'),'exercise_count':len(w.get('exercises') or []),'muscle_sets':dict(sorted((k,round(v,1)) for k,v in muscles.items() if k))})
    warnings=[]
    for i in range(1,len(workouts)):
        overlap=set(workouts[i-1]['muscle_sets']) & set(workouts[i]['muscle_sets'])
        heavy=[m for m in overlap if workouts[i-1]['muscle_sets'][m]>=4 and workouts[i]['muscle_sets'][m]>=4]
        if heavy:warnings.append(f"{workouts[i-1]['name']} → {workouts[i]['name']} repeats substantial {', '.join(heavy[:3])} work on adjacent training sessions.")
    return {'version':'2.0','workouts':workouts,'weekly_muscle_sets':{k:round(v,1) for k,v in weekly.items()},'warnings':warnings}


def intelligence_core(user_id,db_path):
    dash=training_dashboard(user_id,db_path)
    muscle=muscle_development_intelligence(user_id,db_path)
    plan, exercises=_current_exercises(user_id,db_path)
    progression=[]
    for e in exercises[:16]:
        try: progression.append(progression_strategy(user_id,e['exercise_id'],db_path))
        except Exception: pass
    decisions=database.list_programming_decisions(user_id,40,db_path)
    progress=database.get_progress_intelligence(user_id,db_path)
    active=database.get_active_session(user_id,db_path)
    return {'version':'1.0','policy':{
        'session_changes_do_not_rewrite_mesocycle':True,
        'persistent_changes_require_repeated_evidence':True,
        'preserve_successful_exercises':True,
        'prefer_smallest_effective_change':True},
        'mesocycle':dash.get('mesocycle'),'readiness':{'fatigue_score':(progress.get('metrics') or {}).get('fatigue_score'),'signals':progress.get('signals') or []},
        'muscle_development':muscle,'exercise_progression':progression,'active_session_id':active.get('id') if active else None,
        'decisions':decisions,'decision_counts':{
            'session':sum(1 for d in decisions if d.get('scope')=='session'),
            'persistent':sum(1 for d in decisions if d.get('duration')=='persistent'),
            'applied':sum(1 for d in decisions if d.get('applied'))}}

def coach_context_v4(user_id,db_path):
    dash=training_dashboard(user_id,db_path); records=training_records(user_id,db_path); intel=database.get_progress_intelligence(user_id,db_path)
    plan, exercises=_current_exercises(user_id,db_path)
    progression=[]
    for e in exercises[:12]:
        try: progression.append(progression_strategy(user_id,e['exercise_id'],db_path))
        except Exception:pass
    profile=database.get_profile(user_id,db_path) or {}
    readiness={'fatigue_score':(intel.get('metrics') or {}).get('fatigue_score'),'signals':intel.get('signals') or []}
    return {'version':'4.1-core','mesocycle':dash['mesocycle'],'readiness':readiness,'muscle_status':dash['muscles'],'exercise_progression':progression,'recent_records':records['exercise_cards'][:8],'recent_decisions':database.list_programming_decisions(user_id,12,db_path),'schedule':database.get_workout_schedule(user_id,db_path),'nutrition_goal':profile.get('goal'),'coaching_rules':['Explain why a programming decision changed.','State whether a change is session-only or persistent.','Prefer the smallest effective change.','Preserve successful exercises unless plateau, pain/avoidance, equipment, or recovery requires rotation.','Use mesocycle phase and readiness before increasing stress.']}

def decision_governance(user_id,db_path):
    """Resolve competing programming signals with deterministic safety-first precedence."""
    dash=training_dashboard(user_id,db_path)
    progress=database.get_progress_intelligence(user_id,db_path)
    meso=dash.get("mesocycle") or {}
    fatigue=float(meso.get("fatigue_score") or 0)
    phase=meso.get("phase") or "accumulation"
    decisions=database.list_programming_decisions(user_id,80,db_path)
    precedence=["safety","recovery","deload","session_autoregulation","progression","volume","preference"]
    signals=[]
    if fatigue>=8: signals.append({"source":"recovery","action":"reduce","strength":3,"reason":f"Fatigue score {fatigue:.1f}"})
    if phase=="deload": signals.append({"source":"deload","action":"reduce","strength":4,"reason":"Mesocycle is in deload"})
    recent=[d for d in decisions[:20] if d.get("applied")]
    if any(d.get("scope")=="session" and d.get("decision_type")=="autoregulation" for d in recent):
        signals.append({"source":"session_autoregulation","action":"hold","strength":2,"reason":"Recent session autoregulation is active"})
    if fatigue<6 and phase!="deload": signals.append({"source":"progression","action":"progress","strength":1,"reason":"Recovery permits progression"})
    rank={name:i for i,name in enumerate(precedence)}
    winner=min(signals,key=lambda x:(rank.get(x["source"],99),-x["strength"])) if signals else {"source":"progression","action":"hold","strength":0,"reason":"No strong conflicting signal"}
    suppressed=[x for x in signals if x is not winner and x["action"]!=winner["action"]]
    return {"version":"2.0","precedence":precedence,"winner":winner,"signals":signals,"suppressed":suppressed,
            "rule":"Higher-priority recovery/deload signals can block progression; session changes never rewrite the mesocycle."}

def adaptive_week_plan(user_id,db_path):
    plan,_=_current_exercises(user_id,db_path)
    dash=training_dashboard(user_id,db_path); gov=decision_governance(user_id,db_path)
    muscle=muscle_development_intelligence(user_id,db_path)
    phase=(dash.get("mesocycle") or {}).get("phase","accumulation")
    winner=(gov.get("winner") or {}).get("action","hold")
    factor=.72 if phase=="deload" else .9 if winner=="reduce" else 1.04 if winner=="progress" else 1.0
    workouts=[]
    for w in plan.get("workouts") or []:
        exs=[]
        for e in w.get("exercises") or []:
            sets=max(1,int(round(int(e.get("sets") or 1)*factor)))
            exs.append({"exercise_id":e.get("exercise_id"),"name":e.get("name"),"current_sets":e.get("sets"),"recommended_sets":sets,
                        "rep_range":e.get("rep_range") or [e.get("min_reps"),e.get("max_reps")]})
        workouts.append({"workout_id":w.get("workout_id"),"name":w.get("name"),"exercises":exs})
    return {"version":"3.0","phase":phase,"governance":gov,"volume_factor":factor,"workouts":workouts,
            "muscle_status":muscle.get("muscles",[]),"apply_scope":"next_week",
            "summary":f"Next week is coordinated at {round(factor*100)}% of current planned set volume before exercise-specific progression."}

def rotation_plateau_engine(user_id,db_path):
    _,exercises=_current_exercises(user_id,db_path); rows=[]
    for e in exercises:
        try: st=progression_strategy(user_id,e["exercise_id"],db_path)
        except Exception: continue
        status=st.get("status","holding"); retention=float(st.get("retention_score") or 0)
        rotate=status in {"plateauing","regressing"} and retention<70
        rows.append({"exercise_id":e["exercise_id"],"name":e.get("name"),"status":status,"retention_score":retention,
                     "recommendation":"rotate" if rotate else "retain",
                     "confidence":"high" if rotate and retention<50 else "medium" if rotate else "high",
                     "reason":"Repeated stagnation plus low retention value." if rotate else "Preserve the movement while it is productive or evidence is insufficient."})
    return {"version":"3.0","policy":"Rotation requires repeated evidence; successful exercises are preserved.","exercises":rows}

def recovery_forecast(user_id,db_path):
    dash=training_dashboard(user_id,db_path); prog=database.get_progress_intelligence(user_id,db_path)
    fatigue=float((dash.get("mesocycle") or {}).get("fatigue_score") or 0)
    schedule=database.get_workout_schedule(user_id,db_path) or []
    density=min(3,max(0,len(schedule)-3))*.35
    base=fatigue+density
    mode="recovery" if base>=8 else "controlled" if base>=6 else "normal"
    days=[]
    for i in range(1,4):
        projected=max(0,base-(i-1)*.7)
        days.append({"day_offset":i,"projected_fatigue":round(projected,1),
                     "mode":"recovery" if projected>=8 else "controlled" if projected>=6 else "normal",
                     "confidence":"medium" if i>1 else "high"})
    return {"version":"1.0","current_fatigue":round(fatigue,1),"training_density_adjustment":round(density,1),
            "next_session_mode":mode,"days":days,"signals":prog.get("signals") or [],
            "note":"Forecast is advisory and is recalculated from actual readiness before the workout."}

def explainable_programming(user_id,db_path):
    gov=decision_governance(user_id,db_path); decisions=database.list_programming_decisions(user_id,30,db_path)
    cards=[]
    for d in decisions:
        cards.append({"id":d.get("id"),"title":str(d.get("decision_type","programming change")).replace("_"," ").title(),
                      "target":d.get("target_name") or d.get("target_type"),"what_changed":{"from":d.get("old_value"),"to":d.get("new_value")},
                      "why":d.get("evidence"),"confidence":d.get("confidence"),"scope":d.get("scope"),"duration":d.get("duration"),
                      "applied":d.get("applied")})
    return {"version":"1.0","governance":gov,"cards":cards,
            "legend":{"session":"Today only","week":"Current/next training week","program":"Persistent programming change"}}
