/**
 * Execution State Tracker
 *
 * Maintains authoritative record of order lifecycle.
 * Tracks internal → broker state, detects divergence, enables recovery.
 *
 * CRITICAL: This is the source of truth for what is "really" executed.
 * No trade is considered real until:
 * 1. Engine creates order
 * 2. Broker acknowledges with brokerId
 * 3. Broker confirms fill (or partial fill)
 * 4. Reconciler validates external state matches internal
 */

"use strict";

const fs = require("fs");
const path = require("path");

const EXECUTION_LOG_PATH = path.join(__dirname, "..", "..", "data", "lantern-garage", "trading", "execution-state.jsonl");

class ExecutionStateTracker {
  constructor() {
    this.openOrders = new Map();  // orderId -> order state
    this.completedOrders = [];     // historical record
    this.loadState();
  }

  /**
   * Record order submission (engine → broker)
   * At this point: we've sent to broker, awaiting acknowledgement
   */
  recordOrderSubmission(order) {
    const tracked = {
      orderId: order.id || this.generateOrderId(),
      ticker: order.ticker,
      side: order.side,
      quantity: order.quantity,
      status: "PENDING",           // awaiting broker acknowledgement
      filledQty: 0,
      avgPrice: 0,
      brokerId: null,              // not yet assigned by broker
      submittedAt: new Date().toISOString(),
      lastUpdate: new Date().toISOString(),
      brokerAckAt: null,
      filledAt: null,
      failedAt: null,
      failureReason: null,
    };

    this.openOrders.set(tracked.orderId, tracked);
    console.log(`[ExecutionTracker] Order submitted: ${tracked.orderId} (${order.ticker} ${order.side} ${order.quantity})`);
    this.persistOrder(tracked);

    return tracked;
  }

  /**
   * Record broker acknowledgement
   * Broker has accepted order and assigned brokerId
   * But we don't know fill status yet
   */
  recordBrokerAck(orderId, brokerId, brokerStatus, acceptedQty) {
    const order = this.openOrders.get(orderId);
    if (!order) {
      console.warn(`[ExecutionTracker] ACK for unknown order: ${orderId}`);
      return null;
    }

    order.brokerId = brokerId;
    order.brokerAckAt = new Date().toISOString();
    order.status = brokerStatus || "ACCEPTED";  // broker acknowledged
    order.lastUpdate = new Date().toISOString();

    if (acceptedQty < order.quantity) {
      console.warn(`[ExecutionTracker] Partial ACK: ${acceptedQty}/${order.quantity} for ${orderId}`);
    }

    console.log(`[ExecutionTracker] Broker ACK: ${orderId} → broker:${brokerId} (status: ${order.status})`);
    this.persistOrder(order);

    return order;
  }

  /**
   * Record fill confirmation from broker
   * May be partial or full
   */
  recordFill(orderId, filledQty, avgPrice) {
    const order = this.openOrders.get(orderId);
    if (!order) {
      console.error(`[ExecutionTracker] Fill for unknown order: ${orderId}`);
      return null;
    }

    const oldFilledQty = order.filledQty;
    order.filledQty = filledQty;
    order.avgPrice = avgPrice;
    order.lastUpdate = new Date().toISOString();

    // Determine if full or partial
    if (filledQty >= order.quantity) {
      order.status = "FILLED";
      order.filledAt = new Date().toISOString();
      this.completedOrders.push(order);
      this.openOrders.delete(orderId);
      console.log(`[ExecutionTracker] Order FILLED: ${orderId} (${filledQty}@${avgPrice})`);
    } else if (filledQty > 0) {
      order.status = "PARTIAL";
      console.log(`[ExecutionTracker] Partial fill: ${orderId} (${oldFilledQty} → ${filledQty}/${order.quantity})`);
    }

    this.persistOrder(order);
    return order;
  }

  /**
   * Record order failure
   * Broker rejected, cancelled, or execution failed
   */
  recordFailure(orderId, reason) {
    const order = this.openOrders.get(orderId);
    if (!order) {
      console.error(`[ExecutionTracker] Failure for unknown order: ${orderId}`);
      return null;
    }

    order.status = "FAILED";
    order.failedAt = new Date().toISOString();
    order.failureReason = reason;
    order.lastUpdate = new Date().toISOString();

    this.completedOrders.push(order);
    this.openOrders.delete(orderId);

    console.error(`[ExecutionTracker] Order FAILED: ${orderId} (${reason})`);
    this.persistOrder(order);

    return order;
  }

  /**
   * Get current open orders
   * These need broker reconciliation
   */
  getOpenOrders() {
    return Array.from(this.openOrders.values());
  }

  /**
   * Get order by internal ID
   */
  getOrderById(orderId) {
    return this.openOrders.get(orderId) || this.completedOrders.find(o => o.orderId === orderId);
  }

  /**
   * Get order by broker ID
   * Used during reconciliation to match broker state
   */
  getOrderByBrokerId(brokerId) {
    for (const order of this.openOrders.values()) {
      if (order.brokerId === brokerId) return order;
    }
    return null;
  }

  /**
   * Validate order is "really" filled
   * Can only be true if:
   * 1. Broker assigned a brokerId
   * 2. Quantity matches broker's filled amount
   * 3. Status is FILLED
   */
  isReallyFilled(order) {
    return (
      order.brokerId &&
      order.status === "FILLED" &&
      order.filledQty === order.quantity &&
      order.filledAt !== null
    );
  }

  /**
   * Persist order to JSONL log for recovery
   */
  persistOrder(order) {
    try {
      const dir = path.dirname(EXECUTION_LOG_PATH);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      fs.appendFileSync(EXECUTION_LOG_PATH, JSON.stringify(order) + "\n", "utf8");
    } catch (e) {
      console.error(`[ExecutionTracker] Failed to persist order: ${e.message}`);
    }
  }

  /**
   * Load state from disk (recovery on restart)
   */
  loadState() {
    try {
      if (!fs.existsSync(EXECUTION_LOG_PATH)) {
        console.log("[ExecutionTracker] No prior execution state to recover");
        return;
      }

      const lines = fs.readFileSync(EXECUTION_LOG_PATH, "utf8").trim().split("\n").filter(Boolean);
      for (const line of lines) {
        try {
          const order = JSON.parse(line);
          if (order.status !== "FILLED" && order.status !== "FAILED") {
            this.openOrders.set(order.orderId, order);
          } else {
            this.completedOrders.push(order);
          }
        } catch {}
      }

      console.log(`[ExecutionTracker] Recovered state: ${this.openOrders.size} open, ${this.completedOrders.length} completed`);
    } catch (e) {
      console.error(`[ExecutionTracker] Failed to load state: ${e.message}`);
    }
  }

  generateOrderId() {
    return `ORDER_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
  }
}

module.exports = ExecutionStateTracker;
