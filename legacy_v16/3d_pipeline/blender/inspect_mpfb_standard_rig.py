import bpy,sys,argparse
from pathlib import Path
av=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
p=argparse.ArgumentParser();p.add_argument('--athlete',required=True);a=p.parse_args(av)
with bpy.data.libraries.load(a.athlete,link=False) as (src,dst):dst.objects=list(src.objects)
for o in dst.objects:
    if o:bpy.context.collection.objects.link(o)
arms=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
print('ARMATURES:',[x.name for x in arms])
for arm in arms:
    print('\n###',arm.name);print('\n'.join(b.name for b in arm.data.bones))
print('\nSKINNED/CLOTHING MESHES:')
for o in bpy.context.scene.objects:
    if o.type=='MESH':
        mods=[m.object.name if m.type=='ARMATURE' and m.object else '' for m in o.modifiers if m.type=='ARMATURE']
        print(o.name,'armature_modifiers=',mods,'parent=',o.parent.name if o.parent else None)
