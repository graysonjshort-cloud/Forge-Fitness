# Forge Fitness v14.37.4 — MPFB Standard Rig Bench Press

This release targets the actual MPFB/MakeHuman athlete you created in Blender. It no longer expects a generic downloaded FBX.

## Keep the master safe
Do not overwrite `forge_athlete_base.blend`. The Bench Press builder reads it and creates a separate review scene.

## 1. Inspect the MPFB rig (recommended first run)
From `3d_pipeline\blender`:

```bat
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --python inspect_mpfb_standard_rig.py -- --athlete "C:\FULL\PATH\forge_athlete_base.blend"
```

## 2. Build the Bench Press review scene
```bat
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --python build_bench_press_mpfb.py -- --athlete "C:\FULL\PATH\forge_athlete_base.blend" --out forge_bench_press_mpfb_review.blend
```

If your `.blend` contains multiple armatures, use `--armature "ExactName"`.

## 3. Open the generated file
Open `forge_bench_press_mpfb_review.blend` normally in Blender. Review frames **1, 45, 58 and 100**.

Check, in this order:
1. athlete lies centered on the pad;
2. head/upper back/butt contact looks sensible;
3. hands land on the bar at an appropriate width;
4. wrists/elbows deform naturally;
5. bar lowers to the lower/mid chest rather than neck or abdomen;
6. bar returns to a stable lockout;
7. clothes do not clip badly.

The builder exposes `--athlete-z`, `--athlete-y`, and `--grip-width` so alignment can be tuned without editing source code.

## 4. Validate after visual approval
```bat
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b forge_bench_press_mpfb_review.blend --python validate_mpfb_bench_press.py
```

## Important
v14.37.4 intentionally stops at a **review scene**. It does not auto-render a bad pose. Once the MPFB skeleton mapping and Bench Press geometry look correct on your athlete, the next patch can lock the approved offsets and render the side/front-3Q delivery WebMs for the phone.
