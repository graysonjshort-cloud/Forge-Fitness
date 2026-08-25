# Forge Fitness v14.37.0 — 3D Form Demo Pipeline

Forge has retired SVG diagrams as the primary form demonstration format.

## App
- Form Demo now prioritizes short looping WebM renders.
- Supports primary and secondary camera views with an in-player angle switch.
- If no 3D render exists, Forge shows a clean `3D demo in production` state while preserving written Setup, Form Cues, Breathing and Common Mistakes.
- Legacy SVG files remain in the repository as historical/fallback assets but are not presented as completed instructional animations.

## Data
- Added a dedicated `exercise_demo_3d_assets` table.
- Added a dedicated eight-gate 3D review table.
- Existing databases migrate non-destructively through `CREATE TABLE IF NOT EXISTS`.
- Registering a 3D asset changes the exercise's Form Guide media to WebM without deleting user workout data.

## Production pipeline
- Added a five-exercise v1 3D manifest: Back Squat, Barbell Bench Press, Romanian Deadlift, Barbell Overhead Press and Pull-Up.
- Requires side + front WebM views before a demo can become Reviewed.
- Added manifest validation and database import tools.
- Added a Forge 3D render standard covering character, equipment, cameras, motion and mobile review.

v14.37.0 intentionally establishes the 3D production system; it does not pretend the planned WebM renders already exist.
