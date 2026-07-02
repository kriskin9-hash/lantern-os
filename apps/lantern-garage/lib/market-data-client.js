/**
 * Market-data client — one keyless-degrading gateway to the free market-data
 * APIs whose keys live in the Financial Keys panel (routes/financial-keys.js):
 *
 *   - Finnhub  (FINNHUB_API_KEY)        — market/company news, quote, analyst recs
 *   - FRED     (FRED_API_KEY)           — Federal Reserve macro series (free)
 *   - Alpha Vantage (ALPHA_VANTAGE_API_KEY) — quote fallback
 *
 * ONE place reads these keys and speaks to all three so the two consumers
 * (news-collector.js for the Explore feed, kalshi-grounding.js for the Σ₀
 * council) don't each grow their own HTTP + auth code. Every method degrades to
 * null / [] when its key is unset — a missing key is never an error, just no
 * data (the callers already treat "no data" as "skip this source").
 *
 * Only FREE Finnhub endpoints are used: /news, /company-news, /quote,
 * /stock/recommendation. Premium endpoints (news-sentiment, candles, economic
 * calendar, …) are intentionally NOT called — FRED covers macro for free.
 */

"use strict";

const https = require("https");

const FINNHUB_BASE = "finnhub.io";
const FRED_BASE = "api.stlouisfed.org";
const AV_BASE = "www.alphavantage.co";

const REQUEST_TIMEOUT = 9000;

// ── key presence (read at call time — the financial-keys route syncs Windows
// User env → process.env, so a key saved in the UI is picked up without a restart
// of THIS module) ───────────────────────────────────────────────────────────────
function finnhubKey() { return (process.env.FINNHUB_API_KEY || "").trim(); }
function fredKey() { return (process.env.FRED_API_KEY || "").trim(); }
function alphaVantageKey() { return (process.env.ALPHA_VANTAGE_API_KEY || "").trim(); }

function hasFinnhub() { return finnhubKey().length > 0; }
function hasFred() { return fredKey().length > 0; }
function hasAlphaVantage() { return alphaVantageKey().length > 0; }

// ── HTTP + short-TTL cache ────────────────────────────────────────────────────
function httpsGetJson(hostname, pathAndQuery) {
  return new Promise((resolve, reject) => {
    const req = https.get(
      { hostname, path: pathAndQuery, headers: { "User-Agent": "lantern-os-market-data", Accept: "application/json" } },
      (res) => {
        if (res.statusCode !== 200) {
          res.resume();
          return reject(new Error(`HTTP ${res.statusCode}`));
        }
        let data = "";
        res.on("data", (c) => (data += c));
        res.on("end", () => {
          try { resolve(JSON.parse(data)); }
          catch { reject(new Error("bad JSON")); }
        });
      }
    );
    req.on("error", reject);
    req.setTimeout(REQUEST_TIMEOUT, () => req.destroy(new Error("timeout")));
  });
}

const _cache = new Map();
function cached(key, ttlMs, produce) {
  const hit = _cache.get(key);
  if (hit && Date.now() - hit.at < ttlMs) return Promise.resolve(hit.val);
  return Promise.resolve()
    .then(produce)
    .then((val) => { _cache.set(key, { at: Date.now(), val }); return val; });
}

function ymd(d) {
  return new Date(d).toISOString().slice(0, 10);
}

// ── Finnhub ───────────────────────────────────────────────────────────────────

/**
 * Free market news for a broad category. category ∈ general|forex|crypto|merger.
 * Returns [] when no key or on any error. Shape: [{headline,url,source,summary,
 * image,published(ISO),symbols[],category,id}] — normalised to the shape
 * trading-news.recordNewsItem() expects.
 */
async function finnhubMarketNews(category = "general") {
  if (!hasFinnhub()) return [];
  const cat = ["general", "forex", "crypto", "merger"].includes(category) ? category : "general";
  try {
    const rows = await cached(`fh:news:${cat}`, 5 * 60 * 1000, () =>
      httpsGetJson(FINNHUB_BASE, `/api/v1/news?category=${cat}&token=${encodeURIComponent(finnhubKey())}`));
    return Array.isArray(rows) ? rows.map((n) => _normalizeFinnhubNews(n)).filter(Boolean) : [];
  } catch { return []; }
}

/**
 * Free company news for one symbol over a date window (default: last 7 days).
 * Same normalised shape as finnhubMarketNews, with symbols:[symbol].
 */
async function finnhubCompanyNews(symbol, { fromDate = null, toDate = null } = {}) {
  if (!hasFinnhub() || !symbol) return [];
  const sym = String(symbol).toUpperCase();
  const to = toDate || ymd(Date.now());
  const from = fromDate || ymd(Date.now() - 7 * 86400000);
  try {
    const rows = await cached(`fh:cnews:${sym}:${from}:${to}`, 10 * 60 * 1000, () =>
      httpsGetJson(FINNHUB_BASE,
        `/api/v1/company-news?symbol=${encodeURIComponent(sym)}&from=${from}&to=${to}&token=${encodeURIComponent(finnhubKey())}`));
    return Array.isArray(rows) ? rows.map((n) => _normalizeFinnhubNews(n, sym)).filter(Boolean) : [];
  } catch { return []; }
}

function _normalizeFinnhubNews(n, forcedSymbol = null) {
  if (!n || !n.headline || !n.url) return null;
  // `related` is a comma-separated ticker string on Finnhub; forcedSymbol wins for
  // company-news. Uppercase, drop empties.
  const related = forcedSymbol
    ? [forcedSymbol]
    : String(n.related || "").split(",").map((s) => s.trim().toUpperCase()).filter(Boolean).slice(0, 8);
  return {
    id: n.id != null ? `finnhub_${n.id}` : n.url,
    headline: String(n.headline).trim(),
    url: n.url,
    source: n.source || "Finnhub",
    summary: n.summary || "",
    image: /^https:\/\//i.test(n.image || "") ? n.image : "",
    published: n.datetime ? new Date(n.datetime * 1000).toISOString() : new Date().toISOString(),
    symbols: related,
    category: n.category || "",
  };
}

/**
 * Free real-time US-stock quote. Returns {price,changePct,high,low,open,prevClose}
 * or null. (Finnhub /quote → c,d,dp,h,l,o,pc.)
 */
async function finnhubQuote(symbol) {
  if (!hasFinnhub() || !symbol) return null;
  const sym = String(symbol).toUpperCase();
  try {
    const q = await cached(`fh:quote:${sym}`, 30 * 1000, () =>
      httpsGetJson(FINNHUB_BASE, `/api/v1/quote?symbol=${encodeURIComponent(sym)}&token=${encodeURIComponent(finnhubKey())}`));
    if (!q || q.c == null) return null;
    return { symbol: sym, price: Number(q.c), changePct: Number(q.dp), high: Number(q.h), low: Number(q.l), open: Number(q.o), prevClose: Number(q.pc) };
  } catch { return null; }
}

/**
 * Free analyst recommendation trend (latest period). Returns
 * {strongBuy,buy,hold,sell,strongSell,period,net(-1..1)} or null. `net` is a
 * single directional score: (buys − sells) / total, weighting strong 2×.
 */
async function finnhubRecommendation(symbol) {
  if (!hasFinnhub() || !symbol) return null;
  const sym = String(symbol).toUpperCase();
  try {
    const rows = await cached(`fh:rec:${sym}`, 6 * 60 * 60 * 1000, () =>
      httpsGetJson(FINNHUB_BASE, `/api/v1/stock/recommendation?symbol=${encodeURIComponent(sym)}&token=${encodeURIComponent(finnhubKey())}`));
    const r = Array.isArray(rows) && rows.length ? rows[0] : null; // newest first
    if (!r) return null;
    const sb = +r.strongBuy || 0, b = +r.buy || 0, h = +r.hold || 0, s = +r.sell || 0, ss = +r.strongSell || 0;
    const total = sb + b + h + s + ss;
    const net = total ? (2 * sb + b - s - 2 * ss) / (2 * total) : 0; // -1..1
    return { symbol: sym, strongBuy: sb, buy: b, hold: h, sell: s, strongSell: ss, period: r.period || "", net: Math.round(net * 1000) / 1000 };
  } catch { return null; }
}

// ── FRED (Federal Reserve macro series — free, no practical rate limit) ─────────

// Curated series most relevant to economy/politics-flavoured event markets.
// Keyed by short alias so callers name intent, not FRED's opaque IDs.
const FRED_SERIES = {
  cpi: "CPIAUCSL",          // CPI (all urban consumers, SA)
  core_cpi: "CPILFESL",     // Core CPI (ex food & energy)
  unemployment: "UNRATE",   // Unemployment rate
  fed_funds: "FEDFUNDS",    // Federal funds effective rate (monthly)
  fed_funds_daily: "DFF",   // Federal funds effective rate (daily)
  payrolls: "PAYEMS",       // Total nonfarm payrolls
  gdp: "GDP",               // Gross domestic product
  ten_year: "DGS10",        // 10-year Treasury yield
  yield_curve: "T10Y2Y",    // 10y−2y spread (recession signal)
  mortgage_30y: "MORTGAGE30US",
  real_gdp: "GDPC1",
};

/**
 * Latest N observations for a FRED series (by alias or raw id), newest first.
 * Returns [{date, value(Number)}] or [] when no key / error / no data.
 */
async function fredObservations(seriesOrAlias, { limit = 13 } = {}) {
  if (!hasFred() || !seriesOrAlias) return [];
  const seriesId = FRED_SERIES[seriesOrAlias] || String(seriesOrAlias);
  try {
    const j = await cached(`fred:${seriesId}:${limit}`, 60 * 60 * 1000, () =>
      httpsGetJson(FRED_BASE,
        `/fred/series/observations?series_id=${encodeURIComponent(seriesId)}` +
        `&api_key=${encodeURIComponent(fredKey())}&file_type=json&sort_order=desc&limit=${Math.max(1, Math.min(200, limit))}`));
    const obs = (j && Array.isArray(j.observations)) ? j.observations : [];
    return obs
      .map((o) => ({ date: o.date, value: o.value === "." ? null : Number(o.value) }))
      .filter((o) => o.value != null && Number.isFinite(o.value));
  } catch { return []; }
}

// Find the observation closest to ~1 year before `latest`, accepted only within a
// tolerance (so a gap doesn't match a nonsense point). Works for ANY frequency —
// monthly/quarterly/daily/weekly — because it matches by DATE, not list position.
// `obs` is newest-first.
function _yearAgoObs(obs, latest, toleranceDays = 45) {
  const target = Date.parse(latest.date) - 365 * 86400000;
  let best = null, bestDiff = Infinity;
  for (const o of obs) {
    const diff = Math.abs(Date.parse(o.date) - target);
    if (diff < bestDiff) { bestDiff = diff; best = o; }
  }
  return best && bestDiff <= toleranceDays * 86400000 ? best : null;
}

/**
 * Latest reading of a series plus period-over-period and year-over-year change, AND
 * the raw year-ago reading (so the number is independently verifiable regardless of
 * series frequency). Returns {seriesId, alias, latest, prev, yearAgo, momPct, yoyPct}
 * or null. Fetches a wide window so YoY can be found by date even for daily series.
 */
async function fredLatest(seriesOrAlias) {
  const obs = await fredObservations(seriesOrAlias, { limit: 400 });
  if (!obs.length) return null;
  const latest = obs[0];
  const prev = obs[1] || null;
  const yearAgo = _yearAgoObs(obs, latest);
  const pct = (a, b) => (b && b.value ? Math.round(((a.value - b.value) / b.value) * 1000) / 10 : null);
  return {
    seriesId: FRED_SERIES[seriesOrAlias] || String(seriesOrAlias),
    alias: FRED_SERIES[seriesOrAlias] ? seriesOrAlias : null,
    latest,
    prev,
    yearAgo,
    momPct: prev ? pct(latest, prev) : null,
    yoyPct: yearAgo ? pct(latest, yearAgo) : null,
  };
}

/**
 * The FRED release a series belongs to: {id, name} or null. Cached 7d — the
 * series→release mapping is effectively static.
 */
async function fredSeriesRelease(seriesOrAlias) {
  if (!hasFred() || !seriesOrAlias) return null;
  const seriesId = FRED_SERIES[seriesOrAlias] || String(seriesOrAlias);
  try {
    const j = await cached(`fred:rel:${seriesId}`, 7 * 24 * 60 * 60 * 1000, () =>
      httpsGetJson(FRED_BASE,
        `/fred/series/release?series_id=${encodeURIComponent(seriesId)}&api_key=${encodeURIComponent(fredKey())}&file_type=json`));
    const r = j && Array.isArray(j.releases) && j.releases[0];
    return r && r.id ? { id: r.id, name: r.name || `release ${r.id}` } : null;
  } catch { return null; }
}

/**
 * Next scheduled release date for a series' release. Returns {releaseId, releaseName,
 * nextDate(YYYY-MM-DD), daysUntil} or null. This is the timing signal an econ event
 * market resolves on — a "CPI in June" contract settles on the print date. Cached 6h.
 */
async function fredNextRelease(seriesOrAlias) {
  const rel = await fredSeriesRelease(seriesOrAlias);
  if (!rel) return null;
  const today = ymd(Date.now());
  try {
    const j = await cached(`fred:reldates:${rel.id}`, 6 * 60 * 60 * 1000, () =>
      httpsGetJson(FRED_BASE,
        `/fred/release/dates?release_id=${rel.id}&api_key=${encodeURIComponent(fredKey())}&file_type=json` +
        `&include_release_dates_with_no_data=true&sort_order=asc&realtime_start=${today}&limit=6`));
    const dates = (j && Array.isArray(j.release_dates) ? j.release_dates : []).map((d) => d.date).filter(Boolean);
    const next = dates.find((d) => d >= today);
    if (!next) return null;
    const daysUntil = Math.max(0, Math.round((Date.parse(next) - Date.parse(today)) / 86400000));
    return { releaseId: rel.id, releaseName: rel.name, nextDate: next, daysUntil };
  } catch { return null; }
}

// Human labels for each macro alias — shared by the FRED and Alpha Vantage paths
// so callers render one consistent name regardless of which source answered.
const MACRO_LABEL = {
  cpi: "US CPI", core_cpi: "US Core CPI", unemployment: "US Unemployment rate",
  fed_funds: "Fed funds rate", fed_funds_daily: "Fed funds rate",
  payrolls: "US Nonfarm payrolls", gdp: "US GDP", real_gdp: "US Real GDP",
  ten_year: "10y Treasury yield", yield_curve: "10y−2y Treasury spread",
  mortgage_30y: "30y mortgage rate", inflation: "US Inflation rate",
  retail_sales: "US Retail sales",
};

// ── Alpha Vantage (free tier: 25 requests/DAY, ~5/min — treat the quota as scarce) ──
//
// Two free surfaces we use: FRED-sourced Economic Indicators (macro grounding) and
// NEWS_SENTIMENT (sentiment-scored headlines). The 25/day cap is a hard design
// constraint: everything here is heavily cached and gated by a per-UTC-day call
// budget so AV can never blow past its quota or starve the more valuable macro
// path. On rate-limit AV returns {Note}/{Information} (HTTP 200) rather than an
// error — avGet detects that and degrades to empty, same as a missing key.

// alias → Alpha Vantage economic function. Only the indicators AV exposes for free;
// aliases AV lacks (core_cpi, yield_curve, mortgage_30y) simply fall through to null
// so FRED remains their only source.
const AV_ECONOMIC = {
  cpi:             { fn: "CPI", qs: "&interval=monthly", yoyLag: 12 },
  unemployment:    { fn: "UNEMPLOYMENT", qs: "", yoyLag: 12 },
  fed_funds:       { fn: "FEDERAL_FUNDS_RATE", qs: "&interval=monthly", yoyLag: 12 },
  fed_funds_daily: { fn: "FEDERAL_FUNDS_RATE", qs: "&interval=monthly", yoyLag: 12 },
  payrolls:        { fn: "NONFARM_PAYROLL", qs: "", yoyLag: 12 },
  real_gdp:        { fn: "REAL_GDP", qs: "&interval=quarterly", yoyLag: 4 },
  gdp:             { fn: "REAL_GDP", qs: "&interval=quarterly", yoyLag: 4 },
  ten_year:        { fn: "TREASURY_YIELD", qs: "&interval=monthly&maturity=10year", yoyLag: 12 },
  inflation:       { fn: "INFLATION", qs: "", yoyLag: 1 },
  retail_sales:    { fn: "RETAIL_SALES", qs: "", yoyLag: 12 },
};

// Per-UTC-day AV call budget — hard-stop below the 25/day free cap so we always
// leave headroom and never hard-fail. Reset lazily when the UTC date changes.
const AV_DAILY_BUDGET = 20;
let _avBudget = { day: "", used: 0 };
function _avDay() { return new Date().toISOString().slice(0, 10); }
function _avBudgetOk() {
  const day = _avDay();
  if (_avBudget.day !== day) _avBudget = { day, used: 0 };
  return _avBudget.used < AV_DAILY_BUDGET;
}
function _avBudgetSpend() { _avBudget.used += 1; }

// GET one Alpha Vantage query. Returns the parsed JSON, or null when: no key, budget
// exhausted, network error, or AV answered with a rate-limit {Note}/{Information}.
async function avGet(query) {
  if (!hasAlphaVantage() || !_avBudgetOk()) return null;
  _avBudgetSpend();
  try {
    const j = await httpsGetJson(AV_BASE, `/query?${query}&apikey=${encodeURIComponent(alphaVantageKey())}`);
    if (!j || j.Note || j.Information || j["Error Message"]) return null; // rate-limited / invalid
    return j;
  } catch { return null; }
}

/**
 * Latest reading of a free Alpha Vantage economic indicator (by macro alias) plus
 * MoM/YoY change. Returns {alias, label, latest:{date,value}, prev, momPct, yoyPct,
 * source:"AlphaVantage"} or null. Cached 12h — these series update monthly at most,
 * so this costs ≤2 AV calls/day/indicator even under heavy grounding.
 */
async function alphaVantageEconomic(alias) {
  const cfg = AV_ECONOMIC[alias];
  if (!cfg || !hasAlphaVantage()) return null;
  const j = await cached(`av:econ:${alias}`, 12 * 60 * 60 * 1000, () =>
    avGet(`function=${cfg.fn}${cfg.qs}`));
  const data = j && Array.isArray(j.data) ? j.data : [];
  const obs = data
    .map((o) => ({ date: o.date, value: o.value === "." ? null : Number(o.value) }))
    .filter((o) => o.value != null && Number.isFinite(o.value)); // newest-first per AV
  if (!obs.length) return null;
  const latest = obs[0], prev = obs[1] || null;
  // AV series are single-frequency per function, so the positional lag is correct;
  // fall back to date-matching if the series is shorter than the lag expects.
  const yearAgo = obs[cfg.yoyLag] || _yearAgoObs(obs, latest);
  const pct = (a, b) => (b && b.value ? Math.round(((a.value - b.value) / b.value) * 1000) / 10 : null);
  return {
    alias, label: MACRO_LABEL[alias] || (j && j.name) || alias,
    latest, prev, yearAgo,
    momPct: prev ? pct(latest, prev) : null,
    yoyPct: yearAgo ? pct(latest, yearAgo) : null,
    source: "AlphaVantage",
  };
}

/**
 * Free NEWS_SENTIMENT feed — sentiment-scored market news (what Finnhub charges for).
 * opts: { tickers?, topics?='financial_markets', limit?=50 }. Returns normalised
 * items [{id,headline,url,source,summary,image,published(ISO),symbols[],
 * sentimentScore(-1..1),sentimentLabel}] or []. Cached 30min. Deliberately NOT wired
 * into the fast news-collector loop — the 25/day cap makes high-frequency AV news
 * impractical; callers must throttle (see news-collector _collectFromAlphaVantage).
 */
async function alphaVantageNewsSentiment({ tickers = "", topics = "financial_markets", limit = 50 } = {}) {
  if (!hasAlphaVantage()) return [];
  const key = `av:news:${tickers}:${topics}:${limit}`;
  const q = "function=NEWS_SENTIMENT" +
    (tickers ? `&tickers=${encodeURIComponent(tickers)}` : "") +
    (topics ? `&topics=${encodeURIComponent(topics)}` : "") +
    `&limit=${Math.max(1, Math.min(1000, limit))}&sort=LATEST`;
  const j = await cached(key, 30 * 60 * 1000, () => avGet(q));
  const feed = j && Array.isArray(j.feed) ? j.feed : [];
  return feed.map((n) => {
    if (!n || !n.title || !n.url) return null;
    // time_published is "YYYYMMDDTHHMMSS" → ISO.
    const tp = String(n.time_published || "");
    const iso = /^\d{8}T\d{6}$/.test(tp)
      ? `${tp.slice(0, 4)}-${tp.slice(4, 6)}-${tp.slice(6, 8)}T${tp.slice(9, 11)}:${tp.slice(11, 13)}:${tp.slice(13, 15)}Z`
      : new Date().toISOString();
    const symbols = Array.isArray(n.ticker_sentiment)
      ? n.ticker_sentiment.map((t) => String(t.ticker || "").toUpperCase()).filter(Boolean).slice(0, 8)
      : [];
    return {
      id: n.url,
      headline: String(n.title).trim(),
      url: n.url,
      source: n.source || "Alpha Vantage",
      summary: n.summary || "",
      image: /^https:\/\//i.test(n.banner_image || "") ? n.banner_image : "",
      published: iso,
      symbols,
      sentimentScore: Number.isFinite(+n.overall_sentiment_score) ? +n.overall_sentiment_score : 0,
      sentimentLabel: n.overall_sentiment_label || "Neutral",
    };
  }).filter(Boolean);
}

/**
 * Unified macro reading: FRED first (authoritative, generous rate limit), else the
 * free Alpha Vantage economic indicator, else null. Returns
 * {alias, label, latest:{date,value}, momPct, yoyPct, source, url}. This is the seam
 * that lets the Σ₀ council's macro grounding work on the already-connected AV key
 * TODAY and transparently switch to FRED the moment its key is added — no caller
 * change.
 */
async function macroLatest(alias) {
  if (hasFred() && (FRED_SERIES[alias] || alias)) {
    const r = await fredLatest(alias);
    if (r && r.latest) {
      return {
        alias, label: MACRO_LABEL[alias] || r.seriesId, latest: r.latest, yearAgo: r.yearAgo,
        momPct: r.momPct, yoyPct: r.yoyPct, source: "FRED",
        url: `https://fred.stlouisfed.org/series/${r.seriesId}`,
      };
    }
  }
  if (hasAlphaVantage() && AV_ECONOMIC[alias]) {
    const r = await alphaVantageEconomic(alias);
    if (r && r.latest) {
      return {
        alias, label: r.label, latest: r.latest, yearAgo: r.yearAgo, momPct: r.momPct, yoyPct: r.yoyPct,
        source: "AlphaVantage", url: "https://www.alphavantage.co/documentation/#economic-indicators",
      };
    }
  }
  return null;
}

module.exports = {
  hasFinnhub, hasFred, hasAlphaVantage,
  finnhubMarketNews, finnhubCompanyNews, finnhubQuote, finnhubRecommendation,
  fredObservations, fredLatest, fredSeriesRelease, fredNextRelease, FRED_SERIES,
  alphaVantageEconomic, alphaVantageNewsSentiment, AV_ECONOMIC,
  macroLatest, MACRO_LABEL,
};
