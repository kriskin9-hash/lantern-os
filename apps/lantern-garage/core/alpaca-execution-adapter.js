/**
 * Alpaca Execution Adapter — PRL-1.2 Paper Trading Bridge
 *
 * Wraps Alpaca SDK for paper trading.
 * Normalizes all orders into internal schema.
 * Returns broker-confirmed execution results.
 *
 * CRITICAL: This is the ONLY endpoint that talks to Alpaca.
 * AI never calls Alpaca directly.
 * Event queue consumer calls this ONLY after safety gates pass.
 *
 * Alpaca is treated as a DUMB EXECUTION ENDPOINT.
 * Lantern OS remains the source of truth.
 */

"use strict";

class AlpacaExecutionAdapter {
  constructor(config = {}) {
    this.key = config.key || process.env.ALPACA_API_KEY;
    this.secret = config.secret || process.env.ALPACA_SECRET_KEY;
    this.paper = config.paper !== false; // Default to paper trading

    if (!this.key || !this.secret) {
      console.warn("[Alpaca] Missing API credentials. Paper trading disabled.");
      this.enabled = false;
      return;
    }

    this.enabled = true;
    this.baseUrl = this.paper
      ? "https://paper-api.alpaca.markets"
      : "https://api.alpaca.markets";

    this.stats = {
      totalExecutions: 0,
      filledTrades: 0,
      rejectedTrades: 0,
      avgFillLatencyMs: 0,
      lastExecution: null
    };

    console.log(`[Alpaca] Initialized (${this.paper ? "PAPER" : "LIVE"} mode)`);
  }

  /**
   * Execute a trade on Alpaca
   *
   * Input (normalized trade from engine):
   * {
   *   symbol: "AAPL",
   *   side: "buy" | "sell",
   *   qty: number,
   *   type: "market" | "limit",
   *   time_in_force: "day"
   * }
   *
   * Output:
   * {
   *   broker: "alpaca",
   *   orderId: string,
   *   status: "filled" | "accepted" | "rejected",
   *   filledQty: number,
   *   avgFillPrice: number,
   *   timestamp: number,
   *   raw: alpacaResponse
   * }
   */
  async executeTrade(normalizedTrade) {
    const startTime = Date.now();

    // Validate input
    if (!normalizedTrade.symbol || !normalizedTrade.side || !normalizedTrade.qty) {
      return this._rejectionResult(
        normalizedTrade,
        "invalid_schema",
        "Missing required fields: symbol, side, qty"
      );
    }

    if (!this.enabled) {
      return this._rejectionResult(
        normalizedTrade,
        "adapter_disabled",
        "Alpaca adapter not initialized (missing credentials)"
      );
    }

    try {
      // Call Alpaca API
      const result = await this._callAlpacaAPI(normalizedTrade);

      const latencyMs = Date.now() - startTime;
      this._recordExecution(result, latencyMs);

      console.log(`[Alpaca] Trade executed: ${normalizedTrade.symbol} ${normalizedTrade.side} (orderId: ${result.orderId}, latency: ${latencyMs}ms)`);

      return result;

    } catch (error) {
      console.error(`[Alpaca] Execution error: ${error.message}`);
      return this._rejectionResult(
        normalizedTrade,
        "execution_error",
        error.message
      );
    }
  }

  /**
   * Make HTTP call to Alpaca API
   * In production, use official Alpaca SDK (alpaca-trade-api)
   * For now, simulate a successful fill for testing
   */
  async _callAlpacaAPI(trade) {
    // TODO: Replace with real Alpaca SDK call
    // const Alpaca = require('@alpacahq/ts-sdk');
    // const client = new Alpaca({ credentials: { key: this.key, secret: this.secret } });
    // const order = await client.createOrder({ ... });

    // Simulation: assume market order fills immediately on paper account
    return {
      broker: "alpaca",
      orderId: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      status: trade.type === "market" ? "filled" : "accepted",
      filledQty: trade.side === "buy" ? trade.qty : trade.qty,
      avgFillPrice: this._getSimulatedPrice(trade.symbol),
      timestamp: Date.now(),
      raw: {
        symbol: trade.symbol,
        qty: trade.qty,
        side: trade.side,
        order_type: trade.type,
        time_in_force: trade.time_in_force || "day"
      }
    };
  }

  /**
   * Get simulated fill price (for paper trading)
   * In production, this comes from Alpaca's actual market data
   */
  _getSimulatedPrice(symbol) {
    // Simple simulation: use symbol length as price base
    const basePrice = 100 + (symbol.length % 50);
    const jitter = (Math.random() - 0.5) * 2; // ±1
    return parseFloat((basePrice + jitter).toFixed(2));
  }

  /**
   * Build rejection result
   */
  _rejectionResult(trade, reason, message) {
    return {
      broker: "alpaca",
      orderId: null,
      status: "rejected",
      reason,
      message,
      filledQty: 0,
      avgFillPrice: 0,
      timestamp: Date.now(),
      raw: null
    };
  }

  /**
   * Record execution statistics
   */
  _recordExecution(result, latencyMs) {
    this.stats.totalExecutions++;
    this.stats.lastExecution = Date.now();

    if (result.status === "filled") {
      this.stats.filledTrades++;
      // Update rolling average latency
      const totalLatency = (this.stats.avgFillLatencyMs * (this.stats.filledTrades - 1)) + latencyMs;
      this.stats.avgFillLatencyMs = totalLatency / this.stats.filledTrades;
    } else if (result.status === "rejected") {
      this.stats.rejectedTrades++;
    }
  }

  /**
   * Get execution statistics
   */
  getStats() {
    return {
      ...this.stats,
      enabled: this.enabled,
      mode: this.paper ? "paper" : "live",
      successRate: this.stats.totalExecutions > 0
        ? (this.stats.filledTrades / this.stats.totalExecutions * 100).toFixed(1) + "%"
        : "N/A"
    };
  }
}

module.exports = AlpacaExecutionAdapter;
