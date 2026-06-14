"use strict";

/**
 * Paper trading ledger for Kalshi dry-run positions.
 * Records entries, polls current market prices, auto-exits on stop-loss / take-profit.
 *
 * Stop-loss  : pnlPct <= -30  (e.g. bought YES @ 50¢, now bid 35¢ → -30%)
 * Take-profit: pnlPct >= +40  (e.g. bought YES @ 50¢, now bid 70¢ → +40%)
 */

const fs = require("fs");
const path = require("path");

const KALSHI_DIR = path.resolve(__dirname, "../../../data/kalshi");
const PAPER_FILE = path.join(KALSHI_DIR, "paper-positions.jsonl");
const STOP_LOSS_PCT  = -30;
const TAKE_PROFIT_PCT = 40;

function readAll() {
  if (!fs.existsSync(PAPER_FILE)) return [];
  return fs.readFileSync(PAPER_FILE, "utf8")
    .trim().split("\n").filter(Boolean)
    .map(l => { try { return JSON.parse(l); } catch { return null; } })
    .filter(Boolean);
}

function append(entry) {
  fs.mkdirSync(KALSHI_DIR, { recursive: true });
  fs.appendFileSync(PAPER_FILE, JSON.stringify(entry) + "\n");
}

function getOpen() {
  const all = readAll();
  const closedIds = new Set(all.filter(e => e.event === "close").map(e => e.id));
  return all.filter(e => e.event === "open" && !closedIds.has(e.id));
}

function openPosition(o) {
  const id = o.id || `paper_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
  const entry = { event: "open", id, ts: new Date().toISOString(), ...o };
  append(entry);
  return entry;
}

function closePosition(id, { exitTag = "MANUAL", exitPriceCents = null, pnlPct = null } = {}) {
  append({ event: "close", id, exitTag, exitPriceCents, pnlPct, closedAt: new Date().toISOString() });
  return { ok: true, id, exitTag };
}

// Normalize price cents from Kalshi market object (API may return dollars or cents)
function toCents(market, centField, dollarField) {
  if (market[centField] != null) return market[centField];
  const d = parseFloat(market[dollarField]);
  return Number.isFinite(d) ? Math.round(d * 100) : null;
}

async function pollOpen() {
  const open = getOpen();
  if (open.length === 0) return [];

  const kalshi = require("./kalshi-api");
  const results = [];

  for (const pos of open) {
    try {
      const r = await kalshi.getMarket(pos.ticker);
      const market = r.data?.market;

      if (!market) {
        if (r.status === 404) {
          closePosition(pos.id, { exitTag: "RESOLVED" });
          results.push({ ...pos, resolved: true, pnlPct: null, status: "resolved" });
        } else {
          results.push({ ...pos, error: "market unavailable", status: "error" });
        }
        continue;
      }

      const entryCents = pos.limitCents || 50;
      const side = pos.side; // 'yes' | 'no'

      const currentAsk = toCents(market, side === "yes" ? "yes_ask" : "no_ask",
                                         side === "yes" ? "yes_ask_dollars" : "no_ask_dollars")
                         ?? entryCents;
      const currentBid = toCents(market, side === "yes" ? "yes_bid" : "no_bid",
                                         side === "yes" ? "yes_bid_dollars" : "no_bid_dollars")
                         ?? currentAsk;

      // P&L: entered at ask, exit at bid (realistic with spread)
      const pnlCents = currentBid - entryCents;
      const pnlPct   = Math.round((pnlCents / entryCents) * 100);

      const autoExit = pnlPct <= STOP_LOSS_PCT  ? "STOP-LOSS"
                     : pnlPct >= TAKE_PROFIT_PCT ? "TAKE-PROFIT"
                     : null;

      const minsToClose = market.close_time
        ? Math.round((new Date(market.close_time).getTime() - Date.now()) / 60000)
        : null;

      // Expired market → auto-close
      if (minsToClose !== null && minsToClose <= 0) {
        closePosition(pos.id, { exitTag: "EXPIRED", exitPriceCents: currentBid, pnlPct });
        results.push({ ...pos, title: market.title || pos.ticker,
          expired: true, pnlPct, pnlCents, currentBid, minsToClose: 0, status: "expired" });
        continue;
      }

      results.push({
        ...pos,
        title: market.title || pos.ticker,
        entryCents, currentAsk, currentBid,
        pnlCents, pnlPct, autoExit, minsToClose,
        status: autoExit ? "exit-pending" : "open",
      });
    } catch (e) {
      results.push({ ...pos, error: e.message, status: "error" });
    }
  }
  return results;
}

module.exports = { openPosition, closePosition, getOpen, pollOpen };
