(function () {
  window.ForgeNativeBridge = {
    notify(title, body, id = 1) {
      return window.ForgeDeviceServices?.notify?.({ id, title, body }) ?? Promise.resolve(false);
    },
    haptic(style = "MEDIUM") {
      return window.ForgeDeviceServices?.haptic?.(style) ?? Promise.resolve(false);
    },
    setPreference(key, value) {
      return window.ForgeDeviceServices?.setPreference?.(key, value);
    },
    getPreference(key, fallback = null) {
      return window.ForgeDeviceServices?.getPreference?.(key, fallback) ?? Promise.resolve(fallback);
    }
  };
})();