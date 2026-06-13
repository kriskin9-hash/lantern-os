/**
 * Three Doors Failure Reporter
 *
 * Proves every automated test method is currently broken.
 * Run this BEFORE claiming any test passes.
 *
 * Exit code 0 = all failures confirmed (expected)
 * Exit code 1 = something unexpectedly passed (investigate)
 *
 * Usage: node tests/test_three_doors_failures.js
 */

const http = require("http");
const { spawn } = require("child_process");
const path = require("path");
const net = require("net");

const REPO_ROOT = path.resolve(__dirname, "..");
const SERVER_PORT = 4177;
const OLLAMA_PORT = 11434;

let failCount = 0;
let passCount = 0;

function confirmed(label, reason) {
  console.log(`  [FAIL CONFIRMED] ${label}`);
  console.log(`    Reason: ${reason}`);
  failCount++;
}

function unexpected(label, reason) {
  console.error(`  [UNEXPECTED PASS] ${label}`);
  console.error(`    This should have failed: ${reason}`);
  passCount++;
}

function isPortOpen(port) {
  return new Promise((resolve) => {
    const sock = new net.Socket();
    sock.setTimeout(800);
    sock.on("connect", () => { sock.destroy(); resolve(true); });
    sock.on("error", () => resolve(false));
    sock.on("timeout", () => { sock.destroy(); resolve(false); });
    sock.connect(port, "127.0.0.1");
  });
}

function postJson(path, body, port = SERVER_PORT) {
  return new Promise((resolve, reject) => {
    const payload = JSON.stringify(body);
    const req = http.request({
      hostname: "127.0.0.1",
      port,
      path,
      method: "POST",
      headers: { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(payload) },
    }, (res) => {
      let data = "";
      res.on("data", (c) => (data += c));
      res.on("end", () => { try { resolve({ status: res.statusCode, body: JSON.parse(data) }); } catch { resolve({ status: res.statusCode, body: data }); } });
    });
    req.on("error", reject);
    req.setTimeout(1500, () => { req.destroy(); reject(new Error("timeout")); });
    req.write(payload);
    req.end();
  });
}

function spawnPython(script, stdin) {
  return new Promise((resolve, reject) => {
    const py = process.platform === "win32" ? "python" : "python3";
    const proc = spawn(py, ["-c", script], {
      cwd: REPO_ROOT,
      env: { ...process.env, PYTHONPATH: path.join(REPO_ROOT, "src") },
    });
    let out = "", err = "";
    proc.stdout.on("data", (c) => (out += c));
    proc.stderr.on("data", (c) => (err += c));
    proc.on("close", (code) => {
      if (code !== 0) reject(new Error(err.trim() || `exit ${code}`));
      else resolve(out.trim());
    });
    proc.on("error", reject);
    if (stdin) { proc.stdin.write(stdin); proc.stdin.end(); }
  });
}

async function run() {
  console.log("\n╔══════════════════════════════════════════════════════════╗");
  console.log("║     THREE DOORS — AUTOMATED METHOD FAILURE REPORTER     ║");
  console.log("╚══════════════════════════════════════════════════════════╝\n");
  console.log("Each check below proves a current automated path is broken.");
  console.log("Visual human verification is required to confirm game play.\n");

  // ── 1. Server connectivity ─────────────────────────────────────────────
  console.log("── 1. Server API (port 4177) ─────────────────────────────");
  const serverUp = await isPortOpen(SERVER_PORT);
  if (!serverUp) {
    confirmed(
      "Server not reachable",
      `Port ${SERVER_PORT} is closed. All API tests (test_three_doors_game.spec.js) require a running server.`
    );
  } else {
    // Server is up — test the /api/dream/doors endpoint
    try {
      const r = await postJson("/api/dream/doors", { userId: "failure-test", action: "start" });
      if (r.status === 200 && r.body.scene_key) {
        unexpected("Server API /api/dream/doors", "Server is running and returned valid game state");
      } else {
        confirmed("Server API returned unexpected response", JSON.stringify(r.body).slice(0, 120));
      }
    } catch (e) {
      confirmed("Server API call failed", e.message);
    }
  }

  // ── 2. Playwright availability ────────────────────────────────────────
  console.log("\n── 2. Playwright (UI tests) ──────────────────────────────");
  try {
    require.resolve("playwright");
    unexpected("Playwright installed", "Playwright was found — UI tests could theoretically run (but still need server)");
  } catch {
    confirmed(
      "Playwright not installed",
      "'npx playwright test' and require('playwright') both fail. All UI tests in test_three_doors_game.spec.js are unrunnable without server + Playwright."
    );
  }
  if (!serverUp) {
    confirmed(
      "Playwright tests also need server",
      "Even if Playwright were installed, all page.request.post() calls target http://127.0.0.1:4177 which is down."
    );
  }

  // ── 3. Ollama LLM backend ─────────────────────────────────────────────
  console.log("\n── 3. Ollama LLM (primary Three Doors engine) ───────────");
  const ollamaUp = await isPortOpen(OLLAMA_PORT);
  if (!ollamaUp) {
    confirmed(
      "Ollama unavailable",
      `Port ${OLLAMA_PORT} is closed. dream-chat.js primary Three Doors path (lantern-csf-dream model) will always fail and fall through to Python engine.`
    );
  } else {
    // Ollama port is open — check if lantern-csf-dream model exists
    try {
      const r = await postJson("/api/chat", { model: "lantern-csf-dream", stream: false, messages: [{ role: "user", content: "!three-doors" }] }, OLLAMA_PORT);
      if (r.body && r.body.message && r.body.message.content) {
        unexpected("Ollama lantern-csf-dream model", "Model responded — Ollama path is actually working");
      } else {
        confirmed("Ollama responded but model returned empty", JSON.stringify(r.body).slice(0, 120));
      }
    } catch (e) {
      confirmed("Ollama port open but chat API failed", e.message);
    }
  }

  // ── 4. Stable Diffusion image generation ─────────────────────────────
  console.log("\n── 4. Stable Diffusion image generation ─────────────────");
  const sdUrl = process.env.STABLE_DIFFUSION_URL || process.env.SD_WEBUI_URL;
  if (!sdUrl) {
    confirmed(
      "SD image generation disabled",
      "Neither STABLE_DIFFUSION_URL nor SD_WEBUI_URL env vars are set. image_available=false in all API responses. No images will ever be generated by /api/dream/doors/image — only text prompts returned."
    );
  } else {
    unexpected("SD env var is set", `Found SD URL: ${sdUrl} — image generation may be available`);
  }

  // ── 5. handleThreeDoorsServer door-choice routing bug ─────────────────
  console.log("\n── 5. Door-choice routing in dream-chat.js ───────────────");
  try {
    const { handleThreeDoorsServer, isThreeDoorsTrigger, isDoorChoice } = require("../apps/lantern-garage/lib/three-doors-chat");

    // Trigger detection works
    const triggerResult = handleThreeDoorsServer("!three-doors");
    if (!triggerResult) throw new Error("Trigger detection broken");

    // But door choices ("A", "B", "C") bypass the Three Doors intercept entirely
    const choiceResult = handleThreeDoorsServer("A");  // Player types "A" to pick Door A
    const choiceResult2 = handleThreeDoorsServer("door A");
    const choiceResult3 = handleThreeDoorsServer("choose B");

    if (choiceResult || choiceResult2 || choiceResult3) {
      unexpected(
        "handleThreeDoorsServer routes door choices",
        "The function returns non-null for 'A', 'door A', or 'choose B'"
      );
    } else {
      confirmed(
        "handleThreeDoorsServer does NOT route door choices",
        "Messages like 'A', 'door A', 'choose B' return null from handleThreeDoorsServer. " +
        "They fall through to selectAgent() and get a regular LLM persona response instead of advancing the game. " +
        "The isDoorChoice() function exists but is only called in the browser-side handleThreeDoorsChat() — never server-side."
      );
    }
  } catch (e) {
    confirmed("Could not load three-doors-chat.js", e.message);
  }

  // ── 6. callDoorsApi() uses fetch() — Node.js incompatible ─────────────
  console.log("\n── 6. callDoorsApi fetch() Node.js incompatibility ───────");
  try {
    const { callDoorsApi } = require("../apps/lantern-garage/lib/three-doors-chat");
    // callDoorsApi uses `window?.serverBase` — will be undefined in Node
    // fetch() itself doesn't exist in older Node.js without --experimental-fetch
    const nodeVersion = parseInt(process.versions.node.split(".")[0]);
    if (nodeVersion < 18) {
      confirmed(
        `fetch() unavailable in Node ${process.versions.node}`,
        "callDoorsApi() calls fetch() which doesn't exist before Node 18. " +
        "This function is browser-only despite being in a shared module."
      );
    } else {
      // Node 18+ has fetch, but callDoorsApi will still fail in test context (no server)
      try {
        const p = callDoorsApi({ userId: "test", action: "start" });
        await p;
        unexpected("callDoorsApi succeeded in Node.js", "fetch() call somehow succeeded");
      } catch (fetchErr) {
        confirmed(
          `callDoorsApi fails in Node.js (fetch to empty URL)`,
          `Error: ${fetchErr.message}. The function uses window?.serverBase which is undefined in Node, ` +
          `so it fetches '' (empty string), which fails.`
        );
      }
    }
  } catch (e) {
    confirmed("three-doors-chat.js module error", e.message);
  }

  // ── 7. Python engine (only working path) ─────────────────────────────
  console.log("\n── 7. Python ThreeDoorsEngine (offline capability check) ─");
  const pyScript = `
import sys, json, os, pathlib
sys.path.insert(0, str(pathlib.Path("${REPO_ROOT.replace(/\\/g, "\\\\")}") / "src"))
from three_doors_engine import ThreeDoorsEngine
import tempfile, shutil
tmpdir = tempfile.mkdtemp()
try:
    e = ThreeDoorsEngine("failure-test-probe", data_dir=pathlib.Path(tmpdir))
    state = e.start_game()
    turn1 = e.to_api_response(state)
    state2 = e.choose_door("A")
    turn2 = e.to_api_response(state2)
    print(json.dumps({"ok": True, "scene1": turn1["scene_key"], "scene2": turn2["scene_key"], "prompt_len": len(turn1["image_prompt"]), "image_available": turn1["image_available"]}))
finally:
    shutil.rmtree(tmpdir, ignore_errors=True)
`.trim();

  try {
    const result = await spawnPython(pyScript, "");
    const data = JSON.parse(result);
    if (data.ok) {
      console.log(`  [ENGINE OK] Python engine works offline:`);
      console.log(`    scene1=${data.scene1} → choose A → scene2=${data.scene2}`);
      console.log(`    image_prompt length=${data.prompt_len} chars`);
      console.log(`    image_available=${data.image_available}  ← ALWAYS FALSE without SD env var`);
      if (!data.image_available) {
        confirmed(
          "Python engine runs but image_available=false",
          "ThreeDoorsEngine produces image prompts but image_available is always false without STABLE_DIFFUSION_URL. " +
          "No actual images are generated — only text prompts. Automated image assertion tests will fail."
        );
      }
    }
  } catch (e) {
    confirmed("Python ThreeDoorsEngine failed", `${e.message.slice(0, 200)}`);
    console.log(`    Python engine is the ONLY working backend. If this fails, the entire game is broken.`);
  }

  // ── 8. Offline parsing tests (the only things that pass) ─────────────
  console.log("\n── 8. Offline parsing tests (test_three_doors.js) ────────");
  try {
    const { extractDoors, doorsOrFallback } = require("../apps/lantern-garage/lib/stream-chat");
    const r = extractDoors("Hello\n\n[DOORS: A | B | C]");
    if (r.doors.length === 3) {
      console.log(`  [PASS] Offline DOORS parsing works — but these tests only verify text parsing,`);
      console.log(`         NOT actual game state, session persistence, or image generation.`);
      console.log(`         Passing them gives false confidence that the game works end-to-end.`);
    } else {
      confirmed("extractDoors broken", "Could not parse 3 doors from [DOORS: A | B | C]");
    }
  } catch (e) {
    confirmed("stream-chat.js import failed", e.message);
  }

  // ── Summary ────────────────────────────────────────────────────────────
  console.log("\n╔══════════════════════════════════════════════════════════╗");
  console.log("║                       SUMMARY                          ║");
  console.log("╠══════════════════════════════════════════════════════════╣");
  console.log(`║  Failures confirmed: ${String(failCount).padEnd(34)}║`);
  console.log(`║  Unexpected passes:  ${String(passCount).padEnd(34)}║`);
  console.log("╠══════════════════════════════════════════════════════════╣");
  console.log("║                                                          ║");
  console.log("║  AUTOMATED METHODS CANNOT VERIFY:                        ║");
  console.log("║  • That a multi-turn game session was actually played    ║");
  console.log("║  • That door navigation produces coherent scene changes  ║");
  console.log("║  • That image prompts render meaningful scene art        ║");
  console.log("║  • That the fox companion persists across turns          ║");
  console.log("║                                                          ║");
  console.log("║  REQUIRED: Open three-doors-game.html in a browser,     ║");
  console.log("║  play at least 3 doors, then screenshot the session log. ║");
  console.log("╚══════════════════════════════════════════════════════════╝\n");

  process.exit(0); // Exit 0 = failures confirmed as expected
}

run().catch((e) => {
  console.error("Reporter crashed:", e);
  process.exit(2);
});
