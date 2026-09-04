# Forge Fitness v17.1.0 — Native Device Services

v17.1 moves Android-specific behavior behind a dedicated native service boundary.

## Added
- Native startup bootstrap before `app.js`.
- Secure authentication-token abstraction.
- Capacitor 7-compatible secure-storage dependency (`@aparajita/capacitor-secure-storage` 7.1.x).
- Native Preferences adapter.
- Native Local Notifications adapter and permission flow.
- Native haptics adapter.
- Android app lifecycle handling.
- Android hardware-back handling.
- Background workout snapshot persistence.
- Resume-time session reconciliation/offline replay.

## Security
On native Android, Forge no longer intentionally stores newly issued auth tokens in browser localStorage. The native service layer uses secure storage when the installed secure-storage plugin is available. A legacy localStorage token is migrated once and removed after successful secure persistence.

## Startup fix
v17.0's native scripts were appended after `app.js`; therefore the old app could initialize before native detection. v17.1 loads:
1. API config
2. native runtime detector
3. native device services
4. native compatibility bridge
5. bootstrap
6. `app.js` dynamically only after secure-token hydration

## Current boundary
This release creates the native device-service architecture. Workout data itself is still using the existing web/localStorage/offline queue model. A versioned native local database is the next migration step in v17.2.

## Build
After installing Node, Android Studio and a supported JDK:
- `npm install`
- `npm run sync:web`
- `npx cap add android` (first setup only)
- `npm run cap:sync`
- `npx cap open android`

No signed APK is included because signing keys and an Android SDK/build environment are device/developer specific.
