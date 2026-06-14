/**
 * Kalshi suggestion engine — NOW-SLICE favorability for the swipe deck.
 *
 * Each card carries ONE favorable position the AI picks for *this instant*:
 * buy YES or buy NO, chosen from the current data slice only —
 *   - tick      : current yes_ask vs the previous tick (live momentum)
 *   - spread    : bid/ask tightness (how cleanly you can enter)
 *   - liquidity : resting size / liquidity on the book
 *   - urgency   : time to close (shorter game times rank first)
 * No historical trajectory is used — the decision is "only relevant to now's
 * data slice", so it stays valid under a tight (~6s) refresh.
 *
 * The deck is a binary: GREEN/right takes the favorable position, RED/left
 * passes. Nothing is sent here — the take routes through the existing dry-run /
 * kill-switch-gated /order endpoint.
 */

"use strict";

const kalshi = require("./kalshi-api");

// ── exit thresholds (acceptable bands for selling ASAP) ──────────────────────
const STOP_LOSS_PCT = -25;   // down this much vs entry → stop-loss, sell now
const TAKE_PROFIT_PCT = 25;  // up this much vs entry → lock the gain, sell
const FLATTEN_MINS = 30;     // this close to settlement → flatten the position

function num(v) {
  const f = parseFloat(v);
  return Number.isFinite(f) ? f : null;
}

function prevYesCents(m) {
  const f = parseFloat(m.previous_yes_ask_dollars);
  return Number.isFinite(f) ? Math.round(f * 100) : null;
}

function favorability(m, nowMs) {
  const yesA = m.yes_ask, yesB = m.yes_bid, noA = m.no_ask, noB = m.no_bid;
  const prevYes = prevYesCents(m);
  const tick = (yesA != null && prevYes != null) ? yesA - prevYes : 0;
  const spreadYes = (yesA != null && yesB != null) ? yesA - yesB : 99;
  const spreadNo = (noA != null && noB != null) ? noA - noB : 99;

  // favorable side from the now-slice: follow the live tick; tie → tighter book
  let side;
  if (tick > 0) side = "yes";
  else if (tick < 0) side = "no";
  else side = spreadYes <= spreadNo ? "yes" : "no";
  const sideAsk = side === "yes" ? yesA : noA;
  const spread = side === "yes" ? spreadYes : spreadNo;

  const close = m.close_time ? Date.parse(m.close_time) : NaN;
  const minsToClose = Number.isFinite(close) ? Math.max(0, (close - nowMs) / 60000) : Infinity;

  // conviction (all current-slice): momentum + book tightness + liquidity + urgency
  const mom = Math.min(20, Math.abs(tick) * 6);
  const tight = spread <= 1 ? 16 : spread <= 2 ? 9 : spread <= 4 ? 3 : 0;
  const liq = Math.min(14, Math.log10((parseFloat(m.liquidity_dollars) || 0) + 1) * 5);
  const urgency = minsToClose < 60 ? 12 : minsToClose < 240 ? 7 : minsToClose < 1440 ? 3 : 0;
  const conviction = Math.round(Math.min(82, 28 + mom + tight + liq + urgency));

  const dir = tick > 0 ? `YES ticked +${tick}¢`
            : tick < 0 ? `YES ticked ${tick}¢`
            : "flat tick";
  const tt = minsToClose === Infinity ? ""
           : minsToClose < 60 ? `closes ${Math.round(minsToClose)}m`
           : minsToClose < 1440 ? `closes ${Math.round(minsToClose / 60)}h`
           : `closes ${Math.round(minsToClose / 1440)}d`;
  const reason = [dir, `${spread}¢ spread`, tt].filter(Boolean).join(" · ");

  return { side, sideAsk, spread, tick, conviction, reason, minsToClose };
}

// average entry price per contract, in cents (best-effort across schema variants)
function costBasisCents(p, qty) {
  const expD = num(p.market_exposure_dollars);
  if (expD != null && qty > 0) return Math.round((Math.abs(expD) / qty) * 100);
  const exp = num(p.market_exposure);                 // total cost, cents
  if (exp != null && qty > 0) return Math.round(Math.abs(exp) / qty);
  const avg = num(p.average_price_dollars) ?? num(p.avg_price_dollars);
  if (avg != null) return Math.round(avg * 100);
  return null;
}

/**
 * Exit cards — held positions that should be SOLD now. These are the highest-
 * priority items and go on top: stop-losses first, then take-profits at the
 * acceptable band, then pre-close flattening. Each is a SELL of the held side.
 */
async function buildExits(mkByTicker, nowMs) {
  const posRes = await kalshi.getPositions({});
  const positions = (posRes.data && posRes.data.market_positions) || [];
  const exits = [];
  for (const p of positions) {
    const count = num(p.position) || 0;
    if (!count) continue;                              // flat — nothing to exit
    const ticker = p.ticker || p.market_ticker;
    const m = mkByTicker[ticker];
    const heldSide = count > 0 ? "yes" : "no";         // +YES / -NO
    const qty = Math.abs(count);
    const sellBid = m ? (heldSide === "yes" ? m.yes_bid : m.no_bid) : null;
    const cost = costBasisCents(p, qty);
    const pnlPct = (sellBid != null && cost) ? ((sellBid - cost) / cost) * 100 : null;

    const close = m && m.close_time ? Date.parse(m.close_time) : NaN;
    const mins = Number.isFinite(close) ? Math.max(0, (close - nowMs) / 60000) : Infinity;

    let tag = null, urgency = 0;
    if (pnlPct != null && pnlPct <= STOP_LOSS_PCT) { tag = "STOP-LOSS"; urgency = 100; }
    else if (pnlPct != null && pnlPct >= TAKE_PROFIT_PCT) { tag = "TAKE-PROFIT"; urgency = 92; }
    else if (mins <= FLATTEN_MINS) { tag = "FLATTEN"; urgency = 84; }
    if (!tag) continue;                                // position within band → hold

    const heldLabel = heldSide === "yes"
      ? (m && m.yes_sub_title) || "YES" : (m && m.no_sub_title) || "NO";
    const pnlTxt = pnlPct != null ? ` ${pnlPct >= 0 ? "+" : ""}${pnlPct.toFixed(0)}%` : "";
    const reason = tag === "FLATTEN"
      ? `FLATTEN · ${Math.round(mins)}m to close · sell ${qty} @ ${sellBid != null ? sellBid + "¢" : "mkt"}`
      : `${tag}${pnlTxt} · sell ${qty} @ ${sellBid != null ? sellBid + "¢" : "mkt"}`;

    exits.push({
      kind: "exit", action: "sell",
      ticker, title: (m && m.title) || ticker,
      yesLabel: (m && m.yes_sub_title) || "YES",
      noLabel: (m && m.no_sub_title) || "NO",
      yesPct: m && m.yes_ask != null && m.no_ask != null && m.yes_ask + m.no_ask > 0
        ? Math.round((m.yes_ask / (m.yes_ask + m.no_ask)) * 100) : null,
      favSide: heldSide, favLabel: heldLabel, favAsk: sellBid, qty,
      conviction: urgency, exitTag: tag, pnlPct: pnlPct != null ? +pnlPct.toFixed(1) : null,
      reason,
      minsToClose: Number.isFinite(mins) ? Math.round(mins) : null,
      close: (m && m.close_time) || "",
    });
  }
  exits.sort((a, b) => b.conviction - a.conviction);   // stop-loss → take-profit → flatten
  return exits;
}

async function getSuggestions({ limit = 60, series_ticker = "KXMLBGAME", collector = null } = {}) {
  let markets = [];

  // Prefer tight-band snapshot from collector (6s fresh, no API call)
  if (collector) {
    const latest = collector.getLatestMarkets();
    if (latest && latest.length > 0) {
      markets = latest;
    }
  }

  // Fall back to fresh API call if no cached snapshot
  if (markets.length === 0) {
    const mk = await kalshi.getMarkets({ series_ticker, status: "open", limit: 200 });
    markets = (mk.data && mk.data.markets) || [];
  }

  const nowMs = Date.now();
  const mkByTicker = {};
  for (const m of markets) mkByTicker[m.ticker] = m;

  // exits first — held positions to sell ASAP (best-effort; empty if no positions)
  let exits = [];
  try { exits = await buildExits(mkByTicker, nowMs); } catch { exits = []; }
  const exitTickers = new Set(exits.map((e) => e.ticker));

  const entries = [];
  for (const m of markets) {
    if (m.yes_ask == null && m.no_ask == null) continue;
    if (exitTickers.has(m.ticker)) continue;           // already an exit card
    const f = favorability(m, nowMs);
    const denom = (m.yes_ask || 0) + (m.no_ask || 0);
    const yesPct = denom > 0 ? Math.round((m.yes_ask / denom) * 100) : (m.yes_ask || 0);
    entries.push({
      kind: "entry", action: "buy",
      ticker: m.ticker,
      title: m.title || m.ticker,
      yesLabel: m.yes_sub_title || "YES",
      noLabel: m.no_sub_title || "NO",
      yesCents: m.yes_ask, noCents: m.no_ask, yesPct,
      favSide: f.side,                                   // 'yes' | 'no'
      favLabel: f.side === "yes" ? (m.yes_sub_title || "YES") : (m.no_sub_title || "NO"),
      favAsk: f.sideAsk,
      conviction: f.conviction,
      reason: f.reason,
      minsToClose: Number.isFinite(f.minsToClose) ? Math.round(f.minsToClose) : null,
      close: m.close_time || "",
    });
  }

  // entries: time-sensitive — soonest-closing first, then conviction
  entries.sort((a, b) => {
    const ma = a.minsToClose == null ? 1e9 : a.minsToClose;
    const mb = b.minsToClose == null ? 1e9 : b.minsToClose;
    if (ma !== mb) return ma - mb;
    return b.conviction - a.conviction;
  });

  // EXITS ON TOP (sell ASAP), then entries
  const cards = [...exits, ...entries].slice(0, limit);
  return {
    count: cards.length,
    exitCount: exits.length,
    generatedAt: new Date().toISOString(),
    note: "Exits (stop-loss / take-profit / flatten) first — sell ASAP — then now-slice favorable entries. Practice mode, gated dry-run.",
    cards,
  };
}

module.exports = { getSuggestions };
