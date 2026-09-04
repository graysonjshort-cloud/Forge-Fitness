# Forge Fitness v14.26.1 — Equipment Log Fix

This patch fixes the Equipment Log layout regression introduced by the v14.26 UI pass.

The real Equipment Log row markup is now handled correctly as three columns:
1. fixed equipment illustration,
2. flexible equipment name/details,
3. add/check control.

Selected equipment keeps its Edit button in a separate fourth area outside the main equipment card.

The fix also:
- restores clear spacing between illustrations and names,
- prevents names from touching or overlapping artwork,
- keeps long equipment names wrapping cleanly,
- keeps + / check controls aligned at the far right,
- preserves the layout on narrow screens.
