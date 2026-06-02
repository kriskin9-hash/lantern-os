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

function readRecentDreams(limit = 5) {
  const dreamDir = path.join(repoRoot, "data", "dream_journal");
  const entries = [];
  try {
    if (!fs.existsSync(dreamDir)) return [];
    const files = fs.readdirSync(dreamDir).filter((f) => f.endsWith(".jsonl"));
    for (const file of files) {
      const content = fs.readFileSync(path.join(dreamDir, file), "utf-8").trim();
      if (!content) continue;
      for (const line of content.split("\n")) {
        try { entries.push(JSON.parse(line)); } catch { /* skip */ }
      }
    }
  } catch { return []; }
  entries.sort((a, b) => String(b.timestamp || "").localeCompare(String(a.timestamp || "")));
  return entries.slice(0, limit);
}

// Door-series canon — keeps the persona grounded with no external API.
const DREAM_DOORS = {
  founder: { name: "Founder's Wish Door", anchors: ["Love", "Safety", "Truth", "Beauty", "Freedom", "Memory", "Return"], phrase: "Hold the center. Protect the wish. Return to the anchor." },
  xp: { name: "Gage's Windows XP Door", phrase: "Never log off. Level up always." },
  xenon: { name: "Xenon Door", phrase: "Build beyond one world." },
  fog: { name: "Sea of Fog and Clouds Door", phrase: "Let the powerful images rest before they become stories." },
  sigil: { name: "Sigil / City of Doors", phrase: "You hold the keys. You protect the doors. You are never alone." },
};

// In-character Dream Journal reply. Pure rule-engine — no network needed.
function dreamChatReply(message, recentDreams) {
  const text = String(message || "").trim();
  const lower = text.toLowerCase();
  const base = ["Log a dream", "Recent dreams", "Mirror a dream", "Tell me about the doors"];

  if (!text) {
    return { reply: "The dream door is open. What did you bring back? Tell me a dream, or tap a door below.", suggestions: base, online: true };
  }
  for (const key of Object.keys(DREAM_DOORS)) {
    if (lower.includes(key) ||
        (key === "founder" && lower.includes("wish")) ||
        (key === "xp" && (lower.includes("windows") || lower.includes("gage"))) ||
        (key === "fog" && lower.includes("garden")) ||
        (key === "sigil" && lower.includes("city"))) {
      const d = DREAM_DOORS[key];
      const anchors = d.anchors ? ` Its anchors: ${d.anchors.join(", ")}.` : "";
      return { reply: `${d.name} stands open.${anchors} "${d.phrase}" What do you see when you step through? Describe it and I will hold it in the journal.`, suggestions: ["Log this as a dream", "Another door", "Mirror a dream"], online: true };
    }
  }
  if (/^(hi|hello|hey|good (morning|evening|night)|greetings)/.test(lower)) {
    return { reply: "Welcome back. I am the Dream Journal — local, private, always here, even offline. Did you dream? Tell me what was vivid.", suggestions: base, online: true };
  }
  if (lower.includes("mirror") || lower.includes("interpret") || lower.includes("mean") || lower.includes("symbol")) {
    const last = recentDreams[0];
    if (last) {
      const tags = (last.tags || []).join(", ") || "no tags yet";
      return { reply: `Let us mirror your last entry. You wrote: "${String(last.text || "").slice(0, 160)}" (${tags}). Three questions to sit with: 1) What feeling stayed after waking? 2) What in waking life does this echo? 3) What small, reversible step would honor it?`, suggestions: ["Recent dreams", "Tell me about the doors"], online: true };
    }
    return { reply: "There is nothing in the journal to mirror yet. Tell me a dream first, then I will reflect it back gently.", suggestions: ["Log a dream", "Tell me about the doors"], online: true };
  }
  if (lower.includes("recent") || lower.includes("history") || lower.includes("last dream")) {
    if (recentDreams.length === 0) {
      return { reply: "Your journal is empty so far — a fresh page. When you are ready, tell me the first dream.", suggestions: ["Log a dream", "Tell me about the doors"], online: true };
    }
    const lines = recentDreams.slice(0, 3).map((d, i) => `${i + 1}. ${String(d.text || "").slice(0, 90)}${(d.tags && d.tags.length) ? " [" + d.tags.join(", ") + "]" : ""}`);
    return { reply: `Here are recent entries:\n${lines.join("\n")}\n\nWould you like to mirror one of them?`, suggestions: ["Mirror a dream", "Tell me about the doors"], online: true };
  }
  if (lower.includes("log") || lower.includes("had a dream") || lower.includes("dreamed") || lower.includes("dreamt") || lower.includes("save")) {
    return { reply: "Good — let us keep it. Tell me the dream in your own words: what was vivid, what mattered, what surprised you.", suggestions: ["Recent dreams", "Mirror a dream"], online: true };
  }
  return { reply: `I hear it: "${text.slice(0, 160)}". That is worth keeping. Tap "Log this as a dream" to save it, or tell me more about how it felt.`, suggestions: ["Log this as a dream", "Mirror a dream", "Tell me about the doors"], online: true, draft: text };
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
    url.pathname === "/api/dream/chat" && req.method === "POST",
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

  if (url.pathname === "/api/dream/chat" && req.method === "POST") {
    try {
      const body = await collectRequestBody(req);
      const input = JSON.parse(body || "{}");
      const message = String(input.message || "").slice(0, 2000);
      const result = dreamChatReply(message, readRecentDreams(5));
      sendJson(res, { ...result, generatedAt: new Date().toISOString() });
    } catch (error) {
      // Stay in character even on error.
      sendJson(res, {
        reply: "I am still here. Something tangled in the request, but the dream door stays open. Tell me again?",
        suggestions: ["Log a dream", "Recent dreams", "Mirror a dream"],
        online: true,
        error: error.message,
      });
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
