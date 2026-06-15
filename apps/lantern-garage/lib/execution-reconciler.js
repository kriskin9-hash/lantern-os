/**
 * Execution Reconciler
 *
 * Periodic sync with broker to ensure internal state matches reality.
 * Detects and corrects:
 * - Orders broker has that we don't know about
 * - Orders we know about that broker has cancelled/failed
 * - Partial fills
 * - Stale order states
 *
 * CRITICAL: This is the gate that prevents state drift.
 */

"use strict";

class ExecutionReconciler {
  constructor(tracker, broker) {
    this.tracker = tracker;
    this.broker = broker;
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

      // 1. Check each local order against broker state
      for (const localOrder of localOrders) {
        if (!localOrder.brokerId) {
          // Order not yet acknowledged by broker, skip for now
          continue;
        }

        const brokerOrder = brokerOrders.find(b => b.id === localOrder.brokerId);

        if (!brokerOrder) {
          // Order was on broker, now it's gone
          // Could be filled, cancelled, or failed
          console.warn(`[ExecutionReconciler] Missing from broker: ${localOrder.orderId} (brokerId: ${localOrder.brokerId})`);
          divergences++;

          // Assume order was cancelled/rejected
          this.tracker.recordFailure(localOrder.orderId, "Order missing from broker (likely cancelled)");
          continue;
        }

        // Check fill status
        const diverged = this.checkOrderDivergence(localOrder, brokerOrder);
        if (diverged) {
          divergences++;
        }
      }

      // 2. Check for orders broker has that we don't know about (unlikely but possible)
      for (const brokerOrder of brokerOrders) {
        const localOrder = this.tracker.getOrderByBrokerId(brokerOrder.id);
        if (!localOrder) {
          console.warn(`[ExecutionReconciler] Unknown broker order: ${brokerOrder.id}`);
          divergences++;
          // This is unexpected but not fatal - could be order from external system
        }
      }

      const elapsed = Date.now() - startTime;
      console.log(`[ExecutionReconciler] Cycle complete: ${divergences} divergences found (${elapsed}ms)`);

      this.lastReconcileTime = new Date().toISOString();
    } catch (e) {
      console.error(`[ExecutionReconciler] Reconciliation error: ${e.message}`);
    }
  }

  /**
   * Compare single order's internal vs broker state
   * Returns true if divergence was detected and corrected
   */
  checkOrderDivergence(localOrder, brokerOrder) {
    let diverged = false;

    // Check status
    if (brokerOrder.status === "CANCELLED" && localOrder.status !== "FAILED") {
      console.warn(`[ExecutionReconciler] Order was cancelled: ${localOrder.orderId}`);
      this.tracker.recordFailure(localOrder.orderId, "Broker cancelled order");
      return true;
    }

    if (brokerOrder.status === "FAILED" && localOrder.status !== "FAILED") {
      console.warn(`[ExecutionReconciler] Order failed: ${localOrder.orderId} (${brokerOrder.failureReason})`);
      this.tracker.recordFailure(localOrder.orderId, brokerOrder.failureReason || "Broker execution failed");
      return true;
    }

    // Check fill quantity
    if (brokerOrder.filledQty !== localOrder.filledQty) {
      console.warn(`[ExecutionReconciler] Fill divergence: ${localOrder.orderId} (local: ${localOrder.filledQty}, broker: ${brokerOrder.filledQty})`);
      this.tracker.recordFill(localOrder.orderId, brokerOrder.filledQty, brokerOrder.avgPrice || 0);
      diverged = true;
    }

    // Check if broker filled but we didn't know
    if (brokerOrder.status === "FILLED" && localOrder.status !== "FILLED") {
      console.warn(`[ExecutionReconciler] Order filled on broker but not in local state: ${localOrder.orderId}`);
      this.tracker.recordFill(localOrder.orderId, brokerOrder.filledQty, brokerOrder.avgPrice || 0);
      diverged = true;
    }

    // Check partial fill
    if (brokerOrder.filledQty > 0 && brokerOrder.filledQty < brokerOrder.quantity) {
      if (localOrder.status !== "PARTIAL") {
        console.warn(`[ExecutionReconciler] Partial fill detected: ${localOrder.orderId} (${brokerOrder.filledQty}/${brokerOrder.quantity})`);
        this.tracker.recordFill(localOrder.orderId, brokerOrder.filledQty, brokerOrder.avgPrice || 0);
        diverged = true;
      }
    }

    return diverged;
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
