import fs from "node:fs";
const required=[
 "backend/Dockerfile","backend/env.example","cloud/cloudrun.service.yaml",
 "frontend/js/forge_api_config.js","scripts/set-api-base.mjs","scripts/verify-native-api.mjs"
];
for(const f of required)if(!fs.existsSync(f))throw new Error(`Missing ${f}`);
const backend=fs.readFileSync("backend/fitness_backend_api_v2_connected.py","utf8");
for(const t of ['"version":"17.3.0"',"FORGE_SERVE_FRONTEND","/healthz","/readyz",'if FORGE_SERVE_FRONTEND:'])
 if(!backend.includes(t))throw new Error(`Backend migration missing ${t}`);
const docker=fs.readFileSync("backend/Dockerfile","utf8");
if(!docker.includes("${PORT:-8080}")||!docker.includes("--workers 1"))throw new Error("Container contract invalid");
const native=fs.readFileSync("frontend/js/forge_native.js","utf8");
if(!native.includes("packaged")||!native.includes("onrender"))throw new Error("Native API precedence guard missing");
const pkg=JSON.parse(fs.readFileSync("package.json","utf8"));
if(pkg.version!=="17.3.0")throw new Error("Wrong version");
console.log("Forge v17.3 Cloud Backend Migration validation passed.");
