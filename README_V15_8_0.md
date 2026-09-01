# Forge Fitness v15.8.0 — Performance & Modularization

This release keeps the existing app.js size guard and moves Health Check/system-diagnostics rendering plus notification-center rendering into dedicated frontend modules. Home no longer fetches Training Dashboard data it does not render. Notification data is reused during a foreground visit unless explicitly refreshed, and Home aggregation receives a short cache with mutation-driven invalidation. This reduces startup/tab churn without weakening workout/session authority.
