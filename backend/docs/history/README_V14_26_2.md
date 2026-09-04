# Forge Fitness v14.26.2 — Equipment Image Fix

The Equipment Log image system has been rebuilt to use one standalone SVG asset per active
equipment item instead of the previous large inline renderer.

What changed:
- 107 active equipment items now have 107 distinct equipment drawings.
- Each equipment image lives in `assets/equipment/`.
- Images are loaded as normal SVG assets, preventing inline gradient-ID collisions, clipping,
  and styling conflicts.
- The drawings come from the earlier equipment-specific geometry set where every item had a
  unique silhouette matched to its equipment type.
- Custom/unknown equipment uses a generic dumbbell fallback.
- The v14.26.1 row spacing/layout fix is retained.

Validation:
- 107 active catalog items
- 107 unique drawings
- 108 SVG files including the custom-equipment fallback
- JavaScript syntax passed
- Python syntax passed
