// Forge Fitness v14.38.7 — Coach feature module
// Owns Coach and proactive-notification routing behind the stable feature registry.
ForgeFeatures.register("coach", {
  views: {
    "coach": () => window.ForgeLegacyViews["coach"](),
    "notifications": () => window.ForgeLegacyViews["notifications"]()
  }
});
