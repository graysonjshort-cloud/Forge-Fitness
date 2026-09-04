# Forge Fitness v14.37.5.3 — Stage A

This build does only one thing: place the intact MPFB athlete correctly on the bench.

Stage A changes:
- MPFB armature/object transforms are preserved.
- All imported athlete objects are parented under a dedicated `FORGE_ATHLETE_ROOT`.
- Only that parent is rotated and translated.
- Skeleton basis determines body-longitudinal, lateral and anterior directions.
- Target orientation is head toward the rack, left/right across the bench, chest upward.
- No arm IK.
- No leg posing.
- No animation.
- Bar remains racked and out of the way.

Approval criteria for frame 1:
1. athlete is intact;
2. athlete lies straight along the bench;
3. athlete is face-up;
4. shoulders/torso are centered on the pad;
5. limbs are not twisted by the positioning transform.

Do not proceed to Stage B until all five are true.
