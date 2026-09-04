(function () {
  const isNative = !!(window.Capacitor && typeof window.Capacitor.isNativePlatform === "function" && window.Capacitor.isNativePlatform());
  const platform = isNative && typeof window.Capacitor.getPlatform === "function"
    ? window.Capacitor.getPlatform()
    : "web";

  const Native = {
    isNative,
    platform,
    isAndroid: platform === "android",
    isIOS: platform === "ios",
    apiBase() {
      const packaged = String(window.FORGE_API_BASE || "").replace(/\/+$/, "");
      if (isNative && packaged) {
        try {
          const stale = localStorage.getItem("forge_api_base") || "";
          if (/onrender\.com/i.test(stale)) localStorage.removeItem("forge_api_base");
        } catch (_) {}
        return packaged;
      }
      const stored = localStorage.getItem("forge_api_base");
      if (stored) return stored.replace(/\/+$/, "");
      return packaged;
    },
    shouldRegisterServiceWorker() {
      return !isNative;
    },
    markDocument() {
      document.documentElement.dataset.forgeRuntime = isNative ? "native" : "web";
      document.documentElement.dataset.forgePlatform = platform;
    }
  };

  Native.markDocument();
  window.ForgeNative = Native;
})();