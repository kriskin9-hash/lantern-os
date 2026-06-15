# PRL-1.3: Risk Governor — Capital Protection Layer

## The Problem

Before PRL-1.3:

```
AI Trader → Event Queue → Engine → Alpaca

All subsystems say "YES" to a trade.
But... what if we've already lost enough capital today?
What if we're overleveraged?
What if we should just STOP?

Answer: NO ONE IS IN CHARGE OF CAPITAL.
```

Each subsystem validates, but no single point can say "NO" for money reasons.

---

## The Solution: Risk Governor

**A single centralized authority that sits ABOVE all execution logic.**

```
AI Trader
   ↓
Event Queue (PRL-1)
   ↓
Trade Engine
   ↓
Execution Router
   ↓
🟥 RISK GOVERNOR (PRL-1.3) ← FINAL AUTHORITY
   ↓ [decision: allow or block]
Alpaca Paper Trading
```

**Even if:**
- AI says BUY
- Engine validates it
- Router approves it
- Stability gate passes

**Risk Governor can still say NO.**

---

## Architecture

### Seven Capital Protection Gates

The Risk Governor checks these BEFORE any execution:

| Gate | Check | Purpose |
|------|-------|---------|
| **1** | Is governor enabled? | Emergency kill switch |
| **2** | Emergency stop active? | Manual override |
| **3** | Cooldown passed? | Throttle trading frequency |
| **4** | Open trades < max? | Avoid overconcentration |
| **5** | Position size < limit? | Prevent single-trade blowup |
| **6** | Daily loss < max? | Stop after threshold loss |
| **7** | Drawdown < max? | Prevent catastrophic loss |

**All gates must pass. ONE NO blocks the trade.**

---

## Core Component: RiskGovernor

### Configuration

```javascript
new RiskGovernor({
  maxDailyLossUSD: 500,        // Stop if lost $500 today
  maxPositionSizeUSD: 1000,    // No single trade > $1000
  maxOpenTrades: 5,            // Never more than 5 simultaneous
  cooldownMs: 5000,            // Wait 5s between trades
  maxDrawdownPercent: 10       // Stop if down 10% from high water
})
```

### Evaluation Logic

```javascript
const riskCheck = riskGovernor.evaluateTrade(trade, context);

// Returns:
{
  allowed: true|false,
  reasons: ["COOLDOWN_ACTIVE", "MAX_DAILY_LOSS_REACHED"],
  severity: "info" | "warning" | "critical"
}
```

### Record Execution

```javascript
// After trade fills, record the P&L
riskGovernor.recordExecution(trade, executionResult);

// Updates state:
// - lastTradeTime
// - openTrades count
// - dailyPnL
// - drawdown calculation
```

---

## Integration Points

### 1. **Execution Router** (FIRST check, highest priority)

```javascript
const riskCheck = this.riskGovernor.evaluateTrade(trade);

if (!riskCheck.allowed) {
  return {
    routed: false,
    path: "risk_blocked",
    reason: "risk_governor_blocked",
    governorReasons: riskCheck.reasons
  };
}
```

**Why first?** Governor is ABOVE all other gates. Nothing should execute if risk says no.

### 2. **Event Consumer** (Before Alpaca call)

```javascript
const riskCheck = this.riskGovernor.evaluateTrade(trade);

if (!riskCheck.allowed) {
  // Log RISK_BLOCK event
  // Mark queue as processed
  // Return (don't execute)
}

// If allowed, continue to Alpaca...
const result = await this.alpacaAdapter.executeTrade(trade);

// After execution, record in governor
if (result.status === "filled") {
  this.riskGovernor.recordExecution(trade, result);
}
```

### 3. **Server Initialization**

```javascript
const riskGovernor = new RiskGovernor({
  maxDailyLossUSD: Number(process.env.MAX_DAILY_LOSS_USD || 500),
  maxPositionSizeUSD: Number(process.env.MAX_POSITION_SIZE_USD || 1000),
  maxOpenTrades: Number(process.env.MAX_OPEN_TRADES || 5),
  cooldownMs: Number(process.env.TRADE_COOLDOWN_MS || 5000),
  maxDrawdownPercent: Number(process.env.MAX_DRAWDOWN_PERCENT || 10)
});

// Pass to both ExecutionRouter and EventQueueConsumer
const executionRouter = new ExecutionRouter(alpacaAdapter, {
  riskGovernor
});

const eventQueueConsumer = new EventQueueConsumer(queue, idempotency, {
  riskGovernor
});
```

---

## API Endpoints

### GET `/api/risk/status`

View current risk state and limits.

**Response:**
```json
{
  "timestamp": "2026-06-14T10:30:00Z",
  "status": "ACTIVE",
  "limits": {
    "maxDailyLossUSD": 500,
    "maxPositionSizeUSD": 1000,
    "maxOpenTrades": 5,
    "cooldownMs": 5000,
    "maxDrawdownPercent": 10
  },
  "metrics": {
    "dailyPnL": -120.50,
    "openTrades": 2,
    "executedCount": 45,
    "blockedCount": 7,
    "currentDrawdown": "3.2%",
    "lastTradeTime": "2026-06-14T10:29:55Z"
  }
}
```

### POST `/api/risk/emergency-stop`

Activate emergency stop. Freezes ALL trading immediately.

**No body required.**

**Response:**
```json
{
  "status": "emergency_stop_activated",
  "timestamp": "2026-06-14T10:30:00Z",
  "message": "All trading is now frozen. Manual resume required."
}
```

### POST `/api/risk/resume`

Resume trading after emergency stop.

**No body required.**

**Response:**
```json
{
  "status": "trading_resumed",
  "timestamp": "2026-06-14T10:30:05Z",
  "message": "Trading is now enabled."
}
```

### POST `/api/risk/reset-daily`

Reset daily P&L counters. Call at market open each day.

**No body required.**

**Response:**
```json
{
  "status": "daily_reset",
  "timestamp": "2026-06-14T10:30:00Z",
  "message": "Daily P&L and block counters have been reset."
}
```

### POST `/api/risk/limit`

Update a risk limit dynamically.

**Request:**
```json
{
  "field": "maxDailyLossUSD",
  "value": 1000
}
```

**Response:**
```json
{
  "status": "limit_updated",
  "field": "maxDailyLossUSD",
  "value": 1000,
  "timestamp": "2026-06-14T10:30:00Z"
}
```

---

## Safety Architecture (Defense in Depth)

| Layer | System | Question |
|-------|--------|----------|
| **1** | Queue (PRL-1) | Can we lose the trade? |
| **2** | Idempotency (PRL-1) | Will we duplicate it? |
| **3** | Stability (Phase 3.7) | Is the system stable? |
| **4** | Router (PRL-1.2) | Is the execution mode correct? |
| **5** | Governor (PRL-1.3) | Should we risk more capital? |
| **6** | Alpaca (Broker) | Can we fill it? |

**Every layer must say YES. One NO blocks it.**

---

## Example: Emergency Scenario

### Scenario: Market Crash During Trading

```
10:00 AM - System starts, dailyPnL = 0, openTrades = 0
10:05 AM - AI: BUY 100 NVDA (PnL = $0, OK)
10:06 AM - AI: BUY 100 NVDA (PnL = +$50, OK)
10:07 AM - Flash crash: market down 8%
          Current drawdown = 8%, within limit ✅
10:08 AM - AI: BUY 100 TSLA (PnL = -$320, cumulative)
          Daily loss check: -$320 < -$500? No, still OK ✅
10:09 AM - Flash crash intensifies: down 12%
          Current drawdown = 12% > max 10% ❌
          RISK GOVERNOR BLOCKS: "MAX_DRAWDOWN_EXCEEDED"
10:10 AM - Human: POST /api/risk/emergency-stop
          Governor status → EMERGENCY_STOP_ACTIVE
          All future trades blocked (even if AI keeps signaling)
10:15 AM - Market stabilizes
          Human: POST /api/risk/resume
          Governor resumes normal operation
```

**Result:**
- Queue has all events (none lost)
- Only trades that passed all gates executed
- Governor prevented catastrophic further loss
- Full audit trail of what happened and why

---

## Key Principles

### 1. Single Point of Authority
```
Only ONE system makes the capital decision.
Not AI, not engine, not router.
GOVERNOR.
```

### 2. Governor is Above All
```
Governor is checked FIRST.
Before stability gate.
Before idempotency.
Before everything.
```

### 3. Fail Closed
```
If governor is disabled, trading is disabled.
If ANY gate fails, trade is blocked.
Default to "don't trade" not "trade".
```

### 4. Human Override
```
Emergency stop is a one-call override.
POST /api/risk/emergency-stop
Instantly freezes everything.
No trade can execute while active.
```

### 5. Transparency
```
Every block is logged.
Every execution is recorded in governor.
Every limit update is tracked.
Full audit trail always.
```

---

## Environment Variables

```bash
# Risk limits (in USD)
MAX_DAILY_LOSS_USD=500              # Stop if lost this much today
MAX_POSITION_SIZE_USD=1000          # Max notional per trade
MAX_OPEN_TRADES=5                   # Max concurrent positions

# Throttling
TRADE_COOLDOWN_MS=5000              # Minimum time between trades

# Drawdown
MAX_DRAWDOWN_PERCENT=10             # Max % loss from high water mark
```

---

## Observability

### Metrics Tracked

```javascript
{
  enabled: true,                    // Is governor active?
  emergencyStop: false,             // Kill switch status
  dailyPnL: -120.50,               // Today's profit/loss
  openTrades: 2,                    // Active positions
  executedCount: 45,               // Trades filled today
  blockedCount: 7,                 // Trades rejected today
  currentDrawdown: "3.2%",         // % down from high
  lastTradeTime: "2026-06-14..."   // Most recent execution
}
```

### How to Monitor

```bash
# Check current state
curl http://localhost:4177/api/risk/status

# Parse for critical metrics
# - status: "ACTIVE" vs "EMERGENCY_STOP"
# - blockedCount > 10 = system too restrictive?
# - dailyPnL trending negative = may need action
```

---

## What This Fixes

### Before PRL-1.3:
```
Execution is "obedient"
→ AI says trade
→ Engine validates
→ Router routes
→ Alpaca fills
→ System has no capital guardrails
```

### After PRL-1.3:
```
Execution is "guarded"
→ Risk Governor checks capital
→ If "NO", everything stops
→ If "YES", normal flow continues
→ System protects itself
```

---

## Relationship to Other Layers

| Layer | Defends Against | Method |
|-------|-----------------|--------|
| **PRL-1** | Lost trades | Persistent queue + replay |
| **PRL-1.1** | Cloud coupling | HTTP boundary |
| **PRL-1.2** | Execution failure | Alpaca integration |
| **PRL-1.3** | Capital loss | Risk gates |

**Each layer is independent. They don't know about each other.**

---

## Next Steps (After This)

After PRL-1.3, the system is:
- ✅ Crash-safe (PRL-1)
- ✅ Cloud-safe (PRL-1.1)
- ✅ Execution-safe (PRL-1.2)
- ✅ Capital-safe (PRL-1.3)

The next phase would be:
- **PRL-2: Portfolio Intelligence** — Position sizing, adaptive risk, volatility-aware trading

But don't build that until PRL-1.3 is proven in production.

---

## Summary

PRL-1.3 is the **capital preservation layer**.

It answers the question every trading system needs:
> "Even if everything else says YES… should we STILL trade?"

The answer is:
> "ONLY if we're still within our risk envelope."

**This is what separates a paper trading machine from a self-protecting trading system.**
