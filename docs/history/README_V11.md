# Forge Fitness v11 — Session Reliability + MVP Stabilization

Added exact workout resume, duplicate-set protection, persistent rest timers,
persisted workout feedback, fatigue integration, abandon/restart, and recovery
after logout/login.

Run:
1. py -m uvicorn fitness_backend_api_v2_connected:app --host 0.0.0.0 --port 8000
2. py -m http.server 5500 --bind 0.0.0.0

See V11_MVP_STABILIZATION_REPORT.json for automated test coverage.
