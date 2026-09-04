# Forge Fitness v9.1 — Smart Training Experience

Adds:
- previous set recall/prefill
- next-target suggestion before each exercise
- real PR detection from logged sets
- PR toast notifications
- real PR cards on Workout Complete
- estimated 1RM trend chart in Exercise History

Run:
1. `py -m uvicorn fitness_backend_api_v2_connected:app --host 0.0.0.0 --port 8000`
2. `py -m http.server 5500 --bind 0.0.0.0`
