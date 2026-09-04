# Forge Fitness v14.64.1 — Custom Split Rebuild Fix

## Fixed
- Adjust Plan now sends the current `custom_split` through both `/me/plan/preview` and `/me/plan/reconfigure`.
- Changing days/week while Custom Split is active no longer leaves the backend using the old custom-day count.
- Preview uses the submitted custom split without mutating the stored profile.
- Reconfigure persists the submitted custom split before full regeneration.
- Custom workout sequence and explicitly selected weekdays remain preserved.

## Root cause
The v14.64 frontend resized `profile.custom_split` when days/week changed, but the preview/reconfigure request omitted that field. The backend therefore combined the new `days_per_week` with the old stored custom split and raised a custom-day-count mismatch.

## Regression coverage
E2E now tests a four-day Custom Split being expanded to five days through preview and rebuild, including exact weekday assignment.
