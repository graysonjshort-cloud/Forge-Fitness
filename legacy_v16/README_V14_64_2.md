# Forge Fitness v14.64.2 — Sparse Rebuild Target Fix

Fixes Adjust Plan rebuild failures when only some workouts override the global exercise target. JavaScript sparse array slots serialize as `null`; v14.64.2 normalizes every workout target before preview/apply and also accepts/normalizes null targets server-side.

Also improves API validation error formatting so FastAPI validation details are readable instead of `[object Object]`.
