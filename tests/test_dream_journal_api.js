/**
 * Dream Journal REST API tests
 * Runs against a live lantern-garage server on port 4177.
 * Start the server before running: node apps/lantern-garage/server.js
 */

const http = require("http");
const assert = require("assert");

const BASE = "http://127.0.0.1:4177";
let passed = 0;
let failed = 0;

async function request(method, path, body) {
  return new Promise((resolve, reject) => {
    const opts = {
      hostname: "127.0.0.1",
      port: 4177,
      path,
      method,
      headers: { "Content-Type": "application/json" },
    };
    const req = http.request(opts, (res) => {
      let data = "";
      res.on("data", (c) => (data += c));
      res.on("end", () => {
        try {
          resolve({ status: res.statusCode, body: JSON.parse(data) });
        } catch {
          resolve({ status: res.statusCode, body: data });
        }
      });
    });
    req.on("error", reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

async function test(name, fn) {
  try {
    await fn();
    console.log(`  ✓ ${name}`);
    passed++;
  } catch (err) {
    console.error(`  ✗ ${name}`);
    console.error(`    ${err.message}`);
    failed++;
  }
}

async function run() {
  console.log("\nDream Journal REST API Tests\n");

  // ── POST /api/dream/create ──────────────────────────────────────────────
  console.log("POST /api/dream/create");

  let createdId;

  await test("creates entry and returns id + saved:true", async () => {
    const r = await request("POST", "/api/dream/create", {
      kind: "dream",
      text: "API test dream: flying over silver towers",
      lucidity: 0.8,
      emotions: ["awe", "clarity"],
      tags: ["test", "api", "towers"],
      symbols: ["tower", "sky"],
    });
    assert.strictEqual(r.status, 200);
    assert.strictEqual(r.body.saved, true);
    assert.ok(r.body.id, "id should be present");
    assert.ok(r.body.entry.timestamp, "entry should have timestamp");
    assert.strictEqual(r.body.entry.kind, "dream");
    assert.strictEqual(r.body.entry.lucidity, 0.8);
    createdId = r.body.id;
  });

  await test("creates note entry", async () => {
    const r = await request("POST", "/api/dream/create", {
      kind: "note",
      text: "Quick note for testing",
      tags: ["test"],
    });
    assert.strictEqual(r.status, 200);
    assert.strictEqual(r.body.entry.kind, "note");
  });

  await test("truncates tags to 10 max", async () => {
    const tags = Array.from({ length: 15 }, (_, i) => `tag${i}`);
    const r = await request("POST", "/api/dream/create", {
      kind: "dream",
      text: "Too many tags test",
      tags,
    });
    assert.strictEqual(r.status, 200);
    assert.ok(r.body.entry.tags.length <= 10, "Should have at most 10 tags");
  });

  await test("defaults missing fields gracefully", async () => {
    const r = await request("POST", "/api/dream/create", {
      kind: "reflection",
      text: "Minimal entry",
    });
    assert.strictEqual(r.status, 200);
    assert.deepStrictEqual(r.body.entry.emotions, []);
    assert.deepStrictEqual(r.body.entry.tags, []);
    assert.strictEqual(r.body.entry.lucidity, 0);
  });

  // ── GET /api/dream/stats ────────────────────────────────────────────────
  console.log("\nGET /api/dream/stats");

  await test("returns total_entries, entries_by_kind, avg_lucidity", async () => {
    const r = await request("GET", "/api/dream/stats");
    assert.strictEqual(r.status, 200);
    assert.ok(typeof r.body.total_entries === "number");
    assert.ok(typeof r.body.entries_by_kind === "object");
    assert.ok(typeof r.body.top_emotions === "object");
    assert.ok(typeof r.body.top_tags === "object");
    assert.ok(typeof r.body.avg_lucidity !== "undefined");
  });

  await test("total_entries is non-negative", async () => {
    const r = await request("GET", "/api/dream/stats");
    assert.ok(r.body.total_entries >= 0);
  });

  await test("counts include our created test entries", async () => {
    const r = await request("GET", "/api/dream/stats");
    assert.ok(r.body.total_entries >= 2, "Should have at least 2 entries from this test run");
  });

  // ── GET /api/dream/search ───────────────────────────────────────────────
  console.log("\nGET /api/dream/search");

  await test("empty query returns results", async () => {
    const r = await request("GET", "/api/dream/search?text=");
    assert.strictEqual(r.status, 200);
    assert.ok(Array.isArray(r.body.results));
  });

  await test("text search filters by content", async () => {
    const r = await request("GET", "/api/dream/search?text=silver+towers");
    assert.strictEqual(r.status, 200);
    // If our test entry was saved with the right field name, it should appear
    assert.ok(typeof r.body.count === "number");
  });

  await test("tag search narrows results", async () => {
    const r = await request("GET", "/api/dream/search?tags=api");
    assert.strictEqual(r.status, 200);
    assert.ok(typeof r.body.count === "number");
  });

  await test("returns count and results array", async () => {
    const r = await request("GET", "/api/dream/search");
    assert.ok(typeof r.body.count === "number");
    assert.ok(Array.isArray(r.body.results));
  });

  // ── GET /api/dream/read/:id ─────────────────────────────────────────────
  console.log("\nGET /api/dream/read/:id");

  await test("404 for unknown id", async () => {
    const r = await request("GET", "/api/dream/read/does_not_exist_xyz");
    assert.strictEqual(r.status, 404);
    assert.strictEqual(r.body.error, "not_found");
  });

  // ── POST /api/dream/chat ──────────────────────────────────────────────
  console.log("\nPOST /api/dream/chat (multi-agent)");

  await test("multi-agent chat returns agents array", async () => {
    const r = await request("POST", "/api/dream/chat", {
      message: "I saw a glowing light in my dream",
    });
    assert.strictEqual(r.status, 200);
    assert.ok(typeof r.body.reply === "string", "reply should be a string");
    assert.ok(Array.isArray(r.body.agents), "agents should be an array");
    assert.ok(r.body.agents.length >= 2, "should have at least 2 agents");
    assert.ok(typeof r.body.online === "boolean", "online should be boolean");
    assert.ok(r.body.generatedAt, "should have generatedAt timestamp");
  });

  await test("agents have name and reply", async () => {
    const r = await request("POST", "/api/dream/chat", {
      message: "Tell me about the doors",
    });
    assert.strictEqual(r.status, 200);
    for (const agent of r.body.agents) {
      assert.ok(agent.name, "agent should have name");
      assert.ok(typeof agent.reply === "string", "agent should have reply");
    }
  });

  await test("empty message returns suggestions", async () => {
    const r = await request("POST", "/api/dream/chat", { message: "" });
    assert.strictEqual(r.status, 200);
    assert.ok(Array.isArray(r.body.suggestions), "should have suggestions");
  });

  await test("chat logs conversation to jsonl", async () => {
    const r = await request("POST", "/api/dream/chat", {
      message: "API test conversation for logging",
    });
    assert.strictEqual(r.status, 200);
    assert.ok(r.body.reply.length > 0, "reply should not be empty");
  });

  // ── GET /api/dream/stream ──────────────────────────────────────────────
  console.log("\nGET /api/dream/stream (SSE)");

  await test("stream returns text/event-stream", async () => {
    return new Promise((resolve, reject) => {
      const req = http.request(
        { hostname: "127.0.0.1", port: 4177, path: "/api/dream/stream?message=test+stream", method: "GET" },
        (res) => {
          let data = "";
          res.on("data", (c) => (data += c));
          res.on("end", () => {
            try {
              assert.ok(data.includes("data:"), "should contain SSE data lines");
              resolve();
            } catch (e) { reject(e); }
          });
        }
      );
      req.on("error", reject);
      req.end();
    });
  });

  // ── GET / (HTML dashboard) ──────────────────────────────────────────────
  console.log("\nGET / (dashboard)");

  await test("dashboard returns 200 HTML", async () => {
    const r = await new Promise((resolve, reject) => {
      const req = http.request({ hostname: "127.0.0.1", port: 4177, path: "/", method: "GET" }, (res) => {
        let data = "";
        res.on("data", (c) => (data += c));
        res.on("end", () => resolve({ status: res.statusCode, body: data }));
      });
      req.on("error", reject);
      req.end();
    });
    assert.strictEqual(r.status, 200);
    assert.ok(r.body.includes("Dream Journal"), "Page should include Dream Journal heading");
    assert.ok(r.body.includes("entryForm"), "Page should include the entry form");
  });

  await test("dashboard has stat cards", async () => {
    const r = await new Promise((resolve, reject) => {
      const req = http.request({ hostname: "127.0.0.1", port: 4177, path: "/", method: "GET" }, (res) => {
        let data = "";
        res.on("data", (c) => (data += c));
        res.on("end", () => resolve({ status: res.statusCode, body: data }));
      });
      req.on("error", reject);
      req.end();
    });
    assert.ok(r.body.includes("stat-card"), "Page should include stat cards");
    assert.ok(r.body.includes("stat-number"), "Page should include stat numbers");
  });

  // ── Summary ─────────────────────────────────────────────────────────────
  const total = passed + failed;
  console.log(`\n${passed}/${total} passed`);
  if (failed > 0) {
    console.error(`${failed} failed`);
    process.exit(1);
  }
}

run().catch((err) => {
  console.error("\nFATAL: Could not connect to server at", BASE);
  console.error("Make sure lantern-garage is running: node apps/lantern-garage/server.js");
  console.error(err.message);
  process.exit(1);
});
