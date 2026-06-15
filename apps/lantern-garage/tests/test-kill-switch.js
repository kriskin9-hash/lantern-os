/**
 * Kill Switch Tests
 *
 * Validates that the kill switch correctly halts trading
 * and records activation events.
 */

"use strict";

const KillSwitch = require("../lib/kill-switch");

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

// Mock event store
class MockEventStore {
  constructor() {
    this.events = [];
  }

  append(event) {
    this.events.push(event);
    return true;
  }

  getEvents() {
    return this.events;
  }
}

// Mock tracker
class MockTracker {
  constructor() {
    this.orders = [
      { orderId: "ORDER_1", status: "PENDING" },
      { orderId: "ORDER_2", status: "ACCEPTED" },
    ];
    this.cancelledOrders = [];
  }

  getOpenOrders() {
    return this.orders.filter(o => o.status !== "FAILED");
  }

  recordFailure(orderId, reason) {
    const order = this.orders.find(o => o.orderId === orderId);
    if (order) {
      order.status = "FAILED";
      this.cancelledOrders.push({ orderId, reason });
    }
  }
}

// Test 1: Activate kill switch
test("Kill switch activation", async () => {
  const eventStore = new MockEventStore();
  const tracker = new MockTracker();
  const killSwitch = new KillSwitch(eventStore, tracker);

  assert(!killSwitch.isActive(), "Kill switch initially inactive");

  const result = await killSwitch.activate("Test activation");

  assert(killSwitch.isActive(), "Kill switch now active");
  assert(result.success, "Activation successful");
  assert(result.activatedAt, "Activation timestamp recorded");
});

// Test 2: Reject duplicate activation
test("Kill switch rejects duplicate activation", async () => {
  const eventStore = new MockEventStore();
  const killSwitch = new KillSwitch(eventStore);

  await killSwitch.activate("First activation");
  const result = await killSwitch.activate("Second activation");

  assert(!result.success, "Second activation rejected");
});

// Test 3: Guard function blocks trading
test("Kill switch guard blocks trades", () => {
  const killSwitch = new KillSwitch();

  const tradeRequest = { ticker: "AAPL", side: "BUY", quantity: 10 };

  // Trade should work before activation
  try {
    killSwitch.guard(tradeRequest);
    assert(true, "Trade allowed before activation");
  } catch (e) {
    assert(false, "Trade should not be blocked");
  }

  // Activate kill switch
  killSwitch.active = true;
  killSwitch.activationReason = "Test";

  // Trade should be blocked after activation
  try {
    killSwitch.guard(tradeRequest);
    assert(false, "Trade should have been blocked");
  } catch (e) {
    assert(e.code === "KILL_SWITCH_ACTIVE", "Correct error code");
  }
});

// Test 4: Kill switch cancels open orders
test("Kill switch cancels open orders", async () => {
  const eventStore = new MockEventStore();
  const tracker = new MockTracker();
  const killSwitch = new KillSwitch(eventStore, tracker);

  const initialOrders = tracker.getOpenOrders().length;
  assert(initialOrders > 0, "Has open orders");

  await killSwitch.activate("Test cancellation");

  const remainingOrders = tracker.getOpenOrders().length;
  assert(remainingOrders === 0, "All open orders cancelled");
  assert(tracker.cancelledOrders.length > 0, "Cancellation recorded");
});

// Test 5: Deactivate kill switch
test("Kill switch deactivation", async () => {
  const eventStore = new MockEventStore();
  const killSwitch = new KillSwitch(eventStore);

  await killSwitch.activate("Activation");
  assert(killSwitch.isActive(), "Switch is active");

  const result = await killSwitch.deactivate("Manual reactivation");

  assert(!killSwitch.isActive(), "Switch deactivated");
  assert(result.success, "Deactivation successful");
  assert(result.deactivatedAt, "Deactivation timestamp recorded");
});

// Test 6: Event store integration
test("Kill switch appends activation event", async () => {
  const eventStore = new MockEventStore();
  const killSwitch = new KillSwitch(eventStore);

  await killSwitch.activate("Test event");

  const events = eventStore.getEvents();
  assert(events.length > 0, "Event recorded");

  const activationEvent = events.find(e => e.type === "KILL_SWITCH_ACTIVATED");
  assert(activationEvent, "Activation event in store");
  assert(activationEvent.reason === "Test event", "Reason recorded");
});

// Test 7: Status reporting
test("Kill switch status reporting", async () => {
  const killSwitch = new KillSwitch();

  const beforeStatus = killSwitch.getStatus();
  assert(!beforeStatus.active, "Initially inactive");

  await killSwitch.activate("Status test");

  const activeStatus = killSwitch.getStatus();
  assert(activeStatus.active, "Status shows active");
  assert(activeStatus.durationSeconds, "Duration tracked");
});

// Test 8: canTrade function
test("Kill switch canTrade validation", async () => {
  const killSwitch = new KillSwitch();

  let result = killSwitch.canTrade();
  assert(result.allowed, "Trading allowed initially");

  await killSwitch.activate("Trade block test");

  result = killSwitch.canTrade();
  assert(!result.allowed, "Trading blocked after activation");
  assert(result.reason.includes("Kill switch"), "Reason includes kill switch");
});

// Test 9: Multiple activation attempts
test("Kill switch handles rapid activation attempts", async () => {
  const killSwitch = new KillSwitch();

  const promises = [];
  for (let i = 0; i < 3; i++) {
    promises.push(killSwitch.activate(`Attempt ${i + 1}`));
  }

  const results = await Promise.all(promises);
  const successes = results.filter(r => r.success).length;

  assert(successes === 1, "Only first activation succeeds");
  assert(killSwitch.isActive(), "Switch is active");
});

// Test 10: Timeline tracking
test("Kill switch timeline tracking", async () => {
  const killSwitch = new KillSwitch();

  let timeline = killSwitch.getTimeline();
  assert(timeline === null, "No timeline before activation");

  await killSwitch.activate("Timeline test");

  timeline = killSwitch.getTimeline();
  assert(timeline, "Timeline after activation");
  assert(timeline.activatedAt, "Activation time tracked");
  assert(timeline.durationMs >= 0, "Duration measured");
  assert(timeline.reason === "Timeline test", "Reason in timeline");
});

// Summary
console.log("\n" + "=".repeat(60));
console.log(`Kill Switch Tests: ${testsPassed} passed, ${testsFailed} failed`);
console.log("=".repeat(60));

if (testsFailed > 0) {
  process.exit(1);
}
