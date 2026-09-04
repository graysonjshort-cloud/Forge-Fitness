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

def main():
    a=cli();clean(); imported=append_scene_objects(a.athlete)
    arms=[o for o in imported if o.type=='ARMATURE']
    arm=bpy.data.objects.get(a.armature) if a.armature else (arms[0] if len(arms)==1 else None)
    if not arm:raise SystemExit(f'Expected one athlete armature; found {[x.name for x in arms]}. Use --armature NAME.')
    arm.name='ForgeAthleteRig';M=map_standard_rig(arm)
    bar=equipment();place_athlete(imported,arm,a.athlete_z,a.athlete_y);setup_ik(arm,M,bar,a.grip_width);animate(arm,bar);scene()
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(a.out).resolve()))
    print('FORGE v14.37.4 MPFB REVIEW SCENE SAVED:',Path(a.out).resolve());print('BONE MAP:',M)
    print('Review frames 1, 45, 58, 100 before rendering.')
main()
