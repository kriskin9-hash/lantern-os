# Harsanyi Type Space Model for Lantern OS Cloud Agent and Trading Fleet

**Status**: Draft — operator review required  
**Scope**: Cloud runtime, Kalshi connector, IBKR autonomous executor, MCP audit layer  
**Source**: Harsanyi (1967–1968), Mertens & Zamir (1985), Aumann (1976)  
**Repo paths**: `skills/trade/`, `apps/lantern-garage/`, `docs/KALSHI-LIVE-TRADING.md`  

---

## Simple Answer

Lantern OS can be modeled as a Harsanyi type space where each agent (human operator, Kalshi trader, IBKR executor, cloud mirror, MCP auditor) has a private **type** describing its beliefs and capabilities. A **common prior** over the joint type distribution lets us reason about when agents can agree, when they must diverge, and where safety gates (kill switches, approval boundaries) are mathematically necessary.

---

## What It Actually Does

This document maps Harsanyi’s incomplete-information game framework onto the Lantern OS agent fleet. It gives us:

- **Formal structure** for why approval gates exist (belief divergence = mandatory human checkpoint)
- **Type definitions** for each live agent, tied to real files and environment variables
- **Common prior** anchored to `data/` state, not wishful thinking
- **Higher-order belief tracking** so agents know what other agents know about them

---

## Evidence / Source Discipline

| Theory Source | Lantern OS File | Mapping |
|---------------|-----------------|---------|
| Harsanyi type | `Autonomous-Trade-Executor.ps1` param block | Agent type = `(Mode, KillSwitch, MaxPositionSize)` |
| Common prior | `data/kalshi/kalshi-paper-positions-latest.json` | Shared belief over market state and position risk |
| Private type | `KALSHI_API_KEY_ID`, `KALSHI_PRIVATE_KEY` env vars | Credentials known only to Kalshi agent |
| Higher-order belief | `LANTERN_LIVE_ENABLED` env var | Operator’s intent known to all, but verifiable only by human |
| Type space | `skills/trade/Harsanyi-TypeSpace.ps1` | Executable model of the full space |

---

## The Model

### 1. Players (Agents)

```text
N = {Human, KalshiAgent, IBKRExecutor, CloudMirror, McpAuditor, ConvergenceValidator}
```

| Agent | File / Surface | Role |
|-------|---------------|------|
| `Human` | Alex Place (operator) | Approval authority, kill-switch owner |
| `KalshiAgent` | `apps/lantern-trade-chat/app/kalshi.py` | Paper/live order submission, RSA-PSS signing |
| `IBKRExecutor` | `d:\tmp\lantern-os (1)\Autonomous-Trade-Executor.ps1` | Autonomous trade execution with human-in-the-loop |
| `CloudMirror` | `apps/lantern-garage/server.js` | Health monitoring, mirror status, read-only API |
| `McpAuditor` | `data/automation/mcp-canary-results.json` | MCP tool safety validation, read-only checks |
| `ConvergenceValidator` | `scripts/Invoke-LanternConvergenceLoop.ps1` | Repo integrity, issue detection, receipt generation |
```

### 2. Type Definition for Each Agent

A type `t_i` for agent `i` is a tuple:

```text
t_i = (beliefs, capabilities, information_set, risk_tolerance, approval_status)
```

#### Human Operator Type
```text
t_Human = (
    beliefs:       {market_outlook, system_health, family_energy},
    capabilities:  {approve_trade, toggle_kill_switch, deploy_cloud},
    information:   {capital_available, daily_energy, family_context},
    risk_tolerance: {max_loss_usd, max_positions, paper_before_live},
    approval_status: {pending, approved, denied}
)
```

#### KalshiAgent Type
```text
t_Kalshi = (
    beliefs:       {orderbook_depth, market_probability, settlement_risk},
    capabilities:  {submit_order, query_positions, sign_rsa_pss},
    information:   {api_key_id, private_key_pem, paper_positions},
    risk_tolerance: {bankroll_usd=50, per_market_max=10, daily_loss_limit=20},
    approval_status: {blocked, paper, live_pending, live}
)
```

#### IBKRExecutor Type
```text
t_IBKR = (
    beliefs:       {price_feed, spread, margin_requirement},
    capabilities:  {execute_market_order, validate_risk, log_ledger},
    information:   {portfolio_holdings, margin_balance, mode_flag},
    risk_tolerance: {max_position_size, max_risk_per_trade},
    approval_status: {paper, live_approved}
)
```

#### CloudMirror Type
```text
t_Cloud = (
    beliefs:       {mirror_health, netlify_status, local_primary},
    capabilities:  {serve_static, proxy_api, report_health},
    information:   {deploy_id, last_checked, retired_mirrors},
    risk_tolerance: {read_only_methods, no_write_without_local},
    approval_status: {healthy, degraded, held}
)
```

### 3. Common Prior

The common prior `P(t_Human, t_Kalshi, t_IBKR, t_Cloud, ...)` is a joint distribution over all agent types. In Lantern OS, this is grounded in:

- `data/kalshi/kalshi-paper-positions-latest.json` — shared belief about trading state
- `data/wallet/ledger.jsonl` — shared belief about capital flow
- `manifests/cloud-mirrors.json` — shared belief about deployment state
- `manifests/evidence/loop-receipt-LATEST.json` — shared belief about repo health

The prior is **not** uniform optimism. It is the actual state of the repo, read from disk.

### 4. Higher-Order Beliefs

Harsanyi’s framework requires infinite belief hierarchies. In practice, Lantern OS tracks three levels:

| Level | Example |
|-------|---------|
| 1st-order | KalshiAgent knows its own positions |
| 2nd-order | KalshiAgent knows Human knows its positions (via `/api/status`) |
| 3rd-order | KalshiAgent knows Human knows KalshiAgent knows Human has kill-switch active |

**Critical boundary**: At level 3, divergence is common. The Human may believe the KalshiAgent believes `LANTERN_LIVE_ENABLED=1`, but the Human may have forgotten to set it. This is why the kill-switch file and env var checks are **physical verification gates**, not assumed common knowledge.

---

## Proven / Held / Local-Only

| Component | Status | Evidence |
|-----------|--------|----------|
| Kalshi paper positions | ✅ Proven | `data/kalshi/kalshi-paper-positions-latest.json` — 8 positions, $4.07 allocated |
| IBKR demo trade | ✅ Proven | `d:\tmp\lantern-os (1)\trade-ledger.csv` — 1 paper AAPL trade |
| Cloud mirror live | ✅ Proven | `manifests/cloud-mirrors.json` — Netlify active |
| Live trading | ⏸️ Held | All agents have `approval_status = blocked` by default |
| Kill-switch | ⏸️ Held | File-based; requires operator physical action to remove |
| Common prior convergence | 🔶 Local-only | Type space script exists but not yet run in CI |

---

## Next Safe Action

1. Run `skills/trade/Harsanyi-TypeSpace.ps1` to sample the type space and check for belief divergence.
2. If divergence > 0 on trading approval status, **do not proceed to live** — this is the model confirming the human gate.
3. Log the type space snapshot to `logs/harsanyi-type-space.jsonl` for audit trail.
4. Update `docs/HARSANYI-TYPE-SPACE-LANTERN-OS.md` after first run with actual posterior data.

---

## Validation Path

```powershell
# 1. Run the type space model
powershell -ExecutionPolicy Bypass -File skills\trade\Harsanyi-TypeSpace.ps1

# 2. Check for divergence
# Output shows each agent type and whether common prior holds

# 3. Run convergence loop to ensure new files are clean
powershell -ExecutionPolicy Bypass -File scripts\Invoke-LanternConvergenceLoop.ps1

# 4. Run test suite
python -m pytest tests/ -v --tb=short
```

---

## Appendices

### A. Relation to Aumann Agreement Theorem

Aumann says rational agents with common priors and common knowledge of posteriors cannot agree to disagree. In Lantern OS:

- **When agents agree**: Trading can proceed autonomously within risk bounds.
- **When agents disagree**: Mandatory human checkpoint. The disagreement itself is evidence of model divergence or missing information.

The kill-switch is the physical implementation of "we do not have common knowledge of safety."

### B. Relation to Hierarchical Priors

The Hierarchical Priors Engine (`skills/hierarchical-engine/`) is a practical compression of the type space. Instead of tracking full infinite belief hierarchies, it tracks:

- Group-level hyperprior (shared belief about agent reliability)
- Individual posteriors (each agent’s updated beliefs)
- Shrinkage toward group mean when individual data is sparse

This is computationally tractable where full type spaces are not.

### C. Source File Index

| File | Purpose |
|------|---------|
| `skills/trade/Harsanyi-TypeSpace.ps1` | Executable type space model |
| `docs/KALSHI-LIVE-TRADING.md` | Kalshi live trading boundaries |
| `skills/trade/TRADING-ASSISTANT-ARCHITECTURE.md` | Full trading system architecture |
| `data/kalshi/kalshi-paper-positions-latest.json` | Current paper trading state |
| `manifests/cloud-mirrors.json` | Cloud deployment state |

---

**End of Document**
