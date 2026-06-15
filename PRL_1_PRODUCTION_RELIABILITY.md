# PRL-1: Production Reliability Layer 1

## The Heart of a Fault-Tolerant Trading System

**Goal:** Make Lantern OS + Independent AI Trader crash-safe, replay-safe, and delivery-safe.

This is not a feature layer. This is the **immune system and heartbeat** of the trading infrastructure.

---

## The 4 Failure Points This Solves

### ❌ BEFORE PRL-1

```
Problem 1: Python trader crashes → silent failure
Problem 2: HTTP message lost → trade never executed
Problem 3: Restart replays trade → duplicate execution
Problem 4: State desync after restart → corrupted engine
```

### ✅ AFTER PRL-1

```
Solution 1: Watchdog monitors trader, auto-restart on crash
Solution 2: Persistent queue guarantees message durability
Solution 3: Idempotency store prevents duplicate execution
Solution 4: Queue replay rebuilds state deterministically
```

---

## Core Architecture

### Replace This:
```
Python Trader
    ↓ (HTTP call)
Node Trade Engine
    ↓
Execution
```

### With This:
```
Python Trader
    ↓ (write to disk)
Persistent Event Queue
    ↓ (consumer loop, 250ms interval)
Idempotency Check
    ↓
Safety Gate Check (stability)
    ↓
Node Trade Engine
    ↓
Execution + Audit
```

---

## The Components

### 1. **PersistentEventQueue** (`core/persistent-event-queue.js`)

**Purpose:** Guarantee no lost trades EVER.

**How it works:**
- Append-only disk file: `/data/trading/event-queue.jsonl`
- Every AI decision written BEFORE processing
- Survives crashes instantly

**Every event:**
```json
{
  "eventId": "evt-xyz",
  "traceId": "trace-123",
  "source": "independent-ai-trader",
  "type": "TRADE_SIGNAL",
  "payload": {
    "ticker": "NVDA",
    "action": "BUY",
    "confidence": 0.82
  },
  "status": "PENDING",
  "timestamp": 1710000000
}
```

**Key methods:**
- `enqueueEvent(traceId, source, payload)` — Write to disk first
- `getPendingEvents()` — Get all PENDING events
- `markProcessed(eventId, result)` — Mark as EXECUTED (never delete)

### 2. **IdempotencyStore** (`core/idempotency-store.js`)

**Purpose:** Prevent duplicate trades from restart replay.

**How it works:**
- Append-only disk file: `/data/trading/executed-events.jsonl`
- Every executed event recorded
- Check before processing: "Have I seen this before?"

**Rule:**
```
if (alreadyExecuted(eventId)) {
    skip();
}
```

**Key methods:**
- `hasExecuted(eventId)` — Check if already done
- `recordExecution(eventId, tradeId, result)` — Write to disk

### 3. **EventQueueConsumer** (`core/event-queue-consumer.js`)

**Purpose:** The heartbeat that guarantees execution.

**The loop (every 250ms):**
```
1. Get pending events from queue
2. For each (up to 10 per batch):
   a. Check if already executed (idempotency)
   b. Check stability index >= 0.8 (safety gate)
   c. Submit to Trade State Engine
   d. Record idempotency
   e. Mark queue event EXECUTED
```

**Key methods:**
- `start()` — Begin the loop
- `_processEvent(event)` — Process single event
- `getStatus()` — Get health metrics

### 4. **TraderWatchdog** (`core/trader-watchdog.js`)

**Purpose:** Keep Python trader alive and responsive.

**Monitoring (every 10 seconds):**
```
1. Is process alive?
   → No: Restart
2. Is process hanging? (no output in 30s)
   → Yes: Kill + Restart
3. All good: Continue
```

**Key methods:**
- `start()` — Start watchdog + trader
- `_checkHealth()` — Periodic health check
- `getStatus()` — Get process status

---

## Event State Machine

Every event has a strict state:

```
PENDING (in queue, awaiting processing)
   ↓
PROCESSING (consumer working on it)
   ↓
EXECUTED (completed successfully)
   ↓
RECORDED (audit trail written)
```

**CRITICAL RULE:** No hidden states. No silent failures.

---

## Guarantee Chain

### Guarantee 1: No Lost Trades
```
AI Decision Generated
    ↓
Written to disk FIRST (before HTTP, before processing)
    ↓
Consumer picks up from queue
    ↓
Executed in engine
    ↓
EVEN IF system crashes before step 3, decision survives
```

### Guarantee 2: No Duplicates
```
AI Decision Executed (eventId = "evt-123")
    ↓
Recorded in idempotency store
    ↓
System crashes and restarts
    ↓
Queue replays "evt-123"
    ↓
Idempotency check: "Already executed? YES"
    ↓
Skip it (prevents duplicate trade)
```

### Guarantee 3: No Silent Crashes
```
Python trader crashes
    ↓
Watchdog detects (no heartbeat)
    ↓
Auto-restart
    ↓
Event queue consumer resumes
    ↓
All pending events reprocessed
```

### Guarantee 4: Deterministic Recovery
```
System crashes
    ↓
Server restarts
    ↓
Load event queue from disk
    ↓
Load executed events from idempotency store
    ↓
Consumer loop resumes
    ↓
Replay all PENDING events (safe due to idempotency)
    ↓
Engine state rebuilt exactly as it was
```

---

## Startup Sequence

On server boot, MUST happen in this order:

```
1. Load Event Queue
   (read all events from /data/trading/event-queue.jsonl)

2. Load Idempotency Store
   (read all executed events)

3. Rebuild Trade Engine State
   (trades exist in engine from audit log + state snapshots)

4. Start Event Queue Consumer
   (resume processing pending events)

5. Start Trader Watchdog
   (spawn Python trader, monitor health)
```

**Result:** System picks up exactly where it left off. No state loss.

---

## Failure Recovery Examples

### Scenario 1: Python Crash During Decision

```
Python trader generates: BUY NVDA (confidence 0.82)
    ↓
Writes to event queue (disk-backed)
    ↓
Python crashes (before HTTP POST)
    ↓
Watchdog detects crash (no heartbeat)
    ↓
Watchdog restarts Python
    ↓
Consumer picks up from queue
    ↓
Trade executes as normal
RESULT: No lost trade
```

### Scenario 2: HTTP Message Lost

```
Consumer submits to Trade Engine: "BUY NVDA"
    ↓
Network error (message lost)
    ↓
Event still marked PENDING in queue
    ↓
Consumer retries next loop (250ms later)
    ↓
Trade executes successfully
RESULT: No lost trade
```

### Scenario 3: System Crash During Execution

```
Server is executing: "BUY NVDA" trade
    ↓
System power fails
    ↓
Hard crash
    ↓
Server reboots
    ↓
Load event queue (saw "BUY NVDA", status=EXECUTING)
    ↓
Load idempotency store (saw "BUY NVDA" already executed)
    ↓
Consumer gets PENDING event
    ↓
Idempotency check: "Already done? YES"
    ↓
Skip it (no duplicate)
RESULT: No duplicate trade
```

### Scenario 4: Restart Replay

```
System running fine, then restarts
    ↓
Event queue has 100 pending events
    ↓
Consumer resumes loop
    ↓
Reprocesses all 100 (only 50 were already executed)
    ↓
Idempotency store prevents 50 duplicates
    ↓
Engine picks up where it left off
RESULT: Deterministic state recovery
```

---

## Monitoring & Health

### Queue Health
```bash
GET /api/trading/prl/status
→ {
    "queue": {
      "totalEvents": 1247,
      "pendingEvents": 23,
      "executedEvents": 1224
    },
    "consumer": {
      "running": true,
      "processed": 1224,
      "failed": 0
    },
    "watchdog": {
      "traderAlive": true,
      "restartCount": 2,
      "timeSinceHeartbeat": "0.3s"
    }
  }
```

### Alerts
If ANY of these happen:
```
🔴 Consumer stopped
🔴 Queue write failed
🔴 Idempotency store corrupted
🔴 Trader unresponsive for > 30s
🔴 Watchdog restart loop (10+ restarts/hour)
```

→ **Suspend AI trader immediately**

---

## Critical Properties

### Durability
✅ Every decision written to disk before processing

### Idempotency
✅ Every trade executed exactly once

### Determinism
✅ Restart replay is deterministic

### Observability
✅ Full event history preserved

### Atomicity
✅ Event status transitions are atomic

### Crash-Safety
✅ Works after power loss

### Replay-Safety
✅ Can safely replay from any point

---

## What This Enables

With PRL-1 in place:

✅ **Autonomous Operation**
- No babysitting
- Auto-recovery from crashes
- Auto-restart on hang

✅ **Safe Scaling**
- Can add multiple consumers (later)
- Can replicate queue (later)
- Can distribute execution (later)

✅ **Production Deployment**
- Can run 24/7/365
- Handles power loss gracefully
- Handles network loss gracefully

✅ **Regulatory Compliance**
- Full audit trail
- No lost transactions
- Deterministic replay

---

## Implementation Status

### ✅ COMPLETE (PRL-1)
- PersistentEventQueue
- IdempotencyStore
- EventQueueConsumer
- TraderWatchdog
- Startup recovery
- Failure handling

### 🔄 NEXT (PRL-2, optional)
- Redis-backed queue
- Multi-instance consumers
- Distributed replay

### 📌 FUTURE (PRL-3, optional)
- Event compaction
- Cross-datacenter sync
- Byzantine fault tolerance

---

## This is the Foundation

Without PRL-1:
> Lantern OS is an impressive trading app that can crash silently.

With PRL-1:
> Lantern OS is a fault-tolerant trading infrastructure that **never loses a trade and always recovers deterministically**.

---

## Key Achievement

You've moved from:
```
"AI generates trades"
```

To:
```
"System guarantees execution correctness despite any failure"
```

That's the difference between a prototype and production infrastructure.
