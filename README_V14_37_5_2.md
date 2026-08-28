# Forge Fitness v14.37.5.2

Static orientation-calibration update.

Changes:
- derives the athlete's longitudinal, lateral and anterior axes from the real MPFB skeleton;
- constructs a deterministic rotation that maps the body longitudinal axis to the bench,
  left/right across the bench, and chest/anterior upward;
- removes the guessed fixed 90-degree rotation;
- preserves athlete scale while applying the orientation;
- aligns shoulders to the rack side of the bench after orientation;
- keeps the lower body neutral for this calibration pass;
- fixes barbell plate placement by removing problematic post-placement parenting.

This is still a static frame-1 calibration build. Do not render animation yet.
