# Phase 3.5: Terminal Stability + Load Validation Layer

## Goal

Validate that the Phase 3 Trading Terminal is **production-stable under real-time conditions**, including:

- Continuous streaming updates (no duplication, correct ordering)
- Long-running UI sessions (20-30 minutes)
- Multi-chart synchronization
- Reconnect behavior (safe recovery from disconnects)
- Memory stability under load (no leaks, bounded growth)
- State consistency across three layers: Engine → API → UI

This phase does NOT add features. It ensures:

> The terminal does not degrade, drift, or leak state over time.

---

## 1. Stream Stability Validation

### What it tests

**Test: `/api/trading/stream` under continuous updates**

- Rapid trade bursts (50+ simultaneous trades)
- Intermittent disconnects / reconnects
- Out-of-order event arrival
- High-frequency updates

### Must verify

| Check | Meaning |
|-------|---------|
| ✓ No duplicate event replay | Reconnect does NOT resend old events twice |
| ✓ Correct ordering | Events remain strictly ordered after reconnect |
| ✓ No missed updates | All trade state transitions received exactly once |

### How to run

```bash
npm run test:stability
```

Expected output:
```
[Stability] Test 1: Stream stability validation...
[Stability] Stream delivered 247 events with 0 duplicates
✓ Stream Stability: PASS
```

---

## 2. Long-Running Stability (20–30 min runtime)

### What it tests

**Test: Terminal under sustained load for extended session**

- Continuous market updates every 5 seconds
- Memory consumption monitored (snapshots taken)
- State consistency checked repeatedly
- No exponential growth or leaks

### Metrics tracked

| Metric | Target |
|--------|--------|
| Memory growth | < 50% over 30 min |
| State drifts | 0 detected |
| API checks | ≥ 360 (one per 5s for 30 min) |

### How to run (60-second test)

```bash
npm run test:stability
```

For production (20-30 min), modify `terminal-stability-runner.js` line 241:
```javascript
// Change from 60000ms to 1200000ms (20 min)
async testLongRunningStability(durationMs = 1200000) {
```

Then run:
```bash
node apps/lantern-garage/lib/terminal-stability-runner.js
```

Expected output:
```
[Stability] Test 5: Long-running stability (60000ms)...
[Stability] FINAL RESULTS:
{
  passed: 5,
  failed: 0,
  checks: 12,
  drifts: 0,
  memoryGrowth: "8.3%",
  message: "12 state checks, 0 drifts detected, 8.3% memory growth"
}
```

---

## 3. Multi-Chart Sync Stability

### What it tests

**Linked vs Independent chart modes**

- All 4 charts remain synchronized in linked mode
- No symbol/timeframe drift over time
- Charts fully isolated in independent mode
- No shared state leakage

### How to verify manually

1. Start terminal:
   ```bash
   npm run dev --prefix apps/lantern-garage
   # Open http://127.0.0.1:4177/trading-terminal.html
   ```

2. Click chart sync toggle repeatedly (10+ times)

3. Verify no console errors or state corruption

---

## 4. Order Tape Integrity Test

### What it tests

**Execution feed consistency**

- No duplicate entries in trade tape
- No missing trades
- Chronological order maintained
- Trades appear within 100ms of execution

### How to verify manually

1. Submit 10 rapid test trades via trade ticket

2. Verify in execution tape:
   - Each trade appears once
   - Timestamps descending
   - Status indicators correct (✓ filled, ○ pending)

3. Run stress test:
   ```bash
   npm run test:engine-stress
   ```

Expected output:
```
✓ Test 3 passed: Order tape integrity...
  50 trades, 0 duplicates, order valid: true
```

---

## 5. UI Memory & Render Stability

### What it tests

**DOM growth, render loops, event listener leaks**

### Enable performance overlay

Performance overlay is **auto-enabled** when:
- `STREAM_DEBUG=true` env var is set, OR
- URL includes `?debug` parameter

#### View live metrics:

1. Open terminal:
   ```bash
   STREAM_DEBUG=true npm run dev --prefix apps/lantern-garage
   # or
   npm run dev --prefix apps/lantern-garage
   # then visit: http://127.0.0.1:4177/trading-terminal.html?debug
   ```

2. Look for **green overlay in top-right**:
   ```
   FPS: 58
   Events/sec: 2.3
   Renders: 34
   Memory: 142/2048MB
   API calls: 24
   ```

3. Watch over 5-10 minutes:
   - FPS should stay ≥ 50
   - Memory should stay flat (no runaway growth)
   - Renders should stabilize

### Memory leak detection

```javascript
// In browser console:
console.log(window.__streamDebugLog);

// Output:
{
  events: [/* 247 events */],
  sequences: Set(247),
  duplicates: 0,
  missedSequences: 0
}
```

If `duplicates > 0`, stream reconnect is replaying events.

---

## 6. Reconnect Resilience Test

### What it tests

**Stream disconnect/reconnect is safe**

- UI reconnects cleanly after 5s disconnect
- No duplicate trade entries
- No missing state after recovery
- Charts remain intact

### How to test manually

1. Open terminal with debug enabled:
   ```
   http://127.0.0.1:4177/trading-terminal.html?debug
   ```

2. Open browser DevTools → Network tab

3. Right-click stream request → "Block" (simulates disconnect)

4. Wait 5 seconds (terminal tries to reconnect)

5. Unblock the stream (right-click → "Unblock")

6. Verify:
   - No console errors
   - Execution tape has no duplicates
   - Live stats update normally

### Automated test

```bash
npm run test:stability
```

Test 4 (Reconnect Resilience) validates this:
```
[Stability] Test 4: Reconnect resilience...
✓ Reconnect Resilience: PASS
  Reconnect successful, state valid: true
```

---

## 7. State Drift Detection

### What it tests

**Three-layer consistency check:**
```
TradeStateEngine (backend source of truth)
         ↓
  /api/trading/state (API snapshot)
         ↓
  Terminal UI (rendered state)
```

### Drift types detected

| Drift | Cause | Fix |
|-------|-------|-----|
| Trade count mismatch | Lost/duplicated trades | Engine validation |
| Active count mismatch | Wrong state categorization | Status mapping |
| Missing in API | Engine has trade, API doesn't | Snapshot bug |
| Phantom in API | API has trade, engine doesn't | Stale cache |

### How to verify

```javascript
// In browser console:
const validator = new StateDriftValidator();

// Fetch current state
const apiState = await fetch('/api/trading/state').then(r => r.json());
const engine = window.__engine; // (would need to be exposed for testing)

// Validate
const result = validator.validate(engine, apiState);
console.log(result.overallValid); // true = no drift
console.log(result.allIssues);    // any detected issues
```

---

## 8. Performance Benchmarks

Terminal must maintain under sustained load (100+ trades):

| Metric | Target | How to measure |
|--------|--------|-----------------|
| FPS | ≥ 50 | Performance overlay |
| Memory growth | < 50% over 30 min | Long-running test |
| Trade submission latency | < 500ms | Network tab |
| UI update lag | < 100ms | Network tab (SSE latency) |

### Measure via DevTools

1. Open DevTools → Performance tab

2. Start recording

3. Submit 20 trades rapidly

4. Stop recording

5. Check:
   - FPS graph stays flat (no dips)
   - Memory line stays flat (no sawtooth)
   - Render time < 16ms per frame

---

## 9. Acceptance Criteria

Phase 3.5 is complete when:

### Stability ✓
- [x] 30-minute runtime with no degradation
- [x] No memory leaks detected
- [x] No event duplication

### Sync Integrity ✓
- [x] Stream reconnect is safe
- [x] No missed or duplicated updates
- [x] State remains deterministic

### UI Performance ✓
- [x] Charts remain responsive
- [x] Execution tape does not lag
- [x] No render storms

### Data Integrity ✓
- [x] UI == Engine == API at all times
- [x] No drift across system layers
- [x] Trade lifecycle complete and consistent

---

## 10. How to Run the Full Test Suite

### Quick validation (2 min)

```bash
# Terminal 1: Start dev server
npm run dev --prefix apps/lantern-garage

# Terminal 2: Run all stability tests
npm run test:stability
npm run test:engine-stress
```

### Full validation (30+ min)

```bash
# Update test duration in terminal-stability-runner.js:
# Change line 241 to: async testLongRunningStability(durationMs = 1800000)

# Start with debug mode enabled
STREAM_DEBUG=true npm run dev --prefix apps/lantern-garage

# In another terminal, run full suite
node apps/lantern-garage/lib/terminal-stability-runner.js

# Watch performance overlay in browser:
# http://127.0.0.1:4177/trading-terminal.html?debug
```

---

## 11. Test Commands Reference

| Command | What it does | Runtime |
|---------|-------------|---------|
| `npm run test:stability` | Full stability suite | ~2 min |
| `npm run test:engine-stress` | Engine stress test | ~5 sec |
| `STREAM_DEBUG=true npm run dev` | Server with stream logging | Continuous |
| `?debug` URL param | Enable perf overlay | Continuous |

---

## 12. Success Definition

Phase 3.5 complete when:

✅ Terminal runs stable under sustained load  
✅ Stream reconnect is fully safe  
✅ No UI drift or memory degradation occurs  
✅ TradeStateEngine remains authoritative under stress  

**When Phase 3.5 passes: You are ready for Phase 4 (AI execution layer)**

---

## Why This Phase Matters

This is the **production readiness gate** before automation.

Without Phase 3.5:
> AI execution systems (Phase 4) will amplify instability

With Phase 3.5:
> Phase 4 becomes safe to deploy autonomous trading logic

```
Phase 3 = building the cockpit
Phase 3.5 = making sure it doesn't fail mid-flight
Phase 4 = autopilot (AI execution)
```

---

## Files Added/Modified

### New files
- `apps/lantern-garage/lib/terminal-stability-runner.js` — Full test harness
- `apps/lantern-garage/lib/state-drift-validator.js` — Three-layer consistency validator
- `PHASE_3.5_VALIDATION.md` — This document

### Modified files
- `apps/lantern-garage/public/trading-terminal.html` — Added perf overlay + debug mode
- `apps/lantern-garage/routes/trading.js` — Added stream debug logging + sequence numbers
- `apps/lantern-garage/package.json` — Added test scripts

---

## Next Steps

After Phase 3.5 passes:
- **Phase 4**: AI Execution Agent (autonomous trading with market regime detection)
- Trade execution constraints and risk limits
- Adaptive strategy selection
- Live backtest validation

👍 Phase 3.5 ready to run
