/**
 * Tests for Queue Manager
 * Verifies work queue operations
 */

const fs = require("fs");
const path = require("path");
const QueueManager = require("../src/queue-manager");

// Test setup
const testQueuePath = path.join(__dirname, "..", "data", "test-queue");

function cleanupTestQueue() {
  if (fs.existsSync(testQueuePath)) {
    fs.rmSync(testQueuePath, { recursive: true, force: true });
  }
}

async function runTests() {
  let passed = 0;
  let failed = 0;

  const qm = new QueueManager(testQueuePath);

  // Test 1: Enqueue work
  try {
    const work = await qm.enqueueWork({
      issueNumber: 335,
      title: "Phase 2: Stage Routing",
      description: "Implement stage routing...",
      priority: 5,
    });
    if (work.id === "issue-335" && work.status === "pending") {
      console.log("✓ Test 1: Enqueue work — PASS");
      passed++;
    } else {
      throw new Error("Work item not properly created");
    }
  } catch (e) {
    console.log(`✗ Test 1: Enqueue work — FAIL: ${e.message}`);
    failed++;
  }

  // Test 2: Get next work for agent
  try {
    await qm.enqueueWork({
      issueNumber: 336,
      title: "Phase 3: Door Generation",
      priority: 3,
    });

    const work = await qm.getNextWork("claude");
    if (work.issueNumber === 335 && work.assignedTo === "claude" && work.status === "assigned") {
      console.log("✓ Test 2: Get next work — PASS");
      passed++;
    } else {
      throw new Error("Work not assigned correctly");
    }
  } catch (e) {
    console.log(`✗ Test 2: Get next work — FAIL: ${e.message}`);
    failed++;
  }

  // Test 3: Mark work complete
  try {
    await qm.markComplete("issue-335", { pr: "PR #200", commit: "abc123" });
    const status = await qm.getStatus();

    if (status.completed === 1 && status.assigned === 0) {
      console.log("✓ Test 3: Mark work complete — PASS");
      passed++;
    } else {
      throw new Error("Completion not recorded correctly");
    }
  } catch (e) {
    console.log(`✗ Test 3: Mark work complete — FAIL: ${e.message}`);
    failed++;
  }

  // Test 4: Mark work failed with retry
  try {
    const work2 = await qm.getNextWork("gemini");
    await qm.markFailed("issue-336", "Test error");

    const status = await qm.getStatus();
    if (status.pending === 1 && status.assigned === 0) {
      console.log("✓ Test 4: Mark failed with retry — PASS");
      passed++;
    } else {
      throw new Error("Retry not handled correctly");
    }
  } catch (e) {
    console.log(`✗ Test 4: Mark failed with retry — FAIL: ${e.message}`);
    failed++;
  }

  // Test 5: Get queue status
  try {
    const status = await qm.getStatus();
    if (status.pending >= 0 && status.completed >= 0) {
      console.log("✓ Test 5: Queue status — PASS");
      passed++;
    } else {
      throw new Error("Status not computed correctly");
    }
  } catch (e) {
    console.log(`✗ Test 5: Queue status — FAIL: ${e.message}`);
    failed++;
  }

  // Test 6: List work by status
  try {
    const completed = await qm.listByStatus("completed");
    if (completed.length === 1 && completed[0].issueNumber === 335) {
      console.log("✓ Test 6: List by status — PASS");
      passed++;
    } else {
      throw new Error("List not filtered correctly");
    }
  } catch (e) {
    console.log(`✗ Test 6: List by status — FAIL: ${e.message}`);
    failed++;
  }

  // Summary
  console.log(`\n[Queue Manager Tests] Passed: ${passed}/6, Failed: ${failed}/6`);

  // Cleanup
  cleanupTestQueue();

  return failed === 0;
}

if (require.main === module) {
  runTests()
    .then((success) => {
      process.exit(success ? 0 : 1);
    })
    .catch((err) => {
      console.error("Test error:", err);
      process.exit(1);
    });
}

module.exports = { runTests };
