/**
 * Broker Event Normalizer
 *
 * Converts inconsistent broker API responses into clean, canonical events.
 * Different brokers return different formats - this is the normalization layer.
 *
 * INPUT: messy broker responses
 * OUTPUT: clean events that feed into EventStore
 */

"use strict";

const EventStore = require("./execution-event-store");

class BrokerEventNormalizer {
  /**
   * Normalize broker order acknowledgement
   * Brokers have different ACK formats - standardize here
   */
  static normalizeBrokerAck(brokerAckResponse, localOrder) {
    const event = {
      eventId: EventStore.generateEventId(),
      orderId: localOrder.orderId,
      type: "BROKER_ACK",
      timestamp: Date.now(),
      source: "broker_ack",
      brokerId: brokerAckResponse.id || brokerAckResponse.order_id || brokerAckResponse.orderId,
      brokerStatus: this.normalizeStatus(brokerAckResponse.status),
      raw: brokerAckResponse,
    };

    // Validate normalized event
    if (!event.brokerId) {
      throw new Error("Broker response missing order ID");
    }

    return event;
  }

  /**
   * Normalize broker fill response
   * Brokers report fills in different ways
   */
  static normalizeFill(brokerFillResponse, localOrder) {
    // Extract fill details from broker response
    const filledQty = this.extractFilledQty(brokerFillResponse);
    const avgPrice = this.extractAvgPrice(brokerFillResponse);
    const fillTime = this.extractFillTimestamp(brokerFillResponse);

    const event = {
      eventId: EventStore.generateEventId(),
      orderId: localOrder.orderId,
      type: "ORDER_FILLED",
      timestamp: fillTime,
      source: "broker_fill",
      brokerId: brokerFillResponse.id || brokerFillResponse.order_id,
      filledQty,
      avgPrice,
      raw: brokerFillResponse,
    };

    // Validate
    if (filledQty <= 0) {
      throw new Error(`Invalid filled quantity: ${filledQty}`);
    }
    if (avgPrice <= 0) {
      throw new Error(`Invalid average price: ${avgPrice}`);
    }

    return event;
  }

  /**
   * Normalize broker order status response
   * Used during reconciliation
   */
  static normalizeOrderStatus(brokerOrder, localOrder) {
    const status = this.normalizeStatus(brokerOrder.status);

    // Create appropriate event based on status
    if (status === "FILLED") {
      return this.normalizeFill(brokerOrder, localOrder);
    } else if (status === "CANCELLED") {
      return {
        eventId: EventStore.generateEventId(),
        orderId: localOrder.orderId,
        type: "ORDER_CANCELLED",
        timestamp: Date.now(),
        source: "broker_status_check",
        brokerId: brokerOrder.id,
        raw: brokerOrder,
      };
    } else if (status === "FAILED") {
      return {
        eventId: EventStore.generateEventId(),
        orderId: localOrder.orderId,
        type: "ORDER_FAILED",
        timestamp: Date.now(),
        source: "broker_status_check",
        brokerId: brokerOrder.id,
        reason: brokerOrder.failureReason || "Broker execution failed",
        raw: brokerOrder,
      };
    } else if (brokerOrder.filledQty > 0 && brokerOrder.filledQty < brokerOrder.quantity) {
      // Partial fill
      return {
        eventId: EventStore.generateEventId(),
        orderId: localOrder.orderId,
        type: "FILL_UPDATE",
        timestamp: Date.now(),
        source: "broker_status_check",
        brokerId: brokerOrder.id,
        filledQty: brokerOrder.filledQty,
        avgPrice: brokerOrder.avgPrice || 0,
        raw: brokerOrder,
      };
    }

    // Status unchanged, no event
    return null;
  }

  /**
   * Normalize inconsistent status strings from different brokers
   * ALPACA: "pending_new", "accepted", "filled", "cancelled", "rejected"
   * INTERACTIVE: "PreSubmitted", "ApiPending", "ApiCancelled", "Filled", "Cancelled"
   * etc.
   */
  static normalizeStatus(brokerStatus) {
    if (!brokerStatus) return "PENDING";

    const status = String(brokerStatus).toUpperCase();

    // Map all variations to canonical forms
    if (status.includes("FILLED")) return "FILLED";
    if (status.includes("CANCEL")) return "CANCELLED";
    if (status.includes("REJECT") || status.includes("FAILED")) return "FAILED";
    if (status.includes("NEW") || status.includes("PENDING")) return "PENDING";
    if (status.includes("ACCEPT") || status.includes("ACKNOWLEDGED")) return "ACCEPTED";
    if (status.includes("PARTIAL")) return "PARTIAL";

    // Unknown status
    console.warn(`[BrokerNormalizer] Unknown status: ${brokerStatus}`);
    return status;
  }

  /**
   * Extract filled quantity from broker response
   * Different brokers use different field names
   */
  static extractFilledQty(brokerOrder) {
    return (
      brokerOrder.filledQty ||
      brokerOrder.filled_qty ||
      brokerOrder.filled_quantity ||
      brokerOrder.cumQty ||
      brokerOrder.cum_qty ||
      brokerOrder.executedQuantity ||
      brokerOrder.executed_quantity ||
      0
    );
  }

  /**
   * Extract average fill price from broker response
   */
  static extractAvgPrice(brokerOrder) {
    return (
      brokerOrder.avgPrice ||
      brokerOrder.avg_price ||
      brokerOrder.averagePrice ||
      brokerOrder.average_price ||
      brokerOrder.filledPrice ||
      brokerOrder.filled_price ||
      brokerOrder.executionPrice ||
      brokerOrder.execution_price ||
      0
    );
  }

  /**
   * Extract fill timestamp from broker response
   * Use broker's timestamp if available, otherwise use now
   */
  static extractFillTimestamp(brokerOrder) {
    const brokerTime =
      brokerOrder.filledAt ||
      brokerOrder.filled_at ||
      brokerOrder.filledTime ||
      brokerOrder.filled_time ||
      brokerOrder.updatedAt ||
      brokerOrder.updated_at ||
      brokerOrder.transactTime ||
      brokerOrder.transact_time;

    if (brokerTime) {
      // Convert to milliseconds if needed
      const ms = String(brokerTime).length > 10 ? brokerTime : brokerTime * 1000;
      return new Date(ms).getTime();
    }

    return Date.now();
  }

  /**
   * Batch normalize multiple broker fills
   * Used when broker returns fill list in single response
   */
  static normalizeFillBatch(brokerFills, localOrder) {
    const events = [];

    for (const fill of brokerFills) {
      try {
        const event = this.normalizeFill(fill, localOrder);
        events.push(event);
      } catch (e) {
        console.warn(`[BrokerNormalizer] Failed to normalize fill: ${e.message}`);
      }
    }

    return events;
  }

  /**
   * Detect if broker response format changed (API update)
   * Returns list of fields that appeared/disappeared
   */
  static detectFormatChange(newResponse, previousResponse) {
    if (!previousResponse) return null;

    const newFields = new Set(Object.keys(newResponse));
    const oldFields = new Set(Object.keys(previousResponse));

    const added = [...newFields].filter(f => !oldFields.has(f));
    const removed = [...oldFields].filter(f => !newFields.has(f));

    if (added.length > 0 || removed.length > 0) {
      return { added, removed };
    }

    return null;
  }
}

module.exports = BrokerEventNormalizer;
