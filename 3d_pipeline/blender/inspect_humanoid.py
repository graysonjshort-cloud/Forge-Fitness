import bpy,sys,argparse
from pathlib import Path
a=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
p=argparse.ArgumentParser();p.add_argument('--character',required=True);x=p.parse_args(a);e=Path(x.character).suffix.lower()
if e=='.fbx':bpy.ops.wm.fbx_import(filepath=x.character,use_anim=False,ignore_leaf_bones=True)
elif e in {'.glb','.gltf'}:bpy.ops.import_scene.gltf(filepath=x.character)
else:raise SystemExit('Use FBX or GLB/GLTF')
for arm in [o for o in bpy.context.scene.objects if o.type=='ARMATURE']:
 print('ARMATURE',arm.name);print('\n'.join('  '+b.name for b in arm.data.bones))
print('SKINNED MESHES',[o.name for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)])
