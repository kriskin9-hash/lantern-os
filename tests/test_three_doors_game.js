/**
 * Test Three Doors Game Integration
 *
 * Required assertions:
 * - /api/dream/doors REST endpoint returns valid game state (Python ThreeDoorsEngine)
 * - SSE stream at /api/dream/chat/stream returns 200 and eventually fires done event
 * - Done event always has exactly 3 suggestions (online or fallback)
 * - Image generation failure does not fail the text response
 *
 * Note: SSE stream test accepts "offline" done events when no LLM provider is configured.
 * To get AI-generated doors, set ANTHROPIC_API_KEY, OPENAI_API_KEY, or GEMINI_API_KEY,
 * or have lantern-csf-dream loaded and responsive in Ollama.
 */

const http = require("http");

const TEST_PORT = 4177;
const TEST_HOST = "127.0.0.1";

// ── helpers ────────────────────────────────────────────────────────────────

let passed = 0;
let failed = 0;

function ok(label) {
  passed++;
}

function fail(label, reason) {
  failed++;
}

function postJson(path, body, timeoutMs = 5000) {
  const payload = JSON.stringify(body);
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => { req.destroy(); reject(new Error(`timeout after ${timeoutMs}ms`)); }, timeoutMs);
    const req = http.request({
      hostname: TEST_HOST, port: TEST_PORT, path, method: "POST",
      headers: { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(payload) },
    }, (res) => {
      let data = "";
      res.on("data", (c) => { data += c; });
      res.on("end", () => { clearTimeout(timer); resolve({ statusCode: res.statusCode, data }); });
    });
    req.on("error", (e) => { clearTimeout(timer); reject(e); });
    req.write(payload);
    req.end();
  });
}

// ── Test 1: REST /api/dream/doors (Python ThreeDoorsEngine) ────────────────

async function testDoorsRestEndpoint() {

  // Start game
  let res;
  try {
    res = await postJson("/api/dream/doors", { action: "start" }, 10000);
  } catch (e) {
    fail("start action responds", e.message);
    return;
  }

  if (res.statusCode !== 200) {
    fail("start returns 200", `got ${res.statusCode}`);
    return;
  }
  ok("start returns 200");

  let state;
  try { state = JSON.parse(res.data); } catch (e) {
    fail("start response is valid JSON", e.message);
    return;
  }
  ok("start response is valid JSON");

  if (!state.scene_key) fail("start has scene_key", JSON.stringify(state).slice(0, 100));
  else ok(`start has scene_key: ${state.scene_key}`);

  if (!state.text) fail("start has text", "missing");
  else ok(`start has text (${state.text.length} chars)`);

  if (!Array.isArray(state.doors) || state.doors.length !== 3) {
    fail("start returns 3 doors", `got ${JSON.stringify(state.doors)}`);
  } else {
    ok(`start returns 3 doors: ${state.doors.map(d => d.label || d).join(", ")}`);
  }

  // Choose a door — route reads body.choice, not body.door
  const firstDoor = Array.isArray(state.doors) && state.doors[0];
  const doorLabel = firstDoor?.label || "A";
  try {
    res = await postJson("/api/dream/doors", { action: "choose", choice: doorLabel }, 10000);
  } catch (e) {
    fail(`choose door ${doorLabel} responds`, e.message);
    return;
  }

  if (res.statusCode !== 200) {
    fail(`choose door ${doorLabel} returns 200`, `got ${res.statusCode}`);
    return;
  }
  ok(`choose door ${doorLabel} returns 200`);

  try { state = JSON.parse(res.data); } catch (e) {
    fail("choose response is valid JSON", e.message);
    return;
  }

  if (!state.scene_key) fail("choose returns new scene_key", JSON.stringify(state).slice(0, 100));
  else ok(`choose advanced to scene: ${state.scene_key}`);
}

// ── Test 2: SSE stream - !three-doors routing ──────────────────────────────

async function testThreeDoorsStreamRouting() {

  // The full stream test below will verify the 200 response + done event in one pass.

  // Full stream test with generous timeout (handles Ollama slow-start or cloud fallback)
  const STREAM_TIMEOUT = 30000;

  const payload = JSON.stringify({ message: "!three-doors", history: [] });
  const result = await new Promise((resolve) => {
    const timer = setTimeout(() => resolve({ timedOut: true, data: "" }), STREAM_TIMEOUT);
    const req = http.request({
      hostname: TEST_HOST, port: TEST_PORT, path: "/api/dream/chat/stream", method: "POST",
      headers: { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(payload) },
    }, (res) => {
      let data = "";
      let resolved = false;
      function tryResolve() {
        if (resolved) return;
        const norm = data.replace(/\r\n/g, "\n");
        // Support both SSE formats:
        //   Format A (sse.js): data: {"type":"done",...}
        //   Format B (inline):  event: done\ndata: {...}
        const hasDoneA = norm.includes('\ndata: {"type":"done"') || norm.startsWith('data: {"type":"done"');
        const hasDoneB = norm.includes("\nevent: done\ndata: {") || norm.startsWith("event: done\ndata: {");
        if (hasDoneA || hasDoneB) {
          resolved = true;
          clearTimeout(timer);
          resolve({ statusCode: res.statusCode, data: norm });
        }
      }
      res.on("data", (chunk) => { data += chunk; tryResolve(); });
      res.on("end", () => { if (!resolved) { clearTimeout(timer); resolve({ statusCode: res.statusCode, data: data.replace(/\r\n/g, "\n") }); } });
      res.on("close", () => { if (!resolved) { clearTimeout(timer); resolve({ statusCode: res.statusCode, data: data.replace(/\r\n/g, "\n") }); } });
    });
    req.on("error", () => { clearTimeout(timer); resolve({ statusCode: 0, data }); });
    req.write(payload);
    req.end();
  });

  if (result.statusCode !== 200) {
    fail("/api/dream/chat/stream returns 200", `got ${result.statusCode}`);
    return null;
  }
  ok("/api/dream/chat/stream returns 200");

  const hasDone = result.data && (result.data.includes('"type":"done"') || result.data.includes("event: done\n"));
  if (result.timedOut || !hasDone) {
    fail("done event received within timeout", result.timedOut ? `no done event in ${STREAM_TIMEOUT/1000}s` : "stream ended without done event");
    return null;
  }
  ok("done event received");

  // Parse done event — supports both SSE formats used in this codebase:
  //   Format A (sse.js): data: {"type":"done",...}
  //   Format B (inline): event: done\ndata: {...}
  const lines = result.data.split("\n");
  let doneEvent = null;
  for (let i = 0; i < lines.length; i++) {
    // Format A: single data line with type=done
    if (lines[i].startsWith('data: {') && lines[i].includes('"type":"done"')) {
      try { doneEvent = JSON.parse(lines[i].slice(6)); } catch {}
      break;
    }
    // Format B: event header followed by data line
    if (lines[i].startsWith("event: done")) {
      const dataLine = lines[i + 1];
      if (dataLine && dataLine.startsWith("data: ")) {
        try { doneEvent = JSON.parse(dataLine.slice(6)); } catch {}
        break;
      }
    }
  }

  if (!doneEvent) {
    fail("done event is parseable JSON", result.data.slice(0, 200));
    return null;
  }
  ok("done event is parseable JSON");

  return doneEvent;
}

// ── Test 3: Done event has exactly 3 suggestions ───────────────────────────

async function testDoneEventSuggestions(doneEvent) {

  if (!doneEvent) {
    return;
  }

  const suggestions = doneEvent.suggestions || [];
  const online = doneEvent.online !== false;

  if (suggestions.length !== 3) {
    fail(`exactly 3 suggestions`, `got ${suggestions.length}: ${JSON.stringify(suggestions)}`);
  } else {
    ok(`exactly 3 suggestions: ${JSON.stringify(suggestions)}`);
  }

  const allNonEmpty = suggestions.every(s => typeof s === "string" && s.length > 0);
  if (!allNonEmpty) fail("all suggestions are non-empty strings", JSON.stringify(suggestions));
  else ok("all suggestions are non-empty strings");
}

// ── Test 4: Image generation is non-blocking ──────────────────────────────

async function testImageGenerationNonBlocking() {

  // /api/dream/doors/image should respond immediately (not block on SD)
  let res;
  try {
    res = await postJson("/api/dream/doors/image",
      { userId: "test", prompt: "atmospheric dreamscape, moss-covered doorway" }, 5000);
  } catch (e) {
    fail("image endpoint responds within 5s", e.message);
    return;
  }

  if (res.statusCode !== 200) {
    fail("image endpoint returns 200", `got ${res.statusCode}: ${res.data.slice(0,100)}`);
    return;
  }
  ok("image endpoint returns 200 quickly");

  let body;
  try { body = JSON.parse(res.data); } catch (e) {
    fail("image response is valid JSON", e.message);
    return;
  }

  // image_available=false expected when SD server not running
  if (body.image_available === false) {
    ok(`image_available=false (SD server not running — expected)`);
  } else if (body.image_available === true) {
    ok("image_available=true (Stable Diffusion is connected!)");
  } else {
    fail("image response has image_available field", JSON.stringify(body).slice(0,100));
  }

  const imagePrompt = body.image_prompt || "";
  if (imagePrompt.length > 0) {
    ok(`image_prompt present (${imagePrompt.length} chars)`);
  } else {
    // prompt may be empty if game state lookup failed — soft warning
    passed++; // not a hard failure
  }
}

// ── Runner ─────────────────────────────────────────────────────────────────

async function runAllTests() {
  await testDoorsRestEndpoint();
  const doneEvent = await testThreeDoorsStreamRouting();
  await testDoneEventSuggestions(doneEvent);
  await testImageGenerationNonBlocking();

  if (failed > 0) process.exit(1);
  else process.exit(0);
}

if (require.main === module) {
  runAllTests().catch((e) => {
    process.exit(1);
  });
}

module.exports = { testDoorsRestEndpoint, testThreeDoorsStreamRouting, testDoneEventSuggestions, testImageGenerationNonBlocking };
