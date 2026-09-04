# Forge Fitness v14.37.4.1

Compatibility patch for Blender 5.2.1 LTS.

## Fixed
`build_bench_press_mpfb.py` no longer accesses the removed `Action.fcurves`
property directly. Blender 5.x stores F-Curves in the assigned action slot's
channelbag. The script now resolves that channelbag through
`bpy_extras.anim_utils.animdata_get_channelbag_for_assigned_slot()` and sets
the generated bar-path keyframes to BEZIER interpolation there.

A fallback remains for older Blender versions that still expose
`Action.fcurves`.

No change is required to the Forge athlete `.blend` file.
