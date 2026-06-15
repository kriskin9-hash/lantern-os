/**
 * Kalshi Markets Cache Collector
 *
 * Polls Kalshi's /live-markets endpoint on a schedule and caches results locally,
 * preventing direct frontend API calls that cause rate limiting (#439).
 *
 * All frontend requests go to /api/trading/kalshi/live-markets which returns
 * cached data, not a direct passthrough to Kalshi API.
 */

"use strict";

const kalshi = require("./kalshi-api");

class KalshiMarketsCollector {
  constructor() {
    this.running = false;
    this.pollInterval = null;
    this.cachedMarkets = { markets: [] };
    this.cacheTimestamp = 0;
    this.lastError = null;
  }

  /**
   * Fetch fresh markets data from Kalshi API (called on schedule, not per-request)
   */
  async fetchMarkets() {
    try {
      const result = await kalshi.getMarkets({ status: "open", limit: 500 });

      if (result.status === 200 && result.data) {
        this.cachedMarkets = result.data;
        this.cacheTimestamp = Date.now();
        this.lastError = null;
      } else if (result.status >= 400) {
        console.error(`[KalshiMarketsCollector] API error ${result.status}`);
        this.lastError = `Kalshi API error: ${result.status}`;
      }

      return result;
    } catch (e) {
      console.error("[KalshiMarketsCollector] Fetch error:", e.message);
      this.lastError = e.message;
      return { status: 0, error: e.message };
    }
  }

  /**
   * Get cached markets (returned to frontend instead of making direct API call)
   */
  getCached() {
    return {
      ...this.cachedMarkets,
      _cached: true,
      _cacheAge: Date.now() - this.cacheTimestamp,
      _cacheError: this.lastError
    };
  }

  /**
   * Start collecting on a schedule
   */
  start(intervalMs = 30000) {
    if (this.running) return;
    this.running = true;

    console.log("[KalshiMarketsCollector] Starting (interval: " + intervalMs + "ms)");

    // Fetch immediately
    this.fetchMarkets();

    // Then poll at interval
    this.pollInterval = setInterval(() => {
      this.fetchMarkets();
    }, intervalMs);
  }

  /**
   * Stop collecting
   */
  stop() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
    this.running = false;
    console.log("[KalshiMarketsCollector] Stopped");
  }
}

module.exports = KalshiMarketsCollector;
