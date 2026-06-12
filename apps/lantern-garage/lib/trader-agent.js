/**
 * Trader Agent — Local wrapper for Python trading logic
 *
 * This module wraps the Python agents.py trading logic as a callable service.
 * Instead of running agents.py in a separate process, it spawns targeted Python
 * operations on-demand and caches results for the configured interval.
 *
 * No external ports or services required — everything runs locally.
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

class TraderAgent {
  constructor(config = {}) {
    this.config = config;
    this.pythonPath = path.join(__dirname, '../../src/trading_agents');
    this.cache = {};
    this.cacheExpiry = config.cacheExpiry || 60000; // 60s default
    this.pythonTimeout = config.pythonTimeout || 30000; // 30s timeout
    this.alpacaKey = process.env.ALPACA_API_KEY;
    this.alpacaSecret = process.env.ALPACA_SECRET_KEY;
    this.watchlist = this._parseWatchlist(process.env.TRADER_WATCHLIST);
  }

  _parseWatchlist(envString) {
    if (!envString) return ['SPY', 'AAPL', 'TSLA', 'NVDA', 'AMD'];
    try {
      return JSON.parse(envString);
    } catch {
      return envString.split(',').map(s => s.trim());
    }
  }

  /**
   * Scan the market for trading signals using Python agents
   * Returns: { signals: [...], zones: {...}, timestamp, metadata }
   */
  async scanMarket() {
    const cacheKey = 'market_scan';
    if (this.cache[cacheKey] && Date.now() - this.cache[cacheKey].time < this.cacheExpiry) {
      return this.cache[cacheKey].data;
    }

    try {
      const result = await this._callPython('scan_market', {
        watchlist: this.watchlist
      });

      this.cache[cacheKey] = {
        data: result,
        time: Date.now()
      };

      return result;
    } catch (error) {
      console.error('[TraderAgent] Market scan failed:', error.message);
      // Return fallback with empty data
      return {
        signals: [],
        zones: {},
        timestamp: new Date().toISOString(),
        error: error.message
      };
    }
  }

  /**
   * Get market zones for a specific ticker
   * Returns: { support, resistance, trend, volatility, strength, touches }
   */
  async getZones(ticker) {
    const cacheKey = `zones_${ticker}`;
    if (this.cache[cacheKey] && Date.now() - this.cache[cacheKey].time < this.cacheExpiry) {
      return this.cache[cacheKey].data;
    }

    try {
      const result = await this._callPython('get_zones', { ticker });

      this.cache[cacheKey] = {
        data: result,
        time: Date.now()
      };

      return result;
    } catch (error) {
      console.error(`[TraderAgent] Zones for ${ticker} failed:`, error.message);
      return {
        ticker,
        error: error.message
      };
    }
  }

  /**
   * Analyze a specific signal (enrich with ticker, confidence scoring)
   * Returns: { symbol, action, reason, confidence, timestamp }
   */
  async analyzeSignal(signal) {
    try {
      return await this._callPython('analyze_signal', signal);
    } catch (error) {
      console.error('[TraderAgent] Signal analysis failed:', error.message);
      return null;
    }
  }

  /**
   * Get real-time market status
   * Returns: { market_open, vix, vix_regime, spy_trend, day_pnl_pct }
   */
  async getMarketStatus() {
    const cacheKey = 'market_status';
    if (this.cache[cacheKey] && Date.now() - this.cache[cacheKey].time < 30000) { // 30s
      return this.cache[cacheKey].data;
    }

    try {
      const result = await this._callPython('get_market_status', {});

      this.cache[cacheKey] = {
        data: result,
        time: Date.now()
      };

      return result;
    } catch (error) {
      console.error('[TraderAgent] Market status failed:', error.message);
      return {
        market_open: false,
        vix: 0,
        vix_regime: 'UNKNOWN',
        error: error.message
      };
    }
  }

  /**
   * Get watchlist with current prices
   * Returns: [{ ticker, price, chg_pct, is_crypto }, ...]
   */
  async getWatchlistPrices() {
    const cacheKey = 'watchlist_prices';
    if (this.cache[cacheKey] && Date.now() - this.cache[cacheKey].time < 30000) { // 30s
      return this.cache[cacheKey].data;
    }

    try {
      const result = await this._callPython('get_watchlist_prices', {
        tickers: this.watchlist
      });

      this.cache[cacheKey] = {
        data: result,
        time: Date.now()
      };

      return result;
    } catch (error) {
      console.error('[TraderAgent] Watchlist prices failed:', error.message);
      return [];
    }
  }

  /**
   * Get open positions from Alpaca
   * Returns: { positions: [...], account: {...} }
   */
  async getPositions() {
    const cacheKey = 'positions';
    if (this.cache[cacheKey] && Date.now() - this.cache[cacheKey].time < 60000) { // 60s
      return this.cache[cacheKey].data;
    }

    try {
      const result = await this._callPython('get_positions', {
        alpaca_key: this.alpacaKey,
        alpaca_secret: this.alpacaSecret
      });

      this.cache[cacheKey] = {
        data: result,
        time: Date.now()
      };

      return result;
    } catch (error) {
      console.error('[TraderAgent] Get positions failed:', error.message);
      return {
        positions: [],
        account: { equity: 0, cash: 0, buying_power: 0 }
      };
    }
  }

  /**
   * Get OHLCV bars for a ticker
   * Returns: { bars: [...], ticker, timeframe, count }
   */
  async getBars(ticker, timeframe = '1h') {
    const cacheKey = `bars_${ticker}_${timeframe}`;
    if (this.cache[cacheKey] && Date.now() - this.cache[cacheKey].time < 60000) { // 60s
      return this.cache[cacheKey].data;
    }

    try {
      const result = await this._callPython('get_bars', {
        ticker,
        timeframe
      });

      this.cache[cacheKey] = {
        data: result,
        time: Date.now()
      };

      return result;
    } catch (error) {
      console.error(`[TraderAgent] Get bars ${ticker} failed:`, error.message);
      return { bars: [], ticker, timeframe, error: error.message };
    }
  }

  /**
   * Clear cache (useful for testing or forcing refresh)
   */
  clearCache() {
    this.cache = {};
  }

  /**
   * Call Python trading agent via subprocess
   *
   * This spawns a Python process that imports the trading agents module,
   * calls the requested function with arguments, and returns JSON output.
   *
   * @param {string} action - Function to call (e.g., 'scan_market', 'get_zones')
   * @param {object} args - Arguments to pass to the function
   * @returns {Promise<object>} Parsed JSON response from Python
   */
  _callPython(action, args) {
    return new Promise((resolve, reject) => {
      // Validate Python path exists
      if (!fs.existsSync(this.pythonPath)) {
        return reject(new Error(`Python trading_agents path not found: ${this.pythonPath}`));
      }

      // Build Python command
      const pythonScript = path.join(__dirname, '../../src/trading_agents/cli.py');
      if (!fs.existsSync(pythonScript)) {
        return reject(new Error(`Python CLI script not found: ${pythonScript}`));
      }

      // Prepare environment
      const env = {
        ...process.env,
        PYTHONPATH: this.pythonPath,
        ALPACA_API_KEY: this.alpacaKey,
        ALPACA_SECRET_KEY: this.alpacaSecret,
        PYTHONUNBUFFERED: '1'
      };

      // Spawn Python process
      let timedOut = false;
      const timeout = setTimeout(() => {
        timedOut = true;
        proc.kill('SIGTERM');
      }, this.pythonTimeout);

      const proc = spawn('python', [pythonScript, action, JSON.stringify(args)], {
        env,
        stdio: ['pipe', 'pipe', 'pipe'],
        timeout: this.pythonTimeout
      });

      let stdout = '';
      let stderr = '';

      proc.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      proc.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      proc.on('close', (code) => {
        clearTimeout(timeout);

        if (timedOut) {
          return reject(new Error(`Python process timeout (${this.pythonTimeout}ms) for action: ${action}`));
        }

        if (code !== 0) {
          return reject(new Error(`Python error (${action}): ${stderr || stdout}`));
        }

        try {
          const result = JSON.parse(stdout);
          resolve(result);
        } catch (parseError) {
          reject(new Error(`Failed to parse Python output for ${action}: ${parseError.message}\nOutput: ${stdout.slice(0, 200)}`));
        }
      });

      proc.on('error', (error) => {
        clearTimeout(timeout);
        reject(new Error(`Failed to spawn Python process: ${error.message}`));
      });
    });
  }
}

module.exports = TraderAgent;
