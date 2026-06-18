# Interactive Trader App Integration Analysis

**Date:** 2026-06-12  
**Source:** `C:\Users\alexp\Downloads\ai trader.zip`  
**Target:** `lantern-os` (alex-place/lantern-os, master branch)  
**Branch:** `integrate-interactive-trader`

---

## Executive Summary

The AI Trader application is a **Python-based autonomous trading system** that:
- Connects to Alpaca API for paper/live trading
- Exposes REST APIs on multiple ports (5000, 5001, 5555)
- Provides Flask dashboards with real-time market data and news
- Sends alerts via Telegram bot
- Manages positions, signals, and portfolio metrics

**No `trading.html` file exists.** The app uses server-side HTML templates (`render_template_string`).

---

## Architecture Analysis

### Core Components

| Component | File | Purpose | Port | Status |
|-----------|------|---------|------|--------|
| **Main Entry** | `main.py` | Orchestrates trading logic, Alpaca connection, alerts | 5001 | Active |
| **Trading Logic** | `agents.py` | Pattern recognition, signal generation, zone analysis | — | Core logic |
| **REST API** | `src/ai_trader_api.py` | Flask endpoints for status, positions, watchlist, signals, zones | 5555 | Ready |
| **Dashboard** | `dashboard.py` | Flask web UI with charts, news feed, market status | 5000 | Ready |
| **Telegram Bot** | `telegram_bot.py` | Command interface + alerts | — | Configured |
| **Price Watcher** | `price_watcher.py` | Real-time price monitoring | — | Utility |

### Key Files & Dependencies

```
ai trader/
├── .env                          # Alpaca API keys, Telegram token
├── .git                          # Git repository
├── main.py                       # Entry point (orchestration)
├── agents.py                     # Core trading logic (~400KB, complex)
├── dashboard.py                  # Flask UI server (~58KB)
├── src/
│   └── ai_trader_api.py         # REST API factory
├── telegram_bot.py              # Telegram integration (~43KB)
├── price_watcher.py             # Real-time price updates
├── launcher.py                  # Startup helper
├── backtest_today.py            # Backtesting utility
└── [data files: lessons.db, trading.log, etc.]
```

### External Dependencies

**Python packages:**
- `alpaca-trade-api` — Trading platform
- `flask` — Web servers
- `pytz` — Timezone handling
- `apscheduler` — Job scheduling
- `python-telegram-bot` — Telegram integration
- `requests` — HTTP client

**API Integrations:**
- **Alpaca Trading API** — Market data, order execution
- **Telegram Bot API** — Notifications

---

## API Specification

### REST Endpoints (Port 5555 / 5001)

**Health & Status:**
- `GET /health` — System heartbeat
- `GET /api/status` — Market open, equity, positions count, paused flag

**Trading Data:**
- `GET /api/positions` — Open positions with P&L
- `GET /api/watchlist` — Monitored tickers
- `GET /api/signals?limit=10` — Recent trading signals
- `GET /api/zones` — Market analysis per ticker

**Dashboard (Port 5000):**
- `GET /` — Main dashboard
- `GET /news` — News feed page
- `GET /api/bars/<ticker>[/<tf>]` — OHLCV data (1m, 5m, 15m, 1h, 4h, 1d)
- `GET /api/market-status` — VIX, SPY trend, drawdown, market hours
- `GET /api/watchlist-prices` — Live prices for all tickers
- `GET /api/agent-log` — Agent activity log
- `GET /api/news-feed` — Aggregated news articles

### Data Models

**Position:**
```json
{
  "symbol": "AAPL",
  "qty": 10,
  "avg_entry_price": 175.50,
  "current_price": 178.20,
  "pnl_pct": 1.54,
  "stop": null,
  "tp": null
}
```

**Signal:**
```json
{
  "symbol": "TSLA",
  "action": "BUY|SELL|HOLD",
  "reason": "RSI oversold with MACD crossover",
  "confidence": 0.87,
  "timestamp": "2026-06-12T14:32:15Z"
}
```

**Zone (Market Analysis):**
```json
{
  "AAPL": {
    "support": 175.00,
    "resistance": 182.00,
    "trend": "BULLISH",
    "volatility": "NORMAL"
  }
}
```

---

## Lantern OS Integration Strategy

### Option 1: **Native Bounded Module** (Recommended)

Create `apps/lantern-garage/services/ai-trader/` as a bounded service:

```
apps/lantern-garage/services/ai-trader/
├── README.md                    # Integration guide
├── trader-api.js               # Node.js wrapper for Python REST API
├── trader-dashboard.html       # Web UI (ported/embedded)
├── public/
│   ├── js/
│   │   ├── trader-ui.js       # Interactive UI logic
│   │   └── indicators.js      # Chart calculations
│   └── css/
│       └── trader-ui.css      # Styling
├── server.js                   # Optional: local Flask proxy
└── [symlink to Python trader or API-only mode]
```

**Advantages:**
- ✅ Minimal coupling to main lantern-garage
- ✅ Trader runs as separate process, Lantern calls its APIs
- ✅ Can be toggled on/off via environment variables
- ✅ Easy to fork/maintain independently
- ✅ Respects existing dual-boot system (4177/4178)

**Integration Points:**
1. Lantern navbar adds "Trader" link → `/trader-dashboard.html`
2. Lantern server proxies `/api/trader/*` → Python Flask (port 5001)
3. Optional: Trader sends alerts to Lantern via webhook

### Option 2: **Full Python Migration**

Migrate entire trading logic into `src/` with Node.js wrapper:
- More complex, breaks existing architecture
- Good only if you plan to unify Lantern + Trader as one platform

---

## Implementation Plan

### Phase 1: Assessment (✓ Complete)
- [x] Scan `trading.html` (doesn't exist — use dashboard.py instead)
- [x] Identify dependencies (Alpaca API, Flask)
- [x] Map API endpoints (documented above)
- [x] Understand data models

### Phase 2: Preparation
- [ ] Copy Python trader code to temporary holding area
- [ ] Create Node.js API wrapper (`trader-api.js`)
- [ ] Identify which HTML/CSS/JS from `dashboard.py` to reuse
- [ ] Test Python trader in isolation
- [ ] Verify Alpaca credentials work

### Phase 3: Integration
- [ ] Create bounded module structure
- [ ] Build HTML UI (extract from dashboard.py or rebuild)
- [ ] Wire up REST endpoints
- [ ] Add navbar link in `lantern-garage`
- [ ] Test API proxying
- [ ] Document environment setup (.env variables)

### Phase 4: Testing
- [ ] Smoke test dashboard loads
- [ ] Verify API endpoints respond
- [ ] Check real-time data updates
- [ ] Test Alpaca connection
- [ ] Verify no port conflicts with dual-boot

### Phase 5: Documentation
- [ ] Integration README
- [ ] Setup guide (Alpaca keys, .env)
- [ ] API reference
- [ ] Troubleshooting guide

---

## Critical Decisions Needed

### 1. **Where should trader Python code live?**

**Option A:** `services/ai-trader/` (as separate subprocess)
- Pros: Clean isolation, easy to manage independently
- Cons: Requires process management

**Option B:** `src/` alongside existing Python (MCP, Discord bot)
- Pros: Unified Python environment
- Cons: Blurs service boundaries

**Recommended:** Option A (bounded service)

### 2. **Should we use Alpaca API keys from .env?**

**Yes.**  Copy from AI Trader's `.env`:
```
ALPACA_API_KEY=...
ALPACA_SECRET_KEY=...
TRADER_ENABLED=true  # Feature flag
```

### 3. **Should trader alerts go to Lantern?**

**Optional.** Could wire Telegram alerts into Lantern's notification system.  
Status: Out of scope for MVP integration.

### 4. **Port management?**

- 4177: Lantern (stable)
- 4178: Lantern (dev)
- 5000: Trader dashboard (optional if proxied)
- 5001: Trader main process
- 5555: Trader REST API

**Recommendation:** Proxy `/api/trader/*` through Lantern (4177) → Trader API (5555).

---

## File Structure Draft

```
lantern-os/
├── apps/lantern-garage/
│   ├── public/
│   │   ├── trader-dashboard.html    # NEW
│   │   └── css/
│   │       └── trader-ui.css        # NEW
│   └── lib/
│       └── trader-api.js            # NEW (REST client)
├── services/
│   └── ai-trader/                   # NEW
│       ├── README.md
│       ├── main.py                  # (copy from source)
│       ├── agents.py                # (copy from source)
│       ├── dashboard.py             # (copy from source)
│       ├── src/
│       │   └── ai_trader_api.py    # (copy from source)
│       └── .env.example
└── docs/
    └── TRADER-INTEGRATION.md        # This file
```

---

## Next Steps

1. **Clarify integration scope** with user:
   - Full trader in Lantern? Or just UI + API proxy?
   - Python subprocess or embedded?
   - Alerts → Telegram only or also Lantern?

2. **Create environment setup**:
   - Alpaca sandbox credentials
   - .env template

3. **Build Node.js API wrapper**:
   - REST client for Python trader endpoints
   - Port proxy logic
   - Error handling

4. **Port HTML/CSS from dashboard.py**:
   - Extract inline HTML template
   - Create separate `.html` file
   - Adapt chart/data update logic

5. **Wire Lantern navbar**:
   - Add Trader link
   - Style to match existing nav

---

## Files to Copy (if integration approved)

From `C:\Users\alexp\Downloads\ai-trader-new\ai trader\`:

```
main.py                    → services/ai-trader/main.py
agents.py                  → services/ai-trader/agents.py
dashboard.py               → services/ai-trader/dashboard.py
src/ai_trader_api.py       → services/ai-trader/src/ai_trader_api.py
telegram_bot.py            → services/ai-trader/telegram_bot.py
price_watcher.py           → services/ai-trader/price_watcher.py
launcher.py                → services/ai-trader/launcher.py
.env                        → services/ai-trader/.env.example (sanitized)
requirements.txt            → services/ai-trader/requirements.txt
```

---

## Open Questions

1. **Should we run trader alongside Lantern or separately?**
   - Separate = easier to manage, respects Lantern's architecture
   - Alongside = more integrated, shared Python env

2. **Do we expose _all_ trader endpoints or a subset?**
   - Recommend: positions, signals, market-status, watchlist-prices
   - Skip: internal admin endpoints

3. **Should trader data persist in Lantern's data models?**
   - Or stay in trader's isolated state?

4. **Telegram alerts:** Keep as-is, or integrate into Lantern's notification system?

---

## Timeline Estimate

| Phase | Effort | Days |
|-------|--------|------|
| Setup + testing (Phase 2) | 1-2h | 0.5 |
| Core integration (Phase 3) | 3-4h | 1-2 |
| Testing + docs (Phase 4-5) | 2-3h | 1 |
| **Total** | **6-9h** | **2-3** |

---

## Appendix: Source Code Summary

### main.py
- ~650 lines
- Entry point, orchestrates Alpaca connection, scheduling, Telegram commands
- Key state: `_shared_state`, `_position_adjustments`, circuit breaker logic

### agents.py
- ~400KB (very large!)
- Core trading logic: pattern recognition, zone detection, signal generation
- Key functions: `scan_all()`, `agent_log()`, `get_portfolio_equity()`

### dashboard.py
- ~1800 lines of Flask + HTML template
- Routes for data endpoints + web UI
- Inline CSS/JS (~1500 lines of template HTML)

### ai_trader_api.py
- ~200 lines
- Flask factory for REST API
- Endpoints: /health, /api/status, /api/positions, /api/signals, /api/zones, /api/watchlist

---

**Status:** Ready for Phase 2 — awaiting user confirmation on integration approach.
