/**
 * Router Gate Tests — conversation-dynamics escalation signal.
 * Verifies: feature extraction, escalate-on-new-ground, keep-local-on-looping,
 * empty/edge input, and the documented invariant that escalate maps to the
 * "reasoning" taskType (and nothing else).
 *
 * Pure module — no server required.
 * Run: node tests/test_router_gate.js
 */

const assert = require("assert");
const {
  gateDecision,
  features,
} = require("../apps/lantern-garage/lib/router-gate");

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

// ── features ────────────────────────────────────────────────────────────────
ok("empty conversation -> all-zero features, no escalate", () => {
  const d = gateDecision([]);
  assert.deepStrictEqual(d.features, { novelty: 0, self_repeat: 0, echo: 0, length: 0 });
  assert.strictEqual(d.escalate, false);
  assert.strictEqual(d.taskTypeOverride, null);
});

ok("first turn (no prior) counts as fully novel", () => {
  const f = features([{ role: "user", text: "tell me about the wind" }]);
  assert.strictEqual(f.novelty, 1);
  assert.strictEqual(f.echo, 0);
  assert.strictEqual(f.self_repeat, 0);
});

ok("accepts {content} as well as {text}", () => {
  const f = features([{ role: "user", content: "hello world" }]);
  assert.strictEqual(f.novelty, 1);
});

ok("novelty drops when latest turn reuses prior vocabulary", () => {
  const f = features([
    { role: "user", text: "the river runs cold and deep" },
    { role: "user", text: "the river runs cold" },
  ]);
  // every token of the 2nd turn appeared before -> novelty 0
  assert.strictEqual(f.novelty, 0);
  assert.ok(f.self_repeat > 0.8, `self_repeat=${f.self_repeat}`);
});

ok("echo is high when a reply parrots the previous turn", () => {
  const f = features([
    { role: "user", text: "quantum entanglement spooky action" },
    { role: "assistant", text: "quantum entanglement spooky action" },
  ]);
  assert.ok(f.echo > 0.99, `echo=${f.echo}`);
});

// ── decisions ───────────────────────────────────────────────────────────────
ok("genuinely new ground escalates to reasoning chain", () => {
  const d = gateDecision([
    { role: "user", text: "hi" },
    { role: "assistant", text: "hello there" },
    {
      role: "user",
      text:
        "Explain how Freidlin-Wentzell large-deviation theory bounds the " +
        "Kramers escape rate across a saddle in a non-gradient drift field.",
    },
  ]);
  assert.strictEqual(d.escalate, true, JSON.stringify(d));
  assert.strictEqual(d.taskTypeOverride, "reasoning");
});

ok("looping turn (high self_repeat, low novelty) stays local", () => {
  const d = gateDecision([
    { role: "user", text: "are you stuck are you stuck are you stuck" },
    { role: "user", text: "are you stuck are you stuck are you stuck" },
  ]);
  assert.strictEqual(d.escalate, false, JSON.stringify(d));
  assert.match(d.reason, /looping/);
  assert.strictEqual(d.taskTypeOverride, null);
});

ok("trivial short repeat does not escalate", () => {
  const d = gateDecision([
    { role: "user", text: "thanks that helps" },
    { role: "assistant", text: "glad it helped" },
    { role: "user", text: "thanks" },
  ]);
  assert.strictEqual(d.escalate, false, JSON.stringify(d));
});

ok("INVARIANT: taskTypeOverride is only ever 'reasoning' or null", () => {
  const samples = [
    [],
    [{ role: "user", text: "a" }],
    [{ role: "user", text: "explain the architecture of a reservoir computer in depth" }],
    [{ role: "user", text: "loop loop loop" }, { role: "user", text: "loop loop loop" }],
  ];
  for (const s of samples) {
    const d = gateDecision(s);
    assert.ok(
      d.taskTypeOverride === "reasoning" || d.taskTypeOverride === null,
      `unexpected override: ${d.taskTypeOverride}`
    );
    assert.strictEqual(d.escalate, d.taskTypeOverride === "reasoning");
  }
});

ok("threshold is tunable via opts.escalateScore", () => {
  const convo = [
    { role: "user", text: "hi" },
    { role: "user", text: "a modest follow-up question about the weather today" },
  ];
  // max achievable score is 1.0 (novelty 1 * substance 1); 1.2 is unreachable
  const strict = gateDecision(convo, { escalateScore: 1.2 });
  const loose = gateDecision(convo, { escalateScore: -1 });
  assert.strictEqual(strict.escalate, false);
  assert.strictEqual(loose.escalate, true);
});

console.log(`\nRouter Gate: ${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
