# Forge Fitness v14.37.4

The 3D pipeline now targets the saved MPFB/MakeHuman Standard Rig athlete directly from `forge_athlete_base.blend`.

Added:
- complete `.blend` athlete import, preserving skin, hair and clothing objects;
- flexible MakeHuman/MPFB arm-bone mapping;
- Bench Press bench/rack/barbell scene;
- bar-parented left/right grip targets;
- arm IK intended to keep both hands attached to the moving bar;
- controlled eccentric/pause/concentric bar path;
- side, front and front-3/4 review cameras;
- adjustable athlete Y/Z placement and grip width;
- MPFB rig inspector and Bench Press review validator.

The release deliberately creates a review `.blend` before any WebM render so the first real athlete can be visually approved and calibrated.
