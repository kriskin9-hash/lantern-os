const https = require("https");
const http = require("http");
const path = require("path");
const { AGENT_PERSONAS, DREAM_DOORS, selectAgent, parseBangCommand } = require("./dream-chat");
const { readRecentDreams, normalizeDreamerUser } = require("./dreamer-store");
const { appendConversationEntry } = require("./conversation-store");
const { getProviderState, recordProviderSuccess, recordProviderFailure } = require("./provider-cache");
const { swarmOrchestrate } = require("./swarm-orchestrator");
const { unifiedAgentStreamSSE } = require("./unified-agent");
const sse = require("./stream-chat/sse");
const { parseStreamChatRequest } = require("./stream-chat/request");
const { formatCSFContextForPrompt, saveDoorChoice } = require("./csf-memory");
const { route: converganceRoute, buildBehaviorPreamble } = require("./convergance-os/model-router");
const { THREE_DOORS_PREAMBLE } = require("./convergance-os/profiles");
const { generateDoorSceneImage } = require("./image-generation");

const repoRoot = path.resolve(__dirname, "../../../");

const maxConversationTextLength = 4000;

// Fallback doors when AI omits the marker or provider fails
const FALLBACK_DOORS = ["Tell me more about that", "What happened next?", "How are you feeling about it?"];

// Conversation history compaction thresholds
const FULL_FIDELITY_RECENT_TURNS = 2;
const MID_FIDELITY_TURNS = 2;
const MID_FIDELITY_CHAR_LIMIT = 200;
const LOW_FIDELITY_WORD_LIMIT = 10;

// Conversation history compaction: tiered summarization to reduce provider token costs.
// Only compacts turns older than the most recent FULL_FIDELITY_RECENT_TURNS exchanges;
// never re-compacts already-compacted text (FlowKV principle).
function compactHistory(history) {
  if (!Array.isArray(history) || history.length === 0) return [];
  return history.map((h, i) => {
    const text = String(h.text != null ? h.text : (h.content != null ? h.content : ""));
    const role = h.role || "user";
    if (i >= history.length - FULL_FIDELITY_RECENT_TURNS) {
      return { role, text }; // Full fidelity
    }
    if (i >= history.length - FULL_FIDELITY_RECENT_TURNS - MID_FIDELITY_TURNS) {
      const truncated = text.length > MID_FIDELITY_CHAR_LIMIT
        ? text.slice(0, MID_FIDELITY_CHAR_LIMIT) + "…"
        : text;
      return { role, text: truncated };
    }
    // Low fidelity: first N words only
    const words = text.trim().split(/\s+/).filter(Boolean).slice(0, LOW_FIDELITY_WORD_LIMIT).join(" ");
    const roleLabel = role === "assistant" ? "Lantern" : "Dreamer";
    const summary = words.length > 0 ? `[${roleLabel}: ${words}…]` : `[${roleLabel}]`;
    return { role, text: summary };
  });
}

// Build the provider messages array from compacted history + current message.
// Single source of truth — all providers call this instead of inlining history.map.
function buildProviderMessages(systemPrompt, compacted, currentMessage) {
  return [
    { role: "system", content: systemPrompt },
    ...compacted.map(h => ({ role: h.role, content: h.text })),
    { role: "user", content: currentMessage },
  ];
}

// Parse [DOORS: A | B | C] out of the full reply and return cleaned text + doors array.
// Local models (Ollama) sometimes use commas instead of pipes — fall back gracefully.
function extractDoors(text) {
  // Match complete [DOORS: A | B | C] or incomplete [DOORS: A | B | C (no closing bracket)
  const match = text.match(/\[DOORS:\s*([^\]]+)\]?/i);
  if (!match) return { cleanText: text.trim(), doors: [] };
  let doors = match[1].split("|").map(d => d.trim()).filter(Boolean).slice(0, 3);
  // Fallback: if pipe-split didn't produce 3 doors, try comma-before-capital split
  if (doors.length < 3) {
    const commaSplit = match[1].split(/,\s*(?=[A-Z])/).map(d => d.trim()).filter(Boolean).slice(0, 3);
    if (commaSplit.length > doors.length) doors = commaSplit;
  }
  const cleanText = text.replace(/\[DOORS:[^\]]*\]?/i, "").replace(/\n{3,}/g, "\n\n").trim();
  return { cleanText, doors };
}

function doorsOrFallback(text, isKeystoneDebug = false) {
  if (isKeystoneDebug) return { cleanText: text.trim(), suggestions: [] };
  const { cleanText, doors } = extractDoors(text);
  // Always return exactly 3 suggestions. Pad with fallbacks if model gave fewer than 3.
  let finalDoors;
  if (doors.length >= 3) {
    finalDoors = doors.slice(0, 3);
  } else if (doors.length > 0) {
    finalDoors = [...doors, ...FALLBACK_DOORS].slice(0, 3);
  } else {
    finalDoors = FALLBACK_DOORS;
  }
  if (doors.length > 0) {
    try { saveDoorChoice(null, finalDoors); } catch {}
  }
  return { cleanText, suggestions: finalDoors };
}

// Non-blocking image generation sidecar for Three Doors mode
function triggerImageGeneration({ cleanText, suggestions, surfaceMode, symbolMesh }) {
  if (surfaceMode !== "three-doors") return null;
  
  const entryId = Date.now().toString();
  generateDoorSceneImage({ cleanText, doors: suggestions, symbolMesh, entryId })
    .then(result => {
      // Image generation completes asynchronously; failure is non-blocking
    })
    .catch(err => {
      // Image generation errors are non-blocking
    });
  
  return entryId;
}

async function handleStreamChat(req, url, res) {
  const { collectRequestBody } = require("./http-utils");
  const parsed = await parseStreamChatRequest(req, url, {
    normalizeDreamerUser,
    collectRequestBody,
  });
  let { message, user, requestedAgent, requestedProvider, history, mcpFlag } = parsed;

  // Surface mode: dream-chat (default) or three-doors
  let surfaceMode = "dream-chat";

  // Handle bang commands
  const cmd = parseBangCommand(message);
  if (cmd) {
    // Three Doors mode
    if (cmd.name === "three-doors" || cmd.name === "threedoors" || cmd.name === "three_doors") {
      surfaceMode = "three-doors";
      message = message.replace(/!(?:three-doors|threedoors|three_doors)\b/gi, "").trim() || "begin";
    }

    if (cmd.name === "swarm") {
      // Parse: !swarm <mode> <job> <message...>
      // or:   !swarm <job> <message...>  (default mode = single)
      const parts = cmd.args.split(/\s+/);
      const knownModes = ["single", "parallel", "consensus", "council"];
      const knownJobs = ["chat", "coding", "reasoning", "vision", "summarize", "creative", "research"];
      let mode = "single";
      let job = "chat";
      let swarmMessage = cmd.args;
      if (knownModes.includes(parts[0])) {
        mode = parts.shift();
      }
      if (knownJobs.includes(parts[0])) {
        job = parts.shift();
      }
      swarmMessage = parts.join(" ") || "Hello swarm";

      res.writeHead(200, {
        "Content-Type": "text/event-stream; charset=utf-8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*",
        "X-Accel-Buffering": "no",
      });
      const sendToken = (token) => res.write(`event: token\ndata: ${JSON.stringify({ token })}\n\n`);
      const sendDone = (source, meta) => res.write(`event: done\ndata: ${JSON.stringify({ done: true, source, ...meta })}\n\n`);

      sendToken(`Swarm ${mode} · ${job} · routing…\n\n`);
      const agent = selectAgent(swarmMessage);
      const systemPrompt = `${agent.systemPrompt}\n\nTone: thoughtful, unhurried, human. Never clinical. Never sycophantic.`;

      swarmOrchestrate({ job, mode, systemPrompt, message: swarmMessage, history })
        .then((result) => {
          const words = result.text.split(" ");
          for (const word of words) sendToken(word + " ");
          const meta = { agent: agent.name, online: true, swarm: { provider: result.provider, model: result.model, mode, job } };
          if (result.consensus) meta.swarm.consensus = result.consensus;
          if (result.council) meta.swarm.council = result.council;
          sendDone(result.provider, meta);
          res.end();
        })
        .catch((err) => {
          sendToken(`Swarm failed: ${err.message}\n`);
          sendDone("failed", { error: err.message });
          res.end();
        });
      return;
    }

    if (cmd.name === "doors" || cmd.name === "door") {
      const { spawn } = require("child_process");
      const doorTypes = cmd.args || "elephant garden cosmic";
      
      res.writeHead(200, {
        "Content-Type": "text/event-stream; charset=utf-8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*",
        "X-Accel-Buffering": "no",
      });
      const sendToken = (token) => res.write(`event: token\ndata: ${JSON.stringify({ token })}\n\n`);
      const sendDone = (source, meta) => res.write(`event: done\ndata: ${JSON.stringify({ done: true, source, ...meta })}\n\n`);

      sendToken(`◈ Generating mystical doors…\n\n`);
      sendToken(`Door types: ${doorTypes}\n`);
      sendToken(`Style: Abstract, dreamlike, not cartoonish\n\n`);
      
      const py = spawn("python", ["scripts/generate-door-images.py", "generate"], { cwd: repoRoot });
      let stdout = "";
      let stderr = "";
      
      py.stdout.on("data", (d) => {
        stdout += d.toString();
        sendToken(d.toString());
      });
      
      py.stderr.on("data", (d) => {
        stderr += d.toString();
        sendToken(`⚠️ ${d.toString()}`);
      });
      
      py.on("close", (code) => {
        if (code === 0) {
          sendToken(`\n✅ Door images generated successfully!\n`);
          sendToken(`Check: data/images/three-doors/\n`);
          sendDone("doors", { agent: "DoorGenerator", online: true, count: 3 });
        } else {
          sendToken(`\n❌ Generation failed (exit ${code})\n`);
          sendToken(`Make sure Stable Diffusion is running: python -m launch --api\n`);
          sendDone("doors", { agent: "DoorGenerator", online: false, error: stderr });
        }
        res.end();
      });
      
      py.on("error", (err) => {
        sendToken(`\n❌ Failed to spawn generator: ${err.message}\n`);
        sendDone("doors", { agent: "DoorGenerator", online: false, error: err.message });
        res.end();
      });
      
      return;
    }

    if (cmd.name === "converge" || cmd.name === "convergance") {
      const { spawn } = require("child_process");
      const py = spawn("python", ["src/convergence_io_engine.py", "loop"], { cwd: repoRoot });
      let stdout = "";
      let stderr = "";
      py.stdout.on("data", (d) => { stdout += d.toString(); });
      py.stderr.on("data", (d) => { stderr += d.toString(); });
      
      const timeout = setTimeout(() => {
        py.kill();
        sse.writeStreamHeaders(res);
        sse.sendError(res, "Convergence engine timeout (60s)");
        sse.sendDone(res, "failed");
      }, 60000);

      py.on("close", (code) => {
        clearTimeout(timeout);
        
        if (code !== 0) {
          sse.writeStreamHeaders(res);
          sse.sendError(res, `Convergence engine failed (exit ${code}): ${stderr.slice(0, 500)}`);
          sse.sendDone(res, "failed");
          return;
        }

        try {
          const result = JSON.parse(stdout);
          
          // Build 12-step convergence context for AI interpretation
          const convergenceContext = `
12-Step Convergence Analysis:
Overall Score: ${result.convergence_score || 0}/100
Status: ${result.promotion_ready ? "PROMOTION READY" : "NEEDS REVIEW"}
Version: ${result.version?.build || result.version?.tag || "unknown"}

Phase Results:
${result.phases ? result.phases.map((p, i) => `${i + 1}. ${p.name}: ${p.status}`).join("\n") : "No phase data"}

Key Metrics:
- Total phases: ${result.phases?.length || 0}
- Passed: ${result.phases?.filter(p => p.status === "pass").length || 0}
- Failed: ${result.phases?.filter(p => p.status === "fail").length || 0}
- Skipped: ${result.phases?.filter(p => p.status === "skip").length || 0}

Interpret this convergence result and provide:
1. Executive summary (2-3 sentences)
2. Top 3 blockers or risks
3. Recommended next actions
4. Confidence assessment for each of the 12 steps
`;

          sse.writeStreamHeaders(res);
          const sendToken = (token) => sse.sendToken(res, token);
          const sendDone = (source, meta) => sse.sendDone(res, source, meta);

          // Stream the raw convergence data first
          sendToken(`◈ 12-Step Convergence Analysis\n\n`);
          sendToken(`Score: ${result.convergence_score || 0}/100\n`);
          sendToken(`Status: ${result.promotion_ready ? "✅ Ready" : "⚠️ Review Needed"}\n\n`);
          
          if (result.phases) {
            sendToken(`Phase Breakdown:\n`);
            result.phases.forEach((p, i) => {
              const icon = p.status === "pass" ? "✓" : p.status === "fail" ? "✗" : "○";
              sendToken(`${icon} ${i + 1}. ${p.name}: ${p.status}\n`);
            });
            sendToken(`\n`);
          }

          // Now use AI to interpret and provide contextual feedback
          const ollamaBase = process.env.OLLAMA_BASE_URL || "http://127.0.0.1:11434";
          const ollamaModel = process.env.OLLAMA_MODEL || "qwen2.5-coder";
          
          const payload = JSON.stringify({
            model: ollamaModel,
            stream: true,
            messages: [
              { role: "system", content: "You are a convergence analyst. Interpret 12-step convergence results and provide actionable feedback. Be concise, specific, and prioritized." },
              { role: "user", content: convergenceContext }
            ],
          });

          const ollamaUrl = new URL(ollamaBase);
          const req2 = http.request({
            hostname: ollamaUrl.hostname,
            port: ollamaUrl.port || 11434,
            path: "/api/chat",
            method: "POST",
            headers: { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(payload) },
          }, (upstream) => {
            if (upstream.statusCode !== 200) {
              upstream.resume();
              sendToken(`\n⚠️ AI interpretation unavailable. Raw data shown above.\n`);
              sendDone("convergence", { agent: "Convergence", online: true, score: result.convergence_score });
              res.end();
              return;
            }
            
            let buf = "";
            upstream.on("data", (chunk) => {
              buf += chunk.toString();
              const lines = buf.split("\n");
              buf = lines.pop();
              for (const line of lines) {
                if (!line.trim()) continue;
                try {
                  const parsed = JSON.parse(line);
                  if (parsed.message?.content) {
                    sendToken(parsed.message.content);
                  }
                } catch {}
              }
            });
            upstream.on("end", () => {
              sendDone("convergence", { agent: "Convergence", online: true, score: result.convergence_score });
              res.end();
            });
            upstream.on("error", () => {
              sendToken(`\n⚠️ AI interpretation error. Raw data shown above.\n`);
              sendDone("convergence", { agent: "Convergence", online: true, score: result.convergence_score });
              res.end();
            });
          });
          
          req2.on("error", () => {
            sendToken(`\n⚠️ Ollama unavailable. Raw data shown above.\n`);
            sendDone("convergence", { agent: "Convergence", online: false, score: result.convergence_score });
            res.end();
          });
          req2.setTimeout(30000, () => { req2.destroy(); });
          req2.write(payload);
          req2.end();

        } catch (exc) {
          sse.writeStreamHeaders(res);
          sse.sendError(res, `Convergence parse error: ${exc.message}\n\nRaw output:\n${stdout.slice(0, 1000)}`);
          sse.sendDone(res, "failed");
          res.end();
        }
      });
      
      py.on("error", (err) => {
        clearTimeout(timeout);
        sse.writeStreamHeaders(res);
        sse.sendError(res, `Convergence engine spawn error: ${err.message}`);
        sse.sendDone(res, "failed");
        res.end();
      });
      
      return;
    }

    // Three Doors variants: start fresh game if no history, else strip command and continue
    if (cmd.name === "three-doors" || cmd.name === "threedoors" || cmd.name === "three_doors") {
      if (history && history.length > 0) {
        // Game already in progress — strip the bang command, keep any surrounding text
        const stripped = message.replace(/!(?:three-doors|threedoors|three_doors)\b/gi, "").trim();
        message = stripped || "continue";
      }
      // fall through to normal SSE chat routing below
    } else {
      res.writeHead(400, { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" });
      res.end(JSON.stringify({ error: "unsupported_command", command: cmd.name }));
      return;
    }
  }

  sse.writeStreamHeaders(res);

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

  // ── Keystone debug mode ───────────────────────────────────────────────
  // When Keystone is selected, bypass persona/doors and talk raw to the model
  // about app dev, repo state, and convergence. Direct API access from the UX.
  const isKeystoneDebug = agent.id === "keystone" && mcpFlag;

  let dreamContext = recentDreams.length > 0
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

  // Compact history once; providers reuse this via buildProviderMessages.
  // historyContext is kept for Keystone debug prompt only — not injected into dream system prompt.
  const compacted = compactHistory(history);
  const historyContext = compacted.length > 0
    ? `\nPrior conversation turns:\n${compacted.map(h => `${h.role === "assistant" ? "Lantern" : "Dreamer"}: ${h.text}`).join("\n")}`
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
    .map(([k,v]) => `${k}(\xd7${v})`).join(', ');

  const meshHint = symbolMesh.length > 0
    ? `\nRecurring symbols in dreamer's mesh: ${symbolMesh.join(", ")}.${topPairs ? ` Connected pairs: ${topPairs}.` : ''}`
    : "";

  // Three Doors instruction — equally weighted future-tense canaries
  const DOORS_INSTRUCTION = `\n\nAt the end of every response, imagine exactly 3 forward-facing doors — canaries the dreamer is sending ahead into their waking and dreaming life. Each door should be a brief, future-tense, equally weighted sensory or experiential path grounded in the last door mentioned and the dreamer's personal symbol mesh. All 3 should carry equal weight — no door is more important. They represent what the dreamer wants to see, hear, feel, taste, touch, or live. Write them as a single hidden line:\n[DOORS: door one | door two | door three]\nRules: future tense, first person, short (under 8 words), no questions, no commands, equally weighted, rooted in the conversation and symbol mesh.${meshHint}`;

  // Keystone debug prompt — raw dev access, no persona, no doors
  const KEYSTONE_DEBUG_PROMPT = `You are Keystone, a direct debug interface for Lantern OS development. You have access to the full repo context below. Respond as a senior engineer — concise, honest, actionable. No dream persona, no doors, no metaphors.\n\nRepo state:\n- Server: apps/lantern-garage/server.js (modular routes under routes/)\n- Streaming: lib/stream-chat.js (Gemini→Claude→OpenAI→Grok→Ollama chain)\n- Dream journal: ${allRecent.length} entries in data/dream_journal/\n- Providers configured: ${['GEMINI_API_KEY','ANTHROPIC_API_KEY','OPENAI_API_KEY','XAI_API_KEY'].filter(k => process.env[k]).join(', ') || 'none'}\n- Symbol mesh: ${symbolMesh.slice(0, 5).join(', ') || 'empty'}\n- Co-occurrence: ${topPairs || 'none'}\n${historyContext}\n\nYou can EXECUTE commands. When you output a single-line bash code block, the UI renders a ▶ Run button.\nONLY use these exact commands (anything else is blocked):\n\nTESTS: \`npm test\` or \`node tests/test_dream_journal_api.js\` or \`node tests/test_dream_journal_chat.js\` or \`node tests/test_dream_chat_multiturns.js\` or \`node tests/test_dream_journal_keystone.js\`\nGIT: \`git status\` \`git diff --stat\` \`git log --oneline -N\` \`git add FILE\` \`git commit -m "MSG"\` \`git push origin master\` \`git branch\`\nPR: \`gh pr create --repo alex-place/lantern-os --head cdblasioli-gif:master --base master --title "TITLE" --body "BODY"\`\nORCH: \`python src/convergence_io_engine.py health\` or \`loop\` or \`inspect\`\nREAD: \`cat FILE\` \`head -N FILE\`\n\nWhen asked to do something, output the EXACT command in a bash code block. The user clicks ▶ to run it. Do NOT suggest commands outside this list.\n\nAnswer directly. Reference file paths. Check data/pcsf/ for state. Check manifests/dream-journal-v1-agent-slots.json and csf/ingest/*.md for work queue.`;

  // CSF long-term memory + door state (query-time relevance filtered)
  const csfContext = formatCSFContextForPrompt(message);
  const csfBlock = csfContext ? `\n\nLong-term memory (CSF):\n${csfContext}` : "";

  const systemPrompt = isKeystoneDebug
    ? KEYSTONE_DEBUG_PROMPT
    : `${agent.systemPrompt}\n\n${dreamContext}${csfBlock}\n\nTone: thoughtful, unhurried, human. Never clinical. Never sycophantic. Use the dreamer's own words back to them. When the dreamer asks about previous dreams or doors, use the CSF memory and door state above — never fabricate memories.${DOORS_INSTRUCTION}${surfaceMode === "three-doors" ? THREE_DOORS_PREAMBLE : ""}`;


  const sendToken = (token) => sse.sendToken(res, token);
  const sendDone = (source, extra = {}) => sse.sendDone(res, source, extra);
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
      return "Ollama is not running locally. Start it with: ollama serve && ollama pull qwen2.5-coder";
    }
    if (msg.includes("timeout")) {
      return "The provider timed out. Your network or the service may be slow.";
    }
    if (msg.includes("no_provider_configured")) {
      return "No AI providers are set up. Add an API key in Settings to get started.";
    }
    if (msg.includes("all_providers_failed")) {
      return "All providers failed. This can happen when keys are invalid, rate-limited, or the network is slow. Check Settings or try again.";
    }
    return msg;
  }

  const sendError = (msg) => sse.sendError(res, msg);
  const sendFail = (reason) => {
    sendError(humanError(reason));
    sendDone("failed", { agent: agent.name, online: false });
  };
  const sendLocalFallback = (reason) => {
    sendError(`local_fallback: ${reason}`);
    sendDone("offline", { agent: agent.name, online: false });
  };

  // No provider available — stream a clear error instead of static persona replies
  const streamLocalFallback = async (reason) => {
    const errorText = humanError(reason || "no_provider_configured");
    sendError(errorText);
    sendDone("offline", { agent: agent.name, online: false, error: reason || "no_provider_configured", suggestions: FALLBACK_DOORS });
  };

  await appendConversationEntry({
    recordedAt: new Date().toISOString(),
    surface: "dream-chat-stream",
    role: "operator",
    text: message.slice(0, maxConversationTextLength),
  }).catch(() => {});

  // Snapshot provider availability from the 60s PCSF cache (avoids per-request env re-reads)
  const providerState = getProviderState();
  const anyProviderConfigured = !!(
    providerState.gemini.hasKey || providerState.anthropic.hasKey ||
    providerState.openai.hasKey || providerState.xai.hasKey ||
    providerState.mistral.hasKey || providerState.cohere.hasKey ||
    providerState.perplexity.hasKey || providerState.deepseek.hasKey ||
    providerState.openrouter.hasKey || process.env.OLLAMA_BASE_URL
  );

  let fullReply = "";

  // ── Convergance OS: Route intent and select model profile ─────────────────
  let converganceDecision = null;
  try {
    converganceDecision = await converganceRoute(message, {
      requestedProvider,
      forceProfile: surfaceMode === "three-doors" ? "lantern-csf-dream" : undefined,
    });
    // Inject behavior preamble into system prompt context
    if (converganceDecision.behaviorRules && dreamContext) {
      dreamContext = buildBehaviorPreamble(converganceDecision) + "\n" + dreamContext;
    }
  } catch (e) {
    console.error("[Convergance] Router error (non-fatal):", e.message);
  }

  // ── Provider 0: Ollama LOCAL-FIRST (dream chat prefers local models) ──────
  // When no specific cloud provider is requested, try all local Ollama models in sequence
  // for lower latency, zero cost, and offline resilience. Cloud providers are fallbacks.
  const ollamaBase = process.env.OLLAMA_BASE_URL || "http://127.0.0.1:11434";
  
  // Model chain: task-specific ordering with fallbacks
  const OLLAMA_MODEL_CHAIN = {
    // CSF/dream tasks: custom model first, then general models
    csf: [
      "lantern-csf-dream",
      "mistral",
      "qwen2.5-coder",
      "hf.co/PantheonUnbound/Satyr-V0.1-4B:Q4_K_M"
    ],
    // Coding tasks: coder model first
    coding: [
      "qwen2.5-coder",
      "lantern-csf-dream",
      "mistral",
      "hf.co/PantheonUnbound/Satyr-V0.1-4B:Q4_K_M"
    ],
    // Creative/dream tasks: custom CSF model first
    creative: [
      "lantern-csf-dream",
      "mistral",
      "qwen2.5-coder",
      "hf.co/PantheonUnbound/Satyr-V0.1-4B:Q4_K_M"
    ],
    // Default: balanced chain
    default: [
      "lantern-csf-dream",
      "qwen2.5-coder",
      "mistral",
      "hf.co/PantheonUnbound/Satyr-V0.1-4B:Q4_K_M"
    ]
  };
  
  // Select model chain based on intent or use default
  const intent = converganceDecision?.intent || "default";
  const modelChain = OLLAMA_MODEL_CHAIN[intent] || OLLAMA_MODEL_CHAIN.default;
  
  const ollamaLocalFirst = !requestedProvider || requestedProvider === "ollama" || requestedProvider === "local";
  
  if (ollamaLocalFirst && message && !isKeystoneDebug) {
    
    for (const ollamaModel of modelChain) {
      try {
        const payload = JSON.stringify({
          model: ollamaModel,
          stream: true,
          messages: buildProviderMessages(systemPrompt, compacted, message),
        });
        const ollamaUrl = new URL(ollamaBase);
        await new Promise((resolve, reject) => {
          const req2 = http.request({
            hostname: ollamaUrl.hostname,
            port: ollamaUrl.port || 11434,
            path: "/api/chat",
            method: "POST",
            headers: { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(payload) },
          }, (upstream) => {
            if (upstream.statusCode !== 200) { upstream.resume(); reject(new Error(`ollama_status_${upstream.statusCode}`)); return; }
            let buf = "";
            upstream.on("data", (chunk) => {
              buf += chunk.toString();
              const lines = buf.split("\n");
              buf = lines.pop();
              for (const line of lines) {
                if (!line.trim()) continue;
                try {
                  const parsed = JSON.parse(line);
                  if (parsed.message?.content) { fullReply += parsed.message.content; sendToken(parsed.message.content); }
                } catch {}
              }
            });
            upstream.on("end", () => resolve());
            upstream.on("error", reject);
          });
          req2.on("error", reject);
          req2.setTimeout(120000, () => { req2.destroy(); reject(new Error("ollama_timeout")); });
          req2.write(payload);
          req2.end();
        });
        
        if (fullReply) {
          const { cleanText, suggestions } = doorsOrFallback(fullReply, isKeystoneDebug);
          const imageEntryId = triggerImageGeneration({ cleanText, suggestions, surfaceMode, symbolMesh });
          await appendConversationEntry({
            recordedAt: new Date().toISOString(),
            surface: "dream-chat-stream",
            role: "lantern",
            text: cleanText.slice(0, maxConversationTextLength),
          }).catch(() => {});
          recordProviderSuccess("ollama");
          const meta = { agent: agent.name, online: true, cleanText, suggestions, model: ollamaModel };
          if (imageEntryId) meta.image = { entryId: imageEntryId, status: "generating" };
          sendDone("ollama", meta);
          return;
        }
      } catch (err) {
        fullReply = "";
        continue; // Try next model in chain
      }
    }
    
  }

  // Provider 1: Gemini (streaming) — cloud fallback
  const geminiKey = process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY;
  if (geminiKey && message && (!requestedProvider || requestedProvider === "gemini" || requestedProvider === "google" || requestedProvider.startsWith("gemini-"))) {
    // Gemini model fallback chain: primary -> fallbacks on 429/quota
    // Note: gemini-2.0-flash-lite shut down June 1 2026; gemini-3.5-flash is GA with free grounding
    const GEMINI_MODEL_CHAIN = [
      process.env.GEMINI_MODEL || "gemini-2.5-flash",
      "gemini-3.5-flash",
      "gemini-3.1-flash-lite",
    ];
    for (const geminiModel of (requestedProvider && requestedProvider.startsWith("gemini-")
      ? [requestedProvider]
      : GEMINI_MODEL_CHAIN)) {
    try {
      // Grounding: Google Search enabled by default on gemini-3.x models (5K free/month)
      // Disable with GEMINI_GROUNDING=false if needed
      const isGroundable = geminiModel.startsWith("gemini-3");
      const groundingEnabled = process.env.GEMINI_GROUNDING !== "false" && isGroundable;
      const geminiPayloadBase = {
        contents: [{ role: "user", parts: [{ text: `${systemPrompt}\n\n${message}` }] }],
        generationConfig: { maxOutputTokens: 1024, temperature: 0.7 },
      };
      if (groundingEnabled) {
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
      const { cleanText: geminiClean, suggestions: geminiDoors } = doorsOrFallback(fullReply, isKeystoneDebug);
      await appendConversationEntry({
        recordedAt: new Date().toISOString(),
        surface: "dream-chat-stream",
        role: "lantern",
        text: geminiClean.slice(0, maxConversationTextLength),
      }).catch(() => {});
      recordProviderSuccess("gemini");
      sendDone("gemini", { agent: agent.name, online: true, cleanText: geminiClean, suggestions: geminiDoors });
      return;
    } catch (err) {
      recordProviderFailure("gemini", err.message);
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
        messages: [...compacted.map(h => ({ role: h.role, content: h.text })), { role: "user", content: message }],
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
      const { cleanText: anthropicClean, suggestions: anthropicDoors } = doorsOrFallback(fullReply, isKeystoneDebug);
      await appendConversationEntry({
        recordedAt: new Date().toISOString(),
        surface: "dream-chat-stream",
        role: "lantern",
        text: anthropicClean.slice(0, maxConversationTextLength),
      }).catch(() => {});
      recordProviderSuccess("anthropic");
      sendDone("anthropic", { agent: agent.name, online: true, cleanText: anthropicClean, suggestions: anthropicDoors });
      return;
    } catch (err) {
      recordProviderFailure("anthropic", err.message);
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
        model: process.env.OPENAI_MODEL || "gpt-4.1-mini",
        stream: true,
        messages: buildProviderMessages(systemPrompt, compacted, message),
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
      const { cleanText: openaiClean, suggestions: openaiDoors } = doorsOrFallback(fullReply, isKeystoneDebug);
      await appendConversationEntry({
        recordedAt: new Date().toISOString(),
        surface: "dream-chat-stream",
        role: "lantern",
        text: openaiClean.slice(0, maxConversationTextLength),
      }).catch(() => {});
      recordProviderSuccess("openai");
      sendDone("openai", { agent: agent.name, online: true, cleanText: openaiClean, suggestions: openaiDoors });
      return;
    } catch (err) {
      recordProviderFailure("openai", err.message);
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
      const xaiModel = process.env.XAI_MODEL || "grok-4.3";
      const payload = JSON.stringify({
        model: xaiModel, stream: true,
        messages: buildProviderMessages(systemPrompt, compacted, message),
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
      const { cleanText: xaiClean, suggestions: xaiDoors } = doorsOrFallback(fullReply, isKeystoneDebug);
      await appendConversationEntry({ recordedAt: new Date().toISOString(), surface: "dream-chat-stream", role: "lantern", text: xaiClean.slice(0, maxConversationTextLength) }).catch(() => {});
      recordProviderSuccess("xai");
      sendDone("grok", { agent: agent.name, online: true, cleanText: xaiClean, suggestions: xaiDoors });
      return;
    } catch (err) {
      recordProviderFailure("xai", err.message);
      if (requestedProvider) {
        sendError(humanError(err));
        sendFail(err.message);
        return;
      }
      // Auto mode: swallow error silently, let next provider try
    }
  }

  // Provider 5: Ollama (streaming) — last-resort fallback (local-first already tried above)
  if (message && (!requestedProvider || requestedProvider === "ollama" || requestedProvider === "local")) {
    // Attempt 1: Unified Agent Connector (health-checked, provider-ranked, Python-side SSE)
    if (!requestedProvider || requestedProvider === "ollama" || requestedProvider === "local") {
      try {
        let sseDone = false;
        let sseErr = null;
        const sseStream = unifiedAgentStreamSSE(message, agent.id, requestedProvider || "ollama", dreamContext);
        sseStream.onData((parsed) => {
          if (parsed.token) { fullReply += parsed.token; sendToken(parsed.token); }
          if (parsed.done) { sseDone = true; }
        });
        sseStream.onError((err) => { sseErr = err; sseDone = true; });
        await new Promise((resolve) => {
          const check = setInterval(() => {
            if (sseDone) { clearInterval(check); resolve(); }
          }, 50);
        });
        if (sseErr) throw sseErr;
        if (fullReply) {
          const { cleanText, suggestions } = doorsOrFallback(fullReply, isKeystoneDebug);
          await appendConversationEntry({
            recordedAt: new Date().toISOString(),
            surface: "dream-chat-stream",
            role: "lantern",
            text: cleanText.slice(0, maxConversationTextLength),
          }).catch(() => {});
          recordProviderSuccess("ollama");
          sendDone("ollama", { agent: agent.name, online: true, cleanText, suggestions });
          return;
        }
      } catch (err) {
        recordProviderFailure("ollama", `unified_connector: ${err.message}`);
        fullReply = "";
        // Fall through to direct HTTP attempt
      }
    }

    // Attempt 2: Direct HTTP to Ollama
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
        req2.setTimeout(15000, () => { req2.destroy(); reject(new Error("ollama_connect_timeout")); });
        req2.write(payload);
        req2.end();
      });
      if (ollamaOk) {
        const { cleanText: ollamaClean, suggestions: ollamaDoors } = doorsOrFallback(fullReply, isKeystoneDebug);
        await appendConversationEntry({
          recordedAt: new Date().toISOString(),
          surface: "dream-chat-stream",
          role: "lantern",
          text: ollamaClean.slice(0, maxConversationTextLength),
        }).catch(() => {});
        recordProviderSuccess("ollama");
        sendDone("ollama", { agent: agent.name, online: true, cleanText: ollamaClean, suggestions: ollamaDoors });
        return;
      }
    } catch (err) {
      recordProviderFailure("ollama", err.message);
      if (requestedProvider) {
        sendError(humanError(err));
        sendFail(err.message);
        return;
      }
      // Auto mode: swallow error silently, let next provider try
    }
  }

  // No provider available — stream local persona fallback
  const fallbackReason = anyProviderConfigured
    ? "all_providers_failed"
    : "no_provider_configured";
  await streamLocalFallback(fallbackReason);
}

module.exports = { handleStreamChat, extractDoors, doorsOrFallback };
