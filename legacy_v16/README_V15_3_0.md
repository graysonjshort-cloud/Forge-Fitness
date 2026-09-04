# Forge Fitness v15.3.0 — Offline Workout Reliability

Workout mutations can be queued locally while offline. Performance writes retain their request_id for idempotent replay. Position, rest, and completion writes preserve order. Reconnect replay validates the active immutable session/workout before sending queued writes; unsafe replay stops instead of writing into a replaced workout.
