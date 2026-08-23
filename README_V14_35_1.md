# Forge Fitness v14.35.1

Exercise tracking-mode upgrade.

- Isometric exercises such as Plank, Side Plank, Hollow Body Hold, and named hold/wall-sit movements use a set timer instead of weight/reps.
- Timed sets store actual duration in seconds and can create Duration PRs.
- Bodyweight exercises default the Load field to `Bodyweight`.
- Users can switch a bodyweight movement to `Added Weight` when appropriate, which reveals the weight entry field.
- Bodyweight-only sets do not create artificial 0 lb weight/e1RM/volume PRs.
- Existing weighted exercises continue using weight + reps.
- Exercise directory intelligence now reports `tracking_mode` and `bodyweight_default`.
- v14.35.1 uses a fresh service-worker cache so installed phone PWAs receive the frontend update.
