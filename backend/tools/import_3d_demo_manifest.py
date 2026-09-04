from pathlib import Path
import json,sqlite3,sys
ROOT=Path(__file__).resolve().parents[1]
DB=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/"fitness_app_initial_database.sqlite"
m=json.loads((ROOT/"exercise_demo_3d_manifest.json").read_text())
con=sqlite3.connect(DB)
con.row_factory=sqlite3.Row
registered=0
for a in m.get("assets",[]):
    if a.get("status") not in {"asset_ready","reviewed"}: continue
    ex=con.execute("SELECT id FROM exercises WHERE name=?",(a["exercise_name"],)).fetchone()
    if not ex:
        print("SKIP unmatched:",a["exercise_name"]);continue
    con.execute("""INSERT INTO exercise_demo_3d_assets
      (exercise_id,primary_webm,secondary_webm,poster_asset,primary_view,secondary_view,render_version,status,source_kind)
      VALUES (?,?,?,?,?,?,?,?,?)
      ON CONFLICT(exercise_id) DO UPDATE SET
       primary_webm=excluded.primary_webm,secondary_webm=excluded.secondary_webm,
       poster_asset=excluded.poster_asset,primary_view=excluded.primary_view,
       secondary_view=excluded.secondary_view,render_version=excluded.render_version,
       status=excluded.status,source_kind=excluded.source_kind,updated_at=CURRENT_TIMESTAMP""",
      (ex["id"],a["primary_webm"],a["secondary_webm"],a.get("poster_asset"),
       a.get("primary_view","side"),a.get("secondary_view","front"),
       a.get("render_version","forge_3d_v1"),a["status"],a.get("source_kind","original_3d")))
    con.execute("""UPDATE exercise_form_demos SET demo_asset=?,demo_type='webm',
      secondary_asset=?,primary_view=?,animation_status=?,reviewed=?
      WHERE exercise_id=?""",
      (a["primary_webm"],a["secondary_webm"],a.get("primary_view","side"),
       a["status"],1 if a.get("reviewed") else 0,ex["id"]))
    registered+=1
con.commit();con.close()
print(f"Registered {registered} 3D demo records.")
