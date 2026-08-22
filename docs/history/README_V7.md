# Forge Fitness v7 — Original UI Restoration

v7 restores the original 11-screen product direction while keeping the connected FastAPI + SQLite backend.

Implemented screens:
1. Welcome
2. Goal Selection
3. Experience Level
4. Schedule
5. Equipment
6. Preferences
7. Generating Plan
8. Your Plan
9. Home
10. Workout Complete
11. AI Coach

Also retained connected workout detail, exercise logging, and rest timer screens.

Run API:
py -m uvicorn fitness_backend_api_v2_connected:app --host 0.0.0.0 --port 8000

Run UI:
py -m http.server 5500 --bind 0.0.0.0

Notes:
- Onboarding, profile creation, plan generation, workout logging, rest timing, and workout completion use the real backend.
- AI Coach is currently UI-only; the existing backend does not yet expose a coach/chat endpoint.
