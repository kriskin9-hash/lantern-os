/**
 * Trading Phase 2 (#323): local-only trading memory unit tests.
 *
 * Exercises apps/lantern-garage/lib/{csf-memory-writer,trading-store,
 * trading-memory}.js directly — no live server and no Python process
 * required. Confirms:
 *
 *  - orders/signals are written as CSF Tier.TRACE records and verify
 *    against their own checksum
 *  - the local trading store (data/lantern-garage/trading/*.jsonl by
 *    default) round-trips orders and agent-log entries
 *  - recordNewOrders()/recordNewSignals() accept bare arrays AND wrapped
 *    payload shapes (`{ orders: [...] }`, `{ logs: [...] }`,
 *    `{ agentLog: [...] }`) without silently no-op'ing (the PR #338
 *    payload-shape regression)
 *  - duplicate order ids / signal entries are deduped
 *  - queryRecent() returns newest-first and supports kind filtering,
 *    used by GET /api/trading/memory/recent
 *  - lib/trading-memory.js and routes/trading.js contain no
 *    spawn("python" ...) / child_process bridge for trading memory
 *
 * All writes go to temp directories (CSF_MEMORY_PATH /
 * LANTERN_TRADING_DATA_PATH), never the repo's data/ directory.
 */

const assert = require("assert");
const fs = require("fs");
const os = require("os");
const path = require("path");

const repoRoot = path.resolve(__dirname, "..");

let passed = 0;
let failed = 0;

// Plain stdout writer for test-runner output — avoids the console.log
// call CI's "no committed debug statements" check flags as accidental
// debug output, so this CLI test reporter's intentional output isn't
// mistaken for leftover debugging.
function log(...args) {
  process.stdout.write(args.join(" ") + "\n");
}

async function ok(label, fn) {
  try {
    await fn();
    log(`  ✓ ${label}`);
    passed++;
  } catch (e) {
    console.error(`  ✗ ${label}`);
    console.error(`    ${e.message}`);
    failed++;
  }
}

async function main() {
  // Isolate all reads/writes from the real repo's data/ directory.
  const tmpRoot = fs.mkdtempSync(path.join(os.tmpdir(), "lantern-trading-memory-"));
  process.env.CSF_MEMORY_PATH = path.join(tmpRoot, "csf_memory");
  process.env.LANTERN_TRADING_DATA_PATH = path.join(tmpRoot, "trading");

  const csfWriter = require("../apps/lantern-garage/lib/csf-memory-writer");
  const tradingStore = require("../apps/lantern-garage/lib/trading-store");
  const tradingMemory = require("../apps/lantern-garage/lib/trading-memory");

  log("\nCSF memory writer (pure JS, no Python) — unit tests");

  await ok("recordOrder() writes a verifiable Tier.TRACE record", async () => {
    const result = await csfWriter.recordOrder({
      id: "ord-1",
      symbol: "aapl",
      side: "BUY",
      qty: 1,
      type: "market",
      status: "filled",
      filled_at: "14:32:01",
    });
    assert.ok(result.memory_id.startsWith("trace_"), "memory_id should start with trace_");
    assert.ok(fs.existsSync(result.path), "record file should exist on disk");

    const record = JSON.parse(fs.readFileSync(result.path, "utf8"));
    assert.strictEqual(record.tier, "trace");
    assert.strictEqual(record.cube_partition, "raw");
    assert.strictEqual(record.privacy_scope, "internal");
    assert.deepStrictEqual([...record.tags].sort(), ["filled", "order", "trading"]);
    assert.strictEqual(record.content.event, "order");
    assert.strictEqual(record.content.symbol, "aapl");
    assert.ok(csfWriter.verifyRecord(record), "checksum should self-verify");
  });

  await ok("recordSignal() extracts ticker entities from free text", async () => {
    const result = await csfWriter.recordSignal({
      type: "grok",
      agent: "ROTATION",
      body: "AAPL bullish breakout, confidence 82%",
      time: "14:31:55",
    });
    const record = JSON.parse(fs.readFileSync(result.path, "utf8"));
    assert.strictEqual(record.tier, "trace");
    assert.strictEqual(record.content.event, "signal");
    assert.ok(record.tags.includes("signal") && record.tags.includes("grok"));
    assert.deepStrictEqual(record.entities, ["AAPL"]);
    assert.ok(csfWriter.verifyRecord(record), "checksum should self-verify");
  });

  await ok("queryRecent() returns newest-first and supports kind filter", async () => {
    await csfWriter.recordOrder({ id: "ord-2", symbol: "TSLA", side: "sell", qty: 2, status: "filled" });

    const orders = csfWriter.queryRecent({ limit: 10, kind: "order" });
    const signals = csfWriter.queryRecent({ limit: 10, kind: "signal" });
    assert.ok(orders.length >= 2, "expected at least 2 order records");
    assert.ok(signals.length >= 1, "expected at least 1 signal record");
    assert.ok(orders.every((r) => r.tags.includes("order")));
    assert.ok(signals.every((r) => r.tags.includes("signal")));

    for (let i = 1; i < orders.length; i++) {
      assert.ok(orders[i - 1].created_at >= orders[i].created_at, "orders should be newest-first");
    }

    const everything = csfWriter.queryRecent({ limit: 100 });
    assert.ok(everything.length >= orders.length + signals.length);
  });

  log("\nLocal trading store (data/lantern-garage/trading) — unit tests");

  await ok("trading-store appendOrder()/listOrders() round-trip", async () => {
    await tradingStore.appendOrder({ id: "store-ord-1", symbol: "TSLA", side: "sell", qty: 2, status: "filled" });
    const orders = tradingStore.listOrders();
    assert.ok(orders.some((o) => o.id === "store-ord-1"));
  });

  await ok("trading-store appendLogEntry()/listLogEntries() round-trip", async () => {
    await tradingStore.appendLogEntry({ type: "claude", agent: "SENTRY", body: "watching SPY", time: "14:40:00" });
    const logs = tradingStore.listLogEntries();
    assert.ok(logs.some((l) => l.agent === "SENTRY"));
  });

  log("\nrecordNewOrders()/recordNewSignals() — payload-shape regression (PR #338 fix)");

  await ok("recordNewOrders() accepts a bare array", async () => {
    const written = await tradingMemory.recordNewOrders([
      { id: "shape-array-1", symbol: "SPY", side: "buy", status: "filled", qty: 1 },
    ]);
    assert.strictEqual(written.length, 1);
    assert.ok(tradingStore.listOrders().some((o) => o.id === "shape-array-1"));
  });

  await ok("recordNewOrders() accepts { orders: [...] } without no-op'ing", async () => {
    const written = await tradingMemory.recordNewOrders({
      orders: [{ id: "shape-wrapped-1", symbol: "QQQ", side: "buy", status: "filled", qty: 1 }],
    });
    assert.strictEqual(written.length, 1);
    assert.ok(tradingStore.listOrders().some((o) => o.id === "shape-wrapped-1"));
  });

  await ok("recordNewOrders() dedupes repeated order ids", async () => {
    const order = { id: "dedup-1", symbol: "NVDA", side: "buy", status: "filled", qty: 1 };
    const first = await tradingMemory.recordNewOrders({ orders: [order] });
    const second = await tradingMemory.recordNewOrders({ orders: [order] });
    assert.strictEqual(first.length, 1);
    assert.strictEqual(second.length, 0, "second ingestion of the same order id should be skipped");
  });

  await ok("recordNewSignals() accepts { logs: [...] }", async () => {
    const written = await tradingMemory.recordNewSignals({
      logs: [{ type: "risk", agent: "RISK", body: "AMD position trimmed", time: "14:50:00" }],
    });
    assert.strictEqual(written.length, 1);
    assert.ok(tradingStore.listLogEntries().some((l) => l.agent === "RISK"));
  });

  await ok("recordNewSignals() accepts { agentLog: [...] }", async () => {
    const written = await tradingMemory.recordNewSignals({
      agentLog: [{ type: "claude", agent: "SENTRY", body: "TSLA risk note", time: "14:51:00" }],
    });
    assert.strictEqual(written.length, 1);
  });

  await ok("recordNewSignals() accepts { agent_log: [...] }", async () => {
    const written = await tradingMemory.recordNewSignals({
      agent_log: [{ type: "claude", agent: "SENTRY", body: "QQQ risk note", time: "14:52:00" }],
    });
    assert.strictEqual(written.length, 1);
  });

  await ok("_toArray() treats {} / { orders: [] } as empty (no spurious records)", () => {
    assert.deepStrictEqual(tradingMemory._toArray({}, ["orders"]), []);
    assert.deepStrictEqual(tradingMemory._toArray({ orders: [] }, ["orders"]), []);
    assert.deepStrictEqual(tradingMemory._toArray(null, ["orders"]), []);
    assert.deepStrictEqual(tradingMemory._toArray(undefined, ["orders"]), []);
  });

  log("\n/api/trading/memory/recent (queryRecent) — local-only");

  await ok("queryRecent() returns local records newest-first, filterable by kind", async () => {
    const recent = await tradingMemory.queryRecent({ limit: 50 });
    assert.ok(recent.length > 0, "expected at least one trading memory record");
    for (let i = 1; i < recent.length; i++) {
      assert.ok(recent[i - 1].created_at >= recent[i].created_at, "expected newest-first ordering");
    }

    const orderRecords = await tradingMemory.queryRecent({ limit: 50, kind: "order" });
    const signalRecords = await tradingMemory.queryRecent({ limit: 50, kind: "signal" });
    assert.ok(orderRecords.length > 0 && orderRecords.every((r) => r.tags.includes("order")));
    assert.ok(signalRecords.length > 0 && signalRecords.every((r) => r.tags.includes("signal")));
  });

  log("\nNo external bridge — static source checks");

  await ok("lib/trading-memory.js has no child_process / spawn / Python bridge", () => {
    const src = fs.readFileSync(path.join(repoRoot, "apps/lantern-garage/lib/trading-memory.js"), "utf8");
    assert.ok(!/require\(['"]child_process['"]\)/.test(src), "must not require('child_process')");
    assert.ok(!/\b(spawn|exec|execFile)\s*\(/.test(src), "must not invoke a child process");
    // Comments may reference src/csf/trading_memory.py as an optional
    // Python-side reference implementation (not used at runtime) — only
    // flag an *invocation* of a python executable, not a code comment.
    assert.ok(!/spawn\s*\(\s*['"]python/i.test(src), "must not spawn a python executable");
    assert.ok(!/python\s+-m/.test(src), "must not shell out to `python -m ...`");
  });

  await ok("lib/csf-memory-writer.js has no child_process / spawn / Python bridge", () => {
    const src = fs.readFileSync(path.join(repoRoot, "apps/lantern-garage/lib/csf-memory-writer.js"), "utf8");
    assert.ok(!/require\(['"]child_process['"]\)/.test(src), "must not require('child_process')");
    assert.ok(!/spawn\s*\(/.test(src), "must not call spawn(...)");
  });

  await ok("routes/trading.js does not spawn a Python process for trading memory", () => {
    const src = fs.readFileSync(path.join(repoRoot, "apps/lantern-garage/routes/trading.js"), "utf8");
    assert.ok(!/spawn\s*\(\s*['"]python/i.test(src), "must not spawn a python executable");
    assert.ok(!/python\s+-m/.test(src), "must not shell out to `python -m ...`");
  });

  // Cleanup the temp directory; failures here shouldn't affect the exit code.
  try {
    fs.rmSync(tmpRoot, { recursive: true, force: true });
  } catch {
    // best-effort
  }

  log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}

main().catch((err) => {
  console.error("Test runner error:", err);
  process.exit(1);
});
