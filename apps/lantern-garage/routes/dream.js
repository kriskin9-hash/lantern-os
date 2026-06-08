const https = require("https");
const { refreshProviderCache } = require("../lib/provider-cache");

// Dream Journal core — create, chat, stream, stats, search, export, read, settings
const PROVIDER_KEYS = [
  "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY",
  "XAI_API_KEY", "OLLAMA_BASE_URL", "OLLAMA_MODEL", "ANTHROPIC_MODEL", "OPENAI_MODEL", "GEMINI_MODEL",
  "DISCORD_BOT_TOKEN", "LANTERN_DISCORD_GUILD_ID",
  "ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID",
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
      // Background CSF compression (non-blocking, debounced by file mtime)
      let csfStats = { compressed: false };
      try {
        const csfFile = monthFile.replace(/\.jsonl$/, ".csf");
        const jsonlStat = fs.existsSync(monthFile) ? fs.statSync(monthFile) : null;
        const csfStat = fs.existsSync(csfFile) ? fs.statSync(csfFile) : null;
        const needsCompress = !csfStat || !jsonlStat || (csfStat.mtime < jsonlStat.mtime);
        if (needsCompress) {
          const { spawn } = require("child_process");
          const py = process.platform === "win32" ? "python" : "python3";
          const script = `from csf.dream_compressor import compress_dream_file; compress_dream_file(r'${monthFile}')`;
          const proc = spawn(py, ["-c", script], { cwd: repoRoot, env: { ...process.env, PYTHONPATH: path.join(repoRoot, "src") } });
          proc.on("close", (code) => {
            csfStats = { compressed: code === 0 };
          });
        } else {
          csfStats = { compressed: true, cached: true };
        }
      } catch { /* compression is non-critical */ }

      // MemOS save-time ingest (non-blocking)
      let memosResult = { ingested: false };
      try {
        const { spawn } = require("child_process");
        const py = process.platform === "win32" ? "python" : "python3";
        const script = `import sys,json; from convergence_io.memos_bridge import get_cube; c=get_cube(); r=c.ingest_entry(json.loads(sys.stdin.read())); print(json.dumps({'ingested': r}))`;
        const proc = spawn(py, ["-c", script], { cwd: repoRoot, env: { ...process.env, PYTHONPATH: path.join(repoRoot, "src") } });
        let out = "";
        proc.stdout.on("data", (d) => { out += d.toString(); });
        proc.on("close", () => {
          try { memosResult = JSON.parse(out.trim()); } catch { /* non-critical */ }
        });
        proc.stdin.write(JSON.stringify(entry));
        proc.stdin.end();
      } catch { /* MemOS ingest is non-critical */ }

      sendJson(res, { id: dreamId, saved: true, entry, csf: csfStats, memos: memosResult });
    } catch (error) { sendJson(res, { error: error.message }, 400); }
    return true;
  }

  if (url.pathname === "/api/dream/chat" && req.method === "POST") {
    try {
      const raw = await collectRequestBody(req);
      const body = JSON.parse(raw || "{}");
      const message = String(body.message || "").slice(0, maxDreamerTextLength);
      const recentDreams = readRecentDreams(5);
      const provStart = Date.now();
      const result = await dreamChatReply(message, recentDreams, body.agent || "", body.provider || "");
      const provLatency = Date.now() - provStart;
      try {
        await appendConversationEntry({ recordedAt: new Date().toISOString(), surface: "dream-journal", role: "operator", text: message.slice(0, maxConversationTextLength) });
        await appendConversationEntry({ recordedAt: new Date().toISOString(), surface: "dream-journal", role: "lantern", text: String(result.reply || "").slice(0, maxConversationTextLength) });
      } catch { /* logging non-critical */ }
      // Convergence IO provenance (AAPF) — lightweight Node-side record
      try {
        recordChatProvenance({
          actionId: `chat-${Date.now().toString(36)}-${Math.random().toString(36).substr(2, 4)}`,
          agentId: result.agent || "unknown",
          providerId: result.online ? (body.provider || "auto") : "offline",
          inputSummary: message.slice(0, 200),
          outputSummary: String(result.reply || "").slice(0, 200),
          latencyMs: provLatency,
          status: result.reply ? "ok" : (result.error ? "error" : "offline"),
          errorMsg: result.error || "",
          metadata: { source: result.source || "unknown", threeDoors: !!result.threeDoors },
        });
      } catch { /* provenance non-critical */ }
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

  // ── MemOS memory health (cached 5s to avoid Python spawn per poll) ──
  if (url.pathname === "/api/dream/memory/health" && req.method === "GET") {
    const now = Date.now();
    if (module._memosHealthCache && (now - module._memosHealthCache.ts) < 5000) {
      sendJson(res, { ...module._memosHealthCache.data, cached: true, generatedAt: new Date().toISOString() });
      return true;
    }
    try {
      const { spawn } = require("child_process");
      const py = process.platform === "win32" ? "python" : "python3";
      const script = `from convergence_io.memos_bridge import memos_available, get_cube; c=get_cube(); print(__import__('json').dumps({'available': memos_available(), 'installed': memos_available(), 'entry_count': len(c._entries), 'fallback': not memos_available(), 'last_ingest': c._entries[0].get('timestamp','') if c._entries else ''}))`;
      const result = await new Promise((resolve, reject) => {
        let out = "", err = "";
        const proc = spawn(py, ["-c", script], { cwd: repoRoot, env: { ...process.env, PYTHONPATH: path.join(repoRoot, "src") } });
        proc.stdout.on("data", (d) => { out += d.toString(); });
        proc.stderr.on("data", (d) => { err += d.toString(); });
        proc.on("close", (code) => {
          if (code !== 0) reject(new Error(err || `exit ${code}`));
          else resolve(out.trim());
        });
        proc.on("error", reject);
      });
      const data = JSON.parse(result);
      module._memosHealthCache = { data, ts: now };
      sendJson(res, { ...data, generatedAt: new Date().toISOString() });
    } catch (error) {
      sendJson(res, { available: false, installed: false, entry_count: 0, fallback: true, error: error.message, generatedAt: new Date().toISOString() });
    }
    return true;
  }

    // ── Three Doors game ────────────────────────────────────────────────
  if (url.pathname === "/api/dream/doors" && req.method === "POST") {
    try {
      const raw = await collectRequestBody(req);
      let body;
      try { body = JSON.parse(raw || "{}"); } catch { sendJson(res, { error: "invalid_json" }, 400); return true; }
      if (!body || typeof body !== "object" || Array.isArray(body)) body = {};
      const userId = String(body.userId || "web-anon").slice(0, 256);
      const action = String(body.action || "start");
      const choice = String(body.choice || "");

      const { spawn } = require("child_process");
      const enginePath = path.join(repoRoot, "src", "three_doors_engine.py");
      const py = process.platform === "win32" ? "python" : "python3";

      const script = `import sys,json; from three_doors_engine import ThreeDoorsEngine; req=json.loads(sys.stdin.read()); e=ThreeDoorsEngine(req['userId']); \\
result = e.to_api_response(); \\
if req['action'] in ['start','reset']: result = e.to_api_response(e.reset() if req['action']=='reset' else e.start_game()); \\
elif req['action']=='choose': s=e.choose_door(req['choice']); result = e.to_api_response(s) if s else {"error":"invalid_choice"}; \\
print(json.dumps(result))`;

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
        proc.stdin.write(JSON.stringify({ userId, action, choice }));
        proc.stdin.end();
      });

      const data = JSON.parse(result);
      sendJson(res, { ...data, generatedAt: new Date().toISOString() });
    } catch (error) { sendJson(res, { error: error.message, code: error.message === "request_body_too_large" ? 413 : 500 }, error.message === "request_body_too_large" ? 413 : 500); }
    return true;
  }

  if (url.pathname === "/api/dream/doors/image" && req.method === "POST") {
    try {
      const raw = await collectRequestBody(req);
      let body;
      try { body = JSON.parse(raw || "{}"); } catch { sendJson(res, { error: "invalid_json" }, 400); return true; }
      if (!body || typeof body !== "object" || Array.isArray(body)) body = {};
      const userId = String(body.userId || "web-anon").slice(0, 256);
      const rawDoorIdx = Number(body.doorIndex);
      const doorIdx = Number.isFinite(rawDoorIdx) && rawDoorIdx >= 0 ? Math.floor(rawDoorIdx) : 0;

      const sdUrl = process.env.STABLE_DIFFUSION_URL || process.env.SD_WEBUI_URL;
      if (!sdUrl) {
        const { spawn } = require("child_process");
        const py = process.platform === "win32" ? "python" : "python3";
        const script = `import sys,json; from three_doors_engine import ThreeDoorsEngine; req=json.loads(sys.stdin.read()); e=ThreeDoorsEngine(req['userId']); suggestions=e.image_suggestions_for_ai(); print(json.dumps(suggestions[req['doorIdx']] if req['doorIdx'] < len(suggestions) else {}))`;
        const result = await new Promise((resolve, reject) => {
          const proc = spawn(py, ["-c", script], { cwd: repoRoot, env: { ...process.env, PYTHONPATH: path.join(repoRoot, "src") } });
          let out = "";
          proc.stdout.on("data", (c) => (out += c));
          proc.on("close", (code) => resolve(out.trim()));
          proc.on("error", reject);
          proc.stdin.write(JSON.stringify({ userId, doorIdx }));
          proc.stdin.end();
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
      const script = `import sys,json; from three_doors_engine import ThreeDoorsEngine; req=json.loads(sys.stdin.read()); e=ThreeDoorsEngine(req['userId']); print(e.sd_prompt_for_state())`;
      const promptResult = await new Promise((resolve, reject) => {
        const proc = spawn(py, ["-c", script], { cwd: repoRoot, env: { ...process.env, PYTHONPATH: path.join(repoRoot, "src") } });
        let out = "";
        proc.stdout.on("data", (c) => (out += c));
        proc.on("close", (code) => resolve(out.trim()));
        proc.on("error", reject);
        proc.stdin.write(JSON.stringify({ userId }));
        proc.stdin.end();
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

  // ── TTS proxy ─────────────────────────────────────────────────────────
  if (url.pathname === "/api/dream/tts" && req.method === "POST") {
    try {
      const raw = await collectRequestBody(req);
      const body = JSON.parse(raw);
      const text = String(body.text || "").slice(0, 4000).trim();
      if (!text) { sendJson(res, { error: "text_required" }, 400); return true; }
      const voiceId = String(body.voice_id || process.env.ELEVENLABS_VOICE_ID || "Rachel").slice(0, 60);

      const proxyAudio = (hostname, path2, headers, postData) => {
        return new Promise((resolve) => {
          let resolved = false;
          const proxyReq = https.request({ hostname, path: path2, method: "POST", headers, timeout: 15000 }, (proxyRes) => {
            if (proxyRes.statusCode >= 200 && proxyRes.statusCode < 300) {
              res.writeHead(200, { "Content-Type": "audio/mpeg" });
              proxyRes.pipe(res);
              resolved = true;
              resolve(true);
            } else {
              // Drain the error response so the connection closes cleanly
              proxyRes.resume();
              if (!resolved) { resolved = true; resolve(false); }
            }
          });
          proxyReq.on("timeout", () => {
            proxyReq.destroy();
            if (!resolved) { resolved = true; resolve(false); }
          });
          proxyReq.on("error", () => {
            if (!resolved) { resolved = true; resolve(false); }
          });
          proxyReq.write(postData);
          proxyReq.end();
        });
      };

      // Try ElevenLabs first
      if (process.env.ELEVENLABS_API_KEY) {
        const postData = JSON.stringify({ text, model_id: "eleven_turbo_v2_5" });
        const ok = await proxyAudio(
          "api.elevenlabs.io",
          `/v1/text-to-speech/${encodeURIComponent(voiceId)}`,
          {
            "xi-api-key": process.env.ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
            "Content-Length": Buffer.byteLength(postData),
            "Accept": "audio/mpeg",
          },
          postData
        );
        if (ok) return true;
      }

      // Fall back to OpenAI TTS
      if (process.env.OPENAI_API_KEY) {
        const openaiVoice = String(body.voice_id || "nova").slice(0, 20);
        const postData = JSON.stringify({ model: "tts-1", input: text, voice: openaiVoice });
        const ok = await proxyAudio(
          "api.openai.com",
          "/v1/audio/speech",
          {
            "Authorization": `Bearer ${process.env.OPENAI_API_KEY}`,
            "Content-Type": "application/json",
            "Content-Length": Buffer.byteLength(postData),
          },
          postData
        );
        if (ok) return true;
      }

      sendJson(res, { fallback: "browser" });
    } catch (err) { sendJson(res, { error: err.message }, 500); }
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
      refreshProviderCache();
      sendJson(res, { ok: true });
    } catch (err) { sendJson(res, { error: err.message }, 500); }
    return true;
  }

  // ── Door choice persistence ─────────────────────────────────────────────
  if (url.pathname === "/api/dream/door-choice" && req.method === "POST") {
    try {
      const body = JSON.parse(await collectRequestBody(req));
      const { saveDoorChoice } = require("../lib/csf-memory");
      saveDoorChoice(body.choice || null, body.doors || []);
      sendJson(res, { ok: true });
    } catch (err) { sendJson(res, { error: err.message }, 500); }
    return true;
  }

  // ── Convergence Models 3 — live status from Ollama ────────────────────
  if (url.pathname === "/api/dream/lantern-models" && req.method === "GET") {
    const LANTERN_MODELS = [
      { id: "lantern-csf-dream",   role: "dream",       icon: "🌙", base: "mistral",        description: "Three Doors game · Elephant Oasis · dream narrative" },
      { id: "lantern-convergance", role: "convergence", icon: "◈",  base: "qwen2.5-coder",  description: "Convergence receipts · AAPF provenance · structured output" },
      { id: "lantern-pcsf",        role: "pcsf",        icon: "⌖",  base: "qwen2.5-coder",  description: "PCSF state manifests · system receipts · agent declarations" },
    ];
    const ollamaBase = process.env.OLLAMA_BASE_URL || "http://127.0.0.1:11434";
    try {
      const ollamaUrl = new URL(ollamaBase);
      const tagsRaw = await new Promise((resolve, reject) => {
        const r = require("http").request({
          hostname: ollamaUrl.hostname, port: ollamaUrl.port || 11434,
          path: "/api/tags", method: "GET",
        }, (upstream) => {
          let d = ""; upstream.on("data", c => d += c);
          upstream.on("end", () => { try { resolve(JSON.parse(d)); } catch { resolve({}); } });
          upstream.on("error", reject);
        });
        r.on("error", reject);
        r.setTimeout(4000, () => { r.destroy(); reject(new Error("timeout")); });
        r.end();
      });
      const pulledIds = (tagsRaw.models || []).map(m => String(m.name || "").replace(/:latest$/, "").toLowerCase());
      const pulledFull = tagsRaw.models || [];
      const models = LANTERN_MODELS.map(m => {
        const entry = pulledFull.find(p => String(p.name || "").toLowerCase().startsWith(m.id));
        return {
          ...m,
          loaded: pulledIds.some(id => id === m.id),
          size_gb: entry ? Math.round((entry.size / 1e9) * 100) / 100 : null,
          modified_at: entry ? entry.modified_at : null,
        };
      });
      const loaded = models.filter(m => m.loaded).length;
      sendJson(res, { convergence_models: models, loaded, total: LANTERN_MODELS.length, healthy: loaded === LANTERN_MODELS.length, ollama_base: ollamaBase });
    } catch (err) {
      sendJson(res, { convergence_models: LANTERN_MODELS.map(m => ({ ...m, loaded: false, size_gb: null })), loaded: 0, total: LANTERN_MODELS.length, healthy: false, error: err.message }, 200);
    }
    return true;
  }
};

// Lightweight AAPF provenance recorder (Node-side mirror of ConvergenceIO engine)
function recordChatProvenance({ actionId, agentId, providerId, inputSummary, outputSummary, latencyMs, status, errorMsg, metadata }) {
  const crypto = require("crypto");
  const record = {
    action_id: actionId,
    timestamp: new Date().toISOString(),
    actor: { agent_id: agentId, provider_id: providerId, model: "" },
    action_type: "chat",
    input_summary: inputSummary,
    output_summary: outputSummary,
    capability_claim_id: null,
    nap_profile_id: null,
    dcf_ref: null,
    tier: "wanderer",
    consent_state: "implicit",
    data_classifications: ["dream_content"],
    authority_check: "passed",
    boundary: "local",
    latency_ms: latencyMs,
    status,
    error_msg: errorMsg,
    metadata: metadata || {},
  };
  const payload = JSON.stringify(record, Object.keys(record).sort());
  record.integrity_hash = crypto.createHash("sha256").update(payload).digest("hex");
  const provenanceDir = require("path").join(require("path").resolve(__dirname, "..", "..", ".."), "data", "provenance");
  if (!require("fs").existsSync(provenanceDir)) require("fs").mkdirSync(provenanceDir, { recursive: true });
  const provenancePath = require("path").join(provenanceDir, "actions.jsonl");
  require("fs").appendFileSync(provenancePath, JSON.stringify(record) + "\n", "utf8");
}

// Shared helper — read all dream entries from monthly JSONL files
let _dreamEntriesCache = { entries: [], ts: 0 };
const DREAM_ENTRIES_TTL_MS = 3000;

function loadDreamEntries(fs, path, repoRoot, sorted = false) {
  const now = Date.now();
  if ((now - _dreamEntriesCache.ts) < DREAM_ENTRIES_TTL_MS) {
    return _dreamEntriesCache.entries;
  }
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
  _dreamEntriesCache = { entries, ts: now };
  return entries;
}
