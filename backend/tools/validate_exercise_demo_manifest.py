from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/"exercise_demo_manifest.json").read_text())
errors=[]
for a in manifest.get("assets",[]):
    if not a.get("exercise_name"): errors.append("Asset missing exercise_name")
    if a.get("status") in {"asset_ready","reviewed"}:
        p=ROOT/a["primary_asset"].lstrip("/")
        if not p.exists(): errors.append(f'Missing file for {a["exercise_name"]}: {p}')
    if a.get("reviewed") and not all(a.get("review_checklist",{}).values()):
        errors.append(f'{a["exercise_name"]}: reviewed=true but checklist incomplete')
print(f'Checked {len(manifest.get("assets",[]))} planned demo assets.')
if errors:
    print("\n".join("ERROR: "+e for e in errors));sys.exit(1)
print("Manifest validation passed.")
