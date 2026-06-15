# Phase 3.6: Cross-System Consistency Validator

## Goal

Ensure **perfect synchronization** across all system layers:

- **TradeStateEngine** (source of truth — backend)
- **SSE Stream** (real-time propagation — transport)
- **UI Terminal** (renderer — display)
- **Config Pipeline** (data ingestion — input)

This phase guarantees:

> There is no drift, desync, or stale state across any system boundary.

**Key insight:** The system can only be trusted if it can prove itself correct at runtime.

---

## System Truth Model

```
TradeStateEngine = GLOBAL AUTHORITY
↓
Everything else MUST match it
```

All other layers are derived from engine state:

| Layer | Role |
|-------|------|
| SSE Stream | Transport mechanism |
| UI Terminal | Render layer (pure renderer) |
| Config | Input pipeline |

---

## What Phase 3.6 Validates

### 1. **Engine State Consistency**
- All trades in valid states
- No quantity overflows (filled > total)
- Order ID mappings are valid (no orphans)
- Event sequence is monotonic

### 2. **SSE Stream Integrity**
- Event ordering maintained
- No duplicate sequences
- Lossless event capture
- Correct event types

### 3. **Engine ↔ UI Sync**
- Trade count matches (within tolerance)
- No phantom trades in UI
- UI state reflects engine state within 2s window
- PnL consistency

### 4. **Engine ↔ Stream Replay**
- All engine trades appear in stream
- Stream events could reconstruct engine state
- No missing event updates
- Chronological ordering preserved

### 5. **Config ↔ Engine Alignment**
- Config tickers are used in engine
- No phantom tickers in engine
- Watchlist synchronization

---

## Components

### 1. System Consistency Validator
**File:** `lib/system-consistency-validator.js`

Core class with methods:

```javascript
// Validation methods
validator.validateEngineState(engine)      // Internal consistency
validator.compareEngineToUI(engine, uiState)   // UI sync check
validator.compareEngineToStream(engine)    // Stream completeness
validator.validateStreamReplay(engine)     // Event ordering

// State hashing
validator.hashEngineState(engine)          // Deterministic engine hash
validator.hashUIState(uiState)             // Deterministic UI hash
validator.hashStreamEvents(events)         // Deterministic stream hash

// Full validation
validator.validate(engine, uiState, config)    // Run all checks
validator.getConsistencyReport()           // Historical analysis

// Event recording
validator.recordStreamEvent(event)         // Track SSE events
```

### 2. API Endpoint
**GET /api/trading/consistency-report**

Returns cross-system consistency status:

```json
{
  "status": "ok|warning|critical",
  "passRate": "95.2",
  "totalValidations": 127,
  "lastValidation": {
    "timestamp": 1234567890,
    "engine": {
      "valid": true,
      "issues": [],
      "tradeCount": 45
    },
    "stream": {
      "valid": true,
      "issues": [],
      "replayCount": 127
    },
    "engineToUI": {
      "hasDrift": false,
      "drifts": []
    },
    "engineToStream": {
      "hasDrift": false,
      "drifts": []
    },
    "driftSummary": {
      "status": "ok",
      "criticalIssues": 0,
      "warningIssues": 0,
      "totalIssues": 0
    },
    "hashes": {
      "engine": "abc123...",
      "ui": "def456...",
      "stream": "ghi789...",
      "config": "jkl012..."
    }
  },
  "summary": {
    "status": "ok",
    "passRate": "95.2",
    "criticalDriftCount": 0,
    "recentDrifts": []
  }
}
```

### 3. Monitoring Mode
**Enable with:** `CONSISTENCY_MONITOR=true`

- Runs validation every 5 seconds
- Logs warnings to console if drifts detected
- Tracks validation history
- Reports on `/api/trading/consistency-report`

---

## Drift Detection Rules

### Rule 1: Engine is Always Correct
If a mismatch occurs:
> UI / stream is wrong, NOT engine

### Rule 2: UI Must Reflect Engine Within Tolerance
- Allowed delay: max 1–2 seconds
- Beyond that: drift alert issued
- Detects stale UI state

### Rule 3: Stream Must Be Lossless
Every engine event MUST appear in SSE stream:
- No missing trade updates
- No duplicate events
- No reordered states

### Rule 4: Config Propagation Consistency
- Config tickers → appear in engine next cycle
- No extra tickers in engine
- Watchlist alignment verified

---

## How to Run

### Quick validation
```bash
# Start server
npm run dev --prefix apps/lantern-garage

# In another terminal, check consistency
curl http://127.0.0.1:4177/api/trading/consistency-report | jq
```

### Continuous monitoring
```bash
# Start with monitoring enabled
CONSISTENCY_MONITOR=true npm run dev --prefix apps/lantern-garage

# Watch console for drift warnings:
# [System Consistency] Drift detected: { status: 'warning', ... }
```

### Browser integration
```javascript
// In browser console:
const report = await fetch('/api/trading/consistency-report').then(r => r.json());
console.log(report.status); // 'ok' | 'warning' | 'critical'
console.log(report.summary);
```

---

## Latency Tolerance Windows

Safe windows for each layer transition:

| Boundary | Max Allowed Lag |
|----------|-----------------|
| Engine → Stream | 100ms |
| Stream → UI | 2 seconds |
| Config → Engine | Next cycle |

Beyond these windows → drift alert issued.

---

## Critical Failure Modes Detected

### 🔴 Critical (Must stop trading)
- **Missing trade events**: SSE stream incomplete
- **UI-engine mismatch**: UI shows trade not in engine
- **Phantom trades in UI**: UI displays phantom execution
- **Duplicated display**: Trade shown twice in tape
- **Quantity overflow**: Filled > total quantity

### 🟡 Warning (Operational alert)
- **Delayed stream updates**: SSE > 2s behind engine
- **Temporary UI lag**: UI not yet updated from stream
- **Config propagation delay**: Tickers not synced next cycle
- **Orphaned order mappings**: OrderID without trade

---

## State Hashing System

Generates deterministic SHA256 hashes for comparison:

```javascript
// Engine state is hashed as:
{
  totalTrades: count,
  tradeIds: sorted_array,
  openPositions: count,
  eventSequence: number,
  recentCount: number
}

// UI state is hashed as:
{
  tapeEntries: count,
  activeTrades: count,
  displayedTradeIds: sorted_array,
  pnl: amount,
  timestamp: ms
}

// Stream is hashed as:
{
  count: events.length,
  types: sorted_event_types,
  lastSequence: number,
  tradeIds: sorted_unique_trades
}
```

Comparison rule:
```
engineHash MUST == uiHash (within tolerance window)
engineHash MUST == stream_replay_hash
```

---

## Validation Workflow

Each validation cycle:

1. **Capture snapshots** of all three layers
2. **Generate hashes** for each layer
3. **Run consistency checks**:
   - Internal engine validation
   - Stream ordering validation
   - Engine-to-UI comparison
   - Engine-to-stream comparison
4. **Detect drifts** and classify severity
5. **Record history** for analysis
6. **Alert if critical** issues found

Result: `validation` object with detailed findings.

---

## Acceptance Criteria

Phase 3.6 is complete when system can prove:

### ✅ No drift between engine and UI
- Trade counts match (within tolerance)
- No phantom trades
- No missing trades

### ✅ No missing SSE events
- Stream is lossless
- Event ordering preserved
- Replay reconstructs exact state

### ✅ No config-to-engine mismatches
- Config tickers present in engine
- No extra tickers in engine
- Watchlist synchronized

### ✅ All hashes align
- Engine hash stable over time
- UI hash converges to engine hash
- Stream hash consistent

### ✅ Any divergence is detectable
- Drift detection runs continuously
- Severity classification accurate
- Historical audit trail maintained

---

## What This Achieves

You now have a system that:

✅ **Validates itself at runtime**  
✅ **Detects any desynchronization instantly**  
✅ **Proves correctness across all layers**  
✅ **Maintains audit trail of all drifts**  
✅ **Blocks invalid state transitions**  

This is the **production reality check** that separates:
- Working demo (no validation)
- Production system (provably correct)

---

## Files Added/Modified

### New files
- `apps/lantern-garage/lib/system-consistency-validator.js` — Core validator
- `PHASE_3.6_CONSISTENCY.md` — This documentation

### Modified files
- `apps/lantern-garage/routes/trading.js` — Added `/api/trading/consistency-report` endpoint
- `apps/lantern-garage/server.js` — Wired validator, enabled monitoring mode

---

## Next: Why This Matters for Phase 4

Phase 3.6 enables safe AI execution because:

**Without Phase 3.6:**
> AI could make decisions based on wrong/stale state

**With Phase 3.6:**
> System proves state is correct before AI acts

This means Phase 4 (AI Execution) can:
- Check consistency before every decision
- Refuse to trade if drift detected
- Maintain invariants across agent boundaries
- Prove trades are based on truth

```
Phase 3 = building reliable cockpit
Phase 3.5 = proving it's stable under load
Phase 3.6 = proving it can validate itself ← YOU ARE HERE
Phase 4 = safe AI automation (proven correct by 3.6)
```

---

## 🚀 Success Definition

Phase 3.6 proves the system is **self-validating**.

When this passes cleanly:
> You are ready for Phase 4 AI execution with safety guarantees.

The AI will operate within a system that **provably knows when something is wrong**.

That's the final prerequisite for autonomous trading.
