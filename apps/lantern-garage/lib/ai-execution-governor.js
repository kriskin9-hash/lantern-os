/**
 * AI Execution Governor
 *
 * Controls whether AI is allowed to propose trades.
 * Evaluates market regime, risk state, and recent performance.
 *
 * CRITICAL: This decides if AI operates at all.
 * Returns execution mode + position scaling.
 */

"use strict";

class AIExecutionGovernor {
  constructor(config = {}) {
    this.config = {
      aggressiveThreshold: config.aggressiveThreshold || 0.7,  // Win rate
      normalThreshold: config.normalThreshold || 0.55,
      reducedThreshold: config.reducedThreshold || 0.45,
      shadowOnlyThreshold: config.shadowOnlyThreshold || 0.30,
      maxDrawdownForNormal: config.maxDrawdownForNormal || 0.01,  // 1%
      maxDrawdownForReduced: config.maxDrawdownForReduced || 0.02,  // 2%
      volatilityHighThreshold: config.volatilityHighThreshold || 0.35,
      volatilityLowThreshold: config.volatilityLowThreshold || 0.10,
      ...config
    };

    this.state = {
      mode: "NORMAL",
      allowed: true,
      positionMultiplier: 1.0,
      lastEvaluation: null,
      rationale: "",
    };
  }

  /**
   * Evaluate AI permission and execution mode
   */
  evaluate(systemState) {
    const evaluation = {
      timestamp: new Date().toISOString(),
      allowed: true,
      mode: "NORMAL",
      positionMultiplier: 1.0,
      factors: {},
      rationale: [],
    };

    // Factor 1: Win rate (recent trading performance)
    const winRateFactor = this.evaluateWinRate(systemState.shadowPerformance);
    evaluation.factors.winRate = winRateFactor;
    if (winRateFactor.modeAdjustment) {
      evaluation.rationale.push(winRateFactor.rationale);
    }

    // Factor 2: Drawdown risk
    const drawdownFactor = this.evaluateDrawdown(systemState.dailyStats);
    evaluation.factors.drawdown = drawdownFactor;
    if (drawdownFactor.modeAdjustment) {
      evaluation.rationale.push(drawdownFactor.rationale);
    }

    // Factor 3: Market volatility
    const volatilityFactor = this.evaluateVolatility(systemState.volatility);
    evaluation.factors.volatility = volatilityFactor;
    if (volatilityFactor.modeAdjustment) {
      evaluation.rationale.push(volatilityFactor.rationale);
    }

    // Factor 4: Recent losses
    const lossFactor = this.evaluateRecentLosses(systemState.recentTrades);
    evaluation.factors.recentLosses = lossFactor;
    if (lossFactor.modeAdjustment) {
      evaluation.rationale.push(lossFactor.rationale);
    }

    // Factor 5: Execution health
    const executionFactor = this.evaluateExecutionHealth(systemState.executionHealth);
    evaluation.factors.executionHealth = executionFactor;
    if (executionFactor.blockAI) {
      evaluation.allowed = false;
      evaluation.mode = "OFF";
      evaluation.rationale.push(executionFactor.rationale);
    }

    // Determine final mode from factors
    const modes = [
      winRateFactor.mode,
      drawdownFactor.mode,
      volatilityFactor.mode,
      lossFactor.mode,
    ].filter(m => m);

    if (modes.length > 0) {
      evaluation.mode = this.selectRestrictiveMode(modes);
    } else if (evaluation.mode === "NORMAL") {
      // If no restrictive factors, try to go aggressive if win rate is high
      if (winRateFactor.mode === "AGGRESSIVE") {
        evaluation.mode = "AGGRESSIVE";
      }
    }

    // Prevent AI entirely if any circuit breaker triggered
    if (systemState.circuitBreakerActive || systemState.killSwitchActive) {
      evaluation.allowed = false;
      evaluation.mode = "OFF";
      evaluation.rationale.push("Circuit breaker or kill switch active");
    }

    // Calculate position multiplier based on final mode
    const multipliers = {
      "AGGRESSIVE": 1.5,
      "NORMAL": 1.0,
      "REDUCED": 0.5,
      "SHADOW_ONLY": 0.0,
      "OFF": 0.0,
    };
    evaluation.positionMultiplier = (evaluation.mode in multipliers) ? multipliers[evaluation.mode] : 1.0;

    this.state = evaluation;
    return evaluation;
  }

  /**
   * Evaluate win rate from shadow trading
   */
  evaluateWinRate(shadowPerformance) {
    if (!shadowPerformance || shadowPerformance.totalTrades === 0) {
      return {
        winRate: 0,
        mode: null,
        modeAdjustment: false,
        rationale: "",
      };
    }

    const winRate = shadowPerformance.winningTrades / shadowPerformance.totalTrades;

    let mode = null;
    let rationale = "";

    if (winRate >= this.config.aggressiveThreshold) {
      mode = "AGGRESSIVE";
      rationale = `High win rate (${(winRate * 100).toFixed(1)}%) → AGGRESSIVE mode`;
    } else if (winRate >= this.config.normalThreshold) {
      mode = "NORMAL";
      rationale = `Acceptable win rate (${(winRate * 100).toFixed(1)}%)`;
    } else if (winRate >= this.config.reducedThreshold) {
      mode = "REDUCED";
      rationale = `Below-target win rate (${(winRate * 100).toFixed(1)}%) → REDUCED mode`;
    } else if (winRate >= this.config.shadowOnlyThreshold) {
      mode = "SHADOW_ONLY";
      rationale = `Poor win rate (${(winRate * 100).toFixed(1)}%) → SHADOW_ONLY mode`;
    } else {
      mode = "OFF";
      rationale = `Critical win rate failure (${(winRate * 100).toFixed(1)}%) → OFF`;
    }

    return {
      winRate,
      mode,
      modeAdjustment: true,
      rationale,
    };
  }

  /**
   * Evaluate drawdown impact
   */
  evaluateDrawdown(dailyStats) {
    if (!dailyStats || !dailyStats.nav) {
      return {
        drawdownPercent: 0,
        mode: null,
        modeAdjustment: false,
        rationale: "",
      };
    }

    const drawdownPercent = Math.abs(dailyStats.pnl) / dailyStats.nav;

    let mode = null;
    let rationale = "";

    if (drawdownPercent <= this.config.maxDrawdownForNormal) {
      mode = null;  // No adjustment needed
    } else if (drawdownPercent <= this.config.maxDrawdownForReduced) {
      mode = "REDUCED";
      rationale = `Drawdown ${(drawdownPercent * 100).toFixed(2)}% → reduce position size`;
    } else {
      mode = "SHADOW_ONLY";
      rationale = `Drawdown ${(drawdownPercent * 100).toFixed(2)}% exceeds limit → SHADOW_ONLY`;
    }

    return {
      drawdownPercent,
      mode,
      modeAdjustment: !!mode,
      rationale,
    };
  }

  /**
   * Evaluate market volatility regime
   */
  evaluateVolatility(volatility) {
    if (!volatility) {
      return {
        vixLevel: 0,
        mode: null,
        modeAdjustment: false,
        rationale: "",
      };
    }

    let mode = null;
    let rationale = "";

    if (volatility > this.config.volatilityHighThreshold) {
      mode = "REDUCED";
      rationale = `High volatility (${volatility.toFixed(2)}) → reduce exposure`;
    } else if (volatility < this.config.volatilityLowThreshold) {
      // Low volatility might allow aggressive mode
      mode = null;
    }

    return {
      vixLevel: volatility,
      mode,
      modeAdjustment: !!mode,
      rationale,
    };
  }

  /**
   * Evaluate recent loss streak
   */
  evaluateRecentLosses(recentTrades) {
    if (!recentTrades || recentTrades.length === 0) {
      return {
        recentLosses: 0,
        mode: null,
        modeAdjustment: false,
        rationale: "",
      };
    }

    // Count consecutive losses from most recent
    let consecutiveLosses = 0;
    for (let i = recentTrades.length - 1; i >= 0; i--) {
      if (recentTrades[i].pnl < 0) {
        consecutiveLosses++;
      } else {
        break;
      }
    }

    let mode = null;
    let rationale = "";

    if (consecutiveLosses >= 3) {
      mode = "SHADOW_ONLY";
      rationale = `${consecutiveLosses} consecutive losses → SHADOW_ONLY`;
    } else if (consecutiveLosses >= 2) {
      mode = "REDUCED";
      rationale = `${consecutiveLosses} consecutive losses → reduce position size`;
    }

    return {
      recentLosses: consecutiveLosses,
      mode,
      modeAdjustment: !!mode,
      rationale,
    };
  }

  /**
   * Evaluate execution system health
   */
  evaluateExecutionHealth(executionHealth) {
    const blockAI = false;
    let rationale = "";

    if (executionHealth && executionHealth.reconciledFailures > 3) {
      return {
        blockAI: true,
        rationale: "Reconciliation failures → block AI",
      };
    }

    if (executionHealth && executionHealth.brokerUnavailable) {
      return {
        blockAI: true,
        rationale: "Broker unavailable → block AI",
      };
    }

    return {
      blockAI,
      rationale,
    };
  }

  /**
   * Select most restrictive mode from factors
   */
  selectRestrictiveMode(modes) {
    const hierarchy = {
      "OFF": 5,
      "SHADOW_ONLY": 4,
      "REDUCED": 3,
      "NORMAL": 2,
      "AGGRESSIVE": 1,
    };

    let mostRestrictive = "NORMAL";
    let highestLevel = 0;

    for (const mode of modes) {
      if (mode && hierarchy[mode] > highestLevel) {
        mostRestrictive = mode;
        highestLevel = hierarchy[mode];
      }
    }

    return mostRestrictive;
  }


  /**
   * Check if AI is allowed to trade
   */
  isAllowed() {
    return this.state.allowed && this.state.mode !== "OFF";
  }

  /**
   * Get current mode
   */
  getMode() {
    return this.state.mode;
  }

  /**
   * Get position multiplier
   */
  getPositionMultiplier() {
    return this.state.positionMultiplier;
  }

  /**
   * Get detailed status
   */
  getStatus() {
    return {
      allowed: this.state.allowed,
      mode: this.state.mode,
      positionMultiplier: this.state.positionMultiplier,
      factors: this.state.factors,
      rationale: this.state.rationale,
      timestamp: this.state.lastEvaluation,
    };
  }
}

module.exports = AIExecutionGovernor;
