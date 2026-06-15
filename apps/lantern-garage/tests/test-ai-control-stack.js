/**
 * AI Control Stack Integration Tests
 *
 * Tests the complete AI control pipeline:
 * Governor → Strategy Router → Budget Controller → Safety Gate → Execution
 */

"use strict";

const AIExecutionGovernor = require("../lib/ai-execution-governor");
const StrategyRouter = require("../lib/strategy-router");
const ExecutionBudgetController = require("../lib/execution-budget-controller");
const AISafetyGate = require("../lib/ai-safety-gate");
const AIControlState = require("../lib/ai-control-state");

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

// Mock breakers and kill switch
class MockKillSwitch {
  constructor() {
    this.active = false;
  }
  isActive() { return this.active; }
  getStatus() { return { activatedAt: null }; }
}

class MockCircuitBreaker {
  constructor() {
    this.active = false;
  }
  isTriggered() { return this.active; }
  getStatus() { return { breakers: {} }; }
}

// Test 1: Complete pipeline with valid trade
test("Valid trade flows through entire control stack", () => {
  const governor = new AIExecutionGovernor();
  const router = new StrategyRouter();
  const budgetController = new ExecutionBudgetController();
  const killSwitch = new MockKillSwitch();
  const breaker = new MockCircuitBreaker();
  const safetyGate = new AISafetyGate(killSwitch, breaker, governor);
  const controlState = new AIControlState();

  // Step 1: Governor evaluates system
  const systemState = {
    shadowPerformance: { winningTrades: 60, totalTrades: 100 },
    dailyStats: { pnl: 0, nav: 100000 },
    volatility: 0.20,
    recentTrades: [],
    circuitBreakerActive: false,
    killSwitchActive: false,
  };

  const govResult = governor.evaluate(systemState);
  assert(govResult.allowed, "Governor allows trade");

  // Step 2: Strategy router selects strategies
  const marketData = {
    volatility: 0.20,
    trendStrength: 0.55,
    deviationFromMean: 0.05,
  };

  const routeResult = router.analyzeMarketAndRoute(marketData);
  assert(routeResult.activeStrategies.length > 0, "Strategies selected");

  // Step 3: Budget controller validates
  const tradeRequest = {
    ticker: "AAPL",
    side: "BUY",
    quantity: 10,
    price: 150,
    stopLoss: 0.02,
  };

  const budgetResult = budgetController.canExecuteNow(tradeRequest, 100000);
  assert(budgetResult.allowed, "Budget allows trade");

  // Step 4: Safety gate final check
  const safetyResult = safetyGate.checkAIPermission();
  assert(safetyResult.allowed, "Safety gate allows execution");

  // Step 5: Record execution
  budgetController.recordExecution("TRADE_001", tradeRequest, 100000);
  controlState.recordTradeExecution();

  assert(controlState.getState().lastAllowedTradeTime !== null, "Trade recorded");
});

// Test 2: Kill switch blocks entire pipeline
test("Kill switch blocks all trades at safety gate", () => {
  const governor = new AIExecutionGovernor();
  const killSwitch = new MockKillSwitch();
  const breaker = new MockCircuitBreaker();
  const safetyGate = new AISafetyGate(killSwitch, breaker, governor);

  killSwitch.active = true;

  const systemState = {
    shadowPerformance: { winningTrades: 80, totalTrades: 100 },
    dailyStats: { pnl: 0, nav: 100000 },
    volatility: 0.15,
    recentTrades: [],
    circuitBreakerActive: false,
    killSwitchActive: true,
  };

  governor.evaluate(systemState);
  const safetyResult = safetyGate.checkAIPermission();

  assert(!safetyResult.allowed, "Kill switch blocks execution");
  assert(safetyResult.violations.length > 0, "Violations recorded");
});

// Test 3: Governor mode restricts strategy selection
test("REDUCED mode restricts available strategies", () => {
  const governor = new AIExecutionGovernor();
  const router = new StrategyRouter();

  const systemState = {
    shadowPerformance: { winningTrades: 50, totalTrades: 100 },  // 50% win rate
    dailyStats: { pnl: -1000, nav: 100000 },
    volatility: 0.20,
    recentTrades: [],
    circuitBreakerActive: false,
    killSwitchActive: false,
  };

  const govResult = governor.evaluate(systemState);
  assert(govResult.mode === "REDUCED", "Governor enters REDUCED mode");
  assert(govResult.positionMultiplier === 0.5, "Position size reduced by 50%");
});

// Test 4: Budget controller enforces hourly limits
test("Budget controller enforces trade limits", () => {
  const budgetController = new ExecutionBudgetController({
    maxTradesPerHour: 3,
    maxTradesPerDay: 20,
  });

  const tradeRequest = {
    ticker: "AAPL",
    side: "BUY",
    quantity: 10,
    price: 150,
    stopLoss: 0.02,
  };

  // Execute max trades
  for (let i = 0; i < 3; i++) {
    const result = budgetController.canExecuteNow(tradeRequest, 100000);
    assert(result.allowed, `Trade ${i + 1} allowed`);
    budgetController.recordExecution(`TRADE_${i}`, tradeRequest, 100000);
  }

  // Next trade should be blocked
  const result = budgetController.canExecuteNow(tradeRequest, 100000);
  assert(!result.allowed, "4th trade blocked by hourly limit");
  assert(result.violations.length > 0, "Violation reported");
});

// Test 5: Control state tracks AI permissions
test("Control state maintains AI execution permissions", () => {
  const controlState = new AIControlState();

  // Initially enabled
  assert(controlState.canExecuteLiveTrades(), "AI can execute initially");

  // Switch to SHADOW_ONLY
  controlState.setMode("SHADOW_ONLY");
  assert(!controlState.canExecuteLiveTrades(), "AI cannot execute in SHADOW_ONLY");

  // Disable completely
  controlState.disableAI("Test disable");
  assert(!controlState.getState().aiEnabled, "AI disabled");

  // Re-enable
  controlState.enableAI("Test enable");
  assert(controlState.getState().aiEnabled, "AI re-enabled");
});

// Test 6: Strategy permissions independent of AI mode
test("Strategy permissions work independently", () => {
  const controlState = new AIControlState();

  // Set strategy permissions
  controlState.setStrategyPermissions({
    trend_following: true,
    mean_reversion: false,
    volatility_breakout: true,
  }, "Test permissions");

  assert(controlState.isStrategyAllowed("trend_following"), "Allowed strategy accessible");
  assert(!controlState.isStrategyAllowed("mean_reversion"), "Blocked strategy inaccessible");
});

// Test 7: Safety gate guard function throws on blocked AI
test("Safety gate guard function throws when AI blocked", () => {
  const governor = new AIExecutionGovernor();
  const killSwitch = new MockKillSwitch();
  const breaker = new MockCircuitBreaker();
  const safetyGate = new AISafetyGate(killSwitch, breaker, governor);

  killSwitch.active = true;

  const tradeRequest = { ticker: "TEST", side: "BUY", quantity: 10 };

  let exceptionThrown = false;
  try {
    safetyGate.guard(tradeRequest);
  } catch (e) {
    exceptionThrown = true;
    assert(e.code === "AI_SAFETY_GATE_BLOCKED", "Correct error code");
  }

  assert(exceptionThrown, "Exception thrown when blocked");
});

// Test 8: Control state history tracking
test("Control state tracks change history", () => {
  const controlState = new AIControlState();

  controlState.setMode("AGGRESSIVE");
  controlState.setMode("REDUCED");
  controlState.disableAI("Test");

  const history = controlState.getHistory();
  assert(history.length >= 3, "History tracks state changes");
});

// Test 9: Position multiplier propagates through stack
test("Governor position multiplier affects budget calculations", () => {
  const governor = new AIExecutionGovernor();
  const budgetController = new ExecutionBudgetController();

  const systemState = {
    shadowPerformance: { winningTrades: 75, totalTrades: 100 },
    dailyStats: { pnl: 0, nav: 100000 },
    volatility: 0.15,
    recentTrades: [],
    circuitBreakerActive: false,
    killSwitchActive: false,
  };

  const govResult = governor.evaluate(systemState);
  assert(govResult.positionMultiplier === 1.5, "AGGRESSIVE multiplier is 1.5x");

  // Budget controller can use this multiplier
  const shadowMetrics = { totalTrades: 100, winningTrades: 75, maxDrawdown: 0 };
  const budgetMultiplier = budgetController.calculatePositionMultiplier(shadowMetrics);
  assert(budgetMultiplier > 1.0, "Budget allows scaling based on performance");
});

// Test 10: Complete control pipeline status report
test("Control stack provides complete status report", () => {
  const governor = new AIExecutionGovernor();
  const killSwitch = new MockKillSwitch();
  const breaker = new MockCircuitBreaker();
  const safetyGate = new AISafetyGate(killSwitch, breaker, governor);

  const systemState = {
    shadowPerformance: { winningTrades: 65, totalTrades: 100 },
    dailyStats: { pnl: 0, nav: 100000 },
    volatility: 0.20,
    recentTrades: [],
    circuitBreakerActive: false,
    killSwitchActive: false,
  };

  governor.evaluate(systemState);
  const report = safetyGate.getSafetyReport();

  assert(report.systems.governor, "Governor status in report");
  assert(report.overallStatus, "Overall status included");
  assert(report.aiAllowed !== undefined, "AI permission status included");
});

// Summary
console.log("\n" + "=".repeat(60));
console.log(`AI Control Stack Tests: ${testsPassed} passed, ${testsFailed} failed`);
console.log("=".repeat(60));

if (testsFailed > 0) {
  process.exit(1);
}
