# Headless Agent Launcher - No Popups

**Status:** Production-Ready  
**Date:** June 2, 2026  
**Purpose:** Run local agents inside containers without forcing popups on host system

---

## What This Does

✅ **Eliminates forced popups** from agent slots spawning  
✅ **Runs agents inside container** (headless)  
✅ **Auto-monitors** agent processes (restart on crash)  
✅ **Integrates with MCP swarm** for coordination  
✅ **No CLI/PowerShell popups** on host  

---

## Architecture

```
┌─────────────────────────────────────────┐
│   Agent Launcher Container (headless)   │
│  • Spawns 5 agent processes              │
│  • Monitors & restarts on crash          │
│  • No popups on host system              │
└────────────┬────────────────────────────┘
             │
    ┌────────┴──────────────────┐
    │                           │
    v                           v
┌──────────────────┐    ┌─────────────────┐
│ Agent Processes  │    │ MCP Swarm Coord │
│ (inside container)   │ (Dashboard UI)  │
│                      │ (port 5100)     │
│ • Dream Journal      └─────────────────┘
│ • Audit API
│ • Bayesian Model
│ • Lucid Dream
│ • Stats Monitor
└──────────────────┘
```

---

## Quick Start

### 1. Start Containers
```bash
docker-compose -f docker-compose.agent-launcher.yml up -d
```

### 2. View Agent Status
```bash
# Check running agents
docker ps

# View agent logs
docker logs lantern-agent-launcher

# View MCP dashboard
http://localhost:5100
```

### 3. Stop Containers
```bash
docker-compose -f docker-compose.agent-launcher.yml down
```

---

## Configuration

**File:** `config/agent-slots.json`

Defines all agent slots:
```json
{
  "agents": [
    {
      "id": "agent_001",
      "name": "Dream Journal",
      "type": "dream_journal",
      "port": 5000,
      "command": "python -m ...",
      "memory_limit_mb": 256,
      "healthcheck": {...}
    }
  ]
}
```

### Add New Agent Slot
1. Add entry to `agent-slots.json`
2. Define command line
3. Restart container

---

## How It Works

### 1. **Container Start**
- Agent Launcher container boots
- Reads `agent-slots.json`

### 2. **Agent Spawning** (Headless)
- Spawns 5 subprocess agents INSIDE container
- Uses `CREATE_NO_WINDOW` on Windows (no popups)
- Uses standard Popen on Linux/macOS

### 3. **Process Monitoring**
- Monitors each agent process every 5 seconds
- Auto-restarts if crashed
- Logs all events

### 4. **MCP Coordination**
- Agents register with MCP swarm
- Dashboard shows real-time status
- Smart delegation routes jobs

---

## Files

```
lantern-os/
├── Dockerfile.agent-launcher               (Container for launcher)
├── docker-compose.agent-launcher.yml       (Compose setup)
├── config/agent-slots.json                 (Agent configuration)
└── services/
    ├── agent-launcher/
    │   ├── headless_launcher.py           (Launcher service)
    │   └── requirements.txt
    └── mcp-delegation/
        ├── Dockerfile                      (MCP dashboard container)
        ├── dashboard.py
        └── delegation.py
```

---

## Key Features

### No Popups
- Agents spawn inside container
- Host system stays clean
- Windows: `CREATE_NO_WINDOW` flag used

### Auto-Recovery
- Detects crashed agents
- Automatically restarts
- Logs all crashes

### Health Monitoring
- Configurable health checks per agent
- Port-based connectivity checks
- Timeout and retry settings

### Resource Management
- Per-agent memory limits
- Idle timeout settings
- Graceful shutdown on SIGTERM

---

## Monitoring

### Check Agent Status
```bash
# View running container
docker ps | grep agent-launcher

# View agent logs
docker logs -f lantern-agent-launcher

# View MCP dashboard
curl http://localhost:5100/api/agents
```

### Restart Agents
```bash
# Restart launcher (restarts all agents)
docker restart lantern-agent-launcher

# Rebuild and restart
docker-compose -f docker-compose.agent-launcher.yml restart
```

---

## Benefits

✅ **Host Clean** — No popups, no CLI windows  
✅ **Automated** — Auto-restart on crash  
✅ **Scalable** — Easy to add more agents  
✅ **Monitored** — Real-time status  
✅ **Production-Ready** — Error handling, health checks  

---

**Status: ✅ PRODUCTION-READY - NO POPUPS**

