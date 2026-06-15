# Phase 4B: Independent AI Trader Integration (Production Wiring)

## Goal

**Integrate existing profitable AI trader into Lantern OS as a black-box alpha engine.**

This is NOT about rewriting the trader. It's about **connecting, governing, and observing** an already-profitable system.

```
Before:
  Independent AI Trader (agents.py + main.py)
  ↓
  [standalone, profitable, unobserved]

After:
  Independent AI Trader (agents.py + main.py)
  ↓
  [wrapped, gated, logged, observable, integrated]
  ↓
  Lantern OS Trading System
```

---

## Core Principle

> **We treat the AI Trader as a black-box alpha engine.**

### DO NOT modify:
- Strategy logic
- Decision rules
- Model training
- Signal generation

### DO:
- Wrap the execution
- Observe all decisions
- Apply safety gates
- Log to audit trail
- Route through engine
- Display on dashboard

---

## Components

### 1. **IndependentAITraderService** (`services/independent-ai-trader-service.py`)

Python service that wraps the existing trader.

**Responsibilities:**
- Start main.py process
- Intercept decisions (BUY, SELL, NO_TRADE, EXIT)
- Apply safety gate (check stability index)
- Route to Lantern OS via HTTP
- Log all decisions
- Stream events to dashboard

**Entry point:**
```bash
python services/independent-ai-trader-service.py --api-base http://127.0.0.1:4177
```

**Process flow:**
```
agents.py (strategy logic)
   ↓
main.py (execution loop) [UNCHANGED]
   ↓
Service Wrapper (observation point)
   ↓
Safety Gate (stability check)
   ↓
HTTP Bridge → Lantern OS
   ↓
Trade State Engine (paper trading)
   ↓
Audit Trail + Dashboard
```

### 2. **API Bridge Endpoints** (routes/trading.js)

Two new endpoints:

#### `POST /api/trading/independent-ai/order`

Route AI trader decision to Trade State Engine.

**Request:**
```json
{
  "ticker": "NVDA",
  "side": "BUY",
  "quantity": 10,
  "confidence": 0.81,
  "strategy": "alpha-model-v3",
  "decision_id": "d-123"
}
```

**Response:**
```json
{
  "success": true,
  "tradeId": "t-xyz",
  "traceId": "trace-xyz",
  "status": "pending",
  "message": "Paper trade routed: NVDA BUY"
}
```

#### `GET /api/trading/independent-ai/status`

Get integration status.

**Response:**
```json
{
  "service": "independent-ai-trader-integration",
  "phase": "4B",
  "mode": "paper-trading-only",
  "integration": {
    "enabled": true,
    "traceability": true,
    "safetyGateActive": true,
    "realExecutionBlocked": true
  },
  "metrics": {
    "totalTrades": 127,
    "externalTrades": 45,
    "externalWinRate": "N/A (paper)"
  },
  "requirements": {
    "stabilityIndexMinimum": 0.8,
    "executionMode": "PAPER ONLY",
    "auditTrailRequired": true
  }
}
```

---

## Safety Gate System

### Hard Gate: Stability Index Check

Before ANY trade executes:

```python
# Get current stability
stability = fetch('/api/trading/consistency-report')

# Block if unstable
if stability.index < 0.80:
    return {"executed": False, "reason": "safety_gate_blocked"}
```

### Fail-Safe Behavior

If ANY of these occur:
- API unreachable
- Invalid JSON response
- Missing confidence score
- Stability check exception

**→ FORCE NO_TRADE**

### Logging Blocked Decisions

All blocked decisions logged:
```json
{
  "timestamp": "2026-06-14T...",
  "ticker": "NVDA",
  "action": "BUY",
  "confidence": 0.81,
  "reason": "safety_gate_blocked",
  "stability_index": 0.75
}
```

---

## Execution Flow

### 1. AI Trader Generates Decision

```python
# agents.py + main.py (UNCHANGED)
action = agent.decide(market_state)  # BUY, SELL, NO_TRADE
confidence = agent.confidence
```

### 2. Service Intercepts

```python
service.process_decision(
    ticker="NVDA",
    action="BUY",
    confidence=0.81,
    strategy="alpha-model-v3"
)
```

### 3. Safety Gate Check

```python
stability = check_safety_gate()
if not stability.allowed:
    return {"executed": False, "reason": "blocked"}
```

### 4. Route to Lantern OS

```python
POST /api/trading/independent-ai/order
{
  "ticker": "NVDA",
  "side": "BUY",
  "quantity": 10,
  "confidence": 0.81
}
```

### 5. Trade State Engine Processing

```
Trade created → paper trading mode
Status: PENDING
Engine state updated
Event emitted
```

### 6. Audit Trail Recording

```json
{
  "traceId": "trace-xyz",
  "source": "independent-ai-trader",
  "action": "BUY",
  "ticker": "NVDA",
  "confidence": 0.81,
  "executed": true
}
```

### 7. Dashboard Display

```
NVDA
BUY — 0.81 confidence
strategy: alpha-model-v3
status: EXECUTED (paper)
traceId: trace-xyz
```

---

## Data Flow

### Decision Logging

```
/data/trading/independent-ai-decisions.jsonl
```

Every decision recorded:
```json
{
  "timestamp": "2026-06-14T10:30:00Z",
  "decisionId": "d-xyz",
  "ticker": "NVDA",
  "action": "BUY",
  "confidence": 0.81,
  "strategy": "alpha-model-v3",
  "safetyGate": {
    "allowed": true,
    "stability_index": 0.92
  }
}
```

### Trade Execution Log

```
/data/trading/independent-ai-trades.jsonl
```

Trades that executed:
```json
{
  "timestamp": "2026-06-14T10:30:02Z",
  "traceId": "trace-xyz",
  "source": "independent-ai-trader",
  "ticker": "NVDA",
  "action": "BUY",
  "confidence": 0.81,
  "paper": true,
  "executed": true
}
```

---

## Safety Constraints

### HARD CONSTRAINTS (Non-negotiable)

✅ **Paper Trading Only**
- NO real execution path
- ALL trades routed as "mode: paper"
- Real execution flag explicitly DISABLED

✅ **Stability Gate Required**
- Minimum stability index: 0.80
- Blocks at stability < 0.80
- Cannot be bypassed

✅ **Audit Traceability**
- Every decision logged
- Every execution traced
- Full causal chain recorded

✅ **No Strategy Modification**
- agents.py untouched
- Decision logic preserved
- Only wrapper observes

### CANNOT EXECUTE

```
Real orders
Live trading
Leverage
Margin trading
Position size > limits
```

---

## Integration Checklist

✅ **Trader Independence**
- Runs in separate process
- Logic unchanged
- Strategy preserved

✅ **Lantern OS Reception**
- Decisions received via HTTP
- Routed to Trade State Engine
- Paper trading mode

✅ **Safety Gate**
- Stability check working
- Blocks unstable states
- Fail-safe behavior

✅ **Audit Trail**
- Decisions logged
- Traces generated
- Full causal chain

✅ **Dashboard Integration**
- Decisions visible
- Execution status shown
- Confidence displayed

✅ **No Bypass Possible**
- Real execution impossible
- Safety gate required
- Cannot be overridden

---

## Monitoring

### Health Check

```bash
curl http://127.0.0.1:4177/api/trading/independent-ai/status
```

Returns:
- Integration enabled
- Traceability active
- Safety gate operational
- Paper-only execution confirmed

### Metrics

- Total external trades
- Decision success rate (paper)
- Safety gate blocks (when stability drops)
- Audit trail health

### Alerts

If ANY of these occur:
- Service unreachable
- Stability gate not responding
- Trade routing fails
- Audit log corrupted

**→ Suspend AI trader execution**

---

## Operational Model

### Normal State

```
Stability >= 0.8
    ↓
AI trader generates decision
    ↓
Safety gate: ALLOW
    ↓
Paper trade routed to engine
    ↓
Logged to audit trail
    ↓
Displayed on dashboard
```

### Degraded State

```
Stability < 0.8
    ↓
AI trader generates decision
    ↓
Safety gate: BLOCK
    ↓
Decision logged (blocked)
    ↓
NO trade executed
    ↓
Dashboard shows "BLOCKED"
```

### Recovery

```
Wait for stability to recover (auto-reconciliation)
    ↓
When stability >= 0.8 again
    ↓
AI trader resumes normal operation
```

---

## Files Added/Modified

### New files
- `services/independent-ai-trader-service.py` — Service wrapper
- `PHASE_4B_AI_TRADER_INTEGRATION.md` — This documentation

### Modified files
- `routes/trading.js` — Added 2 AI trader integration endpoints

---

## Success Definition

Phase 4B is complete when:

✅ **Independent AI trader runs**
- In separate process
- Strategy logic intact
- Decisions generated

✅ **Lantern OS receives decisions**
- Via HTTP bridge
- Routed to engine
- Paper trading only

✅ **Safety gate works**
- Checks stability
- Blocks when unstable
- Fail-safe behavior

✅ **Full audit trail exists**
- Decisions logged
- Trades traced
- Causal chains valid

✅ **No real execution possible**
- Paper mode only
- Cannot be overridden
- Safety guaranteed

✅ **Dashboard shows integration**
- AI decisions visible
- Execution status clear
- Confidence displayed

---

## Key Achievement

After Phase 4B:

> Independent AI Trader becomes a **black-box alpha engine inside Lantern OS**
> 
> Not replaced.
> Not rewritten.
> Just **connected, governed, and observable**.

---

## Next: Phase 4C (Optional)

When Phase 4B proves stable (typically 2-4 weeks of paper trading):

```
Phase 4C — Controlled Live Execution Upgrade
```

Where paper trades can be **selectively promoted to real execution** with:
- Per-trade confirmation
- Risk limits
- Position sizing constraints
- Maximum loss gates
- Real-time monitoring

But ONLY after Phase 4B demonstrates:
- Zero safety violations
- 100% audit accuracy
- Stable operation
- User confidence

---

## Architecture After 4B

```
Phase 4B = Black-box Alpha Engine Integrated

Independent AI Trader (unchanged logic)
        ↓
Service Wrapper (observation + routing)
        ↓
Safety Gate (stability gated)
        ↓
Trade State Engine (paper execution)
        ↓
Audit System (Phase 3.8)
        ↓
Dashboard (visibility)

= Unified Observability + Control Stack with External Alpha
```

This is **production-ready integration** of external profitable systems.
