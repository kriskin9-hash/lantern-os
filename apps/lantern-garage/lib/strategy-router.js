/**
 * Strategy Router
 *
 * Selects which AI strategy is allowed to run based on market regime.
 * Different strategies work in different conditions.
 *
 * CRITICAL: Wrong strategy in wrong market = losses.
 * This layer ensures strategy-market alignment.
 */

"use strict";

class StrategyRouter {
  constructor(config = {}) {
    this.config = {
      ...config
    };

    // Define available strategies and their conditions
    this.strategies = {
      trend_following: {
        name: "Trend Following",
        description: "Follows established market trends",
        requiredVol: [0.15, 1.0],     // Optimal volatility range
        requiredTrend: 0.5,            // Min trend strength
        disabledIn: ["low_volatility", "ranging"],
        enabled: true,
      },
      mean_reversion: {
        name: "Mean Reversion",
        description: "Trades deviations from average",
        requiredVol: [0.05, 0.30],     // Lower volatility optimal
        requiredRange: 0.2,            // Min price deviation from mean
        disabledIn: ["high_volatility", "trending"],
        enabled: true,
      },
      volatility_breakout: {
        name: "Volatility Breakout",
        description: "Exploits volatility expansion",
        requiredVol: [0.25, 1.0],      // High volatility required
        requiredBreakout: true,        // Needs breakout signal
        disabledIn: ["low_volatility"],
        enabled: true,
      },
      news_momentum: {
        name: "News Momentum",
        description: "Trades on news-driven momentum",
        requiredVol: [0.10, 0.50],     // Moderate volatility
        requiredNews: true,            // News event required
        disabledIn: ["high_volatility"],
        enabled: true,
      },
      arbitrage: {
        name: "Statistical Arbitrage",
        description: "Exploits price inefficiencies",
        requiredVol: [0.05, 0.25],     // Low to moderate volatility
        disabledIn: ["high_volatility", "illiquid"],
        enabled: true,
      },
    };

    this.activeStrategies = new Set();
    this.marketRegime = null;
  }

  /**
   * Analyze market regime and select appropriate strategies
   */
  analyzeMarketAndRoute(marketData) {
    // Classify market regime
    this.marketRegime = this.classifyMarketRegime(marketData);

    // Reset active strategies
    this.activeStrategies.clear();

    // Enable strategies that match regime
    for (const [strategyId, strategy] of Object.entries(this.strategies)) {
      if (!strategy.enabled) {
        continue;  // Skip disabled strategies
      }

      const isDisabled = strategy.disabledIn.some(regime => regime === this.marketRegime);
      if (isDisabled) {
        continue;
      }

      // Check volatility requirements
      if (strategy.requiredVol) {
        const [minVol, maxVol] = strategy.requiredVol;
        if (marketData.volatility < minVol || marketData.volatility > maxVol) {
          continue;
        }
      }

      // Strategy passes all checks
      this.activeStrategies.add(strategyId);
    }

    return {
      regime: this.marketRegime,
      activeStrategies: Array.from(this.activeStrategies),
      details: this.getStrategyDetails(),
    };
  }

  /**
   * Classify market regime from data
   */
  classifyMarketRegime(marketData) {
    const volatility = marketData.volatility || 0;
    const trend = marketData.trendStrength || 0;
    const priceDeviation = marketData.deviationFromMean || 0;

    // High volatility regime
    if (volatility > 0.35) {
      return "high_volatility";
    }

    // Low volatility regime
    if (volatility < 0.10) {
      return "low_volatility";
    }

    // Strong trend regime
    if (trend > 0.6) {
      return "trending";
    }

    // Mean reverting regime
    if (priceDeviation > 0.2) {
      return "ranging";
    }

    // Default: moderate/balanced
    return "balanced";
  }

  /**
   * Check if strategy is allowed
   */
  isStrategyAllowed(strategyId) {
    return this.activeStrategies.has(strategyId);
  }

  /**
   * Get all allowed strategies
   */
  getAllowedStrategies() {
    return Array.from(this.activeStrategies);
  }

  /**
   * Get active strategy count
   */
  getActiveStrategyCount() {
    return this.activeStrategies.size;
  }

  /**
   * Recommend best strategy for current regime
   */
  recommendStrategy(marketData) {
    this.analyzeMarketAndRoute(marketData);

    if (this.activeStrategies.size === 0) {
      return {
        recommended: null,
        reason: "No strategies appropriate for current market regime",
        regime: this.marketRegime,
      };
    }

    if (this.activeStrategies.size === 1) {
      const strategyId = Array.from(this.activeStrategies)[0];
      return {
        recommended: strategyId,
        reason: `Only applicable strategy for ${this.marketRegime} regime`,
        regime: this.marketRegime,
      };
    }

    // Multiple strategies allowed - score them
    const scores = this.scoreStrategies(marketData);
    const sorted = Object.entries(scores)
      .filter(([id]) => this.activeStrategies.has(id))
      .sort((a, b) => b[1].score - a[1].score);

    if (sorted.length === 0) {
      return {
        recommended: null,
        reason: "No strategies scored",
        regime: this.marketRegime,
      };
    }

    return {
      recommended: sorted[0][0],
      score: sorted[0][1].score,
      reason: sorted[0][1].reason,
      regime: this.marketRegime,
      alternatives: sorted.slice(1).map(([id, data]) => ({
        strategy: id,
        score: data.score,
      })),
    };
  }

  /**
   * Score strategies for current conditions
   */
  scoreStrategies(marketData) {
    const scores = {};

    for (const [strategyId, strategy] of Object.entries(this.strategies)) {
      let score = 0;
      let reason = "";

      if (strategyId === "trend_following") {
        score = Math.min(marketData.trendStrength || 0, 1.0) * 100;
        reason = "Scored on trend strength";
      } else if (strategyId === "mean_reversion") {
        score = Math.min(marketData.deviationFromMean || 0, 0.5) * 200;
        reason = "Scored on price deviation from mean";
      } else if (strategyId === "volatility_breakout") {
        score = Math.min(marketData.volatility || 0, 1.0) * 100;
        reason = "Scored on volatility level";
      } else if (strategyId === "news_momentum") {
        score = (marketData.newsSignals || 0) * 100;
        reason = "Scored on news sentiment";
      } else if (strategyId === "arbitrage") {
        score = (marketData.pricingInefficiency || 0) * 100;
        reason = "Scored on pricing inefficiency";
      }

      scores[strategyId] = {
        score: Math.min(score, 100),
        reason,
      };
    }

    return scores;
  }

  /**
   * Get details for active strategies
   */
  getStrategyDetails() {
    const details = {};

    for (const strategyId of this.activeStrategies) {
      const strategy = this.strategies[strategyId];
      if (strategy) {
        details[strategyId] = {
          name: strategy.name,
          description: strategy.description,
        };
      }
    }

    return details;
  }

  /**
   * Get market regime assessment
   */
  getRegimeAssessment() {
    const assessments = {
      high_volatility: "Extreme price swings - breakout and volatility strategies preferred",
      low_volatility: "Calm market - mean reversion and arbitrage preferred",
      trending: "Strong directional movement - trend following preferred",
      ranging: "Price oscillation - mean reversion preferred",
      balanced: "Moderate conditions - most strategies viable",
    };

    return {
      regime: this.marketRegime,
      assessment: assessments[this.marketRegime] || "Unknown regime",
    };
  }

  /**
   * Disable strategy temporarily
   */
  disableStrategy(strategyId, reason) {
    if (this.strategies[strategyId]) {
      this.strategies[strategyId].enabled = false;
      console.log(`[StrategyRouter] Disabled ${strategyId}: ${reason}`);
      this.activeStrategies.delete(strategyId);
      return true;
    }
    return false;
  }

  /**
   * Re-enable strategy
   */
  enableStrategy(strategyId) {
    if (this.strategies[strategyId]) {
      this.strategies[strategyId].enabled = true;
      console.log(`[StrategyRouter] Re-enabled ${strategyId}`);
      return true;
    }
    return false;
  }

  /**
   * Get status report
   */
  getStatus() {
    return {
      regime: this.marketRegime,
      activeStrategies: Array.from(this.activeStrategies),
      strategyCount: this.activeStrategies.size,
      totalStrategies: Object.keys(this.strategies).length,
      strategies: this.getStrategyDetails(),
    };
  }
}

module.exports = StrategyRouter;
