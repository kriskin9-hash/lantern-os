/**
 * Serving-modes (Node) tests — issue #729 dream-chat decode-param parity.
 *
 * PR #723 landed anti-repetition decode params in the Python connector, but the
 * live dream-chat path builds its own provider requests. apps/lantern-garage/lib/
 * serving-modes.js closes that gap. This verifies the Node module matches the
 * Python reference (src/serving_modes.py) and applies params per provider shape.
 *
 * Pure unit test — no server required.
 * Run: node tests/test_serving_modes_node.js
 */

const assert = require("assert");
const path = require("path");

const serving = require(path.join(__dirname, "..", "apps", "lantern-garage", "lib", "serving-modes.js"));

let passed = 0;
let failed = 0;
function ok(label, fn) {
  try {
    fn();
    console.log(`  ✓ ${label}`);
    passed++;
  } catch (e) {
    console.error(`  ✗ ${label}`);
    console.error(`    ${e.message}`);
    failed++;
  }
}

// Ensure a clean baseline regardless of the caller's environment.
delete process.env.OURO_NATIVE;

console.log("\nServing modes (Node) — unit tests");

ok("FAST mode is the default (no OURO_NATIVE)", () => {
  delete process.env.OURO_NATIVE;
  assert.strictEqual(serving.getServingMode().name, "fast");
});

ok("OURO_NATIVE=1/true/yes opts into DEEP mode", () => {
  for (const v of ["1", "true", "YES"]) {
    process.env.OURO_NATIVE = v;
    assert.strictEqual(serving.getServingMode().name, "deep", `value=${v}`);
  }
  delete process.env.OURO_NATIVE;
});

ok("FAST decode params strengthened for anti-collapse (#1609)", () => {
  const dp = serving.getDecodeParams(serving.FAST_MODE);
  assert.strictEqual(dp.top_p, 0.92);
  assert.strictEqual(dp.frequency_penalty, 0.6);
  assert.strictEqual(dp.repetition_penalty, 1.18);
  assert.strictEqual(dp.repeat_last_n, 256);
});

// The local-Ollama degraded path is where small models spiral into repetition (#1609);
// lock in a minimum anti-repetition signal so this can't silently regress to the weak
// 1.1 / 64 that let the loops through.
ok("FAST anti-repetition meets the minimum strength bar (#1609)", () => {
  const dp = serving.getDecodeParams(serving.FAST_MODE);
  assert.ok(dp.repetition_penalty >= 1.15, `repeat_penalty ${dp.repetition_penalty} too weak`);
  assert.ok(dp.repeat_last_n >= 256, `repeat_last_n ${dp.repeat_last_n} window too short`);
  assert.ok(dp.top_p <= 0.95, `top_p ${dp.top_p} too loose`);
});

ok("DEEP decode params are gentler than FAST but still widened", () => {
  const dp = serving.getDecodeParams(serving.DEEP_MODE);
  const fast = serving.getDecodeParams(serving.FAST_MODE);
  assert.strictEqual(dp.top_p, 0.98);
  assert.ok(dp.repetition_penalty < fast.repetition_penalty, "DEEP must be gentler than FAST");
  assert.ok(dp.repeat_last_n >= 256);
});

ok("Ollama gets repeat_penalty form (no OpenAI frequency_penalty)", () => {
  const opts = serving.applyOllamaDecodeParams({});
  assert.strictEqual(opts.top_p, 0.92);
  assert.strictEqual(opts.repeat_penalty, 1.18);
  assert.strictEqual(opts.repeat_last_n, 256);
  assert.ok(!("frequency_penalty" in opts), "Ollama must not receive frequency_penalty");
});

ok("OpenAI-compatible providers get top_p + frequency_penalty", () => {
  const body = serving.applyOpenAIDecodeParams({ model: "m", messages: [] });
  assert.strictEqual(body.top_p, 0.92);
  assert.strictEqual(body.frequency_penalty, 0.6);
  assert.strictEqual(body.model, "m"); // existing fields preserved
});

ok("DEEP mode flows through the apply helpers", () => {
  process.env.OURO_NATIVE = "1";
  const body = serving.applyOpenAIDecodeParams({});
  assert.strictEqual(body.top_p, 0.98);
  assert.strictEqual(body.frequency_penalty, 0.3);
  delete process.env.OURO_NATIVE;
});

console.log(`\nServing modes (Node): ${passed} passed, ${failed} failed\n`);
process.exit(failed === 0 ? 0 : 1);
