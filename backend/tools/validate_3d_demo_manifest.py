from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
m=json.loads((ROOT/"exercise_demo_3d_manifest.json").read_text())
errors=[]
for a in m.get("assets",[]):
    if a.get("status") not in {"planned","production_queued","source_ready","awaiting_humanoid","asset_ready","reviewed"}:
        errors.append(f'{a.get("exercise_name")}: invalid status')
    for key in ("primary_webm","secondary_webm"):
        value=a.get(key)
        if not value or not value.lower().endswith(".webm"):
            errors.append(f'{a.get("exercise_name")}: {key} must be .webm')
        if a.get("status") in {"asset_ready","reviewed"}:
            p=ROOT/value.lstrip("/")
            if not p.exists(): errors.append(f'{a.get("exercise_name")}: missing {p}')
    if a.get("status")=="reviewed" and not a.get("reviewed"):
        errors.append(f'{a.get("exercise_name")}: reviewed status without reviewed=true')
print(f'Checked {len(m.get("assets",[]))} 3D demo entries.')
if errors:
    print("\n".join("ERROR: "+x for x in errors));sys.exit(1)
print("3D manifest validation passed.")
