# Forge Fitness v14.74.3 — Async Loader Stability

Fixes rerender-driven request loops and loading-state flicker across workout substitution and other async screens.

## Repairs
- Smart Swap substitutions are cached by exercise + swap reason and survive rerenders.
- Substitution Intelligence is cached by exercise and no longer refetches after its own render.
- Cardio swap options are cached by workout and survive rerenders.
- Exercise Previous Performance and progression loaders now allow a new exercise to supersede an older in-flight request safely.
- Progress Hub, strength trend, body metrics, progress intelligence, Plan adaptation/recovery, Coach briefing/context, Nutrition, Equipment, Exercise Directory, and System Health use in-flight guards to prevent sibling-loader request amplification.
- Workout History, PRs, and Exercise History now render from cached state rather than returning to Loading on harmless rerenders.
- Empty/error substitution results are treated as settled states so persistent errors cannot cause request storms.

## Regression focus
The browser debug suite forces repeated rerenders after loaders settle and checks that request counts do not increase for swap, substitution intelligence, exercise recall/progression, plan, progress, coach, cardio swap, workout history, PRs, and exercise history.
