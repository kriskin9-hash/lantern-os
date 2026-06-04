const http = require("http");
const fs = require("fs");
const path = require("path");

const repoRoot = process.env.LANTERN_REPO_ROOT || path.resolve(__dirname, "..", "..");
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

const dreamerDir = path.join(repoRoot, "data", "dreamer", "notebooks");

function cloudNormUser(u) {
  return String(u || "orion").toLowerCase().replace(/[^a-z0-9_-]/g, "_").slice(0, 40) || "orion";
}

function cloudReadNotebook(user) {
  const p = path.join(dreamerDir, `${user}.jsonl`);
  try {
    return fs.readFileSync(p, "utf8").trim().split("\n").filter(Boolean)
      .map(l => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean);
  } catch { return []; }
}

async function cloudAppendEntry(user, entry) {
  const record = {
    id: crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36),
    kind: String(entry.kind || "note").slice(0, 40),
    text: String(entry.text || "").slice(0, 8000),
    tags: Array.isArray(entry.tags) ? entry.tags.slice(0, 10) : [],
    recordedAt: new Date().toISOString(),
    private: true,
  };
  const p = path.join(dreamerDir, `${user}.jsonl`);
  await fs.promises.mkdir(path.dirname(p), { recursive: true });
  await fs.promises.appendFile(p, JSON.stringify(record) + "\n", "utf8");
  return record;
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

  // POST write allowlist — add endpoints here to permit writes in cloud mode
  const writePathsAllowed = [
    url.pathname === "/api/chat" && req.method === "POST",
    url.pathname === "/api/dream/chat" && req.method === "POST",
    url.pathname === "/api/dream/chat/stream" && req.method === "POST",
    url.pathname === "/api/dream/create" && req.method === "POST",
    url.pathname === "/api/dreamer" && req.method === "POST",
    url.pathname === "/api/dreamer/chat" && req.method === "POST",
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

  if (url.pathname === "/health") {
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

  if (url.pathname === "/api/dream/create" && req.method === "POST") {
    try {
      const raw = await collectRequestBody(req);
      const body = JSON.parse(raw);
      const dreamId = `dream_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
      const entry = {
        id: dreamId,
        timestamp: new Date().toISOString(),
        kind: body.kind || "dream",
        text: String(body.text || body.content || "").slice(0, 10000),
        lucidity: Number(body.lucidity) || 0,
        emotions: (body.emotions || []).slice(0, 20),
        tags: (body.tags || []).slice(0, 10),
        symbols: body.symbols || [],
        linked_goals: body.linked_goals || [],
        priority: body.priority || "normal",
        reflection_on: body.reflection_on || [],
        source: "api",
      };
      const dreamDir = path.join(repoRoot, "data", "dream_journal");
      if (!fs.existsSync(dreamDir)) fs.mkdirSync(dreamDir, { recursive: true });
      const monthFile = path.join(dreamDir, `dreams_${new Date().toISOString().substring(0, 7)}.jsonl`);
      fs.appendFileSync(monthFile, JSON.stringify(entry) + "\n");
      sendJson(res, { id: dreamId, saved: true, entry });
    } catch (error) {
      sendJson(res, { error: error.message }, 400);
    }
    return;
  }

  if (url.pathname === "/api/dream/stats" && req.method === "GET") {
    try {
      const dreamDir = path.join(repoRoot, "data", "dream_journal");
      let entries = [];
      if (fs.existsSync(dreamDir)) {
        const files = fs.readdirSync(dreamDir).filter((f) => f.endsWith(".jsonl"));
        for (const file of files) {
          const content = fs.readFileSync(path.join(dreamDir, file), "utf-8").trim();
          if (content) {
            entries.push(...content.split("\n").map((line) => {
              try { return JSON.parse(line); } catch { return null; }
            }).filter(Boolean));
          }
        }
      }
      const stats = {
        total_entries: entries.length,
        entries_by_kind: {},
        top_emotions: {},
        top_tags: {},
        top_symbols: {},
        total_lucidity: 0,
        avg_lucidity: 0,
      };
      let totalLucidity = 0;
      for (const e of entries) {
        const k = e.kind || "dream";
        stats.entries_by_kind[k] = (stats.entries_by_kind[k] || 0) + 1;
        for (const em of (e.emotions || [])) stats.top_emotions[em] = (stats.top_emotions[em] || 0) + 1;
        for (const t of (e.tags || [])) stats.top_tags[t] = (stats.top_tags[t] || 0) + 1;
        for (const s of (e.symbols || [])) stats.top_symbols[s] = (stats.top_symbols[s] || 0) + 1;
        totalLucidity += e.lucidity || 0;
      }
      stats.total_lucidity = totalLucidity;
      if (entries.length > 0) stats.avg_lucidity = (totalLucidity / entries.length).toFixed(2);
      sendJson(res, stats);
    } catch (error) {
      sendJson(res, { error: error.message }, 500);
    }
    return;
  }

  // Streaming chat — SSE, word-by-word, works online and offline
  if (url.pathname === "/api/dream/chat/stream" && req.method === "POST") {
    res.writeHead(200, {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache",
      "Connection": "keep-alive",
      "X-Accel-Buffering": "no",
      "Access-Control-Allow-Origin": "*",
      "Referrer-Policy": "no-referrer",
      "X-Frame-Options": "DENY",
    });

    const send = (obj) => res.write(`data: ${JSON.stringify(obj)}\n\n`);

    try {
      const body = await collectRequestBody(req);
      const input = JSON.parse(body || "{}");
      const message = String(input.message || "").slice(0, 2000);
      const result = dreamChatReply(message, readRecentDreams(5));

      send({ type: "start" });

      // Stream word by word with natural variance
      const tokens = result.reply.split(/(\s+)/);
      for (let i = 0; i < tokens.length; i++) {
        if (tokens[i]) {
          send({ type: "token", text: tokens[i] });
          // Vary delay: longer after punctuation, short between words
          const isPunct = /[.!?,;:]$/.test(tokens[i].trim());
          await new Promise((r) => setTimeout(r, isPunct ? 60 + Math.random() * 80 : 18 + Math.random() * 28));
        }
      }

      send({ type: "done", suggestions: result.suggestions, online: result.online, draft: result.draft || null });
    } catch (err) {
      send({ type: "done", suggestions: ["Log a dream", "Recent dreams", "Mirror a dream"], online: false });
    }

    res.write("data: [DONE]\n\n");
    res.end();
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
      message: "Action held in AWS cloud mode.",
      reason: "The local orchestrator queue is not exposed on AWS cloud mode.",
    }, 403);
    return;
  }

  // ── Dreamer endpoints (cloud-compatible) ───────────────────────────────────
  if (url.pathname === "/api/dreamer" && req.method === "GET") {
    const user = cloudNormUser(url.searchParams.get("user") || "orion");
    const entries = cloudReadNotebook(user);
    sendJson(res, { user, entries, mode: "cloud" });
    return;
  }

  if (url.pathname === "/api/dreamer" && req.method === "POST") {
    try {
      const raw = await collectRequestBody(req);
      const body = JSON.parse(raw);
      const user = cloudNormUser(body.user || "orion");
      const record = await cloudAppendEntry(user, body);
      sendJson(res, { saved: true, record });
    } catch (error) { sendJson(res, { error: error.message }, 400); }
    return;
  }

  if (url.pathname === "/api/dreamer/chat" && req.method === "POST") {
    try {
      const raw = await collectRequestBody(req);
      const body = JSON.parse(raw);
      const user = cloudNormUser(body.user || "orion");
      const kind = String(body.kind || "dream").slice(0, 40);
      const text = String(body.text || "").slice(0, 4000);
      const record = await cloudAppendEntry(user, { kind, text });
      const fallbacks = {
        dream: "What a vivid scene — the imagery here is worth sitting with. What feeling stayed with you when you woke?",
        note: "Noted and held. Patterns like this often surface for a reason. Anything else connecting to this?",
        symbol: "Symbols return when they have something left to say. What does this one mean to you right now?",
        mirror: "Mirrors show what we're ready to see. This reflection feels important — what does it reveal?",
        event: "Moments like this leave a mark. How did it shift something inside you?",
        lore: "Every mythology has its keepers. What part of this lore feels most alive for you today?",
        character: "Characters in our inner world often carry messages. What does this one want you to know?",
        place: "Places in dreams hold their own gravity. What did this space feel like to be in?",
      };
      sendJson(res, { saved: true, record, reply: fallbacks[kind] || fallbacks.note });
    } catch (error) { sendJson(res, { error: error.message }, 400); }
    return;
  }

  const staticPath = url.pathname === "/" ? "index.html" :
    url.pathname === "/outreach" ? "outreach.html" :
    url.pathname.slice(1);
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
  const actualPort = server.address().port;
  console.log(`Lantern Garage (Cloud) running on port ${actualPort}`);
});
