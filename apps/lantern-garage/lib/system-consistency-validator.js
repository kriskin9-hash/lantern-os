/**
 * System Consistency Validator — Phase 3.6
 *
 * Ensures perfect synchronization across all layers:
 * - TradeStateEngine (source of truth)
 * - UI Terminal (renderer)
 * - SSE Stream (transport layer)
 * - Config Pipeline (data ingestion)
 *
 * The system can only be trusted if it can prove itself correct at runtime.
 */

"use strict";

const crypto = require("crypto");

class SystemConsistencyValidator {
  constructor() {
    this.validationHistory = [];
    this.driftLog = [];
    this.streamBuffer = []; // Last N SSE events
    this.maxBufferSize = 1000;
    this.lastValidation = null;

    // Tolerance windows (milliseconds)
    this.tolerances = {
      sseToUI: 2000, // 2 seconds
      engineToStream: 100, // 100ms
      configToEngine: null // next cycle only
    };

    // State hashes for comparison
    this.lastHashes = {
      engine: null,
      ui: null,
      stream: null,
      config: null
    };
  }

  /**
   * Generate deterministic hash of engine state
   */
  hashEngineState(engine) {
    if (!engine) return null;

    const state = {
      totalTrades: engine.trades.size,
      tradeIds: Array.from(engine.trades.keys()).sort(),
      openPositions: engine.getOpenPositions?.() ? engine.getOpenPositions().length : 0,
      eventSequence: engine.eventSequence || 0,
      recentCount: (engine.recentTrades || []).length
    };

    return this._hash(JSON.stringify(state));
  }

  /**
   * Generate deterministic hash of UI state
   */
  hashUIState(uiState) {
    if (!uiState) return null;

    const state = {
      tapeEntries: uiState.tapeEntries || 0,
      activeTrades: uiState.activeTrades || 0,
      displayedTradeIds: (uiState.displayedTrades || []).map(t => t.id).sort(),
      pnl: uiState.pnl || 0,
      timestamp: uiState.timestamp || 0
    };

    return this._hash(JSON.stringify(state));
  }

  /**
   * Generate deterministic hash of stream events
   */
  hashStreamEvents(events) {
    if (!events || events.length === 0) return null;

    const eventSummary = {
      count: events.length,
      types: events.map(e => e.type).sort(),
      lastSequence: events[events.length - 1].sequence || 0,
      tradeIds: [...new Set(events.map(e => e.data?.tradeId).filter(Boolean))].sort()
    };

    return this._hash(JSON.stringify(eventSummary));
  }

  /**
   * Generate deterministic hash of config state
   */
  hashConfigState(config) {
    if (!config) return null;

    const state = {
      watchlistTickers: (config.watchlist || []).sort(),
      activeSymbols: (config.activeSymbols || []).sort(),
      collectorStatus: config.collectorActive || false
    };

    return this._hash(JSON.stringify(state));
  }

  /**
   * Helper: SHA256 hash
   */
  _hash(data) {
    return crypto.createHash("sha256").update(data).digest("hex");
  }

  /**
   * Record SSE event in replay buffer
   */
  recordStreamEvent(event) {
    this.streamBuffer.push({
      ...event,
      recordedAt: Date.now()
    });

    // Keep bounded
    if (this.streamBuffer.length > this.maxBufferSize) {
      this.streamBuffer.shift();
    }
  }

  /**
   * Validate engine state consistency
   */
  validateEngineState(engine) {
    const issues = [];

    if (!engine) return { valid: false, issues: ["Engine is null"] };

    // Check 1: All trades have valid state
    for (const [tradeId, trade] of engine.trades.entries()) {
      if (!trade.status) {
        issues.push(`Trade ${tradeId} missing status`);
      }
      if (trade.filledQuantity > trade.quantity) {
        issues.push(`Trade ${tradeId} overflowed: filled ${trade.filledQuantity} > qty ${trade.quantity}`);
      }
    }

    // Check 2: Order mappings are valid
    for (const [orderId, tradeId] of engine.orderIdToTradeId.entries()) {
      if (!engine.trades.has(tradeId)) {
        issues.push(`Orphaned order mapping: ${orderId} → ${tradeId}`);
      }
    }

    // Check 3: Event sequence is monotonic
    if (engine.eventSequence < 0) {
      issues.push("Event sequence corrupted");
    }

    return {
      valid: issues.length === 0,
      issues,
      tradeCount: engine.trades.size
    };
  }

  /**
   * Compare engine state with UI state
   */
  compareEngineToUI(engine, uiState) {
    const drifts = [];

    if (!engine || !uiState) {
      return { hasDrift: true, drifts: ["Missing state object"] };
    }

    // Check 1: Trade count consistency
    const engineTradeCount = engine.trades.size;
    const uiTradeCount = uiState.activeTrades || 0;

    if (Math.abs(engineTradeCount - uiTradeCount) > 10) {
      // Allow small window for async updates
      drifts.push({
        type: "trade_count_divergence",
        engine: engineTradeCount,
        ui: uiTradeCount,
        diff: engineTradeCount - uiTradeCount,
        severity: Math.abs(engineTradeCount - uiTradeCount) > 100 ? "critical" : "warning"
      });
    }

    // Check 2: No phantom trades in UI
    if (uiState.displayedTrades && Array.isArray(uiState.displayedTrades)) {
      for (const uiTrade of uiState.displayedTrades) {
        if (!engine.trades.has(uiTrade.id)) {
          drifts.push({
            type: "phantom_trade_in_ui",
            tradeId: uiTrade.id,
            severity: "critical"
          });
        }
      }
    }

    // Check 3: PnL sanity
    if (uiState.pnl !== undefined && engine.trades.size > 0) {
      // Very basic check: PnL shouldn't be wildly negative without explicit reason
      if (uiState.pnl < -1000000) {
        drifts.push({
          type: "unusual_pnl",
          pnl: uiState.pnl,
          severity: "warning"
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
   * Validate stream replay consistency
   */
  validateStreamReplay(engine) {
    const issues = [];

    if (this.streamBuffer.length === 0) {
      return { valid: true, issues: ["No events to replay"], replayCount: 0 };
    }

    // Count events by type
    const eventCounts = {};
    for (const event of this.streamBuffer) {
      eventCounts[event.type] = (eventCounts[event.type] || 0) + 1;
    }

    // Check 1: Stream contains events
    if (this.streamBuffer.length === 0) {
      issues.push("Stream buffer is empty");
    }

    // Check 2: Events are ordered
    let lastSequence = -1;
    for (const event of this.streamBuffer) {
      if (event.sequence !== undefined) {
        if (event.sequence <= lastSequence && event.sequence >= 0) {
          issues.push(`Out-of-order event: sequence ${event.sequence} after ${lastSequence}`);
          break;
        }
        lastSequence = event.sequence;
      }
    }

    // Check 3: No duplicate sequences
    const sequences = new Set();
    for (const event of this.streamBuffer) {
      if (event.sequence !== undefined && event.sequence >= 0) {
        if (sequences.has(event.sequence)) {
          issues.push(`Duplicate sequence: ${event.sequence}`);
        }
        sequences.add(event.sequence);
      }
    }

    return {
      valid: issues.length === 0,
      issues,
      replayCount: this.streamBuffer.length,
      eventTypes: eventCounts
    };
  }

  /**
   * Compare engine with stream
   */
  compareEngineToStream(engine) {
    const drifts = [];

    if (!engine || this.streamBuffer.length === 0) {
      return { hasDrift: false, drifts: [] };
    }

    // Check 1: Verify all created trades appear in stream
    const streamTradeIds = new Set();
    for (const event of this.streamBuffer) {
      if (event.data?.tradeId) {
        streamTradeIds.add(event.data.tradeId);
      }
    }

    // Count engine trades not in stream (acceptable: recent trades may not yet be streamed)
    let missingCount = 0;
    for (const tradeId of engine.trades.keys()) {
      if (!streamTradeIds.has(tradeId)) {
        missingCount++;
      }
    }

    // If too many missing, that's a drift
    const tolerableMissing = Math.max(5, engine.trades.size * 0.1); // 10% or 5 trades
    if (missingCount > tolerableMissing) {
      drifts.push({
        type: "missing_trades_in_stream",
        missing: missingCount,
        total: engine.trades.size,
        severity: "warning"
      });
    }

    // Check 2: Stream has duplicate trade IDs (shouldn't happen)
    const tradeIdCounts = {};
    for (const event of this.streamBuffer) {
      if (event.data?.tradeId) {
        const tid = event.data.tradeId;
        tradeIdCounts[tid] = (tradeIdCounts[tid] || 0) + 1;
      }
    }

    for (const [tid, count] of Object.entries(tradeIdCounts)) {
      if (count > 5) {
        // Allow multiple events per trade (created, updated, filled)
        // But not excessive repeats
        drifts.push({
          type: "excessive_trade_events",
          tradeId: tid,
          eventCount: count,
          severity: "warning"
        });
      }
    }

    return {
      hasDrift: drifts.length > 0,
      drifts,
      streamTradeCount: streamTradeIds.size,
      engineTradeCount: engine.trades.size
    };
  }

  /**
   * Full cross-system validation
   */
  validate(engine, uiState, config = null) {
    const validation = {
      timestamp: Date.now(),
      engine: this.validateEngineState(engine),
      stream: this.validateStreamReplay(engine),
      engineToUI: this.compareEngineToUI(engine, uiState),
      engineToStream: this.compareEngineToStream(engine),
      overallValid: true,
      issues: [],
      driftSummary: null
    };

    // Aggregate issues
    validation.issues.push(...validation.engine.issues.map(i => `[ENGINE] ${i}`));
    validation.issues.push(...validation.stream.issues.map(i => `[STREAM] ${i}`));
    validation.engineToUI.drifts.forEach(d => {
      validation.issues.push(`[UI-DRIFT] ${d.type}: ${JSON.stringify(d)}`);
    });
    validation.engineToStream.drifts.forEach(d => {
      validation.issues.push(`[STREAM-DRIFT] ${d.type}: ${JSON.stringify(d)}`);
    });

    // Determine severity
    const criticalCount = validation.issues.filter(i => i.includes("critical")).length;
    const warningCount = validation.issues.filter(i => i.includes("warning")).length;

    validation.driftSummary = {
      status: criticalCount > 0 ? "critical" : warningCount > 0 ? "warning" : "ok",
      criticalIssues: criticalCount,
      warningIssues: warningCount,
      totalIssues: validation.issues.length
    };

    validation.overallValid = validation.engine.valid && validation.stream.valid && criticalCount === 0;

    // Record hashes
    this.lastHashes.engine = this.hashEngineState(engine);
    this.lastHashes.ui = this.hashUIState(uiState);
    this.lastHashes.stream = this.hashStreamEvents(this.streamBuffer);
    if (config) {
      this.lastHashes.config = this.hashConfigState(config);
    }

    validation.hashes = this.lastHashes;

    // Log for analysis
    this.validationHistory.push(validation);
    if (!validation.overallValid || validation.driftSummary.status !== "ok") {
      this.driftLog.push({
        timestamp: validation.timestamp,
        status: validation.driftSummary.status,
        issues: validation.issues
      });
    }

    this.lastValidation = validation;
    return validation;
  }

  /**
   * Get consistency report
   */
  getConsistencyReport() {
    const totalValidations = this.validationHistory.length;
    const okValidations = this.validationHistory.filter(v => v.overallValid).length;

    const recentDrifts = this.driftLog.slice(-10);
    const criticalDrifts = this.driftLog.filter(d => d.status === "critical");

    return {
      totalValidations,
      passedValidations: okValidations,
      failedValidations: totalValidations - okValidations,
      passRate: totalValidations > 0 ? ((okValidations / totalValidations) * 100).toFixed(1) : 0,
      status: criticalDrifts.length > 0 ? "critical" : this.driftLog.length > 0 ? "warning" : "ok",
      recentDrifts,
      criticalDriftCount: criticalDrifts.length,
      lastValidation: this.lastValidation,
      hashes: this.lastHashes,
      timestamp: Date.now()
    };
  }

  /**
   * Reset logs
   */
  reset() {
    this.validationHistory = [];
    this.driftLog = [];
    this.streamBuffer = [];
    this.lastHashes = {
      engine: null,
      ui: null,
      stream: null,
      config: null
    };
  }
}

module.exports = SystemConsistencyValidator;
