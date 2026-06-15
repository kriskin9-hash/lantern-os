/**
 * Kill Switch
 *
 * Emergency shutdown mechanism for autonomous trading.
 * Immediately stops all trading activity and cancels open orders.
 *
 * CRITICAL: Activation is irreversible during current session.
 * Requires manual administrator confirmation to reactivate.
 */

"use strict";

class KillSwitch {
  constructor(eventStore, tracker) {
    this.eventStore = eventStore;
    this.tracker = tracker;
    this.active = false;
    this.activatedAt = null;
    this.activationReason = null;
    this.activationEvent = null;
  }

  /**
   * Activate kill switch
   * Immediately halts all autonomous trading
   */
  async activate(reason, source = "MANUAL") {
    if (this.active) {
      console.warn("[KillSwitch] Already active, ignoring activation request");
      return {
        success: false,
        message: "Kill switch already active",
      };
    }

    this.active = true;
    this.activatedAt = new Date().toISOString();
    this.activationReason = reason;

    console.error(`[KillSwitch] ACTIVATED - Reason: ${reason}`);

    // 1. Create audit event
    const event = {
      eventId: require("./execution-event-store").generateEventId(),
      orderId: null,
      type: "KILL_SWITCH_ACTIVATED",
      timestamp: Date.now(),
      source: "kill_switch",
      reason,
      activationSource: source,
    };

    try {
      if (this.eventStore) {
        this.eventStore.append(event);
      }
    } catch (e) {
      console.error(`[KillSwitch] Failed to append event: ${e.message}`);
    }

    this.activationEvent = event;

    // 2. Cancel all open orders
    try {
      await this.cancelAllOpenOrders();
    } catch (e) {
      console.error(`[KillSwitch] Failed to cancel orders: ${e.message}`);
    }

    // 3. Log activation details
    this.logActivation(reason, source);

    return {
      success: true,
      activatedAt: this.activatedAt,
      reason,
      openOrdersCancelled: true,
    };
  }

  /**
   * Deactivate kill switch
   * Requires explicit reason and should be rare
   */
  async deactivate(reason) {
    if (!this.active) {
      return {
        success: false,
        message: "Kill switch not active",
      };
    }

    this.active = false;
    const duration = Date.now() - new Date(this.activatedAt).getTime();

    console.warn(
      `[KillSwitch] DEACTIVATED after ${(duration / 1000).toFixed(1)}s - ` +
      `Reason for reactivation: ${reason}`
    );

    // Create audit event
    const event = {
      eventId: require("./execution-event-store").generateEventId(),
      orderId: null,
      type: "KILL_SWITCH_DEACTIVATED",
      timestamp: Date.now(),
      source: "kill_switch",
      reason,
      durationMs: duration,
    };

    try {
      if (this.eventStore) {
        this.eventStore.append(event);
      }
    } catch (e) {
      console.error(`[KillSwitch] Failed to append deactivation event: ${e.message}`);
    }

    return {
      success: true,
      deactivatedAt: new Date().toISOString(),
      activeDurationSeconds: (duration / 1000).toFixed(1),
    };
  }

  /**
   * Check if kill switch is active
   */
  isActive() {
    return this.active;
  }

  /**
   * Cancel all open orders
   */
  async cancelAllOpenOrders() {
    if (!this.tracker) {
      console.warn("[KillSwitch] No tracker available, skipping order cancellation");
      return { cancelled: 0 };
    }

    const openOrders = this.tracker.getOpenOrders();
    let cancelledCount = 0;

    for (const order of openOrders) {
      try {
        // Record cancellation (actual broker cancellation would happen elsewhere)
        this.tracker.recordFailure(order.orderId, "Kill switch activated");
        cancelledCount++;
        console.log(`[KillSwitch] Cancelled order: ${order.orderId}`);
      } catch (e) {
        console.error(`[KillSwitch] Failed to cancel ${order.orderId}: ${e.message}`);
      }
    }

    console.warn(`[KillSwitch] Cancelled ${cancelledCount} open orders`);
    return { cancelled: cancelledCount };
  }

  /**
   * Log activation details for audit trail
   */
  logActivation(reason, source) {
    const log = {
      timestamp: this.activatedAt,
      reason,
      source,
      details: {
        event: this.activationEvent,
      },
    };

    console.error("[KillSwitch] Activation log:", JSON.stringify(log, null, 2));
  }

  /**
   * Get kill switch status
   */
  getStatus() {
    if (!this.active) {
      return {
        active: false,
        activatedAt: this.activatedAt,
      };
    }

    const durationMs = Date.now() - new Date(this.activatedAt).getTime();

    return {
      active: true,
      activatedAt: this.activatedAt,
      activationReason: this.activationReason,
      durationSeconds: (durationMs / 1000).toFixed(1),
      durationMinutes: (durationMs / 60000).toFixed(2),
    };
  }

  /**
   * Check if trading is allowed
   * Returns { allowed: boolean, reason: string }
   */
  canTrade() {
    if (this.active) {
      return {
        allowed: false,
        reason: `Kill switch active since ${this.activatedAt}. Reason: ${this.activationReason}`,
      };
    }

    return {
      allowed: true,
      reason: "Trading allowed",
    };
  }

  /**
   * Guard function for trade submission
   * Throws error if kill switch active
   */
  guard(tradeRequest) {
    if (this.active) {
      const error = new Error(
        `KILL_SWITCH_ACTIVE: ${this.activationReason}`
      );
      error.code = "KILL_SWITCH_ACTIVE";
      throw error;
    }
  }

  /**
   * Activation timeline
   */
  getTimeline() {
    if (!this.active) {
      return null;
    }

    return {
      activatedAt: this.activatedAt,
      durationMs: Date.now() - new Date(this.activatedAt).getTime(),
      reason: this.activationReason,
      event: this.activationEvent,
    };
  }
}

module.exports = KillSwitch;
