# Forge Fitness v14.24 — Progress Intelligence

Forge now combines multiple parts of the user's actual data to explain progress instead
of showing the strength chart in isolation.

## Progress Intelligence
- 30-day workout adherence.
- 30-day estimated-strength direction.
- Recent four-workout volume versus the previous four completed workouts.
- Recent average effort (RPE).
- Current Forge fatigue score.
- 14-day nutrition consistency against the user's current calorie/protein targets.
- Plateau, decline, recovery-pressure, progressing, steady, and insufficient-data states.
- A 0–100 Progress Intelligence score when sufficient metrics are available.
- Clear recommendations based on the limiting signal instead of blindly increasing volume.

## AI Coach
The Coach understands `Am I progressing?`, `Am I plateauing?`, `Why am I not progressing?`,
`What is limiting my progress?`, and `Analyze my progress.` It uses the same deterministic
Progress Intelligence result as the Progress screen.

## UI
The Progress screen now includes a Progress Intelligence card with the current state,
score, adherence/strength/recovery/nutrition signals, leading recommendation, and an
Ask Coach About My Progress button.

## Current limitation
Nutrition consistency uses the current targets because historical nutrition target revisions
are not versioned yet. Forge states this limitation instead of pretending old targets are known.
