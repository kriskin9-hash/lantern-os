/**
 * Risk Governor — PRL-1.3 Capital Protection Layer
 *
 * HIGHEST AUTHORITY IN THE SYSTEM
 *
 * Sits ABOVE all execution logic.
 * Can block any trade for ANY reason.
 * Owns capital preservation rules globally.
 *
 * Even if:
 * - AI says BUY
 * - Engine validates it
 * - Router approves it
 * - Stability gate passes
 *
 * Risk Governor can still say NO.
 *
 * This is the single point of capital control.
 */

"use strict";

class RiskGovernor {
  constructor(config = {}) {
    this.state = {
      enabled: true,
      maxDailyLossUSD: config.maxDailyLossUSD || 500,
      maxPositionSizeUSD: config.maxPositionSizeUSD || 1000,
      maxOpenTrades: config.maxOpenTrades || 5,
      cooldownMs: config.cooldownMs || 5000,
      maxDrawdownPercent: config.maxDrawdownPercent || 10,

      // Runtime tracking
      lastTradeTime: 0,
      dailyPnL: 0,
      openTrades: 0,
      blockedCount: 0,
      executedCount: 0,
      totalLoss: 0,
      highWaterMark: 0,

      // Emergency state
      emergencyStopActive: false,
      emergencyStopTime: null
    };

    this.blockReasons = [];
    this.tradeHistory = [];

    console.log(`[RiskGovernor] Initialized with limits:`);
    console.log(`  - Max Daily Loss: $${this.state.maxDailyLossUSD}`);
    console.log(`  - Max Position Size: $${this.state.maxPositionSizeUSD}`);
    console.log(`  - Max Open Trades: ${this.state.maxOpenTrades}`);
    console.log(`  - Cooldown: ${this.state.cooldownMs}ms`);
    console.log(`  - Max Drawdown: ${this.state.maxDrawdownPercent}%`);
  }

  /**
   * Evaluate if a trade is allowed to execute
   *
   * Returns:
   * {
   *   allowed: boolean,
   *   reasons: string[],
   *   severity: "info" | "warning" | "critical"
   * }
   */
  evaluateTrade(trade, context = {}) {
    const reasons = [];
    let severity = "info";

    // ──────────────────────────────────────────────────────────
    // GATE 1: Is the Governor enabled?
    // ──────────────────────────────────────────────────────────
    if (!this.state.enabled) {
      return {
        allowed: false,
        reasons: ["GOVERNOR_DISABLED"],
        severity: "critical"
      };
    }

    // ──────────────────────────────────────────────────────────
    // GATE 2: Is emergency stop active?
    // ──────────────────────────────────────────────────────────
    if (this.state.emergencyStopActive) {
      const timeSinceStop = Date.now() - this.state.emergencyStopTime;
      return {
        allowed: false,
        reasons: [`EMERGENCY_STOP_ACTIVE (${timeSinceStop}ms ago)`],
        severity: "critical"
      };
    }

    // ──────────────────────────────────────────────────────────
    // GATE 3: Cooldown enforcement (throttle frequency)
    // ──────────────────────────────────────────────────────────
    const now = Date.now();
    const timeSinceLastTrade = now - this.state.lastTradeTime;
    if (timeSinceLastTrade < this.state.cooldownMs) {
      const remainingCooldown = this.state.cooldownMs - timeSinceLastTrade;
      reasons.push(`COOLDOWN_ACTIVE (${remainingCooldown}ms remaining)`);
      severity = "warning";
    }

    // ──────────────────────────────────────────────────────────
    // GATE 4: Max open trades check
    // ──────────────────────────────────────────────────────────
    if (this.state.openTrades >= this.state.maxOpenTrades) {
      reasons.push(`MAX_OPEN_TRADES_REACHED (${this.state.openTrades}/${this.state.maxOpenTrades})`);
      severity = "warning";
    }

    // ──────────────────────────────────────────────────────────
    // GATE 5: Position size check
    // ──────────────────────────────────────────────────────────
    const positionNotional = context.quantity * context.price || context.notional || 0;
    if (positionNotional > this.state.maxPositionSizeUSD) {
      reasons.push(`POSITION_TOO_LARGE ($${positionNotional.toFixed(2)} > $${this.state.maxPositionSizeUSD})`);
      severity = "warning";
    }

    // ──────────────────────────────────────────────────────────
    // GATE 6: Daily loss limit check (CRITICAL)
    // ──────────────────────────────────────────────────────────
    if (this.state.dailyPnL <= -this.state.maxDailyLossUSD) {
      reasons.push(`MAX_DAILY_LOSS_REACHED ($${this.state.dailyPnL.toFixed(2)} < -$${this.state.maxDailyLossUSD})`);
      severity = "critical";
    }

    // ──────────────────────────────────────────────────────────
    // GATE 7: Drawdown check (unrealized loss)
    // ──────────────────────────────────────────────────────────
    const currentDrawdown = this._calculateDrawdown();
    if (currentDrawdown > this.state.maxDrawdownPercent) {
      reasons.push(`MAX_DRAWDOWN_EXCEEDED (${currentDrawdown.toFixed(1)}% > ${this.state.maxDrawdownPercent}%)`);
      severity = "critical";
    }

    // ──────────────────────────────────────────────────────────
    // DECISION: Are we blocked?
    // ──────────────────────────────────────────────────────────
    const allowed = reasons.length === 0;

    if (!allowed) {
      this.state.blockedCount++;
      console.log(`[RiskGovernor] BLOCKED trade: ${trade.symbol} ${trade.side}`);
      console.log(`  Reasons: ${reasons.join(", ")}`);
    }

    return {
      allowed,
      reasons,
      severity,
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Record a trade execution
   * Called AFTER trade executes successfully
   */
  recordExecution(trade, executionResult) {
    const tradeRecord = {
      symbol: trade.symbol,
      side: trade.side,
      quantity: trade.quantity,
      price: executionResult.avgFillPrice || 0,
      notional: (trade.quantity || 1) * (executionResult.avgFillPrice || 0),
      status: executionResult.status,
      orderId: executionResult.orderId,
      timestamp: Date.now(),
      pnl: executionResult.pnl || 0
    };

    // Update state
    this.state.lastTradeTime = Date.now();
    this.state.executedCount++;

    // Track open trades
    if (executionResult.status === "filled") {
      if (trade.side.toLowerCase() === "buy") {
        this.state.openTrades++;
      } else if (trade.side.toLowerCase() === "sell") {
        this.state.openTrades = Math.max(0, this.state.openTrades - 1);
      }
    }

    // Update P&L
    if (executionResult.pnl !== undefined) {
      this.state.dailyPnL += executionResult.pnl;

      // Track total loss for drawdown calc
      if (executionResult.pnl < 0) {
        this.state.totalLoss += Math.abs(executionResult.pnl);
      } else {
        // Update high water mark
        this.state.highWaterMark = Math.max(this.state.highWaterMark, executionResult.pnl);
      }
    }

    // Record history
    this.tradeHistory.push(tradeRecord);
    if (this.tradeHistory.length > 1000) {
      this.tradeHistory.shift(); // Keep last 1000
    }

    console.log(`[RiskGovernor] Recorded execution: ${tradeRecord.symbol} (PnL: $${tradeRecord.pnl.toFixed(2)})`);
  }

  /**
   * Calculate current drawdown percentage
   */
  _calculateDrawdown() {
    if (this.state.highWaterMark === 0) return 0;
    return (this.state.totalLoss / this.state.highWaterMark) * 100;
  }

  /**
   * Emergency stop: Freeze all trading immediately
   */
  emergencyStop() {
    this.state.emergencyStopActive = true;
    this.state.emergencyStopTime = Date.now();
    console.error(`[RiskGovernor] ⚠️ EMERGENCY STOP ACTIVATED`);
    console.error(`[RiskGovernor] All trading frozen. Manual resume required.`);
  }

  /**
   * Resume trading after emergency stop
   */
  resume() {
    if (!this.state.emergencyStopActive) {
      console.warn(`[RiskGovernor] Resume called but emergency stop not active`);
      return;
    }

    this.state.emergencyStopActive = false;
    this.state.emergencyStopTime = null;
    console.log(`[RiskGovernor] Trading resumed`);
  }

  /**
   * Reset daily counters (call at market open)
   */
  resetDaily() {
    const previousDailyPnL = this.state.dailyPnL;
    this.state.dailyPnL = 0;
    this.state.blockedCount = 0;
    console.log(`[RiskGovernor] Daily reset. Previous PnL: $${previousDailyPnL.toFixed(2)}`);
  }

  /**
   * Update a configuration limit
   */
  updateLimit(field, value) {
    if (field in this.state) {
      const oldValue = this.state[field];
      this.state[field] = value;
      console.log(`[RiskGovernor] Updated ${field}: $${oldValue} → $${value}`);
    }
  }

  /**
   * Get current state
   */
  getState() {
    return {
      enabled: this.state.enabled,
      emergencyStop: this.state.emergencyStopActive,
      limits: {
        maxDailyLossUSD: this.state.maxDailyLossUSD,
        maxPositionSizeUSD: this.state.maxPositionSizeUSD,
        maxOpenTrades: this.state.maxOpenTrades,
        cooldownMs: this.state.cooldownMs,
        maxDrawdownPercent: this.state.maxDrawdownPercent
      },
      metrics: {
        dailyPnL: this.state.dailyPnL,
        openTrades: this.state.openTrades,
        executedCount: this.state.executedCount,
        blockedCount: this.state.blockedCount,
        currentDrawdown: this._calculateDrawdown().toFixed(2) + "%",
        lastTradeTime: new Date(this.state.lastTradeTime).toISOString()
      }
    };
  }

  /**
   * Get status for API response
   */
  getStatus() {
    const state = this.getState();
    return {
      timestamp: new Date().toISOString(),
      status: this.state.emergencyStopActive ? "EMERGENCY_STOP" : (this.state.enabled ? "ACTIVE" : "DISABLED"),
      ...state
    };
  }
}

module.exports = RiskGovernor;
