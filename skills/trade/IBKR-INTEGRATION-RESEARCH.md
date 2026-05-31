# Interactive Brokers (IBKR) Integration Research

**Date:** 2026-05-30  
**Purpose:** Research IBKR API capabilities for Lantern OS trading assistant  
**Status:** Research phase

---

## Simple Answer

Interactive Brokers provides multiple API options for programmatic trading:
- **IBKR API (TWS/Gateway)** - Desktop-based API via Trader Workstation or IB Gateway
- **IBKR Client Portal API** - REST API for account data and basic orders
- **IBKR Pro API** - Advanced API with market data and complex orders

---

## API Options Comparison

| API | Type | Use Case | Pros | Cons |
|---|---|---|---|---|
| TWS API | Socket/Java | Desktop automation | Full feature set | Requires TWS running |
| IB Gateway | Socket/Java | Server deployment | No GUI needed | Separate installation |
| Client Portal | REST | Simple web integration | Easy to use | Limited features |
| Pro API | REST/WebSocket | Advanced trading | Real-time data | Higher cost |

---

## Recommended Approach for Lantern

**Phase 1 (Paper Trading):**
- Use IBKR Paper Trading Account
- Client Portal API for simple orders
- TWS API for advanced features if needed

**Phase 2 (Live Trading):**
- IB Gateway for server deployment
- Full TWS API for complex strategies
- Separate paper/live environments

---

## Key Endpoints (Client Portal API)

### Authentication
- POST `/oauth/token` - OAuth token exchange
- Requires API key and secret

### Account Data
- GET `/iserver/accounts` - List accounts
- GET `/portfolio/accounts` - Account summary
- GET `/portfolio/{accountId}/positions` - Current positions
- GET `/portfolio/{accountId}/summary` - Account balances

### Orders
- POST `/iserver/account/{accountId}/order` - Place order
- GET `/iserver/account/{accountId}/orders` - List orders
- DELETE `/iserver/account/{accountId}/order/{orderId}` - Cancel order
- POST `/iserver/account/{accountId}/order/{orderId}` - Modify order

### Market Data
- GET `/iserver/marketdata/snapshot` - Market snapshot
- GET `/iserver/marketdata/history` - Historical data

---

## Order Types Supported

- Market Orders
- Limit Orders
- Stop Orders
- Stop-Limit Orders
- Trailing Stop Orders
- Bracket Orders (OCA - One-Cancels-All)

---

## Safety Features Required

1. **Paper Trading Mode** - Must use paper account initially
2. **Order Validation** - Validate order parameters before submission
3. **Position Limits** - Enforce max position size
4. **Daily Loss Limits** - Stop trading after daily loss threshold
5. **Kill Switch** - Emergency stop all orders
6. **Human Approval** - Require explicit approval for live orders
7. **Audit Logging** - Log all order attempts and executions

---

## Integration Architecture

```
Lantern Trading Assistant
├── Trade Signal Generator
│   ├── Market Data Agent
│   ├── Signal Agent
│   └── Risk Agent
├── Order Manager
│   ├── Order Validator
│   ├── Position Manager
│   └── Risk Manager
├── Broker Connectors
│   ├── Kalshi Connector (existing)
│   └── IBKR Connector (new)
└── Human Interface
    ├── Trade Dashboard
    ├── Approval Flow
    └── Report Generator
```

---

## Next Steps

1. Set up IBKR Paper Trading Account
2. Generate API keys for Client Portal API
3. Build IBKR API client module
4. Implement order validation logic
5. Create unified trading dashboard
6. Add human approval workflow
7. Test with paper trades only
8. Document safety boundaries

---

## Risk Gates

Before any live trading:

1. ✅ 100+ successful paper trades
2. ✅ Order validation tested
3. ✅ Risk limits enforced
4. ✅ Kill switch tested
5. ✅ Human approval flow working
6. ✅ Audit logging complete
7. ✅ Separate paper/live environments
8. ✅ Operator explicit approval

---

## References

- IBKR API Documentation: https://www.interactivebrokers.com/en/trading/ib-api-student-trading-package.php
- Client Portal API: https://www.interactivebrokers.com/en/trading/ib-api-student-trading-package.php
- Paper Trading: https://www.interactivebrokers.com/en/trading/paper-trading.php
