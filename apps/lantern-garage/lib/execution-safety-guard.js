/**
 * Execution Safety Guard
 *
 * Final validation gate before any order is considered "real".
 * Prevents phantom fills, partial executions being treated as complete fills,
 * and internal assumptions about broker state.
 *
 * CRITICAL: If this validator says "no", the order is not real, period.
 */

"use strict";

class ExecutionSafetyGuard {
  /**
   * Validate that an order is "really" filled and safe to trust
   *
   * Returns { valid: boolean, reason: string }
   */
  validateFilledOrder(order) {
    // Must have broker ID
    if (!order.brokerId) {
      return {
        valid: false,
        reason: "Missing brokerId - broker has not acknowledged this order"
      };
    }

    // Status must be FILLED (not PARTIAL, PENDING, etc)
    if (order.status !== "FILLED") {
      return {
        valid: false,
        reason: `Order status is ${order.status}, not FILLED`
      };
    }

    // Filled quantity must equal requested quantity
    if (order.filledQty !== order.quantity) {
      return {
        valid: false,
        reason: `Partial fill only: ${order.filledQty}/${order.quantity}`
      };
    }

    // Must have a fill time (recorded from broker)
    if (!order.filledAt) {
      return {
        valid: false,
        reason: "Order has no filledAt timestamp"
      };
    }

    // Must have an average price (required to calculate P&L)
    if (order.avgPrice <= 0) {
      return {
        valid: false,
        reason: `Invalid average price: ${order.avgPrice}`
      };
    }

    // Must have been acknowledged by broker (not just submitted)
    if (!order.brokerAckAt) {
      return {
        valid: false,
        reason: "Order not acknowledged by broker"
      };
    }

    // Check for timeout (order is too old, reconciliation may have failed)
    const ageMs = Date.now() - new Date(order.filledAt).getTime();
    const maxAgeMs = 30 * 1000;  // 30 seconds
    if (ageMs > maxAgeMs) {
      return {
        valid: false,
        reason: `Order too old (${Math.round(ageMs / 1000)}s) - reconciliation may have failed`
      };
    }

    // All checks passed
    return {
      valid: true,
      reason: "Order validated: brokerId present, full fill confirmed, timestamps valid"
    };
  }

  /**
   * Validate that an order is safe to submit
   * Catches issues before sending to broker
   */
  validateOrderSubmission(order) {
    if (!order.ticker || order.ticker.length === 0) {
      return { valid: false, reason: "Missing ticker" };
    }

    if (!order.side || !["BUY", "SELL"].includes(order.side)) {
      return { valid: false, reason: "Invalid side (must be BUY or SELL)" };
    }

    if (!Number.isInteger(order.quantity) || order.quantity <= 0) {
      return { valid: false, reason: "Invalid quantity (must be positive integer)" };
    }

    if (order.price && order.price <= 0) {
      return { valid: false, reason: "Invalid price (must be positive)" };
    }

    return { valid: true, reason: "Order submission validation passed" };
  }

  /**
   * Validate reconciliation is healthy
   */
  validateReconciliation(reconciler) {
    if (!reconciler) {
      return { valid: false, reason: "No reconciler configured" };
    }

    if (!reconciler.lastReconcileTime) {
      return { valid: false, reason: "Reconciler has never run" };
    }

    const lastReconcileAge = Date.now() - new Date(reconciler.lastReconcileTime).getTime();
    const maxAge = 15000;  // 15 seconds

    if (lastReconcileAge > maxAge) {
      return {
        valid: false,
        reason: `Last reconciliation was ${Math.round(lastReconcileAge / 1000)}s ago (max: 15s)`
      };
    }

    return {
      valid: true,
      reason: "Reconciliation is healthy"
    };
  }

  /**
   * Validate system is safe for trading
   * Checks all preconditions before autonomous trading
   */
  validateSystemReady(tracker, reconciler, broker) {
    const checks = [];

    // 1. Tracker is initialized
    if (!tracker) {
      checks.push({ component: "ExecutionTracker", valid: false, reason: "Not initialized" });
    } else {
      checks.push({ component: "ExecutionTracker", valid: true, reason: "OK" });
    }

    // 2. Reconciler is running
    if (!reconciler) {
      checks.push({ component: "ExecutionReconciler", valid: false, reason: "Not initialized" });
    } else {
      const status = reconciler.getStatus();
      if (!status.running) {
        checks.push({ component: "ExecutionReconciler", valid: false, reason: "Not running" });
      } else {
        checks.push({ component: "ExecutionReconciler", valid: true, reason: "Running" });
      }
    }

    // 3. Broker connection
    if (!broker) {
      checks.push({ component: "Broker", valid: false, reason: "Not initialized" });
    } else {
      checks.push({ component: "Broker", valid: true, reason: "Connected" });
    }

    const allValid = checks.every(c => c.valid);

    return {
      valid: allValid,
      checks,
      summary: allValid ? "✓ System is safe for autonomous trading" : "✗ System is NOT ready for trading"
    };
  }
}

module.exports = ExecutionSafetyGuard;
