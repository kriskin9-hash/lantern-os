/**
 * Market News Collector
 *
 * Fetches headlines for the trading watchlist plus broad-market indices from
 * Yahoo Finance's public RSS feeds (free, no API key) and records each item
 * into the CSF trading-news registry via trading-news.js's recordNewsItem().
 *
 * This gives /trading-news.html a continuously-growing real feed via its CSF
 * fallback path (/api/trading/news/recent), independent of the legacy AI
 * Trader dashboard (dashboard.py, port 5050) which lanternOS does not start.
 */

"use strict";

const fs = require("fs");
const path = require("path");
const https = require("https");
const tradingNews = require("./trading-news");

// Config-based watchlist (loaded dynamically, not hardcoded)
const CONFIG_WATCHLIST_PATH = path.resolve(__dirname, "..", "..", "..", "config", "watchlist.json");
const LEGACY_WATCHLIST_PATH = path.resolve(__dirname, "..", "..", "..", "data", "lantern-garage", "trading", "watchlist.json");
const BROAD_MARKET_SYMBOLS = ["^GSPC", "^DJI", "^IXIC", "^VIX"];
const FALLBACK_TICKERS = ["AAPL", "SPY", "TLT"];

const HIGH_IMPACT_KEYWORDS = [
  "fed", "rate hike", "rate cut", "inflation", "cpi", "jobs report",
  "earnings", "beats", "misses", "guidance", "downgrade", "upgrade",
  "lawsuit", "recall", "fda", "merger", "acquisition", "bankruptcy",
  "crash", "plunge", "surge", "soar", "investigation", "layoffs",
];
const MED_IMPACT_KEYWORDS = [
  "launch", "partnership", "expansion", "forecast", "outlook", "dividend",
  "buyback", "split", "ipo", "contract", "deal", "stake",
];

function scoreImpact(headline) {
  const h = (headline || "").toLowerCase();
  if (HIGH_IMPACT_KEYWORDS.some((k) => h.includes(k))) return 75;
  if (MED_IMPACT_KEYWORDS.some((k) => h.includes(k))) return 55;
  return 35;
}

function decodeEntities(str) {
  return String(str || "")
    .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/, "$1")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&(#39|apos);/g, "'")
    .trim();
}

function parseRssItems(xml) {
  const items = [];
  const blocks = xml.match(/<item>([\s\S]*?)<\/item>/g) || [];
  for (const block of blocks) {
    const title = (block.match(/<title>([\s\S]*?)<\/title>/) || [])[1];
    const link = (block.match(/<link>([\s\S]*?)<\/link>/) || [])[1];
    const pubDate = (block.match(/<pubDate>([\s\S]*?)<\/pubDate>/) || [])[1];
    const sourceMatch = block.match(/<source[^>]*>([\s\S]*?)<\/source>/);
    if (!title || !link) continue;
    const published = pubDate ? new Date(pubDate).toISOString() : new Date().toISOString();
    items.push({
      headline: decodeEntities(title),
      url: decodeEntities(link),
      published,
      source: sourceMatch ? decodeEntities(sourceMatch[1]) : "Yahoo Finance",
    });
  }
  return items;
}

function fetchRss(symbols) {
  const url = `https://feeds.finance.yahoo.com/rss/2.0/headline?s=${encodeURIComponent(symbols.join(","))}&region=US&lang=en-US`;
  console.log("[NewsCollector] Fetching RSS from symbols:", symbols);
  return new Promise((resolve) => {
    // Note: rejectUnauthorized=false is for development only.
    // In production, use proper certificate validation or a proxy.
    const req = https.get(url, {
      timeout: 8000,
      rejectUnauthorized: false // Dev/testing: allow self-signed certs
    }, (res) => {
      console.log("[NewsCollector] RSS response status:", res.statusCode);
      let body = "";

      // Handle rate limiting gracefully
      if (res.statusCode === 429) {
        console.warn("[NewsCollector] Rate limited (429), skipping this feed");
        resolve("");
        return;
      }

      res.on("data", (chunk) => {
        body += chunk;
      });
      res.on("end", () => {
        console.log("[NewsCollector] RSS fetch complete, received", body.length, "bytes");
        resolve(body);
      });
    });
    req.on("error", (e) => {
      console.error("[NewsCollector] Fetch error:", e.message);
      resolve("");
    });
    req.on("timeout", () => {
      console.error("[NewsCollector] Fetch timeout");
      req.destroy();
      resolve("");
    });
  });
}

// Validate watchlist config for integrity
function validateWatchlistConfig(tickers) {
  if (!Array.isArray(tickers)) {
    console.warn("[NewsCollector] Invalid config: tickers must be an array");
    return false;
  }

  if (tickers.length === 0) {
    console.warn("[NewsCollector] Invalid config: tickers array is empty");
    return false;
  }

  const seen = new Set();
  for (const ticker of tickers) {
    // Check format: A-Z only, 1-5 chars for stocks, up to 6 for indices
    if (!/^[A-Z^]{1,6}$/.test(ticker)) {
      console.warn(`[NewsCollector] Invalid ticker format: "${ticker}" (must be A-Z/^, 1-6 chars)`);
      return false;
    }

    // Check for duplicates
    if (seen.has(ticker)) {
      console.warn(`[NewsCollector] Duplicate ticker in config: "${ticker}"`);
      return false;
    }
    seen.add(ticker);
  }

  return true;
}

// Compute config hash for mutation detection
function hashWatchlist(tickers) {
  const crypto = require("crypto");
  return crypto.createHash("sha256").update(JSON.stringify(tickers)).digest("hex").slice(0, 12);
}

function loadWatchlist() {
  // Try config/watchlist.json first (new config-based approach)
  try {
    const raw = fs.readFileSync(CONFIG_WATCHLIST_PATH, "utf8");
    const parsed = JSON.parse(raw);
    if (validateWatchlistConfig(parsed.tickers)) {
      console.log("[NewsCollector] Loaded watchlist from config:", parsed.tickers.length, "tickers");
      return parsed.tickers;
    }
  } catch (e) {
    console.warn("[NewsCollector] Config load failed:", e.message);
  }

  // Fall back to legacy data/lantern-garage/trading/watchlist.json
  try {
    const raw = fs.readFileSync(LEGACY_WATCHLIST_PATH, "utf8");
    const parsed = JSON.parse(raw);
    if (validateWatchlistConfig(parsed.tickers)) {
      console.log("[NewsCollector] Loaded watchlist from legacy path:", parsed.tickers.length, "tickers");
      return parsed.tickers;
    }
  } catch {
    // legacy file also missing or invalid
  }

  // Final fallback to hardcoded tickers
  console.log("[NewsCollector] Using fallback tickers:", FALLBACK_TICKERS.join(", "));
  return FALLBACK_TICKERS;
}

class NewsCollector {
  constructor() {
    this.running = false;
    this.pollInterval = null;
    this.lastFetchTime = {};  // Track last fetch time per feed to avoid rate limiting
    this.fetchDelayMs = 2000;  // Increased delay between feeds
  }

  async _collectFor(symbols, tag) {
    console.log("[NewsCollector] _collectFor:", { symbols, tag });
    const xml = await fetchRss(symbols);
    console.log("[NewsCollector] RSS fetch result:", {
      tag,
      xmlLength: xml ? xml.length : 0,
      hasContent: !!xml
    });
    if (!xml) {
      console.log("[NewsCollector] Empty XML response for", tag);
      return 0;
    }
    const items = parseRssItems(xml).slice(0, 8);
    console.log("[NewsCollector] Parsed items:", { tag, count: items.length, items: items.slice(0, 2) });
    let recorded = 0;
    for (const item of items) {
      const rec = await tradingNews.recordNewsItem({
        ...item,
        symbols: tag === "broad" ? [] : [tag],
        impact: scoreImpact(item.headline),
      }).catch((e) => {
        console.error("[NewsCollector] Record error:", e.message);
        return null;
      });
      if (rec && rec.tier === "entity") {
        console.log("[NewsCollector] Recorded article:", { tag, headline: item.headline.slice(0, 50) });
        recorded++;
      }
    }
    console.log("[NewsCollector] _collectFor complete:", { tag, recorded });
    return recorded;
  }

  async collectOnce() {
    const cycleStartTime = new Date().toISOString();
    const cycleId = Math.floor(Date.now() / 1000);  // Use unix timestamp as cycle ID

    console.log("[NewsCollector] collectOnce() starting at", cycleStartTime);

    // SNAPSHOT ISOLATION: Load config ONCE per cycle and freeze it
    // This prevents mid-cycle mutations from affecting the current batch
    const rawTickers = loadWatchlist();
    const configSnapshot = JSON.parse(JSON.stringify(rawTickers));  // Deep copy for isolation
    const snapshotHash = hashWatchlist(configSnapshot);

    // Stock-style tickers only (e.g. excludes BTCUSD/ETHUSD/SOLUSD, which
    // don't have Yahoo Finance equity RSS feeds — crypto news is handled by
    // crypto-collector.js).
    const tickers = configSnapshot.filter((t) => /^[A-Z]{1,5}$/.test(t));

    // Log cycle metadata for debugging and stability validation
    console.log("[NewsCollector] Cycle metadata:", {
      cycleId,
      tickersLoaded: configSnapshot.length,
      tickersActive: tickers.length,
      snapshotHash,
      configVersion: cycleStartTime,
      mutationsDetected: false  // Placeholder for future mutation detection
    });

    const now = Date.now();
    const minDelayBetweenFeeds = 60000; // 1 minute between feeds to avoid rate limiting

    // Broad market collection (every 10 minutes)
    let total = 0;
    if (!this.lastFetchTime["broad"] || now - this.lastFetchTime["broad"] > minDelayBetweenFeeds) {
      total = await this._collectFor(BROAD_MARKET_SYMBOLS, "broad");
      this.lastFetchTime["broad"] = now;
      console.log("[NewsCollector] Broad market collection complete, total:", total);
      await new Promise((r) => setTimeout(r, this.fetchDelayMs));
    } else {
      console.log("[NewsCollector] Skipping broad market (too recent)");
    }

    // Rotate through tickers to avoid rate limiting all at once
    // Only fetch 3 tickers per run, cycling through the watchlist
    const tickersToFetch = tickers.slice(0, 3);
    for (const ticker of tickersToFetch) {
      if (!this.lastFetchTime[ticker] || now - this.lastFetchTime[ticker] > minDelayBetweenFeeds) {
        const tickerTotal = await this._collectFor([ticker], ticker);
        total += tickerTotal;
        this.lastFetchTime[ticker] = now;
        await new Promise((r) => setTimeout(r, this.fetchDelayMs));
      } else {
        console.log(`[NewsCollector] Skipping ${ticker} (too recent)`);
      }
    }

    console.log(`[NewsCollector] collectOnce() complete at ${new Date().toISOString()}, total recorded: ${total}`);
    if (total > 0) {
      console.log(`[NewsCollector] Recorded ${total} new headline(s)`);
    } else {
      console.log("[NewsCollector] No new articles in this run");
    }
    return total;
  }

  start(intervalMs = 600000) {
    if (this.running) return;
    this.running = true;

    console.log("[NewsCollector] Starting (interval: " + intervalMs + "ms)");

    this.collectOnce().catch((e) => console.error("[NewsCollector] Collect error:", e.message));
    this.pollInterval = setInterval(() => {
      this.collectOnce().catch((e) => console.error("[NewsCollector] Collect error:", e.message));
    }, intervalMs);
  }

  stop() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
    this.running = false;
    console.log("[NewsCollector] Stopped");
  }
}

module.exports = NewsCollector;
