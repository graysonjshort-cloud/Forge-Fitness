# Forge Fitness v14.37.5.9

Rebased on v14.37.5.7.

Instead of stacking more 180-degree corrections, this version replaces the
Stage-A athlete placement with one anatomical transform:

- body/head axis -> rack end of bench;
- shoulder axis -> across the bench;
- chest/anterior -> world +Z;
- back/posterior -> world -Z toward the pad;
- after orientation, only translation/back-contact seating is performed.

No arm IK, leg posing, or animation is added.
