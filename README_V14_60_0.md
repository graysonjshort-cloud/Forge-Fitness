# Forge Fitness v14.61.0 — Muscle Frequency & Priority Intelligence

v14.60 extends the custom split builder with weekly muscle-frequency controls, per-muscle priority, and split-quality warnings.

## What changed

- Added Weekly Muscle Targets to Custom Split 2.0.
- Each muscle now shows its current weekly training frequency.
- `+` and `−` controls add or remove that muscle from training days while preserving at least one muscle group per day.
- Forge chooses a less-crowded / better-spaced day when increasing frequency.
- Per-muscle Priority toggles reuse Forge's existing muscle-priority system.
- High-priority muscles receive stronger exercise-selection weighting and one extra set on the first matching custom-split movement when recovery/time trimming allow it.
- Added pre-generation split intelligence warnings for:
  - missing major muscle-group coverage,
  - back-to-back training-session overlap for the same muscle,
  - high-priority muscles with no weekly exposure,
  - high-priority muscles trained only once per week on schedules of 3+ days.
- Generated custom plans now include a `split_intelligence` payload with frequency, priority, warnings, and balance status.
- Existing v14.59 full-plan regeneration remains active, so saving these custom split or priority changes rebuilds the entire active plan.
- Updated PWA cache and app/backend version to 14.61.0.

## Validation

- Static frontend validation: passed.
- Frontend/backend contract validation: passed.
- Full E2E application flow: passed.
- E2E regression checks verify custom split intelligence, high-priority muscle state, and plan regeneration.
