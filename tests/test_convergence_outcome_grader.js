/**
 * Tests for the domain-agnostic Brier outcome grader (#1011).
 * Run: node tests/test_convergence_outcome_grader.js
 */
const assert = require("assert");
const path = require("path");
const { brierScore, gradeRecord, calibrationSummary, parseGradedLines } =
  require(path.resolve(__dirname, "..", "apps", "lantern-garage", "lib", "convergence-outcome-grader"));

let n = 0;
const ok = (name, fn) => { try { fn(); n++; console.log(`  ✓ ${name}`); } catch (e) { console.error(`  ✗ ${name}: ${e.message}`); process.exitCode = 1; } };

console.log("convergence-outcome-grader (#1011)");

ok("brierScore: perfect forecast (conf=1 → outcome=1) → 0", () => {
  assert.strictEqual(brierScore(1.0, true), 0.0);
});
ok("brierScore: worst forecast (conf=1 → outcome=0) → 1", () => {
  assert.strictEqual(brierScore(1.0, false), 1.0);
});
ok("brierScore: random forecast (0.5) → 0.25", () => {
  assert.ok(Math.abs(brierScore(0.5, true) - 0.25) < 1e-9);
  assert.ok(Math.abs(brierScore(0.5, false) - 0.25) < 1e-9);
});
ok("brierScore: conf=0.62, outcome=true → ~0.1444", () => {
  assert.ok(Math.abs(brierScore(0.62, true) - 0.1444) < 1e-6);
});
ok("brierScore: conf clamp prevents negative", () => {
  assert.ok(brierScore(-5, true) >= 0);
  assert.ok(brierScore(999, false) <= 1);
});

ok("gradeRecord: includes brier_score + confidence", () => {
  const record = { id: "test-1", confidence: 0.8, reasoner: "grounding" };
  const g = gradeRecord(record, { passed: true, notes: "test" });
  assert.strictEqual(g.record_id, "test-1");
  assert.strictEqual(g.passed, true);
  assert.strictEqual(g.confidence, 0.8);
  assert.ok(Math.abs(g.brier_score - 0.04) < 1e-9, `expected 0.04, got ${g.brier_score}`);
  assert.strictEqual(g.notes, "test");
  assert.strictEqual(g.reasoner, "grounding");
  assert.ok(typeof g.graded_at === "string");
});
ok("gradeRecord: false outcome computes correctly", () => {
  const record = { id: "test-2", confidence: 0.8, reasoner: "x" };
  const g = gradeRecord(record, { passed: false });
  assert.ok(Math.abs(g.brier_score - 0.64) < 1e-9);
});

ok("calibrationSummary: empty → nulls", () => {
  const s = calibrationSummary([]);
  assert.strictEqual(s.n, 0);
  assert.strictEqual(s.mean_brier, null);
  assert.strictEqual(s.ece, null);
});
ok("calibrationSummary: perfect forecaster → mean_brier=0, skill=1", () => {
  const lines = [
    { brier_score: 0, confidence: 1.0, passed: true },
    { brier_score: 0, confidence: 1.0, passed: true },
  ];
  const s = calibrationSummary(lines);
  assert.ok(Math.abs(s.mean_brier) < 1e-9);
  assert.ok(Math.abs(s.skill_score - 1.0) < 1e-9);
});
ok("calibrationSummary: random forecaster → skill_score ~0", () => {
  const lines = Array.from({ length: 20 }, (_, i) => ({
    brier_score: 0.25,
    confidence: 0.5,
    passed: i % 2 === 0,
  }));
  const s = calibrationSummary(lines);
  assert.ok(Math.abs(s.skill_score) < 0.01);
});
ok("calibrationSummary: non-graded lines (no brier_score) ignored", () => {
  const lines = [
    { record_id: "x", passed: true },         // old format, no brier_score
    { brier_score: 0.1, confidence: 0.9, passed: true },
  ];
  const s = calibrationSummary(lines);
  assert.strictEqual(s.n, 1);
});

ok("parseGradedLines: parses JSONL string, skips non-brier lines", () => {
  const text = [
    JSON.stringify({ brier_score: 0.1, confidence: 0.8, passed: true }),
    JSON.stringify({ record_id: "old", passed: true }),  // no brier_score → skipped
    "not json",
    JSON.stringify({ brier_score: 0.4, confidence: 0.5, passed: false }),
  ].join("\n");
  const lines = parseGradedLines(text);
  assert.strictEqual(lines.length, 2);
});

console.log(`\nPASS — ${n} outcome-grader checks`);
