import bpy,sys
required_objects=["ForgeAthleteRig","Bench_Pad","BenchPress_Barbell","Camera_Side","Camera_Front3Q"]
required_bones=["root","spine","chest","upper_arm.L","forearm.L","upper_arm.R","forearm.R"]
errors=[]
for n in required_objects:
    if not bpy.data.objects.get(n):errors.append("Missing object: "+n)
rig=bpy.data.objects.get("ForgeAthleteRig")
if rig:
    for b in required_bones:
        if b not in rig.data.bones:errors.append("Missing bone: "+b)
if not bpy.data.actions.get("BarbellBenchPress"):errors.append("Missing action: BarbellBenchPress")
if errors:
    print("\n".join("ERROR "+e for e in errors));sys.exit(1)
print("Bench press Blender source validation passed.")
