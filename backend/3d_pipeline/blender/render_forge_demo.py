"""
Forge Fitness 3D demo renderer — v14.37.1

Run inside Blender:
  blender -b forge_athlete_master.blend -P render_forge_demo.py -- \
    --job ../exercise_render_jobs.json --exercise barbell-bench-press --view side

Expected source scene:
  Collection: FORGE_ATHLETE
  Armature: ForgeAthleteRig
  Camera objects: Camera_Side, Camera_Front, Camera_Front3Q
  Exercise actions named:
    BackSquat, BarbellBenchPress, RomanianDeadlift, BarbellOverheadPress, PullUp

The script renders PNG frames. encode_webm.py performs the delivery encode.
"""
import bpy, json, argparse, sys
from pathlib import Path

def args_after_double_dash():
    return sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []

p=argparse.ArgumentParser()
p.add_argument("--job", required=True)
p.add_argument("--exercise", required=True)
p.add_argument("--view", required=True)
p.add_argument("--out", default=None)
a=p.parse_args(args_after_double_dash())

jobs=json.loads(Path(a.job).read_text())
job=next((x for x in jobs["exercises"] if x["slug"]==a.exercise),None)
if not job: raise SystemExit("Unknown exercise slug")

action_names={
 "back-squat":"BackSquat",
 "barbell-bench-press":"BarbellBenchPress",
 "romanian-deadlift":"RomanianDeadlift",
 "barbell-overhead-press":"BarbellOverheadPress",
 "pull-up":"PullUp",
}
camera_names={"side":"Camera_Side","front":"Camera_Front","front-3q":"Camera_Front3Q"}

rig=bpy.data.objects.get("ForgeAthleteRig")
if not rig: raise SystemExit("ForgeAthleteRig not found in source .blend")
action=bpy.data.actions.get(action_names[job["slug"]])
if not action: raise SystemExit(f"Animation action missing: {action_names[job['slug']]}")
camera=bpy.data.objects.get(camera_names[a.view])
if not camera: raise SystemExit(f"Camera missing: {camera_names[a.view]}")

rig.animation_data_create()
rig.animation_data.action=action
scene=bpy.context.scene
scene.camera=camera
scene.frame_start=1
scene.frame_end=job["frames"]
scene.render.fps=job["fps"]
scene.render.resolution_x=720
scene.render.resolution_y=720
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=False

out=Path(a.out or f"renders/{job['slug']}-{a.view}")
out.mkdir(parents=True,exist_ok=True)
scene.render.filepath=str(out/"frame_")
bpy.ops.render.render(animation=True)
print(f"Rendered {job['slug']} {a.view}: {scene.frame_end} frames -> {out}")
