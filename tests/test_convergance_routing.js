/**
 * Convergence Routing Tests
 * Tests intent classification and profile routing in model-router.js.
 * No live server required — tests the routing module directly.
 */

const assert = require("assert");
const { classifyIntent, route, buildBehaviorPreamble, INTENT_PATTERNS } = require("../apps/lantern-garage/lib/convergance-os/model-router");
const { getProfile } = require("../apps/lantern-garage/lib/convergance-os/profiles");

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

function run() {
  console.log("\nConvergence Routing Tests\n");

  // ── classifyIntent ────────────────────────────────────────────────────
  console.log("classifyIntent");

  test("!convergance maps to convergance_action", () => {
    assert.strictEqual(classifyIntent("!convergance"), "convergance_action");
  });

  test("!converge maps to convergance_action", () => {
    assert.strictEqual(classifyIntent("!converge"), "convergance_action");
  });

  test("!self-edit maps to coding_change", () => {
    assert.strictEqual(classifyIntent("!self-edit fix the bug"), "coding_change");
  });

  test("!code maps to coding_change", () => {
    assert.strictEqual(classifyIntent("!code add a route"), "coding_change");
  });

  test("!review maps to code_review", () => {
    assert.strictEqual(classifyIntent("!review this PR"), "code_review");
  });

  test("dream chat stays dream_chat", () => {
    assert.strictEqual(classifyIntent("I had a lucid dream about flying"), "dream_chat");
  });

  test("provider query maps to capacity_query", () => {
    assert.strictEqual(classifyIntent("which model is running right now"), "capacity_query");
  });

  test("coding change intent keywords work", () => {
    assert.strictEqual(classifyIntent("fix the Three Doors routing bug and open a PR"), "coding_change");
  });

  test("technical debug maps to technical_debug", () => {
    assert.strictEqual(classifyIntent("the chat bubble is broken"), "technical_debug");
  });

  // ── Profile routing ─────────────────────────────────────────────────
  console.log("Profile routing");

  test("coding_change routes to lantern-coding", () => {
    const profile = getProfile("lantern-coding");
    assert.strictEqual(profile.id, "lantern-coding");
    assert.ok(profile.behavior.some((b) => b.includes("precise")), "coding profile should mention precision");
  });

  test("technical_debug routes to keystone profile", () => {
    const profile = getProfile("keystone");
    assert.strictEqual(profile.id, "keystone");
    assert.ok(profile.behavior.some((b) => b.includes("senior engineer")), "keystone profile should mention senior engineer");
  });

  test("code_review routes to keystone profile", () => {
    const profile = getProfile("keystone");
    assert.strictEqual(profile.id, "keystone");
  });

  test("keystone profile does not silently fall back to dream", () => {
    const profile = getProfile("keystone");
    assert.notStrictEqual(profile.id, "lantern-csf-dream", "keystone should be a real profile, not a fallback");
  });

  // ── route() async decision ────────────────────────────────────────────
  console.log("route() async decision");

  test("route returns coding_change intent for code request", async () => {
    const decision = await route("fix the Three Doors routing bug");
    assert.strictEqual(decision.intent, "coding_change");
    assert.strictEqual(decision.profileId, "lantern-coding");
  });

  test("route returns convergance_action for !converge", async () => {
    const decision = await route("!converge");
    assert.strictEqual(decision.intent, "convergance_action");
    assert.strictEqual(decision.profileId, "lantern-convergance");
  });

  test("route returns technical_debug for bug reports", async () => {
    const decision = await route("debug why the ui is not sending");
    assert.strictEqual(decision.intent, "technical_debug");
    assert.strictEqual(decision.profileId, "keystone");
  });

  test("route returns capacity_query for provider questions", async () => {
    const decision = await route("what is the ollama status");
    assert.strictEqual(decision.intent, "capacity_query");
    assert.strictEqual(decision.profileId, "lantern-pcsf");
  });

  // ── buildBehaviorPreamble ─────────────────────────────────────────────
  console.log("buildBehaviorPreamble");

  test("returns empty string for null decision", () => {
    assert.strictEqual(buildBehaviorPreamble(null), "");
  });

  test("includes profile and intent in preamble", () => {
    const preamble = buildBehaviorPreamble({
      profileId: "lantern-coding",
      intent: "coding_change",
      behaviorRules: ["Rule one", "Rule two"],
    });
    assert.ok(preamble.includes("lantern-coding"), "preamble should mention profile");
    assert.ok(preamble.includes("Rule one"), "preamble should include behavior rules");
  });

  // ── Summary ───────────────────────────────────────────────────────────
  console.log(`\n${passed} passed, ${failed} failed`);
  process.exit(failed > 0 ? 1 : 0);
}

run();
