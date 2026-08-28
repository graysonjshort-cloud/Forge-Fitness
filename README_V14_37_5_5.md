# Forge Fitness v14.37.5.5 — Anatomical Back Contact

The athlete's BACK is now explicitly the bench-contact reference.

Important change:
- whole-body minimum mesh Z is NOT used for vertical placement;
- hands, feet, hair, and other extremities cannot determine bench height;
- shoulder midpoint + pelvis define the torso;
- a character-scaled posterior/back offset estimates the upper-back contact point;
- the athlete root is translated until that upper-back point reaches the bench pad;
- orientation from v14.37.5.4 is retained;
- shoulder placement is moved slightly away from the rack for head clearance.

Still Stage A:
- no arm IK;
- no leg posing;
- no exercise animation.

Approval requires the athlete to be face-up with the BACK visibly resting on the bench.
