/**
 * Execution Budget Controller
 *
 * Controls AI trading activity rate and position sizing.
 * Prevents overtrading and scales positions based on performance.
 *
 * CRITICAL: Even good AI can fail if it trades too much.
 * This layer enforces discipline.
 */

"use strict";

class ExecutionBudgetController {
  constructor(config = {}) {
    this.config = {
      maxTradesPerHour: config.maxTradesPerHour || 10,
      maxTradesPerDay: config.maxTradesPerDay || 50,
      maxRiskPerHour: config.maxRiskPerHour || 0.005,     // 0.5% of portfolio
      maxRiskPerDay: config.maxRiskPerDay || 0.02,        // 2% of portfolio
      ...config
    };

    this.budgets = {
      hourly: {
        trades: 0,
        risk: 0,
        resetTime: Date.now(),
      },
      daily: {
        trades: 0,
        risk: 0,
        resetTime: Date.now(),
      },
    };

    this.executionLog = [];
  }

  /**
   * Check if new trade is within budget
   */
  canExecuteNow(tradeRequest, portfolioNav) {
    // Refresh budgets if time windows expired
    this.refreshBudgets();

    const checks = {
      hourlyTradeCount: this.checkHourlyTradeLimit(),
      dailyTradeCount: this.checkDailyTradeLimit(),
      hourlyRisk: this.checkHourlyRiskLimit(tradeRequest, portfolioNav),
      dailyRisk: this.checkDailyRiskLimit(tradeRequest, portfolioNav),
    };

    const violations = Object.entries(checks)
      .filter(([_, result]) => !result.allowed)
      .map(([name, result]) => result.reason);

    return {
      allowed: Object.values(checks).every(c => c.allowed),
      violations,
      budgetStatus: {
        hourlyTrades: `${this.budgets.hourly.trades}/${this.config.maxTradesPerHour}`,
        dailyTrades: `${this.budgets.daily.trades}/${this.config.maxTradesPerDay}`,
        hourlyRisk: `${(this.budgets.hourly.risk * 100).toFixed(3)}%/${(this.config.maxRiskPerHour * 100).toFixed(3)}%`,
        dailyRisk: `${(this.budgets.daily.risk * 100).toFixed(3)}%/${(this.config.maxRiskPerDay * 100).toFixed(3)}%`,
      },
    };
  }

  /**
   * Check hourly trade count
   */
  checkHourlyTradeLimit() {
    if (this.budgets.hourly.trades >= this.config.maxTradesPerHour) {
      return {
        allowed: false,
        reason: `Hourly trade limit (${this.config.maxTradesPerHour}) reached`,
      };
    }

    return {
      allowed: true,
      reason: "Within hourly trade limit",
    };
  }

  /**
   * Check daily trade count
   */
  checkDailyTradeLimit() {
    if (this.budgets.daily.trades >= this.config.maxTradesPerDay) {
      return {
        allowed: false,
        reason: `Daily trade limit (${this.config.maxTradesPerDay}) reached`,
      };
    }

    return {
      allowed: true,
      reason: "Within daily trade limit",
    };
  }

  /**
   * Check hourly risk budget
   */
  checkHourlyRiskLimit(tradeRequest, portfolioNav) {
    const tradeRisk = this.calculateTradeRisk(tradeRequest, portfolioNav);
    const projectedRisk = this.budgets.hourly.risk + tradeRisk;

    if (projectedRisk > this.config.maxRiskPerHour) {
      return {
        allowed: false,
        reason: `Trade would exceed hourly risk limit (${(projectedRisk * 100).toFixed(3)}% > ${(this.config.maxRiskPerHour * 100).toFixed(3)}%)`,
      };
    }

    return {
      allowed: true,
      reason: "Within hourly risk limit",
    };
  }

  /**
   * Check daily risk budget
   */
  checkDailyRiskLimit(tradeRequest, portfolioNav) {
    const tradeRisk = this.calculateTradeRisk(tradeRequest, portfolioNav);
    const projectedRisk = this.budgets.daily.risk + tradeRisk;

    if (projectedRisk > this.config.maxRiskPerDay) {
      return {
        allowed: false,
        reason: `Trade would exceed daily risk limit (${(projectedRisk * 100).toFixed(3)}% > ${(this.config.maxRiskPerDay * 100).toFixed(3)}%)`,
      };
    }

    return {
      allowed: true,
      reason: "Within daily risk limit",
    };
  }

  /**
   * Calculate risk of a trade
   */
  calculateTradeRisk(tradeRequest, portfolioNav) {
    if (!portfolioNav) return 0;

    const position = tradeRequest.quantity * tradeRequest.price;
    const positionPercent = position / portfolioNav;

    // Use stop loss to estimate risk
    const stopLossPercent = tradeRequest.stopLoss || 0.02;  // Default 2% stop
    const riskPercent = positionPercent * stopLossPercent;

    return Math.min(riskPercent, this.config.maxRiskPerDay);
  }

  /**
   * Record executed trade
   */
  recordExecution(tradeId, tradeRequest, portfolioNav) {
    const tradeRisk = this.calculateTradeRisk(tradeRequest, portfolioNav);

    // Update budgets
    this.budgets.hourly.trades++;
    this.budgets.daily.trades++;
    this.budgets.hourly.risk += tradeRisk;
    this.budgets.daily.risk += tradeRisk;

    // Log execution
    this.executionLog.push({
      timestamp: Date.now(),
      tradeId,
      ticker: tradeRequest.ticker,
      side: tradeRequest.side,
      quantity: tradeRequest.quantity,
      riskUsed: tradeRisk,
      hourlyTradeCount: this.budgets.hourly.trades,
      dailyTradeCount: this.budgets.daily.trades,
    });

    console.log(
      `[BudgetController] Trade recorded: ${tradeRequest.ticker} ` +
      `(hourly: ${this.budgets.hourly.trades}/${this.config.maxTradesPerHour}, ` +
      `daily: ${this.budgets.daily.trades}/${this.config.maxTradesPerDay})`
    );
  }

  /**
   * Calculate position size multiplier based on performance
   */
  calculatePositionMultiplier(shadowMetrics) {
    let multiplier = 1.0;

    if (!shadowMetrics) {
      return multiplier;
    }

    // Win rate scaling
    if (shadowMetrics.totalTrades > 0) {
      const winRate = shadowMetrics.winningTrades / shadowMetrics.totalTrades;

      if (winRate < 0.4) {
        multiplier *= 0.5;  // Losing streak: reduce by 50%
      } else if (winRate > 0.7) {
        multiplier *= 1.2;  // Winning streak: scale up by 20%
      }
    }

    // Drawdown scaling
    if (shadowMetrics.maxDrawdown > 0.05) {
      multiplier *= (1 - shadowMetrics.maxDrawdown);  // Scale down by drawdown
    }

    // Profit factor scaling
    if (shadowMetrics.profitFactor) {
      if (shadowMetrics.profitFactor < 1.0) {
        multiplier *= 0.75;  // Losing ratio: reduce by 25%
      } else if (shadowMetrics.profitFactor > 2.0) {
        multiplier *= 1.1;   // Strong ratio: increase by 10%
      }
    }

    return Math.max(0.1, Math.min(multiplier, 2.0));  // Clamp to 0.1x - 2.0x
  }

  /**
   * Suggest position size based on budget
   */
  getSuggestedPositionSize(tradeRequest, portfolioNav, shadowMetrics) {
    const remaining = this.config.maxTradesPerHour - this.budgets.hourly.trades;

    if (remaining <= 0) {
      return { size: 0, reason: "Hourly trade limit reached" };
    }

    // Calculate multiplier
    const performanceMultiplier = this.calculatePositionMultiplier(shadowMetrics);

    // Calculate base position size from budget
    const maxRiskRemaining = this.config.maxRiskPerHour - this.budgets.hourly.risk;
    const baseSize = Math.floor((maxRiskRemaining * portfolioNav) / (tradeRequest.price * 0.02));

    // Apply multiplier
    const suggestedSize = Math.max(
      Math.floor(baseSize * performanceMultiplier),
      1
    );

    return {
      size: suggestedSize,
      multiplier: performanceMultiplier,
      budgetRemaining: maxRiskRemaining,
    };
  }

  /**
   * Refresh budgets if time windows expired
   */
  refreshBudgets() {
    const now = Date.now();
    const hourMs = 60 * 60 * 1000;
    const dayMs = 24 * 60 * 60 * 1000;

    // Reset hourly budget
    if (now - this.budgets.hourly.resetTime > hourMs) {
      this.budgets.hourly = {
        trades: 0,
        risk: 0,
        resetTime: now,
      };
    }

    // Reset daily budget
    if (now - this.budgets.daily.resetTime > dayMs) {
      this.budgets.daily = {
        trades: 0,
        risk: 0,
        resetTime: now,
      };
    }
  }

  /**
   * Get budget status
   */
  getStatus() {
    return {
      hourly: {
        trades: `${this.budgets.hourly.trades}/${this.config.maxTradesPerHour}`,
        risk: `${(this.budgets.hourly.risk * 100).toFixed(3)}%/${(this.config.maxRiskPerHour * 100).toFixed(3)}%`,
        remaining: this.config.maxTradesPerHour - this.budgets.hourly.trades,
      },
      daily: {
        trades: `${this.budgets.daily.trades}/${this.config.maxTradesPerDay}`,
        risk: `${(this.budgets.daily.risk * 100).toFixed(3)}%/${(this.config.maxRiskPerDay * 100).toFixed(3)}%`,
        remaining: this.config.maxTradesPerDay - this.budgets.daily.trades,
      },
    };
  }

  /**
   * Get recent execution log
   */
  getExecutionLog(limit = 20) {
    return this.executionLog.slice(-limit);
  }

  /**
   * Reset budgets (usually at end of day)
   */
  resetDaily() {
    this.budgets.daily = {
      trades: 0,
      risk: 0,
      resetTime: Date.now(),
    };
    console.log("[BudgetController] Daily budget reset");
  }
}

module.exports = ExecutionBudgetController;
