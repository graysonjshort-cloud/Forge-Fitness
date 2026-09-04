# Forge Fitness v14.33 — Final Polish

v14.33 is the current final iteration focused on cohesion, reliability, and day-to-day usability
rather than adding another infrastructure layer.

## Final UX pass
- Reworked the top-right menu into a real account/settings bottom sheet instead of immediately
  asking the user to sign out.
- Fast access to Training Settings, Equipment Log, and Calendar & Time.
- Clear app/account version and connection status.
- Removed the misleading mock Google account sign-in button. Google remains a Calendar connection
  after the user signs into Forge.
- Added subtle screen transitions and consistent card/button/input rounding.
- Added reduced-motion support.

## Reliability states
- Offline banner when the device loses connectivity.
- Cleaner server/network error messages.
- Automatic online-state recovery message.
- PWA update-ready banner with a Reload action.
- v14.33 service-worker cache version and frontend cache busting.

## Workout completion
- Improved completion hierarchy.
- Recovery guidance after finishing.
- Direct actions to Progress or Nutrition after a session.
- Existing PR and effort feedback remain intact.

## Settings
- New Forge App & Account status card showing online/offline, browser/install mode, Calendar state,
  and v14.33.
- Equipment Log launched from settings now returns to settings correctly.

## Persistence optimization
The free Supabase persistence bridge from v14.32 is retained. v14.33 avoids uploading an entire
database snapshot after read-only database transactions; snapshots are written only after SQLite
actually changes. This reduces unnecessary Supabase traffic while preserving restart/redeploy
durability.

## Existing systems retained
- Free Render hosting
- Free Supabase-backed persistence
- Android PWA
- iPhone/iPad Home Screen web app
- Google Calendar OAuth
- AI Coach
- Nutrition lookup/logging
- Adaptive training
- Equipment Log artwork
