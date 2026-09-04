# Forge Fitness v14.37.4.3

Fixes the `NameError: name 'args' is not defined` regression in v14.37.4.2.

The Blender generator now includes a dedicated `args()` helper that:
- reads only arguments after Blender's `--` separator;
- requires `--athlete`;
- accepts `--out`;
- keeps the v14.37.4.2 skeleton-aware MPFB calibration and Blender 5.2 fixes intact.

Run from `3d_pipeline\blender`:

    "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --python build_bench_press_mpfb.py -- --athlete "C:\ForgeAthlete\forge_athlete_base.blend" --out forge_bench_press_mpfb_review.blend
