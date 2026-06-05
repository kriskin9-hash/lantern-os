// Dreamer notebook and agent list
module.exports = async function dreamerRoutes(req, res, url, deps) {
  const { sendJson, collectRequestBody, path, repoRoot,
    normalizeDreamerUser, dreamerNotebookPath, appendDreamerEntry,
    readDreamerNotebook, readRecentDreams, dreamChatReply, AGENT_PERSONAS } = deps;

  if (url.pathname === "/api/dreamer" && req.method === "GET") {
    const user = normalizeDreamerUser(url.searchParams.get("user") || "courtney");
    const entries = readDreamerNotebook(user);
    sendJson(res, { user, entries, path: path.relative(repoRoot, dreamerNotebookPath(user)) });
    return true;
  }
  if (url.pathname === "/api/dreamer" && req.method === "POST") {
    try {
      const raw = await collectRequestBody(req);
      const body = JSON.parse(raw);
      const user = normalizeDreamerUser(body.user || "courtney");
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
};
