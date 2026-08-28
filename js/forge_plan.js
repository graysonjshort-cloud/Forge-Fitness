// Forge Fitness v14.38.5 — Plan feature module
// Owns routing for this feature while legacy view bodies are migrated behind a stable bridge.
ForgeFeatures.register("plan", {
  views: {
    "plan": () => window.ForgeLegacyViews["planScreen"](),
    "adjustplan": () => window.ForgeLegacyViews["adjustplan"](),
    "trainingsettings": () => window.ForgeLegacyViews["trainingsettings"](),
    "calendarsettings": () => window.ForgeLegacyViews["calendarsettings"]()
  }
});
