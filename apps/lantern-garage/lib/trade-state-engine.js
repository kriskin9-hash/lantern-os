/**
 * Trade State Engine — Single Source of Truth for All Trade Lifecycle
 *
 * Centralizes:
 * - Trade state tracking (PENDING → SUBMITTED → FILLED/REJECTED)
 * - Response normalization (convert any broker response to standard format)
 * - State transition enforcement (no invalid transitions)
 * - Event emission (trade:created, trade:updated, trade:filled, etc.)
 * - Cache layer feeding (all endpoints read from engine, not broker APIs)
 *
 * This eliminates UI↔backend desync, duplicate state sources, and race conditions.
 */

"use strict";

const EventEmitter = require("events");

// Trade states — explicit lifecycle
const TRADE_STATES = {
  PENDING: "pending",           // Just created, not submitted yet
  SUBMITTED: "submitted",       // Sent to broker, awaiting confirmation
  FILLED: "filled",             // Fully executed
  PARTIALLY_FILLED: "partially_filled",
  REJECTED: "rejected",         // Broker rejected
  CANCELLED: "cancelled",       // User cancelled
  FAILED: "failed"              // Execution error
};

// Valid state transitions (prevents impossible sequences)
const VALID_TRANSITIONS = {
  [TRADE_STATES.PENDING]: [TRADE_STATES.SUBMITTED, TRADE_STATES.REJECTED, TRADE_STATES.FAILED],
  [TRADE_STATES.SUBMITTED]: [TRADE_STATES.FILLED, TRADE_STATES.PARTIALLY_FILLED, TRADE_STATES.REJECTED, TRADE_STATES.CANCELLED, TRADE_STATES.FAILED],
  [TRADE_STATES.PARTIALLY_FILLED]: [TRADE_STATES.FILLED, TRADE_STATES.CANCELLED, TRADE_STATES.FAILED],
  [TRADE_STATES.FILLED]: [], // Terminal state
  [TRADE_STATES.REJECTED]: [], // Terminal state
  [TRADE_STATES.CANCELLED]: [], // Terminal state
  [TRADE_STATES.FAILED]: [] // Terminal state
};

class TradeStateEngine extends EventEmitter {
  constructor() {
    super();
    this.trades = new Map(); // tradeId → normalized trade object
    this.orderIdToTradeId = new Map(); // orderId → tradeId (for lookups)
    this.recentTrades = []; // For UI: last N trades
    this.maxRecentTrades = 100;

    // Phase 2.5: Event ordering & dedup
    this.eventSequence = 0; // Monotonic counter for event ordering
    this.tradeEventSequence = new Map(); // tradeId → last event sequence number
    this.tradeEventHashes = new Map(); // tradeId → last event hash (for dedup)
    this.eventQueue = []; // Queued events awaiting processing
  }

  /**
   * Normalize any broker response into standard format
   */
  _normalize(input) {
    if (!input) return null;

    // Handle different broker response formats
    let trade = {
      tradeId: input.tradeId || input.id || input.orderId || `trade_${Date.now()}_${Math.random()}`,
      symbol: input.symbol || input.ticker || input.market_ticker || "",
      side: (input.side || input.action || "").toUpperCase(),
      status: (input.status || "").toLowerCase(),
      price: parseFloat(input.price || input.limitCents || 0) / 100 || 0,
      quantity: parseInt(input.quantity || input.count || input.qty || 0),
      filledQuantity: parseInt(input.filledQuantity || input.filled_qty || 0),
      timestamp: input.timestamp ? new Date(input.timestamp).getTime() : Date.now(),
      submittedAt: input.submittedAt ? new Date(input.submittedAt).getTime() : null,
      filledAt: input.filledAt ? new Date(input.filledAt).getTime() : null,
      error: input.error || null,
      brokerStatus: input.brokerStatus || null,
      mode: input.mode || "live" // "dry_run" or "live"
    };

    // Map any broker status to our standard states
    trade.status = this._mapBrokerStatusToEngineState(trade.status, trade.mode);

    return trade;
  }

  /**
   * Map broker-specific statuses to engine states
   */
  _mapBrokerStatusToEngineState(brokerStatus, mode) {
    if (mode === "dry_run") return TRADE_STATES.PENDING;

    const lower = (brokerStatus || "").toLowerCase();
    if (lower.includes("pending") || lower === "submitted") return TRADE_STATES.SUBMITTED;
    if (lower.includes("filled") || lower.includes("complete")) return TRADE_STATES.FILLED;
    if (lower.includes("partial")) return TRADE_STATES.PARTIALLY_FILLED;
    if (lower.includes("reject") || lower.includes("denied")) return TRADE_STATES.REJECTED;
    if (lower.includes("cancel")) return TRADE_STATES.CANCELLED;
    if (lower.includes("fail") || lower.includes("error")) return TRADE_STATES.FAILED;

    return TRADE_STATES.SUBMITTED; // Default to submitted
  }

  /**
   * Validate state transition
   */
  _isValidTransition(fromState, toState) {
    const valid = VALID_TRANSITIONS[fromState] || [];
    return valid.includes(toState);
  }

  /**
   * Create a new trade (enters PENDING state)
   */
  createTrade(input) {
    const trade = this._normalize(input);
    if (!trade) throw new Error("Invalid trade input");

    trade.status = TRADE_STATES.PENDING;
    trade.createdAt = Date.now();

    this.trades.set(trade.tradeId, trade);
    if (input.orderId) {
      this.orderIdToTradeId.set(input.orderId, trade.tradeId);
    }

    this._addToRecent(trade);
    this.emit("trade:created", trade);

    return trade;
  }

  /**
   * Update trade status (enforces valid transitions)
   */
  updateTradeStatus(tradeId, newStatus, details = {}) {
    const trade = this.trades.get(tradeId);
    if (!trade) throw new Error(`Trade not found: ${tradeId}`);

    const oldStatus = trade.status;
    newStatus = newStatus.toLowerCase();

    // Validate transition
    if (!this._isValidTransition(oldStatus, newStatus)) {
      const err = new Error(`Invalid transition: ${oldStatus} → ${newStatus}`);
      this.emit("trade:error", { tradeId, error: err.message });
      throw err;
    }

    // Update trade
    trade.status = newStatus;
    trade.updatedAt = Date.now();
    Object.assign(trade, details);

    this._addToRecent(trade);

    // Emit specific events for state changes
    this.emit("trade:updated", trade);
    if (newStatus === TRADE_STATES.FILLED) {
      this.emit("trade:filled", trade);
    } else if (newStatus === TRADE_STATES.REJECTED) {
      this.emit("trade:rejected", trade);
    } else if (newStatus === TRADE_STATES.CANCELLED) {
      this.emit("trade:cancelled", trade);
    }

    return trade;
  }

  /**
   * Record a broker response (normalizes → updates state)
   */
  recordBrokerResponse(input) {
    const normalized = this._normalize(input);
    if (!normalized) return null;

    let trade = this.trades.get(normalized.tradeId);

    if (!trade) {
      // New trade from broker response
      trade = this.createTrade(normalized);
    } else {
      // Update existing trade
      const newStatus = normalized.status;
      this.updateTradeStatus(trade.tradeId, newStatus, normalized);
    }

    return trade;
  }

  /**
   * Get trade by ID
   */
  getTrade(tradeId) {
    return this.trades.get(tradeId) || null;
  }

  /**
   * Get trade by order ID (for lookups from broker)
   */
  getTradeByOrderId(orderId) {
    const tradeId = this.orderIdToTradeId.get(orderId);
    return tradeId ? this.trades.get(tradeId) : null;
  }

  /**
   * Get all trades in a given state
   */
  getTradesByStatus(status) {
    const result = [];
    for (const trade of this.trades.values()) {
      if (trade.status === status) result.push(trade);
    }
    return result;
  }

  /**
   * Get open positions (SUBMITTED, PARTIALLY_FILLED, FILLED)
   */
  getOpenPositions() {
    const openStates = [TRADE_STATES.SUBMITTED, TRADE_STATES.PARTIALLY_FILLED, TRADE_STATES.FILLED];
    const result = [];
    for (const trade of this.trades.values()) {
      if (openStates.includes(trade.status)) result.push(trade);
    }
    return result;
  }

  /**
   * Get recent trades (for UI)
   */
  getRecent(limit = 50) {
    return this.recentTrades.slice(-limit).reverse();
  }

  /**
   * Get full engine state snapshot
   */
  getState() {
    return {
      openPositions: this.getOpenPositions(),
      recentTrades: this.getRecent(20),
      totalTrades: this.trades.size,
      activeCount: this.getTradesByStatus(TRADE_STATES.SUBMITTED).length + this.getTradesByStatus(TRADE_STATES.PARTIALLY_FILLED).length,
      filledCount: this.getTradesByStatus(TRADE_STATES.FILLED).length,
      rejectedCount: this.getTradesByStatus(TRADE_STATES.REJECTED).length,
      timestamp: Date.now()
    };
  }

  /**
   * Internal: add to recent trades list (keeps bounded)
   */
  _addToRecent(trade) {
    this.recentTrades.push(trade);
    if (this.recentTrades.length > this.maxRecentTrades) {
      this.recentTrades.shift();
    }
  }

  /**
   * Phase 2.5: Check for duplicate/stale events
   */
  _isDuplicateEvent(tradeId, eventHash) {
    const lastHash = this.tradeEventHashes.get(tradeId);
    return lastHash === eventHash;
  }

  /**
   * Phase 2.5: Get next monotonic event sequence number
   */
  _nextEventSequence() {
    return ++this.eventSequence;
  }

  /**
   * Phase 2.5: Validate trade state consistency
   */
  validateTradeState(tradeId) {
    const trade = this.trades.get(tradeId);
    if (!trade) return { valid: true, message: "Trade not found" };

    // Validate state is in known set
    if (!Object.values(TRADE_STATES).includes(trade.status)) {
      return { valid: false, message: `Unknown state: ${trade.status}` };
    }

    // Validate quantities
    if (trade.filledQuantity > trade.quantity) {
      return { valid: false, message: "Filled quantity exceeds total quantity" };
    }

    // Validate terminal states have timestamps
    if (
      [TRADE_STATES.FILLED, TRADE_STATES.REJECTED, TRADE_STATES.CANCELLED].includes(trade.status) &&
      !trade.filledAt &&
      !trade.error
    ) {
      return { valid: false, message: "Terminal state missing completion details" };
    }

    return { valid: true, message: "State valid" };
  }

  /**
   * Phase 2.5: Full engine integrity check
   */
  validateEngineIntegrity() {
    const issues = [];

    // Check for orphaned orders
    for (const [orderId, tradeId] of this.orderIdToTradeId.entries()) {
      if (!this.trades.has(tradeId)) {
        issues.push(`Orphan order mapping: ${orderId} → ${tradeId}`);
      }
    }

    // Check for invalid states
    for (const [tradeId, trade] of this.trades.entries()) {
      const validation = this.validateTradeState(tradeId);
      if (!validation.valid) {
        issues.push(`Trade ${tradeId}: ${validation.message}`);
      }
    }

    // Check for duplicates in terminal states
    const filled = new Set();
    for (const trade of this.trades.values()) {
      if (trade.status === TRADE_STATES.FILLED && trade.tradeId) {
        if (filled.has(trade.tradeId)) {
          issues.push(`Duplicate filled trade: ${trade.tradeId}`);
        }
        filled.add(trade.tradeId);
      }
    }

    return {
      valid: issues.length === 0,
      issues,
      tradeCount: this.trades.size,
      timestamp: Date.now()
    };
  }

  /**
   * Phase 2.5: Get engine health snapshot
   */
  getHealth() {
    const integrity = this.validateEngineIntegrity();
    return {
      status: integrity.valid ? "healthy" : "degraded",
      activeTrades: this.getOpenPositions().length,
      totalTrades: this.trades.size,
      eventQueueDepth: this.eventQueue.length,
      eventSequence: this.eventSequence,
      lastReconciliation: this.lastReconciliationTime || null,
      issues: integrity.issues,
      timestamp: Date.now()
    };
  }

  /**
   * Phase 2.5: Reconcile state (after restart or consistency check)
   */
  reconcileState() {
    const before = this.trades.size;
    const validation = this.validateEngineIntegrity();

    if (!validation.valid) {
      console.warn("[TradeStateEngine] Reconciliation found issues:", validation.issues);
    }

    this.lastReconciliationTime = Date.now();

    return {
      success: validation.valid,
      tradesBefore: before,
      tradesAfter: this.trades.size,
      issues: validation.issues,
      timestamp: this.lastReconciliationTime
    };
  }

  /**
   * Clear all state (for testing)
   */
  clear() {
    this.trades.clear();
    this.orderIdToTradeId.clear();
    this.recentTrades = [];
    this.eventSequence = 0;
    this.tradeEventSequence.clear();
    this.tradeEventHashes.clear();
    this.eventQueue = [];
    this.lastReconciliationTime = null;
  }
}

module.exports = {
  TradeStateEngine,
  TRADE_STATES
};
