/**
 * Trading Phase 2 (#323): CSF Memory wiring for AI Trader orders & signals.
 *
 * Bridges Node -> Python so new orders (/api/orders) and new agent-log
 * entries (/api/agent-log) get persisted into the existing CSF MemoryEngine
 * (src/csf/trading_memory.py -> src/csf/memory_engine.py) as Tier.TRACE
 * records, queryable by dream-chat and other LanternOS agents.
 *
 * Follows the spawn(python -m ...) pattern used by lib/unified-agent.js.
 *
 * De-duplication: the AI Trader's /api/orders and /api/agent-log endpoints
 * are polled every ~5s by trading.html. To avoid a duplicate-write storm,
 * recordNewOrders()/recordNewSignals() track which items have already been
 * written (by order id, or by a content hash for signals) in a small JSON
 * seen-set persisted to data/csf_memory/_trading_seen.json, and only call
 * recordOrder()/recordSignal() for genuinely new items.
 */

const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");

const repoRoot = path.resolve(__dirname, "..", "..", "..");
const PY = process.platform === "win32" ? "python" : "python3";
const PY_ENV = { ...process.env, PYTHONPATH: path.join(repoRoot, "src") };

const SEEN_PATH = path.join(repoRoot, "data", "csf_memory", "_trading_seen.json");
const MAX_SEEN = 500;

function _loadSeen() {
  try {
    const data = JSON.parse(fs.readFileSync(SEEN_PATH, "utf8"));
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
    fs.mkdirSync(path.dirname(SEEN_PATH), { recursive: true });
    const data = {
      orders: [...seen.orders].slice(-MAX_SEEN),
      signals: [...seen.signals].slice(-MAX_SEEN),
    };
    fs.writeFileSync(SEEN_PATH, JSON.stringify(data));
  } catch (e) {
    console.error("[trading-memory] Failed to persist seen-set:", e.message);
  }
}

let _seenCache = null;
function _seen() {
  if (!_seenCache) _seenCache = _loadSeen();
  return _seenCache;
}

/** Run `python -m csf.trading_memory <args>`, parse stdout as JSON. */
function _runCli(args) {
  return new Promise((resolve, reject) => {
    const proc = spawn(PY, ["-m", "csf.trading_memory", ...args], {
      stdio: ["pipe", "pipe", "pipe"],
      cwd: repoRoot,
      env: PY_ENV,
    });
    let stdout = "";
    let stderr = "";
    proc.stdout.on("data", (d) => { stdout += d.toString(); });
    proc.stderr.on("data", (d) => { stderr += d.toString(); });
    proc.on("error", reject);
    proc.on("close", (code) => {
      if (code !== 0) {
        reject(new Error(stderr.trim() || `trading_memory exited with code ${code}`));
        return;
      }
      try {
        resolve(JSON.parse(stdout));
      } catch (e) {
        reject(new Error(`Invalid JSON from trading_memory: ${e.message}`));
      }
    });
    proc.stdin.end();
  });
}

/** Write a single order (from /api/orders) into CSF as a trace record. */
function recordOrder(order) {
  return _runCli(["--action", "record-order", "--data", JSON.stringify(order || {})]);
}

/** Write a single agent-log entry (from /api/agent-log) into CSF as a trace record. */
function recordSignal(entry) {
  return _runCli(["--action", "record-signal", "--data", JSON.stringify(entry || {})]);
}

/** Query recent trading trace records. kind: "order" | "signal" | undefined (both). */
function queryRecent({ limit = 20, kind } = {}) {
  const args = ["--action", "query", "--limit", String(limit)];
  if (kind) args.push("--kind", kind);
  return _runCli(args);
}

/**
 * Given the latest /api/orders array, write any orders not seen before into
 * CSF. Fire-and-forget — errors are logged, never thrown (must not break the
 * dashboard's polling response).
 */
async function recordNewOrders(orders) {
  if (!Array.isArray(orders) || orders.length === 0) return;
  const seen = _seen();
  let changed = false;
  for (const order of orders) {
    const id = order && order.id;
    if (!id || seen.orders.has(id)) continue;
    seen.orders.add(id);
    changed = true;
    try {
      await recordOrder(order);
    } catch (e) {
      console.error("[trading-memory] recordOrder failed:", e.message);
    }
  }
  if (changed) _saveSeen(seen);
}

/**
 * Given the latest /api/agent-log array, write any signals not seen before
 * into CSF. Entries have no stable id, so dedup is by a hash of their
 * (time, agent, type, body) fields — fire-and-forget, errors are logged.
 */
async function recordNewSignals(entries) {
  if (!Array.isArray(entries) || entries.length === 0) return;
  const seen = _seen();
  let changed = false;
  for (const entry of entries) {
    if (!entry) continue;
    const key = `${entry.time || ""}|${entry.agent || ""}|${entry.type || ""}|${entry.body || ""}`;
    if (seen.signals.has(key)) continue;
    seen.signals.add(key);
    changed = true;
    try {
      await recordSignal(entry);
    } catch (e) {
      console.error("[trading-memory] recordSignal failed:", e.message);
    }
  }
  if (changed) _saveSeen(seen);
}

module.exports = {
  recordOrder,
  recordSignal,
  queryRecent,
  recordNewOrders,
  recordNewSignals,
};
