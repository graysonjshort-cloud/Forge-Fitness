# Forge Fitness v14.34.3

Android launcher-icon patch.

- Uses the approved red Forge icon with the white F interior and silver border/anvil.
- Adds new uniquely named 192px and 512px Android/PWA icons.
- Adds Android maskable icon versions with safe padding.
- Updates the web manifest and shortcut icons.
- Bumps the manifest URL and service-worker cache so installed Android devices can receive the new icon.
- Apple touch icon is intentionally unchanged.

After deploying to Render, open Forge in Chrome once while online. Android caches launcher icons
aggressively; if the existing installed icon does not change after Chrome sees the new manifest,
remove the old Forge Home Screen/PWA icon and install Forge again. Your server-side Forge account
data is unaffected by reinstalling the PWA.
