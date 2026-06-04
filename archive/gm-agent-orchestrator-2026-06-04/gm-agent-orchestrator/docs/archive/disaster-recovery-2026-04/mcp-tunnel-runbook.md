# MCP Tunnel Runbook

## P0 Rule
If GPT says unsafe URL, localhost is the problem first.

## Required for GPT Remote MCP
Use a public HTTPS endpoint, not:
- http://127.0.0.1
- http://localhost
- private LAN IPs

## Fast Path
1. Start MCP server
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-OrchMcpServer.ps1

2. Start Cloudflare Quick Tunnel
cloudflared tunnel --url http://localhost:8787

3. Use printed HTTPS URL + /mcp

Example:
https://random.trycloudflare.com/mcp

## Validation
POST initialize should return HTTP 200.

## Common Failures
- unsafe URL -> use HTTPS tunnel
- unauthorized -> missing bearer token
- 404 root path -> use /mcp
- cloudflared tunnel run error -> wrong mode, use --url

## Contract Update
Before changing agent code, verify tunnel availability.

## Agent Update
Assume remote GPT needs public HTTPS MCP access.
