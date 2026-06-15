/**
 * Event Sourcing Integration Tests
 *
 * Comprehensive validation that the execution truth resolver layer
 * handles real-world scenarios correctly.
 */

"use strict";

const path = require("path");
const ExecutionEventStore = require("../lib/execution-event-store");
const ExecutionTruthReducer = require("../lib/execution-truth-reducer");
const BrokerEventNormalizer = require("../lib/broker-event-normalizer");
const ExecutionConflictResolver = require("../lib/execution-conflict-resolver");
const ExecutionReplayEngine = require("../lib/execution-replay-engine");

let testsPassed = 0;
let testsFailed = 0;

function assert(condition, message) {
  if (!condition) {
    console.error(`  ✗ FAIL: ${message}`);
    testsFailed++;
  } else {
    testsPassed++;
  }
}

function test(name, fn) {
  console.log(`\n[TEST] ${name}`);
  try {
    fn();
  } catch (e) {
    console.error(`  ✗ EXCEPTION: ${e.message}`);
    testsFailed++;
  }
}

// Test 1: Basic event appending
test("Event store appends and retrieves events", () => {
  const store = new ExecutionEventStore();
  const event = {
    eventId: ExecutionEventStore.generateEventId(),
    orderId: "ORDER_123",
    type: "ORDER_SUBMITTED",
    timestamp: Date.now(),
    ticker: "AAPL",
    side: "BUY",
    quantity: 100,
  };

  const appended = store.append(event);
  assert(appended, "Event appended successfully");

  const retrieved = store.getEventById(event.eventId);
  assert(retrieved !== null, "Event retrieved by ID");
  assert(retrieved.orderId === "ORDER_123", "Order ID matches");
});

// Test 2: Duplicate event detection
test("Event store rejects duplicate events", () => {
  const store = new ExecutionEventStore();
  const uniqueId = `EVT_UNIQUE_${Date.now()}_${Math.random()}`;
  const event = {
    eventId: uniqueId,
    orderId: "ORDER_456",
    type: "ORDER_SUBMITTED",
    timestamp: Date.now(),
  };

  const first = store.append(event);
  assert(first, "First append succeeds");

  // Try appending same event again
  const duplicate = store.append(event);
  assert(!duplicate, "Duplicate event rejected");
});

// Test 3: Truth reducer derives state from events
test("Truth reducer builds order state from events", () => {
  const orderId = "ORDER_DERIVE_1";
  const events = [
    {
      eventId: "E1",
      orderId,
      type: "ORDER_SUBMITTED",
      timestamp: 1000,
      ticker: "TSLA",
      side: "BUY",
      quantity: 50,
    },
    {
      eventId: "E2",
      orderId,
      type: "BROKER_ACK",
      timestamp: 1100,
      brokerId: "BROKER_789",
      brokerStatus: "ACCEPTED",
    },
    {
      eventId: "E3",
      orderId,
      type: "ORDER_FILLED",
      timestamp: 1200,
      filledQty: 50,
      avgPrice: 245.50,
    },
  ];

  const state = ExecutionTruthReducer.deriveOrderState(orderId, events);

  assert(state.ticker === "TSLA", "Ticker extracted from submission event");
  assert(state.status === "FILLED", "Status is FILLED");
  assert(state.brokerId === "BROKER_789", "Broker ID set from ACK event");
  assert(state.filledQty === 50, "Fill quantity correct");
  assert(state.avgPrice === 245.50, "Average price correct");
});

// Test 4: Out-of-order events are handled
test("Truth reducer handles out-of-order events", () => {
  const orderId = "ORDER_OOO";
  const events = [
    {
      eventId: "E1",
      orderId,
      type: "ORDER_SUBMITTED",
      timestamp: 3000,
    },
    // Fill arrives before ACK
    {
      eventId: "E2",
      orderId,
      type: "ORDER_FILLED",
      timestamp: 2500,
      filledQty: 100,
      avgPrice: 123.45,
    },
    // ACK arrives last
    {
      eventId: "E3",
      orderId,
      type: "BROKER_ACK",
      timestamp: 2600,
      brokerId: "BID_999",
    },
  ];

  // Should still work - reducer handles any order
  const state = ExecutionTruthReducer.deriveOrderState(orderId, events);
  assert(state.filledQty === 100, "Fill processed despite out-of-order arrival");
  assert(state.brokerId === "BID_999", "Broker ID set");
});

// Test 5: Conflict detection
test("Conflict resolver detects late fills", () => {
  const state = {
    orderId: "ORDER_LATE",
    status: "FAILED",
    filledQty: 0,
    brokerId: "BROKER_123",  // Must have brokerId to trigger late fill check
  };

  const newEvent = {
    type: "ORDER_FILLED",
    filledQty: 100,
    timestamp: Date.now(),
  };

  const conflict = ExecutionConflictResolver.checkConflict(state, newEvent);
  assert(conflict.conflict, "Conflict detected");
  const lowerIssue = (conflict.issue || "").toLowerCase();
  assert(lowerIssue.includes("after") || lowerIssue.includes("cancel"), `Issue should mention timing: "${conflict.issue}"`);
});

// Test 6: Broker event normalization
test("Broker event normalizer standardizes responses", () => {
  // Simulate different broker response formats
  const brokerResponse1 = {
    id: "BROKER_ORDER_1",
    filled_qty: 75,
    avg_price: 150.25,
    status: "PARTIAL",
  };

  const brokerResponse2 = {
    orderId: "BROKER_ORDER_2",
    filledQty: 75,
    avgPrice: 150.25,
    status: "Partial",
  };

  const qty1 = BrokerEventNormalizer.extractFilledQty(brokerResponse1);
  const qty2 = BrokerEventNormalizer.extractFilledQty(brokerResponse2);
  assert(qty1 === qty2, "Both formats extract same quantity");

  const price1 = BrokerEventNormalizer.extractAvgPrice(brokerResponse1);
  const price2 = BrokerEventNormalizer.extractAvgPrice(brokerResponse2);
  assert(price1 === price2, "Both formats extract same price");

  const status1 = BrokerEventNormalizer.normalizeStatus(brokerResponse1.status);
  const status2 = BrokerEventNormalizer.normalizeStatus(brokerResponse2.status);
  assert(status1 === status2, "Both formats normalize to same status");
});

// Test 7: Replay engine determinism
test("Replay engine produces deterministic results", () => {
  const store = new ExecutionEventStore();

  // Populate with events
  const uniquePrefix = Date.now();
  const orderId = `ORDER_DET_${uniquePrefix}`;
  const events = [
    {
      eventId: `E1_${uniquePrefix}`,
      orderId,
      type: "ORDER_SUBMITTED",
      timestamp: 5000,
      ticker: "SPY",
      side: "SELL",
      quantity: 200,
    },
    {
      eventId: `E2_${uniquePrefix}`,
      orderId,
      type: "BROKER_ACK",
      timestamp: 5100,
      brokerId: "BID_111",
    },
    {
      eventId: `E3_${uniquePrefix}`,
      orderId,
      type: "ORDER_FILLED",
      timestamp: 5200,
      filledQty: 200,
      avgPrice: 445.60,
    },
  ];

  for (const event of events) {
    store.append(event);
  }

  const replay = new ExecutionReplayEngine(store);

  // Derive state first time
  const result1 = replay.replayOrder(orderId);
  assert(result1.success, "First replay succeeds");

  // Derive state second time
  const result2 = replay.replayOrder(orderId);
  assert(result2.success, "Second replay succeeds");

  // Compare hashes
  const hash1 = ExecutionTruthReducer.hashOrderState(result1.order);
  const hash2 = ExecutionTruthReducer.hashOrderState(result2.order);
  assert(hash1 === hash2, "Replay is deterministic (same hash)");
});

// Test 8: Multiple orders in event store
test("Event store manages multiple orders correctly", () => {
  const store = new ExecutionEventStore();

  // Add events for 3 different orders with unique IDs
  const baselineStats = store.getStats();
  const baselineEvents = baselineStats.totalEvents;
  const baselineOrders = baselineStats.totalOrders;

  const uniquePrefix = Date.now();
  for (let i = 1; i <= 3; i++) {
    store.append({
      eventId: `E_${uniquePrefix}_${i}`,
      orderId: `ORDER_${uniquePrefix}_${i}`,
      type: "ORDER_SUBMITTED",
      timestamp: i * 1000,
    });
  }

  const stats = store.getStats();
  const newEvents = stats.totalEvents - baselineEvents;
  const newOrders = stats.totalOrders - baselineOrders;

  assert(newEvents === 3, `3 new events stored (got ${newEvents})`);
  assert(newOrders === 3, `3 new orders tracked (got ${newOrders})`);
});

// Test 9: Event validation
test("Event stream validation catches issues", () => {
  const validEvents = [
    {
      eventId: "E1",
      orderId: "O1",
      type: "ORDER_SUBMITTED",
      timestamp: 1000,
    },
    {
      eventId: "E2",
      orderId: "O1",
      type: "ORDER_FILLED",
      timestamp: 2000,
      filledQty: 100,
      avgPrice: 100,
    },
  ];

  const validation = ExecutionTruthReducer.validateEventStream(validEvents);
  assert(validation.valid, "Valid event stream passes");

  const invalidEvents = [
    {
      eventId: "E1",
      orderId: "O1",
      // Missing type
      timestamp: 1000,
    },
  ];

  const invalidValidation = ExecutionTruthReducer.validateEventStream(invalidEvents);
  assert(!invalidValidation.valid, "Invalid event stream detected");
});

// Test 10: Status transitions with history tracking
test("Order state tracks status transition history", () => {
  const orderId = "ORDER_HIST";
  const events = [
    {
      eventId: "E1",
      orderId,
      type: "ORDER_SUBMITTED",
      timestamp: 1000,
      ticker: "NVDA",
      side: "BUY",
      quantity: 75,
    },
    {
      eventId: "E2",
      orderId,
      type: "BROKER_ACK",
      timestamp: 1100,
      brokerId: "BID_777",
      brokerStatus: "ACCEPTED",
    },
    {
      eventId: "E3",
      orderId,
      type: "FILL_UPDATE",
      timestamp: 1200,
      filledQty: 40,
      avgPrice: 890.50,
    },
    {
      eventId: "E4",
      orderId,
      type: "ORDER_FILLED",
      timestamp: 1300,
      filledQty: 75,
      avgPrice: 891.20,
    },
  ];

  const state = ExecutionTruthReducer.deriveOrderState(orderId, events);
  assert(state.history.length > 0, "Status transitions recorded");
  assert(state.history.some(h => h.to === "PARTIAL"), "Partial fill status recorded");
  assert(state.history.some(h => h.to === "FILLED"), "Final fill status recorded");
});

// Summary
console.log("\n" + "=".repeat(60));
console.log(`Test Results: ${testsPassed} passed, ${testsFailed} failed`);
console.log("=".repeat(60));

if (testsFailed > 0) {
  process.exit(1);
}
