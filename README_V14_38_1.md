# Forge Fitness v14.38.1 — Browser Release Gate

This release adds the browser-level reliability layer planned after v14.38.0.

## Added
- `tests/run_browser_smoke.py`
  - Executes the real Forge frontend in headless Chromium at a 390×844 mobile viewport.
  - Uses a real FastAPI test server and a freshly registered/generated-plan test user.
  - Covers authenticated startup, Home, Plan, Workout, Progress, Nutrition, Coach, and the More/account sheet.
  - Fails on uncaught page errors, console errors, or failed requests.
  - Explicitly re-tests the Nutrition provider-status and online-event regressions fixed in v14.38.0.
- `tests/run_frontend_contract_validation.py`
  - Extracts frontend `api()` calls from `app.js` and FastAPI route declarations from the backend.
  - Verifies frontend method/path contracts have matching backend routes.
  - Detects raw `fetch()` calls that bypass Forge's shared authenticated `api()` helper.
- `V14_38_1_BROWSER_SMOKE_REPORT.json`
- `V14_38_1_FRONTEND_CONTRACT_REPORT.json`

## PWA/browser reliability fixes
- Updated visible app version to v14.38.1.
- Updated frontend asset query versions to v14.38.1.
- Rotated the service-worker application-shell cache so installed PWAs receive this release instead of remaining on an older cached shell.
- Updated service-worker shell asset URLs to v14.38.1.
- Excluded `/nutrition/`, `/persistence/`, and legacy `/users/` API routes from service-worker caching. The Nutrition provider-status endpoint therefore cannot be accidentally served as stale cached API data.

## Validation
- Static validation: PASS
- API end-to-end flow: PASS
- Frontend/API contract validation: PASS — 102 frontend API calls checked against 103 backend routes
- Headless Chromium mobile smoke test: PASS — all six primary tabs plus account sheet
- `node --check app.js`: PASS
- `node --check sw.js`: PASS
- Python compilation of backend/database/new tests: PASS

The 3D form-demo assets and pipeline are unchanged.
