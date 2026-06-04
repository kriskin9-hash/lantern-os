# MCP Connector - Final Solution

Archived from root during cleanup. The original contained a concrete bearer token, which is redacted here. Rotate any token that appeared in the previous root document.

**Historical status:** Fixed  
**Historical date:** 2026-04-26  
**Root cause:** Orchestrator and MCP both wanted port 8787.  
**Historical solution:** Move MCP to a separate local port.

---

## Preserved lesson

The local orchestrator and local MCP server must not bind the same port. If the GPT connector points at the orchestrator instead of the MCP JSON-RPC server, it can produce connector failures such as 502 responses.

---

## Safe connector shape

```json
{
  "endpoint": "http://127.0.0.1:<mcp-port>/mcp",
  "method": "POST",
  "headers": {
    "Authorization": "Bearer <redacted-local-token>",
    "Content-Type": "application/json"
  }
}
```

---

## Historical port layout

```text
8787  -> Orchestrator
8788  -> MCP Server
9001  -> Dashboard
```

Use current configuration and operator runbooks as the source of truth. This archived note preserves the incident lesson only.
