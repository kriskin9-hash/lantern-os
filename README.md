# Lantern OS

Local-first OS cockpit built by Alex Place. The repo contains a Dream Journal server, an Imagniverse/status-cube interface, a payment bridge stub, and the Lantern Garage Node.js server that ties them together.

## What it does today

| Component | Description |
|-----------|-------------|
| **Dream Journal** | Local journaling app (entries, emotions, tags, lucidity). Data stored in `data/dream_journal/*.jsonl`. |
| **Lantern Garage server** | Node.js HTTP server (`apps/lantern-garage/server.js`). Serves the Dream Journal UI and REST API on port 4177. |
| **Imagniverse / status cube** | 4D routing matrix for Lantern OS state — a routing and inspection interface, not physical hardware. Lives in `surfaces/`. |
| **Payment bridge** | Stub for Stripe invoice workflows (`apps/lantern-garage/payment-bridge/`). Not connected to a live Stripe account. |
| **GitHub Pages static UI** | The `gh-pages` branch hosts static surfaces (pitch, proof, pricing, wish-door). |

## What is NOT in scope

- No live trading or financial execution.
- No production Stripe integration (payment bridge is a stub).
- No actual outreach automation (outreach scripts are drafts only).
- No cloud data storage — all journal data stays on your machine.

## How to run

### Prerequisites

```
node --version   # v20 or higher required
```

### Local (default)

```bash
node apps/lantern-garage/server.js
# opens at http://127.0.0.1:4177
```

Or with npm:

```bash
npm start --prefix apps/lantern-garage
```

### Cloud (Railway)

Railway auto-deploys from `master`. The `railway.json` and `cloud-server.js` handle the cloud entrypoint. Set `PORT` in Railway environment variables; the server binds to `0.0.0.0` when `PORT` is present.

### Static UI (GitHub Pages)

Static surfaces are deployed from the `gh-pages` branch via the GitHub Actions workflow in `.github/workflows/`.

## Running Services

| Service | Port | Status | URL | Process |
|---------|------|--------|-----|---------|
| **Lantern Garage** | `4177` | Running | http://127.0.0.1:4177 | `node apps/lantern-garage/server.js` |
| **GPT Web API** | `3000` | Running | http://127.0.0.1:3000 | `node integrations/gm-agent-orchestrator/tools/gpt-web-api/server.js` |
| **Discord Radio Bot** | N/A | Needs token | — | `python apps/lantern-discord-radio/bot.py` |

Start all:
```bash
# Terminal 1 — Garage
npm start --prefix apps/lantern-garage

# Terminal 2 — GPT Web API
npm start --prefix integrations/gm-agent-orchestrator/tools/gpt-web-api

# Terminal 3 — Discord Bot (requires token)
python apps/lantern-discord-radio/bot.py
```

## Backlog

Linear is the source of truth for the backlog. GitHub Issues are intake only and may lag behind Linear.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
