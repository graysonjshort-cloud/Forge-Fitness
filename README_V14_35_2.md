# Forge Fitness v14.35.2

## Separate strength / core / cardio
Strength workouts now contain strength exercises only. Core and cardio are separate modules assigned
to selected strength-training days, so a 4-day plan still counts as four workouts even when it also
contains two core circuits and two cardio sessions.

## Balanced Core Circuits
Each generated core circuit attempts to cover four functions:
- Lower abs / hip flexion
- Anti-extension
- Obliques (anti-lateral flexion, anti-rotation, or rotation)
- Trunk flexion

Core circuits use compatible equipment and retain Forge's exercise-intelligence scoring. Timed core
movements remain timed; bodyweight movements remain bodyweight.

## Complete bodyweight behavior
Every directory exercise whose equipment includes Bodyweight receives `bodyweight_default=true`.
The workout logger therefore defaults every bodyweight movement to Bodyweight, with an optional
Added Weight choice where appropriate.

## Adjustable timed exercise targets
Timed exercises now have +5 sec / -5 sec controls. The target is adjustable from 5 to 600 seconds,
while Forge still records the user's actual elapsed duration for history and Duration PRs.

## PWA update
v14.35.2 uses a new service-worker cache so installed phone apps can receive this release.
