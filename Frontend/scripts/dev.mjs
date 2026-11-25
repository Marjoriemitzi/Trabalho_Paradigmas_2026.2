import http from "node:http";
import https from "node:https";
import { readFile } from "node:fs/promises";
import { watch } from "node:fs";
import { resolve, extname, dirname, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { spawn } from "node:child_process";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const publicDir = resolve(root, "public");
const backend = new URL(process.env.BACKEND_URL || "http://127.0.0.1:8000");
const port = Number(process.env.PORT || 5173);
const host = process.env.HOST || "127.0.0.1";
const headers = {
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "same-origin",
  "Content-Security-Policy":
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
  "Cache-Control": "no-store",
};
let compiling = false;
let again = false;
async function compile() {
  if (compiling) {
    again = true;
    return;
  }
  compiling = true;
  const command = process.platform === "win32" ? "elm.cmd" : "elm";
  const child = spawn(
    command,
    ["make", "src/Main.elm", "--output=public/elm.js"],
    { cwd: root, stdio: "inherit", shell: process.platform === "win32" },
  );
  const code = await new Promise((resolveCode, reject) => {
    child.on("exit", resolveCode);
    child.on("error", reject);
  });
  compiling = false;
  if (again) {
    again = false;
    await compile();
  }
  return code;
}
if (!process.argv.includes("--skip-build") && (await compile()) !== 0)
  process.exit(1);
const server = http.createServer(async (req, res) => {
  if (req.url?.startsWith("/api/")) {
    const target = new URL(req.url, backend);
    const transport = target.protocol === "https:" ? https : http;
    const upstream = transport.request(
      target,
      {
        method: req.method,
        headers: { ...req.headers, host: target.host },
        timeout: 20000,
      },
      (response) => {
        res.writeHead(response.statusCode || 502, {
          ...response.headers,
          ...headers,
        });
        response.pipe(res);
      },
    );
    upstream.on("timeout", () => upstream.destroy(new Error("timeout")));
    upstream.on("error", () => {
      if (!res.headersSent)
        res.writeHead(502, { ...headers, "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: "backend_unavailable" }));
    });
    req.on("aborted", () => upstream.destroy());
    req.pipe(upstream);
    return;
  }
  try {
    const url = new URL(req.url || "/", "http://localhost");
    const path = resolve(
      publicDir,
      "." +
        decodeURIComponent(url.pathname === "/" ? "/index.html" : url.pathname),
    );
    if (!path.startsWith(publicDir + sep)) {
      res.writeHead(403, headers);
      res.end();
      return;
    }
    const bytes = await readFile(path);
    const types = {
      ".html": "text/html; charset=utf-8",
      ".js": "text/javascript; charset=utf-8",
      ".css": "text/css; charset=utf-8",
      ".svg": "image/svg+xml",
    };
    res.writeHead(200, {
      ...headers,
      "Content-Type": types[extname(path)] || "application/octet-stream",
    });
    res.end(bytes);
  } catch {
    res.writeHead(404, headers);
    res.end("Não encontrado");
  }
});
server.listen(port, host, () =>
  console.log(`Frontend: http://${host}:${port} — API: ${backend.origin}`),
);
if (!process.argv.includes("--skip-build")) {
  let debounce;
  for (const folder of ["src"])
    watch(resolve(root, folder), (_, name) => {
      if (name?.endsWith(".elm")) {
        clearTimeout(debounce);
        debounce = setTimeout(() => compile().catch(console.error), 150);
      }
    });
}
