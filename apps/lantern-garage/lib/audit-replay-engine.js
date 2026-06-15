/**
 * Audit Replay Engine — Phase 3.8
 *
 * Reconstructs full system timeline from immutable audit log.
 * Enables complete forensic debugging and AI decision explainability.
 *
 * Can answer: "Why did this happen?" with full reproducibility.
 */

"use strict";

class AuditReplayEngine {
  constructor(tracer) {
    this.tracer = tracer;
    this.replayCache = new Map(); // traceId → reconstructed timeline
  }

  /**
   * Full timeline reconstruction
   */
  reconstructTimeline(traceId) {
    // Check cache first
    if (this.replayCache.has(traceId)) {
      return this.replayCache.get(traceId);
    }

    const events = this.tracer.getTraceEvents(traceId);

    if (events.length === 0) {
      return {
        traceId,
        found: false,
        error: "No events found for this trace"
      };
    }

    // Sort chronologically
    const sorted = [...events].sort((a, b) => a.timestamp - b.timestamp);

    // Validate causal integrity
    const integrity = this.tracer.validateCausalIntegrity(traceId);

    // Build decision path
    const decisionPath = this._buildDecisionPath(sorted);

    // Reconstruct final state
    const finalState = this._reconstructFinalState(sorted);

    // Build timeline
    const timeline = {
      traceId,
      found: true,
      startTime: sorted[0].timestamp,
      endTime: sorted[sorted.length - 1].timestamp,
      duration: sorted[sorted.length - 1].timestamp - sorted[0].timestamp,
      eventCount: events.length,
      integrity: integrity,
      decisionPath,
      finalState,
      events: sorted.map(e => ({
        eventId: e.eventId,
        timestamp: e.timestamp,
        type: e.type,
        source: e.source,
        payload: e.payload
      }))
    };

    // Cache
    this.replayCache.set(traceId, timeline);

    return timeline;
  }

  /**
   * Build causal decision path
   */
  _buildDecisionPath(events) {
    const path = [];
    const typeOrder = {
      "AI_DECISION": 0,
      "STABILITY_CHECK": 1,
      "DRIFT": 2,
      "RECONCILE": 3,
      "TRADE_EXECUTION": 4,
      "STREAM_EVENT": 5,
      "UI_RENDER": 6
    };

    const sorted = [...events].sort((a, b) => {
      const aOrder = typeOrder[a.type] ?? 99;
      const bOrder = typeOrder[b.type] ?? 99;
      return aOrder - bOrder || a.timestamp - b.timestamp;
    });

    for (const event of sorted) {
      path.push({
        type: event.type,
        timestamp: event.timestamp,
        source: event.source,
        summary: this._summarizeEvent(event)
      });
    }

    return path;
  }

  /**
   * Summarize event for human reading
   */
  _summarizeEvent(event) {
    switch (event.type) {
      case "AI_DECISION":
        return `AI decided: ${event.payload.decision?.action} (${event.payload.confidence})`;
      case "STABILITY_CHECK":
        return `Stability: ${event.payload.stabilityIndex} (${event.payload.status})`;
      case "DRIFT":
        return `Drift ${event.payload.driftType}: ${event.payload.detected?.severity} ${event.payload.resolved ? "[RESOLVED]" : ""}`;
      case "RECONCILE":
        return `Reconciliation: ${event.payload.status}`;
      case "TRADE_EXECUTION":
        return `Trade ${event.payload.success ? "SUCCESS" : "FAILED"} (${event.payload.orderId})`;
      case "STREAM_EVENT":
        return `Stream: ${event.payload.eventType}`;
      case "UI_RENDER":
        return `UI rendered ${event.payload.tradeCount} trades`;
      default:
        return `${event.type} event`;
    }
  }

  /**
   * Reconstruct final state from events
   */
  _reconstructFinalState(events) {
    const state = {
      trades: {},
      lastAIDecision: null,
      lastStabilityIndex: null,
      driftEvents: [],
      uiState: null
    };

    for (const event of events) {
      switch (event.type) {
        case "AI_DECISION":
          state.lastAIDecision = {
            decision: event.payload.decision,
            confidence: event.payload.confidence,
            reasoning: event.payload.reasoning,
            timestamp: event.timestamp
          };
          break;

        case "STABILITY_CHECK":
          state.lastStabilityIndex = {
            index: event.payload.stabilityIndex,
            status: event.payload.status,
            timestamp: event.timestamp
          };
          break;

        case "DRIFT":
          state.driftEvents.push({
            type: event.payload.driftType,
            severity: event.payload.detected?.severity,
            resolved: event.payload.resolved,
            timestamp: event.timestamp
          });
          break;

        case "TRADE_EXECUTION":
          state.trades[event.payload.orderId] = {
            orderId: event.payload.orderId,
            success: event.payload.success,
            error: event.payload.error,
            timestamp: event.timestamp
          };
          break;

        case "UI_RENDER":
          state.uiState = {
            tradeCount: event.payload.tradeCount,
            displayedTrades: event.payload.displayedTrades,
            timestamp: event.payload.timestamp
          };
          break;
      }
    }

    return state;
  }

  /**
   * Get decision explanation
   */
  explainDecision(traceId) {
    const timeline = this.reconstructTimeline(traceId);

    if (!timeline.found) {
      return { error: "Trace not found" };
    }

    const aiDecisionEvent = timeline.events.find(e => e.type === "AI_DECISION");
    if (!aiDecisionEvent) {
      return { error: "No AI decision in trace" };
    }

    return {
      traceId,
      decision: aiDecisionEvent.payload.decision,
      confidence: aiDecisionEvent.payload.confidence,
      reasoning: aiDecisionEvent.payload.reasoning,
      systemContext: {
        stabilityIndex: timeline.finalState.lastStabilityIndex,
        driftHistory: timeline.finalState.driftEvents
      },
      result: {
        executed: timeline.finalState.trades,
        uiState: timeline.finalState.uiState
      },
      timeline: timeline.decisionPath
    };
  }

  /**
   * Get drift resolution explanation
   */
  explainDriftResolution(traceId) {
    const timeline = this.reconstructTimeline(traceId);

    if (!timeline.found) {
      return { error: "Trace not found" };
    }

    const driftEvents = timeline.events.filter(e => e.type === "DRIFT");
    if (driftEvents.length === 0) {
      return { error: "No drift events in trace" };
    }

    return {
      traceId,
      driftEvents: driftEvents.map(e => ({
        type: e.payload.driftType,
        severity: e.payload.detected?.severity,
        details: e.payload.detected?.details,
        reconciliationActions: e.payload.reconciliationActions,
        resolved: e.payload.resolved,
        timestamp: e.timestamp
      })),
      timeline: timeline.decisionPath
    };
  }

  /**
   * Detect orphan events (events without proper causal chain)
   */
  detectOrphans(traceId) {
    const timeline = this.reconstructTimeline(traceId);

    if (!timeline.found) {
      return { error: "Trace not found" };
    }

    const issues = [];
    const eventIds = new Set(timeline.events.map(e => e.eventId));

    for (const event of timeline.events) {
      // Check 1: Trade execution without AI decision
      if (event.type === "TRADE_EXECUTION") {
        const hasAIDecision = timeline.events.some(e => e.type === "AI_DECISION");
        if (!hasAIDecision) {
          issues.push(`Trade execution ${event.eventId} without AI decision`);
        }
      }

      // Check 2: UI render without trade
      if (event.type === "UI_RENDER") {
        const hasTrade = timeline.events.some(e => e.type === "TRADE_EXECUTION");
        if (!hasTrade && timeline.events.length > 1) {
          issues.push(`UI render ${event.eventId} without preceding trade`);
        }
      }

      // Check 3: Reconciliation without drift detection
      if (event.type === "RECONCILE") {
        const hasDrift = timeline.events.some(e => e.type === "DRIFT");
        if (!hasDrift) {
          issues.push(`Reconciliation ${event.eventId} without drift detection`);
        }
      }
    }

    return {
      traceId,
      hasOrphans: issues.length > 0,
      issues,
      eventCount: timeline.events.length
    };
  }

  /**
   * Get system audit summary
   */
  getSystemAuditSummary() {
    const allTraces = Array.from(this.tracer.eventIndex.keys());

    const summary = {
      totalTraces: allTraces.length,
      systemTraceId: this.tracer.sessionTraceId,
      uptime: Date.now() - this.tracer.startTime,
      totalEvents: this.tracer.eventCount,
      breakdown: this.tracer._getEventTypeBreakdown(),
      recentTraces: allTraces.slice(-10).map(traceId => {
        const events = this.tracer.getTraceEvents(traceId);
        if (events.length === 0) return null;

        const sorted = [...events].sort((a, b) => a.timestamp - b.timestamp);
        return {
          traceId,
          eventCount: events.length,
          startTime: sorted[0].timestamp,
          endTime: sorted[sorted.length - 1].timestamp,
          duration: sorted[sorted.length - 1].timestamp - sorted[0].timestamp,
          types: [...new Set(events.map(e => e.type))]
        };
      }).filter(Boolean)
    };

    return summary;
  }

  /**
   * Clear cache (for memory management)
   */
  clearCache() {
    this.replayCache.clear();
  }
}

module.exports = AuditReplayEngine;
