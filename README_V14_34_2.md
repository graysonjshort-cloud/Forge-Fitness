# Forge Fitness v14.34.2

## Plan rebuild fix
v14.34 attempted to insert a second `week 1` into the same active program, causing:
`ValueError: Program week 1 already exists`.

v14.34.2 rebuilds safely by:
- marking the previous active program as `replaced`;
- creating a fresh active program for the rebuilt plan;
- preserving the old program, workout sessions, performance history and PR data;
- validating preferred days before rebuilding;
- restoring the old profile if generation fails;
- applying the requested training days to the newly generated schedule.

## Phone update delivery
- New service-worker cache: `forge-v14-34-2-final-v1`
- `app.js?v=14.34.2`
- `styles.css?v=14.34.2`
- Visible app version updated to v14.34.2
- Existing service-worker activation deletes older Forge caches.

After Render deploys, open Forge while online. The service worker will fetch the new build.
If the installed app is already open, close/reopen it after the update-ready prompt or press Reload.
