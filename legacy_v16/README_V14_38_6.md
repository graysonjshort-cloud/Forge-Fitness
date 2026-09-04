# Forge Fitness v14.38.6

Progress feature modularization release.

- Added `js/forge_progress.js`.
- The feature now owns these routes through `ForgeFeatures`: progress, history, prs, exercisehistory.
- Existing view implementations remain behind a compatibility bridge so behavior is unchanged while route ownership is separated safely.
- This is an incremental refactor protected by the v14.38.x release gate.
