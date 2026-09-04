# Forge Fitness v17.2.0 — Local-First Workout Runtime

This release makes active workout execution device-first.

## Local runtime
`forge_local_workout.js` introduces a versioned IndexedDB store (`forge_local_workout`, schema v1) with a localStorage fallback.

It persists:
- cached account/profile/current plan for offline launch
- active workout session state
- session mapping between provisional local IDs and server IDs
- ordered workout mutation journal

## Local-first mutations
The following are written to the device before network synchronization:
- workout start
- set/performance logging
- workout position
- rest start/clear
- active workout exercise swap once a replacement option is already available in the session UI
- workout completion
- workout abandonment

Each performance set retains its original request ID. Ordered replay starts a server session first, maps the provisional local session ID to the returned server session ID, then rewrites dependent queued payloads before sending them.

## Offline launch
If the API cannot be reached but a valid native auth token and cached Forge plan exist, the installed app can open from its device cache instead of clearing authentication.

## Recovery
Active session position/rest context is stored both in the v17.2 local runtime and the small crash-recovery workout snapshot. Server reconciliation is skipped while a session exists only locally. On reconnect, the local journal is synchronized before normal server reconciliation.

## Scope
This is the local-first workout runtime, not a claim that every Forge screen is offline. AI Coach, nutrition provider searches, calendar sync, fresh plan generation, and other cloud intelligence still require the backend.

The local database is currently IndexedDB in the Capacitor WebView. This keeps the migration dependency-light and durable across app restarts. A future native-SQLite adapter can be added behind the same runtime interface without changing workout UI code.

### Offline substitution note
The swap mutation itself is local-first. Discovering brand-new substitution candidates still needs cached candidates or a backend connection; expanding the full substitution catalog for offline discovery is a later native-data-cache enhancement.
