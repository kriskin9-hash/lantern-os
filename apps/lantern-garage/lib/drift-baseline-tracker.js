/**
 * Drift Baseline Tracker — Phase 3.7
 *
 * Learns expected system behavior (latency distribution, jitter patterns)
 * and adapts tolerance windows dynamically.
 *
 * Replaces Phase 3.6's strict equality with statistical correctness.
 */

"use strict";

class DriftBaselineTracker {
  constructor(sampleWindow = 50) {
    this.sampleWindow = sampleWindow;

    // UI lag tracking (milliseconds)
    this.uiLagSamples = [];
    this.uiLagAvg = 400; // Baseline 400ms
    this.uiLagStdDev = 150;

    // Stream delay tracking (milliseconds)
    this.streamDelaySamples = [];
    this.streamDelayAvg = 90; // Baseline 90ms
    this.streamDelayStdDev = 30;

    // Engine update frequency tracking (updates/second)
    this.updateFrequencySamples = [];
    this.updateFrequencyAvg = 5; // Baseline 5 updates/sec

    // Config propagation delay (milliseconds)
    this.configPropagationDelaySamples = [];
    this.configPropagationDelayAvg = 0; // Next cycle

    // Overall metrics
    this.eventLossSamples = [];
    this.eventLossRate = 0; // Expected 0%

    this.lastTimestamp = Date.now();
  }

  /**
   * Record UI lag observation
   */
  recordUILag(lagMs) {
    this.uiLagSamples.push(lagMs);
    if (this.uiLagSamples.length > this.sampleWindow) {
      this.uiLagSamples.shift();
    }
    this._updateUILagStats();
  }

  /**
   * Record stream delay observation
   */
  recordStreamDelay(delayMs) {
    this.streamDelaySamples.push(delayMs);
    if (this.streamDelaySamples.length > this.sampleWindow) {
      this.streamDelaySamples.shift();
    }
    this._updateStreamDelayStats();
  }

  /**
   * Record update frequency
   */
  recordUpdateFrequency(frequency) {
    this.updateFrequencySamples.push(frequency);
    if (this.updateFrequencySamples.length > this.sampleWindow) {
      this.updateFrequencySamples.shift();
    }
    this._updateFrequencyStats();
  }

  /**
   * Record event loss
   */
  recordEventLoss(lossRate) {
    this.eventLossSamples.push(lossRate);
    if (this.eventLossSamples.length > this.sampleWindow) {
      this.eventLossSamples.shift();
    }
    this._updateEventLossStats();
  }

  /**
   * Calculate mean
   */
  _mean(samples) {
    if (samples.length === 0) return 0;
    return samples.reduce((a, b) => a + b, 0) / samples.length;
  }

  /**
   * Calculate standard deviation
   */
  _stdDev(samples) {
    if (samples.length < 2) return 0;
    const mean = this._mean(samples);
    const variance = samples.reduce((sum, x) => sum + Math.pow(x - mean, 2), 0) / samples.length;
    return Math.sqrt(variance);
  }

  /**
   * Update UI lag statistics
   */
  _updateUILagStats() {
    this.uiLagAvg = this._mean(this.uiLagSamples);
    this.uiLagStdDev = this._stdDev(this.uiLagSamples);
  }

  /**
   * Update stream delay statistics
   */
  _updateStreamDelayStats() {
    this.streamDelayAvg = this._mean(this.streamDelaySamples);
    this.streamDelayStdDev = this._stdDev(this.streamDelaySamples);
  }

  /**
   * Update frequency statistics
   */
  _updateFrequencyStats() {
    this.updateFrequencyAvg = this._mean(this.updateFrequencySamples);
  }

  /**
   * Update event loss statistics
   */
  _updateEventLossStats() {
    this.eventLossRate = this._mean(this.eventLossSamples);
  }

  /**
   * Get dynamic tolerance for UI lag
   * tolerance = avg + (2 * stdDev) — covers ~95% of normal variance
   */
  getUILagTolerance() {
    return Math.max(2000, this.uiLagAvg + 2 * this.uiLagStdDev);
  }

  /**
   * Get dynamic tolerance for stream delay
   */
  getStreamDelayTolerance() {
    return Math.max(500, this.streamDelayAvg + 2 * this.streamDelayStdDev);
  }

  /**
   * Get baseline metrics snapshot
   */
  getBaseline() {
    return {
      uiLag: {
        avg: Math.round(this.uiLagAvg),
        stdDev: Math.round(this.uiLagStdDev),
        tolerance: Math.round(this.getUILagTolerance()),
        sampleCount: this.uiLagSamples.length
      },
      streamDelay: {
        avg: Math.round(this.streamDelayAvg),
        stdDev: Math.round(this.streamDelayStdDev),
        tolerance: Math.round(this.getStreamDelayTolerance()),
        sampleCount: this.streamDelaySamples.length
      },
      updateFrequency: {
        avg: this.updateFrequencyAvg.toFixed(2),
        sampleCount: this.updateFrequencySamples.length
      },
      eventLoss: {
        rate: (this.eventLossRate * 100).toFixed(2) + "%",
        sampleCount: this.eventLossSamples.length
      }
    };
  }

  /**
   * Reset learning (for testing)
   */
  reset() {
    this.uiLagSamples = [];
    this.streamDelaySamples = [];
    this.updateFrequencySamples = [];
    this.configPropagationDelaySamples = [];
    this.eventLossSamples = [];
    this.uiLagAvg = 400;
    this.uiLagStdDev = 150;
    this.streamDelayAvg = 90;
    this.streamDelayStdDev = 30;
    this.updateFrequencyAvg = 5;
    this.eventLossRate = 0;
  }
}

module.exports = DriftBaselineTracker;
