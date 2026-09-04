(async function () {
  try {
    if (window.ForgeDeviceServices?.bootstrap) {
      await window.ForgeDeviceServices.bootstrap();
    }
  } catch (e) {
    console.warn("Forge native bootstrap degraded gracefully", e);
    window.__FORGE_BOOT_AUTH_TOKEN = "";
  }

  const script = document.createElement("script");
  script.src = "/app.js?v=17.3.0";
  script.async = false;
  script.onerror = () => {
    const view = document.querySelector("#view");
    if (view) view.innerHTML = '<div class="card"><h2>Forge could not start</h2><p>Please restart the app.</p></div>';
  };
  document.body.appendChild(script);
})();