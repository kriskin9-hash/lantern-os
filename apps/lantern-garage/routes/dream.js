// Dream Journal core — create, chat, stream, stats, search, export, read, settings
const PROVIDER_KEYS = [
  "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY",
  "XAI_API_KEY", "OLLAMA_BASE_URL", "OLLAMA_MODEL", "ANTHROPIC_MODEL", "OPENAI_MODEL", "GEMINI_MODEL",
];

module.exports = async function dreamRoutes(req, res, url, deps) {
  const { fs, path, sendJson, collectRequestBody, appendJsonlQueued,
    repoRoot, maxDreamerTextLength, maxConversationTextLength,
    readRecentDreams, dreamChatReply, appendConversationEntry,
    unifiedAgentGreet, unifiedAgentHealth, unifiedAgentInspect,
    handleStreamChat } = deps;

  // ── Unified agent endpoints ───────────────────────────────────────────
  if (url.pathname === "/api/dream/greet" && req.method === "GET") {
    try {
      const recentDreams = readRecentDreams(5);
      const greet = await unifiedAgentGreet(recentDreams);
      sendJson(res, { ...greet, generatedAt: new Date().toISOString() });
    } catch (error) {
      sendJson(res, { greeting: "The dream door is open.", source: "offline_fallback", error: error.message });
    }
    return true;
  }
  if (url.pathname === "/api/agent/health" && req.method === "GET") {
    try {
      sendJson(res, { health: await unifiedAgentHealth(), generatedAt: new Date().toISOString() });
    } catch (error) { sendJson(res, { error: error.message }, 500); }
    return true;
  }
  if (url.pathname === "/api/agent/inspect" && req.method === "GET") {
    try {
      sendJson(res, { inspect: await unifiedAgentInspect(), generatedAt: new Date().toISOString() });
    } catch (error) { sendJson(res, { error: error.message }, 500); }
    return true;
  }

  // ── Dream CRUD ────────────────────────────────────────────────────────
  if (url.pathname === "/api/dream/create" && req.method === "POST") {
    try {
      const raw = await collectRequestBody(req);
      const body = JSON.parse(raw);
      const dreamId = `dream_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
      const normalizeList = (value, limit = 12) => {
        if (Array.isArray(value)) return value.map((item) => String(item).trim()).filter(Boolean).slice(0, limit);
        return String(value || "").split(",").map((item) => item.trim()).filter(Boolean).slice(0, limit);
      };
      const entry = {
        id: dreamId, timestamp: new Date().toISOString(),
        kind: String(body.kind || "dream").slice(0, 40),
        name: String(body.name || body.title || "").slice(0, 140),
        text: String(body.text || body.content || "").slice(0, maxDreamerTextLength),
        lucidity: Math.max(0, Math.min(1, Number(body.lucidity || 0))),
        clarity: Math.max(0, Math.min(1, Number(body.clarity || 0))),
        mood: String(body.mood || "").slice(0, 80),
        technique: String(body.technique || "").slice(0, 80),
        sleep_window: String(body.sleep_window || "").slice(0, 80),
        recurring: Boolean(body.recurring), dreamsign: Boolean(body.dreamsign),
        emotions: normalizeList(body.emotions, 12), tags: normalizeList(body.tags, 10),
        symbols: normalizeList(body.symbols, 12),
        linked_goals: body.linked_goals || [], priority: body.priority || "normal",
        reflection_on: body.reflection_on || [], source: "api",
      };
      const dreamDir = path.join(repoRoot, "data", "dream_journal");
      if (!fs.existsSync(dreamDir)) fs.mkdirSync(dreamDir, { recursive: true });
      const monthFile = path.join(dreamDir, `dreams_${new Date().toISOString().substring(0, 7)}.jsonl`);
      await appendJsonlQueued(monthFile, entry);
      sendJson(res, { id: dreamId, saved: true, entry, csf: { compressed: false } });
    } catch (error) { sendJson(res, { error: error.message }, 400); }
    return true;
  }

  if (url.pathname === "/api/dream/chat" && req.method === "POST") {
    try {
      const raw = await collectRequestBody(req);
      const body = JSON.parse(raw || "{}");
      const message = String(body.message || "").slice(0, maxDreamerTextLength);
      const recentDreams = readRecentDreams(5);
      const result = await dreamChatReply(message, recentDreams, body.agent || "", body.provider || "");
      try {
        await appendConversationEntry({ recordedAt: new Date().toISOString(), surface: "dream-journal", role: "operator", text: message.slice(0, maxConversationTextLength) });
        await appendConversationEntry({ recordedAt: new Date().toISOString(), surface: "dream-journal", role: "lantern", text: String(result.reply || "").slice(0, maxConversationTextLength) });
      } catch { /* logging non-critical */ }
      if (!result.reply) { sendJson(res, { error: result.error || "no_provider_configured", agent: result.agent, online: false }, 503); return true; }
      sendJson(res, { ...result, generatedAt: new Date().toISOString() });
    } catch (error) { sendJson(res, { error: error.message, online: false }); }
    return true;
  }

  if ((url.pathname === "/api/dream/stream" && req.method === "GET") ||
      (url.pathname === "/api/dream/chat/stream" && req.method === "POST")) {
    await handleStreamChat(req, url, res);
    return true;
  }

  // ── Dream stats / search / export / read ────────────────────────────
  if (url.pathname === "/api/dream/stats" && req.method === "GET") {
    try {
      const entries = loadDreamEntries(fs, path, repoRoot);
      const stats = { total_entries: entries.length, entries_by_kind: {}, top_emotions: {}, top_tags: {}, top_symbols: {}, total_lucidity: 0, avg_lucidity: 0 };
      for (const entry of entries) {
        stats.entries_by_kind[entry.kind || "dream"] = (stats.entries_by_kind[entry.kind || "dream"] || 0) + 1;
        for (const e of (entry.emotions || [])) stats.top_emotions[e] = (stats.top_emotions[e] || 0) + 1;
        for (const t of (entry.tags || [])) stats.top_tags[t] = (stats.top_tags[t] || 0) + 1;
        for (const s of (entry.symbols || [])) stats.top_symbols[s] = (stats.top_symbols[s] || 0) + 1;
        stats.total_lucidity += entry.lucidity || 0;
      }
      if (entries.length > 0) stats.avg_lucidity = (stats.total_lucidity / entries.length).toFixed(2);
      sendJson(res, stats);
    } catch (error) { sendJson(res, { error: error.message }, 400); }
    return true;
  }

  if (url.pathname === "/api/dream/search" && req.method === "GET") {
    try {
      const query = url.searchParams.get("text") || "";
      const tags = (url.searchParams.get("tags") || "").split(",").filter(t => t);
      const results = loadDreamEntries(fs, path, repoRoot).filter(e =>
        (query === "" || (e.text || "").toLowerCase().includes(query.toLowerCase())) &&
        (tags.length === 0 || tags.some(t => (e.tags || []).includes(t)))
      );
      sendJson(res, { query, tags, count: results.length, results: results.slice(0, 50) });
    } catch (error) { sendJson(res, { error: error.message }, 400); }
    return true;
  }

  if (url.pathname === "/api/dream/export" && req.method === "GET") {
    try {
      const format = url.searchParams.get("format") || "jsonl";
      const entries = loadDreamEntries(fs, path, repoRoot, true);
      if (format === "csv") {
        const cols = ["id", "timestamp", "kind", "text", "lucidity", "emotions", "tags", "symbols"];
        const escape = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
        const rows = [cols.join(","), ...entries.map(e => [
          escape(e.id), escape(e.timestamp), escape(e.kind), escape(e.text),
          escape(e.lucidity), escape((e.emotions || []).join(";")),
          escape((e.tags || []).join(";")), escape((e.symbols || []).join(";"))
        ].join(","))];
        res.writeHead(200, { "Content-Type": "text/csv", "Content-Disposition": `attachment; filename="dream-journal-${new Date().toISOString().substring(0,10)}.csv"` });
        res.end(rows.join("\n"));
      } else {
        res.writeHead(200, { "Content-Type": "application/x-ndjson", "Content-Disposition": `attachment; filename="dream-journal-${new Date().toISOString().substring(0,10)}.jsonl"` });
        res.end(entries.map(e => JSON.stringify(e)).join("\n"));
      }
    } catch (error) { sendJson(res, { error: error.message }, 400); }
    return true;
  }

  if (url.pathname.startsWith("/api/dream/read/") && req.method === "GET") {
    try {
      const id = url.pathname.replace("/api/dream/read/", "");
      const found = loadDreamEntries(fs, path, repoRoot).find(e => e.id === id);
      found ? sendJson(res, found) : sendJson(res, { error: "not_found" }, 404);
    } catch (error) { sendJson(res, { error: error.message }, 400); }
    return true;
  }

  // ── Provider settings ─────────────────────────────────────────────────
  if (url.pathname === "/api/settings/providers" && req.method === "GET") {
    const result = {};
    let any = false;
    for (const k of PROVIDER_KEYS) { result[k] = !!(process.env[k]); if (result[k]) any = true; }
    result._any = any;
    sendJson(res, result);
    return true;
  }

  if (url.pathname === "/api/settings/providers" && req.method === "POST") {
    try {
      const raw = await collectRequestBody(req);
      const { key, value } = JSON.parse(raw || "{}");
      if (!key || !PROVIDER_KEYS.includes(key)) { sendJson(res, { error: "unknown_key" }, 400); return true; }
      const envFilePath = path.join(repoRoot, ".env");
      let existing = fs.existsSync(envFilePath) ? fs.readFileSync(envFilePath, "utf8") : "";
      const lines = existing.split("\n").filter(l => !l.startsWith(`${key}=`) && !l.startsWith(`${key} =`));
      if (value) lines.push(`${key}=${value}`);
      fs.writeFileSync(envFilePath, lines.join("\n").replace(/\n{3,}/g, "\n\n").trim() + "\n", "utf8");
      if (value) process.env[key] = value; else delete process.env[key];
      sendJson(res, { ok: true });
    } catch (err) { sendJson(res, { error: err.message }, 500); }
    return true;
  }
};

// Shared helper — read all dream entries from monthly JSONL files
function loadDreamEntries(fs, path, repoRoot, sorted = false) {
  const dreamDir = path.join(repoRoot, "data", "dream_journal");
  if (!fs.existsSync(dreamDir)) return [];
  const files = fs.readdirSync(dreamDir).filter(f => f.endsWith(".jsonl"));
  if (sorted) files.sort();
  const entries = [];
  for (const file of files) {
    const content = fs.readFileSync(path.join(dreamDir, file), "utf-8").trim();
    if (content) {
      for (const line of content.split("\n")) {
        try { entries.push(JSON.parse(line)); } catch { /* skip bad lines */ }
      }
    }
  }
  return entries;
}
