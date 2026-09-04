# Forge Fitness v15.11.0 — Frontend Architecture & Modularization

This release removes the large-screen/runtime bodies from `app.js` and places them into domain-specific frontend files. `app.js` is now the orchestration layer: shared state, startup, routing, cross-domain coordination, event dispatch, session persistence, and API bridging.

Extracted domains:

- `forge_onboarding_ui.js` — onboarding, preferences, equipment/setup, exercise directory/demo screens.
- `forge_home_ui.js` — Home dashboard, readiness, weekly insights, and Home data loaders.
- `forge_workout_runtime.js` — workout/exercise screens, timers, core/cardio execution, swaps, completion.
- `forge_nutrition_ui.js` — nutrition screens and workout builder bridge.
- `forge_progress_runtime.js` — history, PRs, Progress Hub, charts, records, strategy panels.
- `forge_coach_runtime.js` — Coach, recovery, adaptive-week review.
- `forge_plan_runtime.js` — plan, rebuild, training settings, calendar settings.

The existing 250 KB `app.js` ceiling remains unchanged. The v15.11 architecture target is under 100 KB; this build is roughly 73 KB. Frontend contract validation now scans every JS module instead of only `app.js`, and browser smoke loads the exact module order declared in `index.html`.
