from pathlib import Path
import json, shutil, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
jobs=json.loads((ROOT/"exercise_render_jobs.json").read_text())
assets=ROOT.parent/"assets"/"exercise_demos_3d"
errors=[]
ffprobe=shutil.which("ffprobe")
for j in jobs["exercises"]:
    for view in (j["primary_view"],j["secondary_view"]):
        p=assets/f'{j["slug"]}-{view}.webm'
        if not p.exists():
            errors.append(f"MISSING {p.name}")
            continue
        if p.stat().st_size < 10000:
            errors.append(f"TOO SMALL {p.name}")
        if ffprobe:
            r=subprocess.run([ffprobe,"-v","error","-select_streams","v:0","-show_entries",
                              "stream=codec_name,width,height,r_frame_rate","-of","json",str(p)],
                             capture_output=True,text=True)
            if r.returncode: errors.append(f"INVALID {p.name}: {r.stderr.strip()}")
if errors:
    print("\n".join(errors));sys.exit(1)
print("All five dual-view WebM demo pairs passed render-pack validation.")
