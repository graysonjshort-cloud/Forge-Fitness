# Forge Fitness v14.74.3 — Active Workout / Swap Session Fix

This patch fixes the active-workout mismatch visible after exercise swaps or after resuming a persisted workout.

## Repairs
- Resume an active session by immutable `workout_id`, not only `workout_index`.
- Ignore stale sessions that do not belong to the current active plan.
- Restrict active-session discovery and workout start to the active program.
- Validate that logged sets belong to the exercise list of the active session workout.
- Preserve the v14.74.2 async-loader stability fixes.
- Prevent a stale session from accepting a set and then failing later inside Session Intelligence.

## Regression target
A workout may be regenerated or an exercise may be swapped while session data persists. Forge must keep the UI workout, session workout, and exercise membership aligned before accepting performance data.
