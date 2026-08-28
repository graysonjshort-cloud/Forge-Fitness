# Forge Fitness v14.38.5

Plan feature modularization release.

- Added `js/forge_plan.js`.
- The feature now owns these routes through `ForgeFeatures`: plan, adjustplan, trainingsettings, calendarsettings.
- Existing view implementations remain behind a compatibility bridge so behavior is unchanged while route ownership is separated safely.
- This is an incremental refactor protected by the v14.38.x release gate.
