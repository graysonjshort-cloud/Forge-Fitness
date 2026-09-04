# Forge Fitness v14.38.0 — General App Stability Pass

This release resumes general Forge Fitness development after the 3D exercise-demo branch.

## Fixed
- Nutrition provider-status diagnostics no longer reference the undefined `API_BASE` browser variable. The screen now uses Forge's shared `api()` helper, so base URL selection, authentication, JSON parsing, offline handling, and HTTP errors follow the same path as the rest of the app.
- The browser `online` event no longer references the undefined `token` variable. It now correctly checks `authToken` before warming current-plan exercise-demo media.

## Regression coverage
`tests/run_static_validation.py` now explicitly fails if either undefined browser reference returns and verifies both corrected code paths.

## Review findings / next development priorities
1. Split the frontend monolith (`app.js`) into feature modules without changing behavior.
2. Split the backend route monolith into FastAPI routers/services and keep database access out of route handlers.
3. Expand browser-level tests. Current static/E2E scripts cover key API workflows, but browser-only runtime bugs escaped them.
4. Add a real migration/versioning layer for SQLite/Supabase schema changes instead of relying only on startup schema reconciliation.
5. Harden session storage/auth behavior for a public production deployment and audit HTML rendering paths for injection safety.
6. Add structured logging and error telemetry so production failures are diagnosable without user screenshots.
7. Add contract tests for all major frontend API calls and run them automatically before release packaging.

The 3D form-demo work is intentionally unchanged in this release.
