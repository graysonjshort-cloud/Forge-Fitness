# Forge Fitness v14.25 — Bodyweight + Measurement Tracking

v14.25 adds body-composition progress tracking directly to the existing Progress system.

## Body check-ins
Users can log bodyweight, body-fat percentage, waist, chest, hips, arm, thigh, and optional notes.
One check-in is stored per date. Logging the same date again updates that date instead of creating a duplicate.

## Progress screen
The new Body Tracking card includes the latest bodyweight, change across the selected range,
a 30D/90D/1Y/ALL weight trend, latest measurements, recent check-in history, and add/delete controls.

## Progress Intelligence
Bodyweight direction is now another Progress Intelligence signal. For current goals where
direction is meaningful, Forge compares the multi-week trend with the goal:
- lose_fat -> a downward bodyweight direction supports the goal
- build_muscle -> an upward bodyweight direction supports the goal

Forge does not treat a single day's scale change as meaningful and does not automatically
change training or nutrition from one measurement.

## AI Coach
The Coach understands questions such as `How is my weight trend?`, `Am I losing weight?`,
`Am I gaining weight?`, `How is my waist trend?`, and `Show my body measurement progress.`

## Validation
Create/update/delete, same-day upsert, weight and circumference trend math, AI body-progress
intent recognition, Python syntax, and JavaScript syntax passed.
