import bpy,sys,argparse
from pathlib import Path

def args():
 a=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
 p=argparse.ArgumentParser();p.add_argument("--character",required=True);p.add_argument("--out",default="forge_bench_press_humanoid.blend");p.add_argument("--armature",default="");return p.parse_args(a)
def clear(): bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
def import_char(p):
 p=Path(p);ext=p.suffix.lower()
 if not p.exists():raise SystemExit(f"Character not found: {p}")
 if ext=='.fbx':bpy.ops.wm.fbx_import(filepath=str(p),use_anim=False,ignore_leaf_bones=True)
 elif ext in {'.glb','.gltf'}:bpy.ops.import_scene.gltf(filepath=str(p))
 elif ext=='.blend':
  with bpy.data.libraries.load(str(p),link=False) as (src,dst):dst.objects=list(src.objects)
  for o in dst.objects:
   if o:bpy.context.collection.objects.link(o)
 else:raise SystemExit('Use FBX, GLB/GLTF, or BLEND')
def main():
 a=args();clear();import_char(a.character)
 arms=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
 arm=bpy.data.objects.get(a.armature) if a.armature else (arms[0] if len(arms)==1 else None)
 if not arm:raise SystemExit(f'Expected one humanoid armature; found {[x.name for x in arms]}. Use --armature NAME.')
 arm.name='ForgeAthleteRig'
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
 if not meshes:raise SystemExit('No skinned humanoid mesh found.')
 bpy.context.scene.render.engine='BLENDER_EEVEE'
 bpy.ops.wm.save_as_mainfile(filepath=str(Path(a.out).resolve()))
 print('Imported high-quality humanoid:',[m.name for m in meshes]);print('Bones:',[x.name for x in arm.data.bones]);print('Saved',Path(a.out).resolve())
main()
