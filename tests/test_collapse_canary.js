/**
 * Tests for the JS chat-level collapse canary (#1010).
 * Run: node tests/test_collapse_canary.js
 *
 * Acceptance: a forced repeating reply raises proximity + emits a logged signal;
 * healthy replies are unaffected.
 */
const assert = require("assert");
const path = require("path");
const { computeProximity, extractNgrams, detectEcho, observe, PROXIMITY_THRESHOLD } =
  require(path.resolve(__dirname, "..", "apps", "lantern-garage", "lib", "collapse-canary"));

let n = 0;
const ok = (name, fn) => {
  try { fn(); n++; console.log(`  ✓ ${name}`); }
  catch (e) { console.error(`  ✗ ${name}: ${e.message}`); process.exitCode = 1; }
};

console.log("collapse-canary (#1010)");

// ── extractNgrams ─────────────────────────────────────────────────────
ok("extractNgrams: healthy unique text → low proximity", () => {
  const text = "The quick brown fox jumps over the lazy dog and then runs away";
  const { proximity } = extractNgrams(text, 3);
  assert.ok(proximity < 0.2, `expected < 0.2, got ${proximity}`);
});

ok("extractNgrams: highly repetitive text → high proximity", () => {
  const phrase = "the cat sat on the mat";
  const repeated = Array(8).fill(phrase).join(" ");
  const { proximity } = extractNgrams(repeated, 3);
  assert.ok(proximity >= 0.35, `expected >= 0.35, got ${proximity}`);
});

ok("extractNgrams: short text → total=0, proximity=0", () => {
  const { proximity } = extractNgrams("hi", 3);
  assert.strictEqual(proximity, 0);
});

// ── detectEcho ───────────────────────────────────────────────────────
ok("detectEcho: tail repeats head → high echo", () => {
  const head = "Alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron";
  const tail = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron";
  const echo = detectEcho(`${head} ${tail} ${tail}`);
  assert.ok(echo > 0.3, `expected echo > 0.3, got ${echo}`);
});

ok("detectEcho: novel tail → low echo", () => {
  const text = "The sky is blue. The grass is green. Water is wet. Fire is hot. Snow is white. " +
    "Mountains are tall. Rivers run long. Birds sing songs. Clouds drift past. Stars glow bright.";
  const echo = detectEcho(text);
  assert.ok(echo < 0.3, `expected echo < 0.3, got ${echo}`);
});

ok("detectEcho: short text → 0", () => {
  assert.strictEqual(detectEcho("too short"), 0);
});

// ── computeProximity ─────────────────────────────────────────────────
ok("computeProximity: healthy varied reply → below threshold", () => {
  const text = [
    "The Convergence Core is a local-first reasoning system that remembers, reasons, acts, and verifies.",
    "It stores experience in append-only logs and improves via retrieval, not weight modification.",
    "The primary interface is dream-chat.html where you can talk to Keystone directly.",
    "External grounding ensures nothing is accepted without evidence from web or codebase sources.",
  ].join(" ");
  const p = computeProximity(text);
  assert.ok(p < PROXIMITY_THRESHOLD, `healthy text should be below threshold (${PROXIMITY_THRESHOLD}), got ${p}`);
});

ok("computeProximity: forced repeating reply → above threshold", () => {
  const loopPhrase = "The answer is yes because the answer is yes because the answer is yes";
  const repeated = Array(5).fill(loopPhrase).join(". ");
  const p = computeProximity(repeated);
  assert.ok(p >= PROXIMITY_THRESHOLD, `looping text should be >= threshold (${PROXIMITY_THRESHOLD}), got ${p}`);
});

// ── observe ──────────────────────────────────────────────────────────
ok("observe: short text → canary_fired=false", () => {
  const result = observe("hi there");
  assert.strictEqual(result.canary_fired, false);
  assert.strictEqual(result.proximity, 0);
});

ok("observe: healthy reply → canary_fired=false", () => {
  const text = "Lantern OS is a persistent local-first reasoning system. It uses a convergence loop: " +
    "Observe, Remember, Reason, Act, Verify. The system never fabricates evidence and always " +
    "grounds claims against observable reality. The dream journal is the primary user interface.";
  const result = observe(text, { agent: "keystone", provider: "anthropic" });
  assert.strictEqual(result.canary_fired, false);
});

ok("observe: looping reply → canary_fired=true (acceptance criterion)", () => {
  const loopPhrase = "The cat sat on the mat and the cat sat on the mat and the cat sat on the mat";
  const text = Array(6).fill(loopPhrase).join(". ");
  const result = observe(text, { agent: "keystone", provider: "ollama" });
  assert.strictEqual(result.canary_fired, true, `proximity=${result.proximity} should trigger canary`);
  assert.ok(result.proximity >= PROXIMITY_THRESHOLD);
  assert.strictEqual(result.action, "logged");
});

console.log(`\nPASS — ${n} collapse-canary checks`);
