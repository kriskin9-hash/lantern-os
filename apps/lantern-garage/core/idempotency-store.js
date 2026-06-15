/**
 * Idempotency Store — PRL-1 Duplicate Prevention
 *
 * Guarantees:
 * - Every eventId executed exactly once
 * - Safe against replay
 * - Safe against restart
 * - Safe against re-emission
 */

"use strict";

const fs = require("fs");
const path = require("path");

class IdempotencyStore {
  constructor(storePath) {
    this.storePath = storePath;
    this.executedEvents = new Map(); // eventId → result

    // Ensure directory exists
    const dir = path.dirname(storePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    // Load existing records
    this._loadStore();
  }

  /**
   * Load idempotency records from disk
   */
  _loadStore() {
    if (!fs.existsSync(this.storePath)) {
      fs.writeFileSync(this.storePath, "");
      return;
    }

    try {
      const content = fs.readFileSync(this.storePath, "utf-8");
      const lines = content.split("\n").filter(line => line.trim());

      for (const line of lines) {
        try {
          const record = JSON.parse(line);
          this.executedEvents.set(record.eventId, record);
        } catch (e) {
          console.error("[Idempotency] Parse error:", e.message);
        }
      }

      console.log(`[Idempotency] Loaded ${this.executedEvents.size} executed events`);
    } catch (e) {
      console.error("[Idempotency] Load error:", e.message);
    }
  }

  /**
   * Check if event has already been executed
   */
  hasExecuted(eventId) {
    return this.executedEvents.has(eventId);
  }

  /**
   * Record event execution
   * WRITES TO DISK for durability
   */
  recordExecution(eventId, tradeId, result) {
    // Check if already executed
    if (this.executedEvents.has(eventId)) {
      console.log(`[Idempotency] Event already executed: ${eventId}`);
      return false; // Already done
    }

    const record = {
      eventId,
      tradeId,
      result: result || null,
      executedAt: new Date().toISOString(),
      timestamp: Date.now()
    };

    // Write to disk FIRST
    try {
      fs.appendFileSync(this.storePath, JSON.stringify(record) + "\n");
    } catch (e) {
      console.error("[Idempotency] CRITICAL: Failed to write execution record:", e.message);
      throw new Error("Idempotency record write failed");
    }

    // Then add to in-memory
    this.executedEvents.set(eventId, record);

    console.log(`[Idempotency] Recorded: ${eventId} → ${tradeId}`);
    return true;
  }

  /**
   * Get execution record
   */
  getExecution(eventId) {
    return this.executedEvents.get(eventId) || null;
  }

  /**
   * Get all executions for a trade
   */
  getExecutionsForTrade(tradeId) {
    const executions = [];

    for (const record of this.executedEvents.values()) {
      if (record.tradeId === tradeId) {
        executions.push(record);
      }
    }

    return executions;
  }

  /**
   * Get statistics
   */
  getStats() {
    return {
      totalExecuted: this.executedEvents.size,
      storePath: this.storePath
    };
  }

  /**
   * Export for backup
   */
  exportStore() {
    const allRecords = Array.from(this.executedEvents.values());

    return {
      exportTime: new Date().toISOString(),
      totalRecords: allRecords.length,
      records: allRecords
    };
  }

  /**
   * Clear store (testing only)
   */
  clearStore() {
    this.executedEvents.clear();
    fs.writeFileSync(this.storePath, "");
    console.log("[Idempotency] Store cleared");
  }
}

module.exports = IdempotencyStore;
