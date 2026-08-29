# Forge Fitness v14.62.0 — Sequence Integrity & Exercise Deduplication

v14.62 tightens custom split scheduling and exercise selection integrity.

## Custom split sequence is fixed
Custom split workout order now follows workout index exactly. The earliest selected training day receives Day 1, the next selected training day receives Day 2, and so on. Rest days are gaps only and never reorder the split. Example: Monday / Wednesday / Friday maps Day 1 -> Monday, Day 2 -> Wednesday, Day 3 -> Friday.

The custom split builder also shows the calendar weekday next to each configured day when a schedule is known.

## Exercise quota without repeats
`exercises_per_day` remains a target, but Forge will never repeat the same exercise to force the requested count. If the eligible exercise pool or session-time fit cannot supply enough unique movements, the workout is returned with `exercise_quota_met=false` and a user-facing `exercise_quota_message` explaining the shortfall.

## Duplicate exercise audit
Canonical aliases were consolidated so they no longer appear or generate as separate exercises:
- Overhead Dumbbell Triceps Extension -> Dumbbell Overhead Triceps Extension
- Cable Overhead Triceps Extension -> Overhead Cable Triceps Extension
- Trap Bar Deadlift -> Trap-Bar Deadlift
- Treadmill Incline Walk -> Incline Treadmill Walk
- Farmer's Carry -> Farmer Carry

Legitimate variations such as High-to-Low Cable Fly and Low-to-High Cable Fly remain separate.

## Validation
- Static validation: passed
- Frontend API contract validation: passed
- Precision plan validation: passed
- Full E2E flow: passed
- Exercise directory: 215 canonical exercises, all with muscle links
- No duplicate names inside generated PPL workouts
- Quota shortfall behavior verified without exercise repetition
