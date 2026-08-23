# Forge Fitness v14.34.1

PWA cache refresh patch for v14.34.

Fixes:
- Service worker cache renamed from the v14.33 cache to `forge-v14-34-final-v1`.
- Cached `app.js` and `styles.css` URLs now use `?v=14.34`.
- `index.html` now requests the v14.34 frontend assets.
- Existing v14.34 workout customization and AI Coach improvements are unchanged.

After deploying:
1. Wait for Render to report the service as Live.
2. Open Forge on the phone and refresh it once.
3. If the installed PWA still shows v14.33, fully close and reopen it.
4. If necessary, uninstall the old Forge PWA once and reinstall from Chrome.
