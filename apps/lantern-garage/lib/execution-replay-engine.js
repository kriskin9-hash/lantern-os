/**
 * Execution Replay Engine
 *
 * Rebuilds complete system state from event log.
 * Used on startup for crash recovery and for forensic analysis.
 *
 * CRITICAL: Replaying the same event log must always produce the same state.
 * If not, there's a bug in the reducer or conflict resolver.
 */

"use strict";

const ExecutionEventStore = require("./execution-event-store");
const ExecutionTruthReducer = require("./execution-truth-reducer");
const ExecutionConflictResolver = require("./execution-conflict-resolver");

class ExecutionReplayEngine {
  constructor(eventStore) {
    this.eventStore = eventStore;
    this.replayLog = [];  // Track all replays for debugging
  }

  /**
   * Full system replay
   * Reconstruct all orders from event log
   */
  async replayAll() {
    console.log("[ReplayEngine] Starting full system replay...");
    const startTime = Date.now();

    try {
      // Get all events from store
      const allEvents = this.eventStore.getAllEvents();

      // Validate event stream integrity
      const validation = ExecutionTruthReducer.validateEventStream(allEvents);
      if (!validation.valid) {
        console.error(`[ReplayEngine] Event stream validation failed: ${validation.reason}`);
        return {
          success: false,
          reason: validation.reason,
        };
      }

      // Derive all orders from events
      const orderMap = ExecutionTruthReducer.deriveAllOrders(allEvents);

      // Separate open and completed orders
      const openOrders = [];
      const completedOrders = [];

      for (const order of orderMap.values()) {
        if (order.status === "FILLED" || order.status === "FAILED") {
          completedOrders.push(order);
        } else {
          openOrders.push(order);
        }
      }

      const elapsed = Date.now() - startTime;
      const stats = {
        totalEvents: allEvents.length,
        totalOrders: orderMap.size,
        openOrders: openOrders.length,
        completedOrders: completedOrders.length,
        elapsedMs: elapsed,
      };

      console.log(
        `[ReplayEngine] Replay complete: ${orderMap.size} orders, ` +
        `${openOrders.length} open, ${completedOrders.length} completed (${elapsed}ms)`
      );

      // Log the replay for debugging
      this.replayLog.push({
        timestamp: new Date().toISOString(),
        type: "full_replay",
        stats,
      });

      return {
        success: true,
        orderMap,
        openOrders,
        completedOrders,
        stats,
      };
    } catch (e) {
      console.error(`[ReplayEngine] Replay failed: ${e.message}`);
      return {
        success: false,
        reason: e.message,
      };
    }
  }

  /**
   * Single order replay
   * Reconstruct specific order from its events
   */
  replayOrder(orderId) {
    console.log(`[ReplayEngine] Replaying order: ${orderId}`);

    try {
      const events = this.eventStore.getOrderEvents(orderId);

      if (events.length === 0) {
        return {
          success: false,
          reason: `No events found for order ${orderId}`,
        };
      }

      // Derive state from events
      const finalState = ExecutionTruthReducer.deriveOrderState(orderId, events);

      console.log(
        `[ReplayEngine] Order replay complete: ${orderId} status=${finalState.status} ` +
        `(${events.length} events)`
      );

      return {
        success: true,
        order: finalState,
        eventCount: events.length,
        events,
      };
    } catch (e) {
      console.error(`[ReplayEngine] Order replay failed: ${e.message}`);
      return {
        success: false,
        reason: e.message,
      };
    }
  }

  /**
   * Time-window replay
   * Reconstruct system state at a specific point in time
   */
  replayUntil(endTimestamp) {
    console.log(`[ReplayEngine] Replaying until ${new Date(endTimestamp).toISOString()}`);

    try {
      // Get events up to timestamp
      const allEvents = this.eventStore.getAllEvents();
      const windowEvents = allEvents.filter(e => e.timestamp <= endTimestamp);

      if (windowEvents.length === 0) {
        return {
          success: false,
          reason: "No events in time window",
        };
      }

      // Derive orders from windowed events
      const orderMap = ExecutionTruthReducer.deriveAllOrders(windowEvents);

      console.log(
        `[ReplayEngine] Time-window replay complete: ${orderMap.size} orders ` +
        `(${windowEvents.length} events)`
      );

      return {
        success: true,
        orderMap,
        eventCount: windowEvents.length,
      };
    } catch (e) {
      console.error(`[ReplayEngine] Time-window replay failed: ${e.message}`);
      return {
        success: false,
        reason: e.message,
      };
    }
  }

  /**
   * Verify replay determinism
   * Replay twice and verify both produce identical results
   */
  verifyDeterminism() {
    console.log("[ReplayEngine] Verifying replay determinism...");

    try {
      // First replay
      const replay1 = this.replayAll();
      if (!replay1.success) {
        return {
          deterministic: false,
          reason: "First replay failed",
        };
      }

      // Second replay
      const replay2 = this.replayAll();
      if (!replay2.success) {
        return {
          deterministic: false,
          reason: "Second replay failed",
        };
      }

      // Compare results
      const map1 = replay1.orderMap;
      const map2 = replay2.orderMap;

      if (map1.size !== map2.size) {
        return {
          deterministic: false,
          reason: `Order count mismatch: ${map1.size} vs ${map2.size}`,
        };
      }

      // Compare each order
      for (const [orderId, order1] of map1) {
        const order2 = map2.get(orderId);
        if (!order2) {
          return {
            deterministic: false,
            reason: `Order ${orderId} missing in second replay`,
          };
        }

        // Compare critical fields
        const hash1 = ExecutionTruthReducer.hashOrderState(order1);
        const hash2 = ExecutionTruthReducer.hashOrderState(order2);

        if (hash1 !== hash2) {
          return {
            deterministic: false,
            reason: `Order ${orderId} state hash mismatch`,
            order1,
            order2,
          };
        }
      }

      console.log("[ReplayEngine] ✓ Determinism verified: identical replays");
      return {
        deterministic: true,
        orderCount: map1.size,
      };
    } catch (e) {
      console.error(`[ReplayEngine] Determinism check failed: ${e.message}`);
      return {
        deterministic: false,
        reason: e.message,
      };
    }
  }

  /**
   * Audit order history
   * Generate detailed timeline of order lifecycle
   */
  auditOrder(orderId) {
    const events = this.eventStore.getOrderEvents(orderId);

    if (events.length === 0) {
      return {
        orderId,
        timeline: [],
        message: "No events found",
      };
    }

    // Build timeline
    const timeline = [];
    for (const event of events) {
      timeline.push({
        timestamp: new Date(event.timestamp).toISOString(),
        type: event.type,
        source: event.source,
        eventId: event.eventId,
        details: {
          brokerId: event.brokerId,
          filledQty: event.filledQty,
          avgPrice: event.avgPrice,
          status: event.brokerStatus,
          reason: event.reason,
        },
      });
    }

    // Derive final state
    const finalState = ExecutionTruthReducer.deriveOrderState(orderId, events);

    return {
      orderId,
      timeline,
      finalState,
      eventCount: events.length,
    };
  }

  /**
   * Get replay statistics
   */
  getStats() {
    return {
      replayCount: this.replayLog.length,
      lastReplay: this.replayLog[this.replayLog.length - 1] || null,
      allReplays: this.replayLog,
    };
  }
}

module.exports = ExecutionReplayEngine;
