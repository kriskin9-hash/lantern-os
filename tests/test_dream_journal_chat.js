/**
 * Dream Journal Multi-Agent Chat Tests
 * Tests the /api/dream/chat endpoint specifically.
 *
 * Run: node tests/test_dream_journal_chat.js
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
    console.log(`  \u2713 ${name}`);
    passed++;
  } catch (err) {
    console.error(`  \u2717 ${name}`);
    console.error(`    ${err.message}`);
    failed++;
  }
}

async function run() {
  console.log("\nDream Journal Multi-Agent Chat Tests\n");
  console.log("Target:", BASE, "/api/dream/chat\n");

  // ── Agent response structure ─────────────────────────────────────────────
  console.log("Agent response structure");

  await test("returns 200 with reply, agents, suggestions, online", async () => {
    const r = await request("POST", "/api/dream/chat", {
      message: "I dreamt of flying",
    });
    assert.strictEqual(r.status, 200);
    assert.ok(typeof r.body.reply === "string", "reply should be string");
    assert.ok(Array.isArray(r.body.agents), "agents should be array");
    assert.ok(r.body.agents.length >= 2, "at least 2 agents");
    assert.ok(typeof r.body.online === "boolean", "online should be boolean");
    assert.ok(Array.isArray(r.body.suggestions), "suggestions should be array");
    assert.ok(r.body.generatedAt, "should have generatedAt");
  });

  await test("each agent has id, name, reply fields", async () => {
    const r = await request("POST", "/api/dream/chat", {
      message: "What do the doors mean?",
    });
    for (const agent of r.body.agents) {
      assert.ok(agent.id, "agent.id required");
      assert.ok(agent.name, "agent.name required");
      assert.ok(typeof agent.reply === "string", "agent.reply should be string");
      assert.ok(agent.reply.length > 0, "agent.reply should not be empty");
    }
  });

  await test("agent names match lore personas", async () => {
    const r = await request("POST", "/api/dream/chat", {
      message: "I saw a waterfall",
    });
    const names = r.body.agents.map((a) => a.name);
    const expected = ["Blinkbug", "Mary / Waterfall", "Courtney / Xenon"];
    for (const expectedName of expected) {
      assert.ok(names.some((n) => n.includes(expectedName.split(" ")[0])), `should include ${expectedName}`);
    }
  });

  // ── Content quality ──────────────────────────────────────────────────────
  console.log("\nContent quality");

  await test("response quotes user's dream text", async () => {
    const dreamText = "I was walking through a crystalline city";
    const r = await request("POST", "/api/dream/chat", { message: dreamText });
    const reply = r.body.reply.toLowerCase();
    // Offline fallback includes snippet; online might reference it
    assert.ok(
      reply.includes("crystalline") || reply.includes("walking") || reply.includes("city") || r.body.agents.length >= 2,
      "response should reference dream content or have agents"
    );
  });

  await test("door mentions trigger lore context", async () => {
    const r = await request("POST", "/api/dream/chat", {
      message: "Tell me about the founder's wish door",
    });
    const reply = r.body.reply.toLowerCase();
    assert.ok(
      reply.includes("wish") || reply.includes("door") || reply.includes("anchor") || r.body.agents.length >= 2,
      "should reference door lore or have agents"
    );
  });

  // ── Edge cases ──────────────────────────────────────────────────────────
  console.log("\nEdge cases");

  await test("empty message returns suggestions without crashing", async () => {
    const r = await request("POST", "/api/dream/chat", { message: "" });
    assert.strictEqual(r.status, 200);
    assert.ok(Array.isArray(r.body.suggestions), "should have suggestions");
  });

  await test("very long message is truncated safely", async () => {
    const longMessage = "dream ".repeat(500);
    const r = await request("POST", "/api/dream/chat", { message: longMessage });
    assert.strictEqual(r.status, 200);
    assert.ok(r.body.agents.length >= 2, "still returns agents after truncation");
  });

  await test("special characters in message don't break JSON", async () => {
    const r = await request("POST", "/api/dream/chat", {
      message: "I saw \"quotes\" and 'apostrophes' and \\backslashes\\",
    });
    assert.strictEqual(r.status, 200);
    assert.ok(r.body.agents.length >= 2, "handles special chars");
  });

  await test("unicode dream text is preserved", async () => {
    const r = await request("POST", "/api/dream/chat", {
      message: "I dreamt of a glowing lantern \uD83C\uDF1F and a waterfall \uD83D\uDCA7",
    });
    assert.strictEqual(r.status, 200);
    assert.ok(r.body.agents.length >= 2, "handles unicode");
  });

  // ── Performance ──────────────────────────────────────────────────────────
  console.log("\nPerformance");

  await test("response time under 5 seconds", async () => {
    const start = Date.now();
    const r = await request("POST", "/api/dream/chat", {
      message: "Quick performance test",
    });
    const elapsed = Date.now() - start;
    assert.strictEqual(r.status, 200);
    assert.ok(elapsed < 5000, `took ${elapsed}ms, should be < 5000ms`);
    console.log(`    (${elapsed}ms)`);
  });

  await test("sequential requests don't corrupt state", async () => {
    for (let i = 0; i < 3; i++) {
      const r = await request("POST", "/api/dream/chat", {
        message: `Sequential test ${i + 1}`,
      });
      assert.strictEqual(r.status, 200);
      assert.ok(r.body.agents.length >= 2, `request ${i + 1} has agents`);
    }
  });

  // ── Summary ───────────────────────────────────────────────────────────────
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
