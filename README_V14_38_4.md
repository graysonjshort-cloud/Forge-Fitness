# Forge Fitness v14.38.4

Workout feature modularization release.

- Added `js/forge_workout.js`.
- The feature now owns these routes through `ForgeFeatures`: workout, exercise, timer, complete, swapexercise, cardioswap, modulemove, coretracker, cardiotracker.
- Existing view implementations remain behind a compatibility bridge so behavior is unchanged while route ownership is separated safely.
- This is an incremental refactor protected by the v14.38.x release gate.
