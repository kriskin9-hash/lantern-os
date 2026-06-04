# MCP Port Conflict - Configuration Workaround

Archived from root during cleanup. The original contained a concrete bearer token, which is redacted here. Rotate any token that appeared in the previous root document.

**Issue:** Orchestrator and MCP both wanted local port 8787.  
**Historical solution:** Configure MCP or app clients to use a separate local port.

---

## Historical Workarounds

### Move MCP to a different port

`Start-OrchMcpServer.ps1` accepts a port parameter. Use a current local operator runbook for the supported port.

```powershell
[int]$Port = 8788
```

Connector shape:

```text
http://127.0.0.1:<port>/mcp
Authorization: Bearer <redacted-local-token>
```

### Configure orchestrator port

Potential configuration surfaces noted historically:

- `config/orchestrator.json`
- `config/server.json`
- `ORCH_PORT`
- `ORCH_SERVER_PORT`

### Environment variable option

```text
ORCH_MCP_PORT=<mcp-port>
ORCHESTRATOR_PORT=<orchestrator-port>
```

---

## Historical Value Preserved

This note preserves the port-conflict lesson: MCP and orchestrator must not bind the same local port, and live bearer tokens must not be stored in repo docs.
