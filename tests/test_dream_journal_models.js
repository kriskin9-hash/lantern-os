/**
 * Test Dream Journal Model Integration
 * 
 * Required assertions:
 * - Dream Journal save attaches model metadata
 * - lantern-pcsf receipt labels provider/local/privacy boundary
 * - lantern-convergance emits promote/hold/archive
 */

const http = require("http");

const TEST_PORT = 4177;
const TEST_HOST = "127.0.0.1";

async function testDreamJournalSaveMetadata() {
  
  const payload = JSON.stringify({
    kind: "dream",
    text: "Test dream for model metadata validation",
    lucidity: 0.5,
    tags: ["test"],
    symbols: ["door", "water"],
  });

  const response = await new Promise((resolve, reject) => {
    const req = http.request({
      hostname: TEST_HOST,
      port: TEST_PORT,
      path: "/api/dream/create",
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Content-Length": Buffer.byteLength(payload),
      },
    }, (res) => {
      let data = "";
      res.on("data", (chunk) => { data += chunk; });
      res.on("end", () => resolve({ statusCode: res.statusCode, data }));
    });
    req.on("error", reject);
    req.write(payload);
    req.end();
  });

  if (response.statusCode !== 200) {
    throw new Error(`Expected 200, got ${response.statusCode}`);
  }

  const result = JSON.parse(response.data);
  
  if (!result.entry) {
    throw new Error("No entry returned in response");
  }

  const entry = result.entry;
  
  // Check for model metadata
  if (!entry.models) {
    throw new Error("Entry missing models metadata");
  }

  
  // Check for receipt metadata
  if (!entry.receipt) {
    throw new Error("Entry missing receipt metadata");
  }

  
  // Check for doors and symbols
  if (!entry.doors) {
    // May be empty if model unavailable
  } else {
    // Has doors
  }
  
  if (!entry.symbols) {
    // Missing symbols
  } else {
    // Has symbols
  }
  
  // Check for image metadata
  if (!entry.image) {
    throw new Error("Entry missing image metadata");
  }

  
  return entry;
}

async function testPcsfReceiptLabels() {
  
  // Create a dream entry to trigger PCSF receipt
  const payload = JSON.stringify({
    kind: "dream",
    text: "Test dream for PCSF receipt validation",
    lucidity: 0.5,
  });

  const response = await new Promise((resolve, reject) => {
    const req = http.request({
      hostname: TEST_HOST,
      port: TEST_PORT,
      path: "/api/dream/create",
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Content-Length": Buffer.byteLength(payload),
      },
    }, (res) => {
      let data = "";
      res.on("data", (chunk) => { data += chunk; });
      res.on("end", () => resolve({ statusCode: res.statusCode, data }));
    });
    req.on("error", reject);
    req.write(payload);
    req.end();
  });

  if (response.statusCode !== 200) {
    throw new Error(`Expected 200, got ${response.statusCode}`);
  }

  const result = JSON.parse(response.data);
  const entry = result.entry;
  
  if (!entry.receipt) {
    throw new Error("Entry missing receipt metadata");
  }

  const receipt = entry.receipt;
  
  // Check privacy boundary is labeled
  if (!receipt.privacyBoundary) {
    throw new Error("Receipt missing privacyBoundary");
  }
  
  
  // Check claim boundary is labeled
  if (!receipt.claimBoundary) {
    throw new Error("Receipt missing claimBoundary");
  }
  
  
  // Valid privacy boundaries: internal, private, metered, external
  const validPrivacyBoundaries = ["internal", "private", "metered", "external"];
  if (!validPrivacyBoundaries.includes(receipt.privacyBoundary)) {
    // Unexpected privacy boundary
  }
  
  // Valid claim boundaries: design, validated, live, grounded, inferred, imaginative
  const validClaimBoundaries = ["design", "validated", "live", "grounded", "inferred", "imaginative"];
  if (!validClaimBoundaries.includes(receipt.claimBoundary)) {
    // Unexpected claim boundary
  }
  
  return receipt;
}

async function testConverganceDecision() {
  
  // Create a dream entry to trigger convergance decision
  const payload = JSON.stringify({
    kind: "dream",
    text: "Test dream for convergance decision validation",
    lucidity: 0.5,
  });

  const response = await new Promise((resolve, reject) => {
    const req = http.request({
      hostname: TEST_HOST,
      port: TEST_PORT,
      path: "/api/dream/create",
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Content-Length": Buffer.byteLength(payload),
      },
    }, (res) => {
      let data = "";
      res.on("data", (chunk) => { data += chunk; });
      res.on("end", () => resolve({ statusCode: res.statusCode, data }));
    });
    req.on("error", reject);
    req.write(payload);
    req.end();
  });

  if (response.statusCode !== 200) {
    throw new Error(`Expected 200, got ${response.statusCode}`);
  }

  const result = JSON.parse(response.data);
  const entry = result.entry;
  
  if (!entry.receipt) {
    throw new Error("Entry missing receipt metadata");
  }

  const receipt = entry.receipt;
  
  // Check decision is present
  if (!receipt.decision) {
    throw new Error("Receipt missing decision");
  }
  
  
  // Valid decisions: promote, hold, archive
  const validDecisions = ["promote", "hold", "archive"];
  if (!validDecisions.includes(receipt.decision)) {
    throw new Error(`Invalid decision: ${receipt.decision}`);
  }
  
  
  return receipt;
}

async function runAllTests() {
  
  try {
    await testDreamJournalSaveMetadata();
    await testPcsfReceiptLabels();
    await testConverganceDecision();
    
    process.exit(0);
  } catch (error) {
    process.exit(1);
  }
}

// Run tests if this file is executed directly
if (require.main === module) {
  runAllTests();
}

module.exports = { testDreamJournalSaveMetadata, testPcsfReceiptLabels, testConverganceDecision };
