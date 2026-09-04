# Forge Fitness v14.37.6.2 — Stage B Pass 2

Built directly on the working v14.37.6.1 architecture.

What changes:
- the manually calibrated `.blend` remains the scene base;
- global athlete/bench orientation is untouched;
- fixed thigh/shin Euler-style rotations are removed;
- each leg now uses a 2-bone IK chain;
- ankle targets are placed on the floor at a symmetric bench-press stance;
- knee pole targets control the bend direction;
- foot pose is kept conservative for this review pass;
- hard guard still aborts if the athlete's global transform changes.

No arm/grip/bar animation work is added yet.
