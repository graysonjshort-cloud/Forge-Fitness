(function () {
  const native = () => !!window.ForgeNative?.isNative;
  const plugins = () => window.Capacitor?.Plugins || {};
  const AUTH_KEY = "forge_auth_token";

  function plugin(...names) {
    const p = plugins();
    for (const name of names) if (p[name]) return p[name];
    return null;
  }

  async function secureGet(key) {
    if (!native()) return localStorage.getItem(key);
    const secure = plugin("SecureStorage", "SecureStoragePlugin");
    if (!secure) return null;
    try {
      if (typeof secure.get === "function") {
        const out = await secure.get({ key });
        return out?.value ?? out ?? null;
      }
      if (typeof secure.getItem === "function") {
        const out = await secure.getItem({ key });
        return out?.value ?? out ?? null;
      }
    } catch (e) {
      console.warn("Forge secure storage read failed", e);
    }
    return null;
  }

  async function secureSet(key, value) {
    if (!native()) {
      localStorage.setItem(key, value);
      return true;
    }
    const secure = plugin("SecureStorage", "SecureStoragePlugin");
    if (!secure) return false;
    try {
      if (typeof secure.set === "function") {
        await secure.set({ key, value });
        return true;
      }
      if (typeof secure.setItem === "function") {
        await secure.setItem({ key, value });
        return true;
      }
    } catch (e) {
      console.warn("Forge secure storage write failed", e);
    }
    return false;
  }

  async function secureRemove(key) {
    if (!native()) {
      localStorage.removeItem(key);
      return true;
    }
    const secure = plugin("SecureStorage", "SecureStoragePlugin");
    if (!secure) return false;
    try {
      if (typeof secure.remove === "function") {
        await secure.remove({ key });
        return true;
      }
      if (typeof secure.removeItem === "function") {
        await secure.removeItem({ key });
        return true;
      }
    } catch (e) {
      console.warn("Forge secure storage remove failed", e);
    }
    return false;
  }

  async function setPreference(key, value) {
    const prefs = plugin("Preferences");
    if (native() && prefs?.set) {
      await prefs.set({ key, value: JSON.stringify(value) });
      return;
    }
    localStorage.setItem(key, JSON.stringify(value));
  }

  async function getPreference(key, fallback = null) {
    const prefs = plugin("Preferences");
    try {
      if (native() && prefs?.get) {
        const out = await prefs.get({ key });
        return out?.value == null ? fallback : JSON.parse(out.value);
      }
      const raw = localStorage.getItem(key);
      return raw == null ? fallback : JSON.parse(raw);
    } catch {
      return fallback;
    }
  }

  async function removePreference(key) {
    const prefs = plugin("Preferences");
    if (native() && prefs?.remove) {
      await prefs.remove({ key });
      return;
    }
    localStorage.removeItem(key);
  }

  async function requestNotificationPermission() {
    if (!native()) return window.ForgeNotifications?.permission?.() || "unsupported";
    const n = plugin("LocalNotifications");
    if (!n) return "unsupported";
    let status = await n.checkPermissions();
    if (status?.display !== "granted") status = await n.requestPermissions();
    return status?.display || "denied";
  }

  async function notify({ id = Date.now() % 2147483647, title, body, route = "notifications" }) {
    if (!native()) {
      return window.ForgeNotifications?.deliver?.([{key:String(id), title, message:body, route}]) ?? false;
    }
    const n = plugin("LocalNotifications");
    if (!n) return false;
    const permission = await requestNotificationPermission();
    if (permission !== "granted") return false;
    await n.schedule({ notifications: [{
      id: Number(id) || 1,
      title: title || "Forge",
      body: body || "",
      extra: { route },
      schedule: { at: new Date(Date.now() + 250) }
    }]});
    return true;
  }

  async function haptic(style = "MEDIUM") {
    if (!native()) return false;
    try {
      const h = plugin("Haptics");
      if (!h?.impact) return false;
      await h.impact({ style });
      return true;
    } catch {
      return false;
    }
  }

  async function setAuthToken(token) {
    const value = String(token || "");
    if (!native()) {
      if (value) localStorage.setItem(AUTH_KEY, value);
      else localStorage.removeItem(AUTH_KEY);
      return true;
    }
    localStorage.removeItem(AUTH_KEY);
    return value ? secureSet(AUTH_KEY, value) : secureRemove(AUTH_KEY);
  }

  async function getAuthToken() {
    if (!native()) return localStorage.getItem(AUTH_KEY) || "";
    const secure = await secureGet(AUTH_KEY);
    if (secure) return String(secure);
    // One-time migration from PWA/WebView-era localStorage.
    const legacy = localStorage.getItem(AUTH_KEY);
    if (legacy) {
      const migrated = await secureSet(AUTH_KEY, legacy);
      if (migrated) localStorage.removeItem(AUTH_KEY);
      return legacy;
    }
    return "";
  }

  async function clearAuthToken() {
    localStorage.removeItem(AUTH_KEY);
    return secureRemove(AUTH_KEY);
  }

  function onAppStateChange(handler) {
    if (!native()) {
      const fn = () => handler({ isActive: document.visibilityState === "visible" });
      document.addEventListener("visibilitychange", fn);
      return () => document.removeEventListener("visibilitychange", fn);
    }
    const app = plugin("App");
    if (!app?.addListener) return () => {};
    let handle = null;
    Promise.resolve(app.addListener("appStateChange", handler)).then(h => { handle = h; });
    return () => handle?.remove?.();
  }

  function onBackButton(handler) {
    if (!native()) return () => {};
    const app = plugin("App");
    if (!app?.addListener) return () => {};
    let handle = null;
    Promise.resolve(app.addListener("backButton", handler)).then(h => { handle = h; });
    return () => handle?.remove?.();
  }

  async function exitApp() {
    const app = plugin("App");
    if (native() && app?.exitApp) await app.exitApp();
  }

  async function bootstrap() {
    const token = await getAuthToken();
    window.__FORGE_BOOT_AUTH_TOKEN = token || "";
    window.__FORGE_NATIVE_READY = true;
    document.documentElement.dataset.nativeServices = native() ? "ready" : "web";
    return { native: native(), tokenPresent: !!token };
  }

  window.ForgeDeviceServices = {
    bootstrap,
    secureGet,
    secureSet,
    secureRemove,
    setPreference,
    getPreference,
    removePreference,
    setAuthToken,
    getAuthToken,
    clearAuthToken,
    requestNotificationPermission,
    notify,
    haptic,
    onAppStateChange,
    onBackButton,
    exitApp
  };
})();