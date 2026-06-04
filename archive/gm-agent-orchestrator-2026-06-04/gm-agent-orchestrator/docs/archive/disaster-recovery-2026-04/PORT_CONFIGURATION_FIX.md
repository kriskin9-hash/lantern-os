# Port Configuration Fix: Orchestrator vs MCP Connector

**Problem:** Orchestrator running on port 8787, MCP needs port 8787  
**Solution:** Move orchestrator to port 8788, MCP uses 8787  

---

## Current State
- **Orchestrator:** Running on port 8787
- **MCP Server:** Needs to run on port 8787  
- **Conflict:** Both want same port → GPT gets 502 Bad Gateway

---

## The Fix (Two Steps)

### Step 1: Stop Orchestrator
```powershell
# Kill process using port 8787
# Find what's using it:
netstat -ano | Select-String "8787"

# Get the PID from output, then:
Stop-Process -Id <PID> -Force

# Verify it's free:
netstat -ano | Select-String "8787" | Measure-Object | Where-Object {$_.Count -eq 0} ? "✅ Port free" : "❌ Still in use"
```

### Step 2: Start Orchestrator on Different Port
Find where orchestrator is started and add `-Port 8788`:

```powershell
# If using Start-GmAgentOrchestrator.ps1, check if it accepts port parameter
# Or start with environment variable:
$env:ORCH_PORT = 8788

# Then start orchestrator with that port
```

### Step 3: Start MCP on Port 8787
```powershell
# MCP will use 8787 by default:
$env:ORCH_MCP_TOKEN = "redacted-in-archive"
& "C:\Users\alexp\Documents\gm-agent-orchestrator\scripts\Start-OrchMcpServer.ps1" -Port 8787
```

---

## Updated Configuration for GPT

After moving ports, update GPT MCP connector:

```json
{
  "endpoint": "http://127.0.0.1:8787/mcp",
  "method": "POST",
  "headers": {
    "Authorization": "Bearer redacted-in-archive",
    "Content-Type": "application/json"
  }
}
```

This stays the same because MCP is now on 8787.

---

## Quick Check

After making changes:
```powershell
# Verify ports
netstat -ano | Select-String "8787|8788"

# Expected output:
# TCP 127.0.0.1:8787 LISTENING (MCP)
# TCP 127.0.0.1:8788 LISTENING (Orchestrator)
```

---

## Why This Works

```
Before:
GPT -> port 8787 -> Orchestrator (wrong - orchestrator cannot respond as MCP)
                -> 502 Bad Gateway

After:
GPT -> port 8787 -> MCP Server
App -> port 8788 -> Orchestrator
```

---

## Summary

1. Stop orchestrator on 8787
2. Start orchestrator on 8788
3. Start MCP on 8787
4. GPT connects to 8787 and gets MCP, not orchestrator
5. GPT no longer sees 502

**This resolves the port conflict permanently.**
