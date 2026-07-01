// Kalshi grounding demo — ground a few LIVE weather markets and print the web-grounded
// P(YES) vs the market price + the fee-aware EV. Shows the profitable mechanism in one
// run: edge from information (a forecast) the thin market hasn't priced.
//
// Needs VERTEX_PROJECT (funded Gemini grounding) or a Gemini grounding key. Read-only —
// places no orders.
//
// Run: node experiments/kalshi_grounding_demo.js
"use strict";

const path = require("path");
const LIB = path.resolve(__dirname, "..", "apps", "lantern-garage", "lib");
const { groundMarket } = require(path.join(LIB, "kalshi-grounding"));
const { toCard } = require(path.join(LIB, "kalshi-event-suggester"));
const https = require("https");

const SERIES = process.argv.slice(2).length ? process.argv.slice(2)
  : ["KXHIGHCHI", "KXHIGHNY", "KXHIGHLAX", "KXHIGHMIA"];

function getMarkets(series) {
  return new Promise((resolve) => {
    https.get(`https://external-api.kalshi.com/trade-api/v2/markets?series_ticker=${series}&status=open&limit=8`,
      (r) => { let d = ""; r.on("data", (c) => d += c); r.on("end", () => { try { resolve(JSON.parse(d).markets || []); } catch { resolve([]); } }); })
      .on("error", () => resolve([]));
  });
}

(async () => {
  console.log(`\nGrounding live weather markets from ${SERIES.length} series (web search + Gemini/Vertex)…\n`);
  const picks = [];
  for (const s of SERIES) {
    const ms = await getMarkets(s);
    const m = ms.map((x) => ({
      ...x, yes_ask: x.yes_ask_dollars != null ? Math.round(x.yes_ask_dollars * 100) : null,
      no_ask: x.no_ask_dollars != null ? Math.round(x.no_ask_dollars * 100) : null,
    })).filter((x) => x.yes_ask != null && x.yes_ask > 8 && x.yes_ask < 92 && (x.rules_primary || "").trim())[0];
    if (m) picks.push(m);
  }

  for (const m of picks) {
    process.stdout.write(`• ${m.title}\n  researching… `);
    const g = await groundMarket(m, { force: true });
    const c = toCard(m, g, Date.now());
    if (c.grounding_status === "done") {
      console.log(`web-grounded ✓`);
      console.log(`  grounded P(YES) ${Math.round(g.p_yes * 100)}%  vs market ${c.yesPct}%  →  ${c.favLabel} @ ${c.favAsk}¢`);
      console.log(`  EV ${c.sigma0.ev_cents >= 0 ? "+" : ""}${c.sigma0.ev_cents}¢/contract  (${c.sigma0.verdict})  · ${g.model} · ${(g.sources || []).length} sources`);
      console.log(`  why: ${g.rationale}\n`);
    } else if (c.grounding_status === "knowledge-only") {
      console.log(`knowledge-only ⚠ (no live sources) — deferring to market, no edge claimed\n`);
    } else {
      console.log(`grounding unavailable\n`);
    }
  }

  console.log("Note: EV is a forecast vs an estimate. Profitability is proven FORWARD — each");
  console.log("paper pick is graded on resolution into the Σ₀ council (Brier + net after fees).\n");
})();
