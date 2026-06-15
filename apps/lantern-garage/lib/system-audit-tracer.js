/**
 * System Audit Tracer — Phase 3.8
 *
 * Complete causal trace system for every system action.
 * Every event becomes a linked node in an immutable timeline DAG.
 *
 * Guarantees:
 * - Full reproducibility
 * - Forensic debugging capability
 * - AI decision explainability
 * - Compliance auditability
 */

"use strict";

const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

class SystemAuditTracer {
  constructor(auditLogPath) {
    this.auditLogPath = auditLogPath;
    this.sessionTraceId = this._generateTraceId();
    this.eventIndex = new Map(); // traceId → [events]
    this.eventCount = 0;
    this.startTime = Date.now();

    // Ensure audit log directory exists
    const dir = path.dirname(auditLogPath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    // Initialize or append to log
    if (!fs.existsSync(auditLogPath)) {
      fs.writeFileSync(auditLogPath, "");
    }
  }

  /**
   * Generate unique IDs
   */
  _generateTraceId() {
    return `t-${Date.now()}-${crypto.randomBytes(8).toString("hex")}`;
  }

  _generateEventId() {
    return `e-${crypto.randomBytes(16).toString("hex")}`;
  }

  /**
   * Record system event in immutable audit log
   */
  recordEvent(type, source, payload, parentEventId = null, customTraceId = null) {
    const event = {
      eventId: this._generateEventId(),
      timestamp: Date.now(),
      type, // TRADE | DRIFT | RECONCILE | UI_RENDER | AI_DECISION | STABILITY_CHECK
      source, // engine | ui | stream | ai | validator | reconciliation
      payload: { ...payload }, // shallow copy to prevent mutation
      parentEventId: parentEventId || null,
      traceId: customTraceId || this.sessionTraceId,
      sessionTraceId: this.sessionTraceId
    };

    // Append to immutable log file
    fs.appendFileSync(
      this.auditLogPath,
      JSON.stringify(event) + "\n"
    );

    // Index by traceId for quick lookup
    if (!this.eventIndex.has(event.traceId)) {
      this.eventIndex.set(event.traceId, []);
    }
    this.eventIndex.get(event.traceId).push(event);

    this.eventCount++;

    return event;
  }

  /**
   * Record AI decision with full context
   */
  recordAIDecision(decision, stabilityIndex, driftReport, confidence, reasoning) {
    const decisionEvent = {
      eventId: this._generateEventId(),
      timestamp: Date.now(),
      type: "AI_DECISION",
      source: "ai",
      payload: {
        decision, // e.g., { action: "BUY", symbol: "AAPL", quantity: 10 }
        confidence,
        reasoning: reasoning || [], // array of decision factors
        systemState: {
          stabilityIndex,
          driftReport: driftReport || null
        }
      },
      parentEventId: null,
      traceId: this._generateTraceId(), // New trace for this decision chain
      sessionTraceId: this.sessionTraceId
    };

    fs.appendFileSync(
      this.auditLogPath,
      JSON.stringify(decisionEvent) + "\n"
    );

    if (!this.eventIndex.has(decisionEvent.traceId)) {
      this.eventIndex.set(decisionEvent.traceId, []);
    }
    this.eventIndex.get(decisionEvent.traceId).push(decisionEvent);

    this.eventCount++;

    return decisionEvent.traceId; // Return trace ID for linking future events
  }

  /**
   * Record trade execution with full chain
   */
  recordTradeExecution(traceId, orderId, engineResponse, success, error = null) {
    const tradeEvent = this.recordEvent(
      "TRADE_EXECUTION",
      "engine",
      {
        orderId,
        success,
        error: error || null,
        engineResponse: engineResponse || null
      },
      null,
      traceId
    );

    return tradeEvent;
  }

  /**
   * Record drift detection and resolution
   */
  recordDriftEvent(driftType, detected, reconciliationActions, resolved) {
    const event = this.recordEvent(
      "DRIFT",
      "validator",
      {
        driftType, // ui_lag | stream_delay | config_mismatch | event_loss
        detected: {
          severity: detected.severity,
          details: detected.details
        },
        reconciliationActions: reconciliationActions || [],
        resolved
      }
    );

    return event;
  }

  /**
   * Record UI state snapshot
   */
  recordUIState(uiStateSnapshot, linkedTradeId = null) {
    const event = this.recordEvent(
      "UI_RENDER",
      "ui",
      {
        tradeCount: uiStateSnapshot.tradeCount,
        displayedTrades: uiStateSnapshot.displayedTrades || [],
        timestamp: uiStateSnapshot.timestamp,
        linkedToTrade: linkedTradeId || null
      }
    );

    return event;
  }

  /**
   * Record stability check
   */
  recordStabilityCheck(stabilityIndex, status, canExecuteTrades) {
    const event = this.recordEvent(
      "STABILITY_CHECK",
      "validator",
      {
        stabilityIndex,
        status,
        canExecuteTrades,
        checked: true
      }
    );

    return event;
  }

  /**
   * Get all events for a trace
   */
  getTraceEvents(traceId) {
    return this.eventIndex.get(traceId) || [];
  }

  /**
   * Reconstruct causal chain for a trace
   */
  reconstructTrace(traceId) {
    const events = this.getTraceEvents(traceId);

    if (events.length === 0) {
      return null;
    }

    // Sort by timestamp
    const sorted = [...events].sort((a, b) => a.timestamp - b.timestamp);

    // Build parent-child relationships
    const eventMap = new Map(sorted.map(e => [e.eventId, e]));
    const chain = [];
    let current = sorted[0];

    while (current) {
      chain.push({
        eventId: current.eventId,
        type: current.type,
        timestamp: current.timestamp,
        payload: current.payload
      });

      // Find child (next event with parentEventId = current.eventId)
      const child = sorted.find(e => e.parentEventId === current.eventId);
      current = child || null;
    }

    return {
      traceId,
      startTime: sorted[0].timestamp,
      endTime: sorted[sorted.length - 1].timestamp,
      duration: sorted[sorted.length - 1].timestamp - sorted[0].timestamp,
      eventCount: events.length,
      chain,
      allEvents: sorted
    };
  }

  /**
   * Validate causal integrity
   */
  validateCausalIntegrity(traceId) {
    const events = this.getTraceEvents(traceId);

    if (events.length === 0) {
      return { valid: false, issues: ["No events found for trace"] };
    }

    const issues = [];
    const eventIds = new Set(events.map(e => e.eventId));

    // Check 1: All parent references exist
    for (const event of events) {
      if (event.parentEventId && !eventIds.has(event.parentEventId)) {
        issues.push(`Orphan parent reference: ${event.eventId} → ${event.parentEventId}`);
      }
    }

    // Check 2: No circular dependencies
    for (const event of events) {
      if (this._hasCircularDependency(event, events)) {
        issues.push(`Circular dependency detected at ${event.eventId}`);
      }
    }

    // Check 3: Required event types present
    const types = new Set(events.map(e => e.type));
    if (types.has("AI_DECISION") && !types.has("TRADE_EXECUTION")) {
      issues.push("AI decision without corresponding trade execution");
    }

    return {
      valid: issues.length === 0,
      issues,
      eventCount: events.length,
      eventTypes: Array.from(types)
    };
  }

  /**
   * Helper: check for circular dependencies
   */
  _hasCircularDependency(event, allEvents) {
    const visited = new Set();
    let current = event;

    while (current && current.parentEventId) {
      if (visited.has(current.parentEventId)) {
        return true; // Circular
      }
      visited.add(current.parentEventId);

      const parent = allEvents.find(e => e.eventId === current.parentEventId);
      current = parent;
    }

    return false;
  }

  /**
   * Get audit summary
   */
  getAuditSummary() {
    return {
      sessionTraceId: this.sessionTraceId,
      startTime: this.startTime,
      uptime: Date.now() - this.startTime,
      totalEvents: this.eventCount,
      uniqueTraces: this.eventIndex.size,
      eventBreakdown: this._getEventTypeBreakdown(),
      auditLogPath: this.auditLogPath
    };
  }

  /**
   * Get event type breakdown
   */
  _getEventTypeBreakdown() {
    const breakdown = {};

    for (const events of this.eventIndex.values()) {
      for (const event of events) {
        breakdown[event.type] = (breakdown[event.type] || 0) + 1;
      }
    }

    return breakdown;
  }

  /**
   * Export full audit log (careful with size)
   */
  exportAuditLog(limit = 1000) {
    const allEvents = Array.from(this.eventIndex.values())
      .flat()
      .sort((a, b) => a.timestamp - b.timestamp)
      .slice(-limit);

    return {
      exportTime: Date.now(),
      eventCount: allEvents.length,
      events: allEvents
    };
  }
}

module.exports = SystemAuditTracer;
