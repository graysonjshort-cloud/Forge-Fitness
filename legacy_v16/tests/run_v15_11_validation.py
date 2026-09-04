from pathlib import Path
import re,json,collections
r=Path(__file__).resolve().parents[1]
app=(r/'app.js').read_text()
idx=(r/'index.html').read_text()
sw=(r/'sw.js').read_text()
arch=json.loads((r/'FRONTEND_ARCHITECTURE_V15_11.json').read_text())
mods=[x['file'] for x in arch['modules']]
texts={m:(r/'js'/m).read_text() for m in mods}
all_frontend=app+'\n'+'\n'.join(texts.values())

assert (r/'VERSION.txt').read_text().strip()=='16.0.1'
assert len(app)<100000, f'app.js should stay an orchestration layer, got {len(app)} bytes'
assert arch['app_js_bytes']==(r/'app.js').stat().st_size
assert arch['architecture_target_bytes']==100000
for m in mods:
    assert f'/js/{m}?v=16.0.1' in idx,m
    assert f'/js/{m}?v=16.0.1' in sw,m
    assert len(texts[m])<60000,(m,len(texts[m]))
assert idx.index('/js/forge_plan_runtime.js?v=16.0.1') < idx.index('/app.js?v=16.0.1')

# Major domain bodies are no longer in app.js.
for fn in ['welcome','home','workout','exercise','nutrition','progress','coach','planScreen','calendarsettings']:
    assert not re.search(rf'(?m)^(?:async\s+)?function\s+{fn}\s*\(',app),fn
    assert re.search(rf'(?m)^(?:async\s+)?function\s+{fn}\s*\(',all_frontend),fn

# No accidental duplicate top-level function declarations across extracted runtime.
names=re.findall(r'(?m)^(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(',all_frontend)
dupes=[n for n,c in collections.Counter(names).items() if c>1]
assert not dupes,dupes

# Orchestration stays centralized.
for token in ['function render()','function go(','async function startWorkout','async function saveSet','async function act(']:
    assert token in app,token

print(json.dumps({'status':'passed','version':'16.0.1','app_js_bytes':(r/'app.js').stat().st_size,'extracted_modules':len(mods),'extracted_module_bytes':sum((r/'js'/m).stat().st_size for m in mods)},indent=2))
