const http = require("http");
const fs = require("fs");
const path = require("path");

const repoRoot = path.resolve(__dirname, "..", "..");
const publicRoot = path.join(__dirname, "public");
const port = Number(process.env.PORT || process.env.LANTERN_GARAGE_PORT || 10000);
const host = process.env.HOST || "0.0.0.0";

function readJson(relativePath, fallback = {}) {
  try {
    return JSON.parse(fs.readFileSync(path.join(repoRoot, relativePath), "utf8").replace(/^\uFEFF/, ""));
  } catch {
    return fallback;
  }
}

function readJsonl(relativePath, limit = 20) {
  try {
    return fs.readFileSync(path.join(repoRoot, relativePath), "utf8")
      .split(/\r?\n/)
      .filter(Boolean)
      .slice(-limit)
      .map((line) => {
        try { return JSON.parse(line); } catch { return { parseError: true, raw: line }; }
      });
  } catch {
    return [];
  }
}

function sendJson(res, data, status = 200) {
  res.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
  });
  res.end(JSON.stringify(data, null, 2));
}

function sendText(res, text, status = 200, contentType = "text/plain; charset=utf-8") {
  res.writeHead(status, {
    "Content-Type": contentType,
    "Cache-Control": "no-store",
  });
  res.end(text);
}

function sendFile(res, filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const type = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".json": "application/json; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
    ".pdf": "application/pdf",
  }[ext] || "application/octet-stream";

  fs.readFile(filePath, (error, data) => {
    if (error) {
      sendJson(res, { error: "not_found" }, 404);
      return;
    }
    res.writeHead(200, { "Content-Type": type, "Cache-Control": "no-store" });
    res.end(data);
  });
}

function getStatus() {
  const arc = readJson("data/arc-reactor/status.json", {});
  const wallet = readJson("data/wallet/local-cash-wallet.json", {});
  const readiness = readJson("manifests/validation/DUAL-BOOT-PREP-LATEST.json", {});
  return {
    generatedAt: new Date().toISOString(),
    app: "Lantern Garage",
    mode: "render_public_static",
    boundary: "Public Render mode serves safe program pages and read-only status only. Local MCP, local controls, and agent dispatch stay local-held.",
    arc,
    wallet: {
      clearedCashUsd: wallet.clearedCashUsd ?? 0,
      pendingInvoiceUsd: wallet.pendingInvoiceUsd ?? 0,
      pendingInvoices: wallet.pendingInvoices ?? [],
    },
    controls: {
      dashboardOk: false,
      mcpOk: false,
      accessXExists: false,
      boundary: "local_only_not_available_on_render",
    },
    readiness,
  };
}

async function route(req, res) {
  const url = new URL(req.url, `http://${req.headers.host || "localhost"}`);

  if (url.pathname === "/health" || url.pathname === "/api/health") {
    sendJson(res, { ok: true, service: "lantern-garage", mode: "render", generatedAt: new Date().toISOString() });
    return;
  }

  if (url.pathname === "/api/status") {
    sendJson(res, getStatus());
    return;
  }

  if (url.pathname === "/api/rag-cache") {
    sendJson(res, readJsonl("data/rag-intake/external-llm-web-cache/cache.jsonl", 50));
    return;
  }

  if (url.pathname === "/api/conversations") {
    sendJson(res, { path: "render_public_static", conversations: [] });
    return;
  }

  if (url.pathname === "/api/flat-rag-house") {
    sendJson(res, {
      generatedAt: new Date().toISOString(),
      purpose: "Render-safe public Lantern OS surface.",
      boundary: "No local source repo or MCP access from Render.",
      sources: [],
      ragRecordCount: readJsonl("data/rag-intake/external-llm-web-cache/cache.jsonl", 200).length,
      windowsSurface: { host: "render", defaultBootMutation: "blocked" },
    });
    return;
  }

  if (url.pathname === "/api/operator-queue") {
    sendJson(res, { items: [], generatedAt: new Date().toISOString(), boundary: "local orchestrator queue is not exposed on Render" });
    return;
  }

  if (url.pathname.startsWith("/api/actions/")) {
    sendJson(res, {
      code: 2,
      stdout: "Action held in Render mode.",
      stderr: "Local MCP, PowerShell, local controls, and agent dispatch are local-only.",
    }, 202);
    return;
  }

  if (url.pathname === "/os") {
    res.writeHead(302, { Location: "/" });
    res.end();
    return;
  }

  if (url.pathname === "/outreach") {
    res.writeHead(302, { Location: "/outreach.html" });
    res.end();
    return;
  }

  if (url.pathname.startsWith("/repo/")) {
    const relative = decodeURIComponent(url.pathname.replace(/^\/repo\//, ""));
    const target = path.resolve(repoRoot, relative);
    if (!target.startsWith(repoRoot)) {
      sendJson(res, { error: "forbidden" }, 403);
      return;
    }
    sendFile(res, target);
    return;
  }

  const staticPath = url.pathname === "/" ? "index.html" : url.pathname.slice(1);
  const target = path.resolve(publicRoot, staticPath);
  if (!target.startsWith(publicRoot)) {
    sendJson(res, { error: "forbidden" }, 403);
    return;
  }
  sendFile(res, target);
}

const server = http.createServer((req, res) => {
  route(req, res).catch((error) => sendJson(res, { error: error.message }, 500));
});

server.listen(port, host, () => {
  console.log(`Lantern Garage Render app listening on http://${host}:${port}`);
});
