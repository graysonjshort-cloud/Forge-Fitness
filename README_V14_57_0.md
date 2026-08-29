# Forge Fitness v14.57.0 — Adaptive Set Targets

Upgrades in-workout progression from a fixed load rule to exercise-aware targets based on the programmed rep range, recent RPE, recent reps, load mode, and available history.

## What changed
- Weighted exercises now progress through the rep range before load increases.
- Load increases use smaller, gym-realistic increments based on current load.
- High-effort or below-range performance can trigger a conservative load reduction.
- Bodyweight exercises progress primarily through reps.
- Timed exercises progress through hold duration.
- Targets include a human-readable reason, evidence count, and confidence level.
- The workout logger pre-fills the adaptive target instead of blindly copying the last set.
- Every completed set returns a fresh next-target recommendation for live in-session adjustment.
- System health version reporting is synchronized to v14.57.0.
