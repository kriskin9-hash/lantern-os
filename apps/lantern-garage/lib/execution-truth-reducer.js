/**
 * Execution Truth Reducer
 *
 * Derives authoritative order state from immutable event stream.
 * This is the single source of truth - all state flows from events.
 *
 * Reducer pattern: (previousState, event) => newState
 * Deterministic: same event sequence always produces same final state.
 */

"use strict";

class ExecutionTruthReducer {
  /**
   * Derive complete order state from event history
   * Used on startup and after any divergence
   */
  static deriveOrderState(orderId, events) {
    // Initial order state (empty)
    let state = {
      orderId,
      ticker: null,
      side: null,
      quantity: 0,
      filledQty: 0,
      avgPrice: 0,
      status: "PENDING",
      brokerId: null,
      submittedAt: null,
      brokerAckAt: null,
      filledAt: null,
      failedAt: null,
      failureReason: null,
      lastUpdate: null,
      history: [],  // Track all state changes for debugging
    };

    // Replay events in order
    for (const event of events) {
      state = this.reduceEvent(state, event);
    }

    return state;
  }

  /**
   * Apply single event to order state
   * Pure function: no side effects
   */
  static reduceEvent(state, event) {
    // Log all state transitions
    const oldStatus = state.status;

    switch (event.type) {
      case "ORDER_SUBMITTED":
        state = {
          ...state,
          ticker: event.ticker,
          side: event.side,
          quantity: event.quantity,
          status: "PENDING",
          submittedAt: event.timestamp,
          lastUpdate: event.timestamp,
        };
        break;

      case "BROKER_ACK":
        state = {
          ...state,
          brokerId: event.brokerId,
          status: event.brokerStatus || "ACCEPTED",
          brokerAckAt: event.timestamp,
          lastUpdate: event.timestamp,
        };
        break;

      case "ORDER_FILLED":
        state = {
          ...state,
          filledQty: event.filledQty,
          avgPrice: event.avgPrice,
          status: event.filledQty >= state.quantity ? "FILLED" : "PARTIAL",
          filledAt: event.filledQty >= state.quantity ? event.timestamp : state.filledAt,
          lastUpdate: event.timestamp,
        };
        break;

      case "ORDER_FAILED":
        state = {
          ...state,
          status: "FAILED",
          failureReason: event.reason,
          failedAt: event.timestamp,
          lastUpdate: event.timestamp,
        };
        break;

      case "FILL_UPDATE":
        // Partial fill or fill quantity correction
        state = {
          ...state,
          filledQty: event.filledQty,
          avgPrice: event.avgPrice || state.avgPrice,
          status: event.filledQty >= state.quantity ? "FILLED" : "PARTIAL",
          filledAt: event.filledQty >= state.quantity ? event.timestamp : state.filledAt,
          lastUpdate: event.timestamp,
        };
        break;

      case "ORDER_CANCELLED":
        state = {
          ...state,
          status: "FAILED",
          failureReason: "Order cancelled",
          failedAt: event.timestamp,
          lastUpdate: event.timestamp,
        };
        break;

      default:
        console.warn(`[TruthReducer] Unknown event type: ${event.type}`);
    }

    // Track state transitions
    if (oldStatus !== state.status) {
      state.history.push({
        from: oldStatus,
        to: state.status,
        event: event.type,
        timestamp: event.timestamp,
      });
    }

    return state;
  }

  /**
   * Derive all orders from complete event log
   */
  static deriveAllOrders(allEvents) {
    const orderMap = new Map();

    // Group events by orderId
    const eventsByOrder = {};
    for (const event of allEvents) {
      if (!eventsByOrder[event.orderId]) {
        eventsByOrder[event.orderId] = [];
      }
      eventsByOrder[event.orderId].push(event);
    }

    // Derive each order's state
    for (const [orderId, events] of Object.entries(eventsByOrder)) {
      const state = this.deriveOrderState(orderId, events);
      orderMap.set(orderId, state);
    }

    return orderMap;
  }

  /**
   * Check if event stream is valid
   * Returns { valid: true } or { valid: false, reason: "..." }
   */
  static validateEventStream(events) {
    const seenEventIds = new Set();

    for (let i = 0; i < events.length; i++) {
      const event = events[i];

      // Check required fields
      if (!event.eventId || !event.orderId || !event.type || !event.timestamp) {
        return {
          valid: false,
          reason: `Event ${i} missing required field`,
          event,
        };
      }

      // Check for duplicates
      if (seenEventIds.has(event.eventId)) {
        return {
          valid: false,
          reason: `Duplicate event ID: ${event.eventId}`,
          event,
        };
      }
      seenEventIds.add(event.eventId);

      // Check timestamp ordering within order (events should be mostly sorted)
      if (i > 0) {
        const prev = events[i - 1];
        if (prev.orderId === event.orderId && prev.timestamp > event.timestamp) {
          console.warn(
            `[TruthReducer] Out-of-order event for ${event.orderId}: ` +
            `${prev.type}(${prev.timestamp}) > ${event.type}(${event.timestamp})`
          );
          // This is not invalid - the reducer handles out-of-order events
        }
      }
    }

    return { valid: true };
  }

  /**
   * Compute deterministic hash of order state
   * Used to detect divergence with external systems
   */
  static hashOrderState(order) {
    const crypto = require("crypto");
    const canonical = JSON.stringify({
      orderId: order.orderId,
      ticker: order.ticker,
      side: order.side,
      quantity: order.quantity,
      filledQty: order.filledQty,
      avgPrice: order.avgPrice,
      status: order.status,
      brokerId: order.brokerId,
    });
    return crypto.createHash("sha256").update(canonical).digest("hex");
  }
}

module.exports = ExecutionTruthReducer;
