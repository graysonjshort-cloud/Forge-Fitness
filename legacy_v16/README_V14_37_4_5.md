# Forge Fitness v14.37.4.5

Pose-solver rewrite based on the v14.37.4.4 calibration screenshot.

Key changes:
- removes independent `_aim_pose_bone()` rotations;
- uses Blender IK constraints with `chain_count=2` on each forearm;
- wrist targets are fixed to two grip points on the same bar;
- dedicated elbow pole targets control each arm's bend plane;
- athlete calibration is translation-only: the generator no longer rotates or
  scales the whole MPFB armature from inferred torso vectors;
- bench lookup is restricted to bench objects and no longer treats generic
  platform/floor geometry as the bench;
- equipment geometry is not transformed by athlete calibration;
- keeps Blender 5.2-compatible animation handling inherited from earlier builds.

Review frames: 1, 45, 58, 100.
