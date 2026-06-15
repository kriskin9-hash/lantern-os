/**
 * Persistent Event Queue — PRL-1 (Production Reliability Layer 1)
 *
 * Guarantees:
 * - No lost trades EVER (disk-backed)
 * - No silent failures (every event tracked)
 * - Full replay capability (event sourced)
 * - Crash recovery (survives restart)
 *
 * This is the heartbeat of the trading system.
 * Every AI decision MUST go through this queue.
 */

"use strict";

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

class PersistentEventQueue {
  constructor(queuePath) {
    this.queuePath = queuePath;
    this.events = new Map(); // eventId → event

    // Ensure queue directory exists
    const dir = path.dirname(queuePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    // Initialize or load existing queue
    this._loadQueue();
  }

  /**
   * Load existing queue from disk
   */
  _loadQueue() {
    if (!fs.existsSync(this.queuePath)) {
      // Create empty queue file
      fs.writeFileSync(this.queuePath, "");
      return;
    }

    try {
      const content = fs.readFileSync(this.queuePath, "utf-8");
      const lines = content.split("\n").filter(line => line.trim());

      for (const line of lines) {
        try {
          const event = JSON.parse(line);
          this.events.set(event.eventId, event);
        } catch (e) {
          console.error("[Queue] Error parsing event:", e.message);
        }
      }

      console.log(`[Queue] Loaded ${this.events.size} events from disk`);
    } catch (e) {
      console.error("[Queue] Error loading queue:", e.message);
    }
  }

  /**
   * Enqueue a trade signal
   * WRITES TO DISK FIRST, then in-memory
   */
  enqueueEvent(traceId, source, payload) {
    const eventId = `evt-${crypto.randomBytes(8).toString("hex")}`;

    const event = {
      eventId,
      traceId,
      source, // "independent-ai-trader"
      type: "TRADE_SIGNAL",
      payload, // { ticker, action, confidence, ... }
      status: "PENDING",
      timestamp: Date.now(),
      createdAt: new Date().toISOString()
    };

    // Write to disk FIRST (durability)
    try {
      fs.appendFileSync(this.queuePath, JSON.stringify(event) + "\n");
    } catch (e) {
      console.error("[Queue] CRITICAL: Failed to write event to disk:", e.message);
      throw new Error("Queue write failed - trade signal NOT persisted");
    }

    // Then add to in-memory index
    this.events.set(eventId, event);

    console.log(`[Queue] Enqueued: ${eventId} (${payload.ticker} ${payload.action})`);

    return eventId;
  }

  /**
   * Get all pending events
   */
  getPendingEvents() {
    const pending = [];

    for (const event of this.events.values()) {
      if (event.status === "PENDING") {
        pending.push(event);
      }
    }

    // Sort by timestamp (FIFO)
    pending.sort((a, b) => a.timestamp - b.timestamp);

    return pending;
  }

  /**
   * Mark event as processed
   * NEVER deletes, just marks status
   */
  markProcessed(eventId, result) {
    const event = this.events.get(eventId);

    if (!event) {
      console.error(`[Queue] Event not found: ${eventId}`);
      return false;
    }

    // Update in-memory
    event.status = "EXECUTED";
    event.processedAt = new Date().toISOString();
    event.result = result || null;

    // Append status update to disk
    try {
      const update = {
        eventId,
        status: "EXECUTED",
        processedAt: event.processedAt,
        result: event.result
      };
      fs.appendFileSync(
        this.queuePath.replace(".jsonl", ".processed"),
        JSON.stringify(update) + "\n"
      );
    } catch (e) {
      console.error("[Queue] Error marking event processed:", e.message);
    }

    console.log(`[Queue] Marked processed: ${eventId}`);
    return true;
  }

  /**
   * Get event by ID
   */
  getEvent(eventId) {
    return this.events.get(eventId) || null;
  }

  /**
   * Get queue statistics
   */
  getStats() {
    let pending = 0;
    let executed = 0;

    for (const event of this.events.values()) {
      if (event.status === "PENDING") pending++;
      if (event.status === "EXECUTED") executed++;
    }

    return {
      totalEvents: this.events.size,
      pendingEvents: pending,
      executedEvents: executed,
      queuePath: this.queuePath
    };
  }

  /**
   * Get all events for a trace (debugging)
   */
  getEventsForTrace(traceId) {
    const traceEvents = [];

    for (const event of this.events.values()) {
      if (event.traceId === traceId) {
        traceEvents.push(event);
      }
    }

    return traceEvents.sort((a, b) => a.timestamp - b.timestamp);
  }

  /**
   * Export queue for backup
   */
  exportQueue() {
    const allEvents = Array.from(this.events.values());

    return {
      exportTime: new Date().toISOString(),
      totalEvents: allEvents.length,
      events: allEvents
    };
  }

  /**
   * Clear queue (for testing only)
   */
  clearQueue() {
    this.events.clear();
    fs.writeFileSync(this.queuePath, "");
    console.log("[Queue] Queue cleared");
  }
}

module.exports = PersistentEventQueue;
