import bpy,sys
err=[]
for n in ['ForgeAthleteRig','Bench_Pad','BenchPress_Barbell','GripTarget_L','GripTarget_R','Camera_Side','Camera_Front3Q']:
    if not bpy.data.objects.get(n):err.append('Missing '+n)
rig=bpy.data.objects.get('ForgeAthleteRig')
if rig:
    ik=sum(1 for p in rig.pose.bones for c in p.constraints if c.type=='IK' and c.name=='Forge_Bench_Grip_IK')
    if ik!=2:err.append(f'Expected 2 Forge grip IK constraints, found {ik}')
bar=bpy.data.objects.get('BenchPress_Barbell')
if not (bar and bar.animation_data and bar.animation_data.action):err.append('Barbell animation missing')
if err:
    print('\n'.join('ERROR: '+e for e in err));sys.exit(1)
print('v14.37.4 MPFB Bench Press review scene validation passed.')
