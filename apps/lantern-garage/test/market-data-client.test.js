// Market-data client (lib/market-data-client.js): the keyless-degrading gateway
// to Finnhub + FRED that feeds the Explore finance rail (news-collector.js) and
// the Kalshi Σ₀ council's macro grounding (kalshi-grounding.js). This suite is
// network-free: it asserts graceful degradation when keys are absent (a missing
// key is never an error, just no data) and that the FRED alias map is intact.
//
// Run: node apps/lantern-garage/test/market-data-client.test.js

const assert = require("assert");

// Force a key-less environment so nothing hits the network.
delete process.env.FINNHUB_API_KEY;
delete process.env.FRED_API_KEY;
delete process.env.ALPHA_VANTAGE_API_KEY;

const md = require("../lib/market-data-client");
const grounding = require("../lib/kalshi-grounding");

let failures = 0;
function check(name, fn) {
  return Promise.resolve()
    .then(fn)
    .then(() => console.log("  ok  -", name))
    .catch((e) => { failures++; console.error("  FAIL-", name, "\n      ", e.message); });
}

(async () => {
  // ── presence flags reflect the empty env ──
  await check("no keys → all presence flags false", () => {
    assert.strictEqual(md.hasFinnhub(), false);
    assert.strictEqual(md.hasFred(), false);
    assert.strictEqual(md.hasAlphaVantage(), false);
  });

  // ── every fetch degrades to empty/null, never throws, never hits the network ──
  await check("finnhubMarketNews → [] with no key", async () => {
    assert.deepStrictEqual(await md.finnhubMarketNews("general"), []);
  });
  await check("finnhubCompanyNews → [] with no key", async () => {
    assert.deepStrictEqual(await md.finnhubCompanyNews("AAPL"), []);
  });
  await check("finnhubQuote → null with no key", async () => {
    assert.strictEqual(await md.finnhubQuote("AAPL"), null);
  });
  await check("finnhubRecommendation → null with no key", async () => {
    assert.strictEqual(await md.finnhubRecommendation("AAPL"), null);
  });
  await check("fredObservations → [] with no key", async () => {
    assert.deepStrictEqual(await md.fredObservations("cpi"), []);
  });
  await check("fredLatest → null with no key", async () => {
    assert.strictEqual(await md.fredLatest("cpi"), null);
  });

  // ── bad inputs are guarded ──
  await check("finnhubQuote(undefined) → null (no throw)", async () => {
    assert.strictEqual(await md.finnhubQuote(undefined), null);
  });
  await check("finnhubMarketNews(bad category) → [] (no throw)", async () => {
    assert.deepStrictEqual(await md.finnhubMarketNews("not-a-category"), []);
  });

  // ── the curated FRED alias map covers the macro series the council maps to ──
  await check("FRED_SERIES exposes the macro aliases the council uses", () => {
    for (const alias of ["cpi", "core_cpi", "unemployment", "fed_funds_daily", "payrolls", "real_gdp", "yield_curve", "mortgage_30y", "ten_year"]) {
      assert.ok(md.FRED_SERIES[alias], "missing alias: " + alias);
    }
  });

  // ── Alpha Vantage layer degrades identically with no key ──
  await check("alphaVantageEconomic → null with no key", async () => {
    assert.strictEqual(await md.alphaVantageEconomic("cpi"), null);
  });
  await check("alphaVantageNewsSentiment → [] with no key", async () => {
    assert.deepStrictEqual(await md.alphaVantageNewsSentiment({ topics: "financial_markets" }), []);
  });
  await check("macroLatest → null with no provider connected", async () => {
    assert.strictEqual(await md.macroLatest("cpi"), null);
  });
  await check("alphaVantageEconomic(unknown alias) → null (no throw)", async () => {
    assert.strictEqual(await md.alphaVantageEconomic("not-an-indicator"), null);
  });

  // ── AV_ECONOMIC covers the free FRED-sourced indicators the macro grounder maps to ──
  await check("AV_ECONOMIC exposes the free economic indicators", () => {
    for (const alias of ["cpi", "unemployment", "fed_funds", "payrolls", "real_gdp", "ten_year", "inflation"]) {
      assert.ok(md.AV_ECONOMIC[alias], "missing AV indicator: " + alias);
    }
    // Aliases AV lacks stay FRED-only (must NOT be in AV_ECONOMIC).
    for (const alias of ["core_cpi", "yield_curve", "mortgage_30y"]) {
      assert.ok(!md.AV_ECONOMIC[alias], "unexpected AV indicator: " + alias);
    }
  });

  // ── kalshi-grounding macro evidence: keyword detection + graceful degradation ──
  await check("macro evidence: econ market detected but empty without FRED key", async () => {
    const r = await grounding._macroEvidence({
      ticker: "CPI-JUN", title: "Will CPI YoY exceed 3% in June?",
      rules_primary: "Resolves YES if CPI year-over-year inflation is above 3.0%",
    });
    assert.ok(Array.isArray(r.lines) && Array.isArray(r.evidence) && Array.isArray(r.sources));
    assert.strictEqual(r.lines.length, 0); // FRED key unset → no macro lines, no throw
  });
  await check("macro evidence: non-econ market yields nothing", async () => {
    const r = await grounding._macroEvidence({
      ticker: "NFL", title: "Will the Chiefs win Sunday?", rules_primary: "YES if Chiefs win",
    });
    assert.strictEqual(r.lines.length, 0);
    assert.strictEqual(r.evidence.length, 0);
  });

  // Keyword matcher (pure, no keys) — real Kalshi phrasings use word VARIANTS
  // ("unemployment", "payrolls", "yields") that a trailing-\b regex would miss.
  // Regression guard for the dev-preview bug where KXU3MAX ("...unemployment...")
  // matched nothing because /\bunemploy\b/ can't match "unemployment".
  const aliasesOf = (m) => [...grounding._macroAliases(m)].sort();
  await check("matcher: real KXU3MAX unemployment market → unemployment+payrolls", () => {
    const a = aliasesOf({ ticker: "KXU3MAX-30-5", title: "How high will unemployment get before 2030?", rules_primary: "If the U-3 unemployment rate is above 5%, resolves Yes." });
    assert.deepStrictEqual(a, ["payrolls", "unemployment"]);
  });
  await check("matcher: 'payrolls' / 'jobless claims' variants match", () => {
    assert.ok(grounding._macroAliases({ title: "nonfarm payrolls beat?" }).has("payrolls"));
    assert.ok(grounding._macroAliases({ title: "weekly jobless claims" }).has("unemployment"));
  });
  await check("matcher: real GDP market → real_gdp+yield_curve", () => {
    assert.deepStrictEqual(aliasesOf({ ticker: "KXGDPYEAR-30", title: "US real GDP growth in 2030?" }), ["real_gdp", "yield_curve"]);
  });
  await check("matcher: CPI / inflation / Fed / mortgage / treasury yields all match", () => {
    assert.ok(grounding._macroAliases({ title: "core CPI print" }).has("cpi"));
    assert.ok(grounding._macroAliases({ title: "inflation above 3%" }).has("cpi"));
    assert.ok(grounding._macroAliases({ title: "Fed funds rate cut in July" }).has("fed_funds"));
    assert.ok(grounding._macroAliases({ title: "30-year mortgage rates" }).has("mortgage_30y"));
    assert.ok(grounding._macroAliases({ title: "10-year treasury yields rise" }).has("ten_year"));
  });
  await check("matcher: non-econ market → no aliases", () => {
    assert.strictEqual(grounding._macroAliases({ title: "Will the Chiefs win Sunday?" }).size, 0);
  });

  console.log(failures ? `\n${failures} test(s) failed` : "\nall passed");
  process.exit(failures ? 1 : 0);
})();
