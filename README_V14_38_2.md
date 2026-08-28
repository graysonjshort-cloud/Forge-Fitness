# Forge Fitness v14.38.2 — Frontend Modularization Foundation

This release starts the frontend refactor behind the v14.38.1 browser release gate without changing the app's user-facing workflows.

## What changed

- Split reusable frontend infrastructure out of the monolithic `app.js` into four load-before-app modules:
  - `js/forge_core.js` — HTML escaping and request IDs.
  - `js/forge_api.js` — authenticated API transport, offline/server errors, and response handling.
  - `js/forge_equipment.js` — equipment SVG asset resolution and fallback behavior.
  - `js/forge_pwa.js` — install-state detection, install UI, service-worker update handling, and online/offline listeners.
- Reduced `app.js` from about 187.5 KB to about 181.1 KB in the first extraction pass.
- Kept the existing global app/controller structure intact to minimize regression risk while creating clean seams for future feature modules.
- Updated the browser smoke runner so the exact module dependency order is exercised before `app.js`.
- Updated static validation to syntax-check all frontend modules, verify module script tags, and enforce a size guard on `app.js`.
- Rotated PWA shell/cache identifiers to v14.38.2 and added the new module files to the offline app shell.

## Release-gate coverage

- Static validation: routes, critical UI hooks, equipment coverage, responsive rules, browser regressions, module presence, Node syntax.
- Full FastAPI E2E flow.
- Frontend/FastAPI contract validation.
- Headless Chromium 390x844 smoke test across primary routes plus module namespace verification.
- Python compilation for backend/test code.

## Next modularization targets

The next safe extractions are the Nutrition view/controller, Progress view/controller, and Exercise Directory/Form Demo code. Those are feature-oriented chunks and can now be moved one at a time behind the browser gate instead of performing a risky whole-app rewrite.
