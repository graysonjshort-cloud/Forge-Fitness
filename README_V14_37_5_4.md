# Forge Fitness v14.37.5.4 — Stage A Back Alignment

This patch specifically addresses the athlete being rolled onto his side.

Changes:
- tests both possible torso-normal orientations;
- chooses the better face-up candidate;
- levels the shoulder line with a roll correction;
- centers pelvis + shoulder midpoint over the bench centerline;
- seats the athlete using actual mesh bounds;
- keeps the MPFB pose neutral;
- still uses no arm IK, no leg pose, and no animation.

Stage A is approved only when the athlete is clearly lying on his back,
straight along the bench, centered, and not distorted.
