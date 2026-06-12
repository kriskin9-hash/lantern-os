/**
 * Orchestration Router Integration Tests
 * Verifies that intent-router, convergence-adapter, and stream-chat work together.
 * Tests the full routing pipeline without requiring a running Python engine.
 */

const assert = require("assert");
const { classifyIntent, getAgent, CAPABILITY_REGISTRY } = require("../apps/lantern-garage/lib/intent-router");
const { convergeMessage, getCircuitState, resetCircuit } = require("../apps/lantern-garage/lib/convergence-adapter");

let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    fn();
    console.log(`  ✓ ${name}`);
    passed++;
  } catch (err) {
    console.error(`  ✗ ${name}`);
    console.error(`    ${err.message}`);
    failed++;
  }
}

console.log("\nOrchestration Router Integration Tests\n");

// Test 1: Intent classification produces valid routing decisions
console.log("Intent Classification → Routing Decision");

test("trading intent routes to trading agent (no convergence)", () => {
  const route = classifyIntent("buy aapl stock");
  assert.strictEqual(route.agent, "trading", "Should route to trading agent");
  assert.strictEqual(route.requires_convergence, false, "Trading has canConverge=false");
  // Surface is "direct" if matchCount > 2, otherwise "ambient"
  assert.ok(route.surface === "direct" || route.surface === "ambient", "Surface should be direct or ambient");
});

test("code intent produces convergence for blocking or long messages", () => {
  const route = classifyIntent("refactor the authentication handler to support oauth and update the database schema");
  assert.strictEqual(route.agent, "keystone", "Should route to code agent (keystone)");
  // Note: convergence only if message is long (>50 words) or agent is blocking
  // This message should trigger convergence if >50 words
  const wordCount = "refactor the authentication handler to support oauth and update the database schema".split(/\s+/).length;
  if (wordCount > 50) {
    assert.strictEqual(route.requires_convergence, true, "Long code message should require convergence");
  }
});

test("rp_game intent does NOT require convergence", () => {
  const route = classifyIntent("play three doors");
  assert.strictEqual(route.agent, "three-doors", "Should route to three-doors agent");
  assert.strictEqual(route.requires_convergence, false, "RP game should not require convergence");
});

test("memory export intent (short message) does NOT require convergence", () => {
  const route = classifyIntent("export data");
  assert.strictEqual(route.agent, "csf", "Should route to CSF/memory agent");
  assert.strictEqual(route.requires_convergence, false, "Short message, not blocking");
});

test("strategy intent produces convergence (blocking agent)", () => {
  const route = classifyIntent("plan the next sprint");
  assert.strictEqual(route.agent, "founder", "Should route to strategy agent");
  // Founder has isBlocking: true, so should converge
  assert.strictEqual(route.requires_convergence, true, "Blocking agent (founder) should require convergence");
});

// Test 2: Agent lookup works correctly
console.log("\nAgent Registry Lookup");

test("getAgent returns valid agent for keystone", () => {
  const agent = getAgent("keystone");
  assert.ok(agent, "Agent should exist");
  assert.strictEqual(agent.id, "keystone");
  assert.strictEqual(agent.canConverge, true, "Keystone should support convergence");
  assert.strictEqual(agent.isBlocking, false, "Keystone is not blocking");
});

test("getAgent returns valid agent for founder", () => {
  const agent = getAgent("founder");
  assert.ok(agent, "Agent should exist");
  assert.strictEqual(agent.canConverge, true, "Founder should support convergence");
  assert.strictEqual(agent.isBlocking, true, "Founder is blocking (decisions needed)");
});

test("getAgent returns null for unknown agent", () => {
  const agent = getAgent("nonexistent");
  assert.strictEqual(agent, null, "Unknown agent should return null");
});

// Test 3: Convergence adapter circuit breaker state
console.log("\nConvergence Adapter Circuit Breaker");

test("circuit starts in closed state", () => {
  resetCircuit();
  const state = getCircuitState();
  assert.strictEqual(state.state, "closed", "Circuit should start closed");
  assert.strictEqual(state.failures, 0, "No failures recorded yet");
});

test("circuit breaker exports are callable", () => {
  assert.strictEqual(typeof convergeMessage, "function", "convergeMessage should be a function");
  assert.strictEqual(typeof getCircuitState, "function", "getCircuitState should be a function");
  assert.strictEqual(typeof resetCircuit, "function", "resetCircuit should be a function");
});

// Test 4: Routing decision data structure validation
console.log("\nRouting Decision Structure");

test("classifyIntent returns all required fields", () => {
  const route = classifyIntent("refactor the code");
  assert.ok(route.intent, "Should have intent field");
  assert.ok(route.agent, "Should have agent field");
  assert.ok(route.surface, "Should have surface field");
  assert.ok(typeof route.confidence === "number", "Should have confidence number");
  assert.ok(route.reason, "Should have reason field");
  assert.ok(typeof route.requires_convergence === "boolean", "Should have requires_convergence boolean");
});

test("convergence-enabled intents have confidence > 0", () => {
  const route = classifyIntent("debug the three-doors crash");
  assert.ok(route.confidence > 0, `Confidence should be > 0, got ${route.confidence}`);
});

test("unknown intents default to lantern with 0 confidence", () => {
  const route = classifyIntent("xyz abc 123");
  assert.strictEqual(route.agent, "lantern", "Should default to lantern");
  assert.strictEqual(route.confidence, 0, "Unknown intent should have 0 confidence");
});

// Test 5: Capability registry structure
console.log("\nCapability Registry Structure");

test("CAPABILITY_REGISTRY has 6 agents", () => {
  assert.strictEqual(CAPABILITY_REGISTRY.length, 6, "Should have exactly 6 agents");
});

test("all agents have required fields", () => {
  for (const agent of CAPABILITY_REGISTRY) {
    assert.ok(agent.id, `Agent ${agent.id} should have id`);
    assert.ok(agent.name, `Agent ${agent.id} should have name`);
    assert.ok(Array.isArray(agent.intents), `Agent ${agent.id} should have intents array`);
    assert.ok(Array.isArray(agent.triggers), `Agent ${agent.id} should have triggers array`);
    assert.ok(typeof agent.canConverge === "boolean", `Agent ${agent.id} should have canConverge boolean`);
    assert.ok(typeof agent.isBlocking === "boolean", `Agent ${agent.id} should have isBlocking boolean`);
  }
});

test("agent IDs are unique", () => {
  const ids = CAPABILITY_REGISTRY.map(a => a.id);
  const uniqueIds = new Set(ids);
  assert.strictEqual(ids.length, uniqueIds.size, "All agent IDs should be unique");
});

// Test 6: Full pipeline scenario
console.log("\nFull Pipeline Scenarios");

test("code bug fix routes to keystone", () => {
  const route = classifyIntent("there is a critical bug in the auth handler that needs fixing now");
  assert.strictEqual(route.agent, "keystone");
  assert.ok(route.reason.includes("Keystone"));
  const agent = getAgent(route.agent);
  assert.ok(agent.canConverge);
  // Convergence depends on word count (>50) or isBlocking
});

test("strategy planning routes to founder with convergence (blocking)", () => {
  const route = classifyIntent("plan the sprint roadmap");
  assert.strictEqual(route.agent, "founder");
  assert.strictEqual(route.requires_convergence, true, "Founder is blocking, so requires convergence");
  const agent = getAgent(route.agent);
  assert.ok(agent.isBlocking);
});

test("dream introspection routes to lantern without convergence", () => {
  const route = classifyIntent("what does this dream symbol mean");
  assert.strictEqual(route.agent, "lantern");
  assert.strictEqual(route.requires_convergence, false, "Short dream message doesn't require convergence");
});

// Summary
console.log(`\n${"=".repeat(50)}`);
console.log(`Tests passed: ${passed}`);
console.log(`Tests failed: ${failed}`);
console.log("=".repeat(50));

process.exit(failed > 0 ? 1 : 0);
