/**
 * Shadow Trading Engine Tests
 *
 * Validates that the shadow trading engine correctly simulates
 * trades and calculates performance metrics without broker execution.
 */

"use strict";

const ShadowTradingEngine = require("../lib/shadow-trading-engine");

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

// Test 1: Shadow trade execution
test("Shadow trading engine executes simulated trades", () => {
  const engine = new ShadowTradingEngine();

  const trade = {
    ticker: "AAPL",
    side: "BUY",
    quantity: 10,
    confidence: 0.75,
  };

  const result = engine.simulateTrade(trade, 150);

  assert(result.success, "Trade simulated successfully");
  assert(result.trade.ticker === "AAPL", "Trade ticker correct");
  assert(result.trade.entryPrice === 150, "Entry price recorded");
  assert(result.trade.status === "OPEN", "Trade status is OPEN");
});

// Test 2: Trade closing and P&L calculation
test("Shadow trading calculates P&L on trade close", () => {
  const engine = new ShadowTradingEngine();

  const trade = {
    ticker: "TSLA",
    side: "BUY",
    quantity: 10,
    confidence: 0.5,
  };

  const result = engine.simulateTrade(trade, 200);
  const tradeId = result.trade.tradeId;

  // Close trade with profit
  const closeResult = engine.closeTrade(tradeId, 210);

  assert(closeResult.success, "Trade closed successfully");
  assert(closeResult.trade.pnl > 0, "Profit calculated");
  assert(closeResult.trade.pnl === 100, "P&L correct (10 * (210-200))");
  assert(closeResult.trade.status === "CLOSED", "Status is CLOSED");
});

// Test 3: Losing trade
test("Shadow trading handles losing trades", () => {
  const engine = new ShadowTradingEngine();

  engine.simulateTrade({ ticker: "MSFT", side: "BUY", quantity: 5, confidence: 0.6 }, 300);
  const trades = engine.trades;
  const tradeId = trades[0].tradeId;

  engine.closeTrade(tradeId, 290);

  const metrics = engine.metrics;
  assert(metrics.losingTrades === 1, "Losing trade counted");
  assert(engine.portfolio.pnl < 0, "Portfolio P&L is negative");
});

// Test 4: Metrics calculation
test("Shadow trading calculates performance metrics", () => {
  const engine = new ShadowTradingEngine();

  // Simulate winning trades
  engine.simulateTrade({ ticker: "A", side: "BUY", quantity: 10, confidence: 0.7 }, 100);
  engine.closeTrade(engine.trades[0].tradeId, 110);

  engine.simulateTrade({ ticker: "B", side: "BUY", quantity: 5, confidence: 0.8 }, 200);
  engine.closeTrade(engine.trades[1].tradeId, 210);

  // Simulate losing trade
  engine.simulateTrade({ ticker: "C", side: "BUY", quantity: 8, confidence: 0.5 }, 150);
  engine.closeTrade(engine.trades[2].tradeId, 140);

  const metrics = engine.getMetrics();

  assert(metrics.trades.total === 3, "Trade count correct");
  assert(metrics.trades.winning === 2, "Winning trades counted");
  assert(metrics.trades.losing === 1, "Losing trades counted");
  assert(parseFloat(metrics.trades.winRate) === 66.67, "Win rate calculated");
});

// Test 5: Portfolio tracking
test("Shadow trading tracks portfolio value", () => {
  const engine = new ShadowTradingEngine({ initialCapital: 100000 });

  assert(engine.portfolio.capital === 100000, "Initial capital set");

  engine.simulateTrade({ ticker: "TEST", side: "BUY", quantity: 10, confidence: 0.5 }, 100);
  engine.closeTrade(engine.trades[0].tradeId, 120);

  assert(engine.portfolio.capital === 100200, "Capital updated with profit");
  assert(engine.portfolio.pnl === 200, "P&L tracked");
});

// Test 6: Maximum drawdown calculation
test("Shadow trading calculates maximum drawdown", () => {
  const engine = new ShadowTradingEngine({ initialCapital: 100000 });

  // Series of losing trades to create drawdown
  for (let i = 0; i < 3; i++) {
    engine.simulateTrade(
      { ticker: `LOSS${i}`, side: "BUY", quantity: 10, confidence: 0.3 },
      100
    );
    engine.closeTrade(engine.trades[i].tradeId, 90);  // $100 loss each
  }

  const metrics = engine.getMetrics();
  const maxDrawdown = parseFloat(metrics.performance.maxDrawdown);

  assert(maxDrawdown > 0, "Max drawdown calculated");
  assert(maxDrawdown < 1, "Max drawdown is reasonable");
});

// Test 7: Short trades
test("Shadow trading handles short positions", () => {
  const engine = new ShadowTradingEngine();

  engine.simulateTrade({ ticker: "SHORT", side: "SELL", quantity: 10, confidence: 0.7 }, 200);
  const tradeId = engine.trades[0].tradeId;

  engine.closeTrade(tradeId, 190);  // Profit on short

  const trade = engine.trades[0];
  assert(trade.pnl > 0, "Short profit calculated correctly");
});

// Test 8: Trade history retrieval
test("Shadow trading retrieves trade history", () => {
  const engine = new ShadowTradingEngine();

  // Create 5 trades
  for (let i = 0; i < 5; i++) {
    engine.simulateTrade({ ticker: `SYM${i}`, side: "BUY", quantity: 1, confidence: 0.5 }, 100);
    engine.closeTrade(engine.trades[i].tradeId, 105);
  }

  const history = engine.getTradeHistory(3);

  assert(history.length === 3, "History limited to requested size");
  assert(history[0].status === "CLOSED", "Closed trades in history");
});

// Test 9: Market price updates
test("Shadow trading updates mark-to-market", () => {
  const engine = new ShadowTradingEngine();

  engine.simulateTrade({ ticker: "AAPL", side: "BUY", quantity: 10, confidence: 0.5 }, 150);

  const prices = { AAPL: 160 };
  const mtmPnL = engine.updateMarketPrices(prices);

  assert(mtmPnL === 100, "Mark-to-market P&L correct");
});

// Test 10: Reset functionality
test("Shadow trading resets correctly", () => {
  const engine = new ShadowTradingEngine();

  engine.simulateTrade({ ticker: "TEST", side: "BUY", quantity: 10, confidence: 0.5 }, 100);

  assert(engine.trades.length > 0, "Has trades before reset");

  engine.reset();

  assert(engine.trades.length === 0, "Trades cleared after reset");
  assert(engine.portfolio.capital === 100000, "Capital reset");
  assert(engine.metrics.totalTrades === 0, "Metrics reset");
});

// Test 11: Profit factor calculation
test("Shadow trading calculates profit factor", () => {
  const engine = new ShadowTradingEngine();

  // Create profitable trade
  engine.simulateTrade({ ticker: "WIN", side: "BUY", quantity: 10, confidence: 0.7 }, 100);
  engine.closeTrade(engine.trades[0].tradeId, 110);

  // Create losing trade
  engine.simulateTrade({ ticker: "LOSS", side: "BUY", quantity: 5, confidence: 0.3 }, 100);
  engine.closeTrade(engine.trades[1].tradeId, 80);

  const metrics = engine.getMetrics();
  const profitFactor = parseFloat(metrics.performance.profitFactor);

  assert(profitFactor > 0, "Profit factor calculated");
  assert(profitFactor !== Infinity, "Profit factor is finite");
});

// Test 12: Sharpe ratio calculation
test("Shadow trading calculates Sharpe ratio", () => {
  const engine = new ShadowTradingEngine();

  // Create several trades
  for (let i = 0; i < 3; i++) {
    engine.simulateTrade({ ticker: `T${i}`, side: "BUY", quantity: 1, confidence: 0.5 }, 100);
    engine.closeTrade(engine.trades[i].tradeId, 105 + i);  // Varying returns
  }

  const metrics = engine.getMetrics();
  const sharpeRatio = parseFloat(metrics.performance.sharpeRatio);

  assert(!isNaN(sharpeRatio), "Sharpe ratio calculated");
  assert(sharpeRatio >= 0 || sharpeRatio < 0, "Sharpe ratio is a number");
});

// Test 13: Report generation
test("Shadow trading generates report", () => {
  const engine = new ShadowTradingEngine();

  engine.simulateTrade({ ticker: "RPT", side: "BUY", quantity: 10, confidence: 0.5 }, 100);
  engine.closeTrade(engine.trades[0].tradeId, 110);

  const report = engine.generateReport();

  assert(report.timestamp, "Report has timestamp");
  assert(report.mode === "shadow", "Mode is shadow");
  assert(report.metrics, "Metrics included");
  assert(report.trades, "Trades included");
  assert(report.summary.note.includes("No real orders"), "Shadow trading note present");
});

// Summary
console.log("\n" + "=".repeat(60));
console.log(`Shadow Trading Tests: ${testsPassed} passed, ${testsFailed} failed`);
console.log("=".repeat(60));

if (testsFailed > 0) {
  process.exit(1);
}
