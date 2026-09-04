// Forge Fitness v14.38.4 — Workout feature module
// Owns routing for this feature while legacy view bodies are migrated behind a stable bridge.
ForgeFeatures.register("workout", {
  views: {
    "workout": () => window.ForgeLegacyViews["workout"](),
    "exercise": () => window.ForgeLegacyViews["exercise"](),
    "timer": () => window.ForgeLegacyViews["timer"](),
    "complete": () => window.ForgeLegacyViews["complete"](),
    "swapexercise": () => window.ForgeLegacyViews["swapexercise"](),
    "cardioswap": () => window.ForgeLegacyViews["cardioswap"](),
    "modulemove": () => window.ForgeLegacyViews["modulemove"](),
    "coretracker": () => window.ForgeLegacyViews["coretracker"](),
    "cardiotracker": () => window.ForgeLegacyViews["cardiotracker"]()
  }
});
