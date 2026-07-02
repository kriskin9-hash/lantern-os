### Fixed — AI trader ran as 3 duplicate instances, churning the Alpaca account

The AI trader is a singleton service (health server on :5555), but nothing enforced that:
both dual-boot servers (stable :4177 + dev :4178) and autostart each spawned their own
`python main.py` via `start-ai-trader.js`. Multiple trading loops on the **same Alpaca
account** placed opposing orders and churned it to death on market-order spread + fees —
observed 2026-07-02 as rapid BUY→SELL round-trips (AAPL flipped in 3–7s) and a negative day
P&L with ~$0 realized edge.

Fix:
- **Per-account run lock** (`scripts/start-ai-trader.js`): before spawning, the manager takes
  an atomic lock keyed on `sha256(ALPACA_API_KEY)` in the OS temp dir. The **same account**
  can only run on **one server at a time** (a second server is refused); **different accounts**
  hash to different locks and may run concurrently. A live owner blocks; a stale (dead-owner)
  lock is reclaimed; the lock releases on exit. The machine-wide health-port check (skip if a
  trader is already healthy on :5555) is kept as a secondary guard.
- **Dev never trades** (`apps/lantern-garage/server-dev.js`): the :4178 dev boot defaults
  `LANTERN_DISABLE_TRADING=1`, so only stable :4177 owns the real-money trader. Opt back in
  explicitly with `LANTERN_DISABLE_TRADING=0` (e.g. a paper account).

Live remediation: collapsed the 3 running instances to 1 (single scheduler confirmed in the
trader log). Existing positions were left untouched — no forced liquidation.
</content>
