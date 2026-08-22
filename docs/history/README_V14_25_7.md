# Forge Fitness v14.25.7 — Equipment Icon Accuracy Pass

This change is implemented in the actual app UI.

The Equipment Log icon system was rebuilt so icons represent the equipment they label instead
of reusing a small handful of generic silhouettes.

## Coverage
- Active Equipment Log items: 107
- Explicit equipment-specific icons defined: 107
- Distinct SVG silhouettes: 107
- Active catalog items without a specific icon: 0

Major equipment families now have visually distinct illustrations, including specialty bars,
individual benches/racks, individual lower- and upper-body machines, cable attachments,
bodyweight stations, cardio machines, and lifting accessories.

Unknown/custom equipment uses a neutral dumbbell fallback rather than pretending it is a
specific piece of equipment.

## AI Coach grounding
Forge Coach now receives an explicit rule to use the exact names from the user's Equipment Log
when discussing equipment or exercise swaps, instead of casually treating similar pieces as
interchangeable.
