# Forge Fitness v5 — Full Repair Build

This build was repaired after a full integration test instead of one-off patches.

Run API:
py -m uvicorn fitness_backend_api_v2_connected:app --host 0.0.0.0 --port 8000

Run UI:
py -m http.server 5500 --bind 0.0.0.0

Then hard-refresh the browser (Ctrl+Shift+R).

See FULL_TEST_REPORT.json for the automated test summary.
