from __future__ import annotations
import json, os, sys, time, urllib.request, urllib.error, subprocess, shutil, socket
from pathlib import Path

SOURCE=Path(__file__).resolve().parents[1]
RUNTIME=Path(os.environ.get("FORGE_TEST_RUNTIME","/mnt/data/forge_v14_27_e2e_runtime"))
PORT=int(os.environ.get("FORGE_TEST_PORT","8765"))
BASE=f"http://127.0.0.1:{PORT}"

def req(method,path,body=None,token=None):
    data=None if body is None else json.dumps(body).encode()
    headers={"Content-Type":"application/json"}
    if token: headers["Authorization"]=f"Bearer {token}"
    r=urllib.request.Request(BASE+path,data=data,headers=headers,method=method)
    try:
        with urllib.request.urlopen(r,timeout=15) as res:
            raw=res.read().decode()
            return res.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw=e.read().decode()
        raise AssertionError(f"{method} {path} -> {e.code}: {raw}") from e

def wait_server():
    for _ in range(100):
        try:
            s,d=req("GET","/health")
            if s==200:return d
        except Exception:
            time.sleep(.15)
    raise RuntimeError("API did not start")

def main():
    if RUNTIME.exists(): shutil.rmtree(RUNTIME)
    shutil.copytree(SOURCE,RUNTIME,ignore=shutil.ignore_patterns("__pycache__","tests","*.zip"))
    # Start with a fresh app database but retain seeded exercise schema/data.
    original=RUNTIME/"fitness_app_initial_database.sqlite"
    env=os.environ.copy()
    env["FORGE_LLM_ENABLED"]="0"
    env["PYTHONPATH"]=str(RUNTIME)
    p=subprocess.Popen(
        [sys.executable,"-m","uvicorn","fitness_backend_api_v2_connected:app","--host","127.0.0.1","--port",str(PORT)],
        cwd=RUNTIME,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True
    )
    try:
        health=wait_server()
        assert health["status"]=="ok"

        email=f"v1427-{int(time.time())}@forge.test"
        _,reg=req("POST","/auth/register",{"email":email,"password":"ForgeTest123!","display_name":"Flow Tester"})
        token=reg["token"]
        _,me=req("GET","/auth/me",token=token)
        assert me["display_name"]=="Flow Tester"

        profile={
            "goal":"build_muscle","experience":"intermediate","days_per_week":4,
            "minutes_per_workout":45,"equipment":["full_gym"],
            "preferred_exercises":[],"excluded_exercises":[],"priority_muscles":[],
            "recovery_level":"normal","cardio_preference":"moderate","workout_split":"upper_lower",
            "sport":"general","core_workouts_per_week":2,"cardio_workouts_per_week":2,"exercises_per_day":6,"seed":1427
        }
        req("POST","/me/profile",profile,token)

        _,cat=req("GET","/me/equipment/catalog",token=token)
        assert len(cat["catalog"])==107
        selected=[{**{k:x[k] for k in ["key","name","category"]},"details":{},"is_custom":False} for x in cat["catalog"][:20]]
        _,elog=req("PUT","/me/equipment",{"items":selected},token)
        assert len(elog["items"])==20

        _,plan=req("POST","/me/plan/generate",{},token)
        assert len(plan["workouts"])==4
        _,current=req("GET","/me/plan/current",token=token)
        assert current["workouts"][0]["workout_id"]

        # v14.59 plan-generation regression coverage: PPL must resolve directly,
        # custom muscle-day splits must generate, and settings changes must fully rebuild.
        ppl={**profile,"workout_split":"push_pull_legs","custom_split":[]}
        _,saved=req("POST","/me/profile",ppl,token)
        assert saved["plan_regenerated"] is True
        assert saved["regenerated_plan"]["split"]==["Push A","Pull A","Legs A","Push B"]
        assert [w["name"] for w in saved["regenerated_plan"]["workouts"]]==["Push","Pull","Legs","Push"]
        custom_days=[
            {"name":"Chest + Triceps","muscles":["Chest","Triceps"],"submuscles":{"Chest":["Upper Chest"],"Triceps":["Triceps Long Head"]}},
            {"name":"Back + Biceps","muscles":["Back","Biceps"]},
            {"name":"Quads + Calves","muscles":["Quads","Calves"]},
            {"name":"Hamstrings + Glutes + Shoulders","muscles":["Hamstrings","Glutes","Shoulders"]},
        ]
        custom={**profile,"workout_split":"custom","custom_split":custom_days,"priority_muscles":["Chest"]}
        _,saved=req("POST","/me/profile",custom,token)
        assert saved["plan_regenerated"] is True
        assert saved["regenerated_plan"]["split"]==[x["name"] for x in custom_days]
        split_intel=saved["regenerated_plan"].get("split_intelligence") or {}
        assert any("Upper Chest" in (e.get("muscle_targets") or []) for e in saved["regenerated_plan"]["workouts"][0]["exercises"])
        assert split_intel.get("frequency",{}).get("Chest")==1
        assert "Chest" in split_intel.get("priority_muscles",[])
        assert any("Chest is high priority" in x for x in split_intel.get("warnings",[]))
        restored={**profile,"minutes_per_workout":50,"exercises_per_day":7}
        _,saved=req("POST","/me/profile",restored,token)
        assert saved["plan_regenerated"] is True
        assert saved["regenerated_plan"]["profile"]["minutes_per_workout"]==50
        assert saved["regenerated_plan"]["profile"]["exercises_per_day"]==7
        assert all(len(w["exercises"])==7 for w in saved["regenerated_plan"]["workouts"])
        profile=restored
        current=saved["regenerated_plan"]

        # Workout lifecycle: start, restore state, log a set, persist position/rest.
        first=current["workouts"][0]
        _,sess=req("POST",f"/me/workout/{first['workout_id']}/start",{},token)
        sid=sess["session_id"]
        _,resume=req("GET","/me/session/resume",token=token)
        assert resume["session_id"]==sid

        ex=first["exercises"][0]
        _,perf=req("POST","/me/performance",{
            "request_id":"v1427-flow-set-1","session_id":sid,"exercise_id":ex["exercise_id"],
            "completed_sets":1,"reps":[max(1,ex["min_reps"])],"difficulty":7.5,"weight":100,"skipped":False
        },token)
        assert perf["status"]=="recorded"
        assert perf.get("session_intelligence") and perf["session_intelligence"]["recommended_rest_seconds"] >= 30
        assert perf["session_intelligence"]["recommended_total_sets"] >= 1
        req("POST","/me/session/position",{"session_id":sid,"exercise_index":0,"set_index":1},token)
        req("POST","/me/session/rest/start",{"session_id":sid,"duration_seconds":60},token)
        _,resume2=req("GET","/me/session/resume",token=token)
        assert resume2["current_set_index"]==1 and resume2["rest_duration_seconds"]==60
        req("POST","/me/session/rest/clear",{"session_id":sid},token)

        # Nutrition lifecycle.
        req("PUT","/me/nutrition/targets",{"calories":2400,"protein_g":180,"carbs_g":275,"fat_g":70},token)
        today=time.strftime("%Y-%m-%d")
        _,food=req("POST","/me/nutrition/entries",{
            "entry_date":today,"meal_type":"Lunch","food_name":"Test chicken bowl",
            "calories":650,"protein_g":55,"carbs_g":70,"fat_g":18,"source":"E2E test"
        },token)
        _,day=req("GET",f"/me/nutrition?date={today}",token=token)
        assert day["totals"]["calories"]>=650

        # Coach fallback still functions without an API key.
        _,coach=req("POST","/me/coach",{"message":"What am I doing today?","workout_id":first["workout_id"]},token)
        assert coach.get("reply")

        # Action-oriented Coach: equipment-aware exercise swap.
        _,swap_coach=req("POST","/me/coach",{"message":f"Swap {ex['name']} for an equipment-compatible alternative","workout_id":first["workout_id"]},token)
        if swap_coach.get("action"):
            assert swap_coach["action"]["action_type"]=="swap_exercise"
            _,applied=req("POST","/me/coach/apply",swap_coach["action"],token)
            assert applied["status"]=="applied"

        # Finish current week so adaptive next-week generation can be tested.
        req("POST","/me/workout/complete",{"session_id":sid,"completed":True},token)
        _,current=req("GET","/me/plan/current",token=token)
        for w in current["workouts"][1:]:
            _,s=req("POST",f"/me/workout/{w['workout_id']}/start",{},token)
            req("POST","/me/workout/complete",{"session_id":s["session_id"],"completed":True},token)

        _,preview=req("GET","/me/program/adaptation-preview",token=token)
        assert preview["can_apply"] is True
        _,adapt=req("POST","/me/program/apply-adaptation",{},token)
        assert adapt["plan"]["weekly_controller"]["recommendation"] in {"progress","maintenance","recovery"}

        # Progress/history after full flow.
        _,hist=req("GET","/me/history",token=token)
        assert len(hist)>=4
        _,intel=req("GET","/me/progress/intelligence",token=token)
        assert "signals" in intel and "recommendations" in intel

        print(json.dumps({
            "status":"passed",
            "tested":[
                "health","register/login session","profile","equipment catalog/log",
                "plan generation/current plan","workout start/resume/set logging + session intelligence",
                "position persistence","persistent rest","nutrition targets/food logging",
                "AI Coach fallback/actionable exercise swap","week completion","adaptive next-week generation",
                "history/progress intelligence"
            ],
            "equipment_catalog_count":len(cat["catalog"]),
            "workouts_generated":len(plan["workouts"]),
            "history_rows":len(hist),
            "adaptation":adapt["plan"]["weekly_controller"]["recommendation"]
        },indent=2))
    finally:
        p.terminate()
        try:p.wait(timeout=5)
        except subprocess.TimeoutExpired:p.kill()
        if p.returncode not in (0,-15,None):
            err=p.stderr.read() if p.stderr else ""
            if err: print(err,file=sys.stderr)

if __name__=="__main__":
    main()
