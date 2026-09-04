import fs from "node:fs";
const required = [
  "package.json","capacitor.config.json","frontend/index.html",
  "frontend/js/forge_native.js","frontend/js/forge_device_services.js",
  "frontend/js/forge_native_bridge.js","frontend/js/forge_native_bootstrap.js",
  "frontend/js/forge_api_config.js","scripts/sync-web.mjs"
];
for (const f of required) if (!fs.existsSync(f)) throw new Error(`Missing ${f}`);
const pkg=JSON.parse(fs.readFileSync("package.json","utf8"));
if(!/^17\.[123]\./.test(pkg.version)) throw new Error("Unexpected Android-foundation version");
if(!pkg.dependencies["@aparajita/capacitor-secure-storage"]) throw new Error("Secure storage missing");
const cfg=JSON.parse(fs.readFileSync("capacitor.config.json","utf8"));
if(cfg.appId!=="com.forgefitness.app") throw new Error("Unexpected Android app ID");
const html=fs.readFileSync("frontend/index.html","utf8");
const order=["forge_api_config.js","forge_native.js","forge_device_services.js","forge_native_bridge.js","forge_native_bootstrap.js"];
let last=-1;
for(const s of order){const i=html.indexOf(s);if(i<0)throw new Error(`index missing ${s}`);if(i<=last)throw new Error(`wrong startup order at ${s}`);last=i}
if(/<script src="\/app\.js/.test(html)) throw new Error("app.js must load through native bootstrap");
const app=fs.readFileSync("frontend/app.js","utf8");
if(!app.includes("__FORGE_BOOT_AUTH_TOKEN")) throw new Error("app does not consume boot token");
if(!app.includes("ForgeDeviceServices.onAppStateChange")) throw new Error("native lifecycle missing");
console.log(`Forge ${pkg.version} Android foundation/device-services validation passed.`);
