# Forge Fitness v14.34

Workout customization release built from v14.33.1.

## Added
- Adjustable planned set counters (1–12 sets) while logging a workout; changes persist to the current plan.
- Adjust Plan screen for 2–6 workouts/week, 20–90 minute session targets, and exact preferred training days.
- Safe plan rebuild endpoint that updates the profile and regenerates the program around new constraints.
- AI Coach context now includes normal workouts/week and session-duration constraints and gives safer guidance for schedule/time changes.
- Existing v14.33.1 Supabase fail-safe behavior retained.

## Behavior
Changing the number of workouts or normal session length rebuilds the current program so the generator can rebalance it. Preferred weekdays are then applied to the newly generated workouts. Adjustable set changes affect the current generated plan immediately.
