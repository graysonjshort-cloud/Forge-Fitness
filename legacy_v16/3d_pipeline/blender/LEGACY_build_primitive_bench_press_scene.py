"""
Forge Fitness v14.37.2
Procedurally builds the first Forge 3D source scene: Barbell Bench Press.

Run with Blender 4.x:
  blender -b --python build_bench_press_scene.py -- --out forge_bench_press_master.blend

The result contains:
  ForgeAthleteRig
  BarbellBenchPress action
  Camera_Side
  Camera_Front3Q
  Bench / rack / barbell / plates
  Forge-style lighting/materials

This is a production source scene, not a rendered delivery asset.
"""
import bpy, math, argparse, sys
from mathutils import Vector

def cli():
    argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="forge_bench_press_master.blend")
    return p.parse_args(argv)

def clean():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes,bpy.data.curves,bpy.data.materials,bpy.data.cameras,bpy.data.lights):
        pass

def mat(name,color,metallic=0.0,roughness=.45):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    bsdf=m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value=(*color,1)
    bsdf.inputs["Metallic"].default_value=metallic
    bsdf.inputs["Roughness"].default_value=roughness
    return m

SILVER=mat("Forge_Silver",(0.62,0.68,0.74),0.05,.38)
DARK=mat("Forge_Dark",(0.035,0.045,0.055),0.15,.5)
RED=mat("Forge_Red",(0.92,0.025,0.07),0.25,.3)
STEEL=mat("Equipment_Steel",(0.20,0.23,0.27),0.65,.28)
RUBBER=mat("Plate_Rubber",(0.055,0.06,0.07),0.05,.72)

def cube(name,loc,scale,material,bevel=.06):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o=bpy.context.object;o.name=name;o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bev=o.modifiers.new("Soft edges","BEVEL");bev.width=bevel;bev.segments=3
    o.data.materials.append(material)
    return o

def sphere(name,loc,r,material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=20,location=loc,radius=r)
    o=bpy.context.object;o.name=name;o.data.materials.append(material)
    return o

def capsule_mesh(name,length,radius,material):
    # Cylinder with UV spheres at ends, joined into one object.
    bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=radius,depth=length)
    cyl=bpy.context.object;cyl.name=name+"_body"
    cyl.data.materials.append(material)
    for z in (-length/2,length/2):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=radius,location=(0,0,z))
        s=bpy.context.object;s.data.materials.append(material)
        cyl.select_set(True);s.select_set(True);bpy.context.view_layer.objects.active=cyl
        bpy.ops.object.join()
    cyl.name=name
    return cyl

def build_rig():
    bpy.ops.object.armature_add(enter_editmode=True,location=(0,0,0))
    arm=bpy.context.object;arm.name="ForgeAthleteRig"
    eb=arm.data.edit_bones
    root=eb[0];root.name="root";root.head=(0,0,.65);root.tail=(0,0,.9)

    def bone(name,head,tail,parent=None):
        b=eb.new(name);b.head=head;b.tail=tail
        if parent:b.parent=parent
        return b

    pelvis=bone("pelvis",(0,0,.9),(0,0,1.08),root)
    spine=bone("spine",(0,0,1.08),(0,0,1.42),pelvis)
    chest=bone("chest",(0,0,1.42),(0,0,1.62),spine)
    neck=bone("neck",(0,0,1.62),(0,0,1.76),chest)
    head=bone("head",(0,0,1.76),(0,0,1.96),neck)

    for side,sx in (("L",-.24),("R",.24)):
        upper=bone(f"upper_arm.{side}",(sx,0,1.56),(sx*1.9,0,1.56),chest)
        fore=bone(f"forearm.{side}",(sx*1.9,0,1.56),(sx*2.75,0,1.56),upper)
        hand=bone(f"hand.{side}",(sx*2.75,0,1.56),(sx*3.0,0,1.56),fore)
        thigh=bone(f"thigh.{side}",(sx*.65,0,.98),(sx*.72,0,.56),pelvis)
        shin=bone(f"shin.{side}",(sx*.72,0,.56),(sx*.78,0,.18),thigh)
        foot=bone(f"foot.{side}",(sx*.78,0,.18),(sx*.78,-.22,.12),shin)

    bpy.ops.object.mode_set(mode="POSE")
    for pb in arm.pose.bones:
        pb.rotation_mode="XYZ"
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm

def bone_parent(obj,arm,bone_name,local_loc=(0,0,0),rot=(0,0,0)):
    obj.parent=arm
    obj.parent_type="BONE"
    obj.parent_bone=bone_name
    obj.location=local_loc
    obj.rotation_euler=rot

def build_athlete(arm):
    # Torso masses.
    torso=cube("Athlete_Torso",(0,0,0),(0.23,.13,.24),SILVER,.10)
    bone_parent(torso,arm,"chest",(0,0,-.10))
    pelvis=cube("Athlete_Pelvis",(0,0,0),(0.20,.12,.14),DARK,.08)
    bone_parent(pelvis,arm,"pelvis",(0,0,-.06))
    h=sphere("Athlete_Head",(0,0,0),.145,DARK);bone_parent(h,arm,"head",(0,0,.08))

    for side in ("L","R"):
        sign=-1 if side=="L" else 1
        ua=capsule_mesh(f"UpperArm_{side}",.38,.075,SILVER)
        bone_parent(ua,arm,f"upper_arm.{side}",(0,0,.19),(0,0,0))
        fa=capsule_mesh(f"Forearm_{side}",.33,.065,SILVER)
        bone_parent(fa,arm,f"forearm.{side}",(0,0,.165),(0,0,0))
        hand=sphere(f"Hand_{side}",(0,0,0),.072,RED);bone_parent(hand,arm,f"hand.{side}",(0,0,.06))
        th=capsule_mesh(f"Thigh_{side}",.42,.10,SILVER);bone_parent(th,arm,f"thigh.{side}",(0,0,.21))
        sh=capsule_mesh(f"Shin_{side}",.38,.085,SILVER);bone_parent(sh,arm,f"shin.{side}",(0,0,.19))
        ft=cube(f"Foot_{side}",(0,0,0),(.08,.16,.045),DARK,.04);bone_parent(ft,arm,f"foot.{side}",(0,-.07,0))

def build_bench_equipment():
    cube("Bench_Pad",(0,0,1.02),(.30,1.08,.07),DARK,.06)
    cube("Bench_Base",(0,0,.47),(.16,.85,.08),STEEL,.04)
    for y in (-.78,.78):
        cube("Bench_Leg_"+str(y),(0,y,.36),(.38,.09,.09),STEEL,.04)
    # Rack posts.
    for x in (-.72,.72):
        cube("Rack_Post_"+str(x),(x,.55,1.20),(.055,.055,.82),STEEL,.03)
        cube("Rack_JHook_"+str(x),(x,.47,1.69),(.085,.11,.04),STEEL,.03)

    # Bar along X axis.
    bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.025,depth=2.05,location=(0,0,1.78),rotation=(0,math.radians(90),0))
    bar=bpy.context.object;bar.name="BenchPress_Barbell";bar.data.materials.append(RED)
    # Plates.
    for x in (-1.00,-.88,.88,1.00):
        bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.19,depth=.055,location=(x,0,1.78),rotation=(0,math.radians(90),0))
        p=bpy.context.object;p.name=f"Plate_{x}";p.data.materials.append(RUBBER);p.parent=bar
    return bar

def animate_bench(arm,bar):
    scene=bpy.context.scene
    scene.frame_start=1;scene.frame_end=105;scene.render.fps=30
    act=bpy.data.actions.new("BarbellBenchPress")
    arm.animation_data_create();arm.animation_data.action=act

    # Athlete lies on back: rotate root around X so body's vertical rig is horizontal.
    root=arm.pose.bones["root"]
    root.rotation_mode="XYZ"
    root.rotation_euler=(math.radians(90),0,0)
    root.location=(0,-.08,.18)
    root.keyframe_insert("rotation_euler",frame=1);root.keyframe_insert("location",frame=1)

    # Shoulder/elbow geometry. Start locked, lower to chest, brief pause, press.
    frames=(1,38,55,105)
    for side in ("L","R"):
        sign=-1 if side=="L" else 1
        ua=arm.pose.bones[f"upper_arm.{side}"]
        fa=arm.pose.bones[f"forearm.{side}"]
        # After global body rotation, these rotations create elbow bend in bench plane.
        vals=[
            (math.radians(-10*sign),math.radians(8),math.radians(8*sign), math.radians(5*sign),0,0),
            (math.radians(-42*sign),math.radians(10),math.radians(22*sign), math.radians(78*sign),0,0),
            (math.radians(-42*sign),math.radians(10),math.radians(22*sign), math.radians(78*sign),0,0),
            (math.radians(-10*sign),math.radians(8),math.radians(8*sign), math.radians(5*sign),0,0),
        ]
        for f,v in zip(frames,vals):
            ua.rotation_euler=v[:3];fa.rotation_euler=v[3:]
            ua.keyframe_insert("rotation_euler",frame=f)
            fa.keyframe_insert("rotation_euler",frame=f)

    # Bar: 1.78m -> chest line ~1.34m.
    for f,z in ((1,1.78),(38,1.36),(55,1.36),(105,1.78)):
        bar.location.z=z
        bar.keyframe_insert("location",frame=f)

def camera(name,loc,target):
    bpy.ops.object.camera_add(location=loc)
    c=bpy.context.object;c.name=name
    direction=Vector(target)-c.location
    c.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
    c.data.lens=56
    return c

def lights():
    bpy.ops.object.light_add(type="AREA",location=(0,-3.0,3.8));key=bpy.context.object;key.name="Key";key.data.energy=950;key.data.shape="DISK";key.data.size=3.2
    bpy.ops.object.light_add(type="AREA",location=(2.6,1.5,2.5));fill=bpy.context.object;fill.name="Fill";fill.data.energy=600;fill.data.size=2.4
    bpy.ops.object.light_add(type="AREA",location=(-2.5,1.8,3.0));rim=bpy.context.object;rim.name="Rim";rim.data.energy=700;rim.data.size=2.0

def world():
    bpy.context.scene.world.color=(.012,.016,.021)
    cube("Floor",(0,0,.02),(3.8,3.8,.025),DARK,.01)

a=cli();clean();world()
arm=build_rig();build_athlete(arm);bar=build_bench_equipment();animate_bench(arm,bar)
camera("Camera_Side",(3.7,-.15,2.15),(0,0,1.15))
camera("Camera_Front3Q",(3.0,-3.2,2.45),(0,0,1.20))
camera("Camera_Front",(0,-4.2,2.1),(0,0,1.20))
lights()
bpy.context.scene.camera=bpy.data.objects["Camera_Side"]
bpy.context.scene.render.engine="BLENDER_EEVEE_NEXT"
bpy.context.scene.render.resolution_x=720;bpy.context.scene.render.resolution_y=720;bpy.context.scene.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(a.out))
print("Saved",a.out)
