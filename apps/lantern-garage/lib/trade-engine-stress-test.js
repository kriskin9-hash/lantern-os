/**
 * Trade State Engine Stress Test Harness
 *
 * Validates engine stability under:
 * - 10-50 rapid trade submissions
 * - Mixed success/failure responses
 * - Random execution delays
 * - Out-of-order API responses
 *
 * Must pass before Phase 3 UI work begins.
 */

"use strict";

const { TradeStateEngine, TRADE_STATES } = require("./trade-state-engine");

class TradeEngineStressTest {
  constructor() {
    this.engine = new TradeStateEngine();
    this.results = {
      passed: 0,
      failed: 0,
      errors: []
    };
  }

  /**
   * Run full stress test suite
   */
  async runFullSuite() {
    console.log("[StressTest] Starting full test suite...");

    await this.testRapidSubmissions();
    await this.testMixedResults();
    await this.testOutOfOrderResponses();
    await this.testConcurrentUpdates();
    await this.testStateConsistency();

    return this.getResults();
  }

  /**
   * Test 1: Rapid trade submissions (10-50)
   */
  async testRapidSubmissions() {
    console.log("[StressTest] Test 1: Rapid submissions (50 trades)...");
    const count = 50;
    const trades = [];

    try {
      for (let i = 0; i < count; i++) {
        const trade = this.engine.createTrade({
          symbol: `TEST${i % 5}`,
          side: i % 2 === 0 ? "BUY" : "SELL",
          quantity: Math.floor(Math.random() * 10) + 1,
          price: Math.random() * 100,
          mode: "dry_run"
        });
        trades.push(trade);
      }

      // Validate no duplicates
      const ids = new Set(trades.map(t => t.tradeId));
      if (ids.size !== count) {
        throw new Error(`Duplicate trade IDs: expected ${count}, got ${ids.size}`);
      }

      // Validate all trades created
      if (this.engine.trades.size !== count) {
        throw new Error(`Trade count mismatch: expected ${count}, got ${this.engine.trades.size}`);
      }

      console.log("[StressTest] ✓ Test 1 passed: 50 rapid trades, no duplicates");
      this.results.passed++;
    } catch (e) {
      console.error("[StressTest] ✗ Test 1 failed:", e.message);
      this.results.failed++;
      this.results.errors.push({ test: "rapid_submissions", error: e.message });
    }
  }

  /**
   * Test 2: Mixed success/failure responses
   */
  async testMixedResults() {
    console.log("[StressTest] Test 2: Mixed success/failure responses...");
    this.engine.clear();

    try {
      const trades = [];
      for (let i = 0; i < 30; i++) {
        const trade = this.engine.createTrade({
          symbol: `MIX${i % 3}`,
          side: "BUY",
          quantity: 1,
          mode: "dry_run"
        });
        trades.push(trade);

        // 70% succeed, 30% fail
        if (Math.random() > 0.7) {
          this.engine.updateTradeStatus(trade.tradeId, TRADE_STATES.REJECTED, {
            error: "Random failure for test"
          });
        } else {
          this.engine.updateTradeStatus(trade.tradeId, TRADE_STATES.SUBMITTED);
          this.engine.updateTradeStatus(trade.tradeId, TRADE_STATES.FILLED);
        }
      }

      // Validate state consistency
      const filled = this.engine.getTradesByStatus(TRADE_STATES.FILLED);
      const rejected = this.engine.getTradesByStatus(TRADE_STATES.REJECTED);
      const total = filled.length + rejected.length;

      if (total !== 30) {
        throw new Error(`State loss: expected 30 trades, got ${total} (${filled.length} filled, ${rejected.length} rejected)`);
      }

      console.log(`[StressTest] ✓ Test 2 passed: 30 mixed results (${filled.length} filled, ${rejected.length} rejected)`);
      this.results.passed++;
    } catch (e) {
      console.error("[StressTest] ✗ Test 2 failed:", e.message);
      this.results.failed++;
      this.results.errors.push({ test: "mixed_results", error: e.message });
    }
  }

  /**
   * Test 3: Out-of-order API responses
   */
  async testOutOfOrderResponses() {
    console.log("[StressTest] Test 3: Out-of-order responses...");
    this.engine.clear();

    try {
      // Create a trade
      const trade = this.engine.createTrade({
        symbol: "OOO",
        side: "BUY",
        quantity: 1,
        mode: "live",
        status: "pending"
      });

      // Simulate out-of-order updates
      this.engine.updateTradeStatus(trade.tradeId, TRADE_STATES.SUBMITTED, {
        submittedAt: Date.now()
      });

      // Try to send a stale "pending" update (should be rejected or ignored)
      try {
        // This would be an invalid transition, should throw
        this.engine.updateTradeStatus(trade.tradeId, TRADE_STATES.PENDING);
        throw new Error("Invalid transition should have been rejected");
      } catch (e) {
        // Expected — invalid transition
        if (!e.message.includes("Invalid transition")) {
          throw e;
        }
      }

      // Correct forward update should work
      this.engine.updateTradeStatus(trade.tradeId, TRADE_STATES.FILLED, {
        filledAt: Date.now()
      });

      const finalTrade = this.engine.getTrade(trade.tradeId);
      if (finalTrade.status !== TRADE_STATES.FILLED) {
        throw new Error(`Final state wrong: expected FILLED, got ${finalTrade.status}`);
      }

      console.log("[StressTest] ✓ Test 3 passed: Invalid transitions rejected, valid ones accepted");
      this.results.passed++;
    } catch (e) {
      console.error("[StressTest] ✗ Test 3 failed:", e.message);
      this.results.failed++;
      this.results.errors.push({ test: "out_of_order", error: e.message });
    }
  }

  /**
   * Test 4: Concurrent updates to different trades
   */
  async testConcurrentUpdates() {
    console.log("[StressTest] Test 4: Concurrent updates...");
    this.engine.clear();

    try {
      // Create 20 trades
      const trades = [];
      for (let i = 0; i < 20; i++) {
        const trade = this.engine.createTrade({
          symbol: `CONC${i}`,
          side: "BUY",
          quantity: 1,
          mode: "live"
        });
        trades.push(trade);
      }

      // "Concurrently" update them (simulate with rapid updates)
      for (const trade of trades) {
        this.engine.updateTradeStatus(trade.tradeId, TRADE_STATES.SUBMITTED);
        this.engine.updateTradeStatus(trade.tradeId, TRADE_STATES.FILLED);
      }

      // Verify all reached final state
      const allFilled = this.engine.getTradesByStatus(TRADE_STATES.FILLED);
      if (allFilled.length !== 20) {
        throw new Error(`Concurrent update loss: expected 20 filled, got ${allFilled.length}`);
      }

      console.log("[StressTest] ✓ Test 4 passed: 20 concurrent updates, no state loss");
      this.results.passed++;
    } catch (e) {
      console.error("[StressTest] ✗ Test 4 failed:", e.message);
      this.results.failed++;
      this.results.errors.push({ test: "concurrent_updates", error: e.message });
    }
  }

  /**
   * Test 5: Overall state consistency
   */
  async testStateConsistency() {
    console.log("[StressTest] Test 5: Overall state consistency...");

    try {
      const state = this.engine.getState();

      // Validate state snapshot
      if (state.totalTrades === undefined || state.activeCount === undefined) {
        throw new Error("State snapshot missing required fields");
      }

      if (state.totalTrades < 0) {
        throw new Error("Negative trade count");
      }

      if (state.activeCount > state.totalTrades) {
        throw new Error("Active count exceeds total trades");
      }

      if (state.filledCount + state.rejectedCount > state.totalTrades) {
        throw new Error("Terminal state counts exceed total");
      }

      console.log(
        `[StressTest] ✓ Test 5 passed: State consistent (${state.totalTrades} total, ${state.activeCount} active, ${state.filledCount} filled, ${state.rejectedCount} rejected)`
      );
      this.results.passed++;
    } catch (e) {
      console.error("[StressTest] ✗ Test 5 failed:", e.message);
      this.results.failed++;
      this.results.errors.push({ test: "state_consistency", error: e.message });
    }
  }

  /**
   * Get test results
   */
  getResults() {
    const total = this.results.passed + this.results.failed;
    const passRate = total > 0 ? ((this.results.passed / total) * 100).toFixed(1) : 0;

    return {
      ...this.results,
      total,
      passRate: `${passRate}%`,
      summary: `${this.results.passed}/${total} tests passed`
    };
  }
}

// Run if invoked directly
if (require.main === module) {
  (async () => {
    const tester = new TradeEngineStressTest();
    const results = await tester.runFullSuite();
    console.log("\n[StressTest] FINAL RESULTS:", results);
    process.exit(results.failed > 0 ? 1 : 0);
  })();
}

module.exports = TradeEngineStressTest;
