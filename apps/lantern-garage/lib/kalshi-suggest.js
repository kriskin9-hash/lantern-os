/**
 * Kalshi suggestion engine — builds the "Tinder of trading" deck.
 *
 * Merges LIVE market prices (kalshi-api) with the CIO trajectory recorded in
 * data/kalshi/price-snapshots.jsonl to produce, per market, a recommended side
 * (green = bet YES / bullish, red = bet NO / bearish), a conviction score, and
 * a plain-English reason.
 *
 * Honesty note: training showed no short-horizon DRIFT edge in these odds, so
 * conviction is driven mainly by trajectory STABILITY (the CIO dilation idea) and
 * is deliberately modest. Reasons say what's actually behind the number. Nothing
 * here places an order — the card's green/red click goes through the existing
 * dry-run / kill-switch-gated /order route.
 *
 * Deck order: bearish (sell/NO) leans first, then bullish (buy/YES) — "sell
 * first, buy second" — each sub-sorted by conviction.
 */

"use strict";

const fs = require("fs");
const path = require("path");
const kalshi = require("./kalshi-api");

const SNAPSHOTS = path.resolve(__dirname, "..", "..", "..", "data", "kalshi", "price-snapshots.jsonl");

function loadSeries() {
  const series = {};   // ticker -> [{ts, p}]
  if (!fs.existsSync(SNAPSHOTS)) return series;
  for (const line of fs.readFileSync(SNAPSHOTS, "utf8").split("\n")) {
    const s = line.trim();
    if (!s) continue;
    let r;
    try { r = JSON.parse(s); } catch { continue; }
    const t = r.ticker;
    if (!t) continue;
    const ya = parseFloat(r.yes_ask) || 0, na = parseFloat(r.no_ask) || 0;
    if (ya + na <= 0) continue;
    (series[t] = series[t] || []).push({ ts: r.ts || "", p: ya / (ya + na) });
  }
  for (const t of Object.keys(series)) series[t].sort((a, b) => a.ts.localeCompare(b.ts));
  return series;
}

function signalFor(ps) {
  // Returns { trendPts, vol, depth, conviction, side, reason }
  if (!ps || ps.length < 4) {
    return {
      trendPts: 0, vol: 0, depth: ps ? ps.length : 0, conviction: 30, side: "yes",
      reason: "thin history — low conviction",
    };
  }
  const w = ps.slice(-8).map((x) => x.p);
  const diffs = w.slice(1).map((v, i) => v - w[i]);
  const trend = diffs.reduce((a, b) => a + b, 0) / diffs.length;       // prob/round
  const vol = Math.sqrt(diffs.reduce((a, b) => a + b * b, 0) / diffs.length);
  const trendPts = trend * 100;                                        // points/round
  const stab = Math.max(0, 1 - vol * 40);                             // 1 = rock steady
  // conviction: modest base + trend clarity + stability (capped — see honesty note)
  const conviction = Math.round(Math.min(85, 32 + Math.abs(trendPts) * 7 + stab * 26));
  const side = trend >= 0 ? "yes" : "no";
  const dir = trend >= 0 ? "odds rising" : "odds falling";
  const steady = vol * 100 < 0.6 ? "stable" : "choppy";
  const reason = `${dir} ${trendPts >= 0 ? "+" : ""}${trendPts.toFixed(1)} pts/round · ${steady} · ${ps.length} rounds`;
  return { trendPts: +trendPts.toFixed(2), vol: +(vol * 100).toFixed(2), depth: ps.length, conviction, side, reason };
}

async function getSuggestions({ limit = 60, series_ticker = "KXMLBGAME" } = {}) {
  const mk = await kalshi.getMarkets({ series_ticker, status: "open", limit: 200 });
  const markets = (mk.data && mk.data.markets) || [];
  const series = loadSeries();

  const cards = [];
  for (const m of markets) {
    const yes = m.yes_ask, no = m.no_ask;                 // cents (normalized by kalshi-api)
    if (yes == null && no == null) continue;
    const denom = (yes || 0) + (no || 0);
    const yesPct = denom > 0 ? Math.round((yes / denom) * 100) : (yes != null ? yes : 0);
    const sig = signalFor(series[m.ticker]);
    cards.push({
      ticker: m.ticker,
      title: m.title || m.ticker,
      yesLabel: m.yes_sub_title || "YES",
      noLabel: m.no_sub_title || "NO",
      yesCents: yes, noCents: no, yesPct,
      side: sig.side,
      conviction: sig.conviction,
      reason: sig.reason,
      trendPts: sig.trendPts,
      depth: sig.depth,
      close: m.close_time || "",
    });
  }

  // sell/NO leans first, then buy/YES; conviction desc within each; near-term tiebreak
  cards.sort((a, b) => {
    const sa = a.side === "no" ? 0 : 1, sb = b.side === "no" ? 0 : 1;
    if (sa !== sb) return sa - sb;
    if (b.conviction !== a.conviction) return b.conviction - a.conviction;
    return String(a.close).localeCompare(String(b.close));
  });

  return {
    count: cards.length,
    generatedAt: new Date().toISOString(),
    note: "Experimental CIO read — conviction from trajectory stability, not a proven edge. Practice mode.",
    cards: cards.slice(0, limit),
  };
}

module.exports = { getSuggestions };
