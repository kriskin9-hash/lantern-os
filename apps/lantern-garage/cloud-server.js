const http = require("http");
const fs = require("fs");
const path = require("path");

const repoRoot = path.resolve(__dirname, "..", "..");
const publicRoot = path.join(__dirname, "public");
const port = Number(process.env.PORT || 8080);
const host = "0.0.0.0";

function readJson(relativePath, fallback = null) {
  try {
    const content = fs.readFileSync(path.join(repoRoot, relativePath), "utf8");
    return JSON.parse(content);
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
        try {
          return JSON.parse(line);
        } catch {
          return { parseError: true, raw: line };
        }
      });
  } catch {
    return [];
  }
}

function sendJson(res, data, status = 200) {
  const body = JSON.stringify(data, null, 2);
  res.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  });
  res.end(body);
}

function sendFile(res, filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const type = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".png": "image/png",
    ".json": "application/json; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
    ".pdf": "application/pdf",
  }[ext] || "application/octet-stream";

  fs.readFile(filePath, (error, data) => {
    if (error) {
      sendJson(res, { error: "not_found" }, 404);
      return;
    }
    res.writeHead(200, {
      "Content-Type": type,
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
      "Referrer-Policy": "no-referrer",
      "X-Frame-Options": "DENY",
      "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
      "Access-Control-Allow-Origin": "*",
    });
    res.end(data);
  });
}

function sendHtml(res, html, status = 200) {
  res.writeHead(status, {
    "Content-Type": "text/html; charset=utf-8",
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Access-Control-Allow-Origin": "*",
  });
  res.end(html);
}

function getMcpFeatureOverview() {
  return {
    name: "Lantern MCP Bridge",
    description: "Model Context Protocol, not Multi-Chain Protocol",
    status: "operational",
    features: ["tool_discovery", "tool_invocation", "sse_transport"],
    boundaryMode: "cloud-read-only",
  };
}

function tryMcpChatReply(messages, context) {
  return {
    source: "mcp_bridge",
    context,
    queued: true,
    status: "waiting_for_mcp_response",
  };
}

async function collectRequestBody(req, maxBytes = 64000) {
  return new Promise((resolve, reject) => {
    let body = "";
    req.on("data", (chunk) => {
      body += chunk.toString();
      if (Buffer.byteLength(body, "utf8") > maxBytes) {
        reject(new Error("request_body_too_large"));
        req.destroy();
      }
    });
    req.on("end", () => resolve(body));
    req.on("error", reject);
  });
}

async function route(req, res) {
  const url = new URL(req.url, `http://${req.headers.host || "localhost"}`);

  if (req.method === "OPTIONS") {
    res.writeHead(204, {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
      "Referrer-Policy": "no-referrer",
      "X-Frame-Options": "DENY",
      "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    });
    res.end();
    return;
  }

  // Cloud read-only gate: block all POST writes except explicitly allowed endpoints
  const writePathsAllowed = [
    url.pathname === "/api/chat" && req.method === "POST",
    url.pathname === "/api/command" && req.method === "POST",
    url.pathname.startsWith("/api/actions/") && req.method === "POST",
  ];

  if (req.method === "POST" && !writePathsAllowed.some(Boolean)) {
    sendJson(res, {
      error: "cloud_read_only_method_not_allowed",
      message: "This endpoint is not available in cloud mode",
      method: req.method,
      path: url.pathname
    }, 403);
    return;
  }

  if (url.pathname === "/api/health") {
    sendJson(res, { ok: true, service: "lantern-garage-cloud", generatedAt: new Date().toISOString() });
    return;
  }

  if (url.pathname === "/api/status") {
    sendJson(res, {
      generatedAt: new Date().toISOString(),
      mode: "cloud",
      app: "Lantern Garage Cloud",
      status: "operational",
    });
    return;
  }

  if (url.pathname === "/api/cloud-mirrors") {
    const mirrors = readJson("manifests/cloud-mirrors.json", { cloudMirrors: [] });
    sendJson(res, mirrors);
    return;
  }

  if (url.pathname === "/api/mcp" && req.method === "GET") {
    sendJson(res, getMcpFeatureOverview());
    return;
  }

  if (url.pathname === "/api/chat" && req.method === "POST") {
    try {
      const body = await collectRequestBody(req);
      const input = JSON.parse(body || "{}");
      const reply = tryMcpChatReply(input.messages || [], { environment: "cloud" });
      sendJson(res, reply, 202);
    } catch (error) {
      sendJson(res, { error: error.message }, 400);
    }
    return;
  }

  if (url.pathname === "/api/command" && req.method === "POST") {
    try {
      const body = await collectRequestBody(req);
      const input = JSON.parse(body || "{}");
      sendJson(res, {
        status: "command_queued",
        command: input.command,
        boundaryMode: "cloud-read-only",
      }, 202);
    } catch (error) {
      sendJson(res, { error: error.message }, 400);
    }
    return;
  }

  if (url.pathname.startsWith("/api/actions/") && req.method === "POST") {
    const action = url.pathname.replace("/api/actions/", "");
    sendJson(res, {
      status: "action_not_available_in_cloud",
      action,
      reason: "Local actions require operator machine access",
    }, 403);
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

server.on("error", (error) => {
  if (error.code === "EADDRINUSE") {
    console.error(`Lantern Garage Cloud port ${port} is already in use.`);
    process.exitCode = 1;
    return;
  }
  throw error;
});

server.listen(port, host, () => {
  console.log(`Lantern Garage (Cloud) running on port ${port}`);
});
