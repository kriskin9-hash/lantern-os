# Phase 3.7: Drift Tolerance & Reconciliation Layer

## Goal

Replace strict equality-based validation (Phase 3.6) with a **real-world tolerance model** that distinguishes:

> True system failure ≠ Normal distributed-system latency behavior

---

## The Problem with Phase 3.6

Phase 3.6 assumes perfect equality at all times:
- Engine == UI == Stream
- Any deviation = drift alert
- Binary pass/fail validation

But real distributed systems have:
- **Async delays** (event loop scheduling)
- **Batching delays** (network queueing)
- **UI render lag** (browser frame timing)
- **Event loop jitter** (process switching)
- **Network scheduling variance** (TCP retransmit windows)

Result of strict validation:
- ❌ False drift alerts on normal operations
- ❌ Noisy critical warnings during latency spikes
- ❌ Unstable health status that doesn't reflect reality

---

## Phase 3.7 Solution: Statistical Validation

Instead of binary validation, measure **deviation from expected behavior**:

```
DRIFT = MEASURED DEVIATION FROM EXPECTED SYSTEM BEHAVIOR
NOT automatic failure
```

### Replace fixed thresholds with adaptive tolerance windows

Before (Phase 3.6):
```
UI lag > 2000ms → CRITICAL ALERT
```

After (Phase 3.7):
```
UI lag > (mean + 2×stdDev) → Consider reconciliation
Reconciliation successful → Still "OK"
Persistent failure after reconciliation → CRITICAL
```

---

## Core Components

### 1. **DriftBaselineTracker** (`lib/drift-baseline-tracker.js`)

Learns expected system behavior through rolling averages.

**What it tracks:**
- UI lag (moving average + stdDev)
- Stream delay (moving average + stdDev)
- Update frequency
- Event loss rate

**Output:**
```json
{
  "uiLag": {
    "avg": 420,
    "stdDev": 120,
    "tolerance": 700,
    "sampleCount": 50
  },
  "streamDelay": {
    "avg": 90,
    "stdDev": 30,
    "tolerance": 180,
    "sampleCount": 50
  }
}
```

**Dynamic tolerance formula:**
```
tolerance = avg + (2 × stdDev)
```

This covers ~95% of normal variance.

### 2. **DriftReconciliationEngine** (`lib/drift-reconciliation-engine.js`)

Automatically reconciles system state when drift is detected.

**Reconciliation types:**

| Type | Action | Does NOT |
|------|--------|----------|
| UI lag | Re-sync missing UI updates from engine | Modify engine |
| Stream gap | Re-emit last engine event if missing | Modify engine |
| Config mismatch | Validate snapshot vs engine | Modify engine |
| Event loss | Verify stream health | Modify engine |

**Important rule:**
> Reconciliation does NOT modify engine state.  
> Engine remains source of truth.

**Example workflow:**
1. Detect UI lag > tolerance
2. Check what UI is missing from engine
3. If missing trades exist → request UI refresh from engine snapshot
4. If no missing trades → transient lag (don't alert)
5. Return reconciliation result (success, degraded, or warning)

### 3. **SystemStabilityIndex** (`lib/system-stability-index.js`)

Holistic health score combining multiple factors.

**Scoring (0.0 to 1.0):**
- 0.9–1.0: Excellent
- 0.8–0.9: Healthy ✅
- 0.7–0.8: Stable
- 0.5–0.7: Degraded ⚠️
- 0.3–0.5: Unstable 🔴
- < 0.3: Critical 🛑

**Computed from (weighted):**
- Drift frequency (25%)
- Reconciliation success rate (25%)
- Lag variance (20%)
- Event loss rate (15%)
- Critical failure count (15%)

**Example:**
```json
{
  "stabilityIndex": 0.92,
  "status": "healthy",
  "message": "System is healthy",
  "confidence": "high",
  "trend": "stable"
}
```

---

## New Tolerance Windows

Dynamic, not fixed:

| Boundary | Baseline | Spike Tolerance |
|----------|----------|-----------------|
| Engine → Stream | 50–150ms | 500ms max |
| Stream → UI | 200–800ms | 2500ms max |
| Config → Engine | Next cycle | Next cycle |

Windows are learned from system behavior, not hardcoded.

---

## Updated `/api/trading/consistency-report`

Now returns pragmatic health metrics instead of strict validation:

```json
{
  "phase": "3.7",
  "timestamp": 1234567890,
  "systemHealth": {
    "stabilityIndex": "0.92",
    "status": "healthy",
    "message": "System is healthy",
    "canExecuteTrades": {
      "canExecute": true,
      "index": "0.92",
      "threshold": "0.80",
      "gap": "0.12"
    },
    "trend": "stable",
    "confidence": "high"
  },
  "baseline": {
    "uiLag": {
      "avg": 420,
      "stdDev": 120,
      "tolerance": 700
    },
    "streamDelay": {
      "avg": 90,
      "stdDev": 30,
      "tolerance": 180
    }
  },
  "reconciliation": {
    "successRate": "98.5",
    "totalCycles": 127,
    "lastReport": { /* ... */ }
  },
  "aiExecutionGuidance": {
    "safeToExecute": true,
    "requiredStabilityIndex": 0.8,
    "currentStabilityIndex": 0.92,
    "recommendation": "System is healthy enough for autonomous execution"
  }
}
```

---

## Drift Classification (3-Tier)

Instead of binary OK/FAIL:

| Level | Meaning | Action |
|-------|---------|--------|
| **OK** | Within normal variance | Continue normally |
| **WARNING** | Outside expected range but self-correcting | Monitor, prepare for degradation |
| **CRITICAL** | Structural inconsistency | Halt autonomy, investigate |

---

## Reconciliation Success Rates

Phase 3.7 measures recovery, not just detection.

**Example scenario:**
1. Detect UI lag spike to 2500ms
2. Attempt reconciliation → successful
3. Result: "WARNING" (temporary) instead of "CRITICAL" (persistent)

Status only becomes critical if reconciliation fails repeatedly.

---

## Alerting Rules (Rebalanced)

### 🔴 CRITICAL (Stop trading immediately)
- Sustained divergence beyond tolerance window
- Reconciliation fails repeatedly (> 3 cycles)
- Event loss confirmed (> 5%)

### 🟡 WARNING (Continue with caution)
- Temporary lag spikes (auto-recovering)
- UI desync but self-recovers within 2s
- Stream delay bursts (< 500ms)

### 🟢 OK (Proceed normally)
- All measurements within statistical variance
- Self-correcting drift detected
- Reconciliation successful

---

## Failure Mode Protection

Phase 3.7 prevents:
- ❌ False drift alarms during network volatility
- ❌ UI jitter misclassified as system failure
- ❌ Stream burst false positives
- ❌ Config reload noise triggering critical alerts

---

## How to Use

### Check system health
```bash
curl http://127.0.0.1:4177/api/trading/consistency-report | jq
```

### Enable debug logging
```bash
DRIFT_RECONCILIATION_DEBUG=true npm run dev --prefix apps/lantern-garage
```

### AI execution check
```javascript
const report = await fetch('/api/trading/consistency-report').then(r => r.json());
const { safeToExecute } = report.aiExecutionGuidance;

if (safeToExecute) {
  // Safe to execute trades
} else {
  // Wait for stability to recover
}
```

---

## Why This Matters

**Before Phase 3.7 (Phase 3.6 strict):**
```
Event: UI lag spike to 2500ms
→ Alert: CRITICAL DRIFT DETECTED
→ AI execution halts
→ false alarm — lag recovered in 1 second
```

**After Phase 3.7 (tolerance-based):**
```
Event: UI lag spike to 2500ms
→ Baseline says: tolerance = 2000ms (avg 400 + 2×stdDev)
→ Detect: Slightly above tolerance
→ Reconcile: Re-sync UI state → successful
→ Result: Status = "WARNING" (temporary)
→ AI continues safely with reconciliation active
```

The difference:
- Phase 3.6: Noisy, frequently halts trading on transients
- Phase 3.7: Pragmatic, tolerates normal variance, self-recovers

---

## Acceptance Criteria

Phase 3.7 is complete when:

### ✅ Drift is measured statistically, not assumed
- Baseline learning works
- Tolerance windows adapt
- No hardcoded thresholds

### ✅ UI lag treated as distribution, not fixed value
- Moving averages computed
- Standard deviation tracked
- Tolerance = mean + 2×stdDev

### ✅ System self-recovers without false alarms
- Reconciliation succeeds > 95% of time
- Stability index remains > 0.8 under normal load
- No critical alerts on transient spikes

### ✅ No persistent unresolvable drift exists
- Events after reconciliation appear in UI
- Stream is lossless (< 1% loss)
- Engine state remains consistent

---

## Safety Guarantees for Phase 4 AI

Phase 3.7 enables safe AI execution because:

1. **Stability index is a hard safety gate**
   - AI will not execute unless index ≥ 0.8
   - Forces recovery before autonomy resumes

2. **Reconciliation is automatic**
   - System self-corrects without human intervention
   - Transient drifts don't stop trading

3. **No false alarms**
   - Network jitter doesn't trigger halts
   - UI lag spikes don't panic the system

4. **Measurable confidence**
   - Each trade execution can check stability
   - AI can reason about system health

---

## Files Added/Modified

### New files
- `apps/lantern-garage/lib/drift-baseline-tracker.js`
- `apps/lantern-garage/lib/drift-reconciliation-engine.js`
- `apps/lantern-garage/lib/system-stability-index.js`
- `PHASE_3.7_DRIFT_TOLERANCE.md` — This documentation

### Modified files
- `apps/lantern-garage/server.js` — Wired Phase 3.7 components
- `apps/lantern-garage/routes/trading.js` — Updated consistency report endpoint

---

## Architecture Evolution

```
Phase 3.6: "Is system exactly equal?"
           → Binary: Yes or No
           → Result: Noisy alerts

Phase 3.7: "How far is system from expected behavior?"
           → Statistical: Within tolerance?
           → Result: Pragmatic health score
           ← YOU ARE HERE
```

---

## Next: Phase 4 Safety

With Phase 3.7, Phase 4 AI execution can:

✅ **Check stability before executing**
```javascript
if (stabilityIndex >= 0.8) {
  // Safe to execute trade
  const trade = await ai.decideTrade();
  await execute(trade);
} else {
  // Wait for stability recovery
  console.log("Waiting for system stability...");
}
```

✅ **Benefit from automatic reconciliation**
- Temporary drifts don't stop AI
- System heals itself
- AI continues operating

✅ **Make confident decisions**
- Knows exact system health
- Can reason about risk
- Never acts on stale state

---

## Success Definition

Phase 3.7 proves the system can:

> Distinguish between real failures and normal variance  
> AND self-reconcile without external intervention  
> AND provide a single health metric for AI to trust

**When Phase 3.7 passes cleanly:**
> You are ready for Phase 4 AI execution with hard safety gates.

The stability index becomes the gatekeeper.
