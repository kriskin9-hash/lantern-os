### Added — Master ON/OFF button for the autonomous AI trader

The Keystone Stock Trader header (`stock-trader.html`) now has an **AI: ON/OFF** toggle (green/red
dot) that turns the autonomous trader on or off. Turning it OFF stops the trader from opening any
new positions; existing positions stay protected (end-of-day close + price-watcher stop-loss are
intentionally NOT gated, so OFF never strands open risk).

Cross-process by design: the button (node) writes a flag file
`data/lantern-garage/trading/ai-trader-enabled.json` via `GET/POST /api/trading/ai-trader/enabled`,
and the Python orchestrator reads it (`trading_enabled()`) before every order-placing job
(`job_scan_market`, `job_scan_crypto`, `job_watch_mode`, emergency scans). Missing file = ON, so the
default auto-trade behavior is unchanged. The button polls state every 30s and reflects it live.
</content>
