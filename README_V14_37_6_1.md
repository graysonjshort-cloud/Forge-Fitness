# Forge Fitness v14.37.6.1

This fixes v14.37.6.0 losing the manual athlete orientation.

The generator now opens `forge_bench_press_calibration.blend` directly with
`bpy.ops.wm.open_mainfile()` instead of appending the athlete into a new scene.

Stage B Pass 1:
- preserves the exact manual scene and athlete global transforms;
- finds the MPFB armature already present in the calibrated scene;
- changes only thigh/shin/foot pose bones;
- includes a hard guard that aborts if the armature global matrix changes;
- does not touch torso, arms, bar grip, animation, cameras, or equipment placement.

Run from `3d_pipeline\blender`:

    "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --python build_bench_press_mpfb.py -- --calibration forge_bench_press_calibration.blend --out forge_bench_press_stage_b_review.blend
