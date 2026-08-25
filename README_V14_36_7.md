# Forge Fitness v14.36.7

This release locks the first Forge motion-diagram visual standard and expands the real demo pack.

## Refined first five
The original first five were rebuilt against the exact exercise names in the database:
- Back Squat
- Barbell Bench Press
- Romanian Deadlift
- Barbell Overhead Press
- Pull-Up

## Expansion batch
Ten additional original SVG motion diagrams were added:
- Chin-Up
- Lat Pulldown
- Barbell Row
- One-Arm Dumbbell Row
- Push-Up
- Leg Press
- Lying Leg Curl
- Leg Extension
- Plank
- Hanging Knee Raise

## Integration
- Bundled assets now self-register against exact exercise names during schema startup, including existing persistent databases.
- Demo Review now shows the animation itself above the six-item review checklist.
- All 15 remain `asset_ready`, not `reviewed`, until the v14.36.6 checklist is actually passed.
- Existing offline demo caching continues to work with these SVG assets.
