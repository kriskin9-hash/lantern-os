# Trading Spreads & Choices — Quick Reference

**Date:** 2026-05-31 10:15 UTC-04:00  
**Mode:** Paper Only  
**Total Allocated:** $4.07 (Kalshi) + $0 (IBKR)  

---

## Kalshi Positions (8 Paper Trades)

| # | Market | Entry | Spread | Risk | Profit Range | Close |
|---|--------|------:|-------:|-----:|-------------:|------:|
| 1 | Boston Temp 56-57°F | 22¢ | 1¢ | $0.22 | -$0.23 to +$0.77 | May 31 |
| 2 | Yankees vs A's Runs | 50¢ | 1¢ | $0.50 | -$0.51 to +$0.49 | Jun 03 |
| 3 | Gas > $4.290 | 97¢ | 1¢ | $0.97 | -$0.98 to +$0.02 | Jun 01 |
| 4 | Top Spotify Song ⚠️ | 96¢ | 1¢ | $0.96 | -$0.97 to +$0.03 | **May 30** |
| 5 | Atlanta +1.5 Runs | 44¢ | 1¢ | $0.44 | -$0.45 to +$0.55 | Jun 02 |
| 6 | Seattle Temp 64-65°F | 24¢ | 1¢ | $0.23 | -$0.24 to +$0.76 | May 31 |
| 7 | Atlanta Temp >85°F | 31¢ | 1¢ | $0.31 | -$0.32 to +$0.68 | May 31 |
| 8 | Trump Approval >39.3% | 44¢ | 1¢ | $0.44 | -$0.45 to +$0.55 | Jun 05 |

**Key:** ⚠️ = Market expired (May 30), position needs settlement review

---

## Spread Analysis

| Metric | Value |
|--------|------:|
| **Average Spread** | 1¢ (1% of contract) |
| **Total Risk Allocated** | $4.07 |
| **Remaining Budget** | $0.93 (of $5 daily limit) |
| **Average Ticket Size** | 51¢ |
| **Contracts Count** | 8 |

---

## IBKR Demo Trade

| Field | Value |
|-------|------:|
| Symbol | AAPL |
| Side | BUY |
| Quantity | 50 shares |
| Entry | $150.25 |
| Exit Target | $150.75 |
| Spread | 50bps |
| Est. P&L | +$25.00 |
| Status | DEMO (not live) |
| Mode | Paper |

---

## Live Trading Status

| System | Status | Gate |
|--------|--------|------|
| IBKR Autonomous | 🟡 Paper (armed) | Needs operator ENTER |
| Kalshi Live | 🔴 Blocked | Pre-v1.0.0 + 6 blockers |
| **Real Money Deployed** | **$0.00** | — |

---

## Next Decision Points

1. **Position #4 (Spotify)** — Expired May 30, needs settlement review
2. **Weather positions (#1, #6, #7)** — Close May 31, review outcomes
3. **IBKR paper trade** — Press ENTER to execute next demo
4. **Live promotion** — Remove kill-switch (requires explicit operator action)

---

**Status:** All systems operational, paper-only mode, zero live exposure
