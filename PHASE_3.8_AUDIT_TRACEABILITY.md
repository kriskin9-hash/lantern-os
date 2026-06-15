# Phase 3.8: Audit & Decision Traceability Layer

## Goal

Build a complete causal trace system for **every system action** so that the system can answer:

> "Why did this happen?" with full reproducibility.

This is what separates:
- **Advanced system** (can do complex things)
- **Production-grade system** (can explain every action)

---

## Core Concept: Event Lineage Graph

Every system action becomes a linked node in an immutable timeline DAG.

```
Event Chain for a Single Trade:

AI_DECISION (confidence: 0.82)
   ↓ (parent: eventId)
STABILITY_CHECK (index: 0.91)
   ↓
DRIFT_EVALUATION (status: ok)
   ↓
TRADE_EXECUTION (success: true)
   ↓
STREAM_EVENT (type: trade:filled)
   ↓
UI_RENDER (displayed)

All linked via traceId
```

---

## Event Structure

Every event in the immutable audit log:

```json
{
  "eventId": "e-a1b2c3d4e5f6g7h8",
  "timestamp": 1710000000000,
  "type": "TRADE | DRIFT | RECONCILE | UI_RENDER | AI_DECISION | STABILITY_CHECK",
  "source": "engine | ui | stream | ai | validator | reconciliation",
  "payload": {
    // Event-specific data
  },
  "parentEventId": "e-previous-event-id",
  "traceId": "t-session-wide-id",
  "sessionTraceId": "session-id"
}
```

---

## Components

### 1. **SystemAuditTracer** (`lib/system-audit-tracer.js`)

Immutable event recorder.

**Key guarantees:**
- Append-only (no overwrites, no deletions)
- Linked parent-child relationships
- Chronological ordering
- SHA256-based integrity

**Methods:**
```javascript
// Record any system event
tracer.recordEvent(type, source, payload, parentEventId, customTraceId)

// Record AI decision with context
tracer.recordAIDecision(decision, stabilityIndex, driftReport, confidence, reasoning)

// Record trade execution
tracer.recordTradeExecution(traceId, orderId, engineResponse, success, error)

// Record drift event
tracer.recordDriftEvent(driftType, detected, reconciliationActions, resolved)

// Record UI state
tracer.recordUIState(uiStateSnapshot, linkedTradeId)

// Validate causal integrity
tracer.validateCausalIntegrity(traceId)

// Get summary
tracer.getAuditSummary()
```

**Audit Log:**
```
/data/trading/audit-log.jsonl  (append-only, immutable)
```

### 2. **AuditReplayEngine** (`lib/audit-replay-engine.js`)

Reconstructs full timelines from immutable log.

**Capabilities:**
- Full timeline reconstruction
- Decision path building
- Final state reconstruction
- Decision explanation
- Drift resolution explanation
- Orphan detection

**Methods:**
```javascript
// Full timeline reconstruction
replay.reconstructTimeline(traceId)

// Explain AI decision
replay.explainDecision(traceId)

// Explain drift resolution
replay.explainDriftResolution(traceId)

// Detect orphan events
replay.detectOrphans(traceId)

// Get system audit summary
replay.getSystemAuditSummary()
```

---

## API Endpoints

### 1. **GET /api/trading/audit/summary**

System-wide audit overview.

```json
{
  "totalTraces": 127,
  "systemTraceId": "session-id",
  "uptime": 3600000,
  "totalEvents": 1547,
  "breakdown": {
    "AI_DECISION": 127,
    "STABILITY_CHECK": 127,
    "DRIFT": 15,
    "TRADE_EXECUTION": 127,
    "UI_RENDER": 254,
    "STREAM_EVENT": 897
  },
  "recentTraces": [...]
}
```

### 2. **GET /api/trading/audit/trace/:traceId**

Full timeline reconstruction for a specific trace.

```json
{
  "traceId": "t-123",
  "found": true,
  "startTime": 1710000000,
  "endTime": 1710000045,
  "duration": 45000,
  "eventCount": 12,
  "integrity": {
    "valid": true,
    "issues": [],
    "eventCount": 12,
    "eventTypes": ["AI_DECISION", "STABILITY_CHECK", ...]
  },
  "decisionPath": [
    {
      "type": "AI_DECISION",
      "timestamp": 1710000000,
      "source": "ai",
      "summary": "AI decided: BUY AAPL (confidence: 0.82)"
    },
    ...
  ],
  "finalState": {
    "trades": {...},
    "lastAIDecision": {...},
    "lastStabilityIndex": {...},
    "driftEvents": [...],
    "uiState": {...}
  },
  "events": [...]
}
```

### 3. **GET /api/trading/audit/explain/:traceId**

Explain an AI decision with full context.

```json
{
  "traceId": "t-123",
  "decision": {
    "action": "BUY",
    "symbol": "AAPL",
    "quantity": 10
  },
  "confidence": 0.82,
  "reasoning": [
    "trend alignment",
    "low volatility",
    "positive momentum"
  ],
  "systemContext": {
    "stabilityIndex": {
      "index": 0.91,
      "status": "healthy",
      "timestamp": 1710000000
    },
    "driftHistory": [
      {
        "type": "ui_lag",
        "severity": "low",
        "resolved": true,
        "timestamp": 1710000015
      }
    ]
  },
  "result": {
    "executed": {
      "orderId": "order-123",
      "success": true,
      "timestamp": 1710000025
    },
    "uiState": {
      "tradeCount": 45,
      "displayedTrades": [...]
    }
  },
  "timeline": [...]
}
```

### 4. **GET /api/trading/audit/drift/:traceId**

Explain drift detection and resolution.

```json
{
  "traceId": "t-456",
  "driftEvents": [
    {
      "type": "ui_lag",
      "severity": "warning",
      "details": {...},
      "reconciliationActions": [
        {
          "type": "ui_resync",
          "action": "refresh_ui_state_from_engine_snapshot"
        }
      ],
      "resolved": true,
      "timestamp": 1710000015
    }
  ],
  "timeline": [...]
}
```

### 5. **GET /api/trading/audit/orphans/:traceId**

Detect events without proper causal chain.

```json
{
  "traceId": "t-789",
  "hasOrphans": false,
  "issues": [],
  "eventCount": 12
}
```

---

## Decision Capture Structure

Every AI decision recorded with:

```json
{
  "type": "AI_DECISION",
  "payload": {
    "decision": {
      "action": "BUY",
      "symbol": "AAPL",
      "quantity": 10
    },
    "confidence": 0.82,
    "reasoning": [
      "trend alignment",
      "low volatility",
      "positive momentum"
    ],
    "systemState": {
      "stabilityIndex": 0.91,
      "driftReport": {
        "status": "ok",
        "drifts": []
      }
    }
  }
}
```

---

## Causal Chain Guarantees

Phase 3.8 ensures:

✅ **Every trade has a traceId**
- Every trade execution is linked to a parent decision

✅ **Every AI decision maps to engine action**
- AI decision → stability check → drift eval → trade exec

✅ **No engine action without trace**
- Every trade in engine appears in audit log

✅ **UI updates trace back to engine event**
- Every UI render is linked to a trade or drift event

✅ **Drift events are linkable to resolution**
- Drift detection → reconciliation actions → resolution

---

## Failure Detection

Phase 3.8 detects:

| Issue | Detection |
|-------|-----------|
| Orphan trades | Trade execution without AI decision |
| Missing decision source | Trade without parent AI_DECISION event |
| UI phantom updates | UI render without trade |
| Unresolved drift | Drift detected but never reconciled |
| Circular dependencies | Event A → B → A |

---

## Forensic Debugging Example

**Scenario:** "Why did we lose $50k on that trade?"

**Query:**
```bash
curl http://127.0.0.1:4177/api/trading/audit/explain/t-loss-12345 | jq
```

**Response shows:**
1. **AI decision**: confidence, reasoning, system state
2. **Stability check**: index, why it was OK to execute
3. **Drift evaluation**: any issues, how they were resolved
4. **Trade execution**: actual result, engine response
5. **UI state**: what was displayed, when
6. **Full timeline**: every step with timestamps

**Can now answer:**
- Why did AI decide to buy?
- What was system stability at that time?
- Did any drift occur? Was it resolved?
- What did UI show?
- When exactly did execution occur?

---

## System Audit Summary Example

```bash
curl http://127.0.0.1:4177/api/trading/audit/summary | jq
```

Shows:
- Total trades executed
- Total AI decisions made
- Drift events detected and resolved
- Average decision confidence
- System uptime
- Audit log health

---

## Compliance & Audit Trail

Phase 3.8 provides:

✅ **Non-repudiation**: Every action is immutable
✅ **Reproducibility**: Full timeline can be reconstructed
✅ **Explainability**: Every decision has reasoning
✅ **Forensic capability**: Find any event in O(1) with index
✅ **Compliance ready**: Immutable audit trail for regulators

---

## Acceptance Criteria

Phase 3.8 is complete when:

### ✅ Every system event is traceable
- All events recorded in audit log
- All events properly linked via traceId and parentEventId

### ✅ Every trade can be replayed end-to-end
- AI decision → stability check → drift eval → execution → UI update
- All steps appear in timeline

### ✅ Every AI decision is explainable
- Decision reasoning captured
- System state at decision time recorded
- Confidence score stored

### ✅ No orphan state exists in logs
- All trades have parent AI decision
- All UI updates have parent trade
- All drifts have reconciliation resolution

### ✅ Full system replay is deterministic
- Reconstructing timeline from audit log produces identical results
- Causal chains are valid
- No circular dependencies

---

## Files Added/Modified

### New files
- `apps/lantern-garage/lib/system-audit-tracer.js`
- `apps/lantern-garage/lib/audit-replay-engine.js`
- `PHASE_3.8_AUDIT_TRACEABILITY.md`

### Modified files
- `apps/lantern-garage/server.js` — Wired audit tracer and replay engine
- `apps/lantern-garage/routes/trading.js` — Added 5 audit endpoints

---

## Complete Stack (Phase 3.1→3.8)

```
Phase 3.6: Detects issues (correctness validation)
Phase 3.7: Smooths over noise (probabilistic stability)
Phase 3.8: Explains every action (forensic traceability) ← YOU ARE HERE

= Full Observability + Control Stack
```

---

## Why This Matters for Phase 4

**Without Phase 3.8:**
> AI made a trade that failed. What happened?  
> (No way to know — black box)

**With Phase 3.8:**
> AI made a trade that failed. Get the trace:  
> (Full causal chain, decision reasoning, system state)

This enables:

✅ **AI Explainability**
- Every trade can be explained by human

✅ **Regulatory Compliance**
- Immutable audit trail
- Decision rationale preserved
- Can prove why each trade happened

✅ **Debugging & Learning**
- Find bugs by replaying traces
- Improve decision logic based on past decisions
- Audit AI behavior over time

✅ **Safety Gates**
- Block trades if audit chain incomplete
- Verify decision consistency
- Force AI to attach traceId

---

## Success Definition

Phase 3.8 proves:

> You can always reconstruct exactly why any action happened.  
> Not just what happened, but the causal chain and reasoning.

**This is production-grade observability.**

---

## Next: Phase 4 (Safe AI Execution)

With Phase 3.8's traceability:

```javascript
// Phase 4 AI execution with traceability enforced:

async function executeAITrade(ai, engine, tracer) {
  // 1. AI makes decision
  const traceId = tracer.recordAIDecision(
    decision,
    stabilityIndex,
    driftReport,
    confidence,
    reasoning
  );

  // 2. Check system health
  if (stabilityIndex < 0.8) {
    tracer.recordEvent("TRADE_BLOCKED", "ai", {
      reason: "Low stability",
      index: stabilityIndex
    }, null, traceId);
    return false;
  }

  // 3. Execute trade
  const result = await engine.submitOrder({...decision, traceId});

  // 4. Record result
  tracer.recordTradeExecution(traceId, result.orderId, result, result.success);

  // 5. Full timeline available via /api/trading/audit/explain/:traceId
  return result;
}
```

---

## The Final Achievement

After Phase 3.8, your system has:

✅ **Detection** (Phase 3.6) — knows when things are wrong  
✅ **Recovery** (Phase 3.7) — fixes problems automatically  
✅ **Explainability** (Phase 3.8) — explains why things happened  

This is what makes a system **production-grade**.

Ready for Phase 4? 👍
