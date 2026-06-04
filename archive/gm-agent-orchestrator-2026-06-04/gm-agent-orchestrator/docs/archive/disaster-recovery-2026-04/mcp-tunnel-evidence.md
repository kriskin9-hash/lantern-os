# MCP Tunnel Evidence Log

## Confirmed Working Public MCP Endpoint

Cloudflare Quick Tunnel created:

https://inner-distinguished-acceptable-bits.trycloudflare.com

Local command used:

cloudflared tunnel --url http://localhost:8787

Cloudflared reported:
- quick tunnel created
- public HTTPS URL assigned
- routed to localhost:8787
- connection registered

## Final GPT MCP URL

https://inner-distinguished-acceptable-bits.trycloudflare.com/mcp

## Why This Matters

GPT rejected:
- http://127.0.0.1:8787/mcp
- localhost URLs

But accepted public HTTPS tunnel path.

## Proven Facts

1. Local MCP initialize returned 200
2. tools/list returned 200
3. Tunnel endpoint returned 200
4. Public HTTPS tunnel is the correct GPT MCP URL

## Contract Update

When MCP fails:
1. Verify local MCP server
2. Verify tunnel exists
3. Use HTTPS tunnel URL + /mcp
4. Only then inspect code

## Agent Update

Do not recommend localhost MCP URLs for hosted GPT connectors.

## Evidence Sources

Cloudflare docs:
Quick tunnels create random trycloudflare.com URLs proxied to localhost.

OpenAI docs:
Remote MCP uses publicly reachable server URLs.

## Session Evidence (2026-04-26)

Current Cloudflare Quick Tunnel URL reported by operator:

https://trio-roy-valium-constant.trycloudflare.com

Current GPT MCP URL:

https://trio-roy-valium-constant.trycloudflare.com/mcp

Operational assumption:

This quick-tunnel setup is temporary and must be recreated whenever the MCP server or cloudflared tunnel is bounced. The public trycloudflare.com hostname should not be treated as durable configuration.

Required follow-up:

Create and prioritize a task to investigate a durable replacement or upgrade path for the temporary Cloudflare Quick Tunnel MCP exposure.

## Connector Acceptance Evidence (2026-04-26)

Current GPT MCP URL under test:

https://martial-historical-rarely-provisions.trycloudflare.com/mcp

Authentication reality:

The GPT MCP configuration surface available to the operator does not support bearer-token auth. Therefore the temporary quick-tunnel path must run scripts/Start-OrchMcpServer.ps1 with -NoAuth, or the project must implement a GPT-compatible auth flow before requiring auth.

Correct temporary configuration:

URL:

https://martial-historical-rarely-provisions.trycloudflare.com/mcp

Authentication:

No authentication

Operator judgment:

The system itself is live. The remaining task is connector acceptance/auth wiring, not basic server engineering.

## Connector Compatibility Evidence (2026-04-27)

Current public MCP URL tested by operator:

https://coalition-blades-fraction-happy.trycloudflare.com/mcp

Observed public GET /mcp response:

```text
is online use json-rpc post requests
```

Observed public JSON-RPC POST initialize result:

```text
success
```

Observed GPT connector result:

```text
failed to add connector
```

Current diagnosis:

The local MCP server, public tunnel reachability, NoAuth mode, and basic JSON-RPC initialize path are working. The remaining blocker is likely ChatGPT connector acceptance/protocol compatibility with the current minimal stateless JSON-RPC server implementation, not basic tunnel or port availability.

Next evidence required:

Run public tools/list against the same URL and preserve exact output. If tools/list succeeds, compare scripts/Start-OrchMcpServer.ps1 against current ChatGPT MCP connector transport/session requirements before changing more ops settings.
