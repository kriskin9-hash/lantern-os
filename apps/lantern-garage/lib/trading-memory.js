/**
 * Trading Phase 2 (#323): LanternOS-native trading memory.
 *
 * Persists trading orders and agent/signal log entries into:
 *  - a local JSONL trading store (./trading-store.js), the system of
 *    record for GET /api/trading/dashboard/{orders,agent-log}
 *  - CSF MemoryEngine-compatible Tier.TRACE records (./csf-memory-writer.js),
 *    queryable via GET /api/trading/memory/recent, GET /api/trading/csf-records,
 *    and by dream-chat / other LanternOS agents.
 *
 * Both dependencies are pure JS and local-first: no external service and
 * no Python process is spawned at runtime. (src/csf/trading_memory.py
 * implements the same CSF record shape in Python and is used by the
 * Python test suite as a reference implementation; it is optional and
 * not required for this module or for any LanternOS route.)
 *
 * Payload normalization: callers may pass either a bare array or a
 * wrapped object (`{ orders: [...] }`, `{ logs: [...] }`,
 * `{ agentLog: [...] }`, `{ agent_log: [...] }`) — see _toArray(). This
 * keeps recordNewOrders()/recordNewSignals() from silently no-op'ing
 * when fed a wrapped response shape.
 *
 * De-duplication: recordNewOrders()/recordNewSignals() track which items
 * have already been written (by order id, or by a content hash for
 * signals) in a small JSON seen-set persisted alongside the local
 * trading store, so repeated ingestion (e.g. an optional legacy sync
 * adapter polling an external source) does not produce a duplicate-write
 * storm. Direct POST /api/trading/{orders,agent-log} writes go through
 * the same path, so retried/duplicate POSTs are idempotent.
 *
 * Compatibility exports (queryRecentTradingRecords, ingestTradingData):
 * a parallel implementation of #323 landed on master that wrote CSF
 * records directly to data/csf_memory/raw.jsonl with its own in-memory
 * (per-process) dedup and a non-canonical checksum scheme. Rather than
 * keep two CSF writers, that implementation's exports are reproduced
 * here as thin wrappers over csf-memory-writer.js / recordNewOrders() /
 * recordNewSignals() so routes/trading.js's GET /api/trading/csf-records
 * and dashboard-proxy CSF wiring keep working, now backed by this
 * module's persisted dedup and ticker-extracting record shape.
 */

const fs = require("fs");
const path = require("path");

const csfMemory = require("./csf-memory-writer");
const tradingStore = require("./trading-store");

const MAX_SEEN = 500;

function _seenPath() {
  return path.join(tradingStore.dataDir(), "_seen.json");
}

function _loadSeen() {
  try {
    const data = JSON.parse(fs.readFileSync(_seenPath(), "utf8"));
    return {
      orders: new Set(Array.isArray(data.orders) ? data.orders : []),
      signals: new Set(Array.isArray(data.signals) ? data.signals : []),
    };
  } catch {
    return { orders: new Set(), signals: new Set() };
  }
}

function _saveSeen(seen) {
  try {
    const seenPath = _seenPath();
    fs.mkdirSync(path.dirname(seenPath), { recursive: true });
    const data = {
      orders: [...seen.orders].slice(-MAX_SEEN),
      signals: [...seen.signals].slice(-MAX_SEEN),
    };
    fs.writeFileSync(seenPath, JSON.stringify(data));
  } catch (e) {
    console.error("[trading-memory] Failed to persist seen-set:", e.message);
  }
}

let _seenCache = null;
function _seen() {
  if (!_seenCache) _seenCache = _loadSeen();
  return _seenCache;
}

/** Reset the in-memory seen-set cache (mainly for tests that swap data dirs). */
function _resetSeenCache() {
  _seenCache = null;
}

/**
 * Normalize a payload to an array. Accepts:
 *  - a bare array (returned as-is)
 *  - an object carrying the array under one of `keys` (checked in order),
 *    e.g. `{ orders: [...] }`, `{ logs: [...] }`, `{ agentLog: [...] }`
 *  - a single non-empty object with none of those keys, treated as one
 *    item (wrapped in a 1-element array) — covers POST bodies that send
 *    a single order/log entry directly
 *  - anything else (including `{}`/null/undefined) -> []
 *
 * This ensures wrapped payload shapes never silently no-op.
 */
function _toArray(data, keys) {
  if (Array.isArray(data)) return data;
  if (data && typeof data === "object") {
    for (const key of keys) {
      if (Array.isArray(data[key])) return data[key];
    }
    if (Object.keys(data).length > 0) return [data];
  }
  return [];
}

/** Write a single order into CSF as a Tier.TRACE record. */
function recordOrder(order) {
  return csfMemory.recordOrder(order || {});
}

/** Write a single agent-log entry into CSF as a Tier.TRACE record. */
function recordSignal(entry) {
  return csfMemory.recordSignal(entry || {});
}

/** Query recent trading trace records. kind: "order" | "signal" | undefined (both). */
function queryRecent({ limit = 20, kind } = {}) {
  return Promise.resolve(csfMemory.queryRecent({ limit, kind }));
}

/**
 * Read recent trading CSF records from the registry, most recent first.
 * Synchronous compat wrapper (matches the earlier #323 implementation's
 * signature) — used directly without `await` by GET /api/trading/csf-records.
 */
function queryRecentTradingRecords(limit = 50) {
  return csfMemory.queryRecent({ limit });
}

/**
 * Given a payload containing orders (bare array or `{ orders: [...] }`),
 * persist any orders not seen before into the local trading store and
 * CSF memory. Returns the list of newly-written orders. Errors for
 * individual orders are logged, never thrown.
 */
async function recordNewOrders(data) {
  const orders = _toArray(data, ["orders"]);
  if (orders.length === 0) return [];
  const seen = _seen();
  const written = [];
  let changed = false;
  for (const order of orders) {
    const id = order && order.id;
    if (!id || seen.orders.has(id)) continue;
    seen.orders.add(id);
    changed = true;
    try {
      await tradingStore.appendOrder(order);
      await recordOrder(order);
      written.push(order);
    } catch (e) {
      console.error("[trading-memory] recordOrder failed:", e.message);
    }
  }
  if (changed) _saveSeen(seen);
  return written;
}

/**
 * Given a payload containing agent-log entries (bare array, or wrapped in
 * `{ logs: [...] }` / `{ agentLog: [...] }` / `{ agent_log: [...] }`),
 * persist any entries not seen before into the local trading store and
 * CSF memory. Entries have no stable id, so dedup is by a hash of their
 * (time, agent, type, body) fields. Returns the list of newly-written
 * entries. Errors for individual entries are logged, never thrown.
 */
async function recordNewSignals(data) {
  const entries = _toArray(data, ["logs", "agentLog", "agent_log"]);
  if (entries.length === 0) return [];
  const seen = _seen();
  const written = [];
  let changed = false;
  for (const entry of entries) {
    if (!entry) continue;
    const key = `${entry.time || ""}|${entry.agent || ""}|${entry.type || ""}|${entry.body || ""}`;
    if (seen.signals.has(key)) continue;
    seen.signals.add(key);
    changed = true;
    try {
      await tradingStore.appendLogEntry(entry);
      await recordSignal(entry);
      written.push(entry);
    } catch (e) {
      console.error("[trading-memory] recordSignal failed:", e.message);
    }
  }
  if (changed) _saveSeen(seen);
  return written;
}

/**
 * Batch-ingest orders and/or signals (compat with the earlier #323
 * implementation's ingestTradingData()). Orders without an `id` get a
 * generated one so they aren't silently dropped by recordNewOrders()'s
 * id-based dedup. Errors for individual items are logged by
 * recordNewOrders()/recordNewSignals(), never thrown.
 */
async function ingestTradingData({ orders = [], signals = [] } = {}) {
  const stamped = orders.map((order) =>
    order && !order.id
      ? { ...order, id: `ingest_${Date.now()}_${Math.random().toString(36).slice(2, 8)}` }
      : order
  );
  const writtenOrders = await recordNewOrders({ orders: stamped });
  const writtenSignals = await recordNewSignals({ logs: signals });
  return {
    orders_written: writtenOrders.length,
    signals_written: writtenSignals.length,
    errors: [],
  };
}

module.exports = {
  recordOrder,
  recordSignal,
  queryRecent,
  queryRecentTradingRecords,
  recordNewOrders,
  recordNewSignals,
  ingestTradingData,
  _toArray,
  _resetSeenCache,
};
