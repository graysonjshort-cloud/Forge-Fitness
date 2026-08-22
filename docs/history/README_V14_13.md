# Forge Fitness v14.13 — Cardio Frequency

Cardio now works like Core Training.

Users choose how many regular workouts per week should include a cardio add-on,
from 0 up to their selected training-days-per-week.

Forge distributes those cardio add-ons across the week and, where possible,
offsets them from Core add-ons so every extra block is not stacked onto the same
sessions.

Each cardio-enhanced workout stores:
- `cardio_included`
- `cardio_name`
- `cardio_minutes`

The workout screen displays a Cardio Add-On card beneath the strength exercise
list, and the weekly workout list shows a `Cardio` indicator.

The existing `cardio_preference` field is retained internally for cardio duration
and sport-aware cardio selection. Choosing 0 cardio sessions sets it to `none`;
choosing cardio again restores `moderate` if it was previously `none`.
