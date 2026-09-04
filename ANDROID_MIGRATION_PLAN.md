# Forge Android Migration Plan

## Phase 1 — v17.0 Android Foundation ✅
Preserve the current modular frontend, add Capacitor, remove PWA-only runtime behavior from native builds, isolate API host configuration, and establish native bridges.

## Phase 2 — v17.1 Native Device Services ✅
Move notifications, app lifecycle handling, haptics, secure credentials, and device preferences behind native adapters.

## Phase 3 — v17.2 Local-First Workout Runtime ✅
Add a versioned local database. Workout start, set logging, timers, swaps, position recovery, and completion work without a network connection. Ordered synchronization reconciles with the cloud API.

## Phase 4 — v17.3 Cloud Backend Migration ✅
Move Forge API hosting away from Render. Supabase/Postgres remains authoritative cloud persistence. The APK points at the new API origin.

## Phase 5 — v17.4 Release Pipeline
Android signing, AAB/APK builds, migration tests, upgrade tests, crash recovery, Play-compatible release artifacts, and rollback documentation.

## Completion criterion
Render can be deleted and an already-installed Forge Android app continues to launch, perform local workouts, and synchronize when the replacement API is available.
