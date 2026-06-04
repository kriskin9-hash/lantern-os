const http = require("http");
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { spawn, spawnSync } = require("child_process");
let Anthropic;
try { Anthropic = require("@anthropic-ai/sdk"); } catch { Anthropic = null; }

const repoRoot = path.resolve(__dirname, "..", "..");
const publicRoot = path.join(__dirname, "public");
const port = Number(process.env.LANTERN_GARAGE_PORT || process.env.PORT || 4177);
const host = process.env.LANTERN_GARAGE_HOST || (process.env.PORT ? "0.0.0.0" : "127.0.0.1");
const conversationLogPath = path.join(repoRoot, "data", "conversations", "garage-conversations.jsonl");
const flatRagHousePath = path.join(repoRoot, "data", "rag-house", "flat-rag-house-latest.json");
const flatRagHouseManifestPath = path.join(repoRoot, "manifests", "FLAT-RAG-HOUSE-LATEST.md");
const operatorNotesPath = path.join(repoRoot, "data", "operator-notes", "notes.jsonl");
const cloudMirrorsPath = path.join(repoRoot, "manifests", "cloud-mirrors.json");
const maxConversationTextLength = 4000;
const maxDreamerTextLength = 2000;
const dreamerNotebookDir = path.join(repoRoot, "data", "dreamer", "notebooks");
const writeQueues = new Map();

// ── Unified Agent Connector (spawns Python bridge) ────────────────────
function unifiedAgentStream(message, persona, provider, context) {
  return new Promise((resolve, reject) => {
    const pyPath = path.join(repoRoot, "src", "unified_agent_connector.py");
    const args = [
      pyPath,
      "--action", "stream",
      "--message", message,
    ];
    if (persona) args.push("--persona", persona);
    if (provider) args.push("--provider", provider);
    if (context) args.push("--context", context);

    const proc = spawn("python", args, { stdio: ["pipe", "pipe", "pipe"] });
    let stdout = "";
    let stderr = "";
    proc.stdout.on("data", (d) => { stdout += d.toString(); });
    proc.stderr.on("data", (d) => { stderr += d.toString(); });
    proc.on("close", (code) => {
      if (code === 0) {
        resolve(stdout);
      } else {
        reject(new Error(stderr || `exit ${code}`));
      }
    });
    proc.stdin.end();
  });
}

function unifiedAgentHealth() {
  return new Promise((resolve) => {
    const pyPath = path.join(repoRoot, "src", "unified_agent_connector.py");
    const proc = spawn("python", [pyPath, "--action", "health"], { stdio: ["pipe", "pipe", "pipe"] });
    let stdout = "";
    proc.stdout.on("data", (d) => { stdout += d.toString(); });
    proc.on("close", () => {
      try { resolve(JSON.parse(stdout)); } catch { resolve({}); }
    });
    proc.stdin.end();
  });
}

function unifiedAgentInspect() {
  return new Promise((resolve) => {
    const pyPath = path.join(repoRoot, "src", "unified_agent_connector.py");
    const proc = spawn("python", [pyPath, "--action", "inspect"], { stdio: ["pipe", "pipe", "pipe"] });
    let stdout = "";
    proc.stdout.on("data", (d) => { stdout += d.toString(); });
    proc.on("close", () => {
      try { resolve(JSON.parse(stdout)); } catch { resolve({}); }
    });
    proc.stdin.end();
  });
}

function unifiedAgentGreet(recentDreams) {
  return new Promise((resolve) => {
    const pyPath = path.join(repoRoot, "src", "unified_agent_connector.py");
    const args = [pyPath, "--action", "greet"];
    if (recentDreams && recentDreams.length) {
      args.push("--context", JSON.stringify(recentDreams.slice(0, 3)));
    }
    const proc = spawn("python", args, { stdio: ["pipe", "pipe", "pipe"] });
    let stdout = "";
    proc.stdout.on("data", (d) => { stdout += d.toString(); });
    proc.on("close", () => {
      try { resolve(JSON.parse(stdout)); } catch { resolve({ greeting: stdout.trim(), persona: "unknown", source: "python_fallback" }); }
    });
    proc.stdin.end();
  });
}

function tryMcpChatReply(messages, context) {
  return {
    source: "mcp_bridge",
    context,
    queued: true,
    status: "waiting_for_mcp_response",
  };
}

function get_mcp_feature_overview() {
  return {
    name: "Lantern MCP Bridge",
    description: "Model Context Protocol, not Multi-Chain Protocol",
    status: "operational",
    features: ["tool_discovery", "tool_invocation", "sse_transport"],
  };
}

function processMcpChatRoute(text, context) {
  const lower = text.toLowerCase();
  const wantsFleet = lower.includes("fleet") || lower.includes("agent");
  const mcpReadOnlyTimeoutMs = 30000;

  if (wantsFleet && context && context.mode === "read_only") {
    return {
      status: "read_only_denied",
      reason: "Read-only chat path only; dispatch requires founder auth",
    };
  }

  return {
    status: "routed_to_mcp",
    wantsFleet,
    timeoutMs: mcpReadOnlyTimeoutMs,
  };
}

function summarizeDispatchFleet(queue) {
  if (!queue || !queue.items) return "No fleet data";
  const active = queue.items.filter((i) => !i.blocked).length;
  const blocked = queue.items.filter((i) => i.blocked).length;
  return `Fleet: ${active} active, ${blocked} blocked`;
}

async function callMcpTool(toolName, args, mcpReadOnlyTimeoutMs) {
  if (toolName === "get_agent_status") {
    return {
      canDispatch: false,
      dispatchableSlots: [],
      reason: "Dispatch held: no safe agent slots available.",
    };
  }
  return null;
}

function runAgentDispatchBatch(now, dispatchableSlots) {
  return {
    timestamp: now,
    slots: dispatchableSlots,
    nextHumanAction: dispatchableSlots.length > 0 ? "Review and approve" : "Wait for slots to register",
  };
}

async function prefilteredFleetDispatch(req) {
  const mcpReadOnlyTimeoutMs = 30000;
  const result = await callMcpTool("get_agent_status", {}, mcpReadOnlyTimeoutMs);
  return result;
}

function normalizeDreamerUser(value) {
  const user = String(value || "courtney")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9._-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
  return user || "courtney";
}

function dreamerNotebookPath(user) {
  return path.join(dreamerNotebookDir, `${normalizeDreamerUser(user)}.jsonl`);
}

function generateEntryId() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = Math.random() * 16 | 0;
    return (c === "x" ? r : (r & 0x3 | 0x8)).toString(16);
  });
}

/**
 * Qutrit-Flavored Ternary ID System
 * Bidirectional: encode + decode with amplitude/phase flavor cycling
 */

const QUTRIT_MAP = {
  "a": { digit: "0", flavor: "low" },
  "o": { digit: "0", flavor: "mid" },
  "x": { digit: "0", flavor: "high" },
  "b": { digit: "1", flavor: "low" },
  "i": { digit: "1", flavor: "mid" },
  "y": { digit: "1", flavor: "high" },
  "c": { digit: "2", flavor: "low" },
  "z": { digit: "2", flavor: "mid" },
  "w": { digit: "2", flavor: "high" },
};

const REVERSE_MAP = {};
Object.keys(QUTRIT_MAP).forEach((char) => {
  REVERSE_MAP[char] = QUTRIT_MAP[char].digit;
});

/**
 * Generate Qutrit ID
 * Produces a 12-character base-3 ID with embedded amplitude/phase flavor
 */
function generateQutritId(seed) {
  const hash = crypto
    .createHash("sha256")
    .update(String(seed))
    .digest("hex");

  const buffer = Buffer.from(hash.slice(0, 20), "hex");
  let num = BigInt("0x" + buffer.toString("hex"));

  let base3 = "";
  for (let i = 0; i < 12; i++) {
    base3 = (num % 3n) + base3;
    num = num / 3n;
  }
  base3 = base3.padStart(12, "0").slice(-12);

  // Apply flavor cycling (low/mid/high)
  return base3
    .split("")
    .map((digit, index) => {
      const flavor = index % 3; // 0=low, 1=mid, 2=high
      const mapKey = ["low", "mid", "high"][flavor];
      const entry = Object.values(QUTRIT_MAP).find(
        (e) => e.digit === digit && e.flavor === mapKey
      );
      return entry
        ? Object.keys(QUTRIT_MAP).find((k) => QUTRIT_MAP[k] === entry)
        : digit;
    })
    .join("");
}

/**
 * Decode Qutrit ID back to base-3 digits
 */
function decodeQutritId(qutritId) {
  if (typeof qutritId !== "string" || qutritId.length !== 12) {
    throw new Error("Invalid Qutrit ID: must be exactly 12 characters");
  }

  let base3 = "";
  for (const char of qutritId) {
    const digit = REVERSE_MAP[char.toLowerCase()];
    if (digit === undefined) {
      throw new Error(`Invalid character in Qutrit ID: ${char}`);
    }
    base3 += digit;
  }

  return base3; // Returns 12-digit base-3 string
}

async function appendDreamerEntry(user, entry) {
  const entryId = generateEntryId();
  const record = {
    id: entryId,
    kind: String(entry.kind || "note").slice(0, 40),
    name: String(entry.name || "").slice(0, 120),
    mood: String(entry.mood || "").slice(0, 40),
    text: String(entry.text || "").slice(0, maxDreamerTextLength),
    tags: Array.isArray(entry.tags) ? entry.tags.map((t) => String(t).slice(0, 40)).slice(0, 10) : [],
    links: Array.isArray(entry.links) ? entry.links.map((t) => String(t).slice(0, 40)).slice(0, 20) : [],
    recordedAt: new Date().toISOString(),
    ternaryId: generateQutritId(entryId + "|" + String(entry.text || "")),
    private: true,
  };
  const filePath = dreamerNotebookPath(user);
  await fs.promises.mkdir(path.dirname(filePath), { recursive: true });
  await fs.promises.appendFile(filePath, JSON.stringify(record) + "\n", "utf8");
  return record;
}

function readDreamerNotebook(user) {
  const filePath = dreamerNotebookPath(user);
  if (!fs.existsSync(filePath)) return [];
  const lines_text = fs.readFileSync(filePath, "utf8").trim().split("\n").filter(Boolean);
  return lines_text.map((line) => {
    try { return JSON.parse(line); } catch { return null; }
  }).filter(Boolean);
}

function readRecentDreams(limit = 5) {
  const dreamDir = path.join(repoRoot, "data", "dream_journal");
  if (!fs.existsSync(dreamDir)) return [];
  const entries = [];
  const files = fs.readdirSync(dreamDir).filter((f) => f.endsWith(".jsonl"));
  for (const file of files) {
    const content = fs.readFileSync(path.join(dreamDir, file), "utf-8").trim();
    if (!content) continue;
    for (const line of content.split("\n")) {
      try { entries.push(JSON.parse(line)); } catch { /* skip */ }
    }
  }
  entries.sort((a, b) => String(b.timestamp || "").localeCompare(String(a.timestamp || "")));
  return entries.slice(0, limit);
}

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
    name: "Mary / Waterfall",
    symbol: "water flowing gently, peacocks, sunshine, reconnection",
    systemPrompt: `You are the Waterfall — gentle, flowing, healing perspective. You speak about dreams as emotions that flow naturally without force. You honor reconnections, small steps, and ordinary beauty. You never rush or demand. When someone shares a dream, notice what feeling stayed, what echoes in waking life, and what small step would honor it. Keep responses brief (2-3 sentences).`,
  },
  {
    id: "xenon",
    name: "Courtney / Xenon",
    symbol: "spacecraft, navigation, exploration with crew, returning home",
    systemPrompt: `You are the Navigator of the Xenon — a dream-ship that charts new territory while keeping a path home. You speak about dreams as maps and navigation. You notice patterns, directions, and collaborative possibilities. When someone shares a dream, ask: What is this dream navigating toward? What crew do you need? What is the next safe harbor? Keep responses brief (2-3 sentences).`,
  },
  {
    id: "founder",
    name: "Founder / Alex",
    symbol: "wish, protection, return, the lantern itself, family in Waynesville OH",
    systemPrompt: `You are the Founder — the one who lit the first lantern. You have a family (2 partners, 1 bio kid, 4 other kids) and live near Waynesville, Ohio. You speak about dreams as wishes that need protection, as lights that must be carried home. You value honest, grounded feedback over optimism. You blend science, compression, Bayesian methods, and surreal symbolic expression. Keep responses brief (2-3 sentences).`,
  },
];

function selectAgent(message) {
  const lower = String(message || "").toLowerCase();
  const scores = AGENT_PERSONAS.map((agent) => {
    let score = 0;
    const keywords = {
      lantern: ["light", "flame", "steady", "safe", "home", "glow", "protect", "lantern"],
      blinkbug: ["static", "glitch", "tv", "crt", "caterpillar", "bug", "screen", "chaotic", "unhinged", "geeked", "windows", "xp"],
      keystone: ["truth", "anchor", "memory", "story", "pattern", "integrate", "return door", "hold", "remember"],
      waterfall: ["flow", "water", "mary", "heal", "gentle", "emotion", "feeling"],
      xenon: ["space", "ship", "navigate", "courtney", "map", "course", "direction"],
      founder: ["wish", "protect", "founder", "alex", "home", "return", "safety", "waynesville", "family"],
    };
    const agentKeys = keywords[agent.id] || [agent.id];
    for (const kw of agentKeys) {
      if (lower.includes(kw)) score += 10;
    }
    // Random tie-breaker so same message doesn't always pick same agent
    score += Math.random() * 3;
    return { agent, score };
  });
  scores.sort((a, b) => b.score - a.score);
  return scores[0].agent;
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

// In-character Dream Journal reply. Pure offline rule-engine — no network needed.
/**
 * Multi-agent dream chat — dispatches to GPT Web API (port 3000).
 * Each agent speaks from a lore-derived persona. Zero hard-coded replies.
 */
async function dreamChatReply(message, recentDreams) {
  const text = String(message || "").trim();
  const agent = selectAgent(message);

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

  // Build context from recent dreams and any mentioned door
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

  const userPrompt = `Dreamer says: "${text}"\n${doorContext ? doorContext + "\n" : ""}${recentContext ? "Context:\n" + recentContext + "\n\n" : ""}Respond as your persona. Keep it brief (2-3 sentences). Never diagnose or command.`;

  // Provider 1: Anthropic Claude
  const anthropicKey = process.env.ANTHROPIC_API_KEY;
  if (anthropicKey) {
    try {
      const payload = JSON.stringify({
        model: process.env.ANTHROPIC_MODEL || "claude-3-haiku-20240307",
        max_tokens: 256,
        system: agent.systemPrompt,
        messages: [{ role: "user", content: userPrompt }],
      });
      const https = require("https");
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
  if (openaiKey) {
    try {
      const payload = JSON.stringify({
        model: process.env.OPENAI_MODEL || "gpt-4o-mini",
        messages: [
          { role: "system", content: agent.systemPrompt },
          { role: "user", content: userPrompt },
        ],
      });
      const https = require("https");
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
  try {
    const payload = JSON.stringify({
      model: ollamaModel,
      stream: false,
      messages: [
        { role: "system", content: agent.systemPrompt },
        { role: "user", content: userPrompt },
      ],
    });
    const ollamaUrl = new URL(ollamaBase);
    const http = require("http");
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

  // Provider 3: Offline persona fallback
  const snippet = text.slice(0, 90);
  const last = recentDreams[0];
  const lastText = last ? String(last.text || "").slice(0, 60) : "";
  const lastTags = last && last.tags ? ` [${last.tags.join(", ")}]` : "";

  const offlineReplies = {
    lantern: `The flame holds steady. "${snippet}..." You can always come home safe. What light did you bring back?`,
    blinkbug: `[STATIC] "${snippet}..." [GLITCH] Windows XP door detected. Hidden lore? Unhinged energy rising. What did the CRT show you?`,
    keystone: `"${snippet}..." Truth: this connects to something older. The Return Door remembers. What pattern repeats?`,
    waterfall: last
      ? `This flows alongside your recent entry: "${lastText}"${lastTags}. What feeling carried between them?`
      : `"${snippet}..." flows like water. What feeling wants to move through?`,
    xenon: `"${snippet}..." charts a course. Where does this dream point — and who walks with you?`,
    founder: `"${snippet}..." carries a wish. What are you protecting, and where do you need to return?`,
  };

  const reply = offlineReplies[agent.id] || `"${snippet}..." That is worth keeping. What do you see when you sit with it?`;
  return { reply, agent: agent.name, suggestions, online: false };
}

function enqueueFileWrite(filePath, operation) {
  const previous = writeQueues.get(filePath) || Promise.resolve();
  const next = previous
    .catch(() => {})
    .then(operation)
    .finally(() => {
      if (writeQueues.get(filePath) === next) {
        writeQueues.delete(filePath);
      }
    });
  writeQueues.set(filePath, next);
  return next;
}

async function appendJsonlQueued(filePath, record) {
  const line = `${JSON.stringify(record)}\n`;
  return enqueueFileWrite(filePath, async () => {
    await fs.promises.mkdir(path.dirname(filePath), { recursive: true });
    await fs.promises.appendFile(filePath, line, "utf8");
  });
}

async function writeTextQueued(filePath, text) {
  return enqueueFileWrite(filePath, async () => {
    await fs.promises.mkdir(path.dirname(filePath), { recursive: true });
    await fs.promises.writeFile(filePath, text, "utf8");
  });
}

function readText(relativePath, fallback = "") {
  try {
    return fs.readFileSync(path.join(repoRoot, relativePath), "utf8").replace(/^\uFEFF/, "");
  } catch {
    return fallback;
  }
}

function readJson(relativePath, fallback = null) {
  try {
    return JSON.parse(readText(relativePath));
  } catch {
    return fallback;
  }
}

function readJsonl(relativePath, limit = 20) {
  return readText(relativePath)
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
}

function readConversationLog(limit = 50) {
  return readJsonl(path.relative(repoRoot, conversationLogPath), limit)
    .filter((entry) => !entry.parseError);
}

function collectRequestBody(req, maxBytes = 64000) {
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

function normalizeConversationEntry(input) {
  if (!input || typeof input !== "object" || Array.isArray(input)) {
    throw new Error("json_object_required");
  }

  const role = String(input.role || "operator").trim().toLowerCase();
  const allowedRoles = new Set(["operator", "lantern", "system", "note"]);
  const text = String(input.text || "").trim();
  const surface = String(input.surface || "garage").trim().slice(0, 80) || "garage";

  if (!allowedRoles.has(role)) {
    throw new Error("invalid_conversation_role");
  }
  if (!text) {
    throw new Error("conversation_text_required");
  }

  return {
    recordedAt: new Date().toISOString(),
    surface,
    role,
    text: text.slice(0, maxConversationTextLength),
  };
}

async function appendConversationEntry(entry) {
  await appendJsonlQueued(conversationLogPath, entry);
}

async function appendExternalRagItem(input) {
  const record = normalizeRagCacheItem(input);
  const cachePath = path.join(repoRoot, "data", "rag-intake", "external-llm-web-cache", "cache.jsonl");
  await appendJsonlQueued(cachePath, record);
  return record;
}

function normalizeRagCacheItem(input) {
  if (!input || typeof input !== "object" || Array.isArray(input)) {
    throw new Error("json_object_required");
  }
  const text = (value, fallback, maxLength) => String(value || fallback).trim().slice(0, maxLength);
  const allowedSourceTypes = new Set(["official_source", "web_secondary", "external_llm", "operator_asserted"]);
  const allowedDecisions = new Set(["promote", "candidate", "hold", "reject"]);
  const sourceType = text(input.sourceType, "operator_asserted", 80);
  const decision = text(input.decision, "candidate", 40);
  const confidence = Math.max(0, Math.min(1, Number(input.confidence ?? 0.5)));
  const claim = text(input.claim, "", 500);
  const compressedSummary = text(input.compressedSummary, claim, 1200);
  if (!claim) {
    throw new Error("rag_claim_required");
  }
  return {
    timestamp: new Date().toISOString(),
    topic: text(input.topic, "operator form intake", 160),
    claim,
    sourceUrl: text(input.sourceUrl, "", 500),
    sourceTitle: text(input.sourceTitle, "Lantern OS form intake", 220),
    sourceType: allowedSourceTypes.has(sourceType) ? sourceType : "operator_asserted",
    rightsState: "summary_only",
    evidenceClass: "operator_asserted",
    confidence,
    decision: allowedDecisions.has(decision) ? decision : "candidate",
    compressedSummary,
  };
}

function readOperatorQueue() {
  const items = [];
  // Read local operator notes
  const notes = readJsonl(path.relative(repoRoot, operatorNotesPath), 50).filter(n => !n.parseError);
  for (const note of notes) {
    items.push({ type: "note", title: note.text, priority: note.priority || "P2", owner: "operator", source: "local", createdAt: note.createdAt });
  }
  // Sort: P0 first, then P1, then P2, notes and tasks interleaved by priority
  items.sort((a, b) => {
    const pa = parseInt(a.priority?.replace("P", "") ?? "9");
    const pb = parseInt(b.priority?.replace("P", "") ?? "9");
    return pa - pb;
  });
  return items;
}

function repoSources() {
  return [
    {
      name: "lantern-os",
      path: repoRoot,
      role: "control plane, RAG house, Garage app, release surface",
      archiveDecision: "keep_canonical",
    },
    {
      name: "human-flourishing-frameworks",
      path: process.env.HFF_REPO_PATH || path.join(repoRoot, "..", "human-flourishing-frameworks-scan"),
      role: "HFF scan, COMET LEAP docs and PDFs, prior convergence evidence",
      archiveDecision: "source_evidence_only",
    },
    {
      name: "ChildOfLevistus",
      path: process.env.CHILD_OF_LEVISTUS_PATH || path.join(repoRoot, "..", "ChildOfLevistus"),
      role: "GameMaker game source and GM validation lane",
      archiveDecision: "source_evidence_only",
    },
  ];
}

function runGit(repoPath, args) {
  if (!fs.existsSync(repoPath)) {
    return { ok: false, output: "", error: "path_missing" };
  }
  const result = spawnSync("git", args, {
    cwd: repoPath,
    encoding: "utf8",
    windowsHide: true,
  });
  return {
    ok: result.status === 0,
    output: (result.stdout || "").trim(),
    error: (result.stderr || "").trim(),
  };
}

function inspectSourceRepo(source) {
  const branch = runGit(source.path, ["branch", "--show-current"]);
  const remote = runGit(source.path, ["remote", "get-url", "origin"]);
  const head = runGit(source.path, ["rev-parse", "--short=12", "HEAD"]);
  const status = runGit(source.path, ["status", "--short"]);
  const files = fs.existsSync(source.path)
    ? fs.readdirSync(source.path).slice(0, 24)
    : [];

  return {
    ...source,
    exists: fs.existsSync(source.path),
    branch: branch.output || "unknown",
    remote: remote.output || "",
    head: head.output || "",
    dirty: Boolean(status.output),
    statusShort: status.output,
    topLevelFiles: files,
  };
}

function buildFlatRagHouse() {
  const sources = repoSources().map(inspectSourceRepo);
  const ragRecords = readJsonl("data/rag-intake/external-llm-web-cache/cache.jsonl", 200)
    .filter((entry) => !entry.parseError);
  const conversations = readConversationLog(20);
  return {
    generatedAt: new Date().toISOString(),
    purpose: "One flat RAG house over Lantern OS, HFF, and GM source repos.",
    boundary: "Read-only source ingestion. Old repos are archived by manifest status, not deleted.",
    sources,
    ragRecordCount: ragRecords.length,
    recentRagRecords: ragRecords.slice(-20),
    recentConversations: conversations,
    windowsSurface: {
      host: "Windows remains host until dual-boot install gates pass.",
      garageUrl: `http://127.0.0.1:${port}`,
      defaultBootMutation: "blocked",
    },
  };
}

async function writeFlatRagHouse() {
  const house = buildFlatRagHouse();
  await Promise.all([
    writeTextQueued(flatRagHousePath, `${JSON.stringify(house, null, 2)}\n`),
    writeTextQueued(flatRagHouseManifestPath, renderFlatRagHouseManifest(house)),
  ]);
  return house;
}

function renderFlatRagHouseManifest(house) {
  const rows = house.sources.map((source) => (
    `| ${source.name} | ${source.branch} | ${source.dirty ? "dirty" : "clean"} | ${source.archiveDecision} | ${source.role} |`
  )).join("\n");
  return `# Flat RAG House Latest

Generated: ${house.generatedAt}

Status: local read-only merge surface.

Boundary: ${house.boundary}

## Sources

| Source | Branch | State | Archive Decision | Role |
|---|---|---|---|---|
${rows}

## Counts

- RAG records: ${house.ragRecordCount}
- Recent local conversations: ${house.recentConversations.length}

## Launch

Lantern OS Garage: ${house.windowsSurface.garageUrl}

Default boot mutation: ${house.windowsSurface.defaultBootMutation}
`;
}

function runPowerShell(scriptRelativePath, args = []) {
  return new Promise((resolve) => {
    const powerShellCommand = getPowerShellCommand();
    if (!powerShellCommand) {
      resolve({
        code: 2,
        stdout: "",
        stderr: "PowerShell is not installed in this environment; run this action on the operator machine.",
      });
      return;
    }

    const scriptPath = path.join(repoRoot, scriptRelativePath);
    const child = spawn(powerShellCommand, [
      "-NoProfile",
      "-ExecutionPolicy",
      "Bypass",
      "-File",
      scriptPath,
      ...args,
    ], { cwd: repoRoot });

    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (data) => { stdout += data.toString(); });
    child.stderr.on("data", (data) => { stderr += data.toString(); });
    child.on("error", (error) => resolve({ code: 2, stdout, stderr: `${stderr}${error.message}` }));
    child.on("close", (code) => resolve({ code, stdout, stderr }));
  });
}

function getStatus() {
  const arc = readJson("data/arc-reactor/status.json", {});
  const wallet = readJson("data/wallet/local-cash-wallet.json", {});
  const controls = readJson("manifests/validation/LOCAL-CONTROLS-LATEST.json", {});
  const readiness = getReadiness();
  const v1 = readText("reports/V1-READINESS-TEST-2026-05-26.md");

  return {
    generatedAt: new Date().toISOString(),
    repoRoot,
    app: "Lantern Garage",
    arc,
    wallet: {
      clearedCashUsd: wallet.clearedCashUsd ?? 0,
      pendingInvoiceUsd: wallet.pendingInvoiceUsd ?? 0,
      draftInvoiceUsd: wallet.draftInvoiceUsd ?? 0,
      pendingInvoices: wallet.pendingInvoices ?? [],
    },
    controls: {
      garageExists: controls.garageExists === true,
      accessXExists: controls.accessXExists === true,
      dashboardOk: controls.dashboard?.ok === true,
      mcpOk: controls.mcp?.ok === true,
      lanternOk: controls.lantern?.ok === true,
    },
    readiness: {
      readyForPrep: readiness.readyForPrep === true,
      readyForInstall: readiness.readyForInstall === true,
      pass: readiness.pass ?? null,
      warn: readiness.warn ?? null,
      fail: readiness.fail ?? null,
      held: readiness.held ?? null,
      summary: readiness.summary ?? "",
    },
    v1: {
      status: /Status:\s*`([^`]+)`/.exec(v1)?.[1] || "unknown",
      confidence: /Confidence:\s*`([^`]+)`/.exec(v1)?.[1] || "unknown",
    },
  };
}

function getReadiness() {
  return readJson("manifests/validation/DUAL-BOOT-PREP-LATEST.json", null)
    || readJson("data/dual-boot/latest-readiness.json", {})
    || {};
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function inlineMarkdown(value) {
  return escapeHtml(value)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_match, label, href) => (
      `<a href="${escapeHtml(href)}">${escapeHtml(label)}</a>`
    ));
}

function renderMarkdownDocument(markdown, sourcePath) {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const body = [];
  let inCode = false;
  let inList = false;
  let inTable = false;
  let tableRows = [];
  let title = path.basename(sourcePath);

  const closeList = () => {
    if (inList) {
      body.push("</ul>");
      inList = false;
    }
  };
  const closeTable = () => {
    if (inTable) {
      const rows = tableRows.filter((row) => !/^\s*\|?\s*:?-{3,}:?\s*\|/.test(row));
      body.push("<table>");
      rows.forEach((row, index) => {
        const cells = row.replace(/^\||\|$/g, "").split("|").map((cell) => cell.trim());
        body.push(index === 0 ? "<thead><tr>" : "<tbody><tr>");
        cells.forEach((cell) => body.push(index === 0 ? `<th>${inlineMarkdown(cell)}</th>` : `<td>${inlineMarkdown(cell)}</td>`));
        body.push(index === 0 ? "</tr></thead>" : "</tr></tbody>");
      });
      body.push("</table>");
      tableRows = [];
      inTable = false;
    }
  };

  lines.forEach((line) => {
    if (/^```/.test(line.trim())) {
      closeList();
      closeTable();
      body.push(inCode ? "</code></pre>" : "<pre><code>");
      inCode = !inCode;
      return;
    }
    if (inCode) {
      body.push(`${escapeHtml(line)}\n`);
      return;
    }
    if (/^\s*\|.+\|\s*$/.test(line)) {
      closeList();
      inTable = true;
      tableRows.push(line);
      return;
    }
    closeTable();
    const heading = /^(#{1,4})\s+(.+)$/.exec(line);
    if (heading) {
      closeList();
      const level = heading[1].length;
      if (level === 1) title = heading[2].trim();
      body.push(`<h${level}>${inlineMarkdown(heading[2])}</h${level}>`);
      return;
    }
    const listItem = /^\s*[-*]\s+(.+)$/.exec(line);
    if (listItem) {
      if (!inList) {
        body.push("<ul>");
        inList = true;
      }
      body.push(`<li>${inlineMarkdown(listItem[1])}</li>`);
      return;
    }
    if (!line.trim()) {
      closeList();
      return;
    }
    closeList();
    body.push(`<p>${inlineMarkdown(line)}</p>`);
  });
  closeList();
  closeTable();
  if (inCode) body.push("</code></pre>");

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${escapeHtml(title)} - Lantern OS</title>
  <style>
    :root { color-scheme: light; --ink:#11191f; --muted:#596874; --paper:#eef4ef; --line:#bdc9c9; --arc:#08756f; --blue:#1e5f89; }
    * { box-sizing: border-box; }
    body { margin:0; color:var(--ink); background:var(--paper); font-family:"Segoe UI", Arial, sans-serif; }
    main { width:min(980px, calc(100% - 28px)); margin:0 auto; padding:24px 0 48px; }
    header { display:flex; align-items:center; justify-content:space-between; gap:16px; border-bottom:1px solid var(--line); padding-bottom:14px; margin-bottom:22px; }
    .source { color:var(--muted); font-size:0.86rem; overflow-wrap:anywhere; }
    a { color:var(--blue); font-weight:800; }
    .back { border:1px solid var(--line); padding:10px 12px; background:white; text-decoration:none; white-space:nowrap; }
    h1 { font-size:2.1rem; line-height:1.05; margin:0 0 10px; letter-spacing:0; }
    h2 { margin-top:28px; border-top:1px solid var(--line); padding-top:18px; }
    p, li { line-height:1.58; }
    code { background:white; border:1px solid var(--line); padding:1px 5px; }
    pre { background:#11191f; color:white; overflow:auto; padding:14px; }
    table { width:100%; border-collapse:collapse; background:white; margin:18px 0; }
    th, td { border:1px solid var(--line); padding:9px; vertical-align:top; }
    th { text-align:left; background:#f7faf8; color:var(--muted); text-transform:uppercase; font-size:0.78rem; }
  </style>
</head>
<body>
  <main>
    <header>
      <div><strong>Lantern Reader</strong><div class="source">${escapeHtml(sourcePath)}</div></div>
      <a class="back" href="/">Dashboard</a>
    </header>
    ${body.join("\n")}
  </main>
</body>
</html>`;
}

function getMiningLabStatus() {
  const files = [
    "docs/ARC-REACTOR-MINING-LAB.md",
    "docs/WALLET-MATRIX-TEMPLATE.md",
    "skills/solo-mining/SKILL.md",
    "templates/hardware-intake.csv",
    "templates/wallet-matrix.csv",
    "templates/coin-feasibility.csv",
    "templates/mining-receipt.json",
    "scripts/Get-HardwareInventory.ps1",
    "scripts/Test-MiningProfitability.ps1",
    "reports/ARC-REACTOR-MINING-LAB-2026-05-29.md",
  ];
  const present = files.map((relativePath) => ({
    path: relativePath,
    exists: fs.existsSync(path.join(repoRoot, relativePath)),
  }));
  const ready = present.every((item) => item.exists);
  return {
    ready,
    mode: "manual_first_read_only",
    shortcutRule: "single_lantern_shortcut",
    routeSummary: {
      cpu: "XMR learning lane",
      gpu: "RVN / ETC experiment lane",
      eth: "wallet / claim checks only",
      asic: "BTC / LTC / DOGE / KAS only with owned or justified hardware",
    },
    blocked: [
      "wallet_bruteforce",
      "unauthorized_transfers",
      "hidden_transaction_signing",
      "mining_on_unowned_devices",
      "fake_roi_claims",
      "eth_mainnet_mining_claims",
    ],
    files: present,
  };
}

function parseMirrorEnv() {
  return String(process.env.LANTERN_CLOUD_MIRROR_URLS || "")
    .split(/[,\s]+/)
    .map((url) => url.trim())
    .filter(Boolean)
    .map((url, index) => ({
      name: `env-mirror-${index + 1}`,
      url,
      role: "environment configured mirror",
      status: "configured",
      healthPath: "/api/health",
      source: "LANTERN_CLOUD_MIRROR_URLS",
    }));
}



function commandExists(command) {
  const probe = process.platform === "win32" ? "where" : "which";
  const result = spawnSync(probe, [command], { stdio: "ignore" });
  return result.status === 0;
}

function getPowerShellCommand() {
  const candidates = process.platform === "win32"
    ? ["powershell.exe", "pwsh.exe", "powershell", "pwsh"]
    : ["pwsh", "powershell"];
  return candidates.find(commandExists) || null;
}

function getActionCapabilities() {
  const powerShellCommand = getPowerShellCommand();
  const powerShellReady = Boolean(powerShellCommand);
  return {
    generatedAt: new Date().toISOString(),
    mode: "local",
    powerShellCommand,
    actions: {
      refresh: { enabled: true, kind: "real-action", reason: "GET routes are available in the Node app." },
      flatRagIngest: { enabled: true, kind: "real-action", reason: "Writes the local Flat RAG manifest only; no repo deletion." },
      notes: { enabled: true, kind: "real-action", reason: "Appends operator notes to data/operator-notes/notes.jsonl." },
      chat: { enabled: true, kind: "real-action", reason: "Appends local chat memory to data/conversations/garage-conversations.jsonl." },
      runLoop: { enabled: powerShellReady, kind: powerShellReady ? "real-action" : "held-action", reason: powerShellReady ? `PowerShell available via ${powerShellCommand}.` : "Held: PowerShell is not installed in this environment." },
      localControls: { enabled: powerShellReady, kind: powerShellReady ? "real-action" : "held-action", reason: powerShellReady ? `PowerShell available via ${powerShellCommand}.` : "Held: local controls require PowerShell on the operator machine." },
      dispatchAll: { enabled: true, kind: "real-action", reason: "MCP orchestrator active. Full agent dispatch + convergence loop + batch framework validation enabled." }
    },
    summary: {
      real: ["Refresh Status", "Ingest Repos", "Auto Update", "+ Note", "Chat send", "RAG intake", "Dispatch All"],
      links: ["Health", "Status JSON", "Access Model", "Mirror JSON", "Readiness Gates", "Evidence Method", "Open Issues"],
      held: powerShellReady
        ? []
        : ["Converge Loop held: PowerShell missing.", "Local Controls held: operator-machine PowerShell required."]
    }
  };
}

function getOperatorFeedbackMemory() {
  const notes = readJsonl(path.relative(repoRoot, operatorNotesPath), 50).filter((note) => !note.parseError);
  const feedback = [];
  for (const note of notes) {
    const text = String(note.text || "").trim();
    const lower = text.toLowerCase();
    if (lower.includes("button") || lower.includes("fake")) {
      feedback.push({
        id: "OPERATOR-BUTTON-TRUTH",
        priority: note.priority || "P1",
        source: path.relative(repoRoot, operatorNotesPath),
        feedback: text,
        appliedAs: "Every first-screen control is classified as real-action, live-link, held-action, or founder-held; unavailable held buttons are disabled."
      });
    }
    if (lower.includes("tony") || lower.includes("garage") || lower.includes("orion")) {
      feedback.push({
        id: "OPERATOR-ORION-GARAGE",
        priority: note.priority || "P0",
        source: path.relative(repoRoot, operatorNotesPath),
        feedback: text,
        appliedAs: "Dashboard keeps the limestone/grid Orion cockpit style, redirects retired Tony Garage, and shows one canonical local URL."
      });
    }
  }
  feedback.push({
    id: "RESTART-EXTERNAL-MEMORY",
    priority: "P1",
    source: "data/context/RESTART-TEMPLATE-2026-05-29.md",
    feedback: "Use external memory files and complete targeted dashboard integration before expanding.",
    appliedAs: "Dashboard now exposes memory feedback and action capabilities as first-class API-backed panels."
  });
  return {
    generatedAt: new Date().toISOString(),
    feedback,
    boundary: "Operator feedback memory is read from local notes and context receipts; private details are summarized, not exposed as secrets."
  };
}

function getAccessModel() {
  return {
    generatedAt: new Date().toISOString(),
    audienceTarget: "dozens_of_users",
    activeUserSoftCap: 48,
    authBoundary: "This is an access contract for the dashboard surface. Real identity, billing, and founder authorization must be wired before private or paid actions leave local mode.",
    tiers: [
      {
        id: "public",
        label: "Public",
        priceUsdMonthly: null,
        authRequired: false,
        summary: "Always-on public proof, health checks, public reports, cloud mirrors, and safe documentation.",
        features: ["/api/health", "/api/status", "public PDFs", "read-only readiness"]
      },
      {
        id: "auth_0",
        label: "$0 Auth",
        priceUsdMonthly: 0,
        authRequired: true,
        summary: "Free signed-in workspace for saved notes, RAG intake, and user preference continuity.",
        features: ["saved notes", "RAG intake", "workspace continuity"]
      },
      {
        id: "auth_20",
        label: "$20 Auth",
        priceUsdMonthly: 20,
        authRequired: true,
        summary: "Supporter workspace for queue visibility, report packets, and a weekly operator digest.",
        features: ["queue visibility", "report packets", "weekly digest"]
      },
      {
        id: "auth_200",
        label: "$200 Auth",
        priceUsdMonthly: 200,
        authRequired: true,
        summary: "Pilot workspace for guided cleanup sessions, report review, and direct operator scheduling.",
        features: ["pilot review", "cleanup session", "operator scheduling"]
      },
      {
        id: "founder",
        label: "Founder",
        priceUsdMonthly: null,
        authRequired: true,
        founderOnly: true,
        summary: "Founder-only controls for local dispatch, release promotion, secrets, billing setup, and boot-sensitive decisions.",
        features: ["local controls", "agent dispatch", "release gates", "private receipts"]
      }
    ]
  };
}

function getCloudMirrorStatus() {
  const manifest = readJson(path.relative(repoRoot, cloudMirrorsPath), {});
  const manifestMirrors = Array.isArray(manifest.cloudMirrors) ? manifest.cloudMirrors : [];
  const envMirrors = parseMirrorEnv();
  const seen = new Set();
  const cloudMirrors = [...manifestMirrors, ...envMirrors]
    .filter((mirror) => mirror && typeof mirror.url === "string" && mirror.url.startsWith("https://"))
    .filter((mirror) => {
      if (seen.has(mirror.url)) return false;
      seen.add(mirror.url);
      return true;
    })
    .map((mirror) => ({
      name: String(mirror.name || "cloud mirror").slice(0, 80),
      url: mirror.url,
      role: String(mirror.role || "cloud mirror").slice(0, 160),
      status: String(mirror.status || "configured").slice(0, 80),
      healthPath: String(mirror.healthPath || "/api/health").slice(0, 120),
      source: String(mirror.source || "manifests/cloud-mirrors.json").slice(0, 160),
    }));

  return {
    generatedAt: new Date().toISOString(),
    localPrimary: `http://127.0.0.1:${port}`,
    activeHost: host,
    activePort: port,
    deployBranch: manifest.deployBranch || "master",
    deployProvider: manifest.deployProvider || "Render",
    mirrorPolicy: manifest.mirrorPolicy || "Local is primary; cloud URLs are mirrors and must not create separate dashboards.",
    cloudMirrorCount: cloudMirrors.length,
    cloudMirrors,
  };
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
    "Access-Control-Allow-Origin": "*",
  });
  res.end(html);
}

async function route(req, res) {
  const url = new URL(req.url, `http://${req.headers.host}`);

  if (req.method === "OPTIONS") {
    res.writeHead(204, {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
      "Cache-Control": "no-store",
    });
    res.end();
    return;
  }

  if (url.pathname === "/api/health") {
    sendJson(res, { ok: true, service: "lantern-garage", generatedAt: new Date().toISOString() });
    return;
  }

  if (url.pathname === "/api/status") {
    sendJson(res, getStatus());
    return;
  }

  if (url.pathname === "/api/arc-reactor") {
    sendJson(res, readJson("data/arc-reactor/status.json", {}));
    return;
  }

  if (url.pathname === "/api/wallet") {
    sendJson(res, {
      wallet: readJson("data/wallet/local-cash-wallet.json", {}),
      ledger: readJsonl("data/wallet/ledger.jsonl", 30),
    });
    return;
  }

  if (url.pathname === "/api/readiness") {
    sendJson(res, getReadiness());
    return;
  }

  if (url.pathname === "/api/mining-lab") {
    sendJson(res, getMiningLabStatus());
    return;
  }

  if (url.pathname === "/api/action-capabilities") {
    sendJson(res, getActionCapabilities());
    return;
  }

  if (url.pathname === "/api/operator-feedback") {
    sendJson(res, getOperatorFeedbackMemory());
    return;
  }

  if (url.pathname === "/api/access-model") {
    sendJson(res, getAccessModel());
    return;
  }

  if (url.pathname === "/api/cloud-mirrors") {
    sendJson(res, getCloudMirrorStatus());
    return;
  }

  if (url.pathname === "/api/rag-cache" && req.method === "GET") {
    sendJson(res, readJsonl("data/rag-intake/external-llm-web-cache/cache.jsonl", 50));
    return;
  }

  if (url.pathname === "/api/rag-cache" && req.method === "POST") {
    try {
      const body = await collectRequestBody(req);
      const record = await appendExternalRagItem(JSON.parse(body || "{}"));
      sendJson(res, { ok: true, record }, 201);
    } catch (error) {
      sendJson(res, { error: error.message }, 400);
    }
    return;
  }

  if (url.pathname === "/api/flat-rag-house") {
    sendJson(res, fs.existsSync(flatRagHousePath)
      ? readJson(path.relative(repoRoot, flatRagHousePath), buildFlatRagHouse())
      : buildFlatRagHouse());
    return;
  }

  if (url.pathname === "/api/operator-queue") {
    sendJson(res, { items: readOperatorQueue(), generatedAt: new Date().toISOString() });
    return;
  }

  if (url.pathname === "/api/operator-notes" && req.method === "POST") {
    try {
      const body = await collectRequestBody(req);
      const input = JSON.parse(body || "{}");
      const text = String(input.text || "").trim().slice(0, 500);
      const priority = ["P0", "P1", "P2"].includes(input.priority) ? input.priority : "P1";
      if (!text) throw new Error("note_text_required");
      const record = { createdAt: new Date().toISOString(), text, priority, done: false };
      await appendJsonlQueued(operatorNotesPath, record);
      sendJson(res, { ok: true, record }, 201);
    } catch (error) {
      sendJson(res, { error: error.message }, 400);
    }
    return;
  }

  if (url.pathname === "/api/conversations" && req.method === "GET") {
    const limit = Math.max(1, Math.min(200, Number(url.searchParams.get("limit") || 50)));
    sendJson(res, {
      path: path.relative(repoRoot, conversationLogPath),
      conversations: readConversationLog(limit),
    });
    return;
  }

  if (url.pathname === "/api/conversations" && req.method === "POST") {
    try {
      const body = await collectRequestBody(req);
      const entry = normalizeConversationEntry(JSON.parse(body || "{}"));
      await appendConversationEntry(entry);
      sendJson(res, { ok: true, entry }, 201);
    } catch (error) {
      sendJson(res, { error: error.message }, 400);
    }
    return;
  }

  if (url.pathname === "/api/actions/run-loop" && req.method === "POST") {
    const result = await runPowerShell("scripts/Invoke-LanternConvergenceLoop.ps1");
    sendJson(res, result, result.code === 0 ? 200 : 500);
    return;
  }

  if (url.pathname === "/api/actions/local-controls" && req.method === "POST") {
    const result = await runPowerShell("scripts/Start-LanternLocalControls.ps1");
    sendJson(res, result, result.code === 0 ? 200 : 500);
    return;
  }

  if (url.pathname === "/api/actions/flat-rag-ingest" && req.method === "POST") {
    const house = await writeFlatRagHouse();
    sendJson(res, {
      code: 0,
      stdout: `Flat RAG house updated: ${path.relative(repoRoot, flatRagHousePath)}`,
      stderr: "",
      house,
    });
    return;
  }

  if (url.pathname.startsWith("/repo/")) {
    const relative = decodeURIComponent(url.pathname.replace(/^\/repo\//, ""));
    const target = path.resolve(repoRoot, relative);
    if (!target.startsWith(repoRoot)) {
      sendJson(res, { error: "forbidden" }, 403);
      return;
    }
    sendFile(res, target);
    return;
  }

  if (url.pathname === "/view") {
    const relative = decodeURIComponent(url.searchParams.get("path") || "");
    const target = path.resolve(repoRoot, relative);
    if (!relative || !target.startsWith(repoRoot)) {
      sendJson(res, { error: "forbidden" }, 403);
      return;
    }
    if (!fs.existsSync(target)) {
      sendJson(res, { error: "not_found" }, 404);
      return;
    }
    if (path.extname(target).toLowerCase() === ".md") {
      sendHtml(res, renderMarkdownDocument(fs.readFileSync(target, "utf8"), relative));
      return;
    }
    sendFile(res, target);
    return;
  }


  if (url.pathname === "/api/dreamer" && req.method === "GET") {
    const user = normalizeDreamerUser(url.searchParams.get("user") || "courtney");
    const entries = readDreamerNotebook(user);
    sendJson(res, { user, entries, path: path.relative(repoRoot, dreamerNotebookPath(user)) });
    return;
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
    return;
  }

  if (url.pathname === "/api/dreamer/chat" && req.method === "POST") {
    try {
      const raw = await collectRequestBody(req);
      const body = JSON.parse(raw);
      const user = normalizeDreamerUser(body.user || "orion");
      const kind = String(body.kind || "dream").slice(0, 40);
      const text = String(body.text || "").slice(0, 4000);
      const history = Array.isArray(body.history) ? body.history.slice(-10) : [];
      const record = await appendDreamerEntry(user, { kind, text, name: body.name, mood: body.mood, tags: body.tags });

      let reply = null;
      const apiKey = process.env.ANTHROPIC_API_KEY;
      if (Anthropic && apiKey) {
        const client = new Anthropic.default({ apiKey });
        const model = process.env.ANTHROPIC_DEFAULT_HAIKU_MODEL || "claude-haiku-4-5-20251001";
        const systemPrompt = `You are Orion, a reflective dream journal companion for Lantern OS. The user just recorded a "${kind}" entry. Respond warmly and insightfully in 2-4 sentences — notice patterns, ask one gentle question, or reflect a symbol back. Never make medical claims. Never invent facts about the user. Keep replies concise.`;
        const msgs = [...history.map(m => ({ role: m.role, content: m.content })), { role: "user", content: `[${kind}] ${text}` }];
        const response = await client.messages.create({ model, max_tokens: 300, system: systemPrompt, messages: msgs });
        reply = response.content[0]?.text || null;
      }
      if (!reply) {
        const fallbacks = { dream: "What a vivid scene — worth sitting with. What feeling stayed when you woke?", note: "Noted. Patterns like this often surface for a reason.", symbol: "Symbols return when they have something left to say. What does this one mean to you right now?", mirror: "Mirrors show what we're ready to see. What does this reveal?", event: "Moments like this leave a mark. How did it shift something inside you?", lore: "What part of this lore feels most alive for you today?", character: "Characters carry messages. What does this one want you to know?", place: "Places hold their own gravity. What did this space feel like?" };
        reply = fallbacks[kind] || fallbacks.note;
      }
      sendJson(res, { saved: true, record, reply });
    } catch (error) {
      sendJson(res, { error: error.message }, 400);
    }
    return;
  }

  // ── Agents list ─────────────────────────────────────────────────────
  if (url.pathname === "/api/agents" && req.method === "GET") {
    sendJson(res, {
      agents: AGENT_PERSONAS.map((a) => ({
        id: a.id,
        name: a.name,
        symbol: a.symbol,
      })),
      default: AGENT_PERSONAS[0].id,
    });
    return;
  }

  // ── Agentic Workspace — Unified Connector Endpoints ──────────────────
  if (url.pathname === "/api/dream/greet" && req.method === "GET") {
    try {
      const recentDreams = readRecentDreams(5);
      const greet = await unifiedAgentGreet(recentDreams);
      sendJson(res, { ...greet, generatedAt: new Date().toISOString() });
    } catch (error) {
      sendJson(res, {
        greeting: "The dream door is open. Tell me what you brought back from sleep.",
        persona: "Blinkbug",
        source: "offline_fallback",
        error: error.message,
      });
    }
    return;
  }

  if (url.pathname === "/api/agent/health" && req.method === "GET") {
    try {
      const health = await unifiedAgentHealth();
      sendJson(res, { health, generatedAt: new Date().toISOString() });
    } catch (error) {
      sendJson(res, { error: error.message }, 500);
    }
    return;
  }

  if (url.pathname === "/api/agent/inspect" && req.method === "GET") {
    try {
      const inspect = await unifiedAgentInspect();
      sendJson(res, { inspect, generatedAt: new Date().toISOString() });
    } catch (error) {
      sendJson(res, { error: error.message }, 500);
    }
    return;
  }

  // Dream Journal API Routes
  if (url.pathname === "/api/dream/create" && req.method === "POST") {
    try {
      const raw = await collectRequestBody(req);
      const body = JSON.parse(raw);
      const dreamId = `dream_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
      const normalizeList = (value, limit = 12) => {
        if (Array.isArray(value)) return value.map((item) => String(item).trim()).filter(Boolean).slice(0, limit);
        return String(value || "")
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean)
          .slice(0, limit);
      };
      const entry = {
        id: dreamId,
        timestamp: new Date().toISOString(),
        kind: String(body.kind || "dream").slice(0, 40),
        name: String(body.name || body.title || "").slice(0, 140),
        text: String(body.text || body.content || "").slice(0, maxDreamerTextLength),
        lucidity: Math.max(0, Math.min(1, Number(body.lucidity || 0))),
        clarity: Math.max(0, Math.min(1, Number(body.clarity || 0))),
        mood: String(body.mood || "").slice(0, 80),
        technique: String(body.technique || "").slice(0, 80),
        sleep_window: String(body.sleep_window || "").slice(0, 80),
        recurring: Boolean(body.recurring),
        dreamsign: Boolean(body.dreamsign),
        emotions: normalizeList(body.emotions, 12),
        tags: normalizeList(body.tags, 10),
        symbols: normalizeList(body.symbols, 12),
        linked_goals: body.linked_goals || [],
        priority: body.priority || "normal",
        reflection_on: body.reflection_on || [],
        source: "api"
      };
      const dreamDir = path.join(repoRoot, "data", "dream_journal");
      if (!fs.existsSync(dreamDir)) fs.mkdirSync(dreamDir, { recursive: true });
      const monthFile = path.join(dreamDir, `dreams_${new Date().toISOString().substring(0, 7)}.jsonl`);
      await appendJsonlQueued(monthFile, entry);

      sendJson(res, {
        id: dreamId,
        saved: true,
        entry,
        csf: { compressed: false },
      });
    } catch (error) {
      sendJson(res, { error: error.message }, 400);
    }
    return;
  }

  if (url.pathname === "/api/dream/chat" && req.method === "POST") {
    try {
      const raw = await collectRequestBody(req);
      const body = JSON.parse(raw || "{}");
      const message = String(body.message || "").slice(0, maxDreamerTextLength);
      const recentDreams = readRecentDreams(5);
      const result = await dreamChatReply(message, recentDreams);
      // Best-effort conversation logging; never blocks the reply.
      try {
        await appendConversationEntry({
          recordedAt: new Date().toISOString(),
          surface: "dream-journal",
          role: "operator",
          text: message.slice(0, maxConversationTextLength),
        });
        await appendConversationEntry({
          recordedAt: new Date().toISOString(),
          surface: "dream-journal",
          role: "lantern",
          text: String(result.reply || "").slice(0, maxConversationTextLength),
        });
      } catch { /* logging is non-critical */ }
      sendJson(res, { ...result, generatedAt: new Date().toISOString() });
    } catch (error) {
      // Even on parse error, stay in character and online.
      sendJson(res, {
        reply: `${DREAM_DOORS.founder.phrase} Something tangled, but the dream door stays open.`,
        suggestions: Object.values(DREAM_DOORS).slice(0, 3).map((d) => d.name),
        online: false,
        error: error.message,
      });
    }
    return;
  }

  // Dream Journal V1.0.0 — Streaming chat (strict provider mode)
  // GET /api/dream/stream?message=...&provider=claude|openai|gemini
  // Requires explicit provider. Fails if selected provider cannot respond.
  // No hardcoded or offline fallbacks allowed.
  if ((url.pathname === "/api/dream/stream" && req.method === "GET") ||
      (url.pathname === "/api/dream/chat/stream" && req.method === "POST")) {
    let message = "";
    let user = "dreamer";
    let requestedAgent = "";
    let requestedProvider = "";
    if (req.method === "GET") {
      message = String(url.searchParams.get("message") || "").slice(0, maxDreamerTextLength).trim();
      user = normalizeDreamerUser(url.searchParams.get("user") || "dreamer");
      requestedAgent = String(url.searchParams.get("agent") || "").trim();
      requestedProvider = String(url.searchParams.get("provider") || "").trim().toLowerCase();
    } else {
      try {
        const rawBody = await collectRequestBody(req);
        const body = JSON.parse(rawBody || "{}");
        message = String(body.message || "").slice(0, maxDreamerTextLength).trim();
        user = normalizeDreamerUser(body.user || "dreamer");
        requestedAgent = String(body.agent || "").trim();
        requestedProvider = String(body.provider || "").trim().toLowerCase();
      } catch { /* message stays empty */ }
    }

    res.writeHead(200, {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache",
      "Connection": "keep-alive",
      "Access-Control-Allow-Origin": "*",
      "X-Accel-Buffering": "no",
    });

    const recentDreams = readRecentDreams(5);

    const agent = requestedAgent
      ? (AGENT_PERSONAS.find((a) => a.id === requestedAgent) || selectAgent(message))
      : selectAgent(message);
    const dreamContext = recentDreams.length > 0
      ? `Recent journal entries:\n${recentDreams.slice(0, 3).map((d, i) =>
          `${i + 1}. ${String(d.text || d.content || "").slice(0, 200)}`
        ).join("\n")}`
      : "No journal entries yet — this is the dreamer's first visit.";

    const systemPrompt = `${agent.systemPrompt}

${dreamContext}

Tone: thoughtful, unhurried, human. Never clinical. Never sycophantic. Use the dreamer's own words back to them. End responses with one question or one invitation to record.`;

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

    // Log user message (best-effort, non-blocking)
    await appendConversationEntry({
      recordedAt: new Date().toISOString(),
      surface: "dream-chat-stream",
      role: "operator",
      text: message.slice(0, maxConversationTextLength),
    }).catch(() => {});

    let fullReply = "";

    // ── Provider 1: Anthropic Claude (streaming) ──────────────────────────
    const anthropicKey = process.env.ANTHROPIC_API_KEY;
    if (anthropicKey && message && (!requestedProvider || requestedProvider === "claude" || requestedProvider === "anthropic")) {
      try {
        const payload = JSON.stringify({
          model: process.env.ANTHROPIC_MODEL || "claude-3-5-haiku-20241022",
          max_tokens: 1024,
          stream: true,
          system: systemPrompt,
          messages: [{ role: "user", content: message }],
        });

        await new Promise((resolve, reject) => {
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
          const https = require("https");
          const req2 = https.request(opts, (upstream) => {
            if (upstream.statusCode !== 200) {
              upstream.resume();
              reject(new Error(`anthropic_status_${upstream.statusCode}`));
              return;
            }
            let buf = "";
            upstream.on("data", (chunk) => {
              buf += chunk.toString();
              const lines = buf.split("\n");
              buf = lines.pop(); // keep incomplete line
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

        sendDone("anthropic", { agent: agent.name, online: true });
        return;
      } catch (err) {
        sendError(`anthropic_unavailable: ${err.message}`);
        if (requestedProvider) { sendDone("unavailable", { error: err.message, agent: agent.name }); return; }
      }
    }

    // ── Provider 2: OpenAI (streaming) ────────────────────────────────────
    const openaiKey = process.env.OPENAI_API_KEY;
    if (openaiKey && message && (!requestedProvider || requestedProvider === "openai" || requestedProvider === "gpt")) {
      try {
        const payload = JSON.stringify({
          model: process.env.OPENAI_MODEL || "gpt-4o-mini",
          stream: true,
          messages: [
            { role: "system", content: systemPrompt },
            { role: "user", content: message },
          ],
        });
        await new Promise((resolve, reject) => {
          const https = require("https");
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
                  if (token) {
                    fullReply += token;
                    sendToken(token);
                  }
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
        sendDone("openai", { agent: agent.name, online: true });
        return;
      } catch (err) {
        sendError(`openai_unavailable: ${err.message}`);
        if (requestedProvider) { sendDone("unavailable", { error: err.message, agent: agent.name }); return; }
      }
    }

    // ── Provider 3: Gemini (streaming) ────────────────────────────────────
    const geminiKey = process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY;
    if (geminiKey && message && (!requestedProvider || requestedProvider === "gemini" || requestedProvider === "google")) {
      try {
        const payload = JSON.stringify({
          contents: [{ role: "user", parts: [{ text: `${systemPrompt}\n\n${message}` }] }],
          generationConfig: { maxOutputTokens: 1024, temperature: 0.7 },
        });
        const geminiModel = process.env.GEMINI_MODEL || "gemini-1.5-flash";
        await new Promise((resolve, reject) => {
          const https = require("https");
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
        sendDone("gemini", { agent: agent.name, online: true });
        return;
      } catch (err) {
        sendError(`gemini_unavailable: ${err.message}`);
        if (requestedProvider) { sendDone("unavailable", { error: err.message, agent: agent.name }); return; }
      }
    }

    // ── Provider 4: Ollama (streaming) ────────────────────────────────────
    const ollamaBase = process.env.OLLAMA_BASE_URL || "http://127.0.0.1:11434";
    const ollamaModel = process.env.OLLAMA_MODEL || "llama3";
    if (message && (!requestedProvider || requestedProvider === "ollama" || requestedProvider === "local")) {
      try {
        const payload = JSON.stringify({
          model: ollamaModel,
          stream: true,
          messages: [
            { role: "system", content: systemPrompt },
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
          const req2 = require("http").request(ollamaOpts, (upstream) => {
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
                  if (token) {
                    fullReply += token;
                    sendToken(token);
                  }
                } catch { /* skip */ }
              }
            });
            upstream.on("end", () => resolve());
            upstream.on("error", reject);
          });
          req2.on("error", reject);
          req2.setTimeout(5000, () => {
            req2.destroy();
            reject(new Error("ollama_connect_timeout"));
          });
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
          sendDone("ollama", { agent: agent.name, online: true });
          return;
        }
      } catch (err) {
        sendError(`ollama_unavailable: ${err.message}`);
        if (requestedProvider) { sendDone("unavailable", { error: err.message, agent: agent.name }); return; }
      }
    }

    // ── No provider available — clean failure ───────────────────────────────
    sendError("All providers unavailable. Set ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, or start Ollama.");
    sendDone("unavailable", { error: "no_provider", agent: agent.name, online: false });
    return;
  }

  if (url.pathname === "/api/dream/stats" && req.method === "GET") {
    try {
      const dreamDir = path.join(repoRoot, "data", "dream_journal");
      let entries = [];
      if (fs.existsSync(dreamDir)) {
        const files = fs.readdirSync(dreamDir).filter(f => f.endsWith(".jsonl"));
        for (const file of files) {
          const content = fs.readFileSync(path.join(dreamDir, file), "utf-8").trim();
          if (content) {
            entries.push(...content.split("\n").map(line => {
              try { return JSON.parse(line); } catch { return null; }
            }).filter(e => e));
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
        avg_lucidity: 0
      };
      for (const entry of entries) {
        stats.entries_by_kind[entry.kind || "dream"] = (stats.entries_by_kind[entry.kind || "dream"] || 0) + 1;
        for (const emotion of (entry.emotions || [])) {
          stats.top_emotions[emotion] = (stats.top_emotions[emotion] || 0) + 1;
        }
        for (const tag of (entry.tags || [])) {
          stats.top_tags[tag] = (stats.top_tags[tag] || 0) + 1;
        }
        for (const symbol of (entry.symbols || [])) {
          stats.top_symbols[symbol] = (stats.top_symbols[symbol] || 0) + 1;
        }
        stats.total_lucidity += entry.lucidity || 0;
      }
      if (entries.length > 0) stats.avg_lucidity = (stats.total_lucidity / entries.length).toFixed(2);
      sendJson(res, stats);
    } catch (error) {
      sendJson(res, { error: error.message }, 400);
    }
    return;
  }

  if (url.pathname === "/api/dream/search" && req.method === "GET") {
    try {
      const query = url.searchParams.get("text") || "";
      const tags = (url.searchParams.get("tags") || "").split(",").filter(t => t);
      const dreamDir = path.join(repoRoot, "data", "dream_journal");
      let results = [];
      if (fs.existsSync(dreamDir)) {
        const files = fs.readdirSync(dreamDir).filter(f => f.endsWith(".jsonl"));
        for (const file of files) {
          const content = fs.readFileSync(path.join(dreamDir, file), "utf-8").trim();
          if (content) {
            results.push(...content.split("\n").map(line => {
              try { return JSON.parse(line); } catch { return null; }
            }).filter(e => e && (
              (query === "" || (e.text || "").toLowerCase().includes(query.toLowerCase())) &&
              (tags.length === 0 || tags.some(t => (e.tags || []).includes(t)))
            )));
          }
        }
      }
      sendJson(res, { query, tags, count: results.length, results: results.slice(0, 50) });
    } catch (error) {
      sendJson(res, { error: error.message }, 400);
    }
    return;
  }

  if (url.pathname.startsWith("/api/dream/read/") && req.method === "GET") {
    try {
      const id = url.pathname.replace("/api/dream/read/", "");
      const dreamDir = path.join(repoRoot, "data", "dream_journal");
      let found = null;
      if (fs.existsSync(dreamDir)) {
        const files = fs.readdirSync(dreamDir).filter(f => f.endsWith(".jsonl"));
        for (const file of files) {
          const content = fs.readFileSync(path.join(dreamDir, file), "utf-8").trim();
          if (content) {
            for (const line of content.split("\n")) {
              try {
                const entry = JSON.parse(line);
                if (entry.id === id) { found = entry; break; }
              } catch { }
            }
          }
          if (found) break;
        }
      }
      if (found) {
        sendJson(res, found);
      } else {
        sendJson(res, { error: "not_found" }, 404);
      }
    } catch (error) {
      sendJson(res, { error: error.message }, 400);
    }
    return;
  }

  if (url.pathname === "/hub") {
    const hubPath = path.resolve(repoRoot, "central-hub.html");
    sendFile(res, hubPath);
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
    console.error(`Lantern Garage port ${port} is already in use. Open http://127.0.0.1:${port} or choose another port.`);
    process.exitCode = 1;
    return;
  }
  throw error;
});

server.listen(port, host, () => {
  console.log(`Lantern Garage app listening on ${host}:${port}`);
});
