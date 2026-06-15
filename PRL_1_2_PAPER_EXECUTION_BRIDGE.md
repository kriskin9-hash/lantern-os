# PRL-1.2: Paper Execution Bridge — Alpaca Integration

## The Goal

Connect Lantern OS execution layer to Alpaca paper trading so that:

- AI decisions flow through PRL-1 queue → Trade State Engine → Alpaca paper account
- NO live trading is introduced (paper mode only)
- FULL traceability preserved (Phase 3.8 audit chain)
- Safety gate (stability index ≥ 0.8) remains mandatory
- System becomes a **closed-loop paper trading machine**

---

## Architecture

```
AI Trader (Python)
   ↓ HTTP ingestion (PRL-1.1)
Event Queue (PRL-1)
   ↓ [250ms heartbeat]
Consumer
   ↓
Trade State Engine
   ↓ [NEW: PRL-1.2]
Execution Router
   ↓
Alpaca Paper API
   ↓
Broker Confirmation
   ↓
Audit Log (Phase 3.8)
   ↓
Dashboard UI
```

---

## Core Components

### 1. **Alpaca Execution Adapter** (`core/alpaca-execution-adapter.js`)

**Responsibility:** Normalize trades and call Alpaca API for paper execution.

**Input (from Trade Engine):**
```json
{
  "symbol": "AAPL",
  "side": "buy",
  "qty": 100,
  "type": "market",
  "time_in_force": "day"
}
```

**Output:**
```json
{
  "broker": "alpaca",
  "orderId": "evt-12345-abc123",
  "status": "filled|accepted|rejected",
  "filledQty": 100,
  "avgFillPrice": 150.23,
  "timestamp": 1710000000,
  "raw": {...}
}
```

**Key Features:**
- Wraps Alpaca SDK (or simulates for testing)
- Treats Alpaca as a "dumb execution endpoint"
- Maintains execution statistics (success rate, avg latency)
- Separates paper (default) from live trading modes

### 2. **Execution Router** (`core/execution-router.js`)

**Responsibility:** Decide execution path based on system state.

**Modes:**
- `paper`: Execute on Alpaca paper account (default)
- `simulation`: Mock fills (for testing, no broker call)
- `blocked`: Reject all execution (circuit breaker)

**Route Decision Logic:**
```
Check safety gates:
  ✅ stabilityIndex >= 0.8
  ✅ idempotency check passed
  ✅ event schema valid
  ✅ trade state = PENDING

→ Route based on execution mode
  → paper: Alpaca
  → simulation: Mock
  → blocked: Reject
```

**Safety Gates (Non-Negotiable):**
```
A trade ONLY executes if ALL are true:
  ✅ stabilityIndex >= 0.8 (Phase 3.7)
  ✅ idempotency check passed (PRL-1)
  ✅ event validated (schema OK)
  ✅ engine state = PENDING
  ✅ mode = paper (or explicitly enabled live)
```

### 3. **Modified Event Consumer** (`core/event-queue-consumer.js`)

**New Execution Flow:**

```
For each pending event:
  1. Check if already executed (idempotency guard)
  2. Check safety gate (stability >= 0.8)
  3. Validate event schema
  4. Create trade in State Engine
  5. [NEW] Execute on Alpaca via adapter
  6. Record execution result
  7. Log to audit trail (Phase 3.8)
  8. Mark queue event as processed
```

**Key Addition (Step 5):**
```javascript
const executionResult = await alpacaAdapter.executeTrade({
  symbol: payload.ticker,
  side: payload.action.toLowerCase(),
  qty: payload.quantity || 1,
  type: "market",
  time_in_force: "day"
});
```

---

## Configuration

### Environment Variables

```bash
# Alpaca credentials (from your account)
ALPACA_API_KEY=your-key
ALPACA_SECRET_KEY=your-secret

# Execution mode
EXECUTION_MODE=paper          # paper | simulation | blocked
ALLOW_LIVE_TRADING=false      # true only if you intend to enable live trading
```

### Runtime Topology (`config/runtime-topology.json`)

```json
{
  "execution": {
    "version": "prl-1.2",
    "mode": "paper",
    "broker": "alpaca",
    "allowLive": false,
    "safety_gates": {
      "stability_index_min": 0.8,
      "idempotency_required": true,
      "schema_validation_required": true,
      "engine_state_check_required": true
    }
  }
}
```

---

## Observability

### Execution Status Endpoint

```bash
GET /api/trading/execution-status
```

**Response:**
```json
{
  "timestamp": "2026-06-14T10:30:00Z",
  "broker": "alpaca",
  "mode": "paper",
  "alpaca": {
    "enabled": true,
    "mode": "paper",
    "totalExecutions": 1234,
    "filledTrades": 1212,
    "rejectedTrades": 22,
    "avgFillLatencyMs": 320,
    "successRate": "98.2%",
    "lastExecution": 1718356200000
  },
  "consumer": {
    "running": true,
    "metrics": {
      "processed": 1234,
      "executed": 1212,
      "skipped": 45,
      "failed": 22,
      "pending": 0,
      "successRate": "98.2%"
    },
    "alpaca": {...},
    "lastProcessTime": "2026-06-14T10:29:59Z",
    "loopInterval": "250ms"
  },
  "router": {
    "mode": "paper",
    "allowLive": false,
    "totalRouted": 1234,
    "acceptedTrades": 1212,
    "rejectedTrades": 22,
    "mockTrades": 0,
    "successRate": "98.2%"
  }
}
```

---

## Safety Architecture

### The Defense Layers

**Layer 1: Event Queue (PRL-1)**
- Persistent disk-backed queue
- No lost trades ever
- Survives crashes instantly

**Layer 2: Idempotency Store (PRL-1)**
- Prevents duplicate execution
- Every event executed exactly once

**Layer 3: Safety Gate (Phase 3.7)**
- Requires stability index ≥ 0.8
- Blocks execution if system is unstable

**Layer 4: Execution Router (PRL-1.2)**
- Routes based on mode (paper/simulation/blocked)
- Validates trade state before execution

**Layer 5: Audit Trail (Phase 3.8)**
- Every execution logged with full context
- Traceability for compliance and debugging

### Execution Cannot Happen Without:
```javascript
// Gate 1: Idempotency
if (idempotency.hasExecuted(eventId)) return skip;

// Gate 2: Safety
if (stabilityIndex < 0.8) return block;

// Gate 3: Schema
if (!payload.ticker || !payload.action) return reject;

// Gate 4: State
if (trade.status !== "PENDING") return reject;

// Gate 5: Mode
if (mode !== "paper" && !allowLive) return block;
```

---

## Test Flow

### Manual Verification

```bash
# 1. Check system is running
curl http://localhost:4177/api/trading/execution-status

# 2. Submit test trade via ingestion API
curl -X POST http://localhost:4177/api/events/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source": "test",
    "ticker": "AAPL",
    "action": "BUY",
    "confidence": 0.85
  }'

# 3. Verify execution (wait 250ms for consumer heartbeat)
curl http://localhost:4177/api/trading/execution-status

# 4. Check audit trail
curl http://localhost:4177/api/trading/audit/summary
```

### Expected Pipeline

```
1. AI generates: BUY AAPL confidence=0.85
2. POST /api/events/ingest accepts decision
3. Event enqueued (eventId, traceId returned)
4. Consumer picks up every 250ms
5. Checks stability >= 0.8 ✅
6. Checks idempotency ✅
7. Creates trade in State Engine
8. Calls Alpaca API (paper mode)
9. Alpaca returns filled order
10. Updates trade with execution
11. Records audit event BROKER_EXECUTION
12. Marks queue event PROCESSED
13. Trade appears in dashboard
14. Full trace available: /api/trading/audit/trace/{traceId}
```

---

## Files Changed

### New Files:
- `core/alpaca-execution-adapter.js` — Broker execution wrapper
- `core/execution-router.js` — Execution path decision engine

### Modified Files:
- `core/event-queue-consumer.js` — Added Alpaca execution step
- `apps/lantern-garage/server.js` — Initialized Alpaca and router
- `apps/lantern-garage/routes/trading.js` — Added execution-status endpoint
- `config/runtime-topology.json` — Added execution configuration

---

## Critical Design Rules

### ❌ NEVER:
- Call Alpaca directly from Python AI
- Skip the event queue
- Execute without stability gate (< 0.8)
- Allow live trading without explicit safeguards
- Bypass idempotency check

### ✅ ALWAYS:
- Route through PRL-1 queue
- Validate via Trade State Engine
- Log everything in audit layer
- Treat Alpaca as dumb execution endpoint
- Treat Node as source of truth

---

## What PRL-1.2 Enables

### Before:
> System validates trades but doesn't execute them.

### After:
> System validates trades AND executes them on Alpaca paper account.
> Every trade is traceable end-to-end.
> System is a closed-loop paper trading machine.

### Concrete Features:
✅ **Paper Trading** — Execute on Alpaca paper account (no real money)
✅ **Full Traceability** — Every trade in audit log with causal chain
✅ **Safety Gates** — Stability index check prevents bad executions
✅ **Idempotency** — Crash recovery doesn't cause duplicate trades
✅ **Observability** — Real-time execution metrics via API
✅ **Simulation Mode** — Test without calling Alpaca

---

## Why Alpaca as Dumb Endpoint?

We don't ask Alpaca to be smart. We ask it to:
1. Accept orders in a standard format
2. Fill them (paper mode)
3. Confirm execution

Alpaca doesn't:
- Decide if a trade should execute
- Check system stability
- Prevent duplicates
- Maintain audit trail

Node does all of that. Alpaca is purely a **mechanism for putting orders in the market**.

---

## Next Steps (PRL-2)

After PRL-1.2, the system is:
- ✅ Crash-safe (PRL-1)
- ✅ Cloud-safe (PRL-1.1)
- ✅ Paper-execution-safe (PRL-1.2)

The next phase (PRL-2) would be:
- **Live Trading Gating**: Unlock real money with strict risk caps
- **Position Limits**: Max holdings per symbol
- **Daily Loss Limits**: Auto-shutdown on losses
- **Volatility Checks**: Don't trade in extreme conditions

But that's a separate phase. For now, **PRL-1.2 is paper-only**.

---

## Summary

PRL-1.2 closes the loop from signal to execution:

```
Signal Generation → Validation → Durability → Execution
    (AI)           (Engine)      (Queue)      (Alpaca)
```

The system now:
1. Receives signals from external AI
2. Queues them durably
3. Validates them continuously
4. Routes them through execution gates
5. Fills them on Alpaca paper account
6. Records every step in audit trail

**This is a production-grade paper trading system.**

The next question is: **Can it handle live money?**

Answer: Not yet. That's PRL-2.
