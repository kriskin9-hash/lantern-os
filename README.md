# Lantern OS

Local-first OS cockpit built by Alex Place. The repo contains a Dream Journal server, an Imagniverse/status-cube interface, a payment bridge stub, and the Lantern Garage Node.js server that ties them together.

## What it does today

| Component | Description |
|-----------|-------------|
| **Dream Journal** | Freeform RP chat interface. No hardcoded fields — just talk. Chat at top, fixed input bar at bottom. Data stored in browser localStorage with JSONL export. |
| **Lantern Garage server** | Node.js HTTP server (`apps/lantern-garage/server.js`). Serves the Dream Journal UI and REST API on port 4177. |
| **Imagniverse / status cube** | 4D routing matrix for Lantern OS state — a routing and inspection interface, not physical hardware. Lives in `surfaces/`. |
| **Payment bridge** | Stub for Stripe invoice workflows (`apps/lantern-garage/payment-bridge/`). Not connected to a live Stripe account. |
| **CSF / CADD** | Convergence-Fitted Searchable Binary Archive format (v1.0 spec) + Context Archive for Dream Data. Used for memory exports and symbolic data compression. |
| **GitHub Pages / Netlify static UI** | Static surfaces deployed from `apps/lantern-garage/public/` (pitch, proof, pricing, wish-door, dream-journal). |

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
| **MCP Server** | `8771` | Running | http://127.0.0.1:8771 | `python src/mcp_server/server.py` |
| **Discord Radio Bot** | N/A | Needs token | — | `python apps/lantern-discord-radio/bot.py` |

Start all:
```bash
# Terminal 1 — Garage
npm start --prefix apps/lantern-garage

# Terminal 2 — GPT Web API
npm start --prefix integrations/gm-agent-orchestrator/tools/gpt-web-api

# Terminal 3 — MCP Server
python src/mcp_server/server.py

# Terminal 4 — Discord Bot (requires token)
python apps/lantern-discord-radio/bot.py
```

## Deployed URLs

| Environment | URL | Description |
|-------------|-----|-------------|
| **GitHub Pages** | https://alex-place.github.io/lantern-os/ | Static UI (pitch, proof, pricing, wish-door, dream-journal) |
| **Repository** | https://github.com/alex-place/lantern-os | Source code, issues, PRs |

## IDE Integration (Windsurf / Cascade MCP)

The Lantern OS MCP server is linked to Windsurf/Cascade via a stdio bridge.

1. Start the MCP server (port 8771):
   ```bash
   python src/mcp_server/server.py
   ```
2. Windsurf reads `.windsurf/mcp.json` and connects through `scripts/mcp_stdio_bridge.py`.
3. Exposed tools: `queue_status`, `task_intake`, `dispatch_work`, `boot_check`, `list_skills`, `get_status`, `fleet_status`.

## User Guides

| Workstream | Guide | Description |
|------------|-------|-------------|
| **Tesseract Convergence** | `manifests/TESSERACT-ARCHITECTURE.md` | 4-layer hypercube (Surface, Interface, Convergence, Core) — personas, slots, connector, dollhouse CSF, convergence engine, inspector |
| **Unified Agent Connector** | `src/unified_agent_connector.py` docstring | Multi-provider AI streaming with health checks — OpenAI, Anthropic, Google, Mistral |
| **CSF Dollhouse** | `src/cadd_dollhouse_csf.py` docstring | Convergence-Fitted Searchable Binary format for memory archives and segment building |
| **Agent Inspector** | `scripts/agent_inspector.py` docstring | Health and self-monitoring daemon with tesseract layer checks |
| **MCP Connector** | `docs/MCP-CONNECTOR.md` | Local-first MCP connector, RAG-house indexing, safety contract |
| **Dream Journal** | `apps/lantern-garage/public/dream-journal.html` | Freeform RP chat interface with localStorage + JSONL export |

## Backlog

Linear is the source of truth for the backlog. GitHub Issues are intake only and may lag behind Linear.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
