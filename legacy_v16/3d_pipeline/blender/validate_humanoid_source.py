import bpy,sys
e=[];r=bpy.data.objects.get('ForgeAthleteRig')
if not r or r.type!='ARMATURE':e.append('ForgeAthleteRig missing')
if not [o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]:e.append('No skinned humanoid mesh')
if e:print('\n'.join('ERROR '+x for x in e));sys.exit(1)
print('Humanoid source validation passed')
