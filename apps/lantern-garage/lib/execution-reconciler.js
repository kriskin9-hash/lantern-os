/**
 * Execution Reconciler
 *
 * Periodic sync with broker to ensure internal state matches reality.
 * Generates events from divergences (immutable audit trail).
 *
 * Detects and corrects:
 * - Orders broker has that we don't know about
 * - Orders we know about that broker has cancelled/failed
 * - Partial fills
 * - Stale order states
 *
 * CRITICAL: This is the gate that prevents state drift.
 */

"use strict";

const BrokerEventNormalizer = require("./broker-event-normalizer");
const ExecutionConflictResolver = require("./execution-conflict-resolver");
const ExecutionEventStore = require("./execution-event-store");

class ExecutionReconciler {
  constructor(tracker, broker, eventStore) {
    this.tracker = tracker;
    this.broker = broker;
    this.eventStore = eventStore;
    this.lastReconcileTime = null;
    this.reconcileInterval = 5000;  // Every 5 seconds
  }

  /**
   * Start periodic reconciliation
   */
  start() {
    console.log(`[ExecutionReconciler] Starting (interval: ${this.reconcileInterval}ms)`);
    this.reconcileTimer = setInterval(() => {
      this.reconcile().catch(e => {
        console.error(`[ExecutionReconciler] Reconciliation failed: ${e.message}`);
      });
    }, this.reconcileInterval);
  }

  /**
   * Stop reconciliation
   */
  stop() {
    if (this.reconcileTimer) {
      clearInterval(this.reconcileTimer);
      this.reconcileTimer = null;
      console.log("[ExecutionReconciler] Stopped");
    }
  }

  /**
   * Main reconciliation loop
   * Compares internal state with broker state
   * Emits events instead of direct mutations
   */
  async reconcile() {
    const startTime = Date.now();
    console.log("[ExecutionReconciler] Starting reconciliation cycle...");

    try {
      // Get current broker state
      const brokerOrders = await this.getBrokerOrders();
      if (!brokerOrders) {
        console.warn("[ExecutionReconciler] Failed to fetch broker orders, skipping reconciliation");
        return;
      }

      // Get our open orders
      const localOrders = this.tracker.getOpenOrders();

      // Check for divergence
      let divergences = 0;
      const events = [];  // Collect events to append

      // 1. Check each local order against broker state
      for (const localOrder of localOrders) {
        if (!localOrder.brokerId) {
          // Order not yet acknowledged by broker, skip for now
          continue;
        }

        const brokerOrder = brokerOrders.find(b => b.id === localOrder.brokerId);

        if (!brokerOrder) {
          // Order was on broker, now it's gone
          console.warn(`[ExecutionReconciler] Missing from broker: ${localOrder.orderId}`);
          divergences++;

          // Emit failure event
          const event = {
            eventId: ExecutionEventStore.generateEventId(),
            orderId: localOrder.orderId,
            type: "ORDER_FAILED",
            timestamp: Date.now(),
            source: "reconciliation",
            reason: "Order missing from broker (likely cancelled)",
          };
          events.push(event);
          continue;
        }

        // Check fill status and collect events
        const orderEvents = this.checkOrderDivergence(localOrder, brokerOrder);
        if (orderEvents.length > 0) {
          events.push(...orderEvents);
          divergences++;
        }
      }

      // 2. Check for orders broker has that we don't know about
      for (const brokerOrder of brokerOrders) {
        const localOrder = this.tracker.getOrderByBrokerId(brokerOrder.id);
        if (!localOrder) {
          console.warn(`[ExecutionReconciler] Unknown broker order: ${brokerOrder.id}`);
          divergences++;
        }
      }

      // Append all events to event store
      for (const event of events) {
        try {
          this.eventStore.append(event);
        } catch (e) {
          console.error(`[ExecutionReconciler] Failed to append event: ${e.message}`);
        }
      }

      const elapsed = Date.now() - startTime;
      console.log(
        `[ExecutionReconciler] Cycle complete: ${divergences} divergences, ` +
        `${events.length} events (${elapsed}ms)`
      );

      this.lastReconcileTime = new Date().toISOString();
    } catch (e) {
      console.error(`[ExecutionReconciler] Reconciliation error: ${e.message}`);
    }
  }

  /**
   * Compare single order's internal vs broker state
   * Returns array of events (empty if no divergence)
   */
  checkOrderDivergence(localOrder, brokerOrder) {
    const events = [];

    // Normalize broker response
    let normalizedStatus;
    try {
      normalizedStatus = BrokerEventNormalizer.normalizeStatus(brokerOrder.status);
    } catch (e) {
      console.warn(`[ExecutionReconciler] Failed to normalize status: ${e.message}`);
      return events;
    }

    // Check status changes
    if (normalizedStatus === "CANCELLED" && localOrder.status !== "FAILED") {
      console.warn(`[ExecutionReconciler] Order was cancelled: ${localOrder.orderId}`);
      events.push({
        eventId: ExecutionEventStore.generateEventId(),
        orderId: localOrder.orderId,
        type: "ORDER_CANCELLED",
        timestamp: Date.now(),
        source: "reconciliation",
        brokerId: brokerOrder.id,
      });
      return events;
    }

    if (normalizedStatus === "FAILED" && localOrder.status !== "FAILED") {
      console.warn(`[ExecutionReconciler] Order failed: ${localOrder.orderId}`);
      events.push({
        eventId: ExecutionEventStore.generateEventId(),
        orderId: localOrder.orderId,
        type: "ORDER_FAILED",
        timestamp: Date.now(),
        source: "reconciliation",
        brokerId: brokerOrder.id,
        reason: brokerOrder.failureReason || "Broker execution failed",
      });
      return events;
    }

    // Extract fill details
    const filledQty = BrokerEventNormalizer.extractFilledQty(brokerOrder);
    const avgPrice = BrokerEventNormalizer.extractAvgPrice(brokerOrder);

    // Check fill quantity divergence
    if (filledQty !== localOrder.filledQty) {
      console.warn(
        `[ExecutionReconciler] Fill divergence: ${localOrder.orderId} ` +
        `(local: ${localOrder.filledQty}, broker: ${filledQty})`
      );

      // Check for conflicts before generating event
      const conflict = ExecutionConflictResolver.checkConflict(
        localOrder,
        {
          type: "ORDER_FILLED",
          filledQty,
          avgPrice,
          timestamp: Date.now(),
        }
      );

      if (!conflict.conflict) {
        events.push({
          eventId: ExecutionEventStore.generateEventId(),
          orderId: localOrder.orderId,
          type: filledQty >= localOrder.quantity ? "ORDER_FILLED" : "FILL_UPDATE",
          timestamp: Date.now(),
          source: "reconciliation",
          brokerId: brokerOrder.id,
          filledQty,
          avgPrice,
        });
      } else {
        console.warn(`[ExecutionReconciler] Conflict detected: ${conflict.issue}`);
      }
    }

    // Check if broker filled but we didn't know
    if (normalizedStatus === "FILLED" && localOrder.status !== "FILLED") {
      console.warn(`[ExecutionReconciler] Order filled on broker but not local: ${localOrder.orderId}`);
      if (filledQty > 0 && avgPrice > 0) {
        events.push({
          eventId: ExecutionEventStore.generateEventId(),
          orderId: localOrder.orderId,
          type: "ORDER_FILLED",
          timestamp: Date.now(),
          source: "reconciliation",
          brokerId: brokerOrder.id,
          filledQty,
          avgPrice,
        });
      }
    }

    return events;
  }

  /**
   * Fetch open orders from broker
   * Implementation depends on broker API
   * Returns null if broker is unavailable
   */
  async getBrokerOrders() {
    try {
      if (!this.broker || !this.broker.getOpenOrders) {
        console.warn("[ExecutionReconciler] Broker API not available");
        return null;
      }

      const orders = await this.broker.getOpenOrders();
      return orders || [];
    } catch (e) {
      console.error(`[ExecutionReconciler] Failed to fetch broker orders: ${e.message}`);
      return null;
    }
  }

  /**
   * Get reconciliation status
   */
  getStatus() {
    return {
      lastReconcileTime: this.lastReconcileTime,
      reconcileInterval: this.reconcileInterval,
      openOrders: this.tracker.getOpenOrders().length,
      running: !!this.reconcileTimer,
    };
  }
}

module.exports = ExecutionReconciler;
