import fs from "node:fs";
import path from "node:path";

const raw = process.argv[2] || "";
const base = raw.replace(/\/+$/,"");
if (!/^https:\/\/[A-Za-z0-9.-]+(?::\d+)?(?:\/.*)?$/.test(base)) {
  console.error("Forge native API URL must be an HTTPS URL.");
  process.exit(2);
}
if (/onrender\.com/i.test(base)) {
  console.error("v17.3 refuses Render API origins. Deploy the replacement backend first.");
  process.exit(3);
}
const target=path.join(process.cwd(),"frontend","js","forge_api_config.js");
fs.writeFileSync(target,`window.FORGE_API_BASE=${JSON.stringify(base)};\n`);
console.log(`Forge native API base set to ${base}`);
