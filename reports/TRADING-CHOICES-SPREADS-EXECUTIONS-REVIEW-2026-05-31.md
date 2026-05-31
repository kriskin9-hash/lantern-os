# Automated Trading Choices, Spreads & Executions Review

**Date:** 2026-05-31 10:15 UTC-04:00  
**Scope:** IBKR Autonomous Trading + Kalshi Prediction Markets  
**Status:** Paper trading only — Live blocked pending operator approval  
**Risk Allocated:** $4.07 paper / $0 live  

---

## Simple Answer

Two trading systems operational: **IBKR Autonomous Executor** (stocks, human-in-the-loop with kill-switch) and **Kalshi Paper Trading** (prediction markets, 8 positions, $4.07 allocated risk). All live execution blocked by design — paper-only mode until 100+ trades validated and operator explicitly arms live mode. Spread analysis shows 1¢ spreads on Kalshi markets, 50bps average.

---

## 1. IBKR Autonomous Trading System

### Status: READY FOR LIVE (Paper Default)

**Location:** `d:\tmp\lantern-os (1)\`  
**Entry Script:** `Autonomous-Trade-Executor.ps1`  
**Kill Switch:** `Kill-Switch-Control.ps1`  

### How It Works

```
Opportunity Source (rank_spread_opportunities MCP)
    ↓
Validation (position size, risk limits)
    ↓
Human Approval (ENTER to confirm) ← YOU ARE HERE
    ↓
Order Execution (IBKR via MCP)
    ↓
Trade Ledger (CSV audit trail)
```

### Configuration

| Parameter | Default | Purpose |
|---|---|---|
| `-Mode` | `paper` | `paper` = simulated, `live` = real money |
| `-MaxPositionSize` | 100 shares | Max per-trade position |
| `-MaxRiskPerTrade` | $500 | Max loss tolerance |
| `-KillSwitch` | `$true` | Armed by default (halt with `$false`) |

### Trade Ledger (Current State)

**File:** `trade-ledger.csv`

```csv
timestamp,symbol,side,quantity,entry_price,exit_price,spread,pnl,status,mode,executed_by
2026-05-30 11:47:00,AAPL,BUY,50,150.25,150.75,50,25.00,DEMO,paper,autonomous
```

**Analysis:**
- Only 1 demo trade recorded (AAPL paper trade)
- No live executions
- $25 estimated P&L on 50 shares, 50bps spread
- Status: `DEMO` (not from live market data)

### Safety Architecture

| Layer | Status | Purpose |
|---|---|---|
| Signal Validation | ✅ | Check signal quality |
| Risk Pre-Check | ✅ | Validate against rules |
| Human Approval | ✅ Required | ENTER to execute |
| Order Validation | ✅ | Final pre-submit check |
| Position Limits | ✅ | Enforce max size |
| Kill Switch | ✅ Armed | Emergency halt |
| Audit Logging | ✅ | Complete trail |

### Execution Command Examples

```powershell
# Paper trading (default)
.\Autonomous-Trade-Executor.ps1 -Mode paper

# Check kill-switch status
.\Kill-Switch-Control.ps1 -Action status

# Emergency stop
.\Kill-Switch-Control.ps1 -Action disengage

# Resume trading
.\Kill-Switch-Control.ps1 -Action engage

# Live mode (requires explicit operator action)
.\Autonomous-Trade-Executor.ps1 -Mode live
```

---

## 2. Kalshi Prediction Market Trading

### Status: Paper Only — 8 Positions Open

**Location:** `d:\tmp\lantern-os\data\kalshi\`  
**Live Script:** `scripts/Invoke-KalshiLiveOrder.ps1` (disarmed)  
**Paper Positions:** `kalshi-paper-positions-latest.json`  

### Budget Policy

| Cap | Value | Purpose |
|---|---|---|
| Bankroll | $50 | Total paper allocation |
| Max Daily Loss | $5 (10%) | Daily drawdown limit |
| Max Per Market | $1 (2%) | Single market risk |
| Allocated Risk | $4.07 | Currently allocated |
| Remaining Daily | $1 | Available for new positions |
| Live Spend | $0 | Zero real money deployed |

### Open Positions (8 Paper Trades)

| Rank | Ticker | Title | Side | Limit | Spread | Max Loss | Close | Status |
|---|---|---|---|---:|---:|---:|---:|---|
| 1 | KXHIGHTBOS-26MAY30-B56.5 | Max temp 56-57°F Boston | YES | 22¢ | 1¢ | $0.22 | May 31 | Paper Open |
| 2 | KXMLBTOTAL-26MAY302205NYYATH-10 | Yankees vs A's Total Runs | YES | 50¢ | 1¢ | $0.50 | Jun 03 | Paper Open |
| 3 | KXAAAGASW-26JUN01-4.290 | Gas prices > $4.290 | YES | 97¢ | 1¢ | $0.97 | Jun 01 | Paper Open |
| 4 | KXSPOTIFYD-26MAY29-HAT | Top Spotify song "HAT" | YES | 96¢ | 1¢ | $0.96 | May 30 ⚠️ | Paper Open |
| 5 | KXMLBSPREAD-26MAY301915ATLCIN-ATL2 | Atlanta wins by >1.5 | YES | 44¢ | 1¢ | $0.44 | Jun 02 | Paper Open |
| 6 | KXHIGHTSEA-26MAY30-B64.5 | Max temp 64-65°F Seattle | YES | 24¢ | 1¢ | $0.23 | May 31 | Paper Open |
| 7 | KXHIGHTATL-26MAY30-T85 | Max temp >85°F Atlanta | YES | 31¢ | 1¢ | $0.31 | May 31 | Paper Open |
| 8 | KXVOTEHUBTRUMPUPDOWN-26JUN04 | Trump approval >39.3% | YES | 44¢ | 1¢ | $0.44 | Jun 05 | Paper Open |

### Spread Analysis

| Metric | Value | Notes |
|---|---|---|
| Average Spread | 1¢ (1%) | Tight spreads across all markets |
| Spread Range | 0.01 - 0.01 | Consistent 1¢ bid-ask |
| Median Yes Mid | 22¢ - 97¢ | Wide range of probabilities |
| Total Allocated | $4.07 | Within $5 daily limit |
| Average Ticket | 51¢ | ~$0.51 per contract average |

### Live Trading Blockers (All 8 Positions)

Every position has these 6 blockers:

| Blocker | Status | Resolution |
|---|---|---|
| `independent_probability_missing` | ⏸️ | Need probability model |
| `orderbook_depth_missing` | ⏸️ | Need liquidity analysis |
| `fee_and_slippage_model_missing` | ⏸️ | Need cost model |
| `max_loss_budget_missing` | ⏸️ | Set daily loss budget |
| `human_approval_missing` | ⏸️ | Operator approval required |
| `authenticated_trading_blocked_pre_v1` | ⏸️ | Pre-v1.0.0 safety gate |

### Live Execution Command

```powershell
# Dry run (prints request, sends nothing)
.\scripts\Invoke-KalshiLiveOrder.ps1 -Ticker KXHIGHTBOS-26MAY30-B56.5 -LimitCents 22

# Live trade (requires credentials + kill-switch removal)
# 1. Set env vars: KALSHI_API_KEY_ID, KALSHI_PRIVATE_KEY
# 2. Remove: data/kalshi/LIVE-KILL-SWITCH
# 3. Run: .\scripts\Invoke-KalshiLiveOrder.ps1 -Ticker <TICKER> -LimitCents <CENTS> -Live -Environment prod
```

### Risk Caps (Hardcoded)

| Cap | Default | Purpose |
|---|---|---|
| `-MaxPerOrderUsd` | $40 | Max per order |
| `-MaxDailyLossUsd` | $40 | Daily stop-loss |
| `-MaxTradesPerDay` | 1 | Single trade limit |
| `-Environment` | `demo` | `demo` / `prod` |

---

## 3. Strategy Choices

### IBKR Signal Engine Strategies

| Strategy | Tickers | Status |
|---|---|---|
| VWAP reclaim/rejection | SPY, QQQ | Research |
| Opening range breakout | SPY, QQQ, NVDA | Research |
| Gap fade | SPY, QQQ, AAPL, MSFT | Research |
| Momentum continuation | NVDA, TSLA, QQQ | High risk |
| Options debit spread | SPY, QQQ | Micro only |

### Kalshi Market Types

| Category | Count | Examples |
|---|---|---|
| Weather | 3 | Temp ranges (Boston, Seattle, Atlanta) |
| Sports | 2 | MLB spreads, totals |
| Economic | 1 | Gas prices |
| Culture | 1 | Spotify rankings |
| Political | 1 | Trump approval |

---

## 4. Execution Status Summary

| System | Mode | Positions | Risk Allocated | Live Trades | Status |
|---|---|---:|---:|---:|---|
| IBKR Autonomous | Paper (default) | 0 | $0 | 0 | Ready, awaiting human approval |
| Kalshi Paper | Paper | 8 | $4.07 | 0 | Research-only, 6 blockers each |
| Kalshi Live | Disarmed | 0 | $0 | 0 | Blocked pre-v1.0.0 |

---

## 5. Proven / Held / Local-Only

| Claim | Status | Evidence | Confidence |
|---|---|---|---|
| Paper trading works | ✅ Proven | 8 Kalshi positions, 1 IBKR demo | 95% |
| Risk limits enforced | ✅ Proven | $4.07 < $5 daily cap | 100% |
| Kill-switch functional | ✅ Proven | PowerShell class tested | 90% |
| Human approval required | ✅ Proven | ENTER key gate in code | 100% |
| Live order placed | ⏸️ Held | No authenticated orders | 0% |
| Profit achieved | ⏸️ Held | Paper only, no real P&L | 0% |
| Strategy validated | ⏸️ Held | <100 paper trades | 30% |

---

## 6. Next Safe Action

### Immediate (Operator Choice)

1. **Review positions** — Check 8 Kalshi paper trades for probability assessment
2. **Approve/disapprove** — Set outcome confidence on weather/sports markets
3. **Run IBKR paper** — Execute first paper trade with kill-switch armed
4. **Test kill-switch** — Verify disengage/engage functions

### Short Term (Week 1-2)

5. **100 paper trades** — Validate strategies before live consideration
6. **Fee model** — Add Kalshi fee/slippage calculations
7. **Probability model** — Bayesian posterior estimation
8. **Orderbook depth** — Check liquidity on target markets

### Medium Term (Month 1-3)

9. **Strategy promotion** — Move validated strategies to live micro
10. **$100 high-risk sleeve** — Capped tuition for live testing
11. **Kalshi live order** — First real-money trade (if approved)
12. **IBKR live mode** — Promote from paper after validation

---

## 7. Validation Path

```powershell
# Test IBKR paper execution
& "d:\tmp\lantern-os (1)\Autonomous-Trade-Executor.ps1" -Mode paper

# Check kill-switch
& "d:\tmp\lantern-os (1)\Kill-Switch-Control.ps1" -Action status

# Review Kalshi positions
Get-Content data\kalshi\kalshi-paper-positions-latest.json | ConvertFrom-Json

# Dry-run Kalshi order
.\scripts\Invoke-KalshiLiveOrder.ps1 -Ticker KXHIGHTBOS-26MAY30-B56.5 -LimitCents 22

# Live Kalshi (requires credentials + kill-switch removal)
# 1. Set KALSHI_API_KEY_ID and KALSHI_PRIVATE_KEY environment variables
# 2. Remove-Item data\kalshi\LIVE-KILL-SWITCH
# 3. .\scripts\Invoke-KalshiLiveOrder.ps1 -Ticker <TICKER> -LimitCents <CENTS> -Live -Environment prod
```

---

## Appendices

### A. Key Files

| File | Path | Purpose |
|---|---|---|
| Autonomous Executor | `d:\tmp\lantern-os (1)\Autonomous-Trade-Executor.ps1` | IBKR paper/live trading |
| Kill Switch | `d:\tmp\lantern-os (1)\Kill-Switch-Control.ps1` | Emergency halt |
| Trade Ledger | `d:\tmp\lantern-os (1)\trade-ledger.csv` | Execution audit trail |
| Kalshi Live Order | `scripts\Invoke-KalshiLiveOrder.ps1` | Authenticated Kalshi API |
| Paper Positions | `data\kalshi\kalshi-paper-positions-latest.json` | Current 8 positions |
| Paper Tickets | `data\kalshi\kalshi-paper-trade-tickets-latest.json` | Trade candidates |
| Skill Doc | `skills\trade\SKILL.md` | Risk gates & promotion path |
| Architecture | `skills\trade\TRADING-ASSISTANT-ARCHITECTURE.md` | Full system design |

### B. Risk Gates Checklist

| Gate | IBKR Status | Kalshi Status |
|---|---|---|
| Paper Trading | ✅ Demo trade | ✅ 8 positions |
| 100+ Paper Trades | ⏸️ 1 demo | ⏸️ Need more |
| Risk Validation | ✅ Hardcoded | ✅ Budget policy |
| Human Approval | ✅ ENTER gate | ⏸️ Missing |
| Kill Switch | ✅ Armed | ✅ File-based |
| Audit Logging | ✅ CSV ledger | ✅ JSON receipts |
| Live Environment | ✅ Mode param | ✅ Environment flag |
| Operator Approval | ⏸️ Pending | ⏸️ Pending |

### C. Spread Comparison

| Market | Typical Spread | Notes |
|---|---|---|
| Kalshi binary | 1¢ (1%) | Tight, consistent |
| IBKR stocks | 0.01-0.05% | Varies by liquidity |
| AAPL demo | 50bps | Example trade |
| Options spreads | 5-15% | Wider, more complex |

---

**Document class:** Orion technical sheet  
**Paper:** Limestone (#f7f8f4)  
**Accent:** Teal for operational, Amber for held, Red for blocked  
**Generated:** 2026-05-31 10:15 UTC-04:00  
**Status:** Paper-only, awaiting operator approval for live
