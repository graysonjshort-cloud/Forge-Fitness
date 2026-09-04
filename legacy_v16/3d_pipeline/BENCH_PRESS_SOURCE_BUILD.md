# v14.37.2 — Bench Press 3D Source Build

The first procedural Forge 3D source scene is now defined.

## Requirements
Install Blender 4.x locally. The ChatGPT build environment used to create this package does not include Blender, so the `.blend` file and WebM cannot be truthfully generated or rendered here.

## Build source scene
From `3d_pipeline/blender`:

```bash
blender -b --python build_bench_press_scene.py -- --out forge_bench_press_master.blend
```

## Validate source
```bash
blender -b forge_bench_press_master.blend --python validate_bench_press_source.py
```

## Render side view
```bash
blender -b forge_bench_press_master.blend -P render_forge_demo.py --   --job ../exercise_render_jobs.json --exercise barbell-bench-press --view side   --out ../renders/barbell-bench-press-side
```

## Render front 3/4 view
```bash
blender -b forge_bench_press_master.blend -P render_forge_demo.py --   --job ../exercise_render_jobs.json --exercise barbell-bench-press --view front-3q   --out ../renders/barbell-bench-press-front-3q
```

Then use `encode_webm.py` and `make_poster.py`, copy the resulting delivery files to `/assets/exercise_demos_3d/`, set the manifest entry to `asset_ready`, validate, and import it.

The scene builder creates the athlete rig, body meshes, bench, rack, barbell/plates, lighting, cameras, and Bench Press animation programmatically so this first reference scene is reproducible rather than dependent on an opaque manual Blender file.
