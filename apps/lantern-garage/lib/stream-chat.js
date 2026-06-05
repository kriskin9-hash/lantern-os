const https = require("https");
const http = require("http");
const { AGENT_PERSONAS, DREAM_DOORS, selectAgent } = require("./dream-chat");
const { readRecentDreams, normalizeDreamerUser } = require("./dreamer-store");
const { appendConversationEntry } = require("./conversation-store");

const maxConversationTextLength = 4000;

async function handleStreamChat(req, url, res) {
  let message = "";
  let user = "dreamer";
  let requestedAgent = "";
  let requestedProvider = "";
  let history = []; // [{role:"user"|"assistant", text:"..."}]
  if (req.method === "GET") {
    message = String(url.searchParams.get("message") || "").slice(0, 4000).trim();
    user = normalizeDreamerUser(url.searchParams.get("user") || "dreamer");
    requestedAgent = String(url.searchParams.get("agent") || "").trim();
    requestedProvider = String(url.searchParams.get("provider") || "").trim().toLowerCase();
  } else {
    try {
      const { collectRequestBody } = require("./http-utils");
      const rawBody = await collectRequestBody(req);
      const body = JSON.parse(rawBody || "{}");
      message = String(body.message || "").slice(0, 4000).trim();
      user = normalizeDreamerUser(body.user || "dreamer");
      requestedAgent = String(body.agent || "").trim();
      requestedProvider = String(body.provider || "").trim().toLowerCase();
      // Conversation history — last N turns from the client [{role, text}]
      if (Array.isArray(body.history)) {
        history = body.history
          .filter(h => h && typeof h.role === "string" && typeof h.text === "string")
          .slice(-6) // max 3 exchanges = 6 turns
          .map(h => ({ role: h.role === "assistant" ? "assistant" : "user", text: String(h.text).slice(0, 1000) }));
      }
    } catch { /* message stays empty */ }
  }

  res.writeHead(200, {
    "Content-Type": "text/event-stream; charset=utf-8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Access-Control-Allow-Origin": "*",
    "X-Accel-Buffering": "no",
  });

  const recentDreams = readRecentDreams(8);

  const agent = requestedAgent
    ? (AGENT_PERSONAS.find((a) => a.id === requestedAgent) || selectAgent(message))
    : selectAgent(message);

  const dreamContext = recentDreams.length > 0
    ? `Recent journal entries:\n${recentDreams.slice(0, 3).map((d, i) =>
        `${i + 1}. ${String(d.text || d.content || "").slice(0, 200)}`
      ).join("\n")}`
    : "No journal entries yet — this is the dreamer's first visit.";

  // Include prior conversation turns so the model has full context
  const historyContext = history.length > 0
    ? `\nPrior conversation turns:\n${history.map(h => `${h.role === "assistant" ? "Lantern" : "Dreamer"}: ${h.text}`).join("\n")}`
    : "";

  const systemPrompt = `${agent.systemPrompt}\n\n${dreamContext}${historyContext}\n\nTone: thoughtful, unhurried, human. Never clinical. Never sycophantic. Use the dreamer's own words back to them. End responses with one question or one invitation to record.`;

  // Build contextual suggestions from real dream memory (tags, emotions, symbols)
  function buildSuggestions() {
    const tagFreq = {}, emotionFreq = {}, symbolFreq = {};
    for (const d of recentDreams) {
      for (const t of (d.tags || [])) tagFreq[t] = (tagFreq[t] || 0) + 1;
      for (const e of (d.emotions || [])) emotionFreq[e] = (emotionFreq[e] || 0) + 1;
      for (const s of (d.symbols || [])) symbolFreq[s] = (symbolFreq[s] || 0) + 1;
    }
    const top = (freq) => Object.entries(freq).sort((a,b) => b[1]-a[1]).slice(0,2).map(([k]) => k);
    const topTags = top(tagFreq);
    const topEmotions = top(emotionFreq);
    const topSymbols = top(symbolFreq);
    const chips = [];
    if (topTags[0]) chips.push(`Tell me more about "${topTags[0]}"`);
    if (topEmotions[0]) chips.push(`I often feel ${topEmotions[0]} in my dreams`);
    if (topSymbols[0]) chips.push(`The symbol "${topSymbols[0]}" keeps appearing`);
    if (chips.length < 3 && topTags[1]) chips.push(`What does "${topTags[1]}" mean?`);
    if (chips.length < 3 && topEmotions[1]) chips.push(`Why do I feel ${topEmotions[1]}?`);
    // Fallback to generic prompts if not enough data
    const fallbacks = ["I had a vivid dream last night", "I want to log a recurring dream", "Help me understand a symbol"];
    while (chips.length < 3) chips.push(fallbacks[chips.length]);
    return chips.slice(0, 3);
  }

  const sendToken = (token) => {
    res.write(`data: ${JSON.stringify({ type: "token", text: token })}\n\n`);
  };
  const sendDone = (source, extra = {}) => {
    res.write(`data: ${JSON.stringify({ type: "done", source, ...extra })}\n\n`);
    res.end();
  };
  const sendError = (msg) => {
    res.write(`data: ${JSON.stringify({ type: "error", text: msg })}\n\n`);
  };
  const sendFail = (reason) => {
    sendError(`no_provider: ${reason}`);
    sendDone("failed", { agent: agent.name, online: false });
  };
  const sendLocalFallback = (reason) => {
    sendError(`local_fallback: ${reason}`);
    sendDone("offline", { agent: agent.name, online: false });
  };

  await appendConversationEntry({
    recordedAt: new Date().toISOString(),
    surface: "dream-chat-stream",
    role: "operator",
    text: message.slice(0, maxConversationTextLength),
  }).catch(() => {});

  let fullReply = "";

  // Provider 1: Gemini (streaming) — checked first for Auto mode
  const geminiKey = process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY;
  if (geminiKey && message && (!requestedProvider || requestedProvider === "gemini" || requestedProvider === "google" || requestedProvider.startsWith("gemini-"))) {
    try {
      const geminiModel = requestedProvider && requestedProvider.startsWith("gemini-")
        ? requestedProvider
        : (process.env.GEMINI_MODEL || "gemini-2.5-flash");
      const payload = JSON.stringify({
        contents: [{ role: "user", parts: [{ text: `${systemPrompt}\n\n${message}` }] }],
        generationConfig: { maxOutputTokens: 1024, temperature: 0.7 },
      });
      await new Promise((resolve, reject) => {
        const req2 = https.request({
          hostname: "generativelanguage.googleapis.com",
          path: `/v1beta/models/${geminiModel}:streamGenerateContent?alt=sse&key=${geminiKey}`,
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Content-Length": Buffer.byteLength(payload),
          },
        }, (upstream) => {
          if (upstream.statusCode !== 200) {
            upstream.resume();
            reject(new Error(`gemini_status_${upstream.statusCode}`));
            return;
          }
          let buf = "";
          upstream.on("data", (chunk) => {
            buf += chunk.toString();
            const lines = buf.split("\n");
            buf = lines.pop();
            for (const line of lines) {
              if (!line.startsWith("data: ")) continue;
              const raw = line.slice(6).trim();
              if (!raw) continue;
              try {
                const evt = JSON.parse(raw);
                const parts = evt.candidates?.[0]?.content?.parts || [];
                for (const p of parts) {
                  const token = p.text || "";
                  if (token) { fullReply += token; sendToken(token); }
                }
              } catch { /* skip malformed */ }
            }
          });
          upstream.on("end", () => resolve());
          upstream.on("error", reject);
        });
        req2.on("error", reject);
        req2.setTimeout(15000, () => { req2.destroy(); reject(new Error("gemini_timeout")); });
        req2.write(payload);
        req2.end();
      });
      await appendConversationEntry({
        recordedAt: new Date().toISOString(),
        surface: "dream-chat-stream",
        role: "lantern",
        text: fullReply.slice(0, maxConversationTextLength),
      }).catch(() => {});
      sendDone("gemini", { agent: agent.name, online: true, suggestions: buildSuggestions() });
      return;
    } catch (err) {
      sendError(`gemini_unavailable: ${err.message}`);
      if (requestedProvider && requestedProvider !== "" && requestedProvider !== "gemini" && !requestedProvider.startsWith("gemini-")) {
        await sendLocalFallback(err.message);
        return;
      }
    }
  }

  // Provider 2: Anthropic Claude (streaming)
  const anthropicKey = process.env.ANTHROPIC_API_KEY;
  if (anthropicKey && message && (!requestedProvider || requestedProvider === "claude" || requestedProvider === "anthropic" || requestedProvider === "claude-sonnet")) {
    try {
      let claudeModel = "claude-3-5-haiku-20241022";
      if (requestedProvider === "claude-sonnet") {
        claudeModel = process.env.ANTHROPIC_SONNET_MODEL || "claude-3-5-sonnet-20241022";
      } else {
        claudeModel = process.env.ANTHROPIC_MODEL || claudeModel;
      }
      const payload = JSON.stringify({
        model: claudeModel,
        max_tokens: 1024,
        stream: true,
        system: systemPrompt,
        messages: [...history.map(h => ({ role: h.role, content: h.text })), { role: "user", content: message }],
      });
      await new Promise((resolve, reject) => {
        const req2 = https.request({
          hostname: "api.anthropic.com",
          path: "/v1/messages",
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "x-api-key": anthropicKey,
            "anthropic-version": "2023-06-01",
            "Content-Length": Buffer.byteLength(payload),
          },
        }, (upstream) => {
          if (upstream.statusCode !== 200) {
            upstream.resume();
            reject(new Error(`anthropic_status_${upstream.statusCode}`));
            return;
          }
          let buf = "";
          upstream.on("data", (chunk) => {
            buf += chunk.toString();
            const lines = buf.split("\n");
            buf = lines.pop();
            for (const line of lines) {
              if (!line.startsWith("data:")) continue;
              const raw = line.slice(5).trim();
              if (raw === "[DONE]" || raw === "") continue;
              try {
                const evt = JSON.parse(raw);
                if (evt.type === "content_block_delta" && evt.delta?.text) {
                  fullReply += evt.delta.text;
                  sendToken(evt.delta.text);
                }
              } catch { /* skip malformed */ }
            }
          });
          upstream.on("end", () => resolve());
          upstream.on("error", reject);
        });
        req2.on("error", reject);
        req2.write(payload);
        req2.end();
      });
      await appendConversationEntry({
        recordedAt: new Date().toISOString(),
        surface: "dream-chat-stream",
        role: "lantern",
        text: fullReply.slice(0, maxConversationTextLength),
      }).catch(() => {});
      sendDone("anthropic", { agent: agent.name, online: true, suggestions: buildSuggestions() });
      return;
    } catch (err) {
      sendError(`anthropic_unavailable: ${err.message}`);
      if (requestedProvider) { await sendLocalFallback(err.message); return; }

    }
  }

  // Provider 3: OpenAI (streaming)
  const openaiKey = process.env.OPENAI_API_KEY;
  if (openaiKey && message && (!requestedProvider || requestedProvider === "openai" || requestedProvider === "gpt")) {
    try {
      const payload = JSON.stringify({
        model: process.env.OPENAI_MODEL || "gpt-4o-mini",
        stream: true,
        messages: [
          { role: "system", content: systemPrompt },
          ...history.map(h => ({ role: h.role, content: h.text })),
          { role: "user", content: message },
        ],
      });

      await new Promise((resolve, reject) => {
        const req2 = https.request({
          hostname: "api.openai.com",
          path: "/v1/chat/completions",
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${openaiKey}`,
            "Content-Length": Buffer.byteLength(payload),
          },
        }, (upstream) => {
          if (upstream.statusCode !== 200) {
            upstream.resume();
            reject(new Error(`openai_status_${upstream.statusCode}`));
            return;
          }
          let buf = "";
          upstream.on("data", (chunk) => {
            buf += chunk.toString();
            const lines = buf.split("\n");
            buf = lines.pop();
            for (const line of lines) {
              if (!line.startsWith("data: ")) continue;
              const raw = line.slice(6).trim();
              if (raw === "[DONE]" || raw === "") continue;
              try {
                const evt = JSON.parse(raw);
                const token = evt.choices?.[0]?.delta?.content || "";
                if (token) { fullReply += token; sendToken(token); }
              } catch { /* skip malformed */ }
            }
          });
          upstream.on("end", () => resolve());
          upstream.on("error", reject);
        });
        req2.on("error", reject);
        req2.setTimeout(15000, () => { req2.destroy(); reject(new Error("openai_timeout")); });
        req2.write(payload);
        req2.end();
      });
      await appendConversationEntry({
        recordedAt: new Date().toISOString(),
        surface: "dream-chat-stream",
        role: "lantern",
        text: fullReply.slice(0, maxConversationTextLength),
      }).catch(() => {});
      sendDone("openai", { agent: agent.name, online: true, suggestions: buildSuggestions() });
      return;
    } catch (err) {
if (requestedProvider) { sendFail(err.message); return; }

      sendError(`openai_unavailable: ${err.message}`);
      if (requestedProvider) { await sendLocalFallback(err.message); return; }

    }
  }

  // Provider 5: Ollama (streaming)
  const ollamaBase = process.env.OLLAMA_BASE_URL || "http://127.0.0.1:11434";
  const ollamaModel = process.env.OLLAMA_MODEL || "llama3";
  if (message && (!requestedProvider || requestedProvider === "ollama" || requestedProvider === "local")) {
    try {
      const payload = JSON.stringify({
        model: ollamaModel,
        stream: true,
        messages: [
          { role: "system", content: systemPrompt },
          ...history.map(h => ({ role: h.role, content: h.text })),
          { role: "user", content: message },
        ],
      });
      const ollamaUrl = new URL(ollamaBase);
      const ollamaOpts = {
        hostname: ollamaUrl.hostname,
        port: ollamaUrl.port || 11434,
        path: "/api/chat",
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(payload),
        },
      };
      let ollamaOk = false;
      await new Promise((resolve, reject) => {
        const req2 = http.request(ollamaOpts, (upstream) => {
          if (upstream.statusCode !== 200) {
            upstream.resume();
            reject(new Error(`ollama_status_${upstream.statusCode}`));
            return;
          }
          ollamaOk = true;
          let buf = "";
          upstream.on("data", (chunk) => {
            buf += chunk.toString();
            const lines = buf.split("\n");
            buf = lines.pop();
            for (const line of lines) {
              if (!line.trim()) continue;
              try {
                const evt = JSON.parse(line);
                const token = evt.message?.content || evt.response || "";
                if (token) { fullReply += token; sendToken(token); }
              } catch { /* skip */ }
            }
          });
          upstream.on("end", () => resolve());
          upstream.on("error", reject);
        });
        req2.on("error", reject);
        req2.setTimeout(5000, () => { req2.destroy(); reject(new Error("ollama_connect_timeout")); });
        req2.write(payload);
        req2.end();
      });
      if (ollamaOk) {
        await appendConversationEntry({
          recordedAt: new Date().toISOString(),
          surface: "dream-chat-stream",
          role: "lantern",
          text: fullReply.slice(0, maxConversationTextLength),
        }).catch(() => {});
        sendDone("ollama", { agent: agent.name, online: true, suggestions: buildSuggestions() });
        return;
      }
    } catch (err) {
      sendError(`ollama_unavailable: ${err.message}`);
      if (requestedProvider) { sendFail(err.message); return; }
    }
  }

  // No provider available — local persona fallback
  sendFail("no_provider_configured");
}

module.exports = { handleStreamChat };
