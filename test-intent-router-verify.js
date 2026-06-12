/**
 * Verification Test: Intent Router Classification
 *
 * Tests:
 * 1. "make changes to repo" → intent:"code"
 * 2. "play three doors" → intent:"rp_game"
 * 3. Capability registry correctly maps intents to agents
 */

const { classifyIntent, CAPABILITY_REGISTRY, getAgent } = require('./apps/lantern-garage/lib/intent-router.js');

console.log('='.repeat(80));
console.log('INTENT ROUTER VERIFICATION TEST');
console.log('='.repeat(80));

// ============================================================================
// TEST 1: "make changes to repo" → should classify as intent:"code"
// ============================================================================
console.log('\n[TEST 1] "make changes to repo"');
const test1Message = "make changes to repo";
const test1Result = classifyIntent(test1Message);
console.log('Result:', JSON.stringify(test1Result, null, 2));
const test1Pass = test1Result.intent === "code" || test1Result.intent === "refactor";
console.log(`Status: ${test1Pass ? 'PASS' : 'FAIL'}`);
console.log(`Expected intent: "code" or "refactor" | Got: "${test1Result.intent}"`);
console.log(`Agent: ${test1Result.agent} (expected: keystone)`);
console.log(`Confidence: ${test1Result.confidence}`);

// ============================================================================
// TEST 2: "play three doors" → should classify as intent:"rp_game"
// ============================================================================
console.log('\n' + '='.repeat(80));
console.log('[TEST 2] "play three doors"');
const test2Message = "play three doors";
const test2Result = classifyIntent(test2Message);
console.log('Result:', JSON.stringify(test2Result, null, 2));
const test2Pass = test2Result.intent === "rp_game" || test2Result.intent === "game_state";
console.log(`Status: ${test2Pass ? 'PASS' : 'FAIL'}`);
console.log(`Expected intent: "rp_game" or "game_state" | Got: "${test2Result.intent}"`);
console.log(`Agent: ${test2Result.agent} (expected: three-doors)`);
console.log(`Confidence: ${test2Result.confidence}`);

// ============================================================================
// TEST 3: Capability registry maps intents to agents
// ============================================================================
console.log('\n' + '='.repeat(80));
console.log('[TEST 3] Capability Registry Mapping');
console.log(`Total capabilities: ${CAPABILITY_REGISTRY.length}`);

const expectedMappings = [
  { agentId: "keystone", expectedIntents: ["code", "refactor", "bug_fix"] },
  { agentId: "founder", expectedIntents: ["strategy", "planning", "architecture"] },
  { agentId: "lantern", expectedIntents: ["dream", "reflection", "journal"] },
  { agentId: "three-doors", expectedIntents: ["rp_game", "game_state"] },
  { agentId: "csf", expectedIntents: ["memory", "export", "archive"] },
  { agentId: "trading", expectedIntents: ["market", "trading", "order"] },
];

let registryPass = true;
expectedMappings.forEach(({ agentId, expectedIntents }) => {
  const agent = getAgent(agentId);
  if (!agent) {
    console.log(`  FAIL: Agent "${agentId}" not found in registry`);
    registryPass = false;
    return;
  }

  const hasExpectedIntents = expectedIntents.every(intent =>
    agent.intents.includes(intent)
  );

  if (hasExpectedIntents) {
    console.log(`  PASS: ${agentId} has intents ${JSON.stringify(expectedIntents)}`);
  } else {
    console.log(`  FAIL: ${agentId} missing some intents. Found: ${JSON.stringify(agent.intents)}`);
    registryPass = false;
  }
});

console.log(`\nRegistry Mapping Status: ${registryPass ? 'PASS' : 'FAIL'}`);

// ============================================================================
// ADDITIONAL EDGE CASES
// ============================================================================
console.log('\n' + '='.repeat(80));
console.log('[EDGE CASES]');

const edgeCases = [
  { msg: "debug the code", expectedAgent: "keystone", desc: "Code + debug keyword" },
  { msg: "fix a bug in the repo", expectedAgent: "keystone", desc: "Code + bug + repo" },
  { msg: "I want to play kingdome", expectedAgent: "three-doors", desc: "Game with kingdome variant" },
  { msg: "three doors stage 3", expectedAgent: "three-doors", desc: "Game + stage" },
  { msg: "architectural decision", expectedAgent: "founder", desc: "Architecture keyword" },
  { msg: "remember this memory", expectedAgent: "lantern", desc: "Reflection + memory" },
  { msg: "buy some stocks", expectedAgent: "trading", desc: "Trading intent" },
  { msg: "hello there", expectedAgent: "lantern", desc: "Fallback to lantern (no triggers)" },
];

edgeCases.forEach(({ msg, expectedAgent, desc }) => {
  const result = classifyIntent(msg);
  const pass = result.agent === expectedAgent;
  console.log(`  ${pass ? 'PASS' : 'FAIL'}: "${msg}"`);
  console.log(`    Expected: ${expectedAgent} | Got: ${result.agent} (intent: ${result.intent}, confidence: ${result.confidence.toFixed(2)})`);
  console.log(`    ${desc}`);
});

// ============================================================================
// SUMMARY
// ============================================================================
console.log('\n' + '='.repeat(80));
console.log('SUMMARY');
console.log('='.repeat(80));
console.log(`TEST 1 (repo code): ${test1Pass ? 'PASS' : 'FAIL'}`);
console.log(`TEST 2 (three doors): ${test2Pass ? 'PASS' : 'FAIL'}`);
console.log(`TEST 3 (registry): ${registryPass ? 'PASS' : 'FAIL'}`);

const allPass = test1Pass && test2Pass && registryPass;
console.log(`\nOVERALL: ${allPass ? 'PASS' : 'FAIL'}`);
console.log('='.repeat(80));
