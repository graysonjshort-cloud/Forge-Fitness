# Forge Fitness v14.37.5.6 — Forced Supine Alignment

This specifically fixes the athlete being placed stomach-down in v14.37.5.5.

What changed:
- preserves the already-correct head-to-feet / bench alignment;
- explicitly rolls the intact athlete 180° around the bench longitudinal axis;
- converts the current prone orientation into a supine orientation;
- re-runs shoulder leveling, centerline placement, and anatomical back seating afterward;
- the BACK remains the contact reference for the bench pad;
- still no arm IK, no leg posing, and no animation.

Stage A approval target:
- face/chest upward;
- back on the bench;
- body straight and centered;
- neutral untwisted limbs.
