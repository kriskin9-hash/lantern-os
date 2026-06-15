/**
 * AI Governor Tests
 *
 * Validates that the governor correctly evaluates system conditions
 * and determines AI execution modes.
 */

"use strict";

const AIExecutionGovernor = require("../lib/ai-execution-governor");

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

// Test 1: High win rate → AGGRESSIVE mode
test("Governor enables AGGRESSIVE mode on high win rate", () => {
  const governor = new AIExecutionGovernor();

  const systemState = {
    shadowPerformance: {
      winningTrades: 70,
      totalTrades: 100,
    },
    dailyStats: { pnl: 500, nav: 100000 },
    volatility: 0.20,
    recentTrades: [],
    circuitBreakerActive: false,
    killSwitchActive: false,
  };

  const result = governor.evaluate(systemState);

  assert(result.mode === "AGGRESSIVE", "Mode is AGGRESSIVE with high win rate");
  assert(result.allowed, "AI allowed in AGGRESSIVE mode");
  assert(result.positionMultiplier > 1.0, "Position multiplier increased");
});

// Test 2: Low win rate → REDUCED mode
test("Governor restricts to REDUCED mode on low win rate", () => {
  const governor = new AIExecutionGovernor();

  const systemState = {
    shadowPerformance: {
      winningTrades: 50,
      totalTrades: 100,  // 50% win rate
    },
    dailyStats: { pnl: -500, nav: 100000 },
    volatility: 0.20,
    recentTrades: [],
    circuitBreakerActive: false,
    killSwitchActive: false,
  };

  const result = governor.evaluate(systemState);

  assert(result.mode === "REDUCED", "Mode is REDUCED with 50% win rate");
  assert(result.positionMultiplier < 1.0, "Position multiplier reduced");
});

// Test 3: Excessive drawdown → SHADOW_ONLY mode
test("Governor enforces SHADOW_ONLY mode on excessive drawdown", () => {
  const governor = new AIExecutionGovernor();

  const systemState = {
    shadowPerformance: {
      winningTrades: 50,
      totalTrades: 100,
    },
    dailyStats: { pnl: -3000, nav: 100000 },  // 3% drawdown
    volatility: 0.20,
    recentTrades: [],
    circuitBreakerActive: false,
    killSwitchActive: false,
  };

  const result = governor.evaluate(systemState);

  assert(result.mode === "SHADOW_ONLY", "Mode is SHADOW_ONLY on excessive drawdown");
  assert(result.positionMultiplier === 0.0, "Position multiplier is zero (no live trading)");
});

// Test 4: Kill switch active → OFF mode
test("Governor disables AI when kill switch active", () => {
  const governor = new AIExecutionGovernor();

  const systemState = {
    shadowPerformance: {
      winningTrades: 70,
      totalTrades: 100,
    },
    dailyStats: { pnl: 0, nav: 100000 },
    volatility: 0.20,
    recentTrades: [],
    circuitBreakerActive: false,
    killSwitchActive: true,  // Kill switch triggered
  };

  const result = governor.evaluate(systemState);

  assert(result.mode === "OFF", "Mode is OFF when kill switch active");
  assert(!result.allowed, "AI not allowed when kill switch active");
});

// Test 5: Circuit breaker active → OFF mode
test("Governor disables AI when circuit breaker active", () => {
  const governor = new AIExecutionGovernor();

  const systemState = {
    shadowPerformance: {
      winningTrades: 70,
      totalTrades: 100,
    },
    dailyStats: { pnl: 0, nav: 100000 },
    volatility: 0.20,
    recentTrades: [],
    circuitBreakerActive: true,  // Breaker triggered
    killSwitchActive: false,
  };

  const result = governor.evaluate(systemState);

  assert(result.mode === "OFF", "Mode is OFF when circuit breaker active");
  assert(!result.allowed, "AI not allowed when breaker active");
});

// Test 6: High volatility reduces mode
test("Governor reduces mode on high volatility", () => {
  const governor = new AIExecutionGovernor();

  const systemState = {
    shadowPerformance: {
      winningTrades: 70,
      totalTrades: 100,
    },
    dailyStats: { pnl: 0, nav: 100000 },
    volatility: 0.50,  // High volatility
    recentTrades: [],
    circuitBreakerActive: false,
    killSwitchActive: false,
  };

  const result = governor.evaluate(systemState);

  assert(result.mode === "REDUCED", "Mode reduced on high volatility");
});

// Test 7: Consecutive losses trigger safety
test("Governor responds to consecutive losses", () => {
  const governor = new AIExecutionGovernor();

  const systemState = {
    shadowPerformance: {
      winningTrades: 30,
      totalTrades: 100,
    },
    dailyStats: { pnl: 0, nav: 100000 },
    volatility: 0.20,
    recentTrades: [
      { pnl: -100 },
      { pnl: -200 },
      { pnl: -150 },  // 3 consecutive losses
    ],
    circuitBreakerActive: false,
    killSwitchActive: false,
  };

  const result = governor.evaluate(systemState);

  assert(result.mode === "SHADOW_ONLY", "Mode is SHADOW_ONLY with 3 consecutive losses");
});

// Test 8: isAllowed() method
test("Governor isAllowed() reflects permission correctly", () => {
  const governor = new AIExecutionGovernor();

  let systemState = {
    shadowPerformance: { winningTrades: 70, totalTrades: 100 },
    dailyStats: { pnl: 0, nav: 100000 },
    volatility: 0.20,
    recentTrades: [],
    circuitBreakerActive: false,
    killSwitchActive: false,
  };

  governor.evaluate(systemState);
  assert(governor.isAllowed(), "AI allowed in good conditions");

  systemState.killSwitchActive = true;
  governor.evaluate(systemState);
  assert(!governor.isAllowed(), "AI not allowed when kill switch active");
});

// Test 9: Position multiplier scaling
test("Governor calculates correct position multiplier", () => {
  const governor = new AIExecutionGovernor();

  const systemState = {
    shadowPerformance: {
      winningTrades: 75,
      totalTrades: 100,  // 75% win rate
    },
    dailyStats: { pnl: 0, nav: 100000 },
    volatility: 0.15,
    recentTrades: [],
    circuitBreakerActive: false,
    killSwitchActive: false,
  };

  const result = governor.evaluate(systemState);

  assert(result.positionMultiplier === 1.5, "AGGRESSIVE mode multiplier is 1.5x");
});

// Test 10: Evaluation with no performance data
test("Governor handles missing performance data gracefully", () => {
  const governor = new AIExecutionGovernor();

  const systemState = {
    shadowPerformance: null,  // No data yet
    dailyStats: { pnl: 0, nav: 100000 },
    volatility: 0.20,
    recentTrades: [],
    circuitBreakerActive: false,
    killSwitchActive: false,
  };

  const result = governor.evaluate(systemState);

  assert(result.allowed, "AI allowed even with no performance data (default to NORMAL)");
  assert(result.mode === "NORMAL", "Default to NORMAL mode");
});

// Summary
console.log("\n" + "=".repeat(60));
console.log(`AI Governor Tests: ${testsPassed} passed, ${testsFailed} failed`);
console.log("=".repeat(60));

if (testsFailed > 0) {
  process.exit(1);
}
