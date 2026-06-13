// Dreamer notebook and agent list
module.exports = async function dreamerRoutes(req, res, url, deps) {
  const { sendJson, collectRequestBody, path, repoRoot,
    normalizeDreamerUser, dreamerNotebookPath, appendDreamerEntry,
    readDreamerNotebook, readRecentDreams, dreamChatReply, AGENT_PERSONAS } = deps;

  if (url.pathname === "/api/dreamer" && req.method === "GET") {
    const user = normalizeDreamerUser(url.searchParams.get("user") || "dreamer");
    const entries = readDreamerNotebook(user);
    sendJson(res, { user, entries, path: path.relative(repoRoot, dreamerNotebookPath(user)) });
    return true;
  }
  if (url.pathname === "/api/dreamer" && req.method === "POST") {
    try {
      const raw = await collectRequestBody(req);
      const body = JSON.parse(raw);
      const user = normalizeDreamerUser(body.user || "dreamer");
      const record = await appendDreamerEntry(user, body);
      sendJson(res, { saved: true, record });
    } catch (error) {
      sendJson(res, { error: error.message }, 400);
    }
    return true;
  }
  if (url.pathname === "/api/dreamer/chat" && req.method === "POST") {
    try {
      const raw = await collectRequestBody(req);
      const body = JSON.parse(raw);
      const user = normalizeDreamerUser(body.user || "orion");
      const kind = String(body.kind || "dream").slice(0, 40);
      const text = String(body.text || "").slice(0, 4000);
      const record = await appendDreamerEntry(user, { kind, text, name: body.name, mood: body.mood, tags: body.tags });
      const recentDreams = readRecentDreams(5);
      const chatResult = await dreamChatReply(`[${kind}] ${text}`, recentDreams, body.agent || "", body.provider || "");
      if (!chatResult.reply) {
        sendJson(res, { saved: true, record, error: chatResult.error || "no_provider_configured", agent: chatResult.agent, online: false, help: chatResult.help || "", suggestions: chatResult.suggestions || [] }, 503);
        return true;
      }
      sendJson(res, {
        saved: true, record,
        reply: chatResult.reply, agent: chatResult.agent,
        source: chatResult.online ? "llm" : "offline",
        suggestions: chatResult.suggestions,
      });
    } catch (error) {
      sendJson(res, { error: error.message }, 400);
    }
    return true;
  }
  if (url.pathname === "/api/agents" && req.method === "GET") {
    sendJson(res, {
      agents: AGENT_PERSONAS.map((a) => ({ id: a.id, name: a.name, symbol: a.symbol })),
      default: AGENT_PERSONAS[0].id,
    });
    return true;
  }
  if (url.pathname === "/api/agents/slots" && req.method === "GET") {
    try {
      const fs = require("fs");
      const claudePath = path.join(repoRoot, ".claude", "agent-slots.json");
      const manifestPath = path.join(repoRoot, "manifests", "dream-journal-v1-agent-slots.json");
      let slotsPath = claudePath;
      if (!fs.existsSync(claudePath)) {
        if (!fs.existsSync(manifestPath)) {
          sendJson(res, { error: "agent-slots.json not found" }, 404);
          return true;
        }
        slotsPath = manifestPath;
      }
      if (!fs.existsSync(slotsPath)) {
        sendJson(res, { error: "agent-slots.json not found" }, 404);
        return true;
      }
      const raw = require("fs").readFileSync(slotsPath, "utf8");
      const data = JSON.parse(raw);
      sendJson(res, {
        slots: data.slots.map((s) => ({
          id: s.id,
          agent: s.agent,
          provider: s.provider,
          model: s.model,
          status: s.status,
          responsibilities: s.responsibilities,
          fallback: s.quotaTracking?.fallbackAgent || null,
        })),
        routing: data.routing?.dailyBootOrder || [],
        weights: data.routing?.weights || {},
      });
    } catch (error) {
      sendJson(res, { error: error.message }, 500);
    }
    return true;
  }
  if (url.pathname === "/api/dreamer/upload" && req.method === "POST") {
    try {
      const fs = require("fs");
      const busboy = require("busboy");
      const user = normalizeDreamerUser(url.searchParams.get("user") || "dreamer");

      const videosDir = path.join(repoRoot, "data", "dreamer", "videos");
      if (!fs.existsSync(videosDir)) {
        fs.mkdirSync(videosDir, { recursive: true });
      }

      const bb = busboy({ headers: req.headers });
      let fileInfo = null;
      let fields = {};

      bb.on("file", (fieldname, file, info) => {
        const timestamp = Date.now();
        const filename = `${timestamp}-${info.filename}`;
        const filepath = path.join(videosDir, filename);
        const writeStream = fs.createWriteStream(filepath);

        file.pipe(writeStream);

        writeStream.on("finish", () => {
          const stats = fs.statSync(filepath);
          fileInfo = {
            filename: info.filename,
            savedAs: filename,
            mimeType: info.mimeType,
            size: stats.size,
            path: filepath
          };
        });

        writeStream.on("error", (err) => {
          console.error("Upload error:", err);
          if (fs.existsSync(filepath)) fs.unlinkSync(filepath);
        });
      });

      bb.on("field", (fieldname, value) => {
        fields[fieldname] = String(value).slice(0, 1000);
      });

      bb.on("close", async () => {
        try {
          const entry = {
            kind: fields.type || "video",
            title: fields.title || "Untitled",
            project: fields.project || "",
            description: fields.description || "",
            tags: fields.tags ? fields.tags.split(",").map(t => t.trim()).filter(Boolean) : [],
            private: true,
            file: fileInfo || null
          };

          const record = await appendDreamerEntry(user, entry);
          sendJson(res, { saved: true, record, file: fileInfo });
        } catch (error) {
          sendJson(res, { error: error.message }, 400);
        }
      });

      bb.on("error", (error) => {
        console.error("Busboy error:", error);
        sendJson(res, { error: error.message }, 400);
      });

      req.pipe(bb);
    } catch (error) {
      console.error("Upload route error:", error);
      sendJson(res, { error: error.message }, 500);
    }
    return true;
  }
};
