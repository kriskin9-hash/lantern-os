/**
 * System Stability Index — Phase 3.7
 *
 * Computes holistic system health score combining:
 * - drift frequency
 * - reconciliation success rate
 * - lag variance
 * - event loss rate
 *
 * Single metric for "is the system healthy?" without false alarms.
 */

"use strict";

class SystemStabilityIndex {
  constructor() {
    this.measurements = [];
    this.maxMeasurements = 300; // 5 minutes at 1Hz
    this.lastIndex = 1.0; // Perfect start
  }

  /**
   * Record system measurement
   */
  record(measurement) {
    this.measurements.push({
      timestamp: Date.now(),
      ...measurement
    });

    if (this.measurements.length > this.maxMeasurements) {
      this.measurements.shift();
    }
  }

  /**
   * Calculate stability index (0.0 to 1.0)
   */
  calculate() {
    if (this.measurements.length === 0) {
      return 1.0; // Perfect when no data
    }

    const recent = this.measurements.slice(-60); // Last minute
    if (recent.length === 0) return 1.0;

    // Score 1: Drift frequency
    const driftFrequency = recent.filter(m => m.hasDrift).length / recent.length;
    const driftScore = Math.max(0, 1 - driftFrequency);

    // Score 2: Reconciliation success rate
    const reconciliationScores = recent
      .filter(m => m.reconciliationSuccessRate !== undefined)
      .map(m => m.reconciliationSuccessRate);
    const reconciliationScore = reconciliationScores.length > 0
      ? reconciliationScores.reduce((a, b) => a + b) / reconciliationScores.length
      : 1.0;

    // Score 3: Lag variance (lower is better)
    const lagValues = recent
      .filter(m => m.uiLag !== undefined)
      .map(m => m.uiLag);
    let lagScore = 1.0;
    if (lagValues.length > 1) {
      const mean = lagValues.reduce((a, b) => a + b) / lagValues.length;
      const variance = lagValues.reduce((sum, x) => sum + Math.pow(x - mean, 2), 0) / lagValues.length;
      const stdDev = Math.sqrt(variance);
      // Normalize: high variance = low score
      // At 500ms stdDev, score = 0.5
      lagScore = Math.max(0, 1 - (stdDev / 500));
    }

    // Score 4: Event loss rate
    const eventLosses = recent
      .filter(m => m.eventLossRate !== undefined)
      .map(m => m.eventLossRate);
    let eventLossScore = 1.0;
    if (eventLosses.length > 0) {
      const avgLoss = eventLosses.reduce((a, b) => a + b) / eventLosses.length;
      // At 5% loss, score = 0.5
      eventLossScore = Math.max(0, 1 - (avgLoss / 0.05));
    }

    // Score 5: Critical failure count
    const criticalCount = recent.filter(m => m.criticalIssues > 0).length;
    const criticalScore = Math.max(0, 1 - (criticalCount / recent.length));

    // Weighted average
    const weights = {
      drift: 0.25,
      reconciliation: 0.25,
      lag: 0.20,
      eventLoss: 0.15,
      critical: 0.15
    };

    const index = (
      driftScore * weights.drift +
      reconciliationScore * weights.reconciliation +
      lagScore * weights.lag +
      eventLossScore * weights.eventLoss +
      criticalScore * weights.critical
    );

    this.lastIndex = index;
    return Math.max(0, Math.min(1, index)); // Clamp to [0, 1]
  }

  /**
   * Get health classification
   */
  getHealthStatus() {
    const index = this.lastIndex;

    if (index >= 0.9) return "excellent";
    if (index >= 0.8) return "healthy";
    if (index >= 0.7) return "stable";
    if (index >= 0.5) return "degraded";
    if (index >= 0.3) return "unstable";
    return "critical";
  }

  /**
   * Get stability report
   */
  getReport() {
    const index = this.calculate();

    return {
      stabilityIndex: index.toFixed(3),
      status: this.getHealthStatus(),
      confidence: this._getConfidence(index),
      message: this._getMessage(index),
      sampleCount: this.measurements.length,
      trend: this._getTrend(),
      timestamp: Date.now()
    };
  }

  /**
   * Get confidence level
   */
  _getConfidence(index) {
    if (this.measurements.length < 10) return "low";
    if (this.measurements.length < 60) return "medium";
    return "high";
  }

  /**
   * Get human-readable message
   */
  _getMessage(index) {
    if (index >= 0.9) return "System operating excellently";
    if (index >= 0.8) return "System is healthy";
    if (index >= 0.7) return "System is stable";
    if (index >= 0.5) return "System experiencing degradation";
    if (index >= 0.3) return "System is unstable — investigate";
    return "System is critical — immediate action required";
  }

  /**
   * Get trend (improving, stable, declining)
   */
  _getTrend() {
    if (this.measurements.length < 20) return "insufficient_data";

    const recent = this.measurements.slice(-10);
    const older = this.measurements.slice(-20, -10);

    const recentAvg = recent.filter(m => m.stabilityScore !== undefined).length > 0
      ? recent.reduce((sum, m) => sum + (m.stabilityScore || 0), 0) / recent.length
      : this.lastIndex;

    const olderAvg = older.filter(m => m.stabilityScore !== undefined).length > 0
      ? older.reduce((sum, m) => sum + (m.stabilityScore || 0), 0) / older.length
      : this.lastIndex;

    const diff = recentAvg - olderAvg;
    if (Math.abs(diff) < 0.05) return "stable";
    if (diff > 0) return "improving";
    return "declining";
  }

  /**
   * Can AI trade safely with current stability?
   */
  canExecuteTrades(minThreshold = 0.8) {
    const index = this.lastIndex;
    return {
      canExecute: index >= minThreshold,
      index: index.toFixed(3),
      threshold: minThreshold.toFixed(2),
      gap: (index - minThreshold).toFixed(3)
    };
  }

  /**
   * Reset
   */
  reset() {
    this.measurements = [];
    this.lastIndex = 1.0;
  }
}

module.exports = SystemStabilityIndex;
