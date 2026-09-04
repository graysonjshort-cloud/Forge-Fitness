"""Forge Fitness v14.37.4 - MPFB/MakeHuman Standard Rig Bench Press builder.

Designed for the saved forge_athlete_base.blend created in MPFB.
It imports the complete dressed athlete, maps common MakeHuman/MPFB Standard Rig
bone names, adds a bench/rack/barbell, lays the athlete on the bench, creates
bar-following hand IK targets, animates one controlled rep, and saves a review
scene.  Render only after visual review.
"""
import bpy, sys, argparse, math, re
from pathlib import Path
from mathutils import Vector

def cli():
    av=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    p=argparse.ArgumentParser()
    p.add_argument('--athlete', required=True, help='forge_athlete_base.blend')
    p.add_argument('--out', default='forge_bench_press_mpfb_review.blend')
    p.add_argument('--armature', default='')
    p.add_argument('--athlete-z', type=float, default=1.14)
    p.add_argument('--athlete-y', type=float, default=-0.08)
    p.add_argument('--grip-width', type=float, default=0.72)
    return p.parse_args(av)

def clean():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)

def append_scene_objects(path):
    path=Path(path)
    if not path.exists(): raise SystemExit(f'Athlete file not found: {path}')
    if path.suffix.lower()!='.blend': raise SystemExit('v14.37.4 expects the MPFB master as a .blend file.')
    with bpy.data.libraries.load(str(path), link=False) as (src,dst): dst.objects=list(src.objects)
    imported=[]
    for o in dst.objects:
        if o:
            bpy.context.collection.objects.link(o); imported.append(o)
    return imported

def n(s): return re.sub(r'[^a-z0-9]','',s.lower())

def pick(arm, candidates, contains=()):
    bones=list(arm.data.bones); by={n(b.name):b.name for b in bones}
    for c in candidates:
        if n(c) in by:return by[n(c)]
    for b in bones:
        nb=n(b.name)
        if all(x in nb for x in contains): return b.name
    return None

def map_standard_rig(arm):
    M={
      'hips':pick(arm,['pelvis','hips','root'],('pelvis',)),
      'chest':pick(arm,['spine03','spine2','chest','spine.003'],('spine',)),
      'head':pick(arm,['head','head01'],('head',)),
      'upper_l':pick(arm,['upperarm01.L','upper_arm.L','upperarm.L','LeftArm'],('upperarm','l')),
      'lower_l':pick(arm,['lowerarm01.L','forearm.L','lowerarm.L','LeftForeArm'],('lowerarm','l')),
      'hand_l':pick(arm,['wrist.L','hand.L','LeftHand'],('wrist','l')),
      'upper_r':pick(arm,['upperarm01.R','upper_arm.R','upperarm.R','RightArm'],('upperarm','r')),
      'lower_r':pick(arm,['lowerarm01.R','forearm.R','lowerarm.R','RightForeArm'],('lowerarm','r')),
      'hand_r':pick(arm,['wrist.R','hand.R','RightHand'],('wrist','r')),
    }
    missing=[k for k in ['upper_l','lower_l','hand_l','upper_r','lower_r','hand_r'] if not M[k]]
    if missing:
        print('\nAVAILABLE BONES:');print('\n'.join('  '+b.name for b in arm.data.bones))
        raise SystemExit('Could not map required MPFB arm bones: '+', '.join(missing))
    return M

def mat(name,c,metal=.0,rough=.45):
    m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    if bs:
        bs.inputs['Base Color'].default_value=(*c,1);bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough
    return m
DARK=None;STEEL=None;RED=None

def cube(name,loc,scale,material,bevel=.04):
    bpy.ops.mesh.primitive_cube_add(location=loc);o=bpy.context.object;o.name=name;o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    b=o.modifiers.new('Soft edges','BEVEL');b.width=bevel;b.segments=3;o.data.materials.append(material);return o

def equipment():
    global DARK,STEEL,RED
    DARK=mat('Forge_Dark',(.018,.023,.03),.1,.52);STEEL=mat('Forge_Steel',(.19,.22,.26),.72,.24);RED=mat('Forge_Red',(.94,.018,.055),.25,.28)
    cube('Bench_Pad',(0,0,1.00),(.32,1.12,.075),DARK,.06)
    cube('Bench_Frame',(0,0,.54),(.11,.82,.07),STEEL)
    for y in (-.78,.78):cube('Bench_Foot',(0,y,.36),(.43,.075,.075),STEEL)
    for x in (-.74,.74):
        cube('Rack_Post',(x,.58,1.23),(.055,.055,.85),STEEL)
        cube('Rack_JHook',(x,.49,1.69),(.09,.12,.04),STEEL)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=.025,depth=2.22,location=(0,0,1.78),rotation=(0,math.radians(90),0))
    bar=bpy.context.object;bar.name='BenchPress_Barbell';bar.data.materials.append(RED)
    for x in (-1.04,-.94,.94,1.04):
        bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=.19,depth=.055,location=(x,0,1.78),rotation=(0,math.radians(90),0))
        p=bpy.context.object;p.name='Plate';p.data.materials.append(DARK);p.parent=bar
    return bar

def empty(name,loc,parent=None):
    bpy.ops.object.empty_add(type='SPHERE',radius=.055,location=loc);o=bpy.context.object;o.name=name;o.parent=parent;return o

def setup_ik(arm,M,bar,grip):
    # Targets are parented to the bar, so grip follows the bar path exactly.
    targets={}
    for side,sgn in [('l',-1),('r',1)]:
        t=empty('GripTarget_'+side.upper(),(sgn*grip,0,0),bar);t.location=(sgn*grip,0,0)
        targets[side]=t
        hand=arm.pose.bones[M['hand_'+side]]
        c=hand.constraints.new('IK');c.name='Forge_Bench_Grip_IK';c.target=t;c.chain_count=3;c.use_tail=True;c.iterations=64
    return targets

def animate(arm,bar):
    sc=bpy.context.scene;sc.frame_start=1;sc.frame_end=105;sc.render.fps=30
    # Whole dressed athlete lies supine along Y; preserve all child relationships.
    arm.rotation_mode='XYZ';arm.rotation_euler=(math.radians(90),0,0)
    arm.keyframe_insert('rotation_euler',frame=1)
    # Controlled eccentric, pause, concentric.
    for f,z in [(1,1.78),(10,1.78),(45,1.35),(58,1.35),(100,1.78),(105,1.78)]:
        bar.location.z=z;bar.keyframe_insert('location',frame=f)
    # Blender 5.x stores Action F-Curves inside slot channelbags rather than
    # exposing Action.fcurves directly. keyframe_insert() already creates the
    # appropriate Action/slot/layer/strip; resolve that assigned channelbag.
    if bar.animation_data and bar.animation_data.action:
        try:
            from bpy_extras.anim_utils import animdata_get_channelbag_for_assigned_slot
            channelbag = animdata_get_channelbag_for_assigned_slot(bar.animation_data)
            if channelbag:
                for fc in channelbag.fcurves:
                    for kp in fc.keyframe_points:
                        kp.interpolation='BEZIER'
        except (ImportError, AttributeError):
            # Compatibility fallback for older Blender versions.
            action = bar.animation_data.action
            if hasattr(action, 'fcurves'):
                for fc in action.fcurves:
                    for kp in fc.keyframe_points:
                        kp.interpolation='BEZIER'

def place_athlete(imported,arm,z,y):
    # Move/rotate the armature only; skinned meshes and parented clothes follow it.
    arm.location=(0,y,z);arm.rotation_mode='XYZ';arm.rotation_euler=(math.radians(90),0,0)
    # Keep rig visible in review but not renders.
    arm.show_in_front=True

def camera(name,loc,target,lens=58):
    bpy.ops.object.camera_add(location=loc);c=bpy.context.object;c.name=name;c.data.lens=lens
    c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();return c

def scene():
    bpy.context.scene.world.color=(.006,.009,.013)
    cube('Floor',(0,0,.02),(3.7,3.7,.025),DARK,.01)
    camera('Camera_Side',(3.85,-.05,2.05),(0,0,1.18),62)
    camera('Camera_Front3Q',(3.05,-3.15,2.38),(0,0,1.20),58)
    camera('Camera_Front',(0,-4.15,2.18),(0,0,1.20),60)
    for loc,e,size in [((0,-3.0,3.9),1100,3.0),((2.6,1.5,2.7),650,2.4),((-2.5,1.7,3.0),800,2.2)]:
        bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.data.energy=e;l.data.shape='DISK';l.data.size=size
    sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=720;sc.render.resolution_y=720;sc.render.resolution_percentage=100;sc.camera=bpy.data.objects['Camera_Side']


def import_athlete(path):
    """v14.37.4.4 adapter around the known-good v14.37.4.1 blend append helper."""
    return append_scene_objects(path)

def find_arm(imported):
    """Resolve the appended MPFB armature from returned objects or the current scene."""
    if imported:
        try:
            for o in imported:
                if getattr(o, "type", None) == "ARMATURE":
                    return o
        except TypeError:
            pass
    arms=[o for o in bpy.context.scene.objects if o.type=="ARMATURE"]
    if not arms:
        return None
    # Prefer a Standard Rig with the known MPFB bones.
    for o in arms:
        names=set(o.data.bones.keys())
        if "upperarm01.L" in names and "upperarm01.R" in names:
            return o
    return arms[0]

def bone_map(arm):
    return map_standard_rig(arm)

# ---- Forge v14.37.4.5 MPFB pose-solver rewrite -----------------------------
from mathutils import Vector, Matrix, Quaternion
import math

def _wpoint(arm, bone_name, tail=False):
    pb=arm.pose.bones.get(bone_name)
    if not pb: return None
    return arm.matrix_world @ (pb.tail if tail else pb.head)

def _find_bone(arm, candidates):
    for n in candidates:
        if n and arm.pose.bones.get(n): return n
    return None

def _bench_pad():
    # Never infer the bench from generic scene geometry: this prevents the
    # athlete solver from touching the old floor/platform mesh.
    for n in ("Bench_Pad","Bench_Top"):
        o=bpy.data.objects.get(n)
        if o: return o
    # Known generator bench mesh is named Bench when available.
    o=bpy.data.objects.get("Bench")
    return o

def _reset_pose_channels(arm):
    for pb in arm.pose.bones:
        pb.matrix_basis=Matrix.Identity(4)

def _safe_remove_constraints(pb):
    # Solver owns only arm-chain IK for this review scene.
    for c in list(pb.constraints):
        if c.type=="IK" or c.name.startswith("FORGE_"):
            pb.constraints.remove(c)

def _empty(name, loc):
    o=bpy.data.objects.get(name)
    if not o:
        o=bpy.data.objects.new(name,None)
        bpy.context.scene.collection.objects.link(o)
    o.location=loc
    o.empty_display_type='SPHERE'
    o.empty_display_size=.045
    o.hide_render=True
    return o

def _arm_chain_names(arm,M,side):
    if side=="L":
        upper=M.get("upper_l"); lower=M.get("lower_l"); hand=M.get("hand_l")
        pole_sign=1
    else:
        upper=M.get("upper_r"); lower=M.get("lower_r"); hand=M.get("hand_r")
        pole_sign=-1
    return upper,lower,hand,pole_sign

def _add_two_bone_ik(arm,M,side,wrist_world,elbow_hint_world):
    upper,lower,hand,pole_sign=_arm_chain_names(arm,M,side)
    if not upper or not lower: return None,None
    lower_pb=arm.pose.bones.get(lower)
    if not lower_pb: return None,None
    _safe_remove_constraints(lower_pb)
    target=_empty("FORGE_WRIST_"+side,wrist_world)
    pole=_empty("FORGE_ELBOW_POLE_"+side,elbow_hint_world)
    c=lower_pb.constraints.new("IK")
    c.name="FORGE_ARM_IK_"+side
    c.target=target
    c.pole_target=pole
    c.chain_count=2
    c.use_tail=True
    c.use_stretch=False
    # Pole angle is determined from the actual rest chain; start neutral.
    c.pole_angle=0.0
    return target,pole

def _key_empty(o,loc,frame):
    o.location=loc
    o.keyframe_insert(data_path="location",frame=frame)

def _athlete_landmarks(arm,M):
    sl=_wpoint(arm,M.get("upper_l"))
    sr=_wpoint(arm,M.get("upper_r"))
    hips=_wpoint(arm,M.get("hips"))
    chest=_wpoint(arm,M.get("chest"))
    head=_wpoint(arm,M.get("head"))
    return sl,sr,hips,chest,head

def calibrate_athlete_to_bench(imported,arm,M):
    """Translation-only calibration. Never rotates/scales the entire athlete."""
    _reset_pose_channels(arm)
    bpy.context.view_layer.update()
    pad=_bench_pad()
    sl,sr,hips,chest,head=_athlete_landmarks(arm,M)
    if sl is None or sr is None:
        raise RuntimeError("MPFB shoulder landmarks unavailable")
    shoulder=(sl+sr)*.5

    if pad:
        corners=[pad.matrix_world @ Vector(c) for c in pad.bound_box]
        xs=[p.x for p in corners]; ys=[p.y for p in corners]; zs=[p.z for p in corners]
        pad_center=Vector(((min(xs)+max(xs))*.5,(min(ys)+max(ys))*.5,max(zs)))
        long_x=(max(xs)-min(xs)) >= (max(ys)-min(ys))
        rackward=Vector((-1,0,0)) if long_x else Vector((0,-1,0))
        desired=pad_center + rackward*.28 + Vector((0,0,.12))
    else:
        desired=Vector((0,0,.84))

    # Translation only. The athlete's imported orientation is preserved.
    arm.location += desired-shoulder
    bpy.context.view_layer.update()
    print("FORGE v14.37.4.5: athlete translation-calibrated; armature rotation/scale preserved")
    return {"pad":pad}

def _bar_axis_from_shoulders(sl,sr):
    v=sl-sr
    v.z=0
    if v.length < 1e-5: return Vector((0,1,0))
    return v.normalized()

def build_anatomical_bench_press(arm,M,bar,calibration=None):
    """Constraint-based two-bone solve: bar -> wrists, poles -> elbows."""
    _reset_pose_channels(arm)
    bpy.context.view_layer.update()
    sl,sr,hips,chest,head=_athlete_landmarks(arm,M)
    if sl is None or sr is None: raise RuntimeError("Shoulder landmarks missing")
    shoulder=(sl+sr)*.5
    sw=(sl-sr).length
    sw=max(.32,min(.62,sw))
    bar_axis=_bar_axis_from_shoulders(sl,sr)

    # Press direction uses world Z only; torso placement is already calibrated.
    lock=shoulder+Vector((0,0,.48))
    bottom=shoulder+Vector((.10,0,.16))
    grip=max(.30,min(.58,sw*.82))

    # Keep existing bar geometry/orientation; only animate its location.
    if bar:
        for fr,pos in ((1,lock),(20,lock),(45,bottom),(58,bottom),(85,lock),(100,lock)):
            bar.location=pos
            bar.keyframe_insert(data_path="location",frame=fr)

    # Create persistent IK wrist and elbow-pole targets once.
    wl_lock=lock+bar_axis*grip; wr_lock=lock-bar_axis*grip
    wl_bot=bottom+bar_axis*grip; wr_bot=bottom-bar_axis*grip

    # Elbow hints are lateral but tucked toward torso; importantly they are not
    # solved by rotating bones independently.
    el_lock=shoulder+bar_axis*(grip*.58)+Vector((.02,0,.22))
    er_lock=shoulder-bar_axis*(grip*.58)+Vector((.02,0,.22))
    el_bot=shoulder+bar_axis*(grip*.72)+Vector((.08,0,.02))
    er_bot=shoulder-bar_axis*(grip*.72)+Vector((.08,0,.02))

    tl,pl=_add_two_bone_ik(arm,M,"L",wl_lock,el_lock)
    tr,pr=_add_two_bone_ik(arm,M,"R",wr_lock,er_lock)
    if not all((tl,pl,tr,pr)): raise RuntimeError("Could not create both MPFB arm IK chains")

    for fr,wlp,wrp,elp,erp in (
        (1,wl_lock,wr_lock,el_lock,er_lock),
        (20,wl_lock,wr_lock,el_lock,er_lock),
        (45,wl_bot,wr_bot,el_bot,er_bot),
        (58,wl_bot,wr_bot,el_bot,er_bot),
        (85,wl_lock,wr_lock,el_lock,er_lock),
        (100,wl_lock,wr_lock,el_lock,er_lock)):
        _key_empty(tl,wlp,fr); _key_empty(tr,wrp,fr)
        _key_empty(pl,elp,fr); _key_empty(pr,erp,fr)

    bpy.context.scene.frame_start=1
    bpy.context.scene.frame_end=105
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    print("FORGE v14.37.4.5: two-bone IK arm solver generated")

def hide_review_clutter(arm):
    if arm:
        arm.show_in_front=False
        arm.hide_render=True
    # Hide helper empties in render only; keep them visible in viewport for
    # calibration diagnosis. Cameras/lights are left alone so the scene remains usable.
    for o in bpy.context.scene.objects:
        if o.name.startswith("FORGE_"):
            o.hide_render=True
# ---------------------------------------------------------------------------

def args():
    import argparse, sys
    argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser(description="Forge MPFB skeleton-calibrated bench press review")
    p.add_argument("--athlete",required=True)
    p.add_argument("--out",default="forge_bench_press_mpfb_review.blend")
    return p.parse_args(argv)


def main():
    a=args()
    imported=import_athlete(a.athlete)
    arm=find_arm(imported)
    if arm is None:
        raise RuntimeError("No MPFB armature found after athlete import.")
    M=bone_map(arm)
    bar=equipment()
    calibration=calibrate_athlete_to_bench(imported,arm,M)
    build_anatomical_bench_press(arm,M,bar,calibration)
    scene()
    hide_review_clutter(arm)
    bpy.context.scene.frame_set(1)
    out_path=str(Path(a.out).resolve())
    bpy.ops.wm.save_as_mainfile(filepath=out_path)
    print("FORGE v14.37.4.6 POSE-SOLVER MPFB REVIEW SCENE SAVED:",out_path)
    print("BONE MAP:",M)
    print("Review frames 1, 45, 58, 100 before rendering.")
if __name__=="__main__":
    main()
