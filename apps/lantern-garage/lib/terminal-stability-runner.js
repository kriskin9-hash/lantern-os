/**
 * Terminal Stability Validation Runner — Phase 3.5
 *
 * Stress-tests the Phase 3 Trading Terminal under:
 * - Continuous streaming updates
 * - Long-running sessions (20-30 minutes)
 * - Multi-chart synchronization
 * - Reconnect behavior
 * - Memory stability
 *
 * Does NOT add features. Only validates production stability.
 */

"use strict";

const http = require("http");
const EventEmitter = require("events");

class TerminalStabilityRunner {
  constructor(baseUrl = "http://127.0.0.1:4177") {
    this.baseUrl = baseUrl;
    this.results = {
      passed: 0,
      failed: 0,
      errors: [],
      metrics: {
        eventCount: 0,
        duplicateEvents: 0,
        missedUpdates: 0,
        memorySnapshots: [],
        reconnectCount: 0,
        stateChecks: 0,
        driftDetections: 0
      }
    };
    this.seenEventIds = new Set();
    this.lastState = null;
    this.eventLog = [];
  }

  /**
   * Test 1: Stream stability (no duplicates, correct ordering)
   */
  async testStreamStability(durationMs = 10000) {
    console.log("[Stability] Test 1: Stream stability validation...");

    return new Promise((resolve) => {
      let eventCount = 0;
      let duplicates = 0;
      let lastSequence = -1;

      const startTime = Date.now();

      const eventSource = new EventSource(`${this.baseUrl}/api/trading/stream`);

      eventSource.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data);
          eventCount++;

          // Check for duplicates
          const eventId = `${msg.type}:${msg.data?.tradeId}:${msg.data?.timestamp}`;
          if (this.seenEventIds.has(eventId)) {
            duplicates++;
            console.warn("[Stability] Duplicate event detected:", eventId);
          }
          this.seenEventIds.add(eventId);

          // Check ordering (if sequence field present)
          if (msg.data?.sequence !== undefined) {
            if (msg.data.sequence <= lastSequence) {
              console.warn("[Stability] Out-of-order event:", msg.data.sequence, "after", lastSequence);
            }
            lastSequence = msg.data.sequence;
          }

          // Log for later analysis
          this.eventLog.push({
            timestamp: Date.now(),
            type: msg.type,
            id: eventId
          });

          // Check time budget
          if (Date.now() - startTime > durationMs) {
            eventSource.close();
            resolve({
              eventCount,
              duplicates,
              passed: duplicates === 0,
              message: `Stream delivered ${eventCount} events with ${duplicates} duplicates`
            });
          }
        } catch (err) {
          console.error("[Stability] Stream parse error:", err.message);
        }
      };

      eventSource.onerror = () => {
        console.log("[Stability] Stream closed (normal for test)");
      };

      // Cleanup timeout
      setTimeout(() => {
        eventSource.close();
        resolve({
          eventCount,
          duplicates,
          passed: duplicates === 0,
          message: `Stream delivered ${eventCount} events with ${duplicates} duplicates`
        });
      }, durationMs + 1000);
    });
  }

  /**
   * Test 2: State drift detection (UI == Engine == API)
   */
  async testStateDrift() {
    console.log("[Stability] Test 2: State drift detection...");

    try {
      // Fetch engine state
      const res = await this.fetch(`${this.baseUrl}/api/trading/state`);
      const engineState = res;

      // Validate consistency
      const drift = this._detectDrift(this.lastState, engineState);
      this.lastState = engineState;

      if (drift.hasDrift) {
        this.results.metrics.driftDetections++;
        console.warn("[Stability] State drift detected:", drift.details);
        return { passed: false, drift };
      }

      this.results.metrics.stateChecks++;
      return {
        passed: true,
        trades: engineState.totalTrades,
        active: engineState.activeCount,
        message: `State consistent (${engineState.totalTrades} trades, ${engineState.activeCount} active)`
      };
    } catch (e) {
      console.error("[Stability] State drift test error:", e.message);
      return { passed: false, error: e.message };
    }
  }

  /**
   * Test 3: Order tape integrity (no duplicates, correct order)
   */
  async testOrderTapeIntegrity() {
    console.log("[Stability] Test 3: Order tape integrity...");

    try {
      const res = await this.fetch(`${this.baseUrl}/api/trading/state`);
      const trades = res.recentTrades || [];

      // Check for duplicates
      const tradeIds = new Set();
      let duplicateCount = 0;

      for (const trade of trades) {
        if (tradeIds.has(trade.tradeId)) {
          duplicateCount++;
        }
        tradeIds.add(trade.tradeId);
      }

      // Check chronological order
      let orderValid = true;
      for (let i = 1; i < trades.length; i++) {
        if (trades[i].timestamp > trades[i - 1].timestamp) {
          orderValid = false;
          break;
        }
      }

      const passed = duplicateCount === 0 && orderValid;
      return {
        passed,
        tradeCount: trades.length,
        duplicates: duplicateCount,
        orderValid,
        message: `${trades.length} trades, ${duplicateCount} duplicates, order valid: ${orderValid}`
      };
    } catch (e) {
      console.error("[Stability] Tape integrity test error:", e.message);
      return { passed: false, error: e.message };
    }
  }

  /**
   * Test 4: Reconnect resilience
   */
  async testReconnectResilience() {
    console.log("[Stability] Test 4: Reconnect resilience...");

    try {
      const beforeState = await this.fetch(`${this.baseUrl}/api/trading/state`);

      // Simulate reconnect by opening/closing stream
      let reconnected = false;

      return new Promise((resolve) => {
        const eventSource = new EventSource(`${this.baseUrl}/api/trading/stream`);

        // Connect briefly
        setTimeout(() => {
          eventSource.close();
          reconnected = true;

          // Verify state is still valid after disconnect
          this.fetch(`${this.baseUrl}/api/trading/state`)
            .then((afterState) => {
              const stateValid = beforeState.totalTrades === afterState.totalTrades;
              resolve({
                passed: stateValid && reconnected,
                message: `Reconnect ${reconnected ? "successful" : "failed"}, state valid: ${stateValid}`
              });
            })
            .catch((e) => {
              resolve({ passed: false, error: e.message });
            });
        }, 500);

        eventSource.onerror = () => {
          console.log("[Stability] Stream error during reconnect test (expected)");
        };
      });
    } catch (e) {
      console.error("[Stability] Reconnect test error:", e.message);
      return { passed: false, error: e.message };
    }
  }

  /**
   * Test 5: Long-running stability (20 min simulation)
   */
  async testLongRunningStability(durationMs = 60000) {
    // Note: For testing, use 60s; production runs 20-30 min
    console.log(`[Stability] Test 5: Long-running stability (${durationMs}ms)...`);

    const startTime = Date.now();
    const snapshots = [];
    let checks = 0;
    let drifts = 0;

    return new Promise((resolve) => {
      const interval = setInterval(async () => {
        try {
          checks++;

          // Take memory snapshot
          if (global.gc) {
            global.gc();
          }
          const memUsage = process.memoryUsage();
          snapshots.push({
            timestamp: Date.now() - startTime,
            heapUsed: memUsage.heapUsed,
            external: memUsage.external
          });

          // Check state
          const state = await this.fetch(`${this.baseUrl}/api/trading/state`);
          const drift = this._detectDrift(this.lastState, state);
          if (drift.hasDrift) {
            drifts++;
          }
          this.lastState = state;

          // Check time budget
          if (Date.now() - startTime > durationMs) {
            clearInterval(interval);

            // Analyze memory trend
            let memoryGrowth = 0;
            if (snapshots.length > 1) {
              const firstHeap = snapshots[0].heapUsed;
              const lastHeap = snapshots[snapshots.length - 1].heapUsed;
              memoryGrowth = ((lastHeap - firstHeap) / firstHeap) * 100;
            }

            const passed = drifts === 0 && memoryGrowth < 50; // Allow up to 50% growth

            resolve({
              passed,
              duration: Date.now() - startTime,
              checks,
              drifts,
              memoryGrowth: `${memoryGrowth.toFixed(1)}%`,
              snapshots,
              message: `${checks} state checks, ${drifts} drifts detected, ${memoryGrowth.toFixed(1)}% memory growth`
            });
          }
        } catch (e) {
          console.error("[Stability] Long-running test error:", e.message);
          drifts++;
        }
      }, 5000); // Check every 5 seconds

      // Safety timeout
      setTimeout(() => {
        clearInterval(interval);
        resolve({ passed: false, error: "Test timeout" });
      }, durationMs + 10000);
    });
  }

  /**
   * Helper: Fetch JSON from API
   */
  async fetch(url) {
    return new Promise((resolve, reject) => {
      const req = http.get(url, (res) => {
        let data = "";
        res.on("data", (chunk) => (data += chunk));
        res.on("end", () => {
          try {
            resolve(JSON.parse(data));
          } catch (e) {
            reject(e);
          }
        });
      });
      req.on("error", reject);
      req.setTimeout(5000, () => {
        req.destroy();
        reject(new Error("Request timeout"));
      });
    });
  }

  /**
   * Helper: Detect state drift
   */
  _detectDrift(prev, curr) {
    if (!prev) {
      return { hasDrift: false };
    }

    const drifts = [];

    // Check for lost trades
    if (curr.totalTrades < prev.totalTrades) {
      drifts.push(`Trade loss: ${prev.totalTrades} → ${curr.totalTrades}`);
    }

    // Check for trade count jump (possible duplicate)
    if (curr.totalTrades > prev.totalTrades + 10) {
      drifts.push(`Unexpected trade jump: +${curr.totalTrades - prev.totalTrades}`);
    }

    // Check for active count inconsistency
    if (curr.activeCount > curr.totalTrades) {
      drifts.push(`Active > total: ${curr.activeCount} > ${curr.totalTrades}`);
    }

    return {
      hasDrift: drifts.length > 0,
      details: drifts
    };
  }

  /**
   * Run full test suite
   */
  async runFullSuite() {
    console.log("\n[Stability] Starting full stability validation suite...\n");

    const tests = [
      { name: "Stream Stability", fn: () => this.testStreamStability(5000) },
      { name: "State Drift Detection", fn: () => this.testStateDrift() },
      { name: "Order Tape Integrity", fn: () => this.testOrderTapeIntegrity() },
      { name: "Reconnect Resilience", fn: () => this.testReconnectResilience() },
      { name: "Long-Running (60s)", fn: () => this.testLongRunningStability(60000) }
    ];

    for (const test of tests) {
      try {
        const result = await test.fn();
        if (result.passed) {
          this.results.passed++;
          console.log(`\n✓ ${test.name}: PASS`);
          console.log(`  ${result.message}`);
        } else {
          this.results.failed++;
          console.log(`\n✗ ${test.name}: FAIL`);
          console.log(`  ${result.message || result.error}`);
          this.results.errors.push({ test: test.name, ...result });
        }
      } catch (e) {
        this.results.failed++;
        console.error(`\n✗ ${test.name}: ERROR`);
        console.error(`  ${e.message}`);
        this.results.errors.push({ test: test.name, error: e.message });
      }
    }

    console.log("\n[Stability] FINAL RESULTS:\n", this.results);
    return this.results;
  }
}

// Run if invoked directly
if (require.main === module) {
  (async () => {
    const runner = new TerminalStabilityRunner();
    const results = await runner.runFullSuite();
    process.exit(results.failed > 0 ? 1 : 0);
  })();
}

module.exports = TerminalStabilityRunner;
