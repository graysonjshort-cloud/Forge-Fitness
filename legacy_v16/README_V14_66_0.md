# Forge Fitness v14.66.0 — Reliable Adaptive Programming

This release combines Plan Reliability & Transparency with Adaptive Programming 2.0.

## Plan reliability

- Added `POST /me/plan/validate` preflight validation before rebuild preview/application.
- Validates workout-day counts, weekday selection, custom split completeness, exercise-count targets, and lock/exclusion conflicts.
- Added generated-plan invariants for workout count, custom split sequence, duplicate exercise IDs/names, and locked-exercise preservation.
- Preview now returns detailed per-workout diffs including exercise counts, added/removed/kept exercises, and set changes.
- Preview includes generator diagnostics and plan-audit warnings.
- Structured backend errors are rendered as readable messages instead of object strings.
- Existing v14.64.1 and v14.64.2 rebuild fixes remain covered.

## Adaptive Programming 2.0

- Converts real logged exercise history into explicit next-week decisions: `progress`, `hold`, `reduce`, or `rotate`.
- Decisions use recent skips, effort/RPE, reps, and logged load history.
- Exercise-level decisions are visible in the next-week adaptation preview.
- Decisions feed generator scoring, set targets, rep targets, and exercise rotation pressure.
- Weekly recovery recommendation still controls session-length/recovery pressure and weekly volume management.
- Existing adaptive set targets and session intelligence remain active.

## Validation

- Static validation: passed
- Frontend/backend contract validation: passed
- Precision plan validation: passed
- Full E2E flow: passed
- v14.66 targeted reliability/adaptation validation: passed
