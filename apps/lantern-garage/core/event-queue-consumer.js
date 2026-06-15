/**
 * Event Queue Consumer — PRL-1 Heartbeat Loop
 *
 * Continuously:
 * 1. Read pending events from queue
 * 2. Check safety gate (stability index)
 * 3. Check idempotency (not already executed)
 * 4. Submit to Trade State Engine
 * 5. Mark as EXECUTED
 *
 * This is the heartbeat that guarantees execution.
 */

"use strict";

class EventQueueConsumer {
  constructor(queue, idempotency, tradeEngine, stabilityIndex, tracer) {
    this.queue = queue;
    this.idempotency = idempotency;
    this.tradeEngine = tradeEngine;
    this.stabilityIndex = stabilityIndex;
    this.tracer = tracer;

    this.running = false;
    this.processedCount = 0;
    this.skippedCount = 0;
    this.failedCount = 0;
    this.lastProcessTime = Date.now();

    // Consumer loop interval (250ms = 4 events/sec max)
    this.loopInterval = 250;
  }

  /**
   * Start the consumer loop
   */
  start() {
    if (this.running) {
      console.log("[Consumer] Already running");
      return;
    }

    this.running = true;
    console.log("[Consumer] Starting heartbeat loop (250ms interval)");

    this._runLoop();
  }

  /**
   * Stop the consumer loop
   */
  stop() {
    this.running = false;
    console.log("[Consumer] Stopped");
  }

  /**
   * Main consumer loop
   */
  _runLoop() {
    if (!this.running) return;

    try {
      this._processBatch();
    } catch (e) {
      console.error("[Consumer] Loop error:", e.message);
    }

    // Schedule next iteration
    setTimeout(() => this._runLoop(), this.loopInterval);
  }

  /**
   * Process a batch of pending events
   */
  _processBatch() {
    const pending = this.queue.getPendingEvents();

    if (pending.length === 0) {
      return; // No work to do
    }

    console.log(`[Consumer] Processing ${Math.min(pending.length, 10)} of ${pending.length} pending events`);

    // Process up to 10 events per batch (non-blocking)
    for (let i = 0; i < Math.min(pending.length, 10); i++) {
      const event = pending[i];
      this._processEvent(event);
    }

    this.lastProcessTime = Date.now();
  }

  /**
   * Process a single event
   */
  _processEvent(event) {
    const { eventId, payload, traceId } = event;

    // Step 1: Check if already executed (idempotency)
    if (this.idempotency.hasExecuted(eventId)) {
      console.log(`[Consumer] Skipped (already executed): ${eventId}`);
      this.skippedCount++;
      this.queue.markProcessed(eventId, { reason: "already_executed" });
      return;
    }

    // Step 2: Check safety gate
    const stabilityOk = this.stabilityIndex.lastIndex >= 0.8;
    if (!stabilityOk) {
      console.log(`[Consumer] Skipped (low stability): ${eventId} (stability: ${this.stabilityIndex.lastIndex.toFixed(2)})`);
      this.skippedCount++;
      // Don't mark as executed - retry when stability recovers
      return;
    }

    // Step 3: Submit to Trade State Engine
    try {
      const trade = this.tradeEngine.createTrade({
        symbol: payload.ticker,
        side: payload.action.toUpperCase(),
        quantity: payload.quantity || 1,
        price: 0, // Market order
        mode: "paper",
        externalAgent: "independent-ai-trader",
        confidence: payload.confidence,
        strategy: payload.strategy,
        eventId,
        traceId
      });

      // Step 4: Record idempotency
      this.idempotency.recordExecution(eventId, trade.tradeId, {
        status: trade.status,
        timestamp: Date.now()
      });

      // Step 5: Mark queue event as processed
      this.queue.markProcessed(eventId, {
        tradeId: trade.tradeId,
        status: trade.status
      });

      // Step 6: Audit logging
      if (this.tracer) {
        this.tracer.recordTradeExecution(
          traceId,
          trade.tradeId,
          { status: trade.status },
          true
        );
      }

      console.log(`[Consumer] Executed: ${eventId} → ${trade.tradeId} (${payload.ticker} ${payload.action})`);
      this.processedCount++;

    } catch (e) {
      console.error(`[Consumer] Execution error for ${eventId}:`, e.message);
      this.failedCount++;
      this.queue.markProcessed(eventId, { error: e.message });
    }
  }

  /**
   * Get consumer status
   */
  getStatus() {
    const pending = this.queue.getPendingEvents();

    return {
      running: this.running,
      metrics: {
        processed: this.processedCount,
        skipped: this.skippedCount,
        failed: this.failedCount,
        pending: pending.length
      },
      lastProcessTime: new Date(this.lastProcessTime).toISOString(),
      loopInterval: `${this.loopInterval}ms`
    };
  }

  /**
   * Get detailed statistics
   */
  getStats() {
    return {
      status: this.getStatus(),
      queue: this.queue.getStats(),
      idempotency: this.idempotency.getStats()
    };
  }
}

module.exports = EventQueueConsumer;
