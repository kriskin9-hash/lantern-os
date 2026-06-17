/**
 * Flywheel metrics test for the Convergence Router.
 *
 * Verifies the live lockup/slippage/stall counters added to
 * apps/lantern-garage/lib/convergence-router.js — turning the previously
 * *asserted* "~90% local hit" into measured numbers.
 *
 * Taxonomy:
 *   lockup — served from the flywheel (cache/template/deterministic), no recompute
 *   slip   — recomputed fresh or fell back locally (no cache reuse)
 *   stall  — genuinely needs the external model (needs_llm)
 *
 * Run:  node tests/test_convergence_router_flywheel.js
 */
"use strict";

const assert = require("assert");
const { ConvergenceRouter } = require("../apps/lantern-garage/lib/convergence-router");

function eq(actual, expected, msg) {
  assert.strictEqual(actual, expected, `${msg}: expected ${expected}, got ${actual}`);
}

(async () => {
  const r = new ConvergenceRouter();
  r.savePatternCache = () => {};          // don't mutate the real cache on disk
  r.patterns = { marketPatterns: {}, intentPatterns: {}, codePatterns: {} };
  r.resetFlywheelMetrics();

  // ── lockups (served from the flywheel) ──
  r.patterns.marketPatterns["KXTST"] = { trend: "up", timestamp: new Date().toISOString() };
  let out = await r.routeMarketSearch("KXTST");
  eq(out.source, "cache", "market cache hit");

  const intentMsg = "debug the trace log breakpoint";   // → blinkbug, strong winner
  r.patterns.intentPatterns[r.hashIntent(intentMsg)] = { agent_id: "blinkbug", confidence: 0.9 };
  out = await r.routeIntent(intentMsg);
  eq(out.source, "cache_validated", "intent cache validated");

  r.patterns.codePatterns["js:component"] = { template: "x", tokens_saved: 100 };
  out = await r.routeCodeGeneration("js", "component");
  eq(out.source, "template_cache", "code template cache hit");

  out = await r.routeTask("market_analysis");
  eq(out.source, "deterministic_route", "task deterministic route");

  // ── slips (recompute / local fallback) ──
  out = await r.routeMarketSearch("UNKNOWN_TICKER");
  eq(out.source, "local_mock", "market local mock fallback");

  out = await r.routeIntent("compose a brand new strategic vision plan goal");  // founder, fresh
  eq(out.source, "keystone_routing", "intent fresh keystone routing");

  out = await r.routeTask("totally_unknown_task");
  eq(out.source, "dynamic_route", "task dynamic route");

  // ── stall (needs external model) ──
  out = await r.routeCodeGeneration("rust", "novel_scope_never_seen");
  eq(out.source, "needs_llm", "code needs llm");

  // ── assert measured flywheel metrics ──
  const m = r.getFlywheelMetrics();
  eq(m.total, 8, "total routes");
  eq(m.lockup, 4, "lockup count");
  eq(m.slip, 3, "slip count");
  eq(m.stall, 1, "stall count");
  eq(m.lockupRate, 50, "lockup rate %");
  eq(m.slippageRate, 50, "slippage rate %");
  eq(m.stallRate, 12.5, "stall rate %");

  // per-surface sanity
  eq(m.bySurface.market.total, 2, "market surface total");
  eq(m.bySurface.market.lockupRate, 50, "market lockup rate");
  eq(m.bySurface.code.total, 2, "code surface total");
  eq(m.bySurface.task.total, 2, "task surface total");
  eq(m.bySurface.intent.total, 2, "intent surface total");

  // reset clears counters
  r.resetFlywheelMetrics();
  eq(r.getFlywheelMetrics().total, 0, "reset clears total");

  console.log("CONVERGENCE_ROUTER_FLYWHEEL_TEST_OK", JSON.stringify({
    lockupRate: m.lockupRate, slippageRate: m.slippageRate, stallRate: m.stallRate
  }));
})().catch((e) => { console.error("FAIL:", e.message); process.exit(1); });
