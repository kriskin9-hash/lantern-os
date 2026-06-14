"use strict";

const fs = require("fs");
const path = require("path");
const FileQueue = require("./file-queue");

const repoRoot = path.resolve(__dirname, "..", "..", "..");
const CSF_MEMORY_DIR = path.join(repoRoot, "data", "csf_memory");
const PERFORMANCE_LOG = path.join(CSF_MEMORY_DIR, "strategy-performance.jsonl");

// Ensure directory exists
function _ensureDir() {
  if (!fs.existsSync(CSF_MEMORY_DIR)) {
    fs.mkdirSync(CSF_MEMORY_DIR, { recursive: true });
  }
}

_ensureDir();

// Use file-queue for safe concurrent appends
let _queue = null;
function _getQueue() {
  if (!_queue) {
    _queue = new FileQueue(PERFORMANCE_LOG);
  }
  return _queue;
}

/**
 * Log a strategy performance record
 *
 * @param {Object} record - performance measurement
 *   - timestamp (ms, required)
 *   - commit_hash (git SHA or strategy version ID)
 *   - strategy_id (e.g. "2026-06-10-conviction-v3")
 *   - regime (Conviction_Trend | Reversion | Shock | Liquidity_Fragility | Event_Countdown)
 *   - pnl (realized P&L in dollars)
 *   - drawdown (max drawdown %)
 *   - stability (metric 0-1, higher = better)
 *   - position_id (market position identifier)
 *   - market (ticker/market identifier)
 *   - is_live (1 = live, 0 = paper/simulated)
 *   - extra (optional object for additional context)
 */
async function logPerformance(record) {
  try {
    _ensureDir();

    // Validate required fields
    if (!record.timestamp) record.timestamp = Date.now();
    if (!record.commit_hash) record.commit_hash = "unknown";
    if (!record.strategy_id) record.strategy_id = "default";
    if (!record.regime) record.regime = "Unknown";
    if (record.pnl === undefined) record.pnl = 0;
    if (record.drawdown === undefined) record.drawdown = 0;
    if (record.stability === undefined) record.stability = 0.5;
    if (record.is_live === undefined) record.is_live = 0;

    // Serialize to JSONL
    const line = JSON.stringify({
      timestamp: record.timestamp,
      commit_hash: record.commit_hash,
      strategy_id: record.strategy_id,
      regime: record.regime,
      pnl: parseFloat(record.pnl),
      drawdown: parseFloat(record.drawdown),
      stability: parseFloat(record.stability),
      position_id: record.position_id || null,
      market: record.market || null,
      is_live: record.is_live,
      ...(record.extra || {}),
    });

    // Append via file-queue (safe concurrent appends)
    await _getQueue().append(line);
    return true;
  } catch (error) {
    console.error("[StrategyPerformanceLogger] Failed to log:", error.message);
    return false;
  }
}

/**
 * Read recent performance records
 *
 * @param {Number} limit - max records to return
 * @param {Object} filter - optional filters
 *   - regime: filter by regime type
 *   - strategy_id: filter by strategy
 *   - minTimestamp: only records after this time
 * @returns {Array<Object>} performance records
 */
function readPerformanceRecords(limit = 100, filter = {}) {
  _ensureDir();

  if (!fs.existsSync(PERFORMANCE_LOG)) {
    return [];
  }

  try {
    const lines = fs
      .readFileSync(PERFORMANCE_LOG, "utf8")
      .trim()
      .split("\n")
      .filter(Boolean);

    let records = [];
    for (const line of lines) {
      try {
        const rec = JSON.parse(line);
        records.push(rec);
      } catch {}
    }

    // Apply filters
    if (filter.regime) {
      records = records.filter(r => r.regime === filter.regime);
    }
    if (filter.strategy_id) {
      records = records.filter(r => r.strategy_id === filter.strategy_id);
    }
    if (filter.minTimestamp) {
      records = records.filter(r => r.timestamp >= filter.minTimestamp);
    }
    if (filter.is_live !== undefined) {
      records = records.filter(r => r.is_live === filter.is_live);
    }

    // Return most recent first
    return records.reverse().slice(0, limit);
  } catch (error) {
    console.error("[StrategyPerformanceLogger] Failed to read records:", error.message);
    return [];
  }
}

/**
 * Get fitness score for a strategy in a given regime
 *
 * @param {String} strategy_id
 * @param {String} regime
 * @param {Number} windowMs - lookback window (default 1 hour)
 * @returns {Object} { pnl, drawdown, stability, count, trend }
 */
function getStrategyFitness(strategy_id, regime, windowMs = 3_600_000) {
  const minTime = Date.now() - windowMs;
  const records = readPerformanceRecords(1000, {
    strategy_id,
    regime,
    minTimestamp: minTime,
  });

  if (records.length === 0) {
    return { pnl: 0, drawdown: 0, stability: 0.5, count: 0, trend: 0 };
  }

  const pnls = records.map(r => r.pnl);
  const drawdowns = records.map(r => r.drawdown);
  const stabilities = records.map(r => r.stability);

  const totalPnL = pnls.reduce((a, b) => a + b, 0);
  const avgDrawdown = drawdowns.reduce((a, b) => a + b, 0) / drawdowns.length;
  const avgStability = stabilities.reduce((a, b) => a + b, 0) / stabilities.length;

  // Trend: is PnL improving over time?
  const trend =
    records.length > 1
      ? pnls[0] - pnls[records.length - 1] // positive = improving (newer records first)
      : 0;

  return {
    pnl: totalPnL,
    drawdown: avgDrawdown,
    stability: avgStability,
    count: records.length,
    trend,
  };
}

/**
 * Get best strategy for a given regime
 *
 * @param {String} regime
 * @param {Array<String>} strategy_ids - candidates to compare
 * @param {Number} windowMs - lookback window
 * @returns {Object} { strategy_id, fitness }
 */
function getBestStrategyForRegime(regime, strategy_ids = [], windowMs = 3_600_000) {
  let best = null;
  let bestScore = -Infinity;

  for (const sid of strategy_ids) {
    const fitness = getStrategyFitness(sid, regime, windowMs);
    // Score: total PnL weighted by stability, penalize drawdown
    const score = fitness.pnl * fitness.stability - Math.abs(fitness.drawdown) * 0.5;

    if (score > bestScore) {
      bestScore = score;
      best = { strategy_id: sid, fitness, score };
    }
  }

  return best || { strategy_id: strategy_ids[0] || "default", fitness: { pnl: 0, drawdown: 0, stability: 0.5, count: 0 }, score: 0 };
}

module.exports = {
  logPerformance,
  readPerformanceRecords,
  getStrategyFitness,
  getBestStrategyForRegime,
};
