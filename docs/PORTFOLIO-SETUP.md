# Portfolio Integration Setup

**Current Status:** System running with **demo/mock portfolio data**
**Target:** Connect to IBKR (Interactive Brokers) for **real portfolio**

---

## Current Demo Portfolio

The local system includes mock portfolio data to demonstrate the trading integration:

```json
{
  "account": {
    "equity": $247,500,
    "cash": $23,400,
    "pnl_today": $1,250,
    "pnl_pct": 0.51%
  },
  "positions": [],
  "signals": [
    { "symbol": "AAPL", "type": "BUY", "confidence": 82% },
    { "symbol": "TSLA", "type": "BUY", "confidence": 75% }
  ]
}
```

This data is served from `/api/positions` via the Trading Dashboard service (port 5050).

---

## To Get Real Portfolio Data

### Option 1: IBKR Gateway (Recommended)

1. **Download IBKR Gateway**
   - https://www.interactivebrokers.com/en/trading/ibkr-gateway
   - Install and launch locally

2. **Configure Credentials**
   - Launch IBKR Gateway on default port 4001
   - Log in with your IBKR username/password

3. **Set Environment Variables** in `.env` or `.env.local`:
   ```
   IBKR_HOST=127.0.0.1
   IBKR_PORT=4001
   ```

4. **Restart Lantern OS**
   ```bash
   npm run dev --prefix apps/lantern-garage
   ```

### Option 2: Demo Account (Paper Trading)

1. Open IBKR Gateway
2. Select "Paper Trading" account login
3. Same setup as Option 1

---

## How It Works

```
Chat: "Check my portfolio"
         ↓
Keystone Router detects "trading" context
         ↓
Trading API Bridge connects to IBKR Gateway (port 4001)
         ↓
Retrieves real account data + positions + signals
         ↓
Injects into chat context
         ↓
LLM responds with actual portfolio (via Keystone routing)
```

---

## Testing Portfolio Integration

### 1. Check Trading Service Status
```bash
curl http://127.0.0.1:5050/api/positions
```

Should return your actual portfolio when IBKR Gateway is running.

### 2. Test in Dream Chat
- Open http://127.0.0.1:4177/dream-chat.html
- Enable "Trading Context" in settings
- Ask: "What's my current portfolio?"
- Response should show real positions + P&L

### 3. Check Provider Attribution
Response metadata should show:
```json
{
  "agent": "Keystone",
  "provider": "gemini" (or selected provider),
  "trading_context": true
}
```

---

## Troubleshooting

### "Getting symbolic answers instead of real data"

**Cause:** IBKR Gateway not running on port 4001

**Fix:**
1. Verify IBKR Gateway is installed
2. Launch IBKR Gateway application
3. Check http://127.0.0.1:4001/status returns 200
4. Restart Lantern OS

### "Can't connect to IBKR"

**Cause:** Port 4001 is blocked or IBKR using different port

**Fix:**
1. Check IBKR Gateway settings for actual port
2. Update `IBKR_PORT` in `.env`
3. Restart Lantern OS

### "Getting paper trading data instead of live"

**Cause:** IBKR account set to paper/demo

**Fix:**
1. Open IBKR Gateway
2. Switch to live trading account
3. Log in with live credentials
4. Restart Lantern OS

---

## Live vs. Demo

| Feature | Demo (Mock) | Paper (IBKR) | Live (IBKR) |
|---------|------------|-------------|------------|
| Real positions | ❌ | ✅ | ✅ |
| Real P&L | ❌ | ✅ | ✅ |
| Trade execution | ❌ | Simulated | Real |
| Position history | ❌ | ✅ | ✅ |
| Market data | Demo | Real | Real |

---

## Current Implementation Files

- **Service:** `apps/lantern-garage/lib/trading-service.js`
- **API Bridge:** `apps/lantern-garage/lib/trading-api-bridge.js`
- **Routes:** `apps/lantern-garage/routes/trading.js`
- **Memory:** `apps/lantern-garage/lib/trading-memory.js`

---

## Next Steps

1. ✅ Trading integration wired (Keystone routing ready)
2. ⏳ Install IBKR Gateway (when ready for real data)
3. ⏳ Configure `.env` with IBKR credentials
4. ⏳ Test portfolio queries in Dream Chat

Until then, the demo portfolio data demonstrates the system architecture.
