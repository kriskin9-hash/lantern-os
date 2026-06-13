/**
 * Crypto intraday market suggester — 15min, hourly, daily crypto predictions.
 * Markets close in minutes/hours, NOT days. Perfect for convergence trading.
 */

"use strict";

const kalshi = require("./kalshi-api");

function isShortWindowMarket(m, nowMs) {
  // Include ANY market closing in 1-6 hours (convergence window)
  const closeMs = new Date(m.close_time).getTime();
  const minsToClose = Math.round((closeMs - nowMs) / 60000);
  return minsToClose > 0 && minsToClose <= 360; // 0-6 hours
}

function scoreIntraday(m, nowMs) {
  const closeMs = new Date(m.close_time).getTime();
  const minsToClose = Math.round((closeMs - nowMs) / 60000);

  // Urgency: sooner = higher score
  let urgency = 0;
  if (minsToClose <= 5) urgency = 100;        // NOW
  else if (minsToClose <= 15) urgency = 90;   // very soon
  else if (minsToClose <= 30) urgency = 80;   // soon (12pm markets)
  else if (minsToClose <= 60) urgency = 70;   // within 1h
  else if (minsToClose <= 120) urgency = 60;  // within 2h
  else if (minsToClose <= 360) urgency = 40;  // within 6h
  else urgency = 10;                           // too far

  // Spread quality: tighter = higher score
  const spread = Math.abs((m.yes_ask || 0) - (m.no_ask || 0));
  let spreadScore = 0;
  if (spread <= 1) spreadScore = 20;
  else if (spread <= 2) spreadScore = 15;
  else if (spread <= 4) spreadScore = 10;
  else if (spread <= 6) spreadScore = 5;

  // Tick/momentum
  const prevYes = m.previous_yes_ask_dollars ? Math.round(m.previous_yes_ask_dollars * 100) : null;
  const currentYes = m.yes_ask || 0;
  const tick = (prevYes && currentYes) ? Math.abs(currentYes - prevYes) : 0;
  const momentumScore = Math.min(15, tick * 3);

  return urgency + spreadScore + momentumScore;
}

async function getCryptoSuggestions({ limit = 20, collector = null } = {}) {
  let markets = [];

  // Try collector cache first
  if (collector) {
    const latest = collector.getLatestMarkets();
    if (latest && latest.length > 0) {
      markets = latest.filter(isCryptoMarket);
    }
  }

  // Fall back to API
  const nowMs = Date.now();
  if (markets.length === 0) {
    try {
      const mk = await kalshi.getMarkets({ status: "open", limit: 500 });
      markets = (mk.data && mk.data.markets || []).filter(m => isShortWindowMarket(m, nowMs));
    } catch (e) {
      return { count: 0, cards: [], error: e.message };
    }
  }

  if (markets.length === 0) {
    return { count: 0, cards: [], note: "No markets closing in next 6 hours" };
  }
  const cards = [];

  for (const m of markets) {
    const closeMs = new Date(m.close_time).getTime();
    const minsToClose = Math.round((closeMs - nowMs) / 60000);

    if (minsToClose <= 0) continue; // expired

    const score = scoreIntraday(m, nowMs);
    const yesAsk = m.yes_ask || 0;
    const noAsk = m.no_ask || 0;
    const denom = yesAsk + noAsk;
    const yesPct = denom > 0 ? Math.round((yesAsk / denom) * 100) : 50;

    // Determine favorable side: follow the tighter book or recent tick
    let favSide = "yes";
    if ((m.yes_ask || 99) > (m.no_ask || 99)) {
      favSide = "no"; // NO is cheaper
    }

    const spread = Math.abs(yesAsk - noAsk);
    const reason = [
      `${minsToClose}m to close`,
      `${spread}¢ spread`,
      yesAsk === noAsk ? "even odds" : (yesPct > 50 ? "YES favored" : "NO favored")
    ].join(" · ");

    cards.push({
      kind: "entry",
      action: "buy",
      ticker: m.ticker,
      title: m.title || m.ticker,
      yesLabel: "YES",
      noLabel: "NO",
      yesCents: yesAsk,
      noCents: noAsk,
      yesPct,
      favSide,
      favLabel: favSide === "yes" ? "YES" : "NO",
      favAsk: favSide === "yes" ? yesAsk : noAsk,
      conviction: Math.round(Math.min(99, 40 + (score || 0) / 3)),
      reason,
      minsToClose,
      close: m.close_time,
      urgencyLevel: minsToClose <= 5 ? "critical" : minsToClose <= 30 ? "hot" : "normal",
      convergenceScore: score
    });
  }

  // Sort by convergence score (urgency + spread + momentum)
  cards.sort((a, b) => b.convergenceScore - a.convergenceScore);

  return {
    count: cards.length,
    generatedAt: new Date().toISOString(),
    note: "Crypto intraday markets — 15m, 1h, daily predictions. Peak accuracy window.",
    cards: cards.slice(0, limit)
  };
}

module.exports = { getCryptoSuggestions, isCryptoMarket };
