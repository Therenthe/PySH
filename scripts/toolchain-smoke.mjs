import { mkdir, mkdtemp, readFile, rm, stat, writeFile } from "node:fs/promises";
import { createServer } from "node:http";
import { fileURLToPath } from "node:url";
import { dirname, extname, isAbsolute, join, relative, resolve, sep } from "node:path";
import react from "@vitejs/plugin-react";
import { chromium } from "@playwright/test";
import { build } from "vite";

const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const runtimeRoot = resolve(projectRoot, ".runtime");
const manifest = JSON.parse(await readFile(resolve(projectRoot, "package.json"), "utf8"));
const nodeMajor = Number(process.versions.node.split(".")[0]);
const args = new Set(process.argv.slice(2));
const validArgs = new Set(["--serve", "--build-only"]);

for (const arg of args) {
  if (!validArgs.has(arg)) throw new Error(`Unknown option: ${arg}`);
}
if (args.has("--serve") && args.has("--build-only")) throw new Error("Use either --serve or --build-only, not both.");

function assertFixtureIsWithinRuntime(candidate) {
  const runtime = resolve(runtimeRoot);
  const fixture = resolve(candidate);
  const relativeFixture = relative(runtime, fixture);
  if (!relativeFixture || relativeFixture === "." || isAbsolute(relativeFixture) || relativeFixture === ".." || relativeFixture.startsWith(`..${sep}`)) {
    throw new Error(`Refusing to operate outside the temporary fixture directory under .runtime: ${fixture}`);
  }
  return fixture;
}

if (nodeMajor < 22) throw new Error(`Node ${process.versions.node} is below the configured Node 22 minimum.`);
if (manifest.packageManager !== "pnpm@11.19.0") throw new Error("The pnpm version pin is missing or changed.");

const fixtureRoot = assertFixtureIsWithinRuntime(await mkdtemp(join(runtimeRoot, "frontend-toolchain-smoke-")));
let httpServer;

try {
  const sourceRoot = join(fixtureRoot, "src");
  await mkdir(sourceRoot, { recursive: true });
  await writeFile(join(fixtureRoot, "index.html"), `<!doctype html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Toolchain fixture</title></head>
<body><div id="root"></div><script type="module" src="/src/main.tsx"></script></body></html>
`);
  await writeFile(join(sourceRoot, "main.tsx"), `import React, { useState } from "react";
import { createRoot } from "react-dom/client";

function ToolchainFixture() {
  const [count, setCount] = useState(0);
  return <main><h1>Touch smoke fixture</h1><button type="button" onClick={() => setCount((value) => value + 1)}>Increase count</button><output aria-label="count">Count: {count}</output></main>;
}

createRoot(document.getElementById("root")!).render(<ToolchainFixture />);
`);
  console.log("Temporary React/TypeScript fixture created; Vite will compile its TSX entry point.");

  await build({
    configFile: false,
    root: fixtureRoot,
    plugins: [react()],
    logLevel: "silent",
    build: { outDir: join(fixtureRoot, "dist"), emptyOutDir: true },
  });
  const distRoot = join(fixtureRoot, "dist");
  const builtHtml = await readFile(join(distRoot, "index.html"), "utf8");
  const assetPaths = [...builtHtml.matchAll(/(?:src|href)="([^"]+\.(?:js|css))"/g)].map((match) => match[1]);
  if (!assetPaths.some((asset) => asset.endsWith(".js"))) throw new Error("Vite output did not reference a compiled JavaScript asset.");
  for (const assetUrl of assetPaths) {
    const assetPath = resolve(distRoot, `.${assetUrl}`);
    const relativePath = relative(distRoot, assetPath);
    if (relativePath.startsWith(`..${sep}`) || relativePath === "..") throw new Error(`Unexpected Vite asset path: ${assetUrl}`);
    const info = await stat(assetPath);
    if (!info.isFile() || info.size === 0) throw new Error(`Vite asset is missing or empty: ${assetUrl}`);
  }
  console.log(`Vite fixture build passed; ${assetPaths.length} compiled asset(s) verified.`);

  if (args.has("--build-only")) {
    console.log("Build-only mode complete; Playwright was not run.");
  } else {

    const mimeTypes = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml" };
    httpServer = createServer(async (request, response) => {
      try {
        const pathname = new URL(request.url ?? "/", "http://127.0.0.1").pathname;
        const requested = pathname === "/" ? "index.html" : decodeURIComponent(pathname.slice(1));
        const filePath = resolve(distRoot, requested);
        const local = relative(distRoot, filePath);
        if (local.startsWith(`..${sep}`) || local === "..") {
          response.writeHead(403).end();
          return;
        }
        const contents = await readFile(filePath);
        response.writeHead(200, { "content-type": mimeTypes[extname(filePath)] ?? "application/octet-stream" }).end(contents);
      } catch {
        response.writeHead(404).end("Not found");
      }
    });
    await new Promise((resolveListen, rejectListen) => {
      httpServer.once("error", rejectListen);
      httpServer.listen(0, "127.0.0.1", resolveListen);
    });
    const address = httpServer.address();
    if (!address || typeof address === "string") throw new Error("Could not determine the local fixture server port.");
    const fixtureUrl = `http://127.0.0.1:${address.port}/`;

    if (args.has("--serve")) {
      console.log(`Fixture is serving at ${fixtureUrl}`);
      console.log("Press Ctrl+C to stop the server and remove its temporary files.");
      await new Promise((resolveStop) => {
        const stop = () => resolveStop();
        process.once("SIGINT", stop);
        process.once("SIGTERM", stop);
      });
    } else {
    const browser = await chromium.launch({ headless: true });
    try {
      for (const locale of ["en-GB", "ro-RO"]) {
        const context = await browser.newContext({
          locale,
          viewport: { width: 800, height: 480 },
          deviceScaleFactor: 1,
          isMobile: false,
          hasTouch: true,
        });
        const page = await context.newPage();
        await page.goto(fixtureUrl);
        if (await page.evaluate(() => navigator.language) !== locale) throw new Error(`Browser locale was not applied: ${locale}`);
        await page.getByRole("button", { name: "Increase count" }).tap();
        await page.getByRole("button", { name: "Increase count" }).tap();
        const count = await page.getByLabel("count").textContent();
        if (count?.trim() !== "Count: 2") throw new Error(`Touch operation failed for ${locale}: ${count}`);
        await context.close();
        console.log(`Headless Playwright touch smoke passed at 800×480 (${locale}).`);
      }
    } finally {
      await browser.close();
    }
    }
  }
} finally {
  if (httpServer?.listening) await new Promise((resolveClose) => httpServer.close(resolveClose));
  await rm(assertFixtureIsWithinRuntime(fixtureRoot), { recursive: true, force: true });
}
