/**
 * Execution Router — PRL-1.2 Route Decision Engine
 *
 * Decides where to send trades:
 * - paper: Execute on Alpaca paper account
 * - simulation: Mock fill (for testing)
 * - blocked: Reject all execution
 *
 * Implements safety gates and validation before routing.
 */

"use strict";

class ExecutionRouter {
  constructor(alpacaAdapter, options = {}) {
    this.alpacaAdapter = alpacaAdapter;
    this.mode = options.mode || "paper";
    this.allowLive = options.allowLive === true ? true : false;

    if (this.allowLive && this.mode === "live") {
      console.warn("[Router] LIVE TRADING MODE ENABLED (REAL MONEY)");
    } else if (!this.allowLive) {
      console.log("[Router] Live trading disabled (paper mode only)");
    }

    this.routedTrades = 0;
    this.acceptedTrades = 0;
    this.rejectedTrades = 0;
    this.mockTrades = 0;

    console.log(`[Router] Initialized (mode: ${this.mode}, allowLive: ${this.allowLive})`);
  }

  /**
   * Route a trade to the appropriate execution path
   *
   * Returns:
   * {
   *   routed: true|false,
   *   path: "alpaca" | "mock" | "blocked",
   *   reason: string,
   *   execution: executionResult (if executed)
   * }
   */
  async routeTrade(trade, context = {}) {
    this.routedTrades++;

    const {
      tradeId,
      symbol,
      side,
      quantity,
      stabilityIndex = 0.8,
      eventId,
      traceId
    } = trade;

    // Validation Check 1: Is trade state valid?
    if (!symbol || !side || !quantity) {
      this.rejectedTrades++;
      return {
        routed: false,
        path: "rejected",
        reason: "invalid_trade_schema",
        execution: null
      };
    }

    // Validation Check 2: Safety gate (stability >= 0.8)
    if (stabilityIndex < 0.8) {
      this.rejectedTrades++;
      return {
        routed: false,
        path: "blocked",
        reason: `safety_gate_failed (stability: ${stabilityIndex.toFixed(2)} < 0.8)`,
        execution: null
      };
    }

    // Validation Check 3: Trade state must be PENDING
    if (trade.status && trade.status !== "PENDING") {
      this.rejectedTrades++;
      return {
        routed: false,
        path: "blocked",
        reason: `invalid_trade_status (${trade.status})`,
        execution: null
      };
    }

    // Route based on mode
    if (this.mode === "blocked") {
      this.rejectedTrades++;
      return {
        routed: false,
        path: "blocked",
        reason: "execution_disabled",
        execution: null
      };
    }

    if (this.mode === "simulation") {
      return this._executeMock(trade, context);
    }

    if (this.mode === "paper" || (this.mode === "live" && this.allowLive)) {
      return this._executeAlpaca(trade, context);
    }

    this.rejectedTrades++;
    return {
      routed: false,
      path: "blocked",
      reason: "unknown_mode",
      execution: null
    };
  }

  /**
   * Execute on Alpaca (paper or live)
   */
  async _executeAlpaca(trade, context) {
    try {
      if (!this.alpacaAdapter) {
        throw new Error("Alpaca adapter not initialized");
      }

      const normalizedTrade = {
        symbol: trade.symbol,
        side: trade.side.toLowerCase(),
        qty: trade.quantity,
        type: "market",
        time_in_force: "day"
      };

      const result = await this.alpacaAdapter.executeTrade(normalizedTrade);

      if (result.status === "filled" || result.status === "accepted") {
        this.acceptedTrades++;
        return {
          routed: true,
          path: "alpaca",
          reason: "executed",
          execution: result
        };
      } else {
        this.rejectedTrades++;
        return {
          routed: false,
          path: "alpaca",
          reason: "execution_failed",
          execution: result
        };
      }

    } catch (error) {
      console.error(`[Router] Alpaca execution error: ${error.message}`);
      this.rejectedTrades++;
      return {
        routed: false,
        path: "alpaca",
        reason: `execution_error (${error.message})`,
        execution: null
      };
    }
  }

  /**
   * Execute with mock fill (for testing)
   */
  async _executeMock(trade, context) {
    try {
      // Simulate immediate fill
      const mockResult = {
        broker: "mock",
        orderId: `mock-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        status: "filled",
        filledQty: trade.quantity,
        avgFillPrice: 100 + (Math.random() * 20), // Random fill price
        timestamp: Date.now(),
        raw: {
          symbol: trade.symbol,
          qty: trade.quantity,
          side: trade.side
        }
      };

      this.acceptedTrades++;
      this.mockTrades++;

      return {
        routed: true,
        path: "mock",
        reason: "mock_fill",
        execution: mockResult
      };

    } catch (error) {
      console.error(`[Router] Mock execution error: ${error.message}`);
      this.rejectedTrades++;
      return {
        routed: false,
        path: "mock",
        reason: `mock_error (${error.message})`,
        execution: null
      };
    }
  }

  /**
   * Set execution mode
   */
  setMode(mode) {
    if (!["paper", "simulation", "blocked"].includes(mode) && !(mode === "live" && this.allowLive)) {
      throw new Error(`Invalid mode: ${mode}`);
    }
    console.log(`[Router] Mode changed: ${this.mode} → ${mode}`);
    this.mode = mode;
  }

  /**
   * Get routing statistics
   */
  getStats() {
    const total = this.routedTrades || 1;
    return {
      mode: this.mode,
      allowLive: this.allowLive,
      totalRouted: this.routedTrades,
      acceptedTrades: this.acceptedTrades,
      rejectedTrades: this.rejectedTrades,
      mockTrades: this.mockTrades,
      successRate: ((this.acceptedTrades / total) * 100).toFixed(1) + "%"
    };
  }
}

module.exports = ExecutionRouter;
