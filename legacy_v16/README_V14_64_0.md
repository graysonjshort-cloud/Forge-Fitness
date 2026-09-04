# Forge Fitness v14.64.0 — Plan Generator 4.0 + Exercise Database 4.0

## Plan Generator 4.0
- Per-workout exercise-count targets (3–10) in addition to the global target.
- Preview-before-replace workflow for schedule/workout-size regeneration.
- Exercise locks anchored to workout sequence and preserved during regeneration.
- Plan-level "Never include" action for future generated plans.
- Detailed sub-muscle weekly set-equivalent audit.
- Movement-family redundancy warnings.
- Stronger similarity-family penalties during exercise selection.
- Existing custom-split sequence integrity, PPL naming, quota-shortfall behavior and full-plan regeneration remain intact.

## Exercise Database 4.0
Every canonical exercise receives normalized intelligence metadata:
- movement family
- similarity family
- joint stress
- stability demand
- skill demand
- fatigue cost

The generator uses this metadata to reduce redundant movement selection and prefer lower-fatigue alternatives when stimulus is comparable. The existing detailed broad-muscle/sub-muscle taxonomy, primary/secondary muscle links, exercise preferences, and substitution system remain integrated.

## Validation
- Static validation: passed
- Frontend/backend contract validation: passed (124 frontend API calls, 118 backend routes, 0 missing contracts)
- Precision plan validation: passed
- Full E2E flow: passed
- 215/215 canonical exercises have Database 4.0 intelligence rows
- Per-workout target test: 4 / 7 / 5 generated correctly
- Locked-exercise regeneration test: passed
- Plan audit generation: passed
