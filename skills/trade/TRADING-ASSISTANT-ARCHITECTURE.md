# Lantern Trading Assistant Architecture

**Date:** 2026-05-30  
**Purpose:** Unified human-in-the-loop trading system for Kalshi and Interactive Brokers  
**Status:** Architecture design

---

## Simple Answer

A unified trading assistant that connects Lantern OS to Kalshi (prediction markets) and Interactive Brokers (traditional markets) with human approval at every step. The system generates trade signals, validates them against risk rules, presents them for human review, and executes only with explicit approval.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Lantern Trading Assistant                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Signal     │  │    Risk      │  │   Order      │      │
│  │   Engine     │──▶│   Manager    │──▶│   Manager    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         ▼                  ▼                  ▼              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Market Data │  │  Position    │  │  Broker      │      │
│  │  Feed        │  │  Tracker     │  │  Connectors  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                                    │              │
│         └────────────────────────────────────┘              │
│                              │                               │
│                              ▼                               │
│                    ┌──────────────┐                         │
│                    │  Human       │                         │
│                    │  Interface  │                         │
│                    └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. Signal Engine

**Purpose:** Generate trade signals from market data

**Inputs:**
- Market data (prices, volume, orderbook)
- Historical data
- Strategy parameters

**Outputs:**
- Trade signals (ticker, direction, entry, exit, confidence)
- Risk parameters (max loss, position size)

**Strategies:**
- VWAP reclaim/rejection
- Opening range breakout
- Gap fade
- Momentum continuation
- Kalshi event probability

---

### 2. Risk Manager

**Purpose:** Validate signals against risk rules

**Rules:**
- Max daily loss: $X
- Max per-trade loss: $Y
- No averaging down
- No revenge trading
- Position size limits
- Account balance checks

**Outputs:**
- Approved/rejected decision
- Recommended position size
- Stop loss level
- Take profit level

---

### 3. Order Manager

**Purpose:** Execute approved orders

**Features:**
- Order routing to appropriate broker
- Order validation
- Position tracking
- Order status monitoring
- Kill switch

**Brokers:**
- Kalshi (prediction markets)
- Interactive Brokers (stocks, options, futures)

---

### 4. Market Data Feed

**Purpose:** Provide real-time market data

**Sources:**
- Kalshi public API (unauthenticated)
- IBKR market data (authenticated)
- Historical data stores

**Data Types:**
- OHLCV (Open, High, Low, Close, Volume)
- Orderbook depth
- Trade history
- Options chains

---

### 5. Position Tracker

**Purpose:** Track current positions and P&L

**Tracking:**
- Open positions
- Real-time P&L
- Unrealized gains/losses
- Position history
- Trade ledger

---

### 6. Broker Connectors

**Purpose:** Interface with broker APIs

**Kalshi Connector:**
- Public market data (already working)
- Paper order placement (blocked pre-v1)
- Order status tracking
- Position management

**IBKR Connector:**
- Account data
- Market data
- Order placement (paper first)
- Position management
- Portfolio data

---

### 7. Human Interface

**Purpose:** Present trades for human review and approval

**Components:**
- Trading Dashboard
- Signal Review Panel
- Order Approval Flow
- Position Monitor
- P&L Dashboard
- Trade History

---

## Data Flow

### Signal Generation Flow

```
Market Data → Signal Engine → Risk Manager → Human Review → Order Manager → Broker
```

### Order Execution Flow

```
Human Approval → Order Validation → Position Check → Order Submission → Execution → Position Update
```

### Risk Enforcement Flow

```
Order Request → Risk Rules Check → Position Size Calc → Max Loss Check → Daily Loss Check → Approval/Reject
```

---

## Safety Architecture

### Multi-Layer Safety

1. **Signal Validation** - Check signal quality and confidence
2. **Risk Pre-Check** - Validate against risk rules before human review
3. **Human Approval** - Explicit human approval required
4. **Order Validation** - Final validation before submission
5. **Position Limits** - Enforce position size limits
6. **Kill Switch** - Emergency stop capability
7. **Audit Logging** - Complete audit trail

### Fail-Safes

- Paper trading mode by default
- Separate paper/live environments
- Hard-coded position size limits
- Daily loss limits
- Automatic stop on consecutive losses
- Manual kill switch

---

## Human-in-the-Loop Design

### Approval Workflow

1. **Signal Generated** - System generates trade signal
2. **Risk Check** - Signal validated against risk rules
3. **Human Review** - Trade presented to human with:
   - Ticker and market
   - Entry and exit levels
   - Max loss amount
   - Risk/reward ratio
   - Confidence score
   - Supporting data
4. **Human Decision** - Human approves, modifies, or rejects
5. **Order Placement** - If approved, order placed
6. **Execution Confirmation** - Human notified of execution
7. **Position Monitoring** - Position tracked and reported

### Review Panel Information

For each trade, show:
- Market and ticker
- Strategy used
- Entry price and stop loss
- Take profit level
- Position size
- Max loss amount
- Risk/reward ratio
- Confidence score
- Supporting chart/data
- Recent performance of strategy

---

## Paper Trading First

### Paper Trading Mode

- All trades simulated
- No real money at risk
- Full feature set available
- Complete audit trail
- Performance tracking

### Promotion to Live

**Requirements:**
- 100+ successful paper trades
- Positive average R multiple
- Documented drawdown
- Tested kill switch
- Validated risk limits
- Human approval flow working
- Separate live environment
- Operator explicit approval

---

## Customer-Facing Features

### Trade Transparency

- Real-time position display
- P&L tracking
- Trade history
- Performance metrics
- Risk metrics

### Customer Controls

- View all signals
- Approve/reject trades
- Modify trade parameters
- Set risk limits
- Activate kill switch
- View audit logs

### Reporting

- Daily trade summary
- Weekly performance report
- Monthly risk report
- Strategy performance
- Compliance report

---

## Technology Stack

### Backend
- Python for signal engine
- Node.js for broker connectors
- SQLite/PostgreSQL for data storage
- Redis for caching

### Frontend
- React for dashboard
- WebSocket for real-time updates
- Chart.js for visualizations

### APIs
- Kalshi REST API
- IBKR Client Portal API
- IBKR TWS API (advanced)

---

## File Structure

```
skills/trade/
├── TRADING-ASSISTANT-ARCHITECTURE.md
├── IBKR-INTEGRATION-RESEARCH.md
├── signal_engine/
│   ├── __init__.py
│   ├── market_data.py
│   ├── strategies.py
│   └── signal_generator.py
├── risk_manager/
│   ├── __init__.py
│   ├── risk_rules.py
│   ├── position_sizer.py
│   └── risk_validator.py
├── order_manager/
│   ├── __init__.py
│   ├── order_validator.py
│   ├── order_executor.py
│   └── position_tracker.py
├── brokers/
│   ├── kalshi_connector.py
│   ├── ibkr_connector.py
│   └── base_connector.py
├── dashboard/
│   ├── trading_dashboard.html
│   ├── signal_review.html
│   └── position_monitor.html
└── data/
    ├── paper_ledger.jsonl
    ├── positions.json
    └── signals.json
```

---

## Next Steps

1. Build IBKR API client
2. Implement signal engine
3. Implement risk manager
4. Build order manager
5. Create trading dashboard
6. Implement human approval flow
7. Test with paper trades
8. Document safety boundaries
9. Get operator approval for live testing
10. Deploy with hard safety limits

---

## Risk Gates Summary

| Gate | Status | Requirement |
|---|---|---|
| Paper Trading | Required | 100+ trades |
| Risk Validation | Required | All rules enforced |
| Human Approval | Required | Explicit approval |
| Kill Switch | Required | Tested and working |
| Audit Logging | Required | Complete trail |
| Live Environment | Required | Separate from paper |
| Operator Approval | Required | Explicit consent |
