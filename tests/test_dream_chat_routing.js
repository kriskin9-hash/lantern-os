const assert = require("assert");
const { AGENT_PERSONAS, selectAgent, parseBangCommand } = require("../apps/lantern-garage/lib/dream-chat");

let passed = 0, failed = 0;

function test(name, fn) {
  try { fn(); console.log(`  ✓ ${name}`); passed++; }
  catch (err) { console.error(`  ✗ ${name}\n    ${err.message}`); failed++; }
}

function detectIntent(message) {
  const lower = String(message || "").toLowerCase();
  if (/\b(buy|sell|trade|market|stock|invest|portfolio)\b/.test(lower)) return "trading";
  if (/\b(play|game|doors|kingdome|three.?doors?)\b/.test(lower)) return "rp_game";
  if (/\b(export|archive|csf|compress)\b/.test(lower)) return "memory_export";
  if (/^!convergence/.test(lower)) return "convergence";
  return "unknown";
}

function supportsConvergence(intent) {
  return ["trading", "memory_export", "convergence"].includes(intent);
}

console.log("\nTest: Trading Query");
test('should route "buy aapl shares"', () => {
  const agent = selectAgent("buy aapl shares");
  assert.strictEqual(agent.id, "keystone");
});

console.log("\nTest: Intent Detection");
test("should detect trading intent", () => {
  assert.strictEqual(detectIntent("buy stock"), "trading");
});

console.log("\nTest: Agent Personas");
test("should have 6+ agents", () => {
  assert.ok(AGENT_PERSONAS.length >= 6);
});

console.log("\n" + "=".repeat(50));
console.log(`Tests passed: ${passed}`);
console.log(`Tests failed: ${failed}`);
console.log("=".repeat(50));

process.exit(failed > 0 ? 1 : 0);
