/**
 * Risk Engine Tests
 *
 * Validates that the risk engine correctly evaluates trades
 * and blocks unsafe positions.
 */

"use strict";

const RiskEngine = require("../lib/risk-engine");

let testsPassed = 0;
let testsFailed = 0;

function assert(condition, message) {
  if (!condition) {
    console.error(`  ✗ FAIL: ${message}`);
    testsFailed++;
  } else {
    testsPassed++;
  }
}

function test(name, fn) {
  console.log(`\n[TEST] ${name}`);
  try {
    fn();
  } catch (e) {
    console.error(`  ✗ EXCEPTION: ${e.message}`);
    testsFailed++;
  }
}

const mockPortfolio = {
  nav: 100000,
  capital: 100000,
};

const mockPositions = [];
const mockDailyStats = {
  pnl: 0,
  trades: 0,
  wins: 0,
};

// Test 1: Approve valid trade
test("Risk engine approves valid small trade", () => {
  const engine = new RiskEngine();

  const trade = {
    ticker: "AAPL",
    side: "BUY",
    quantity: 10,
    price: 150,
  };

  const result = engine.evaluateTrade(trade, mockPortfolio, mockPositions, mockDailyStats);

  assert(result.approved, "Valid trade approved");
  assert(result.violations.length === 0, "No violations");
  assert(result.riskScore < 0.2, "Risk score is low");
});

// Test 2: Reject oversized position
test("Risk engine rejects oversized position", () => {
  const engine = new RiskEngine();

  const trade = {
    ticker: "TSLA",
    side: "BUY",
    quantity: 400,  // 400 * $300 = $120,000 > 5% of $100k NAV
    price: 300,
  };

  const result = engine.evaluateTrade(trade, mockPortfolio, mockPositions, mockDailyStats);

  assert(!result.approved, "Oversized trade rejected");
  assert(result.violations.includes("MAX_POSITION_SIZE"), "Violation recorded");
});

// Test 3: Reject trade during drawdown
test("Risk engine rejects trade when daily loss limit reached", () => {
  const engine = new RiskEngine();

  const trade = {
    ticker: "MSFT",
    side: "BUY",
    quantity: 5,
    price: 300,
  };

  const statsWithLoss = {
    pnl: -2500,  // 2.5% loss on $100k
    trades: 3,
    wins: 1,
  };

  const result = engine.evaluateTrade(trade, mockPortfolio, mockPositions, statsWithLoss);

  assert(!result.approved, "Trade rejected when drawdown limit reached");
  assert(result.violations.includes("DAILY_DRAWDOWN_LIMIT"), "Drawdown violation");
});

// Test 4: Reject duplicate position
test("Risk engine rejects duplicate position", () => {
  const engine = new RiskEngine();

  const existingPositions = [
    {
      ticker: "NVDA",
      quantity: 10,
      side: "BUY",
    },
  ];

  const trade = {
    ticker: "NVDA",  // Same ticker
    side: "BUY",
    quantity: 5,
    price: 800,
  };

  const result = engine.evaluateTrade(trade, mockPortfolio, existingPositions, mockDailyStats);

  assert(!result.approved, "Duplicate position rejected");
  assert(result.violations.includes("EXISTING_POSITION"), "Duplicate violation");
});

// Test 5: Reject too many open positions
test("Risk engine rejects when too many positions open", () => {
  const engine = new RiskEngine();

  const manyPositions = [];
  for (let i = 0; i < 10; i++) {
    manyPositions.push({
      ticker: `SYM${i}`,
      quantity: 1,
      side: "BUY",
    });
  }

  const trade = {
    ticker: "NEW",
    side: "BUY",
    quantity: 1,
    price: 100,
  };

  const result = engine.evaluateTrade(trade, mockPortfolio, manyPositions, mockDailyStats);

  assert(!result.approved, "Trade rejected when position limit reached");
  assert(result.violations.includes("MAX_OPEN_POSITIONS"), "Position count violation");
});

// Test 6: Portfolio risk score calculation
test("Risk engine calculates portfolio risk score", () => {
  const engine = new RiskEngine();

  const positions = [
    { ticker: "A", quantity: 10, side: "BUY", value: 10000 },
    { ticker: "B", quantity: 10, side: "BUY", value: 10000 },
  ];

  const stats = {
    pnl: -500,
    trades: 5,
    wins: 2,
  };

  const riskScore = engine.calculatePortfolioRiskScore(mockPortfolio, positions, stats);

  assert(riskScore >= 0 && riskScore <= 1, "Risk score in valid range");
  assert(riskScore > 0, "Risk score reflects some risk");
});

// Test 7: Risk state classification
test("Risk engine classifies risk states correctly", () => {
  const engine = new RiskEngine();

  assert(engine.getRiskStateName(0.1) === "NORMAL", "Low score = NORMAL");
  assert(engine.getRiskStateName(0.3) === "ELEVATED", "Mid-low score = ELEVATED");
  assert(engine.getRiskStateName(0.6) === "HIGH", "Mid-high score = HIGH");
  assert(engine.getRiskStateName(0.9) === "CRITICAL", "High score = CRITICAL");
});

// Test 8: Multiple violations tracked
test("Risk engine tracks multiple violations", () => {
  const engine = new RiskEngine();

  const positions = [
    { ticker: "EXISTING", quantity: 50, side: "BUY" },
  ];

  const statsWithLoss = {
    pnl: -3000,
    trades: 2,
    wins: 0,
  };

  const trade = {
    ticker: "EXISTING",  // Duplicate
    side: "BUY",
    quantity: 600,  // Also oversized
    price: 300,
  };

  const result = engine.evaluateTrade(trade, mockPortfolio, positions, statsWithLoss);

  assert(result.violations.length >= 2, "Multiple violations recorded");
  assert(!result.approved, "Trade rejected due to multiple violations");
});

// Test 9: Edge case - zero NAV
test("Risk engine handles edge cases gracefully", () => {
  const engine = new RiskEngine();

  const zeroNavPortfolio = { nav: 0, capital: 0 };
  const trade = {
    ticker: "TEST",
    side: "BUY",
    quantity: 10,
    price: 100,
  };

  const result = engine.evaluateTrade(trade, zeroNavPortfolio, mockPositions, mockDailyStats);

  assert(!result.approved, "Rejects trades when NAV is zero");
});

// Test 10: Rationale generation
test("Risk engine generates readable violation rationale", () => {
  const engine = new RiskEngine();

  const trade = {
    ticker: "BAD",
    side: "BUY",
    quantity: 400,
    price: 300,
  };

  const result = engine.evaluateTrade(trade, mockPortfolio, mockPositions, mockDailyStats);

  assert(result.rationale, "Rationale provided");
  assert(result.rationale.length > 0, "Rationale is not empty");
  assert(result.rationale.includes("exceeds"), "Rationale describes violation");
});

// Summary
console.log("\n" + "=".repeat(60));
console.log(`Risk Engine Tests: ${testsPassed} passed, ${testsFailed} failed`);
console.log("=".repeat(60));

if (testsFailed > 0) {
  process.exit(1);
}
