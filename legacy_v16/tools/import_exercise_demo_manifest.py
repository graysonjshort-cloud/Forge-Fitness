from pathlib import Path
import json, sqlite3, sys
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/"exercise_demo_manifest.json").read_text())
db_path=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/"fitness_app.db"
con=sqlite3.connect(db_path)
con.row_factory=sqlite3.Row
updated=0;missing=[]
for a in manifest["assets"]:
    if a.get("status") not in {"asset_ready","reviewed"}: continue
    row=con.execute("SELECT id FROM exercises WHERE lower(name)=lower(?)",(a["exercise_name"],)).fetchone()
    if not row:
        missing.append(a["exercise_name"]);continue
    con.execute("""UPDATE exercise_form_demos SET demo_asset=?,demo_type='svg',
      animation_status=?,reviewed=?,demo_version=demo_version+1,updated_at=CURRENT_TIMESTAMP
      WHERE exercise_id=?""",(a["primary_asset"],a["status"],1 if a.get("reviewed") else 0,row["id"]))
    updated+=1
con.commit();con.close()
print(f"Registered {updated} demo assets.")
if missing: print("Exercise names not matched:",", ".join(missing))
