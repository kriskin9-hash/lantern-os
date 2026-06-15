/**
 * Drift Reconciliation Engine — Phase 3.7
 *
 * Automatically reconciles system state within tolerance windows.
 * Does NOT modify engine state (engine is always source of truth).
 * Instead, resolves UI lag, stream gaps, and config mismatches.
 *
 * Replaces strict validation with pragmatic self-correction.
 */

"use strict";

const crypto = require("crypto");

class DriftReconciliationEngine {
  constructor(baseline) {
    this.baseline = baseline;
    this.reconciliationLog = [];
    this.successCount = 0;
    this.failureCount = 0;

    // State snapshots for reconciliation
    this.engineStateSnapshot = null;
    this.uiStateSnapshot = null;
    this.lastStreamEventId = null;

    // Drift buffer (rolling window for tolerance)
    this.driftBuffer = [];
    this.bufferWindow = 5000; // 5 seconds
  }

  /**
   * Reconcile UI lag — re-sync missing UI updates from engine snapshot
   */
  reconcileUILag(engine, uiState, observedLagMs) {
    const actions = [];

    // Check 1: Is lag within tolerance?
    const tolerance = this.baseline.getUILagTolerance();
    if (observedLagMs <= tolerance) {
      return { status: "ok", actions: [] };
    }

    // Check 2: Can we detect what UI is missing?
    const engineTrades = Array.from(engine.trades.values());
    const uiTradeIds = new Set((uiState.displayedTrades || []).map(t => t.id));

    const missingInUI = [];
    for (const trade of engineTrades) {
      if (!uiTradeIds.has(trade.tradeId) && trade.timestamp > Date.now() - tolerance) {
        missingInUI.push(trade.tradeId);
      }
    }

    if (missingInUI.length > 0) {
      actions.push({
        type: "ui_resync",
        reason: `UI lag ${observedLagMs}ms > tolerance ${tolerance}ms`,
        missingTrades: missingInUI.length,
        action: "refresh_ui_state_from_engine_snapshot"
      });
      this.successCount++;
      return { status: "reconciled", actions };
    }

    // Check 3: If no missing trades but lag is high, it's just display latency
    // This is normal and doesn't require action
    return { status: "transient_lag", actions: [] };
  }

  /**
   * Reconcile stream — re-emit last known engine event if missing
   */
  reconcileStreamGap(engine, streamBuffer, observedDelayMs) {
    const actions = [];

    // Check 1: Is delay within tolerance?
    const tolerance = this.baseline.getStreamDelayTolerance();
    if (observedDelayMs <= tolerance) {
      return { status: "ok", actions: [] };
    }

    // Check 2: Are we missing events?
    const lastStreamEvent = streamBuffer[streamBuffer.length - 1];
    if (!lastStreamEvent) {
      return { status: "no_stream_history", actions: [] };
    }

    // Check 3: Can we reconstruct missing updates?
    const timeSinceLastEvent = Date.now() - lastStreamEvent.recordedAt;
    if (timeSinceLastEvent > tolerance) {
      // Likely a batch of updates are stuck
      const engineState = engine.getState();

      actions.push({
        type: "stream_resync",
        reason: `Stream delay ${observedDelayMs}ms > tolerance ${tolerance}ms`,
        lastEventAge: timeSinceLastEvent,
        action: "emit_current_engine_state_snapshot",
        snapshot: {
          totalTrades: engineState.totalTrades,
          activeCount: engineState.activeCount,
          filledCount: engineState.filledCount
        }
      });
      this.successCount++;
      return { status: "reconciled", actions };
    }

    return { status: "transient_delay", actions: [] };
  }

  /**
   * Reconcile config mismatch — validate snapshot vs engine
   */
  reconcileConfigMismatch(engine, config, configTickers) {
    const actions = [];

    // Get current engine tickers
    const engineTickers = Array.from(new Set(
      Array.from(engine.trades.values()).map(t => t.symbol).filter(Boolean)
    ));

    // Check 1: Are all engine tickers in config?
    const extraTickers = engineTickers.filter(t => !configTickers.includes(t));
    if (extraTickers.length > 0) {
      actions.push({
        type: "config_mismatch",
        reason: `Engine has ${extraTickers.length} tickers not in config`,
        extraTickers,
        action: "log_for_next_config_cycle" // Don't fix, just note
      });
    }

    // Check 2: Are config tickers represented in engine?
    const missingFromEngine = configTickers.filter(t => !engineTickers.includes(t));
    if (missingFromEngine.length > 0) {
      // This is expected — not all watchlist symbols are traded yet
      // Don't flag as error
    }

    if (actions.length > 0) {
      this.successCount++;
      return { status: "noted", actions };
    }

    return { status: "ok", actions: [] };
  }

  /**
   * Reconcile event loss — detect missing events in stream
   */
  reconcileEventLoss(engine, streamBuffer, expectedEventCount) {
    const actions = [];

    if (!streamBuffer || streamBuffer.length === 0) {
      return { status: "no_stream_history", actions: [] };
    }

    // Check 1: Calculate expected vs observed events
    const observedCount = streamBuffer.length;
    const lossRate = Math.max(0, 1 - (observedCount / expectedEventCount));

    // Record loss
    if (this.baseline) {
      this.baseline.recordEventLoss(lossRate);
    }

    // Check 2: Is loss within acceptable range (< 5%)?
    if (lossRate > 0.05) {
      actions.push({
        type: "event_loss_detected",
        reason: `Lost ${(lossRate * 100).toFixed(1)}% of events`,
        expected: expectedEventCount,
        observed: observedCount,
        severity: lossRate > 0.2 ? "high" : "medium",
        action: "verify_stream_health"
      });
      this.failureCount++;
      return { status: "warning", actions };
    }

    return { status: "ok", actions: [] };
  }

  /**
   * Full reconciliation cycle
   */
  reconcile(engine, uiState, streamBuffer, config) {
    const reconciliation = {
      timestamp: Date.now(),
      checks: [],
      actions: [],
      status: "ok",
      successCount: this.successCount,
      failureCount: this.failureCount
    };

    // Get current state
    const engineState = engine.getState();
    const engineTickers = Array.from(new Set(
      Array.from(engine.trades.values()).map(t => t.symbol).filter(Boolean)
    ));

    // Measurement 1: Calculate observed UI lag
    const uiLag = uiState.timestamp ? Date.now() - uiState.timestamp : 0;
    const uiReconciliation = this.reconcileUILag(engine, uiState, uiLag);
    reconciliation.checks.push({
      type: "ui_lag",
      observed: uiLag,
      tolerance: this.baseline.getUILagTolerance(),
      result: uiReconciliation
    });

    // Measurement 2: Calculate observed stream delay
    const streamDelay = streamBuffer.length > 0
      ? Date.now() - streamBuffer[streamBuffer.length - 1].recordedAt
      : 0;
    const streamReconciliation = this.reconcileStreamGap(engine, streamBuffer, streamDelay);
    reconciliation.checks.push({
      type: "stream_delay",
      observed: streamDelay,
      tolerance: this.baseline.getStreamDelayTolerance(),
      result: streamReconciliation
    });

    // Measurement 3: Check config alignment
    const configTickers = config?.watchlist || [];
    const configReconciliation = this.reconcileConfigMismatch(engine, config, configTickers);
    reconciliation.checks.push({
      type: "config_alignment",
      result: configReconciliation
    });

    // Measurement 4: Check event loss
    const expectedEvents = engineState.totalTrades * 2; // Rough estimate
    const eventLossReconciliation = this.reconcileEventLoss(engine, streamBuffer, expectedEvents);
    reconciliation.checks.push({
      type: "event_loss",
      result: eventLossReconciliation
    });

    // Aggregate actions
    reconciliation.checks.forEach(check => {
      reconciliation.actions.push(...(check.result.actions || []));
    });

    // Determine overall status
    const warnings = reconciliation.checks.filter(c => c.result.status === "warning" || c.result.status === "critical");
    if (warnings.length > 2) {
      reconciliation.status = "warning";
    } else if (warnings.length > 0) {
      reconciliation.status = "degraded";
    }

    this.reconciliationLog.push(reconciliation);
    if (this.reconciliationLog.length > 1000) {
      this.reconciliationLog.shift();
    }

    return reconciliation;
  }

  /**
   * Get reconciliation report
   */
  getReport() {
    const totalCycles = this.reconciliationLog.length;
    const successCycles = this.reconciliationLog.filter(r => r.status === "ok").length;

    return {
      totalReconciliationCycles: totalCycles,
      successfulCycles: successCycles,
      successRate: totalCycles > 0 ? ((successCycles / totalCycles) * 100).toFixed(1) : 0,
      totalActionsNeeded: this.reconciliationLog.reduce((sum, r) => sum + r.actions.length, 0),
      systemHealthy: this.failureCount === 0,
      lastReconciliation: this.reconciliationLog[this.reconciliationLog.length - 1] || null
    };
  }

  /**
   * Reset for testing
   */
  reset() {
    this.reconciliationLog = [];
    this.successCount = 0;
    this.failureCount = 0;
    this.driftBuffer = [];
  }
}

module.exports = DriftReconciliationEngine;
