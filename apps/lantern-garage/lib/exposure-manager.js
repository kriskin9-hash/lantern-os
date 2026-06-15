/**
 * Exposure Manager
 *
 * Tracks and validates portfolio exposure metrics.
 * Prevents excessive risk concentration.
 */

"use strict";

class ExposureManager {
  constructor(config = {}) {
    this.config = {
      maxGrossExposure: config.maxGrossExposure || 1.0,  // 100%
      maxNetExposure: config.maxNetExposure || 0.75,     // 75%
      ...config
    };
  }

  /**
   * Calculate all exposure metrics from positions
   */
  calculateExposure(positions, portfolioNav) {
    if (!portfolioNav || portfolioNav <= 0) {
      return this.getZeroExposure();
    }

    let longValue = 0;
    let shortValue = 0;
    const positionValues = {};

    // Calculate per-position exposure
    for (const position of positions) {
      const value = position.quantity * position.currentPrice;
      positionValues[position.ticker] = value;

      if (position.side === "BUY") {
        longValue += value;
      } else if (position.side === "SELL") {
        shortValue += value;
      }
    }

    const grossExposure = (longValue + shortValue) / portfolioNav;
    const netExposure = Math.abs(longValue - shortValue) / portfolioNav;

    return {
      longExposure: longValue / portfolioNav,
      shortExposure: shortValue / portfolioNav,
      grossExposure,
      netExposure,
      positionValues,
      positionCount: positions.length,
      longCount: positions.filter(p => p.side === "BUY").length,
      shortCount: positions.filter(p => p.side === "SELL").length,
    };
  }

  /**
   * Check if exposure would be exceeded
   */
  validateExposure(exposure) {
    const violations = [];

    if (exposure.grossExposure > this.config.maxGrossExposure) {
      violations.push({
        type: "GROSS_EXPOSURE_EXCEEDED",
        current: exposure.grossExposure,
        limit: this.config.maxGrossExposure,
        excess: exposure.grossExposure - this.config.maxGrossExposure,
      });
    }

    if (exposure.netExposure > this.config.maxNetExposure) {
      violations.push({
        type: "NET_EXPOSURE_EXCEEDED",
        current: exposure.netExposure,
        limit: this.config.maxNetExposure,
        excess: exposure.netExposure - this.config.maxNetExposure,
      });
    }

    return {
      valid: violations.length === 0,
      violations,
    };
  }

  /**
   * Check if new trade would exceed exposure limits
   */
  checkTradeImpact(newTrade, currentExposure, portfolioNav) {
    if (!portfolioNav || portfolioNav <= 0) {
      return { wouldViolate: true, reason: "Portfolio NAV unknown" };
    }

    const tradeValue = newTrade.quantity * newTrade.price;
    const tradePercent = tradeValue / portfolioNav;

    let newGrossExposure = currentExposure.grossExposure;
    let newNetExposure = currentExposure.netExposure;

    if (newTrade.side === "BUY") {
      newGrossExposure += tradePercent;
      newNetExposure = Math.abs(
        (currentExposure.longExposure + tradePercent) - currentExposure.shortExposure
      );
    } else if (newTrade.side === "SELL") {
      newGrossExposure += tradePercent;
      newNetExposure = Math.abs(
        currentExposure.longExposure - (currentExposure.shortExposure + tradePercent)
      );
    }

    const violations = [];

    if (newGrossExposure > this.config.maxGrossExposure) {
      violations.push("WOULD_EXCEED_GROSS_EXPOSURE");
    }

    if (newNetExposure > this.config.maxNetExposure) {
      violations.push("WOULD_EXCEED_NET_EXPOSURE");
    }

    return {
      wouldViolate: violations.length > 0,
      violations,
      projectedGrossExposure: newGrossExposure,
      projectedNetExposure: newNetExposure,
    };
  }

  /**
   * Get detailed exposure report
   */
  getExposureReport(positions, portfolioNav) {
    const exposure = this.calculateExposure(positions, portfolioNav);
    const validation = this.validateExposure(exposure);

    return {
      timestamp: new Date().toISOString(),
      exposure,
      validation,
      status: validation.valid ? "OK" : "VIOLATION",
      summary: {
        totalPositions: positions.length,
        longPositions: exposure.longCount,
        shortPositions: exposure.shortCount,
        grossExposurePercent: (exposure.grossExposure * 100).toFixed(1),
        netExposurePercent: (exposure.netExposure * 100).toFixed(1),
      },
    };
  }

  /**
   * Calculate concentration risk
   */
  calculateConcentration(positions, portfolioNav) {
    if (positions.length === 0) {
      return { herfindahlIndex: 0, maxPositionPercent: 0 };
    }

    let herfindahlSum = 0;
    let maxPosition = 0;

    for (const position of positions) {
      const posValue = Math.abs(position.quantity * position.currentPrice);
      const posPercent = posValue / portfolioNav;
      herfindahlSum += posPercent * posPercent;
      maxPosition = Math.max(maxPosition, posPercent);
    }

    // Herfindahl index: 0 = perfect diversification, 1 = all in one
    const herfindahlIndex = herfindahlSum;

    return {
      herfindahlIndex,
      maxPositionPercent: maxPosition,
      concentrated: herfindahlIndex > 0.15,  // Threshold
    };
  }

  /**
   * Suggest position reductions if needed
   */
  suggestReductions(positions, portfolioNav, targetExposure = 0.8) {
    const exposure = this.calculateExposure(positions, portfolioNav);

    if (exposure.grossExposure <= targetExposure) {
      return { needed: false, suggestions: [] };
    }

    const reductionNeeded = exposure.grossExposure - targetExposure;
    const suggestedReductions = [];

    // Sort by value, largest first
    const sortedPositions = [...positions].sort(
      (a, b) => Math.abs(b.quantity * b.currentPrice) - Math.abs(a.quantity * a.currentPrice)
    );

    let reductionAccumulated = 0;
    for (const position of sortedPositions) {
      const posValue = position.quantity * position.currentPrice;
      const posPercent = Math.abs(posValue) / portfolioNav;

      if (reductionAccumulated >= reductionNeeded) break;

      suggestedReductions.push({
        ticker: position.ticker,
        side: position.side,
        currentQuantity: position.quantity,
        currentValue: posValue,
        percentOfPortfolio: (posPercent * 100).toFixed(1),
        suggestion: `Reduce ${position.ticker} position`,
      });

      reductionAccumulated += posPercent;
    }

    return {
      needed: true,
      reductionPercentNeeded: (reductionNeeded * 100).toFixed(1),
      suggestions: suggestedReductions,
    };
  }

  getZeroExposure() {
    return {
      longExposure: 0,
      shortExposure: 0,
      grossExposure: 0,
      netExposure: 0,
      positionValues: {},
      positionCount: 0,
      longCount: 0,
      shortCount: 0,
    };
  }
}

module.exports = ExposureManager;
