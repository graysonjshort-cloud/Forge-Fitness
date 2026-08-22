# Forge Fitness — Repaired Connected Build

Repairs:
- Weight now persists with set performance.
- Logged exercise data is converted into exercise-specific adaptation history.
- Next-week generation consumes actual exercise performance history.
- Progress completion-rate field mismatch fixed.
- Rest timer counts down using each exercise's programmed rest duration.
- Active workout session restores after browser refresh.
- Saved profile values hydrate the preferences form.
- Added active-session and session-exercise aggregation API endpoints.

Run API:
py -m uvicorn fitness_backend_api_v2_connected:app --host 0.0.0.0 --port 8000

Run UI:
py -m http.server 5500 --bind 0.0.0.0
