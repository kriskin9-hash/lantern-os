### Changed — AI trader now runs fully internally (no external engine)

The autonomous trader previously ran from an out-of-repo project (`C:\Independant AI Trader`)
that `start-ai-trader.js` shelled out to. Worse, a near-duplicate engine already lived in-repo
at `src/trading_agents/` (driven on-demand by `trader-agent.js`), so **two** systems traded the
same paper Alpaca account and churned it (5 concurrent loops observed 2026-07-02).

The trader is now **entirely in-repo**:

- **New orchestrator** — `src/trading_agents/orchestrator.py` ports the external `main.py`
  scheduler loop (scan / EOD / crypto-timeout / watch-mode / portfolio jobs) onto the internal
  `agents.py` brain (every imported symbol — `scan_all`, `close_position`, `get_open_positions`,
  `is_market_hours`, … — already existed internally). Telegram (`telegram_bot.py`) is optional
  (no-op if absent/misconfigured); the :5555 health/status API is ported to `trader_api.py`.
  Loads the repo `.env` before importing agents so it runs standalone too.
- **Manager rewired** — `start-ai-trader.js` launches `python orchestrator.py` from
  `src/trading_agents` (via `AI_TRADER_PATH`/`AI_TRADER_ENTRY`, `PYTHONPATH` set); the
  `C:\Independant AI Trader` default is gone. The per-account singleton lock + dev-no-trade
  guard still apply.
- **Scans single-flighted** — `trader-agent.js scanMarket()` now collapses concurrent callers
  onto one in-flight `scan_market` subprocess (dual-boot + dashboard polling previously spawned
  4+ at once).
- **Finance news internalized** — `/api/trading/dashboard/news-feed` is served from the local
  CSF news registry (keyless Yahoo RSS collector) instead of proxying to the retired external
  dashboard (:5050), so the finance news works with the trader fully internal.

No external `C:\` trading dependency remains in the live path.
</content>
