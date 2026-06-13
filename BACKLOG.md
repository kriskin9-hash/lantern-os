# Trading Integration Backlog

## Phase 2: Dream Chat Integration & Data Persistence

### High Priority

#### [P1] Dream Chat Trading Agent Persona
- **Description**: Add "trading" agent persona to dream-chat.js that responds to market/trading keywords
- **Acceptance Criteria**:
  - User can type "What's the status of AAPL?" and trading agent responds
  - Agent queries `/api/trading/ai-trader/zones` + `/api/trading/ai-trader/signals`
  - Agent interprets commands like "close BTCUSD position"
  - Responses are formatted as markdown with suggestions
- **Effort**: Medium (2-3 hours)
- **Blocks**: Dream chat trading workflow

#### [P2] Fix Trading API Routes 404 Error
- **Description**: Routes are defined but returning 404 "not_found" instead of data
- **Current Behavior**: 
  - `/api/trading/ai-trader/watchlist` → 404
  - `/api/trading/ai-trader/zones` → 404
  - `/api/trading/ai-trader/status` → 404
- **Root Cause**: Unknown - routes are syntactically correct, likely a routing logic issue
- **Acceptance Criteria**:
  - All trading API endpoints return 200 with valid JSON
  - Bridge receives real data from AI Trader
  - Dashboard shows actual portfolio data
- **Effort**: High (3-4 hours)
- **Blocks**: All dashboard functionality

#### [P3] Trade History Persistence
- **Description**: Log all trades to JSONL for audit trail and historical analysis
- **Files to Create**:
  - `data/trading/trades.jsonl` - One trade per line (entry_timestamp, symbol, side, entry_price, exit_price, pnl, confidence)
  - `data/trading/signals.jsonl` - All generated signals (agent, ticker, direction, confidence, reasoning)
- **Acceptance Criteria**:
  - Each executed trade logged immediately
  - Each signal logged when generated
  - Dream chat can reference "what happened in trading"
- **Effort**: Low (2 hours)

### Medium Priority

#### [P4] Enhanced Trading Dashboard UI
- **Description**: Add CSS styling to match Lantern theme, improve visual hierarchy
- **Current State**: Basic HTML with inline styles
- **Improvements**:
  - Dark mode support (matches Lantern's mandala aesthetic)
  - Responsive grid layout for positions
  - Color-coded P&L (green/red gains/losses)
  - Animated refresh indicator
  - Market-open/closed status visual
- **Acceptance Criteria**:
  - Dashboard matches Lantern OS design language
  - Fully responsive on mobile/tablet
  - Accessible (WCAG AA)
- **Effort**: Medium (3-4 hours)

#### [P5] Alerts & Notifications System
- **Description**: Surface critical trading events to user
- **Features**:
  - Large position P&L changes (>5%)
  - Stop loss hits
  - Take profit reaches
  - API Trader service down/reconnected
  - High-confidence signals (>85%)
- **Acceptance Criteria**:
  - Alerts appear in trading panel with timestamp
  - Can clear/dismiss alerts
  - Optional email/Telegram notifications
- **Effort**: Medium (3 hours)

#### [P6] Real-time Position Monitor
- **Description**: Show live position updates without manual refresh
- **Current**: Auto-refresh every 5 seconds
- **Improve**: 
  - Use WebSocket or SSE for real-time updates
  - Highlight positions that moved in last update
  - Show entry → current price animation
- **Effort**: Medium (3-4 hours)

### Lower Priority

#### [P7] Trading Statistics Dashboard
- **Description**: Show trading performance metrics
- **Metrics**:
  - Win rate (% profitable trades)
  - Average win/loss
  - Largest win/loss
  - Sharpe ratio
  - Max drawdown
  - Days in market vs. on sidelines
- **Effort**: Low-Medium (2-3 hours)

#### [P8] Backtesting Integration
- **Description**: Allow users to test strategies on historical data
- **Features**:
  - Load past 30/60/90 days of data
  - Simulate trading with same AI agents
  - Compare: what would have happened vs. what did happen
- **Effort**: High (5-6 hours)

#### [P9] Multi-Account Support
- **Description**: Trade multiple Alpaca accounts simultaneously
- **Current**: Single account hardcoded
- **Improve**:
  - Select account from dropdown
  - Monitor P&L across accounts
  - Route signals to specific accounts
- **Effort**: Medium (3-4 hours)

#### [P10] Portfolio Rebalancing
- **Description**: Auto-rebalance portfolio to target allocations
- **Features**:
  - Define target weights (e.g., 40% BTC, 30% ETH, 30% cash)
  - Auto-execute rebalancing on threshold (e.g., 5% drift)
  - Show suggested trades before execution
- **Effort**: Medium-High (4-5 hours)

---

## Phase 3: Advanced Features

### High Priority

#### [P11] Risk Management Enhancements
- **Description**: Improve position sizing and risk controls
- **Features**:
  - Portfolio-level stop loss (max daily loss)
  - Per-position Kelly Criterion sizing
  - Correlation-aware position sizing
  - Sector concentration limits
- **Effort**: High (5-6 hours)

#### [P12] Multi-Broker Support
- **Description**: Support Interactive Brokers, Kraken, Coinbase in addition to Alpaca
- **Current**: Alpaca only
- **Effort**: Very High (10+ hours)

### Medium Priority

#### [P13] Machine Learning Signal Fusion
- **Description**: Combine signals from multiple agents with ML weighting
- **Current**: Simple agent routing
- **Improve**:
  - Weight agents by historical accuracy
  - Ensemble predictions with confidence intervals
  - Learn optimal signal combinations
- **Effort**: High (6-8 hours)

#### [P14] Voice Control
- **Description**: Control trading via voice commands
- **Features**:
  - "Pause trading"
  - "Close BTCUSD"
  - "What's my equity?"
  - "Show recent signals"
- **Effort**: Medium (3-4 hours)

---

## Known Issues & Bugs

### Critical

- **[BUG-001]** Trading API routes return 404 instead of data
  - Status: OPEN
  - Severity: Critical
  - Impact: Dashboard shows no real data
  - Priority: P2

### High

- **[BUG-002]** AI Trader process may not start if Python path is wrong
  - Status: OPEN
  - Severity: High
  - Workaround: Manually start AI Trader
  - Fix: Better error handling in start-ai-trader.js

- **[BUG-003]** No fallback when Alpaca API is down
  - Status: OPEN
  - Severity: High
  - Impact: Trading halts completely
  - Fix: Implement circuit breaker pattern

### Medium

- **[BUG-004]** Dashboard shows $0 equity on initial load
  - Status: OPEN
  - Severity: Medium
  - Cause: Async data loading race condition
  - Fix: Loading spinner + retry logic

- **[BUG-005]** Console errors for missing CSS/styling
  - Status: OPEN
  - Severity: Low
  - Cause: Basic component styling
  - Fix: Add proper CSS file

---

## Technical Debt

### High Priority

- [ ] Extract trading component to separate npm package
- [ ] Add TypeScript types for trading data structures
- [ ] Implement proper error boundary for trading panel
- [ ] Add unit tests for TradingAPIBridge
- [ ] Extract hardcoded values to config

### Medium Priority

- [ ] Refactor trading.js routes (too many if statements)
- [ ] Add JSDoc comments to JavaScript modules
- [ ] Create trading API OpenAPI/Swagger spec
- [ ] Add performance monitoring for API calls
- [ ] Implement caching strategy for market data

### Low Priority

- [ ] Add storybook stories for trading components
- [ ] Create design tokens for trading panel colors
- [ ] Add accessibility labels to all trading controls
- [ ] Implement analytics for trading feature usage

---

## Dependencies & Blockers

### Blocked By

1. **[BUG-001]** - Must fix 404 error before most features can be tested
2. **Alpaca API keys** - Need user to configure for real data

### Blocking

1. **Dream Chat Integration** - Blocked by fixing BUG-001
2. **Real-time Updates** - Blocked by fixing API routes
3. **Performance optimization** - Blocked by having real data flowing

---

## Estimated Timeline

| Phase | Features | Effort | Timeline |
|-------|----------|--------|----------|
| Phase 1 | Core integration | 40 hrs | ✅ Complete |
| Phase 2 | Dream Chat + UI | 15-20 hrs | 3-4 days |
| Phase 3 | Advanced features | 30-40 hrs | 1-2 weeks |
| Phase 4 | Multi-broker + ML | 60+ hrs | 4+ weeks |

---

## Success Metrics

- [ ] All 10 trading API endpoints return 200 with real data
- [ ] Dashboard shows live Alpaca portfolio data
- [ ] Trading agent persona responds to market queries
- [ ] Trade history persists to disk
- [ ] UI matches Lantern aesthetic
- [ ] Zero console errors or warnings
- [ ] 90%+ test coverage for trading logic
- [ ] <500ms latency for API calls
- [ ] Handles Alpaca API downtime gracefully

---

Last Updated: 2026-06-11
Created By: Claude Integration Phase 1
