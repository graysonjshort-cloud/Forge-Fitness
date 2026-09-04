// Forge Fitness v14.38.3 — Nutrition feature module
// Owns routing for this feature while legacy view bodies are migrated behind a stable bridge.
ForgeFeatures.register("nutrition", {
  views: {
    "nutrition": () => window.ForgeLegacyViews["nutrition"](),
    "nutritionadd": () => window.ForgeLegacyViews["nutritionadd"]()
  }
});
