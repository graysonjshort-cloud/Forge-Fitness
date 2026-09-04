# v14.37.3 Humanoid Import

The primitive mannequin is retired. Supply a properly modeled, skinned humanoid you have rights to use. FBX is preferred; GLB/GLTF and BLEND are accepted by the builder.

Inspect:
```bat
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --python inspect_humanoid.py -- --character "C:\PATH\athlete.fbx"
```

Import into Forge source:
```bat
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --python build_bench_press_humanoid_scene.py -- --character "C:\PATH\athlete.fbx" --out forge_bench_press_humanoid.blend
```

If more than one armature is present, add `--armature "ExactName"`. Open the generated BLEND and visually approve the character before exercise retargeting/rendering.
