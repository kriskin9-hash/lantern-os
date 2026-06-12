/**
 * Trading CSF Memory Writer
 * Writes order fills and agent signals into data/csf_memory/raw.jsonl
 * as Trace-tier MemoryRecord objects readable by Python's MemoryEngine.
 *
 * Dedup: in-memory seen-set per process lifetime; JSONL append is idempotent
 * for downstream consumers (they dedupe by memory_id).
 */

const path = require("path");
const crypto = require("crypto");
const { appendJsonlQueued } = require("./file-queue");

const REPO_ROOT = path.resolve(__dirname, "..", "..", "..");
const CSF_MEMORY_REGISTRY = path.join(REPO_ROOT, "data", "csf_memory", "raw.jsonl");

const _seenOrders = new Set();
const _seenSignals = new Set();

function _now() {
  return new Date().toISOString();
}

function _id(prefix, key) {
  const hash = crypto.createHash("sha256").update(key).digest("hex").slice(0, 12);
  return `${prefix}_${hash}`;
}

function _record(tier, content, tags, keywords, memoryId) {
  const now = _now();
  const base = {
    memory_id: memoryId,
    tier,
    created_at: now,
    updated_at: now,
    content,
    confidence: 0.75,
    privacy_scope: "internal",
    source_surface: "trading-dashboard",
    promoted_from: null,
    promotion_chain: [],
    cube_partition: "raw",
    tags,
    agents: ["trading-memory"],
    checksum: "",
    vector_embedding: null,
    keywords,
    entities: [],
    metadata: {},
    actor_id: "trading-system",
    actor_type: "system",
    confidence_reasoning: "",
    staleness_signals: [],
  };
  // Compute a simple checksum matching Python's approach (content hash)
  const payload = Object.fromEntries(Object.entries(base).filter(([k]) => k !== "checksum"));
  base.checksum = crypto.createHash("sha256")
    .update(JSON.stringify(payload, Object.keys(payload).sort()))
    .digest("hex");
  return base;
}

/**
 * Record a single order into CSF if not already seen.
 * @param {object} order - order object from AI Trader /api/orders
 */
async function recordOrder(order) {
  const key = String(order.id || order.order_id || JSON.stringify(order));
  if (_seenOrders.has(key)) return;
  _seenOrders.add(key);
  const memId = _id("trading_order", key);
  const rec = _record(
    "trace",
    { order_id: key, symbol: order.symbol, side: order.side, qty: order.qty, status: order.status, filled_at: order.filled_at || null, price: order.price || order.filled_avg_price || null, raw: order },
    ["trading", "order", String(order.symbol || ""), String(order.side || ""), String(order.status || "")].filter(Boolean),
    [String(order.symbol || ""), "order"].filter(Boolean),
    memId,
  );
  await appendJsonlQueued(CSF_MEMORY_REGISTRY, rec);
}

/**
 * Record a single agent signal into CSF if not already seen.
 * @param {object} signal - signal/log entry from AI Trader /api/agent-log
 */
async function recordSignal(signal) {
  const key = String(signal.id || signal.signal_id || signal.timestamp || JSON.stringify(signal)).slice(0, 64);
  if (_seenSignals.has(key)) return;
  _seenSignals.add(key);
  const memId = _id("trading_signal", key);
  const rec = _record(
    "trace",
    { signal_id: key, agent: signal.agent || signal.agent_type || "", action: signal.action || signal.signal || "", symbol: signal.symbol || "", confidence: signal.confidence || null, timestamp: signal.timestamp || null, raw: signal },
    ["trading", "signal", String(signal.agent || signal.agent_type || ""), String(signal.symbol || "")].filter(Boolean),
    [String(signal.symbol || ""), "signal", String(signal.agent || "")].filter(Boolean),
    memId,
  );
  await appendJsonlQueued(CSF_MEMORY_REGISTRY, rec);
}

/**
 * Ingest a batch of orders and/or signals. Silently drops errors per item.
 */
async function ingestTradingData({ orders = [], signals = [] } = {}) {
  const results = { orders_written: 0, signals_written: 0, errors: [] };
  for (const o of orders) {
    try { const before = _seenOrders.size; await recordOrder(o); if (_seenOrders.size > before) results.orders_written++; }
    catch (e) { results.errors.push(e.message); }
  }
  for (const s of signals) {
    try { const before = _seenSignals.size; await recordSignal(s); if (_seenSignals.size > before) results.signals_written++; }
    catch (e) { results.errors.push(e.message); }
  }
  return results;
}

/**
 * Read recent trading CSF records from the raw registry.
 * Returns up to `limit` records with tag "trading", most recent first.
 */
function queryRecentTradingRecords(limit = 50) {
  const fs = require("fs");
  try {
    const lines = fs.readFileSync(CSF_MEMORY_REGISTRY, "utf8").trim().split("\n").filter(Boolean);
    return lines
      .map(l => { try { return JSON.parse(l); } catch { return null; } })
      .filter(r => r && Array.isArray(r.tags) && r.tags.includes("trading"))
      .slice(-limit)
      .reverse();
  } catch {
    return [];
  }
}

module.exports = { recordOrder, recordSignal, ingestTradingData, queryRecentTradingRecords };
