/**
 * Risk Engine
 *
 * Evaluates every trade before submission.
 * Answers: "Should this trade happen at all?"
 *
 * CRITICAL: This is the final gate before execution.
 * A rejected trade never touches the broker.
 */

"use strict";

class RiskEngine {
  constructor(config = {}) {
    this.config = {
      maxPositionSize: config.maxPositionSize || 0.05,        // 5% of portfolio
      maxDailyDrawdown: config.maxDailyDrawdown || 0.02,       // 2% daily loss
      maxOpenPositions: config.maxOpenPositions || 10,
      maxOrderSize: config.maxOrderSize || 0.02,               // 2% NAV
      maxGrossExposure: config.maxGrossExposure || 1.0,        // 100%
      maxNetExposure: config.maxNetExposure || 0.75,           // 75%
      ...config
    };
  }

  /**
   * Evaluate trade for approval
   * Returns { approved: boolean, violations: [], riskScore: number }
   */
  evaluateTrade(tradeRequest, portfolio, positions, dailyStats) {
    const violations = [];
    let riskScore = 0;

    // 1. Position size validation
    const positionSizeViolation = this.checkMaxPositionSize(
      tradeRequest.quantity,
      tradeRequest.price,
      portfolio.nav
    );
    if (positionSizeViolation) {
      violations.push("MAX_POSITION_SIZE");
      riskScore += 0.3;
    }

    // 2. Daily drawdown validation
    const drawdownViolation = this.checkDailyDrawdown(dailyStats.pnl, portfolio.nav);
    if (drawdownViolation) {
      violations.push("DAILY_DRAWDOWN_LIMIT");
      riskScore += 0.3;
    }

    // 3. Open positions limit
    const positionCountViolation = this.checkOpenPositionCount(
      positions.length,
      tradeRequest.side
    );
    if (positionCountViolation) {
      violations.push("MAX_OPEN_POSITIONS");
      riskScore += 0.2;
    }

    // 4. Order size validation
    const orderSizeViolation = this.checkMaxOrderSize(
      tradeRequest.quantity,
      tradeRequest.price,
      portfolio.nav
    );
    if (orderSizeViolation) {
      violations.push("MAX_ORDER_SIZE");
      riskScore += 0.2;
    }

    // 5. Duplicate position check
    const duplicateViolation = this.checkDuplicatePosition(
      tradeRequest.ticker,
      positions
    );
    if (duplicateViolation) {
      violations.push("EXISTING_POSITION");
      riskScore += 0.15;
    }

    // 6. Liquidity check
    const liquidityViolation = this.checkLiquidity(
      tradeRequest.ticker,
      tradeRequest.quantity,
      tradeRequest.price
    );
    if (liquidityViolation) {
      violations.push("LIQUIDITY_WARNING");
      riskScore += 0.1;
    }

    return {
      approved: violations.length === 0,
      violations,
      riskScore: Math.min(riskScore, 1.0),
      rationale: this.generateRationale(violations),
    };
  }

  /**
   * Check if position size exceeds limit
   */
  checkMaxPositionSize(quantity, price, portfolioNav) {
    if (!portfolioNav || portfolioNav <= 0) {
      return true;  // Reject if NAV unknown
    }

    const positionValue = quantity * price;
    const positionPercent = positionValue / portfolioNav;

    return positionPercent > this.config.maxPositionSize;
  }

  /**
   * Check if daily drawdown exceeded
   */
  checkDailyDrawdown(dailyPnL, portfolioNav) {
    if (!portfolioNav || portfolioNav <= 0) {
      return false;  // Can't validate
    }

    const drawdownPercent = Math.abs(dailyPnL) / portfolioNav;
    return drawdownPercent > this.config.maxDailyDrawdown;
  }

  /**
   * Check if too many open positions
   */
  checkOpenPositionCount(currentCount, side) {
    // For simplicity, treat BUY/SELL separately in some cases
    // But for now, just check total
    return currentCount >= this.config.maxOpenPositions;
  }

  /**
   * Check if order size exceeds limit
   */
  checkMaxOrderSize(quantity, price, portfolioNav) {
    if (!portfolioNav || portfolioNav <= 0) {
      return true;
    }

    const orderValue = quantity * price;
    const orderPercent = orderValue / portfolioNav;

    return orderPercent > this.config.maxOrderSize;
  }

  /**
   * Check if position already exists
   */
  checkDuplicatePosition(ticker, positions) {
    return positions.some(p => p.ticker === ticker);
  }

  /**
   * Check liquidity (simplified)
   */
  checkLiquidity(ticker, quantity, price) {
    // This is a placeholder - real implementation would check:
    // - Bid-ask spread
    // - Average volume
    // - Impact cost

    // For now, flag very large orders
    const orderValue = quantity * price;
    return orderValue > 1000000;  // Flag if > $1M
  }

  /**
   * Generate human-readable explanation
   */
  generateRationale(violations) {
    const reasons = {
      MAX_POSITION_SIZE: "Position exceeds 5% of portfolio",
      DAILY_DRAWDOWN_LIMIT: "Daily loss limit (2%) already reached",
      MAX_OPEN_POSITIONS: "Maximum 10 concurrent positions exceeded",
      MAX_ORDER_SIZE: "Order exceeds 2% of portfolio NAV",
      EXISTING_POSITION: "Position already open in this ticker",
      LIQUIDITY_WARNING: "Order size may exceed reasonable liquidity",
    };

    return violations.map(v => reasons[v] || v).join("; ");
  }

  /**
   * Calculate aggregate risk score
   * Returns 0-1, where 0 = no risk, 1 = extreme risk
   */
  calculatePortfolioRiskScore(portfolio, positions, dailyStats) {
    let score = 0;

    // Position count risk
    const positionRatio = positions.length / this.config.maxOpenPositions;
    score += Math.min(positionRatio, 1.0) * 0.25;

    // Drawdown risk
    if (portfolio.nav > 0) {
      const drawdownRatio = Math.abs(dailyStats.pnl) / (portfolio.nav * this.config.maxDailyDrawdown);
      score += Math.min(drawdownRatio, 1.0) * 0.25;
    }

    // Concentration risk (largest position vs total)
    if (positions.length > 0) {
      const largestPosition = Math.max(...positions.map(p => Math.abs(p.value || 0)));
      const concentrationRatio = largestPosition / portfolio.nav;
      score += Math.min(concentrationRatio / this.config.maxPositionSize, 1.0) * 0.25;
    }

    // Win rate risk
    if (dailyStats.trades > 0) {
      const winRate = dailyStats.wins / dailyStats.trades;
      if (winRate < 0.4) {
        score += 0.25;  // Losing streak
      } else if (winRate > 0.7) {
        score -= 0.1;  // Winning streak (reduce risk)
      }
    }

    return Math.max(0, Math.min(score, 1.0));
  }

  /**
   * Get risk state name
   */
  getRiskStateName(riskScore) {
    if (riskScore < 0.2) return "NORMAL";
    if (riskScore < 0.5) return "ELEVATED";
    if (riskScore < 0.75) return "HIGH";
    return "CRITICAL";
  }
}

module.exports = RiskEngine;
