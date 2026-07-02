"use strict";

/**
 * Kalshi grounding engine — the Reason stage for the grounded position-taker.
 *
 * Σ₀ External-Reality rule applied to trading: a position is an important claim, so
 * it needs evidence. Momentum on efficient markets has no edge after fees (proven in
 * PR #1765). The only durable edge is INFORMATION the thin market hasn't priced — so
 * for a groundable event market (weather, econ, near-term events) we estimate a
 * web-grounded P(YES) and only act when it diverges from the market price enough to
 * clear the fee hurdle.
 *
 * groundMarket(market) -> { p_yes, confidence, rationale, evidence[], sources[], model, ts }
 *
 * Grounding path (funded providers only — Anthropic/OpenAI/xAI are dead here):
 *   1. webSearch() — keyless (MCP -> DuckDuckGo -> Wikipedia), for evidence snippets.
 *   2. Gemini + native googleSearch tool — live web grounding with cited sources,
 *      with the proven 429 -> free-knowledge fallback (mirrors dream-chat.js).
 *   3. callLlm("auto") fallback (Vertex -> Gemini -> Ollama) if the direct call fails.
 *
 * Results are cached (TTL) and appended to data/kalshi/grounding-cache.jsonl as an
 * audit trail. NOTHING here places an order.
 */

const fs = require("fs");
const path = require("path");
const https = require("https");

const { webSearch } = require("./web-search-client");
const { geminiTransport } = require("./gemini-transport");
const marketData = require("./market-data-client");
let _callLlm = null;
try { _callLlm = require("./self-edit-engine").callLlm; } catch { /* optional */ }

const KALSHI_DIR = path.resolve(__dirname, "..", "..", "..", "data", "kalshi");
const CACHE_FILE = path.join(KALSHI_DIR, "grounding-cache.jsonl");

const TTL_MS = Number(process.env.KALSHI_GROUND_TTL_MS) || 2 * 60 * 60 * 1000; // 2h
const GROUND_MODEL = process.env.GEMINI_GROUND_MODEL || process.env.GEMINI_MODEL || "gemini-2.5-flash";

// ── cache (in-memory, warmed + persisted to jsonl) ──────────────────────────────
const _cache = new Map(); // ticker -> { result, expires }

function _warm() {
  try {
    const lines = fs.readFileSync(CACHE_FILE, "utf8").split("\n").filter(Boolean);
    for (const l of lines) {
      try {
        const r = JSON.parse(l);
        if (!r.ticker || !r.ts) continue;
        const expires = Date.parse(r.ts) + TTL_MS;
        if (expires > Date.now()) _cache.set(r.ticker, { result: r, expires });
      } catch { /* skip */ }
    }
  } catch { /* no cache yet */ }
}
_warm();

function _persist(result) {
  try {
    fs.mkdirSync(KALSHI_DIR, { recursive: true });
    fs.appendFileSync(CACHE_FILE, JSON.stringify(result) + "\n");
  } catch { /* best-effort */ }
}

// ── helpers ─────────────────────────────────────────────────────────────────────
function _clamp01(x) { return Math.max(0, Math.min(1, x)); }

function _extractJson(text) {
  if (!text) return null;
  const m = text.match(/\{[\s\S]*\}/);
  if (m) { try { return JSON.parse(m[0]); } catch { /* fall through to lenient */ } }
  // Lenient: a grounded reply can truncate mid-rationale (finishReason MAX_TOKENS),
  // leaving invalid JSON. p_yes is the one field we must recover — pull it directly.
  const py = text.match(/"p_yes"\s*:\s*(-?\d*\.?\d+)/i);
  if (!py) return null;
  const conf = text.match(/"confidence"\s*:\s*(-?\d*\.?\d+)/i);
  const rat = text.match(/"rationale"\s*:\s*"([^"]*)/i);
  return {
    p_yes: Number(py[1]),
    confidence: conf ? Number(conf[1]) : 0.5,
    rationale: rat ? rat[1] : "",
  };
}

// ── Macro grounding (FRED / Alpha Vantage + Finnhub) ─────────────────────────
// Economy/politics-flavoured event markets (CPI prints, Fed decisions, jobs
// numbers, GDP, mortgage rates) can be grounded on the SAME authoritative series
// the market is about to resolve against — real numbers the thin market may not
// have priced. We map resolution-text keywords to macro aliases (and a Finnhub
// quote for an explicit $TICKER), fetch the latest reading + MoM/YoY via the
// unified marketData.macroLatest() (FRED if its key is set, else the free Alpha
// Vantage economic feed), and return evidence lines the forecaster sees. This is
// the External-Reality Rule applied to macro contracts: [claim, evidence, source].
// NOTE: these are PREFIX matches (leading \b, no trailing \b) on purpose — real
// Kalshi market text says "unemployment"/"unemployed"/"payrolls"/"yields", so a
// trailing \b (e.g. /\bunemploy\b/) would fail to match the very words that appear.
const MACRO_KEYWORD_SERIES = [
  [/\b(cpi|inflation|consumer price)/i, ["cpi", "core_cpi"]],
  [/\b(unemploy|jobless|jobs report|nonfarm|payroll)/i, ["unemployment", "payrolls"]],
  [/\b(fed funds|federal funds|interest rate|rate (hike|cut|decision)|fomc|fed )/i, ["fed_funds"]],
  [/\b(gdp|recession|economic growth)/i, ["real_gdp", "yield_curve"]],
  [/\bmortgage/i, ["mortgage_30y"]],
  [/\b(treasury|10[- ]?year|yield)/i, ["ten_year"]],
];

// Aliases where a relative YoY % is the meaningful headline (level indices). Rates
// and spreads (fed_funds, ten_year, yield_curve, mortgage_30y, unemployment) fall
// through to a raw year-ago-level comparison instead — see _macroEvidence.
const YOY_PCT_ALIASES = new Set(["cpi", "core_cpi", "payrolls", "real_gdp", "gdp", "retail_sales"]);

// Map a market's text to the macro aliases it references. Pure (no I/O, no keys) so
// the keyword rules are unit-testable on their own — this is where the "unemployment
// must match, not just nonfarm" contract lives.
function _macroAliases(market) {
  const text = `${market.title || ""} ${market.rules_primary || ""} ${market.ticker || ""}`;
  const aliases = new Set();
  for (const [re, series] of MACRO_KEYWORD_SERIES) {
    if (re.test(text)) series.forEach((s) => aliases.add(s));
  }
  return aliases;
}

// Returns { lines:[str], evidence:[{title,url,snippet}], sources:[url] } — empty
// when nothing macro matched or no macro provider is connected. Never throws.
async function _macroEvidence(market) {
  const text = `${market.title || ""} ${market.rules_primary || ""} ${market.ticker || ""}`;
  const aliases = _macroAliases(market);
  const out = { lines: [], evidence: [], sources: [] };
  if (aliases.size && (marketData.hasFred() || marketData.hasAlphaVantage())) {
    const results = await Promise.all([...aliases].map((a) => marketData.macroLatest(a).catch(() => null)));
    for (const r of results) {
      if (!r || !r.latest) continue;
      const parts = [`${r.latest.value} as of ${r.latest.date}`];
      // Year-over-year framing depends on series type: a relative % is meaningful
      // for level indices (CPI, payrolls, GDP) — that's literally what a "CPI YoY >
      // 3%" market resolves on — but nonsense for rates/spreads (a yield going
      // 0.10→0.31 is not "+210%"). For rates we show the raw year-ago level instead,
      // so the forecaster always gets a correct, verifiable trend.
      if (r.yearAgo) {
        if (YOY_PCT_ALIASES.has(r.alias) && r.yoyPct != null) {
          parts.push(`YoY ${r.yoyPct >= 0 ? "+" : ""}${r.yoyPct}% (was ${r.yearAgo.value} on ${r.yearAgo.date})`);
        } else {
          parts.push(`year ago ${r.yearAgo.value} (${r.yearAgo.date})`);
        }
      }
      const snippet = parts.join(", ");
      out.lines.push(`${r.label}: ${snippet} (${r.source})`);
      out.evidence.push({ title: `${r.label} — ${r.source}`, url: r.url, snippet });
      if (r.url) out.sources.push(r.url);
    }

    // Release timing (FRED only): when does this series next PRINT? An econ market
    // resolves on the print date — if the next release lands on/before the market
    // closes, fresh data will settle it (the current reading is provisional); if it
    // lands after, the current reading is effectively final. Dedupe by release so
    // CPI + core CPI (same release) add ONE timing line, not two.
    if (marketData.hasFred()) {
      const fredAliases = results.filter((r) => r && r.source === "FRED").map((r) => r.alias);
      const rels = await Promise.all(fredAliases.map((a) => marketData.fredNextRelease(a).catch(() => null)));
      const closeDate = market.close_time ? String(market.close_time).slice(0, 10) : null;
      const seenRel = new Set();
      for (const rel of rels) {
        if (!rel || seenRel.has(rel.releaseId)) continue;
        seenRel.add(rel.releaseId);
        let line = `Next ${rel.releaseName} release: ${rel.nextDate} (in ${rel.daysUntil} day${rel.daysUntil === 1 ? "" : "s"})`;
        if (closeDate) {
          line += rel.nextDate <= closeDate
            ? " — BEFORE this market closes, so fresh data will settle it (current reading is provisional)"
            : " — after this market closes, so the current reading is effectively final";
        }
        out.lines.push(line);
        out.evidence.push({
          title: `${rel.releaseName} release schedule — FRED`,
          url: `https://fred.stlouisfed.org/release/dates?rid=${rel.releaseId}`,
          snippet: `next release ${rel.nextDate} (in ${rel.daysUntil}d)`,
        });
      }
    }
  }
  // Explicit equity ticker in the market (e.g. "$AAPL above 250")? Add a live quote.
  const tm = text.match(/\$([A-Z]{1,5})\b/);
  if (tm && marketData.hasFinnhub()) {
    const q = await marketData.finnhubQuote(tm[1]).catch(() => null);
    if (q && q.price) {
      const snippet = `${q.symbol} $${q.price} (${q.changePct >= 0 ? "+" : ""}${q.changePct}% today)`;
      out.lines.push(`Live quote: ${snippet}`);
      out.evidence.push({ title: `${q.symbol} live quote — Finnhub`, url: `https://finnhub.io/`, snippet });
    }
  }
  return out;
}

function _researchQuery(market) {
  const title = market.title || market.ticker || "";
  // The resolution rule is the precise YES condition — the thing to research.
  const rule = (market.rules_primary || "").slice(0, 220);
  const close = market.close_time ? ` (resolves ${String(market.close_time).slice(0, 10)})` : "";
  return `${title}${close} — ${rule}`.trim();
}

// Gemini call with the native googleSearch tool (live web grounding), routed through
// geminiTransport — Vertex (funded GCP, no rate limit, reliable grounding) when
// VERTEX_PROJECT is set, else the AI-Studio free key with the proven 429 ->
// free-knowledge fallback (the free googleSearch tool is a paid feature → 429s).
// Returns { text, sources, grounded, model }.
async function _geminiGrounded(prompt) {
  let wire;
  try { wire = await geminiTransport({ model: GROUND_MODEL, method: "generateContent", streaming: false }); }
  catch { return null; } // no Vertex token AND no AI-Studio key
  const onVertex = !!wire.vertex;

  function call(useSearch) {
    const payload = JSON.stringify({
      contents: [{ role: "user", parts: [{ text: prompt }] }],
      ...(useSearch ? { tools: [{ googleSearch: {} }] } : {}),
      // Grounding spends output tokens on internal search reasoning, so the JSON can
      // truncate at a small cap (finishReason MAX_TOKENS). Give it ample room.
      generationConfig: { temperature: 0.2, maxOutputTokens: 2048 },
    });
    return new Promise((resolve, reject) => {
      const req = https.request({
        hostname: wire.hostname, path: wire.path, method: "POST",
        headers: { ...wire.headers, "Content-Length": Buffer.byteLength(payload) },
      }, (res) => { let d = ""; res.on("data", c => d += c); res.on("end", () => resolve({ status: res.statusCode, body: d })); res.on("error", reject); });
      req.on("error", reject);
      req.setTimeout(28000, () => { req.destroy(); reject(new Error("timeout")); });
      req.write(payload); req.end();
    });
  }

  try {
    let searched = true;
    let { status, body } = await call(true);
    // Only the AI-Studio free key 429s on the paid search tool; retry knowledge-only.
    if (status === 429 && !onVertex) { searched = false; ({ status, body } = await call(false)); }
    if (status !== 200) return null;
    const j = JSON.parse(body);
    const text = (j.candidates?.[0]?.content?.parts || []).map(p => p.text).filter(Boolean).join("") || "";
    if (!text.trim()) return null;
    const meta = j.candidates?.[0]?.groundingMetadata;
    const sources = (meta?.groundingChunks || []).map(c => c.web?.uri).filter(Boolean);
    return {
      text, sources,
      grounded: searched && sources.length > 0,
      model: `${onVertex ? "vertex" : "gemini"}:${GROUND_MODEL}${searched ? "+search" : ""}`,
    };
  } catch { return null; }
}

function _systemPrompt() {
  return [
    "You are a calibrated forecaster pricing a binary prediction market.",
    "Estimate the TRUE probability the market resolves YES, using the resolution rule and any",
    "current real-world evidence (forecasts, data, reporting). Be well-calibrated and honest:",
    "if you lack information, say so with a probability near the market's implied price.",
    'Return ONLY JSON: {"p_yes": 0.0-1.0, "confidence": 0.0-1.0, "rationale": "one sentence"}.',
  ].join(" ");
}

// ── main: ground one market ─────────────────────────────────────────────────────
async function groundMarket(market, { force = false } = {}) {
  const ticker = market.ticker;
  if (!ticker) return { error: "no ticker" };

  const cached = _cache.get(ticker);
  if (!force && cached && cached.expires > Date.now()) {
    return { ...cached.result, cached: true };
  }

  const query = _researchQuery(market);
  const marketPct = market.yesPct != null ? market.yesPct
    : (market.yes_ask_dollars != null ? Math.round(Number(market.yes_ask_dollars) * 100) : null);

  // 1) keyless web evidence (snippets for the UI + context for the LLM fallback)
  let evidence = [];
  try {
    const ws = await webSearch(query, 5).catch(() => null);
    if (ws && ws.success) evidence = (ws.results || []).slice(0, 5).map(r => ({ title: r.title, url: r.url, snippet: r.snippet }));
  } catch { /* non-fatal */ }

  // 1b) authoritative macro data (FRED) + live quotes (Finnhub) for econ markets.
  // Prepended to evidence so the real numbers lead, and its sources are merged in.
  let macro = { lines: [], evidence: [], sources: [] };
  try { macro = await _macroEvidence(market); } catch { /* non-fatal */ }
  if (macro.evidence.length) evidence = [...macro.evidence, ...evidence];

  const userPrompt =
    `Market: ${market.title || ticker}\n` +
    `Resolution rule (YES if true): ${(market.rules_primary || "n/a").slice(0, 400)}\n` +
    (market.close_time ? `Closes: ${market.close_time}\n` : "") +
    (marketPct != null ? `Market currently prices YES at ${marketPct}%.\n` : "") +
    (macro.lines.length ? `\nLive macro data (FRED/Finnhub, authoritative):\n${macro.lines.map((l) => `- ${l}`).join("\n")}\n` : "") +
    (evidence.length ? `\nWeb evidence:\n${evidence.map((e, i) => `[${i + 1}] ${e.title}: ${e.snippet}`).join("\n").slice(0, 1500)}\n` : "") +
    `\nEstimate the true probability of YES.`;

  // 2) Gemini with live googleSearch grounding (best for current data)
  let p_yes = null, confidence = 0.5, rationale = "", sources = [], model = "none";
  // web_grounded = the estimate is backed by a LIVE web search (real sources), not
  // model-memory/climatology. The External-Reality rule: only a web-grounded estimate
  // may assert an edge over the market price; a knowledge-only guess defers to it.
  let webGrounded = false;
  const g = await _geminiGrounded(`${_systemPrompt()}\n\n${userPrompt}`);
  if (g) {
    const j = _extractJson(g.text);
    if (j && j.p_yes != null && isFinite(Number(j.p_yes))) {
      p_yes = _clamp01(Number(j.p_yes));
      confidence = _clamp01(Number(j.confidence != null ? j.confidence : 0.5));
      rationale = String(j.rationale || g.text.slice(0, 200)).slice(0, 280);
      sources = g.sources || [];
      model = g.model;
      // live only if the googleSearch tool actually ran AND returned sources
      webGrounded = !!g.grounded && sources.length > 0;
    }
  }

  // 3) fallback: auto-cascade LLM (Vertex -> Gemini -> Ollama) on the evidence block.
  // This has NO live web access — it is knowledge/climatology only, so web_grounded stays false.
  if (p_yes == null && _callLlm) {
    try {
      const out = await _callLlm(_systemPrompt(), userPrompt, "auto", 400);
      const j = _extractJson(out);
      if (j && j.p_yes != null && isFinite(Number(j.p_yes))) {
        p_yes = _clamp01(Number(j.p_yes));
        confidence = _clamp01(Number(j.confidence != null ? j.confidence : 0.5));
        rationale = String(j.rationale || "").slice(0, 280);
        model = "callLlm:auto(knowledge-only)";
      }
    } catch { /* fall through */ }
  }
  // FRED-backed macro data is authoritative live external reality — as legitimate a
  // grounding as a googleSearch source (arguably stronger). An econ estimate fed the
  // actual current CPI/rate/jobs number counts as web-grounded and may assert an edge.
  const macroGrounded = macro.lines.length > 0;
  if (macroGrounded) webGrounded = true;

  // A non-web-grounded estimate is weak evidence by construction — cap its confidence
  // so it can't masquerade as a high-conviction edge.
  if (!webGrounded) confidence = Math.min(confidence, 0.4);

  if (p_yes == null) {
    const result = {
      ticker, p_yes: null, confidence: 0, rationale: "grounding unavailable (no provider returned a probability)",
      evidence, sources, model: "none", query, ts: new Date().toISOString(), grounded: false,
    };
    return result; // not cached — retry next cycle
  }

  // merge web-evidence + FRED/Finnhub macro urls into sources for the audit trail
  const allSources = Array.from(new Set([...(sources || []), ...macro.sources, ...evidence.map(e => e.url).filter(Boolean)]));
  const result = {
    ticker, p_yes: Math.round(p_yes * 1000) / 1000,
    confidence: Math.round(confidence * 100) / 100,
    rationale, evidence, sources: allSources, model, query,
    ts: new Date().toISOString(), grounded: true, web_grounded: webGrounded,
    macro_grounded: macroGrounded,
  };
  _cache.set(ticker, { result, expires: Date.now() + TTL_MS });
  _persist(result);
  return result;
}

// Cache-only read — returns the cached grounding for a ticker or null, WITHOUT
// triggering a (slow) grounding call. The deck uses this to render instantly and
// kick off background grounding for the misses.
function peek(ticker) {
  const c = _cache.get(ticker);
  return (c && c.expires > Date.now()) ? c.result : null;
}

// ground many with a small concurrency cap (bounded LLM/search usage)
async function groundMany(markets, { concurrency = 4, force = false } = {}) {
  const out = [];
  let i = 0;
  async function worker() {
    while (i < markets.length) {
      const m = markets[i++];
      out.push(await groundMarket(m, { force }));
    }
  }
  await Promise.all(Array.from({ length: Math.min(concurrency, markets.length) }, worker));
  return out;
}

module.exports = { groundMarket, groundMany, peek, CACHE_FILE, TTL_MS };
// Exported for tests: macro/quote evidence builder + the pure keyword matcher.
module.exports._macroEvidence = _macroEvidence;
module.exports._macroAliases = _macroAliases;
