# Forge Fitness v14.27 — Stabilization + Adaptive Coaching

v14.27 completes the seven-part stabilization and product-polish pass.

## 1. End-to-end workflow testing
`tests/run_e2e_flow.py` now exercises the real backend through HTTP in an isolated copy of the app:
account registration, profile setup, Equipment Log, plan generation, workout start/resume,
set logging, position persistence, persistent rest, nutrition, Coach, exercise swaps, week
completion, adaptive next-week generation, history, and progress intelligence.

`tests/run_static_validation.py` checks the route map, critical UI actions, responsive rules,
and all 107 Equipment Log assets.

## 2. Workout logging
The logging screen retains the v14.26 hierarchy and now shows up to four recent working sets
under Previous Performance. Session position and the rest state continue to persist through the
backend so a refresh/restart can resume the workout.

## 3. Equipment Log validation
All 107 active catalog items are validated against a corresponding standalone SVG asset.
Broken image loads fall back to `generic.svg`, and the fixed image/text/check-column layout from
v14.26.1 is retained.

## 4. AI Coach actions
Coach now has action-first shortcuts for readiness adjustment, equipment-aware smart swaps,
calendar fitting, and next-week review. A swap request can now produce a real `swap_exercise`
action and apply it directly. Elevated readiness/fatigue can produce a shortened-workout action.
Existing calendar scheduling, food logging, nutrition target, move/swap day, and shorten actions
remain available.

## 5. Adaptive programming
The Plan Overview now includes a Next-Week Adaptation card using completion, fatigue, recovery,
adherence, strength signals, and recorded training history. Once every workout in the current
week is completed or skipped, Forge can build the next week. The existing WeeklyProgramController
then chooses Progress, Maintenance, or Recovery and generates the adjusted plan.

New endpoints:
- `GET /me/program/adaptation-preview`
- `POST /me/program/apply-adaptation`

## 6. Responsive/mobile pass
Additional layouts are included for <=390px and <=340px phones, plus a wider >=700px layout.
The pass covers Home cards, Nutrition, Coach actions, previous-set history, adaptive metrics,
Plan calendar, Equipment Log rows, effort buttons, and keyboard focus states.

## 7. Release cleanup
Historical version notes are moved into `docs/history/`. The release includes:
- `START_BACKEND.bat`
- `START_UI.bat`
- `RUN_VALIDATION.bat`
- `VERSION.txt`
- automated validation scripts

## Validation result
The final build passed JavaScript/Python syntax validation, static UI validation across 29
application routes and all 107 equipment assets, and the full isolated HTTP workflow test.
