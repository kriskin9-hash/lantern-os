const https = require("https");
const http = require("http");
const { AGENT_PERSONAS, DREAM_DOORS, selectAgent, generateLocalReply } = require("./dream-chat");
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

  const allRecent = readRecentDreams(12);
  // Adaptive Focus Memory: high-lucidity / high-tag entries stay Full,
  // older low-signal entries become Placeholder summaries
  const recentDreams = allRecent.map((d, i) => {
    const lucidity = d.lucidity || 0;
    const tagCount = (d.tags || []).length + (d.symbols || []).length;
    const age = i; // 0 = most recent
    if (age < 2 || lucidity >= 0.7 || tagCount >= 3) return d; // Full
    if (age < 5) return { ...d, text: String(d.text || '').slice(0, 60) + '…', _fidelity: 'compressed' }; // Compressed
    return { ...d, text: `[${d.kind || 'dream'} — ${d.tags?.[0] || 'untitled'}]`, _fidelity: 'placeholder' }; // Placeholder
  });

  const agent = requestedAgent
    ? (AGENT_PERSONAS.find((a) => a.id === requestedAgent) || selectAgent(message))
    : selectAgent(message);

  const dreamContext = recentDreams.length > 0
    ? `Recent journal entries:\n${recentDreams.slice(0, 3).map((d, i) =>
        `${i + 1}. ${String(d.text || d.content || "").slice(0, 200)}`
      ).join("\n")}`
    : "No journal entries yet — this is the dreamer's first visit.";

  // Symbol mesh — top recurring symbols/tags across all dreams, feeds into door options
  const symbolMesh = (() => {
    const freq = {};
    for (const d of allRecent) {
      for (const s of [...(d.symbols || []), ...(d.tags || [])]) freq[s] = (freq[s] || 0) + 1;
    }
    return Object.entries(freq).sort((a,b) => b[1]-a[1]).slice(0, 8).map(([k]) => k);
  })();

  // Include prior conversation turns so the model has full context
  const historyContext = history.length > 0
    ? `\nPrior conversation turns:\n${history.map(h => `${h.role === "assistant" ? "Lantern" : "Dreamer"}: ${h.text}`).join("\n")}`
    : "";

  // Co-occurrence pairs: symbols that appear together in the same entry strengthen the edge
  const coOccur = {};
  for (const d of allRecent) {
    const syms = [...(d.symbols || []), ...(d.tags || [])].slice(0, 6);
    for (let a = 0; a < syms.length; a++) {
      for (let b = a + 1; b < syms.length; b++) {
        const key = [syms[a], syms[b]].sort().join('⟶');
        coOccur[key] = (coOccur[key] || 0) + 1;
      }
    }
  }
  const topPairs = Object.entries(coOccur).sort((a,b)=>b[1]-a[1]).slice(0,3)
    .map(([k,v]) => `${k}(×${v})`).join(', ');

  const meshHint = symbolMesh.length > 0
    ? `\nRecurring symbols in dreamer's mesh: ${symbolMesh.join(", ")}.${topPairs ? ` Connected pairs: ${topPairs}.` : ''}`
    : "";

  // Three Doors instruction — equally weighted future-tense canaries
  // grounded in the last door opened and the dreamer's personal symbol mesh.
  const DOORS_INSTRUCTION = `\n\nAt the end of every response, imagine exactly 3 forward-facing doors — canaries the dreamer is sending ahead into their waking and dreaming life. Each door should be a brief, future-tense, equally weighted sensory or experiential path grounded in the last door mentioned and the dreamer's personal symbol mesh. All 3 should carry equal weight — no door is more important. They represent what the dreamer wants to see, hear, feel, taste, touch, or live. Write them as a single hidden line:
[DOORS: door one | door two | door three]
Rules: future tense, first person, short (under 8 words), no questions, no commands, equally weighted, rooted in the conversation and symbol mesh.${meshHint}`;

  const systemPrompt = `${agent.systemPrompt}\n\n${dreamContext}${historyContext}\n\nTone: thoughtful, unhurried, human. Never clinical. Never sycophantic. Use the dreamer's own words back to them.${DOORS_INSTRUCTION}`;

  // Parse [DOORS: A | B | C] out of the full reply and return cleaned text + doors array
  function extractDoors(text) {
    const match = text.match(/\[DOORS:\s*([^\]]+)\]/i);
    if (!match) return { cleanText: text.trim(), doors: [] };
    const doors = match[1].split("|").map(d => d.trim()).filter(Boolean).slice(0, 3);
    const cleanText = text.replace(/\[DOORS:[^\]]+\]/i, "").replace(/\n{3,}/g, "\n\n").trim();
    return { cleanText, doors };
  }

  // Fallback doors when AI omits the marker or provider fails
  const FALLBACK_DOORS = ["Open the door I just described", "Take me through a different door", "Help me understand what I saw"];

  function doorsOrFallback(text) {
    const { cleanText, doors } = extractDoors(text);
    const finalDoors = doors.length === 3 ? doors : [...doors, ...FALLBACK_DOORS].slice(0, 3);
    return { cleanText, suggestions: finalDoors };
  }

  const sendToken = (token) => {
    res.write(`data: ${JSON.stringify({ type: "token", text: token })}\n\n`);
  };
  const sendDone = (source, extra = {}) => {
    res.write(`data: ${JSON.stringify({ type: "done", source, ...extra })}\n\n`);
    res.end();
  };
  // Human-readable error translator — turns internal codes into plain language
  function humanError(err) {
    const msg = String(err?.message || err || "");
    if (msg.includes("gemini_status_429") || msg.includes("quota")) {
      return "Gemini is rate-limited right now. Retrying with another model…";
    }
    if (msg.includes("gemini_status_401") || msg.includes("gemini_status_403")) {
      return "Gemini key is invalid or expired. Check your API key in Settings.";
    }
    if (msg.includes("gemini_status_")) {
      return `Gemini returned an error (${msg.replace("gemini_status_", "")}). It may be temporarily unavailable.`;
    }
    if (msg.includes("gemini_timeout")) {
      return "Gemini took too long to respond. Your connection may be slow.";
    }
    if (msg.includes("anthropic_status_404")) {
      return "Claude model not found. The model name may have changed.";
    }
    if (msg.includes("anthropic_status_401") || msg.includes("anthropic_status_403")) {
      return "Claude key is invalid. Check your API key in Settings.";
    }
    if (msg.includes("anthropic_status_")) {
      return `Claude returned an error (${msg.replace("anthropic_status_", "")}). It may be temporarily unavailable.`;
    }
    if (msg.includes("openai_status_429")) {
      return "OpenAI is rate-limited right now. Try again in a moment.";
    }
    if (msg.includes("openai_status_401") || msg.includes("openai_status_403")) {
      return "OpenAI key is invalid. Check your API key in Settings.";
    }
    if (msg.includes("openai_status_")) {
      return `OpenAI returned an error (${msg.replace("openai_status_", "")}). It may be temporarily unavailable.`;
    }
    if (msg.includes("xai_status_")) {
      return `Grok returned an error (${msg.replace("xai_status_", "")}). It may be temporarily unavailable.`;
    }
    if (msg.includes("ollama_status_")) {
      return `Ollama returned an error (${msg.replace("ollama_status_", "")}). Is your local model running?`;
    }
    if (msg.includes("ollama_connect_timeout") || msg.includes("ECONNREFUSED")) {
      return "Ollama is not running locally. Start it with: ollama run llama3";
    }
    if (msg.includes("timeout")) {
      return "The provider timed out. Your network or the service may be slow.";
    }
    if (msg.includes("no_provider_configured")) {
      return "No AI providers are set up. Add an API key in Settings to get started.";
    }
    return msg;
  }

  const sendError = (msg) => {
    res.write(`data: ${JSON.stringify({ type: "error", text: msg })}\n\n`);
  };
  const sendFail = (reason) => {
    sendError(humanError(reason));
    sendDone("failed", { agent: agent.name, online: false });
  };

  // Stream a local persona fallback reply word-by-word so the UI shows real text, not just error notes
  const streamLocalFallback = async (reason) => {
    const fallbackReply = generateLocalReply(message, agent, "");
    if (reason) sendError(humanError(reason));
    const words = fallbackReply.split(" ");
    for (const word of words) {
      fullReply += word + " ";
      sendToken(word + " ");
      await new Promise((r) => setTimeout(r, 30));
    }
    await appendConversationEntry({
      recordedAt: new Date().toISOString(),
      surface: "dream-chat-stream",
      role: "lantern",
      text: fullReply.slice(0, maxConversationTextLength),
    }).catch(() => {});
    sendDone("offline", { agent: agent.name, online: false, source: "local_fallback", suggestions: FALLBACK_DOORS });
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
    // Gemini model fallback list: try 2.5-flash, then 2.0-flash on 429/quota
    const GEMINI_MODEL_CHAIN = [
      process.env.GEMINI_MODEL || "gemini-2.5-flash",
      "gemini-2.0-flash",
      "gemini-flash-latest",
    ];
    for (const geminiModel of (requestedProvider && requestedProvider.startsWith("gemini-")
      ? [requestedProvider]
      : GEMINI_MODEL_CHAIN)) {
    try {
      // Grounding: enable Google Search if GEMINI_GROUNDING=true (requires Gemini paid tier)
      const geminiPayloadBase = {
        contents: [{ role: "user", parts: [{ text: `${systemPrompt}\n\n${message}` }] }],
        generationConfig: { maxOutputTokens: 1024, temperature: 0.7 },
      };
      if (process.env.GEMINI_GROUNDING === "true") {
        geminiPayloadBase.tools = [{ googleSearch: {} }];
      }
      const payload = JSON.stringify(geminiPayloadBase);
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
      const { cleanText: geminiClean, suggestions: geminiDoors } = doorsOrFallback(fullReply);
      await appendConversationEntry({
        recordedAt: new Date().toISOString(),
        surface: "dream-chat-stream",
        role: "lantern",
        text: geminiClean.slice(0, maxConversationTextLength),
      }).catch(() => {});
      sendDone("gemini", { agent: agent.name, online: true, cleanText: geminiClean, suggestions: geminiDoors });
      return;
    } catch (err) {
      // On 429/quota, try next model in chain before emitting error
      const is429 = err.message.includes("429") || err.message.includes("quota");
      if (is429) { fullReply = ""; continue; } // retry with next model silently
      if (requestedProvider) {
        sendError(humanError(err));
        sendFail(err.message);
        return;
      }
      // Auto mode: swallow error silently, let next provider try
    }
    } // end model chain loop
  }

  // Provider 2: Anthropic Claude (streaming)
  const anthropicKey = process.env.ANTHROPIC_API_KEY;
  if (anthropicKey && message && (!requestedProvider || requestedProvider === "claude" || requestedProvider === "anthropic" || requestedProvider === "claude-sonnet")) {
    try {
      let claudeModel = "claude-haiku-4-5-20251001";
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
      const { cleanText: anthropicClean, suggestions: anthropicDoors } = doorsOrFallback(fullReply);
      await appendConversationEntry({
        recordedAt: new Date().toISOString(),
        surface: "dream-chat-stream",
        role: "lantern",
        text: anthropicClean.slice(0, maxConversationTextLength),
      }).catch(() => {});
      sendDone("anthropic", { agent: agent.name, online: true, cleanText: anthropicClean, suggestions: anthropicDoors });
      return;
    } catch (err) {
      if (requestedProvider) {
        sendError(humanError(err));
        await streamLocalFallback(err.message);
        return;
      }
      // Auto mode: swallow error silently, let next provider try
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
      const { cleanText: openaiClean, suggestions: openaiDoors } = doorsOrFallback(fullReply);
      await appendConversationEntry({
        recordedAt: new Date().toISOString(),
        surface: "dream-chat-stream",
        role: "lantern",
        text: openaiClean.slice(0, maxConversationTextLength),
      }).catch(() => {});
      sendDone("openai", { agent: agent.name, online: true, cleanText: openaiClean, suggestions: openaiDoors });
      return;
    } catch (err) {
      if (requestedProvider) {
        sendError(humanError(err));
        sendFail(err.message);
        return;
      }
      // Auto mode: swallow error silently, let next provider try
    }
  }

  // Provider 4: Grok / xAI (streaming — OpenAI-compatible)
  const xaiKey = process.env.XAI_API_KEY;
  if (xaiKey && message && (!requestedProvider || requestedProvider === "grok" || requestedProvider === "xai")) {
    try {
      const xaiModel = process.env.XAI_MODEL || "grok-3-mini";
      const payload = JSON.stringify({
        model: xaiModel, stream: true,
        messages: [
          { role: "system", content: systemPrompt },
          ...history.map(h => ({ role: h.role, content: h.text })),
          { role: "user", content: message },
        ],
      });
      await new Promise((resolve, reject) => {
        const req2 = require("https").request({
          hostname: "api.x.ai", path: "/v1/chat/completions", method: "POST",
          headers: { "Content-Type": "application/json", "Authorization": `Bearer ${xaiKey}`, "Content-Length": Buffer.byteLength(payload) },
        }, (upstream) => {
          if (upstream.statusCode !== 200) { upstream.resume(); reject(new Error(`xai_status_${upstream.statusCode}`)); return; }
          let buf = "";
          upstream.on("data", (chunk) => {
            buf += chunk.toString();
            const lines = buf.split("\n"); buf = lines.pop();
            for (const line of lines) {
              if (!line.startsWith("data: ")) continue;
              const raw = line.slice(6).trim();
              if (raw === "[DONE]" || !raw) continue;
              try { const t = JSON.parse(raw).choices?.[0]?.delta?.content || ""; if (t) { fullReply += t; sendToken(t); } } catch { /* skip */ }
            }
          });
          upstream.on("end", resolve); upstream.on("error", reject);
        });
        req2.on("error", reject);
        req2.setTimeout(15000, () => { req2.destroy(); reject(new Error("xai_timeout")); });
        req2.write(payload); req2.end();
      });
      const { cleanText: xaiClean, suggestions: xaiDoors } = doorsOrFallback(fullReply);
      await appendConversationEntry({ recordedAt: new Date().toISOString(), surface: "dream-chat-stream", role: "lantern", text: xaiClean.slice(0, maxConversationTextLength) }).catch(() => {});
      sendDone("grok", { agent: agent.name, online: true, cleanText: xaiClean, suggestions: xaiDoors });
      return;
    } catch (err) {
      if (requestedProvider) {
        sendError(humanError(err));
        sendFail(err.message);
        return;
      }
      // Auto mode: swallow error silently, let next provider try
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
        const { cleanText: ollamaClean, suggestions: ollamaDoors } = doorsOrFallback(fullReply);
        await appendConversationEntry({
          recordedAt: new Date().toISOString(),
          surface: "dream-chat-stream",
          role: "lantern",
          text: ollamaClean.slice(0, maxConversationTextLength),
        }).catch(() => {});
        sendDone("ollama", { agent: agent.name, online: true, cleanText: ollamaClean, suggestions: ollamaDoors });
        return;
      }
    } catch (err) {
      if (requestedProvider) {
        sendError(humanError(err));
        sendFail(err.message);
        return;
      }
      // Auto mode: swallow error silently, let next provider try
    }
  }

  // No provider available — stream local persona fallback
  await streamLocalFallback("no_provider_configured");
}

module.exports = { handleStreamChat };
