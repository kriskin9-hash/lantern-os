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

const WATCHLIST_PATH = path.resolve(__dirname, "..", "..", "..", "data", "lantern-garage", "trading", "watchlist.json");
const BROAD_MARKET_SYMBOLS = ["^GSPC", "^DJI", "^IXIC", "^VIX"];

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
  return new Promise((resolve) => {
    const req = https.get(url, { timeout: 8000 }, (res) => {
      let body = "";
      res.on("data", (chunk) => (body += chunk));
      res.on("end", () => resolve(body));
    });
    req.on("error", (e) => {
      console.error("[NewsCollector] Fetch error:", e.message);
      resolve("");
    });
    req.on("timeout", () => {
      req.destroy();
      resolve("");
    });
  });
}

function loadWatchlist() {
  try {
    const raw = fs.readFileSync(WATCHLIST_PATH, "utf8");
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed.tickers)) return parsed.tickers;
  } catch {
    // file missing or invalid — fall back to empty list (broad-market still runs)
  }
  return [];
}

class NewsCollector {
  constructor() {
    this.running = false;
    this.pollInterval = null;
  }

  async _collectFor(symbols, tag) {
    const xml = await fetchRss(symbols);
    if (!xml) return 0;
    const items = parseRssItems(xml).slice(0, 8);
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
      if (rec && rec.tier === "entity") recorded++;
    }
    return recorded;
  }

  async collectOnce() {
    // Stock-style tickers only (e.g. excludes BTCUSD/ETHUSD/SOLUSD, which
    // don't have Yahoo Finance equity RSS feeds — crypto news is handled by
    // crypto-collector.js).
    const tickers = loadWatchlist().filter((t) => /^[A-Z]{1,5}$/.test(t));

    let total = await this._collectFor(BROAD_MARKET_SYMBOLS, "broad");
    for (const ticker of tickers) {
      total += await this._collectFor([ticker], ticker);
      // Be polite to Yahoo's free RSS endpoint
      await new Promise((r) => setTimeout(r, 500));
    }

    if (total > 0) {
      console.log(`[NewsCollector] Recorded ${total} new headline(s)`);
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
