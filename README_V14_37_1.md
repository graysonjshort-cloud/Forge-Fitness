# Forge Fitness v14.37.1 — 3D Production Pipeline

This release turns the v14.37.0 WebM delivery architecture into a reproducible production pipeline.

Included:
- Five locked reference render jobs: Back Squat, Bench Press, RDL, Overhead Press, Pull-Up.
- Side + front/front-3Q camera requirements.
- 720×720, 30 fps delivery target.
- Blender batch-render automation expecting a real Forge athlete rig and named exercise actions.
- VP9 WebM encoding helper.
- WebP poster extraction helper.
- Render-pack validation that refuses missing/tiny/invalid media.
- Production manifests and movement checkpoints for each reference exercise.

Important: this package does not contain fake 3D videos. A rigged Blender athlete/equipment source and the five approved animation actions are still required to create the real WebM files. Once those source assets exist, this pipeline renders, encodes, validates, and imports them into the app.
