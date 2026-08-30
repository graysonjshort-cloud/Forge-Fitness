# Forge Fitness v14.74.1 — Exercise History Reload Fix

Fixes the exercise-screen reload/glitch where Previous Performance repeatedly returned to its loading state.

- Previous Performance is cached by exercise ID.
- Duplicate in-flight history requests are blocked.
- Progression strategy is cached by exercise ID.
- Harmless rerenders reuse already-loaded performance instead of refetching it.
- Logging a set intentionally invalidates the current exercise cache once so the newly logged performance can refresh.
- Browser regression verifies history and progression request counts do not increase after an exercise-screen rerender.
