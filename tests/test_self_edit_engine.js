/**
 * Self-Edit Engine Unit Tests
 * Tests the engine helpers directly without a live server.
 */

const assert = require("assert");
const path = require("path");
const fs = require("fs");
const {
  isPathSafe,
  sanitizeBranchName,
  parseUnifiedDiff,
  validateDiff,
  applyPatch,
  isAllowedTest,
  requireSafePaths,
} = require("../apps/lantern-garage/lib/self-edit-engine");

const repoRoot = path.resolve(__dirname, "..");

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
  console.log("\nSelf-Edit Engine Unit Tests\n");

  // ── Path safety ───────────────────────────────────────────────────────
  console.log("Path safety");

  test("allows paths inside repo", () => {
    assert.strictEqual(isPathSafe(repoRoot, "apps/lantern-garage/server.js"), true);
    assert.strictEqual(isPathSafe(repoRoot, "data/test.json"), true);
  });

  test("rejects paths outside repo", () => {
    assert.strictEqual(isPathSafe(repoRoot, "../../outside.js"), false);
    assert.strictEqual(isPathSafe(repoRoot, "/etc/passwd"), false);
  });

  test("rejects traversal attempts", () => {
    assert.strictEqual(isPathSafe(repoRoot, "foo/../../../etc/passwd"), false);
  });

  test("requireSafePaths throws on unsafe paths", () => {
    assert.throws(() => requireSafePaths(repoRoot, ["safe.js", "../../bad.js"]), /unsafe_path/);
  });

  // ── Branch safety ─────────────────────────────────────────────────────
  console.log("Branch safety");

  test("sanitizes branch names", () => {
    assert.strictEqual(sanitizeBranchName("fix the bug"), "auto/fix-the-bug");
    assert.strictEqual(sanitizeBranchName("Feature!!!123"), "auto/feature123");
    assert.strictEqual(sanitizeBranchName(""), "auto/auto-change");
  });

  test("prefixes with auto/", () => {
    const branch = sanitizeBranchName("my-feature");
    assert.ok(branch.startsWith("auto/"), "branch should start with auto/");
  });

  // ── Diff parsing ──────────────────────────────────────────────────────
  console.log("Diff parsing");

  test("parses a valid unified diff", () => {
    const diff = `--- a/test.js
+++ b/test.js
@@ -1,3 +1,4 @@
 line one
+new line
 line two
 line three
`;
    const files = parseUnifiedDiff(diff);
    assert.strictEqual(files.length, 1);
    assert.strictEqual(files[0].oldFile, "a/test.js");
    assert.strictEqual(files[0].newFile, "b/test.js");
    assert.strictEqual(files[0].hunks.length, 1);
    assert.strictEqual(files[0].hunks[0].oldStart, 1);
    assert.strictEqual(files[0].hunks[0].oldCount, 3);
    assert.strictEqual(files[0].hunks[0].newCount, 4);
  });

  test("returns empty for invalid diff", () => {
    const files = parseUnifiedDiff("not a diff");
    assert.strictEqual(files.length, 0);
  });

  // ── Diff validation ───────────────────────────────────────────────────
  console.log("Diff validation");

  test("accepts safe diff", () => {
    const diff = `--- a/apps/lantern-garage/server.js
+++ b/apps/lantern-garage/server.js
@@ -1,1 +1,2 @@
 // existing
+// new
`;
    assert.doesNotThrow(() => validateDiff(diff, repoRoot));
  });

  test("rejects diff with unsafe paths", () => {
    const diff = `--- a/../../outside.js
+++ b/../../outside.js
@@ -1,1 +1,2 @@
 // existing
+// new
`;
    assert.throws(() => validateDiff(diff, repoRoot), /unsafe_path/);
  });

  test("rejects diff that is too large", () => {
    const hugeDiff = "--- a/file.js\n+++ b/file.js\n" + "@@ -1,1 +1,2 @@\n".repeat(100000);
    assert.throws(() => validateDiff(hugeDiff, repoRoot), /diff_too_large/);
  });

  // ── Patch application ─────────────────────────────────────────────────
  console.log("Patch application");

  test("applies a simple patch", () => {
    const testFile = path.join(repoRoot, "tests", "_self_edit_test_target.js");
    fs.writeFileSync(testFile, "line one\nline two\nline three\n", "utf8");
    const diff = `--- a/tests/_self_edit_test_target.js
+++ b/tests/_self_edit_test_target.js
@@ -1,3 +1,4 @@
 line one
+new line
 line two
 line three
`;
    const stats = applyPatch(repoRoot, diff);
    assert.ok(stats.changed.includes("tests/_self_edit_test_target.js"), "should list changed file");
    const content = fs.readFileSync(testFile, "utf8");
    assert.ok(content.includes("new line"), "patch should add new line");
    fs.unlinkSync(testFile);
  });

  test("reports errors for bad hunks", () => {
    const testFile = path.join(repoRoot, "tests", "_self_edit_test_target2.js");
    fs.writeFileSync(testFile, "line one\nline two\n", "utf8");
    const diff = `--- a/tests/_self_edit_test_target2.js
+++ b/tests/_self_edit_test_target2.js
@@ -1,2 +1,2 @@
- wrong line
+ replaced
 line two
`;
    const stats = applyPatch(repoRoot, diff);
    assert.strictEqual(stats.errors.length, 1, "should record a hunk mismatch error");
    fs.unlinkSync(testFile);
  });

  // ── Test allowlist ──────────────────────────────────────────────────
  console.log("Test allowlist");

  test("allows known test commands", () => {
    assert.strictEqual(isAllowedTest("node tests/test_dream_journal_api.js"), true);
    assert.strictEqual(isAllowedTest("npm test"), true);
    assert.strictEqual(isAllowedTest("python -m pytest tests/test_dashboard_ux.py"), true);
  });

  test("rejects unknown test commands", () => {
    assert.strictEqual(isAllowedTest("rm -rf /"), false);
    assert.strictEqual(isAllowedTest("node evil.js"), false);
    assert.strictEqual(isAllowedTest("curl http://bad.com"), false);
  });

  // ── Summary ───────────────────────────────────────────────────────────
  console.log(`\n${passed} passed, ${failed} failed`);
  process.exit(failed > 0 ? 1 : 0);
}

run();
