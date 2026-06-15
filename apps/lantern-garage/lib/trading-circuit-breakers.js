/**
 * Trading Circuit Breakers
 *
 * Automatically halts trading when risk thresholds are breached.
 * Four independent breakers protect against different failure modes.
 *
 * CRITICAL: Breaker activation is final - requires manual review to deactivate.
 */

"use strict";

class TradingCircuitBreakers {
  constructor(config = {}) {
    this.config = {
      consecutiveLossThreshold: config.consecutiveLossThreshold || 5,
      dailyDrawdownLimit: config.dailyDrawdownLimit || 0.02,  // 2%
      reconciliationFailureLimit: config.reconciliationFailureLimit || 3,
      brokerTimeoutSeconds: config.brokerTimeoutSeconds || 60,
      ...config
    };

    this.state = {
      consecutiveLoosesBreaker: false,
      dailyDrawdownBreaker: false,
      reconciliationBreaker: false,
      brokerUnavailableBreaker: false,
    };

    this.metrics = {
      consecutiveLosses: 0,
      lastTradePnL: null,
      reconciliationFailures: 0,
      lastBrokerResponse: null,
      activatedAt: null,
    };
  }

  /**
   * Check consecutive losses breaker
   */
  checkConsecutiveLosses(recentTrades) {
    const losses = [];

    // Count consecutive losses from most recent
    for (let i = recentTrades.length - 1; i >= 0; i--) {
      if (recentTrades[i].pnl < 0) {
        losses.push(recentTrades[i]);
      } else {
        break;  // Streak broken
      }
    }

    this.metrics.consecutiveLosses = losses.length;

    if (losses.length >= this.config.consecutiveLossThreshold) {
      console.error(
        `[CircuitBreaker] TRIGGERED: ${losses.length} consecutive losses ` +
        `(threshold: ${this.config.consecutiveLossThreshold})`
      );
      return true;
    }

    return false;
  }

  /**
   * Check daily drawdown breaker
   */
  checkDailyDrawdown(dailyPnL, portfolioNav) {
    if (!portfolioNav || portfolioNav <= 0) {
      return false;
    }

    const drawdownPercent = Math.abs(dailyPnL) / portfolioNav;

    if (drawdownPercent > this.config.dailyDrawdownLimit) {
      console.error(
        `[CircuitBreaker] TRIGGERED: Daily drawdown ${(drawdownPercent * 100).toFixed(2)}% ` +
        `exceeds limit ${(this.config.dailyDrawdownLimit * 100).toFixed(2)}%`
      );
      return true;
    }

    return false;
  }

  /**
   * Check reconciliation failure breaker
   */
  checkReconciliationFailures(reconciliationStatus) {
    if (!reconciliationStatus.lastResult) {
      return false;
    }

    if (!reconciliationStatus.lastResult.success) {
      this.metrics.reconciliationFailures++;
    } else {
      this.metrics.reconciliationFailures = 0;  // Reset on success
    }

    if (this.metrics.reconciliationFailures >= this.config.reconciliationFailureLimit) {
      console.error(
        `[CircuitBreaker] TRIGGERED: ${this.metrics.reconciliationFailures} ` +
        `consecutive reconciliation failures`
      );
      return true;
    }

    return false;
  }

  /**
   * Check broker availability breaker
   */
  checkBrokerAvailability(brokerLastResponseTime) {
    const now = Date.now();
    const silenceMs = now - brokerLastResponseTime;
    const silenceSeconds = silenceMs / 1000;

    this.metrics.lastBrokerResponse = brokerLastResponseTime;

    if (silenceSeconds > this.config.brokerTimeoutSeconds) {
      console.error(
        `[CircuitBreaker] TRIGGERED: No broker response for ${silenceSeconds.toFixed(1)}s ` +
        `(timeout: ${this.config.brokerTimeoutSeconds}s)`
      );
      return true;
    }

    return false;
  }

  /**
   * Update all breakers
   */
  updateBreakers(systemState) {
    this.state.consecutiveLoosesBreaker = this.checkConsecutiveLosses(
      systemState.recentTrades || []
    );

    this.state.dailyDrawdownBreaker = this.checkDailyDrawdown(
      systemState.dailyPnL || 0,
      systemState.portfolioNav || 1
    );

    this.state.reconciliationBreaker = this.checkReconciliationFailures(
      systemState.reconciliationStatus || {}
    );

    this.state.brokerUnavailableBreaker = this.checkBrokerAvailability(
      systemState.lastBrokerResponseTime || Date.now()
    );

    return this.getBreacherState();
  }

  /**
   * Get current breaker state
   */
  getBreacherState() {
    const anyTriggered = Object.values(this.state).some(v => v === true);

    return {
      active: anyTriggered,
      breakers: this.state,
      metrics: this.metrics,
      activatedAt: this.metrics.activatedAt,
      summary: this.generateSummary(),
    };
  }

  /**
   * Generate human-readable summary
   */
  generateSummary() {
    const triggered = [];

    if (this.state.consecutiveLoosesBreaker) {
      triggered.push(`Consecutive losses: ${this.metrics.consecutiveLosses}`);
    }
    if (this.state.dailyDrawdownBreaker) {
      triggered.push(`Daily drawdown exceeded`);
    }
    if (this.state.reconciliationBreaker) {
      triggered.push(`Reconciliation failures: ${this.metrics.reconciliationFailures}`);
    }
    if (this.state.brokerUnavailableBreaker) {
      triggered.push(`Broker unavailable`);
    }

    if (triggered.length === 0) {
      return "All breakers normal";
    }

    return `Circuit breakers triggered: ${triggered.join(", ")}`;
  }

  /**
   * Record trade result for loss tracking
   */
  recordTrade(tradeResult) {
    this.metrics.lastTradePnL = tradeResult.pnl;

    // Update broker response time on successful trade
    if (tradeResult.status === "FILLED") {
      this.metrics.lastBrokerResponse = Date.now();
    }
  }

  /**
   * Reset specific breaker
   */
  reset(breakerName) {
    switch (breakerName) {
      case "consecutiveLosses":
        this.state.consecutiveLoosesBreaker = false;
        this.metrics.consecutiveLosses = 0;
        break;
      case "dailyDrawdown":
        this.state.dailyDrawdownBreaker = false;
        break;
      case "reconciliation":
        this.state.reconciliationBreaker = false;
        this.metrics.reconciliationFailures = 0;
        break;
      case "brokerUnavailable":
        this.state.brokerUnavailableBreaker = false;
        break;
      case "all":
        this.state = {
          consecutiveLoosesBreaker: false,
          dailyDrawdownBreaker: false,
          reconciliationBreaker: false,
          brokerUnavailableBreaker: false,
        };
        this.metrics.consecutiveLosses = 0;
        this.metrics.reconciliationFailures = 0;
        break;
    }
  }

  /**
   * Reset at end of trading day
   */
  resetDaily() {
    this.metrics.consecutiveLosses = 0;
    this.metrics.reconciliationFailures = 0;
    this.state.dailyDrawdownBreaker = false;
    this.state.consecutiveLoosesBreaker = false;
    console.log("[CircuitBreaker] Daily reset complete");
  }

  /**
   * Check if any breaker is active
   */
  isTriggered() {
    return Object.values(this.state).some(v => v === true);
  }

  /**
   * Get detailed status for API
   */
  getStatus() {
    return {
      triggered: this.isTriggered(),
      breakers: {
        consecutiveLosses: {
          active: this.state.consecutiveLoosesBreaker,
          threshold: this.config.consecutiveLossThreshold,
          current: this.metrics.consecutiveLosses,
        },
        dailyDrawdown: {
          active: this.state.dailyDrawdownBreaker,
          limit: this.config.dailyDrawdownLimit,
        },
        reconciliation: {
          active: this.state.reconciliationBreaker,
          threshold: this.config.reconciliationFailureLimit,
          current: this.metrics.reconciliationFailures,
        },
        brokerUnavailable: {
          active: this.state.brokerUnavailableBreaker,
          timeoutSeconds: this.config.brokerTimeoutSeconds,
        },
      },
    };
  }
}

module.exports = TradingCircuitBreakers;
