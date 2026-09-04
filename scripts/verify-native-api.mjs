import fs from "node:fs";
const text=fs.readFileSync("frontend/js/forge_api_config.js","utf8");
const match=text.match(/window\.FORGE_API_BASE=(?:"([^"]*)"|'([^']*)')/);
const base=(match?.[1]??match?.[2]??"").trim();
if(!base){
  console.error("Forge API is not configured. Run: node scripts/set-api-base.mjs https://YOUR-API");
  process.exit(2);
}
if(!base.startsWith("https://")){
  console.error("Forge native production API must use HTTPS.");
  process.exit(3);
}
if(/onrender\.com/i.test(base)){
  console.error("Render dependency detected. v17.3 native release must use the replacement API.");
  process.exit(4);
}
console.log(`Forge native API verified: ${base}`);
