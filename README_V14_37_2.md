# Forge Fitness v14.37.2

This release starts the actual source-asset stage.

## Bench Press
Added a procedural Blender scene builder that creates:
- Forge athlete armature.
- Filled 3D athlete body segments.
- Bench and rack.
- Barbell and plates.
- Side, front, and front-3/4 cameras.
- Forge-style materials and lighting.
- A keyed Barbell Bench Press motion cycle.
- A Blender-side source validator.

The source is reproducible from Python instead of being a manually-created opaque `.blend`.

## Important limitation
Blender is not installed in the build environment used for this package. Therefore the builder script has been created and syntax-validated, but a real `.blend` scene and rendered WebM are not falsely included. Run the included Blender command locally to build and validate the source scene, then use the v14.37.1 render/encode pipeline.

The other four reference exercises remain queued until the Bench Press source/render is visually approved.
