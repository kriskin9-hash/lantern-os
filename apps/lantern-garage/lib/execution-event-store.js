/**
 * Execution Event Store
 *
 * Immutable append-only log of all execution events.
 * Events are the source of truth - state is derived from them.
 *
 * CRITICAL: This is the financial heartbeat of the system.
 * Every trade decision must be reversible from this log.
 */

"use strict";

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const EVENT_LOG_PATH = path.join(__dirname, "..", "..", "data", "lantern-garage", "trading", "execution-events.jsonl");

class ExecutionEventStore {
  constructor() {
    this.events = [];      // In-memory cache
    this.eventIndex = {};  // eventId -> event lookup
    this.orderIndex = {};  // orderId -> [event, event, ...]
    this.loadFromDisk();
  }

  /**
   * Append an event to the store
   * Events are immutable - this is append-only
   */
  append(event) {
    // Validate event structure
    if (!event.eventId || !event.orderId || !event.type) {
      throw new Error("Invalid event: missing eventId, orderId, or type");
    }

    // Ensure timestamp
    if (!event.timestamp) {
      event.timestamp = Date.now();
    }

    // Check for duplicates (same eventId)
    if (this.eventIndex[event.eventId]) {
      console.warn(`[EventStore] Duplicate event ignored: ${event.eventId}`);
      return false;
    }

    // Append to store
    this.events.push(event);
    this.eventIndex[event.eventId] = event;

    // Index by orderId
    if (!this.orderIndex[event.orderId]) {
      this.orderIndex[event.orderId] = [];
    }
    this.orderIndex[event.orderId].push(event);

    // Persist to disk
    this.persistEvent(event);

    console.log(`[EventStore] Event appended: ${event.type} for order ${event.orderId}`);
    return true;
  }

  /**
   * Get all events for an order
   * Sorted by timestamp (order matters)
   */
  getOrderEvents(orderId) {
    const events = this.orderIndex[orderId] || [];
    // Sort by timestamp to ensure correct order (broker events may arrive out of order)
    return events.sort((a, b) => a.timestamp - b.timestamp);
  }

  /**
   * Get all events of a specific type
   */
  getEventsByType(type) {
    return this.events.filter(e => e.type === type);
  }

  /**
   * Get all events between timestamps
   */
  getEventsBetween(startTime, endTime) {
    return this.events.filter(e => e.timestamp >= startTime && e.timestamp <= endTime);
  }

  /**
   * Get event by ID
   */
  getEventById(eventId) {
    return this.eventIndex[eventId] || null;
  }

  /**
   * Get all events (full history)
   */
  getAllEvents() {
    return [...this.events];
  }

  /**
   * Generate a unique event ID
   */
  static generateEventId() {
    return `EVT_${Date.now()}_${crypto.randomBytes(4).toString("hex")}`;
  }

  /**
   * Persist event to disk (JSONL append)
   */
  persistEvent(event) {
    try {
      const dir = path.dirname(EVENT_LOG_PATH);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      fs.appendFileSync(EVENT_LOG_PATH, JSON.stringify(event) + "\n", "utf8");
    } catch (e) {
      console.error(`[EventStore] Failed to persist event: ${e.message}`);
    }
  }

  /**
   * Load all events from disk
   * Called on startup for recovery
   */
  loadFromDisk() {
    try {
      if (!fs.existsSync(EVENT_LOG_PATH)) {
        console.log("[EventStore] No prior event log to recover");
        return;
      }

      const lines = fs.readFileSync(EVENT_LOG_PATH, "utf8").trim().split("\n").filter(Boolean);
      for (const line of lines) {
        try {
          const event = JSON.parse(line);
          // Replay event into memory
          this.events.push(event);
          this.eventIndex[event.eventId] = event;

          if (!this.orderIndex[event.orderId]) {
            this.orderIndex[event.orderId] = [];
          }
          this.orderIndex[event.orderId].push(event);
        } catch (e) {
          console.warn(`[EventStore] Failed to parse event line: ${e.message}`);
        }
      }

      console.log(`[EventStore] Recovered ${this.events.length} events from disk`);
    } catch (e) {
      console.error(`[EventStore] Failed to load event log: ${e.message}`);
    }
  }

  /**
   * Get event store statistics
   */
  getStats() {
    const eventTypes = {};
    for (const event of this.events) {
      eventTypes[event.type] = (eventTypes[event.type] || 0) + 1;
    }

    return {
      totalEvents: this.events.length,
      totalOrders: Object.keys(this.orderIndex).length,
      eventTypes,
      oldestEvent: this.events[0]?.timestamp,
      newestEvent: this.events[this.events.length - 1]?.timestamp,
    };
  }
}

module.exports = ExecutionEventStore;
