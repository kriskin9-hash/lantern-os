### Kalshi swipe deck: close the Σ₀ loop + a web-grounded position-taker

The Kalshi terminal was dead — the global trading-pause cleared every deck and swipe-take
no longer recorded anything, so the Observe→…→Converge loop was severed. Two changes bring
it back, paper-only, with the live kill-switch untouched.

**Loop closed + honest verdict.** `experiments/kalshi_council_train.py` replays the momentum
signal over the recorded tight-band history under a fee-aware EV gate, grades each trade vs
its real resolution, and feeds the shared Σ₀ council (`sigma0-trader-council.js`). The full
verdict is now shown prominently in the terminal: **NO PROVEN EDGE** — 68% gross win but
−$48/6209 trades net after fees; momentum can't beat the fee. New LIVE / PAPER / **REPLAY**
deck modes let you swipe recorded history (graded instantly vs the known outcome) or live
candidates (paper-only), each re-wired to the paper ledger + council. Also fixes a
pre-existing swipe bug (`attachSwipe` leaked `window` listeners each render, eating swipes).

**Grounded arm — the profitable direction.** Since momentum has no edge, a new grounded
trader chases the only durable one: information the thin market hasn't priced. It researches
near-term event markets (weather first — NWS-tied, ~1-day resolution, forecastable) via web
search + Gemini googleSearch grounding (routed through funded Vertex), estimates a
web-grounded `P(YES)` with cited sources, and takes a position only when that diverges from
the market price enough to clear the fee hurdle (`kalshi-fees` EV gate). A knowledge-only
estimate (no live sources) is capped and defers to the market — the External-Reality rule in
code. The new "🔎 Grounded" mode shows P(YES) vs market, the edge, rationale, and live source
links; swipe-take logs a paper pick that `groundedSync` Brier-grades into the council on
resolution. Profitability is measured **forward**, not asserted.

New: `lib/kalshi-council.js`, `lib/kalshi-grounding.js`, `lib/kalshi-event-suggester.js`,
paper-only routes (`replay-deck`, `paper-deck`, `grounded-deck`, `ground`, `grounded-sync`,
`council`). Tests: `test/kalshi-grounded.test.js` (11) + `tests/test_kalshi_council_train.py`
(6). Live kill-switch (`TRADING-PAUSED`, `LIVE-KILL-SWITCH`) stays engaged throughout.
