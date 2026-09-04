import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const source = path.join(root, "frontend");
const dist = path.join(root, "dist");

fs.rmSync(dist, { recursive: true, force: true });
fs.cpSync(source, dist, { recursive: true });

for (const file of ["sw.js", "service-worker.js", "manifest.webmanifest", "manifest.json"]) {
  const p = path.join(dist, file);
  if (fs.existsSync(p)) fs.rmSync(p);
}

const indexPath = path.join(dist, "index.html");
let html = fs.readFileSync(indexPath, "utf8");
html = html
  .replace(/<link rel="manifest"[^>]*>\s*/g, "")
  .replace(/<link rel="apple-touch-icon"[^>]*>\s*/g, "")
  .replace(/<meta name="apple-mobile-web-app-[^"]+"[^>]*>\s*/g, "");
fs.writeFileSync(indexPath, html);

console.log("Forge native bundle prepared: PWA runtime removed, native services retained.");
