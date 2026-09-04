# Forge Fitness v6 — UI Repair

This version addresses the 11 UI issues found in the UI-specific audit while preserving the v5 backend fixes.

Run API:
py -m uvicorn fitness_backend_api_v2_connected:app --host 0.0.0.0 --port 8000

Run UI:
py -m http.server 5500 --bind 0.0.0.0

Hard refresh after replacing an older build: Ctrl + Shift + R.
