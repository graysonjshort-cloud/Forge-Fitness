# Forge Fitness v15.10.4 — Workout Reliability

This patch addresses four issues observed during a real workout.

- Auto-added bonus sets now have a stable session-only set target and an explicit Finish Exercise option. A suggested bonus set is optional and can no longer trap the workout flow.
- Opening another exercise from the workout list while resting now opens a read-only preview. It does not change or persist the active exercise/set position.
- Plan generation now receives the exact Equipment Log keys and uses machine-specific compatibility rules. Specific machines no longer unlock unrelated generic-machine exercises, and EZ/trap bars no longer count as a general Olympic barbell. If a strict equipment filter removes a template option, Forge fills the requested exercise count with another unique compatible exercise for the same training day when available.
- Rest copy now distinguishes base rest from Forge's post-set recommendation. The timer starts with the same recommended value it reports and explains when rest was adjusted.
