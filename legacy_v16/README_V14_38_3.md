# Forge Fitness v14.38.3

Nutrition feature modularization release.

- Added `js/forge_nutrition.js`.
- The feature now owns these routes through `ForgeFeatures`: nutrition, nutritionadd.
- Existing view implementations remain behind a compatibility bridge so behavior is unchanged while route ownership is separated safely.
- This is an incremental refactor protected by the v14.38.x release gate.
