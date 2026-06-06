// Dream Journal core — create, chat, stream, stats, search, export, read, settings
const PROVIDER_KEYS = [
  "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY",
  "XAI_API_KEY", "OLLAMA_BASE_URL", "OLLAMA_MODEL", "ANTHROPIC_MODEL", "OPENAI_MODEL", "GEMINI_MODEL",
  "DISCORD_BOT_TOKEN", "LANTERN_DISCORD_GUILD_ID",
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
        reflection_on: body.reflection_on || [], source: String(body.source || "api").slice(0, 40),
        dcf_class: body.dcf_class || null,
        rps_flags: body.rps_flags || [],
        ctf_glyphs: normalizeList(body.ctf_glyphs, 20),
      };
      const dreamDir = path.join(repoRoot, "data", "dream_journal");
      if (!fs.existsSync(dreamDir)) fs.mkdirSync(dreamDir, { recursive: true });
      const monthFile = path.join(dreamDir, `dreams_${new Date().toISOString().substring(0, 7)}.jsonl`);
      await appendJsonlQueued(monthFile, entry);
      // MemOS ingest runs via: python -c "from src.convergence_io.memos_bridge import get_cube; get_cube().ingest_all()"
      // or automatically on each TesseractEngine._convergence_rag() call (lazy load).
      // Background CSF compression (non-blocking)
      let csfStats = { compressed: false };
      try {
        const { spawn } = require("child_process");
        const py = process.platform === "win32" ? "python" : "python3";
        const script = `from src.csf.dream_compressor import compress_dream_file; compress_dream_file(r'${monthFile}')`;
        const proc = spawn(py, ["-c", script], { cwd: repoRoot, env: { ...process.env, PYTHONPATH: path.join(repoRoot, "src") } });
        proc.on("close", (code) => {
          // Compression complete; .csf file written alongside .jsonl
        });
      } catch { /* compression is non-critical */ }
      sendJson(res, { id: dreamId, saved: true, entry, csf: csfStats });
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

    // ── Three Doors game ────────────────────────────────────────────────
  if (url.pathname === "/api/dream/doors" && req.method === "POST") {
    try {
      const raw = await collectRequestBody(req);
      const body = JSON.parse(raw || "{}");
      const userId = String(body.userId || "web-anon");
      const action = String(body.action || "start");
      const choice = String(body.choice || "");

      const { spawn } = require("child_process");
      const enginePath = path.join(repoRoot, "src", "three_doors_engine.py");
      const py = process.platform === "win32" ? "python" : "python3";

      let script = "";
      if (action === "start" || action === "reset") {
        script = `from three_doors_engine import ThreeDoorsEngine; e=ThreeDoorsEngine("${userId}"); print(__import__('json').dumps(e.to_api_response(e.reset() if "${action}"=="reset" else e.start_game())))`;
      } else if (action === "choose") {
        script = `from three_doors_engine import ThreeDoorsEngine; e=ThreeDoorsEngine("${userId}"); s=e.choose_door("${choice}"); print(__import__('json').dumps(e.to_api_response(s) if s else {"error":"invalid_choice"}))`;
      } else {
        script = `from three_doors_engine import ThreeDoorsEngine; e=ThreeDoorsEngine("${userId}"); print(__import__('json').dumps(e.to_api_response()))`;
      }

      const result = await new Promise((resolve, reject) => {
        const proc = spawn(py, ["-c", script], { cwd: repoRoot, env: { ...process.env, PYTHONPATH: path.join(repoRoot, "src") } });
        let out = "", err = "";
        proc.stdout.on("data", (c) => (out += c));
        proc.stderr.on("data", (c) => (err += c));
        proc.on("close", (code) => {
          if (code !== 0) reject(new Error(err || `exit ${code}`));
          else resolve(out.trim());
        });
        proc.on("error", reject);
      });

      const data = JSON.parse(result);
      sendJson(res, { ...data, generatedAt: new Date().toISOString() });
    } catch (error) { sendJson(res, { error: error.message }, 500); }
    return true;
  }

  if (url.pathname === "/api/dream/doors/image" && req.method === "POST") {
    try {
      const raw = await collectRequestBody(req);
      const body = JSON.parse(raw || "{}");
      const userId = String(body.userId || "web-anon");
      const doorIdx = Number(body.doorIndex || 0);

      const sdUrl = process.env.STABLE_DIFFUSION_URL || process.env.SD_WEBUI_URL;
      if (!sdUrl) {
        const { spawn } = require("child_process");
        const py = process.platform === "win32" ? "python" : "python3";
        const script = `from three_doors_engine import ThreeDoorsEngine; e=ThreeDoorsEngine("${userId}"); print(__import__('json').dumps(e.image_suggestions_for_ai()[${doorIdx}] if ${doorIdx} < 3 else {}))`;
        const result = await new Promise((resolve, reject) => {
          const proc = spawn(py, ["-c", script], { cwd: repoRoot, env: { ...process.env, PYTHONPATH: path.join(repoRoot, "src") } });
          let out = "";
          proc.stdout.on("data", (c) => (out += c));
          proc.on("close", (code) => resolve(out.trim()));
          proc.on("error", reject);
        });
        const suggestion = JSON.parse(result);
        sendJson(res, {
          available: false,
          sdUrl: null,
          suggestion,
          message: "No local Stable Diffusion detected. Use the prompt with your preferred image generator (DALL-E, Midjourney, etc.)",
          generatedAt: new Date().toISOString(),
        });
        return true;
      }

      const { spawn } = require("child_process");
      const py = process.platform === "win32" ? "python" : "python3";
      const script = `from three_doors_engine import ThreeDoorsEngine; e=ThreeDoorsEngine("${userId}"); print(e.sd_prompt_for_state())`;
      const promptResult = await new Promise((resolve, reject) => {
        const proc = spawn(py, ["-c", script], { cwd: repoRoot, env: { ...process.env, PYTHONPATH: path.join(repoRoot, "src") } });
        let out = "";
        proc.stdout.on("data", (c) => (out += c));
        proc.on("close", (code) => resolve(out.trim()));
        proc.on("error", reject);
      });

      sendJson(res, {
        available: true,
        sdUrl,
        prompt: promptResult,
        message: "Stable Diffusion endpoint detected. POST to /sdapi/v1/txt2img with this prompt to generate the door image.",
        generatedAt: new Date().toISOString(),
      });
    } catch (error) { sendJson(res, { error: error.message }, 500); }
    return true;
  }

  // ── Dream stats / search / export / read ────────────────────────────
  if (url.pathname === "/api/dream/stats" && req.method === "GET") {
    try {
      const entries = loadDreamEntries(fs, path, repoRoot);
      const stats = { total_entries: entries.length, entries_by_kind: {}, top_emotions: {}, top_tags: {}, top_symbols: {}, top_ctf: {}, entries_with_ctf: 0, total_lucidity: 0, avg_lucidity: 0 };
      for (const entry of entries) {
        stats.entries_by_kind[entry.kind || "dream"] = (stats.entries_by_kind[entry.kind || "dream"] || 0) + 1;
        for (const e of (entry.emotions || [])) stats.top_emotions[e] = (stats.top_emotions[e] || 0) + 1;
        for (const t of (entry.tags || [])) stats.top_tags[t] = (stats.top_tags[t] || 0) + 1;
        for (const s of (entry.symbols || [])) stats.top_symbols[s] = (stats.top_symbols[s] || 0) + 1;
        const ctf = entry.ctf_glyphs || [];
        if (ctf.length) stats.entries_with_ctf++;
        for (const g of ctf) stats.top_ctf[g] = (stats.top_ctf[g] || 0) + 1;
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
      const ctf = (url.searchParams.get("ctf") || "").split(",").filter(t => t);
      const results = loadDreamEntries(fs, path, repoRoot).filter(e =>
        (query === "" || (e.text || "").toLowerCase().includes(query.toLowerCase())) &&
        (tags.length === 0 || tags.some(t => (e.tags || []).includes(t))) &&
        (ctf.length === 0 || ctf.some(t => (e.ctf_glyphs || []).includes(t)))
      );
      sendJson(res, { query, tags, ctf, count: results.length, results: results.slice(0, 50) });
    } catch (error) { sendJson(res, { error: error.message }, 400); }
    return true;
  }

  if (url.pathname === "/api/dream/export" && req.method === "GET") {
    try {
      const format = url.searchParams.get("format") || "jsonl";
      const entries = loadDreamEntries(fs, path, repoRoot, true);
      if (format === "csv") {
        const cols = ["id", "timestamp", "kind", "text", "lucidity", "emotions", "tags", "symbols", "ctf_glyphs"];
        const escape = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
        const rows = [cols.join(","), ...entries.map(e => [
          escape(e.id), escape(e.timestamp), escape(e.kind), escape(e.text),
          escape(e.lucidity), escape((e.emotions || []).join(";")),
          escape((e.tags || []).join(";")), escape((e.symbols || []).join(";")), escape((e.ctf_glyphs || []).join(";"))
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

  // ── Symbol co-occurrence timeline ────────────────────────────────────
  if (url.pathname === "/api/dream/symbols/timeline" && req.method === "GET") {
    try {
      const entries = loadDreamEntries(fs, path, repoRoot);
      const byWeek = {};
      for (const e of entries) {
        if (!e.timestamp) continue;
        const d = new Date(e.timestamp);
        const week = `${d.getUTCFullYear()}-W${String(Math.ceil((d.getUTCDate() - d.getUTCDay() + 6) / 7)).padStart(2,'0')}`;
        if (!byWeek[week]) byWeek[week] = {};
        for (const s of [...(e.symbols || []), ...(e.tags || [])]) {
          byWeek[week][s] = (byWeek[week][s] || 0) + 1;
        }
      }
      // Co-occurrence across all entries
      const coOccur = {};
      for (const e of entries) {
        const syms = [...(e.symbols || []), ...(e.tags || [])].slice(0, 8);
        for (let a = 0; a < syms.length; a++)
          for (let b = a + 1; b < syms.length; b++) {
            const key = [syms[a], syms[b]].sort().join('⟶');
            coOccur[key] = (coOccur[key] || 0) + 1;
          }
      }
      const topPairs = Object.entries(coOccur).sort((x,y)=>y[1]-x[1]).slice(0,10)
        .map(([k,v]) => ({ pair: k, count: v }));
      sendJson(res, { weeks: byWeek, top_pairs: topPairs, total_entries: entries.length });
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
      const envFilePath = path.join(repoRoot, ".env.local");
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
