/**
 * Dream Journal cloud-server integration tests.
 * Spawns cloud-server.js on a random port, runs assertions, tears down.
 * No external dependencies — pure Node.js built-ins.
 * Run: node tests/test_cloud_server.js
 */

"use strict";

const http   = require("http");
const path   = require("path");
const fs     = require("fs");
const os     = require("os");
const { spawn } = require("child_process");

const SERVER  = path.resolve(__dirname, "../apps/lantern-garage/cloud-server.js");
const PORT    = 14177; // separate from local server port (4177)
const BASE    = `http://127.0.0.1:${PORT}`;

let server;
let passed = 0;
let failed = 0;

// ── Helpers ──────────────────────────────────────────────────────────────────

function req(method, pathname, body) {
  return new Promise((resolve, reject) => {
    const payload = body ? JSON.stringify(body) : null;
    const opts = {
      hostname: "127.0.0.1",
      port: PORT,
      path: pathname,
      method,
      headers: {
        "Content-Type": "application/json",
        ...(payload ? { "Content-Length": Buffer.byteLength(payload) } : {}),
      },
    };
    const r = http.request(opts, (res) => {
      let data = "";
      res.on("data", (c) => (data += c));
      res.on("end", () => {
        try { resolve({ status: res.statusCode, body: JSON.parse(data) }); }
        catch { resolve({ status: res.statusCode, body: data }); }
      });
    });
    r.on("error", reject);
    if (payload) r.write(payload);
    r.end();
  });
}

async function test(name, fn) {
  try {
    await fn();
    console.log(`  ✓ ${name}`);
    passed++;
  } catch (e) {
    console.error(`  ✗ ${name}: ${e.message}`);
    failed++;
  }
}

function assert(cond, msg) {
  if (!cond) throw new Error(msg || "assertion failed");
}

// ── Server lifecycle ──────────────────────────────────────────────────────────

function startServer() {
  return new Promise((resolve, reject) => {
    // Point repoRoot at a temp dir so data writes don't pollute the real repo
    const tmpRoot = fs.mkdtempSync(path.join(os.tmpdir(), "lantern-test-"));
    server = spawn(process.execPath, [SERVER], {
      env: { ...process.env, PORT: String(PORT), LANTERN_REPO_ROOT: tmpRoot },
      stdio: ["ignore", "pipe", "pipe"],
    });
    server.stderr.on("data", (d) => { /* suppress */ });
    server.stdout.on("data", (d) => {
      if (d.toString().includes("running on port")) resolve(tmpRoot);
    });
    server.on("error", reject);
    setTimeout(() => reject(new Error("server startup timeout")), 8000);
  });
}

function stopServer() {
  if (server) server.kill();
}

function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

// ── Tests ─────────────────────────────────────────────────────────────────────

async function runTests() {
  console.log("\nDream Journal — cloud-server integration tests");
  console.log("─".repeat(50));

  await test("GET /api/health returns ok", async () => {
    const r = await req("GET", "/api/health");
    assert(r.status === 200, `expected 200, got ${r.status}`);
    assert(r.body.ok === true, "expected ok=true");
    assert(r.body.service === "lantern-garage-cloud", "wrong service name");
  });

  await test("GET /api/status returns operational", async () => {
    const r = await req("GET", "/api/status");
    assert(r.status === 200);
    assert(r.body.status === "operational");
    assert(r.body.mode === "cloud");
  });

  await test("GET /api/dream/stats returns empty stats when no entries", async () => {
    const r = await req("GET", "/api/dream/stats");
    assert(r.status === 200, `expected 200, got ${r.status}`);
    assert(typeof r.body.total_entries === "number", "missing total_entries");
    assert(r.body.total_entries === 0, "expected 0 entries initially");
    assert(typeof r.body.entries_by_kind === "object", "missing entries_by_kind");
  });

  await test("POST /api/dream/create saves entry and returns id", async () => {
    const r = await req("POST", "/api/dream/create", {
      kind: "dream",
      text: "I was flying over a luminous city at dusk.",
      emotions: ["wonder", "calm"],
      tags: ["flying", "city", "dusk"],
      lucidity: 0.8,
    });
    assert(r.status === 200, `expected 200, got ${r.status} — ${JSON.stringify(r.body)}`);
    assert(r.body.saved === true, "expected saved=true");
    assert(typeof r.body.id === "string", "missing id");
    assert(r.body.entry.kind === "dream", "wrong kind");
    assert(r.body.entry.text.includes("luminous city"), "wrong text");
    assert(r.body.entry.emotions[0] === "wonder", "wrong emotions");
    assert(r.body.entry.tags.includes("flying"), "missing tag");
    assert(r.body.entry.lucidity === 0.8, "wrong lucidity");
  });

  await test("GET /api/dream/stats reflects saved entry", async () => {
    const r = await req("GET", "/api/dream/stats");
    assert(r.status === 200);
    assert(r.body.total_entries === 1, `expected 1 entry, got ${r.body.total_entries}`);
    assert(r.body.entries_by_kind.dream === 1, "expected 1 dream entry");
    assert(r.body.top_tags.flying === 1, "expected flying tag");
    assert(parseFloat(r.body.avg_lucidity) === 0.8, "wrong avg_lucidity");
  });

  await test("POST /api/dream/create saves a note entry", async () => {
    const r = await req("POST", "/api/dream/create", {
      kind: "note",
      text: "Remember to write down the door symbols from last night.",
      tags: ["reminder", "symbols"],
      lucidity: 0,
    });
    assert(r.status === 200);
    assert(r.body.entry.kind === "note");
  });

  await test("GET /api/dream/stats counts multiple kinds", async () => {
    const r = await req("GET", "/api/dream/stats");
    assert(r.status === 200);
    assert(r.body.total_entries === 2, `expected 2, got ${r.body.total_entries}`);
    assert(r.body.entries_by_kind.dream === 1);
    assert(r.body.entries_by_kind.note === 1);
  });

  await test("POST /api/dream/chat returns in-character reply", async () => {
    const r = await req("POST", "/api/dream/chat", { message: "I dreamed of a luminous door." });
    assert(r.status === 200);
    assert(typeof r.body.reply === "string" && r.body.reply.length > 0, "missing reply");
    assert(r.body.online === true, "expected online=true");
    assert(Array.isArray(r.body.suggestions), "missing suggestions");
  });

  await test("POST /api/dream/chat empty message returns prompt", async () => {
    const r = await req("POST", "/api/dream/chat", { message: "" });
    assert(r.status === 200);
    assert(typeof r.body.reply === "string");
  });

  await test("POST /api/dream/create rejects oversized text gracefully", async () => {
    const r = await req("POST", "/api/dream/create", {
      kind: "dream",
      text: "x".repeat(20000),
    });
    assert(r.status === 200, "should accept but truncate");
    assert(r.body.entry.text.length <= 10000, "text should be truncated");
  });

  await test("POST to unlisted path returns 403 cloud_read_only", async () => {
    const r = await req("POST", "/api/some/unknown/path", { x: 1 });
    assert(r.status === 403);
    assert(r.body.error === "cloud_read_only_method_not_allowed");
  });

  await test("GET unknown path returns 404 JSON", async () => {
    const r = await req("GET", "/api/does-not-exist");
    assert(r.status === 404);
  });

  await test("OPTIONS preflight returns 204 with CORS headers", async () => {
    const r = await new Promise((resolve, reject) => {
      const opts = { hostname: "127.0.0.1", port: PORT, path: "/api/dream/create", method: "OPTIONS" };
      const request = http.request(opts, (res) => resolve({ status: res.statusCode, headers: res.headers }));
      request.on("error", reject);
      request.end();
    });
    assert(r.status === 204);
    assert(r.headers["access-control-allow-origin"] === "*");
  });

  console.log("─".repeat(50));
  console.log(`  ${passed} passed, ${failed} failed`);
  return failed;
}

// ── Entry point ───────────────────────────────────────────────────────────────

(async () => {
  let tmpRoot;
  try {
    tmpRoot = await startServer();
    await sleep(300); // let server fully initialise
    const failures = await runTests();
    process.exit(failures > 0 ? 1 : 0);
  } catch (e) {
    console.error("Fatal:", e.message);
    process.exit(1);
  } finally {
    stopServer();
    // clean up temp root handled by OS
  }
})();
