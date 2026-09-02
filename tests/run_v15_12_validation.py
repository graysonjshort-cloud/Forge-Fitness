from pathlib import Path
import subprocess, textwrap
r=Path(__file__).resolve().parents[1]
app=(r/"app.js").read_text(); idx=(r/"index.html").read_text(); sw=(r/"sw.js").read_text()
state=(r/"js/forge_workout_state.js").read_text()
for token in ["ForgeWorkoutState","persistWorkoutSnapshot","clampSet","recoverContext","exerciseinspect"]:
    assert token in app+state, token
assert 'S.set=0;await persistPosition();go("exercise")' not in app
assert 'if(S.set>=effectiveSetCount(e))' in app
assert "/js/forge_workout_state.js?v=16.0.0" in idx
assert "/js/forge_workout_state.js?v=16.0.0" in sw
assert (r/"app.js").stat().st_size < 100000

# Simulate crash/reload snapshot behavior in Node.
script=r"""
global.window=global;
const store={};
global.localStorage={getItem:k=>store[k]??null,setItem:(k,v)=>store[k]=String(v),removeItem:k=>delete store[k]};
require('./js/forge_workout_state.js');
ForgeWorkoutState.snapshot({sessionId:9,workoutId:22,exerciseId:101,exerciseIndex:2,setIndex:3,setGoal:5,restRemaining:74,restTotal:90,restContext:{base:60,recommended:90}});
const x=ForgeWorkoutState.recoverContext({sessionId:9,workoutId:22,exerciseId:101});
if(!x||x.set_index!==3||x.rest_remaining!==74)process.exit(2);
if(ForgeWorkoutState.clampSet(8,5)!==4)process.exit(3);
if(ForgeWorkoutState.recoverContext({sessionId:10,workoutId:22,exerciseId:101})!==null)process.exit(4);
ForgeWorkoutState.clear();
if(ForgeWorkoutState.read()!==null)process.exit(5);
"""
p=subprocess.run(["node","-e",script],cwd=r,text=True,capture_output=True)
assert p.returncode==0,p.stderr
print("v15.12 workout-state reliability validation passed")
