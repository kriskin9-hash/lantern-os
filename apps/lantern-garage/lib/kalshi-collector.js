/**
 * Kalshi Tight-Band Collector — polls live markets every 6s when active.
 *
 * Stores snapshots as JSONL in data/kalshi/tight-band-{YYYY-MM-DD}.jsonl
 * Each line: {ts, exitCount, entryCount, snapshot: {markets: [...], generatedAt}}
 *
 * The swipe deck uses the latest snapshot for live trajectory analysis instead
 * of making a fresh API call each time.
 */

"use strict";

const fs = require("fs");
const path = require("path");
const kalshi = require("./kalshi-api");

const KALSHI_DIR = path.resolve(__dirname, "..", "..", "..", "data", "kalshi");

let collector = null;
let latestSnapshot = null;
let isRunning = false;
let backoffUntil = null;

function getSnapshotPath() {
  const today = new Date().toISOString().split("T")[0];
  return path.join(KALSHI_DIR, `tight-band-${today}.jsonl`);
}

function logSnapshot(snapshot) {
  try {
    fs.mkdirSync(KALSHI_DIR, { recursive: true });
    const ts = new Date().toISOString();
    const line = JSON.stringify({
      ts,
      markets: snapshot.cards?.length || 0,
      exitCount: snapshot.exitCount || 0,
      snapshot,
    });
    fs.appendFileSync(getSnapshotPath(), line + "\n");
  } catch (e) {
    console.error("[Kalshi Collector] snapshot log failed:", e.message);
  }
}

/**
 * Fetch and store a fresh now-slice snapshot
 */
async function collectSnapshot() {
  if (backoffUntil && Date.now() < backoffUntil) return null;

  try {
    // Check if exchange is active
    const status = await kalshi.getExchangeStatus();
    if (status.status === 429) {
      const retryAfter = Math.max(30, parseInt(status.retryAfter || "60", 10)) * 1000;
      backoffUntil = Date.now() + retryAfter;
      console.warn(`[Kalshi Collector] 429 rate limit — pausing ${retryAfter / 1000}s`);
      return null;
    }
    if (!status.ok || !status.data?.exchange_active) {
      return null; // markets closed
    }

    // Get live markets
    const mk = await kalshi.getMarkets({
      series_ticker: "KXMLBGAME",
      status: "open",
      limit: 200,
    });

    if (mk.status === 429) {
      const retryAfter = Math.max(30, parseInt(mk.retryAfter || "60", 10)) * 1000;
      backoffUntil = Date.now() + retryAfter;
      console.warn(`[Kalshi Collector] 429 rate limit — pausing ${retryAfter / 1000}s`);
      return null;
    }
    if (!mk.ok || !mk.data?.markets) {
      return null;
    }

    const markets = mk.data.markets;
    if (markets.length === 0) {
      return null; // no open games
    }

    // Build snapshot structure matching kalshi-suggest output
    const snapshot = {
      count: markets.length,
      exitCount: 0, // exits require positions; would need separate call
      generatedAt: new Date().toISOString(),
      note: "Tight-band 6s snapshot for delta analysis",
      markets,
    };

    latestSnapshot = snapshot;
    logSnapshot(snapshot);
    return snapshot;
  } catch (e) {
    console.error("[Kalshi Collector] collection failed:", e.message);
    return null;
  }
}

/**
 * Start the 6-second polling loop
 */
function start() {
  if (isRunning) return;
  isRunning = true;
  console.log("[Kalshi Collector] starting 6s polling loop");

  // Initial collection
  collectSnapshot().catch((e) => console.error("[Kalshi Collector] init failed:", e));

  // Poll every 6 seconds
  collector = setInterval(() => {
    collectSnapshot().catch((e) =>
      console.error("[Kalshi Collector] polling failed:", e)
    );
  }, 6000);
}

/**
 * Stop the polling loop
 */
function stop() {
  if (collector) {
    clearInterval(collector);
    collector = null;
  }
  isRunning = false;
  console.log("[Kalshi Collector] stopped");
}

/**
 * Get the latest snapshot (used by kalshi-suggest to avoid redundant API calls)
 */
function getLatest() {
  return latestSnapshot;
}

/**
 * Get latest markets from the snapshot
 */
function getLatestMarkets() {
  return latestSnapshot?.markets || [];
}

function getStatus() {
  const now = Date.now();
  const inBackoff = backoffUntil != null && now < backoffUntil;
  return {
    running: isRunning,
    backoff: inBackoff,
    resumeAt: inBackoff ? new Date(backoffUntil).toISOString() : null,
    latestSnapshotAt: latestSnapshot?.generatedAt || null,
  };
}

module.exports = {
  start,
  stop,
  getLatest,
  getLatestMarkets,
  getStatus,
  collectSnapshot, // for manual testing
};
