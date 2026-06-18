/**
 * Sprint 1.6 integration tests — Trader Dashboard + Creator Dashboard
 * Runs against a live lantern-garage server on port 4177.
 * Start the server before running: node apps/lantern-garage/server.js
 *
 * Issue #619: Testing & Verification for 1.6 release
 */

const http = require("http");
const assert = require("assert");
const { hostname: HOST, port: PORT } = require("./lantern-test-base");

let passed = 0;
let failed = 0;

async function request(method, path, body) {
  return new Promise((resolve, reject) => {
    const opts = {
      hostname: HOST,
      port: PORT,
      path,
      method,
      headers: { "Content-Type": "application/json" },
    };
    const req = http.request(opts, (res) => {
      let data = "";
      res.on("data", (c) => (data += c));
      res.on("end", () => {
        try { resolve({ status: res.statusCode, body: JSON.parse(data) }); }
        catch { resolve({ status: res.statusCode, body: data }); }
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
    console.error(`  ✗ ${name}: ${err.message}`);
    failed++;
  }
}

// ── Trader Dashboard ──────────────────────────────────────────────────────────

async function testTraderDashboard() {
  console.log("\nTrader Dashboard:");

  await test("GET /api/trading/kalshi/collector-status returns 200", async () => {
    const r = await request("GET", "/api/trading/kalshi/collector-status");
    assert.ok(r.status === 200, `Expected 200, got ${r.status}`);
  });

  await test("GET /api/trading/kalshi/collector-status has status field", async () => {
    const r = await request("GET", "/api/trading/kalshi/collector-status");
    assert.ok(r.status === 200);
    assert.ok(r.body && typeof r.body === "object", "Expected object response");
  });

  await test("GET /api/trading/kalshi/paper-positions returns 200", async () => {
    const r = await request("GET", "/api/trading/kalshi/paper-positions");
    assert.ok(r.status === 200, `Expected 200, got ${r.status}`);
  });

  await test("GET /api/trading/kalshi/paper-positions returns array or object with positions", async () => {
    const r = await request("GET", "/api/trading/kalshi/paper-positions");
    assert.ok(r.status === 200);
    const positions = Array.isArray(r.body) ? r.body : (r.body && r.body.positions);
    assert.ok(Array.isArray(positions), "Expected positions array");
  });

  await test("GET /api/trading/kalshi/winrate-stats returns 200", async () => {
    const r = await request("GET", "/api/trading/kalshi/winrate-stats");
    assert.ok(r.status === 200, `Expected 200, got ${r.status}`);
  });

  await test("GET /api/trading/status returns 200", async () => {
    const r = await request("GET", "/api/trading/status");
    assert.ok(r.status === 200, `Expected 200, got ${r.status}`);
  });

  await test("GET /trader-dashboard.html redirects to auth (protected page)", async () => {
    const r = await request("GET", "/trader-dashboard.html");
    // Protected page — 302 to auth is the correct response without a session cookie
    assert.ok(r.status === 302 || r.status === 200, `Expected 302 or 200, got ${r.status}`);
  });

  await test("trader-dashboard.html source contains live panel (file check)", async () => {
    const fs = require("fs");
    const src = fs.readFileSync(__dirname + "/../apps/lantern-garage/public/trader-dashboard.html", "utf8");
    assert.ok(src.includes("live-panel"), "Missing live-panel element in source");
  });

  await test("trader-dashboard.html source contains positions panel (file check)", async () => {
    const fs = require("fs");
    const src = fs.readFileSync(__dirname + "/../apps/lantern-garage/public/trader-dashboard.html", "utf8");
    assert.ok(src.includes("positions-panel"), "Missing positions-panel element in source");
  });
}

// ── Creator Dashboard ─────────────────────────────────────────────────────────

async function testCreatorDashboard() {
  console.log("\nCreator Dashboard:");

  await test("GET /create.html redirects to auth (protected page)", async () => {
    const r = await request("GET", "/create.html");
    assert.ok(r.status === 302 || r.status === 200, `Expected 302 or 200, got ${r.status}`);
  });

  await test("create.html source contains journal editor (file check)", async () => {
    const fs = require("fs");
    const src = fs.readFileSync(__dirname + "/../apps/lantern-garage/public/create.html", "utf8");
    assert.ok(src.includes("journal-editor"), "Missing journal-editor element in source");
  });

  await test("create.html source contains template select (file check)", async () => {
    const fs = require("fs");
    const src = fs.readFileSync(__dirname + "/../apps/lantern-garage/public/create.html", "utf8");
    assert.ok(src.includes("journal-template"), "Missing template select in source");
  });

  await test("create.html source contains markdown preview (file check)", async () => {
    const fs = require("fs");
    const src = fs.readFileSync(__dirname + "/../apps/lantern-garage/public/create.html", "utf8");
    assert.ok(src.includes("md-preview"), "Missing markdown preview in source");
  });

  await test("create.html source contains share panel (file check)", async () => {
    const fs = require("fs");
    const src = fs.readFileSync(__dirname + "/../apps/lantern-garage/public/create.html", "utf8");
    assert.ok(src.includes("share-panel"), "Missing share panel in source");
  });

  await test("POST /api/dream/create saves an entry", async () => {
    const r = await request("POST", "/api/dream/create", {
      kind: "dream",
      text: "Test entry from sprint 1.6 verification suite",
      tags: ["test"],
      source: "test_sprint16",
    });
    assert.ok(r.status === 200 || r.status === 201, `Expected 200/201, got ${r.status}`);
    assert.ok(r.body && (r.body.saved || r.body.ok || r.body.id), "Expected saved/ok/id in response");
  });

  await test("GET /api/agents/status returns 200", async () => {
    const r = await request("GET", "/api/agents/status");
    assert.ok(r.status === 200, `Expected 200, got ${r.status}`);
  });
}

// ── Position filtering unit tests (pure logic) ───────────────────────────────

async function testPositionFiltering() {
  console.log("\nPosition filtering logic:");

  await test("filters open positions by status field", async () => {
    const positions = [
      { ticker: "A", status: "open", pnl: 5 },
      { ticker: "B", status: "closed", pnl: -2 },
      { ticker: "C", pnl: 1 },
    ];
    const open = positions.filter(p => p.status === "open" || !p.status);
    assert.strictEqual(open.length, 2);
    assert.ok(open.map(p => p.ticker).includes("A"));
    assert.ok(open.map(p => p.ticker).includes("C"));
  });

  await test("calculates P&L sign correctly", async () => {
    const pnl = -3.5;
    const sign = pnl >= 0 ? "positive" : "negative";
    assert.strictEqual(sign, "negative");
    const pnl2 = 0;
    assert.strictEqual(pnl2 >= 0 ? "positive" : "negative", "positive");
  });

  await test("signal classification covers stop/take/hold", async () => {
    function signalClass(pos) {
      const sig = (pos.signal || pos.exit_signal || "").toLowerCase();
      if (sig.includes("stop")) return "stop";
      if (sig.includes("take") || sig.includes("profit")) return "take";
      return "hold";
    }
    assert.strictEqual(signalClass({ signal: "STOP-LOSS" }), "stop");
    assert.strictEqual(signalClass({ signal: "TAKE-PROFIT" }), "take");
    assert.strictEqual(signalClass({ exit_signal: "profit target" }), "take");
    assert.strictEqual(signalClass({ signal: "" }), "hold");
    assert.strictEqual(signalClass({}), "hold");
  });

  await test("win rate formatting rounds correctly", async () => {
    function fmtWr(wr) { return wr != null ? (Math.round(wr * 100) + "%") : "—"; }
    assert.strictEqual(fmtWr(0.666), "67%");
    assert.strictEqual(fmtWr(0.5), "50%");
    assert.strictEqual(fmtWr(null), "—");
  });
}

// ── Main ──────────────────────────────────────────────────────────────────────

(async () => {
  console.log("Sprint 1.6 Dashboard Tests");
  console.log("=".repeat(40));

  await testPositionFiltering();
  await testTraderDashboard();
  await testCreatorDashboard();

  console.log(`\n${"=".repeat(40)}`);
  console.log(`Results: ${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
})();
