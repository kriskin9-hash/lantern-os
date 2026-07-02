---
author: Alex Place
created: 2026-07-02
---

# AI Trader — per-account locking + multi-tenancy review (Σ₀)

**Loop stage:** Act (safe execution) + Verify (grounded review).
**Question:** (1) make each Alpaca account run on only one server at a time; (2) could a
*different* user with a *different* account run this, and what would they need?

Every claim below carries **[evidence · confidence · source]** per the External Reality Rule.

## Part 1 — "one account, one server" (implemented)

`scripts/start-ai-trader.js` now takes a **per-account run lock** before spawning:

- The lock file is `os.tmpdir()/lantern-ai-trader-<sha256(ALPACA_API_KEY)[:12]>.lock`. **Same
  account → same lock → only one server runs it; different accounts → different locks → they
  run concurrently.** *(evidence: functional test — same-account 2nd acquire refused, different
  account acquired its own lock, stale/dead-owner lock taken over; confidence: high; source:
  this change + test run.)*
- Acquisition is atomic (`fs.openSync(path, 'wx')`). A held lock whose owner PID is **alive**
  (`process.kill(pid, 0)`) refuses the spawn; a **stale** lock (dead owner) is reclaimed. The
  lock is released on manager exit (`process.on('exit')`); a `SIGKILL` leaves a stale lock the
  next start reclaims. *(high; source: code.)*
- The earlier machine-wide health-port guard (skip if a trader is already healthy on :5555) is
  kept as a secondary check. *(high; source: code.)*

The API key never appears in the filename — only its SHA-256 prefix. *(high; source: code.)*

### Honest limit of the lock
The lock coordinates **servers on one machine** (the real bug: dual-boot :4177 + :4178 +
autostart all hit the same account). It is a local file, so it does **not** coordinate across
**different machines** — two boxes with the same API key can't see each other's lock. True
cross-host mutual exclusion would need a shared store (Alpaca offers no such lock). For the
actual deployment (one box, several servers) the file lock is correct and sufficient. *(high.)*

## Part 2 — could a different user with a different account run it? **Mostly no — it's single-tenant.**

Findings, most load-bearing first:

- **The trading engine isn't in this repo.** `start-ai-trader.js` shells out to
  `AI_TRADER_PATH` (default `C:\Independant AI Trader`) — a **separate, unshipped** project.
  lanternOS contains only the *manager/monitor*, not `main.py`/`agents.py`. A new user does not
  get the trader by cloning lanternOS. *(confidence: high; source: `scripts/start-ai-trader.js:11`;
  the engine lives outside the repo.)*
- **Credentials are one global set per box, read at import.** `main.py:78` and `agents.py:33`
  call `os.getenv("ALPACA_API_KEY"/"ALPACA_SECRET_KEY")` once at module load. One process = one
  account; there is **no per-user account store** wired into the trader. *(high; source: those
  lines.)*
- **It also needs two more paid keys.** `agents.py` builds a Claude + Grok council:
  `ANTHROPIC_API_KEY` and `XAI_API_KEY` are required for the trade decisions. *(high; source:
  `agents.py:22,31`.)*
- **Hardwired to PAPER, single port.** The Alpaca base URL is
  `https://paper-api.alpaca.markets` (`main.py:80`) and the health/flask server is a single
  port (`AI_TRADER_PORT`, default **5555**). So today it trades **paper money**, and only one
  trader can bind the box's :5555 — two *different* accounts can't co-run on one machine even
  with the per-account lock. *(high; source: `main.py:80`, flask import, port default.)*
- **Windows-shaped defaults.** Hardcoded `C:\...` path, a `venv`, Python deps. Portable only by
  overriding `AI_TRADER_PATH`. *(medium-high; source: repo layout.)*

### What a new user would actually need
1. Obtain the **`Independant AI Trader`** engine repo (not in lanternOS) and place it at
   `C:\Independant AI Trader` or set `AI_TRADER_PATH` to its location.
2. Python env from that repo's `requirements.txt` (`alpaca_trade_api`, `apscheduler`, `flask`,
   `pytz`, `anthropic`, `openai`, …).
3. A `.env` with **their own** `ALPACA_API_KEY` + `ALPACA_SECRET_KEY`, plus `ANTHROPIC_API_KEY`
   and `XAI_API_KEY`.
4. Run one server; the per-account lock keeps it to one instance. On a **different box** they're
   fully independent; on the **same box** as another user they'd collide on :5555 (would need a
   per-account `AI_TRADER_PORT`).

**Verdict:** as built this is a **single-tenant, single-operator, paper-trading personal
system**, not a multi-user product. A different user *can* run their own copy on their own box
with their own keys, but there is **no built-in multi-account or multi-user path** — no account
store, one global credential set, one hardcoded engine path, one health port.

### If we wanted real multi-tenancy (follow-up, not done)
- Parameterize `AI_TRADER_PORT` per account (drop the single-:5555 assumption) so >1 account can
  co-run on a box.
- Source credentials per-account from a store (there is a `routes/financial-keys.js` /
  `api-keys-settings.html` surface in lanternOS that is **not** currently wired into this
  external trader) instead of one global env set.
- Ship or vendor the engine so it isn't an out-of-repo `C:\` dependency.

## Related
- `scripts/start-ai-trader.js` — the manager + per-account lock (this change)
- `apps/lantern-garage/server-dev.js` — dev boot defaults `LANTERN_DISABLE_TRADING=1`
- `changelog.d/ai-trader-singleton-guard.md` — the churn incident this hardens
</content>
