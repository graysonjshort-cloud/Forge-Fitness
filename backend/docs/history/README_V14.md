# Forge Fitness v14 — Dynamic Coach Actions + Workout Rescheduling

New Coach capabilities:
- Move a workout to another day
- Detect schedule conflicts
- Offer a workout-day swap when the target day is occupied
- Swap two workout days directly
- Skip a planned workout
- Restore a skipped workout
- Preserve the existing shorten-workout action
- Show recovery warnings for back-to-back training days
- Persist the weekly schedule separately from generated workout order
- Ground the real LLM in the current weekly schedule

Examples:
- "Move my Thursday workout to Saturday"
- "Swap Tuesday and Friday"
- "Skip my Friday workout"
- "Restore my Saturday workout"
- "I only have 25 minutes today"

The LLM interprets/converses, while Forge validates and executes structured actions only after the user taps Apply Change.
