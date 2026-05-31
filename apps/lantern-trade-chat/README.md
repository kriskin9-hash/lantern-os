# Lantern Trade Chat

**Status:** working app, login-walled. Live trading ships disabled.
**Surface:** FastAPI + static chat UI. Docker + Kubernetes ready.
**Audience:** founder + Courtney only (GitHub username allowlist).

---

## Simple Answer

A private chat app for placing Kalshi orders by typing plain English
("`buy 1 yes on TICKER at 40c`"). Access is gated by **GitHub OAuth** and an
**allowlist** of usernames. It reuses the exact safety rails from
`scripts/Invoke-KalshiLiveOrder.ps1`: dry-run by default, kill switch, and
per-order / per-day / trades-per-day caps. Real money is only spent when the
deployment is explicitly armed **and** the request comes from an allowlisted,
logged-in user.

## What It Actually Does

- **Login** — `/login` → GitHub OAuth. Only usernames in `GITHUB_ALLOWED_LOGINS`
  are admitted; everyone else gets a 403. No login → every trading endpoint 401s.
- **Chat** — type an order; the app parses it (rule-based, no LLM), shows the
  order plan, cost/risk, balance, and any blockers, then offers a confirm button.
- **Dry-run by default** — orders preview unless you prefix `live` *and* the
  deployment has `LANTERN_LIVE_ENABLED=1`.
- **Read-only balance** — `/api/balance` signs a real Kalshi request (RSA-PSS).
- **Full account status** — `/api/status` returns connectivity, open orders, positions, recent fills, settlements, and any settlement warnings (voided/disputed/pending markets surface automatically).

## Evidence / Source Discipline

- No secrets in the repo. Keys come from env (`KALSHI_*`, `GITHUB_OAUTH_*`).
- Signing is a direct Python port of the PowerShell live-order script; verified
  against Kalshi **production** with a read-only balance call ($7.39 observed).
- `tests/test_app.py`: 14 tests cover parsing, every safety gate, key loading +
  signature round-trip, and auth gating (401 without login).

## Proven / Held / Local-only

- **Proven:** auth gating, dry-run default, caps math, RSA-PSS signing vs. prod.
- **Operator-approved (2026-05-31):** read-only status queries — `get_balance`, `get_orders`, `get_positions`, `get_fills`, `get_settlements` — wired and approved for external calls.
- **Held:** live order submission against prod is gated behind `LANTERN_LIVE_ENABLED` + kill switch + allowlisted login. Not exercised with a real order in CI.
- **Local-only:** the live ledger (`data/kalshi/kalshi-live-ledger.jsonl`) is written at runtime and gitignored.
- **Platform-risk note:** Kalshi regulatory/settlement disputes flagged in public coverage as of March 2026. `settlementWarnings` in `/api/status` surfaces any voided, disputed, or pending settlements automatically.

## Next Safe Action

```bash
# Local run
cd apps/lantern-trade-chat
python -m venv .venv && . .venv/bin/activate
pip install -e .
cp .env.example .env        # fill in GitHub OAuth + Kalshi creds
set -a && . ./.env && set +a
uvicorn app.main:app --reload --port 8080
# open http://127.0.0.1:8080
```

GitHub OAuth app callback URL: `https://<your-host>/auth/callback`
(local: `http://127.0.0.1:8080/auth/callback`).

To arm real money: set `LANTERN_LIVE_ENABLED=1`, `KALSHI_ENVIRONMENT=prod`, and
ensure no `data/kalshi/LIVE-KILL-SWITCH` file is present.

## Validation Path

```bash
pip install -e . pytest httpx
pytest tests -q          # 14 passed
```

## Appendices

### Docker
```bash
docker build -t lantern-trade-chat .
docker run --rm -p 8080:8080 --env-file .env lantern-trade-chat
```

### Kubernetes
```bash
kubectl create namespace lantern
kubectl -n lantern create secret generic lantern-trade-chat-secrets \
  --from-literal=GITHUB_OAUTH_CLIENT_ID=... \
  --from-literal=GITHUB_OAUTH_CLIENT_SECRET=... \
  --from-literal=LANTERN_SESSION_SECRET="$(openssl rand -hex 32)" \
  --from-literal=KALSHI_API_KEY_ID=... \
  --from-literal=KALSHI_PRIVATE_KEY="$(cat kalshi-private-key.pem)"
kubectl apply -f k8s/         # deployment, service, ingress
```
Edit `k8s/ingress.yaml` host + `k8s/deployment.yaml` image before applying.

### Environment variables
See `.env.example`. Safety-relevant: `LANTERN_LIVE_ENABLED` (default 0),
`KALSHI_ENVIRONMENT` (default demo), `LANTERN_MAX_PER_ORDER_USD` (40),
`LANTERN_MAX_DAILY_LOSS_USD` (40), `LANTERN_MAX_TRADES_PER_DAY` (1).

### API surface

| Endpoint | Auth | Write | Description |
|---|---|---|---|
| `GET /api/health` | none | no | App health, env, kill-switch state |
| `GET /api/me` | none | no | Current session user |
| `GET /api/balance` | login required | no | Account balance in USD + daily caps |
| `GET /api/status` | login required | no | Full read-only status: connectivity, open orders, positions, fills, settlements, settlement warnings |
| `POST /api/chat` | login required | dry-run default | Parse plain-English order; returns plan + blockers |
| `POST /api/order` | login required | live-gated | Submit order; dry-run unless `live: true` + `LANTERN_LIVE_ENABLED=1` |

### Kalshi client methods (`app/kalshi.py`)

| Method | HTTP | Description |
|---|---|---|
| `get_balance()` | GET /portfolio/balance | Account balance in cents |
| `get_orders(status, limit)` | GET /portfolio/orders | Orders by status: `resting` \| `all` \| `canceled` \| `executed` |
| `get_positions(limit)` | GET /portfolio/positions | Open positions |
| `get_fills(limit)` | GET /portfolio/fills | Recent executed fills |
| `get_settlements(limit)` | GET /portfolio/settlements | Settlement history; voided/disputed/pending flagged as warnings |
| `create_order(...)` | POST /portfolio/orders | Place limit or market order (live-gated) |
