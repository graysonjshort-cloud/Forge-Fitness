# Forge Fitness v14.40.0 — Daily Workout Intelligence

Built on v14.39.0.

## User-facing improvements
- Faster logging: previous exercise performance now prefills the logging form and adds a one-tap **Repeat Last Set** action.
- In-workout history: **Full History** opens the current exercise's history without hunting through Progress.
- Smarter progression explanation: the next-target card explains why Forge recommends increasing load, holding load, or building reps using recent RPE and rep performance.
- Redesigned workout completion summary: duration, exercises, completed sets, volume, PRs, and a clear explanation of how the session feeds the next progression target.
- Completion metrics are refreshed from workout history after the session closes, while retaining a local duration fallback.

## Scope
This release intentionally reuses Forge's existing progression engine and exercise-history API rather than introducing a second progression algorithm in the frontend.
