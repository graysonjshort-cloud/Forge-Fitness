// Forge Fitness v14.38.6 — Progress feature module
// Owns routing for this feature while legacy view bodies are migrated behind a stable bridge.
ForgeFeatures.register("progress", {
  views: {
    "progress": () => window.ForgeLegacyViews["progress"](),
    "history": () => window.ForgeLegacyViews["history"](),
    "prs": () => window.ForgeLegacyViews["prs"](),
    "exercisehistory": () => window.ForgeLegacyViews["exercisehistory"]()
  }
});
