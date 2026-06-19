// Bundles the extension entry points and copies static assets into dist/.
import { cp } from "node:fs/promises";
import * as esbuild from "esbuild";

await esbuild.build({
  entryPoints: ["src/background.ts", "src/content.ts", "src/popup.ts", "src/consent.ts"],
  bundle: true,
  format: "esm",
  target: "chrome110",
  outdir: "dist",
  logLevel: "info",
});

await Promise.all([
  cp("manifest.json", "dist/manifest.json"),
  cp("src/popup.html", "dist/popup.html"),
  cp("src/consent.html", "dist/consent.html"),
]);

console.log("Extension built to dist/. Load it via chrome://extensions (Developer mode → Load unpacked).");
