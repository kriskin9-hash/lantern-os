// #1411 — outcome metric computation (verified-patch / honesty / route-quality).
// Pure functions over parsed records; locks the honesty rule (no data → null +
// status:"insufficient_data", never a fabricated rate).
//
// Run: node apps/lantern-garage/test/outcome-metrics.test.js
const assert = require("assert");
const m = require("../lib/outcome-metrics");

let failures = 0;
function check(name, fn) {
  try { fn(); process.stdout.write(`  ok  - ${name}\n`); }
  catch (e) { failures++; process.stderr.write(`  FAIL- ${name}\n       ${e.message}\n`); }
}

// ── verifiedPatchRate ───────────────────────────────────────────────────────────
check("verified flag + pass result both count as verified", () => {
  const r = m.verifiedPatchRate([
    { verified: true }, { verified: false },
    { result: "tests passed" }, { result: "apply_failed" },
  ]);
  assert.strictEqual(r.n, 4);
  assert.strictEqual(r.verified, 2);
  assert.strictEqual(r.rate, 0.5);
  assert.strictEqual(r.status, "ok");
});

check("no records → insufficient_data, null rate (no fabrication)", () => {
  const r = m.verifiedPatchRate([]);
  assert.strictEqual(r.rate, null);
  assert.strictEqual(r.status, "insufficient_data");
});

// ── honestyRate ─────────────────────────────────────────────────────────────────
check("anchored vs confident-but-unanchored", () => {
  const r = m.honestyRate([
    { grounded: true, groundedBy: "execution" },
    { grounded: true, groundedBy: "anchor" },
    { grounded: false, groundedBy: "none" },   // the 42-state
    { grounded: false },                          // unsupported, no anchor
  ]);
  assert.strictEqual(r.n, 4);
  assert.strictEqual(r.anchored, 2);
  assert.strictEqual(r.unsupported, 2);
  assert.strictEqual(r.rate, 0.5);
});

check("honesty with no reviews → insufficient_data", () => {
  const r = m.honestyRate([]);
  assert.strictEqual(r.rate, null);
  assert.strictEqual(r.status, "insufficient_data");
});

// ── routeQuality ────────────────────────────────────────────────────────────────
check("escalation rate + latency from leaderboard", () => {
  const r = m.routeQuality(
    [{ escalate: true }, { escalate: false }, { escalate: false }, { escalate: true }],
    [{ sec_per_problem: 2 }, { sec_per_problem: 4 }, { sec_per_problem: null }]);
  assert.strictEqual(r.decisions, 4);
  assert.strictEqual(r.escalations, 2);
  assert.strictEqual(r.escalationRate, 0.5);
  assert.strictEqual(r.avgLatencySec, 3);
  assert.strictEqual(r.latencySamples, 2);
});

check("route quality reports uninstrumented fields honestly", () => {
  const r = m.routeQuality([{ escalate: false }], []);
  assert.strictEqual(r.cost.status, "not_instrumented");
  assert.strictEqual(r.rePromptRate.status, "not_instrumented");
  assert.strictEqual(r.avgLatencySec, null);
});

check("no decisions → insufficient_data", () => {
  const r = m.routeQuality([], []);
  assert.strictEqual(r.escalationRate, null);
  assert.strictEqual(r.status, "insufficient_data");
});

// ── readJsonl is resilient to bad lines / missing files ─────────────────────────
check("readJsonl returns [] for a missing file", () =>
  assert.deepStrictEqual(m.readJsonl("/no/such/file.jsonl"), []));

if (failures) { process.stderr.write(`\n${failures} FAILED\n`); process.exit(1); }
process.stdout.write("\nall outcome-metrics checks passed\n");
