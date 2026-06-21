/**
 * Regression tests for the fuzzy in-process patch applier (#854).
 * Run: node tests/test_self_edit_applier.js
 *
 * The autowork loop's strict fallback applier used to reject otherwise-valid
 * LLM diffs because it gated on the `@@` hunk line-counts and required byte-exact
 * context. These tests feed diffs with (a) wrong @@ counts, (b) trailing/indent
 * whitespace drift, and (c) CRLF files, and assert the applier still lands them.
 */

"use strict";

const fs   = require("fs");
const path = require("path");
const os   = require("os");
const assert = require("assert");

const { parseUnifiedDiff, applyPatchStrict } = require("../apps/lantern-garage/lib/self-edit-engine.js");

let passed = 0, failed = 0;
function test(name, fn) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "lantern-applier-"));
  try { fn(dir); console.log(`  ✓ ${name}`); passed++; }
  catch (e) { console.error(`  ✗ ${name}\n      ${e.message}`); failed++; }
  finally { fs.rmSync(dir, { recursive: true, force: true }); }
}

// Apply a diff string against a scratch repo and return the apply stats.
function apply(dir, diff) {
  const files = parseUnifiedDiff(diff);
  return applyPatchStrict(dir, files);
}

console.log("\n── fuzzy patch applier (#854)");

// (a) Wrong @@ hunk counts — header says -2,4/+2,4 but the body is 3 old lines.
test("applies despite wrong @@ line-counts", (dir) => {
  fs.writeFileSync(path.join(dir, "f.txt"), "line1\nline2\nline3\nline4\n");
  const diff = [
    "--- a/f.txt",
    "+++ b/f.txt",
    "@@ -2,4 +2,4 @@",       // deliberately wrong counts (real body is 3 old / 3 new)
    " line1",
    "-line2",
    "+line2-CHANGED",
    " line3",
    "",
  ].join("\n");
  const stats = apply(dir, diff);
  assert.deepStrictEqual(stats.errors, [], "no apply errors");
  assert.strictEqual(fs.readFileSync(path.join(dir, "f.txt"), "utf8"), "line1\nline2-CHANGED\nline3\nline4\n");
});

// (b) Trailing-whitespace drift on a context line.
test("tolerates trailing-whitespace drift in context", (dir) => {
  fs.writeFileSync(path.join(dir, "f.txt"), "alpha\nbeta\ngamma\n");
  const diff = [
    "--- a/f.txt",
    "+++ b/f.txt",
    "@@ -1,3 +1,3 @@",
    " alpha  ",              // diff has trailing spaces the file doesn't
    "-beta",
    "+beta2",
    " gamma",
    "",
  ].join("\n");
  const stats = apply(dir, diff);
  assert.deepStrictEqual(stats.errors, [], "no apply errors");
  const out = fs.readFileSync(path.join(dir, "f.txt"), "utf8");
  assert.strictEqual(out, "alpha\nbeta2\ngamma\n");
  // The file's own context line ("alpha" w/o trailing spaces) is preserved.
  assert.ok(out.startsWith("alpha\n"), "file context whitespace preserved");
});

// (c) Indent drift on CONTEXT lines (the realistic case): the diff's context is
// mis-indented but the +/- lines are correct. The fix still lands, and the file's
// own context indentation is preserved (added lines come from the diff verbatim).
test("tolerates indent drift in context", (dir) => {
  fs.writeFileSync(path.join(dir, "f.txt"), "def f():\n    return 1\n    x = 2\n");
  const diff = [
    "--- a/f.txt",
    "+++ b/f.txt",
    "@@ -1,3 +1,3 @@",
    "def f():",              // context: should be unindented — matches
    "-    return 1",         // removed line: correct indent
    "+    return 42",        // added line: correct indent
    "  x = 2",               // context: under-indented (file has 4 spaces) — fuzzy-matched
    "",
  ].join("\n");
  const stats = apply(dir, diff);
  assert.deepStrictEqual(stats.errors, [], "no apply errors");
  assert.strictEqual(fs.readFileSync(path.join(dir, "f.txt"), "utf8"), "def f():\n    return 42\n    x = 2\n");
});

// (d) CRLF preservation.
test("preserves CRLF line endings", (dir) => {
  fs.writeFileSync(path.join(dir, "f.txt"), "one\r\ntwo\r\nthree\r\n");
  const diff = [
    "--- a/f.txt",
    "+++ b/f.txt",
    "@@ -1,3 +1,3 @@",
    " one",
    "-two",
    "+two-X",
    " three",
    "",
  ].join("\n");
  const stats = apply(dir, diff);
  assert.deepStrictEqual(stats.errors, [], "no apply errors");
  assert.strictEqual(fs.readFileSync(path.join(dir, "f.txt"), "utf8"), "one\r\ntwo-X\r\nthree\r\n");
});

// (e) New-file creation still works.
test("creates a new file", (dir) => {
  const diff = [
    "--- /dev/null",
    "+++ b/new.txt",
    "@@ -0,0 +1,2 @@",
    "+hello",
    "+world",
    "",
  ].join("\n");
  const stats = apply(dir, diff);
  assert.deepStrictEqual(stats.errors, [], "no apply errors");
  assert.deepStrictEqual(stats.created, ["new.txt"]);
  assert.strictEqual(fs.readFileSync(path.join(dir, "new.txt"), "utf8"), "hello\nworld");
});

// (f) Genuinely-absent context is still rejected (no false positives).
test("rejects a hunk whose context is not in the file", (dir) => {
  fs.writeFileSync(path.join(dir, "f.txt"), "aaa\nbbb\nccc\n");
  const diff = [
    "--- a/f.txt",
    "+++ b/f.txt",
    "@@ -1,2 +1,2 @@",
    " nonexistent-context",
    "-zzz",
    "+yyy",
    "",
  ].join("\n");
  const stats = apply(dir, diff);
  assert.strictEqual(stats.errors.length, 1, "unlocatable hunk reported as an error");
  assert.strictEqual(fs.readFileSync(path.join(dir, "f.txt"), "utf8"), "aaa\nbbb\nccc\n", "file untouched on failure");
});

console.log(`\n${passed + failed} tests: ${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
