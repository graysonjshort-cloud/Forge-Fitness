# Forge Fitness v14.36.3 — Offline Demo Delivery

- Added a current-plan demo asset endpoint.
- Added a dedicated `forge-exercise-demos-v1` Cache API store.
- Current week's real demo assets can be cached on demand from the Form Guide.
- Demo media uses cache-first playback with network fill.
- Demo cache is bounded to 40 assets and kept separate from the application-shell cache.
- Reconnecting to the network opportunistically warms current-plan demos without blocking the workout UI.
- Missing animations still fall back to the v14.36.2 written Form Guide.
- Added a 20-exercise starter-pack manifest for the first original/licensed, biomechanically reviewed assets.

No fake exercise animations are marked as complete in this release.
