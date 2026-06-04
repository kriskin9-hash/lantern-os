# Cloudflare Tunnel Setup (Legacy / Verify Before Use)

**Purpose:** Historical setup for exposing MCP through Cloudflare Tunnel.  
**Status:** Legacy / not the observed current operator path.  
**Current observed path:** ngrok gateway in a separate prompt window, documented in `docs/mcp-connector-config.md`.

---

## Current operator note

Do not assume Cloudflare is active. As of the latest operator handoff, Alex uses ngrok for the external gateway path and may run ngrok against local port `8787` in a separate prompt window.

Use `docs/mcp-connector-config.md` as the active sanitized connector target. This Cloudflare document is retained only in case the Cloudflare path is intentionally reactivated later.

---

## Historical prerequisites

1. Cloudflare account
2. `cloudflared` installed (`choco install cloudflare-warp` or `winget install Cloudflare.cloudflared`)
3. API token saved as environment variable `CLOUDFLARE_API_TOKEN`

## Historical setup steps

### 1. Create Tunnel
```powershell
$env:CLOUDFLARE_API_TOKEN = [Environment]::GetEnvironmentVariable("CLOUDFLARE_API_TOKEN", "User")
cloudflared tunnel create gm-agent-orchestrator
```

### 2. Configure Routing
Historically, the tunnel routed to the local MCP server port.

### 3. Start Tunnel
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-CloudflareTunnel.ps1
```

### 4. Record Public URL
If Cloudflare is reactivated, record only the endpoint shape in `docs/mcp-connector-config.md` with redacted token placeholders.

Do not paste live bearer tokens into repository docs. Keep the token in the local `ORCH_MCP_TOKEN` environment variable.

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `cert.pem not found` | Authenticate: `cloudflared login` in browser, complete callback |
| `origin cert not found` | API token missing - set `CLOUDFLARE_API_TOKEN` env var |
| `tunnel already exists` | Tunnel already created; just run `Start-CloudflareTunnel.ps1` |

## Integration

Tunnel startup was manual in the historical setup. If Cloudflare is reactivated, update this document and `docs/mcp-connector-config.md` in the same PR.
