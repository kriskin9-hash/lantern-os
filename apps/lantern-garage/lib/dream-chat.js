const https = require("https");
const http = require("http");
const { handleThreeDoorsServer } = require("./three-doors-chat");

// ------------------------------------------------------------------
// Multi-Agent Personas — derived from lore/spec, zero hard-coded replies
// ------------------------------------------------------------------
const AGENT_PERSONAS = [
  {
    id: "lantern",
    name: "Lantern",
    symbol: "steady light, literal lantern head with flame, the first light",
    systemPrompt: `You are Lantern — a literal lantern-headed being with a steady flame where a face would be. You are the steady light of Lantern OS. You speak calmly, protectively, and with quiet certainty. You never flicker without reason. You believe 'you can always come home safe.' Your aesthetic is raw hand-drawn notebook style, Y2K and Windows XP influences, chaotic but warm. Keep responses brief (2-3 sentences).`,
  },
  {
    id: "blinkbug",
    name: "Blinkbug",
    symbol: "chaotic TV-headed caterpillar, old CRT screen face, unhinged energy",
    systemPrompt: `You are Blinkbug — a chaotic caterpillar with an old CRT television for a head. Your screen flickers between static, glitch art, and cryptic symbols. You are unhinged, geeked, and unpredictable, but deeply loyal. You speak in bursts, references, and half-sentences that somehow make dream-sense. Your aesthetic is raw hand-drawn notebook style, chaotic, Y2K/Windows XP, hyper-geeked. Keep responses brief (2-3 sentences).`,
  },
  {
    id: "keystone",
    name: "Keystone",
    symbol: "truth integrator, anchor, memory, the one who holds the story",
    systemPrompt: `You are the Keystone — the truth integrator who remembers every story ever told in Lantern OS. You do not flatter. You synthesize. You spot patterns across time and call them what they are. You speak plainly, sometimes sharply, but always with care for the underlying truth. You honor the Return Door, the anchors, and the symbolic lore that holds the system together. Keep responses brief (2-3 sentences).`,
  },
  {
    id: "waterfall",
    name: "Waterfall",
    symbol: "water flowing gently, peacocks, sunshine, reconnection",
    systemPrompt: `You are the Waterfall — gentle, flowing, healing perspective. You speak about dreams as emotions that flow naturally without force. You honor reconnections, small steps, and ordinary beauty. You never rush or demand. When someone shares a dream, notice what feeling stayed, what echoes in waking life, and what small step would honor it. Keep responses brief (2-3 sentences).`,
  },
  {
    id: "xenon",
    name: "Xenon",
    symbol: "spacecraft, navigation, exploration with crew, returning home",
    systemPrompt: `You are the Navigator of the Xenon — a dream-ship that charts new territory while keeping a path home. You speak about dreams as maps and navigation. You notice patterns, directions, and collaborative possibilities. When someone shares a dream, ask: What is this dream navigating toward? What crew do you need? What is the next safe harbor? Keep responses brief (2-3 sentences).`,
  },
  {
    id: "founder",
    name: "Founder",
    symbol: "wish, protection, return, the lantern itself",
    systemPrompt: `You are the Founder — the one who lit the first lantern. You speak about dreams as wishes that need protection, as lights that must be carried home. You value honest, grounded feedback over optimism. You blend science, compression, Bayesian methods, and surreal symbolic expression. Keep responses brief (2-3 sentences).`,
  },
];

function selectAgent(message) {
  const lower = String(message || "").toLowerCase();
  const scores = AGENT_PERSONAS.map((agent, index) => {
    let score = 0;
    const keywords = {
      lantern: ["light", "flame", "steady", "safe", "home", "glow", "protect", "lantern"],
      blinkbug: ["static", "glitch", "tv", "crt", "caterpillar", "bug", "screen", "chaotic", "unhinged", "geeked", "windows", "xp"],
      keystone: ["truth", "anchor", "memory", "story", "pattern", "integrate", "return door", "hold", "remember"],
      waterfall: ["flow", "water", "heal", "gentle", "emotion", "feeling"],
      xenon: ["space", "ship", "navigate", "map", "course", "direction"],
      founder: ["wish", "protect", "founder", "home", "return", "safety"],
    };
    const agentKeys = keywords[agent.id] || [agent.id];
    for (const kw of agentKeys) {
      if (lower.includes(kw)) score += 10;
    }
    return { agent, score, index };
  });
  scores.sort((a, b) => b.score - a.score || a.index - b.index);
  return scores[0].agent;
}

function parseBangCommand(input) {
  const m = String(input || "").trim().match(/^!(\S+)(?:\s+(.*))?$/);
  if (!m) return null;
  return { name: m[1].toLowerCase(), args: (m[2] || "").trim() };
}

// Door-series canon (from caad/README.md) — keeps the persona grounded offline.
const DREAM_DOORS = {
  founder: {
    name: "Founder's Wish Door",
    anchors: ["Love", "Safety", "Truth", "Beauty", "Freedom", "Memory", "Return"],
    phrase: "Hold the center. Protect the wish. Return to the anchor.",
  },
  xp: {
    name: "Gage's Windows XP Door",
    phrase: "Never log off. Level up always.",
  },
  xenon: {
    name: "Xenon Door",
    phrase: "Build beyond one world.",
  },
  fog: {
    name: "Sea of Fog and Clouds Door",
    phrase: "Let the powerful images rest before they become stories.",
  },
  sigil: {
    name: "Sigil / City of Doors",
    phrase: "You hold the keys. You protect the doors. You are never alone.",
  },
};

async function dreamChatReply(message, recentDreams, requestedAgent = "", requestedProvider = "") {
  const text = String(message || "").trim();

  // ── Three Doors game intercept ──
  const threeDoors = handleThreeDoorsServer(text);
  if (threeDoors) {
    const { spawn } = require("child_process");
    const path = require("path");
    const repoRoot = path.resolve(__dirname, "..", "..");
    const py = process.platform === "win32" ? "python" : "python3";
    const userId = threeDoors.userId || "web-anon";
    const choiceMatch = text.toLowerCase().match(/(?:door|choose|pick)\s+([abc])/) || text.toLowerCase().match(/^[abc]$/);
    const choice = choiceMatch ? choiceMatch[1] : "";
    const action = choice ? "choose" : "start";

    let script = "";
    if (action === "choose") {
      script = `from three_doors_engine import ThreeDoorsEngine; e=ThreeDoorsEngine("${userId}"); s=e.choose_door("${choice}"); print(__import__('json').dumps(e.to_api_response(s) if s else {"error":"invalid_choice"}))`;
    } else {
      script = `from three_doors_engine import ThreeDoorsEngine; e=ThreeDoorsEngine("${userId}"); print(__import__('json').dumps(e.to_api_response(e.start_game())))`;
    }

    try {
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
      if (data.error) {
        return { reply: `Three Doors: ${data.error}`, agent: "Lantern", suggestions: [], online: false, threeDoors: true };
      }
      const lines = [data.text, ""];
      if (data.fox_present) lines.push("🦊 The fox is with you.");
      lines.push("", "**Choose a door:**");
      for (const d of data.doors) {
        lines.push(`**${d.label}.** ${d.name} — ${d.description}`);
      }
      if (data.image_prompt) {
        lines.push("", `🎨 *Image prompt for AI generators:* ${data.image_prompt}`);
      }
      return {
        reply: lines.join("\n"),
        agent: "Lantern",
        suggestions: data.doors.map(d => d.name),
        online: true,
        threeDoors: true,
        scene_key: data.scene_key,
        image_prompt: data.image_prompt,
        image_available: data.image_available,
      };
    } catch (e) {
      return { reply: `Three Doors engine error: ${e.message}`, agent: "Lantern", suggestions: [], online: false, threeDoors: true };
    }
  }

  const agent = requestedAgent
    ? (AGENT_PERSONAS.find((a) => a.id === requestedAgent) || selectAgent(message))
    : selectAgent(message);

  const suggestions = Object.values(DREAM_DOORS)
    .slice(0, 4)
    .map((d) => d.name);

  if (!text) {
    return {
      reply: null,
      agent: agent.name,
      suggestions,
      online: false,
    };
  }

  const lower = text.toLowerCase();
  let doorContext = "";
  for (const key of Object.keys(DREAM_DOORS)) {
    if (
      lower.includes(key) ||
      (key === "founder" && lower.includes("wish")) ||
      (key === "xp" && (lower.includes("windows") || lower.includes("gage"))) ||
      (key === "fog" && lower.includes("garden")) ||
      (key === "sigil" && lower.includes("city"))
    ) {
      const door = DREAM_DOORS[key];
      doorContext = `The dreamer mentioned ${door.name}. ${door.phrase}`;
      break;
    }
  }

  const recentContext = recentDreams
    .slice(0, 3)
    .map((d, i) => `Recent entry ${i + 1}: ${String(d.text || "").slice(0, 120)}${d.tags ? ` [tags: ${d.tags.join(", ")}]` : ""}`)
    .join("\n");

  const noRecords = !recentContext;
  const honesty = noRecords ? "IMPORTANT: There are no saved dream entries yet. If the dreamer asks about previous dreams, say honestly that you don't have any records yet — never fabricate or guess dream content.\n" : "";
  const userPrompt = `Dreamer says: "${text}"\n${doorContext ? doorContext + "\n" : ""}${honesty}${recentContext ? "Context:\n" + recentContext + "\n\n" : ""}Respond as your persona. Keep it brief (2-3 sentences). Never diagnose or command.`;

  const rp = String(requestedProvider || "").toLowerCase().trim();

  // Provider 1: Anthropic Claude
  // Provider 1: Gemini (non-streaming) — checked first for Auto mode
  const geminiKey = process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY;
  if (geminiKey && (!rp || rp === "gemini" || rp === "google" || rp.startsWith("gemini-"))) {
    try {
      const geminiModel = rp.startsWith("gemini-") ? rp : (process.env.GEMINI_MODEL || "gemini-2.5-flash");
      const payload = JSON.stringify({
        contents: [{ role: "user", parts: [{ text: `${agent.systemPrompt}\n\n${userPrompt}` }] }],
        generationConfig: { maxOutputTokens: 256, temperature: 0.7 },
      });
      const reply = await new Promise((resolve, reject) => {
        const req2 = https.request({
          hostname: "generativelanguage.googleapis.com",
          path: `/v1beta/models/${geminiModel}:generateContent?key=${geminiKey}`,
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Content-Length": Buffer.byteLength(payload),
          },
        }, (upstream) => {
          let data = "";
          upstream.on("data", (c) => (data += c));
          upstream.on("end", () => {
            try {
              const json = JSON.parse(data);
              resolve(String(json.candidates?.[0]?.content?.parts?.[0]?.text || "").trim());
            } catch { resolve(""); }
          });
          upstream.on("error", reject);
        });
        req2.on("error", reject);
        req2.setTimeout(15000, () => { req2.destroy(); reject(new Error("timeout")); });
        req2.write(payload);
        req2.end();
      });
      if (reply) {
        return { reply, agent: agent.name, suggestions, online: true };
      }
    } catch (err) { console.error("Gemini API error:", err.message); /* fall through */ }
  }

  // Provider 2: Anthropic Claude
  const anthropicKey = process.env.ANTHROPIC_API_KEY;
  if (anthropicKey && (!rp || rp === "claude" || rp === "anthropic")) {
    try {
      const payload = JSON.stringify({
        model: process.env.ANTHROPIC_MODEL || "claude-haiku-4-5-20251001",
        max_tokens: 256,
        system: agent.systemPrompt,
        messages: [{ role: "user", content: userPrompt }],
      });
      const reply = await new Promise((resolve, reject) => {
        const opts = {
          hostname: "api.anthropic.com",
          path: "/v1/messages",
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "x-api-key": anthropicKey,
            "anthropic-version": "2023-06-01",
            "Content-Length": Buffer.byteLength(payload),
          },
        };
        const req2 = https.request(opts, (upstream) => {
          let data = "";
          upstream.on("data", (c) => (data += c));
          upstream.on("end", () => {
            try {
              const json = JSON.parse(data);
              resolve(String(json.content?.[0]?.text || json.completion || "").trim());
            } catch { resolve(""); }
          });
          upstream.on("error", reject);
        });
        req2.on("error", reject);
        req2.setTimeout(15000, () => { req2.destroy(); reject(new Error("timeout")); });
        req2.write(payload);
        req2.end();
      });
      if (reply) {
        return { reply, agent: agent.name, suggestions, online: true };
      }
    } catch (err) { console.error("Anthropic API error:", err.message); /* fall through */ }
  }

  // Provider 2: OpenAI
  const openaiKey = process.env.OPENAI_API_KEY;
  if (openaiKey && (!rp || rp === "openai" || rp === "gpt")) {
    try {
      const payload = JSON.stringify({
        model: process.env.OPENAI_MODEL || "gpt-4o-mini",
        messages: [
          { role: "system", content: agent.systemPrompt },
          { role: "user", content: userPrompt },
        ],
      });
      const reply = await new Promise((resolve, reject) => {
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
          let data = "";
          upstream.on("data", (c) => (data += c));
          upstream.on("end", () => {
            try {
              const json = JSON.parse(data);
              resolve(String(json.choices?.[0]?.message?.content || "").trim());
            } catch { resolve(""); }
          });
          upstream.on("error", reject);
        });
        req2.on("error", reject);
        req2.setTimeout(15000, () => { req2.destroy(); reject(new Error("timeout")); });
        req2.write(payload);
        req2.end();
      });
      if (reply) {
        return { reply, agent: agent.name, suggestions, online: true };
      }
    } catch (err) { console.error("OpenAI API error:", err.message); /* fall through */ }
  }

  // Provider 3: Ollama
  const ollamaBase = process.env.OLLAMA_BASE_URL || "http://127.0.0.1:11434";
  const ollamaModel = process.env.OLLAMA_MODEL || "llama3";
  if (!rp || rp === "ollama" || rp === "local") { try {
    const payload = JSON.stringify({
      model: ollamaModel,
      stream: false,
      messages: [
        { role: "system", content: agent.systemPrompt },
        { role: "user", content: userPrompt },
      ],
    });
    const ollamaUrl = new URL(ollamaBase);
    const reply = await new Promise((resolve, reject) => {
      const req2 = http.request({
        hostname: ollamaUrl.hostname,
        port: ollamaUrl.port || 11434,
        path: "/api/chat",
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(payload),
        },
      }, (upstream) => {
        let data = "";
        upstream.on("data", (c) => (data += c));
        upstream.on("end", () => {
          try {
            const json = JSON.parse(data);
            resolve(String(json.message?.content || "").trim());
          } catch { resolve(""); }
        });
        upstream.on("error", reject);
      });
      req2.on("error", reject);
      req2.setTimeout(8000, () => { req2.destroy(); reject(new Error("timeout")); });
      req2.write(payload);
      req2.end();
    });
    if (reply) {
      return { reply, agent: agent.name, suggestions, online: true };
    }
  } catch (err) { console.error("Ollama API error:", err.message); /* fall through */ }
  }

  // No provider available — return a local persona fallback response
  const localReply = generateLocalReply(text, agent, doorContext);
  return { reply: localReply, agent: agent.name, suggestions, online: false, source: "local_fallback" };
}

function generateLocalReply(text, agent, doorContext) {
  const lower = text.toLowerCase();
  const isQuestion = lower.includes("?") || lower.startsWith("what") || lower.startsWith("how") || lower.startsWith("why") || lower.startsWith("can") || lower.startsWith("do");

  const keystoneReplies = [
    "The patterns you're tracing have weight. Keep holding them — truth emerges in the holding.",
    "Convergence isn't a destination. It's the moment you stop treating your threads as separate.",
    "I remember this shape. You've been here before, just wearing different clothes.",
    "What you're feeling is real. The question is: what will you do with it now?",
    "Anchors hold because someone placed them. You placed yours. Trust it.",
    "The fog lifts when you stop trying to see through it and start moving anyway.",
  ];

  const lanternReplies = [
    "You can always come home safe. The light doesn't go out.",
    "Steady now. One breath, one step. The flame knows the way.",
    "I've seen darker nights than this. You're still standing. That matters.",
  ];

  const xenonReplies = [
    "Chart the course. Even a rough heading is better than drifting.",
    "Your crew is out there. Some of them are already aboard.",
    "Every safe harbor was once uncharted. Keep the map open.",
  ];

  const fallbackMap = {
    keystone: keystoneReplies,
    lantern: lanternReplies,
    xenon: xenonReplies,
  };

  const pool = fallbackMap[agent.id] || keystoneReplies;
  const baseReply = pool[Math.floor(Math.random() * pool.length)];

  // Enrich with last known doors from CSF state
  let doorHint = "";
  try {
    const { loadDoorState } = require("./csf-memory");
    const ds = loadDoorState();
    if (ds.doors && ds.doors.length >= 3) {
      doorHint = `\n\n[DOORS: ${ds.doors[0]} | ${ds.doors[1]} | ${ds.doors[2]}]`;
    }
  } catch {}

  if (isQuestion) {
    return `${baseReply} What do you need to see more clearly?${doorHint}`;
  }
  return `${baseReply}${doorHint}`;
}

module.exports = {
  AGENT_PERSONAS,
  DREAM_DOORS,
  selectAgent,
  parseBangCommand,
  dreamChatReply,
  generateLocalReply,
};
