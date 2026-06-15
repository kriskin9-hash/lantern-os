/**
 * Execution Conflict Resolver
 *
 * Handles conflicting or out-of-order messages from broker.
 * Examples of conflicts:
 * - Fill arrives before ACK
 * - Duplicate fills
 * - Late fills after cancellation
 * - Out-of-order events
 *
 * CRITICAL: Broker is unreliable. This layer makes the system robust.
 */

"use strict";

class ExecutionConflictResolver {
  /**
   * Check if new event conflicts with existing state
   * Returns { conflict: boolean, issue: string, resolution: string }
   */
  static checkConflict(currentState, newEvent) {
    // Can't fill an order that hasn't been ACK'd yet
    if (newEvent.type === "ORDER_FILLED" && !currentState.brokerId) {
      return {
        conflict: true,
        issue: "Fill arrived before ACK",
        resolution: "buffer_fill_until_ack",
      };
    }

    // Duplicate fill detection
    if (newEvent.type === "ORDER_FILLED" && currentState.filledQty === newEvent.filledQty) {
      return {
        conflict: true,
        issue: "Duplicate fill (same quantity)",
        resolution: "ignore_duplicate",
      };
    }

    // Fill after cancellation
    if (newEvent.type === "ORDER_FILLED" && currentState.status === "FAILED") {
      return {
        conflict: true,
        issue: "Fill received after order was cancelled",
        resolution: "reject_late_fill",
      };
    }

    // Backwards-moving fill (should never happen but broker is unreliable)
    if (newEvent.type === "ORDER_FILLED" && newEvent.filledQty < currentState.filledQty) {
      return {
        conflict: true,
        issue: "Fill quantity decreased (impossible)",
        resolution: "reject_backwards_fill",
      };
    }

    // No conflict detected
    return {
      conflict: false,
      issue: null,
      resolution: "accept_event",
    };
  }

  /**
   * Resolve conflict by choosing which event to trust
   * Uses timestamp precedence: earlier timestamp wins
   */
  static resolveConflict(currentState, newEvent, conflictInfo) {
    switch (conflictInfo.resolution) {
      case "buffer_fill_until_ack":
        // Store fill for replay after ACK arrives
        return {
          action: "buffer",
          event: newEvent,
          reason: "Will replay after ACK",
        };

      case "ignore_duplicate":
        // Same fill arrived again
        return {
          action: "ignore",
          reason: "Duplicate event (same fill quantity)",
        };

      case "reject_late_fill":
        // Broker trying to fill cancelled order (network delay?)
        return {
          action: "ignore",
          reason: "Late fill after cancellation (broker retry)",
        };

      case "reject_backwards_fill":
        // Should never happen - reject it
        return {
          action: "reject",
          reason: "Fill quantity decreased (data corruption?)",
        };

      default:
        return {
          action: "accept",
          reason: "No conflict detected",
        };
    }
  }

  /**
   * Detect out-of-order events
   * Returns true if event came out of order
   */
  static isOutOfOrder(currentState, newEvent) {
    // Check if we have a prior state for this order
    if (!currentState.lastUpdate) {
      return false;  // First event for this order
    }

    // Event timestamp is older than last update
    if (newEvent.timestamp < new Date(currentState.lastUpdate).getTime()) {
      return true;
    }

    return false;
  }

  /**
   * Merge conflicting fills
   * When broker reports different fill quantities, merge them
   */
  static mergeFills(fill1, fill2) {
    // Take the maximum filled quantity (most conservative)
    const maxFilledQty = Math.max(fill1.filledQty, fill2.filledQty);

    // Merge prices with VWAP
    const totalQuantity = maxFilledQty;
    const totalCost = (fill1.filledQty * fill1.avgPrice) + (fill2.filledQty * fill2.avgPrice);
    const mergedPrice = totalCost / totalQuantity;

    return {
      filledQty: maxFilledQty,
      avgPrice: Math.round(mergedPrice * 10000) / 10000,  // Round to 4 decimals
      eventIds: [fill1.eventId, fill2.eventId],  // Track both sources
    };
  }

  /**
   * Detect potential broker stale data
   * If fill is much older than now, it might be stale
   */
  static isStaleData(event, maxAgeMs = 60000) {
    const age = Date.now() - event.timestamp;
    return age > maxAgeMs;
  }

  /**
   * Detect broker response inconsistency
   * Same brokerOrder received with different fills
   */
  static detectInconsistency(priorOrder, newOrder) {
    if (newOrder.filledQty !== priorOrder.filledQty) {
      return {
        inconsistent: true,
        field: "filledQty",
        prior: priorOrder.filledQty,
        new: newOrder.filledQty,
      };
    }

    if (Math.abs(newOrder.avgPrice - priorOrder.avgPrice) > 0.01) {
      return {
        inconsistent: true,
        field: "avgPrice",
        prior: priorOrder.avgPrice,
        new: newOrder.avgPrice,
      };
    }

    if (newOrder.status !== priorOrder.status) {
      return {
        inconsistent: true,
        field: "status",
        prior: priorOrder.status,
        new: newOrder.status,
      };
    }

    return {
      inconsistent: false,
    };
  }

  /**
   * Choose which timestamp to trust
   * If timestamps differ significantly, investigate
   */
  static selectTrustworthy(event1, event2) {
    const timeDiff = Math.abs(event1.timestamp - event2.timestamp);

    if (timeDiff > 5000) {
      // More than 5 seconds apart - both are suspicious
      console.warn(
        `[ConflictResolver] Large timestamp gap: ` +
        `${new Date(event1.timestamp).toISOString()} vs ${new Date(event2.timestamp).toISOString()}`
      );
      return {
        selected: event1,  // Default to first
        reason: "timestamp_gap_detected",
      };
    }

    // Same timeframe - trust the one that came from broker first
    return {
      selected: event1.source === "broker_fill" ? event1 : event2,
      reason: "prefer_broker_source",
    };
  }

  /**
   * Validate conflict resolution
   * Sanity check that we didn't create an impossible state
   */
  static validateResolution(priorState, newState) {
    const issues = [];

    if (newState.filledQty > newState.quantity) {
      issues.push("Filled more than ordered");
    }

    if (newState.filledQty < 0) {
      issues.push("Negative fill quantity");
    }

    if (newState.avgPrice < 0) {
      issues.push("Negative average price");
    }

    // Status downgrade check (only forward transitions allowed)
    const statusHierarchy = {
      "PENDING": 0,
      "ACCEPTED": 1,
      "PARTIAL": 2,
      "FILLED": 3,
      "FAILED": 4,
    };

    const priorRank = statusHierarchy[priorState.status] || -1;
    const newRank = statusHierarchy[newState.status] || -1;

    if (newRank < priorRank && priorState.status !== "FAILED") {
      // Status downgrade is only allowed if prior was FAILED (idempotent)
      issues.push(`Status downgrade: ${priorState.status} → ${newState.status}`);
    }

    return {
      valid: issues.length === 0,
      issues,
    };
  }
}

module.exports = ExecutionConflictResolver;
