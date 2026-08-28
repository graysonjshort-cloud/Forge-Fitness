"""
Forge Fitness v14.37.6.2
Stage B Pass 2 — Foot-target / knee-pole leg solver.

Architecture retained from v14.37.6.1:
- open the manually calibrated .blend directly;
- preserve the athlete's global transform;
- do not rebuild or reorient the scene;
- modify only leg pose controls.

This pass replaces fixed leg rotations with two-bone IK targets.
"""

import bpy
import sys
import argparse
from pathlib import Path
from mathutils import Vector

def args():
    argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--calibration", default="forge_bench_press_calibration.blend")
    p.add_argument("--out", default="forge_bench_press_stage_b_review.blend")
    return p.parse_args(argv)

def open_calibration(path):
    p = Path(path).resolve()
    if not p.exists():
        raise RuntimeError(f"Calibration .blend not found: {p}")
    bpy.ops.wm.open_mainfile(filepath=str(p))
    print("FORGE v14.37.6.2 opened calibration scene:", p)

def find_armature():
    arms = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    if not arms:
        raise RuntimeError("No armature found in calibration scene.")
    for o in arms:
        names = set(o.data.bones.keys())
        if "upperarm01.L" in names and "upperarm01.R" in names:
            return o
    return arms[0]

def pick_bone(arm, *cands):
    for n in cands:
        if n and arm.pose.bones.get(n):
            return n
    return None

def map_bones(arm):
    M = {
        "hips": pick_bone(arm, "root", "pelvis", "hips"),
        "upper_l": pick_bone(arm, "upperarm01.L", "upperarm.L"),
        "upper_r": pick_bone(arm, "upperarm01.R", "upperarm.R"),
        "thigh_l": pick_bone(arm, "upperleg01.L", "upperleg.L", "thigh.L"),
        "shin_l":  pick_bone(arm, "lowerleg01.L", "lowerleg.L", "shin.L"),
        "foot_l":  pick_bone(arm, "foot.L", "foot01.L"),
        "thigh_r": pick_bone(arm, "upperleg01.R", "upperleg.R", "thigh.R"),
        "shin_r":  pick_bone(arm, "lowerleg01.R", "lowerleg.R", "shin.R"),
        "foot_r":  pick_bone(arm, "foot.R", "foot01.R"),
    }
    missing = [k for k in ("hips","upper_l","upper_r","thigh_l","shin_l","thigh_r","shin_r") if not M[k]]
    if missing:
        print("Available bones:")
        print(", ".join(pb.name for pb in arm.pose.bones))
        raise RuntimeError("Missing required Stage-B bones: " + ", ".join(missing))
    return M

def wpoint(arm, bone_name, tail=False):
    pb = arm.pose.bones.get(bone_name)
    if not pb:
        return None
    return arm.matrix_world @ (pb.tail if tail else pb.head)

def world_bone_length(arm, bone_name):
    a = wpoint(arm, bone_name, False)
    b = wpoint(arm, bone_name, True)
    return (b-a).length if a is not None and b is not None else 0.0

def floor_z():
    for name in ("Floor", "floor", "Ground", "ground"):
        o = bpy.data.objects.get(name)
        if o and o.type == "MESH":
            return max((o.matrix_world @ Vector(c)).z for c in o.bound_box)
    # Stable fallback for the calibrated Forge scene.
    return 0.0

def ensure_empty(name, location, size=0.05):
    o = bpy.data.objects.get(name)
    if not o:
        o = bpy.data.objects.new(name, None)
        bpy.context.scene.collection.objects.link(o)
    o.location = location
    o.empty_display_type = "SPHERE"
    o.empty_display_size = size
    o.hide_render = True
    return o

def clear_forge_leg_constraints(pb):
    for c in list(pb.constraints):
        if c.name.startswith("FORGE_LEG_") or c.type == "IK":
            pb.constraints.remove(c)

def body_axes(arm, M):
    hips = wpoint(arm, M["hips"])
    sl = wpoint(arm, M["upper_l"])
    sr = wpoint(arm, M["upper_r"])
    shoulders = (sl + sr) * 0.5

    headward = (shoulders - hips)
    if headward.length < 1e-6:
        raise RuntimeError("Could not derive bench/body longitudinal axis.")
    headward.normalize()
    footward = -headward

    lateral = (sl - sr)
    if lateral.length < 1e-6:
        lateral = Vector((0,1,0))
    lateral.normalize()

    # Flatten target directions to the floor plane.
    footward.z = 0.0
    if footward.length < 1e-6:
        footward = Vector((1,0,0))
    footward.normalize()

    lateral.z = 0.0
    if lateral.length < 1e-6:
        lateral = Vector((0,1,0))
    lateral.normalize()
    return hips, footward, lateral

def add_leg_ik(arm, shin_name, ankle_target, knee_pole, side):
    shin = arm.pose.bones.get(shin_name)
    if not shin:
        raise RuntimeError(f"Missing shin pose bone for {side}")

    clear_forge_leg_constraints(shin)

    ankle = ensure_empty(f"FORGE_LEG_ANKLE_{side}", ankle_target, 0.045)
    pole  = ensure_empty(f"FORGE_LEG_KNEE_POLE_{side}", knee_pole, 0.055)

    ik = shin.constraints.new("IK")
    ik.name = f"FORGE_LEG_IK_{side}"
    ik.target = ankle
    ik.pole_target = pole
    ik.chain_count = 2
    ik.use_tail = True
    ik.use_stretch = False

    return ankle, pole

def flatten_foot(arm, foot_name):
    """
    Keep foot treatment conservative: clear only the foot's own pose rotation.
    The ankle target establishes floor height; fine sole-angle tuning comes next
    if needed after visual review.
    """
    if not foot_name:
        return
    pb = arm.pose.bones.get(foot_name)
    if not pb:
        return
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)

def stage_b_leg_pose(arm, M):
    """
    Bench-press lower-body target:
    - both knees bent;
    - feet on the floor;
    - feet separated symmetrically;
    - feet slightly back toward the hips rather than far out in front;
    - calibrated torso/global transform untouched.
    """
    global_before = arm.matrix_world.copy()

    hips, footward, lateral = body_axes(arm, M)
    z_floor = floor_z()

    # Scale all target distances from the actual leg segments.
    femur = 0.5 * (
        world_bone_length(arm, M["thigh_l"]) +
        world_bone_length(arm, M["thigh_r"])
    )
    tibia = 0.5 * (
        world_bone_length(arm, M["shin_l"]) +
        world_bone_length(arm, M["shin_r"])
    )
    leg_len = max(0.55, femur + tibia)

    # A compact, stable bench stance:
    # ankles roughly 55% of leg length footward of the hips and moderately wide.
    ankle_forward = leg_len * 0.55
    stance_half = leg_len * 0.18
    ankle_z = z_floor + max(0.035, leg_len * 0.045)

    # Knee poles sit above and somewhat footward of the hip, controlling knee bend plane.
    knee_forward = leg_len * 0.24
    knee_up = leg_len * 0.36
    knee_half = stance_half * 0.72

    for side, sign in (("L", 1.0), ("R", -1.0)):
        ankle_target = (
            hips
            + footward * ankle_forward
            + lateral * (stance_half * sign)
        )
        ankle_target.z = ankle_z

        knee_pole = (
            hips
            + footward * knee_forward
            + lateral * (knee_half * sign)
            + Vector((0,0,knee_up))
        )

        shin_name = M["shin_l"] if side == "L" else M["shin_r"]
        foot_name = M["foot_l"] if side == "L" else M["foot_r"]

        add_leg_ik(arm, shin_name, ankle_target, knee_pole, side)
        flatten_foot(arm, foot_name)

        print(f"FORGE v14.37.6.2 {side} ankle target:", tuple(round(v,4) for v in ankle_target))
        print(f"FORGE v14.37.6.2 {side} knee pole:", tuple(round(v,4) for v in knee_pole))

    bpy.context.view_layer.update()

    # Hard safety guard: never modify the calibrated global athlete transform.
    after = arm.matrix_world
    max_delta = max(
        abs(global_before[i][j] - after[i][j])
        for i in range(4) for j in range(4)
    )
    if max_delta > 1e-8:
        raise RuntimeError(
            f"Stage B altered armature global transform unexpectedly: {max_delta}"
        )

    print("FORGE v14.37.6.2 Stage B leg IK applied")
    print("FORGE v14.37.6.2 calibrated global athlete transform preserved")

def save_review(path):
    out = str(Path(path).resolve())
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 1
    bpy.context.scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print("FORGE v14.37.6.2 STAGE B REVIEW SAVED:", out)

def main():
    a = args()
    open_calibration(a.calibration)
    arm = find_armature()
    M = map_bones(arm)
    print("FORGE v14.37.6.2 bone map:", M)
    stage_b_leg_pose(arm, M)
    save_review(a.out)

if __name__ == "__main__":
    main()
