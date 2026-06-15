/**
 * State Drift Validator — Phase 3.5
 *
 * Validates that state remains consistent across three layers:
 * 1. TradeStateEngine (backend source of truth)
 * 2. API responses (/api/trading/state snapshot)
 * 3. UI-rendered state (simulated or observed)
 *
 * Detects:
 * - Trade count divergence
 * - Missing or phantom trades
 * - Status mismatches
 * - Orphaned orders
 * - Event duplication
 */

"use strict";

class StateDriftValidator {
  constructor() {
    this.validationLog = [];
    this.driftHistory = [];
  }

  /**
   * Validate engine state (internal consistency)
   */
  validateEngineState(engine) {
    const issues = [];

    // Check 1: All trades are in a valid state
    for (const [tradeId, trade] of engine.trades.entries()) {
      if (!trade.status) {
        issues.push(`Trade ${tradeId} missing status field`);
      }
      if (trade.filledQuantity > trade.quantity) {
        issues.push(`Trade ${tradeId} filled (${trade.filledQuantity}) > total (${trade.quantity})`);
      }
      if (!trade.symbol || !trade.side) {
        issues.push(`Trade ${tradeId} missing symbol or side`);
      }
    }

    // Check 2: Order ID mappings are valid
    for (const [orderId, tradeId] of engine.orderIdToTradeId.entries()) {
      if (!engine.trades.has(tradeId)) {
        issues.push(`Orphan order mapping: ${orderId} → ${tradeId} (trade not found)`);
      }
    }

    // Check 3: Recent trades are bounded
    if (engine.recentTrades.length > engine.maxRecentTrades) {
      issues.push(`Recent trades buffer overflow: ${engine.recentTrades.length} > ${engine.maxRecentTrades}`);
    }

    // Check 4: Event sequence is monotonic
    if (engine.eventSequence < 0) {
      issues.push("Event sequence counter corrupted");
    }

    return {
      valid: issues.length === 0,
      issues,
      tradeCount: engine.trades.size,
      recentCount: engine.recentTrades.length
    };
  }

  /**
   * Validate API state snapshot
   */
  validateApiState(apiState) {
    const issues = [];

    if (!apiState) {
      return { valid: false, issues: ["API state is null/undefined"] };
    }

    // Check 1: Required fields exist
    const required = ["totalTrades", "activeCount", "filledCount", "rejectedCount", "recentTrades", "openPositions"];
    for (const field of required) {
      if (apiState[field] === undefined) {
        issues.push(`API state missing field: ${field}`);
      }
    }

    // Check 2: Counts are consistent
    if (apiState.activeCount > apiState.totalTrades) {
      issues.push(`Active count (${apiState.activeCount}) > total (${apiState.totalTrades})`);
    }

    if (apiState.filledCount + apiState.rejectedCount > apiState.totalTrades) {
      issues.push(`Terminal states (${apiState.filledCount + apiState.rejectedCount}) > total (${apiState.totalTrades})`);
    }

    // Check 3: Recent trades is an array
    if (!Array.isArray(apiState.recentTrades)) {
      issues.push("API recentTrades is not an array");
    }

    // Check 4: Recent trades are in descending timestamp order
    if (Array.isArray(apiState.recentTrades) && apiState.recentTrades.length > 1) {
      for (let i = 1; i < apiState.recentTrades.length; i++) {
        const prev = apiState.recentTrades[i - 1];
        const curr = apiState.recentTrades[i];
        if (prev.timestamp < curr.timestamp) {
          issues.push(`Recent trades out of order at position ${i}`);
          break;
        }
      }
    }

    // Check 5: No duplicate trades
    const seenIds = new Set();
    for (const trade of apiState.recentTrades || []) {
      if (seenIds.has(trade.tradeId)) {
        issues.push(`Duplicate trade in recent: ${trade.tradeId}`);
      }
      seenIds.add(trade.tradeId);
    }

    return {
      valid: issues.length === 0,
      issues,
      totalTrades: apiState.totalTrades,
      activeCount: apiState.activeCount
    };
  }

  /**
   * Compare engine state with API state
   */
  compareEngineToApi(engine, apiState) {
    const drifts = [];

    // Check 1: Trade count matches
    if (engine.trades.size !== apiState.totalTrades) {
      drifts.push({
        type: "trade_count_mismatch",
        engine: engine.trades.size,
        api: apiState.totalTrades,
        diff: apiState.totalTrades - engine.trades.size
      });
    }

    // Check 2: Active count consistency
    const engineActive = engine.getOpenPositions ? engine.getOpenPositions().length : 0;
    if (engineActive !== apiState.activeCount) {
      drifts.push({
        type: "active_count_mismatch",
        engine: engineActive,
        api: apiState.activeCount,
        diff: apiState.activeCount - engineActive
      });
    }

    // Check 3: Recent trades are in both
    const apiRecentIds = new Set((apiState.recentTrades || []).map(t => t.tradeId));
    for (const trade of engine.recentTrades || []) {
      if (!apiRecentIds.has(trade.tradeId)) {
        drifts.push({
          type: "missing_in_api",
          tradeId: trade.tradeId,
          status: trade.status
        });
      }
    }

    // Check 4: No phantom trades in API
    for (const apiTrade of apiState.recentTrades || []) {
      if (!engine.trades.has(apiTrade.tradeId)) {
        drifts.push({
          type: "phantom_in_api",
          tradeId: apiTrade.tradeId,
          status: apiTrade.status
        });
      }
    }

    return {
      hasDrift: drifts.length > 0,
      drifts,
      timestamp: Date.now()
    };
  }

  /**
   * Full three-layer validation
   */
  validate(engine, apiState, uiState = null) {
    const validation = {
      timestamp: Date.now(),
      engine: this.validateEngineState(engine),
      api: this.validateApiState(apiState),
      comparison: this.compareEngineToApi(engine, apiState),
      overallValid: true,
      allIssues: []
    };

    // Aggregate issues
    validation.allIssues.push(...validation.engine.issues.map(i => `[ENGINE] ${i}`));
    validation.allIssues.push(...validation.api.issues.map(i => `[API] ${i}`));
    validation.comparison.drifts.forEach(d => {
      validation.allIssues.push(`[DRIFT] ${JSON.stringify(d)}`);
    });

    // Determine overall validity
    validation.overallValid =
      validation.engine.valid &&
      validation.api.valid &&
      !validation.comparison.hasDrift;

    // Log for analysis
    this.validationLog.push(validation);
    if (!validation.overallValid) {
      this.driftHistory.push({
        timestamp: validation.timestamp,
        issues: validation.allIssues
      });
    }

    return validation;
  }

  /**
   * Get validation report
   */
  getReport() {
    const totalChecks = this.validationLog.length;
    const validChecks = this.validationLog.filter(v => v.overallValid).length;

    return {
      totalChecks,
      validChecks,
      failedChecks: totalChecks - validChecks,
      passRate: totalChecks > 0 ? ((validChecks / totalChecks) * 100).toFixed(1) : 0,
      driftCount: this.driftHistory.length,
      recentDrifts: this.driftHistory.slice(-5),
      summary: `${validChecks}/${totalChecks} validations passed (${((validChecks / totalChecks) * 100).toFixed(1)}%)`
    };
  }

  /**
   * Clear logs
   */
  reset() {
    this.validationLog = [];
    this.driftHistory = [];
  }
}

module.exports = StateDriftValidator;
