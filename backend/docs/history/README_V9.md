# Forge Fitness v9 — Workout History + PRs

Adds real history and progression data on top of the v8 account system.

New:
- GET /me/history
- GET /me/prs
- GET /me/exercises/{exercise_id}/history
- Workout History UI
- Personal Records UI
- Exercise History UI
- max weight, best reps, best set volume, and estimated 1RM
- basic next-target suggestion from recent reps/RPE

Run API:
py -m uvicorn fitness_backend_api_v2_connected:app --host 0.0.0.0 --port 8000

Run UI:
py -m http.server 5500 --bind 0.0.0.0
