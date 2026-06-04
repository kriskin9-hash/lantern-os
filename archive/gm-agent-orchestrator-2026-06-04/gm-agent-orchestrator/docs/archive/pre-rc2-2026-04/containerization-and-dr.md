# Containerization & Disaster Recovery Plan

**Status:** Preparing orchestrator system for resilient deployment  
**Challenge:** All 3 servers going "blocked" on reset → need persistent state recovery  
**Goal:** Containerized deployment with automatic recovery from power loss

---

## Current Issues

1. **Orchestrator** - Won't start, exits immediately
2. **MCP Server** - Crashes after brief startup  
3. **Dashboard** - Loses state on restart
4. **Problem:** Single point of failure - one reset blocks all three

---

## Proposed Architecture: Containerized with Persistence

```
┌─────────────────────────────────────────┐
│ Docker Compose (handles orchestration)  │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────────┐                  │
│  │ Orchestrator     │                  │
│  │ (service)        │  ← Restart:     │
│  │ Port: 8787       │    always       │
│  └──────────────────┘                  │
│          ↓ (persist)                   │
│  ┌──────────────────┐                  │
│  │ Task State Vol   │  ← Survives     │
│  │ /tasks/          │    power loss   │
│  └──────────────────┘                  │
│                                        │
│  ┌──────────────────┐                  │
│  │ MCP Server       │                  │
│  │ Port: 8788       │  ← Restart:     │
│  │ Token: env var   │    always       │
│  └──────────────────┘                  │
│                                        │
│  ┌──────────────────┐                  │
│  │ Dashboard        │                  │
│  │ Port: 9001       │  ← Restart:     │
│  │ (static assets)  │    always       │
│  └──────────────────┘                  │
│                                        │
└─────────────────────────────────────────┘
```

---

## Step 1: Power Loss Recovery (Immediate)

### Problem
When power is lost:
- Servers stop unexpectedly
- Services get "blocked" state
- No automatic recovery

### Solution: Service Manager with Auto-Restart

**File:** `.docker/docker-compose.yml` (create)

```yaml
version: '3.8'
services:
  orchestrator:
    build: .
    ports:
      - "8787:8787"
    volumes:
      - ./tasks:/app/tasks  # Persist task state
      - ./status:/app/status # Persist agent status
    restart: always  # Auto-restart on crash/power loss
    environment:
      - ORCH_PORT=8787
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8787/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  mcp-server:
    build: .
    ports:
      - "8788:8788"
    restart: always
    environment:
      - ORCH_MCP_PORT=8788
      - ORCH_MCP_TOKEN=${ORCH_MCP_TOKEN}
    depends_on:
      - orchestrator
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8788/"]
      interval: 30s
      timeout: 10s
      retries: 3

  dashboard:
    build: .
    ports:
      - "9001:9001"
    restart: always
    depends_on:
      - orchestrator
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9001/dashboard/index-v3.html"]
      interval: 30s
```

---

## Step 2: State Persistence (Critical)

### What Must Survive Power Loss

```
✅ MUST PERSIST:
  - /tasks/queue/        (pending work)
  - /tasks/active/       (in-progress)
  - /tasks/done/         (completed)
  - /tasks/failed/       (failed items)
  - /status/orchestrator.json  (agent state)
  - /tasks/QUEUE_STATUS.json   (queue state)

❌ OK TO LOSE:
  - Temporary logs
  - Cache
  - Running connections
  - Session state (will reconnect)
```

### Implementation

Using Docker volumes to mount these directories:

```yaml
volumes:
  - ./tasks:/app/tasks  # All task state
  - ./status:/app/status # Agent status
```

On power loss:
1. Server stops
2. Volumes preserved on disk
3. Power restored
4. Container restarts
5. Volumes remounted
6. Services read current state
7. Continue from where they left off

---

## Step 3: Blocked State Recovery (Handle 3-Server Reset)

### Current Problem
When one service resets or crashes, all become blocked.

### Solution: Independent Health Checks + Fallback

Each service checks other services:
- If orchestrator down: MCP retries
- If MCP down: Dashboard falls back to local state
- If one is blocked: Others continue

**File:** `health-check.ps1` (create)

```powershell
# Check all three services
# If any are blocked, reset their blocker state
# Restart the blocked one
```

---

## Step 4: Dockerfile (Container Image)

**File:** `Dockerfile` (create)

```dockerfile
FROM mcr.microsoft.com/windows/servercore:ltsc2022

# Install PowerShell, .NET, required tools
RUN powershell -Command \
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; \
    iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))

WORKDIR /app
COPY . .

# Expose ports
EXPOSE 8787 8788 9001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD powershell -Command \
    try { \
        $response = Invoke-WebRequest http://localhost:8787/health -UseBasicParsing; \
        if ($response.StatusCode -eq 200) { exit 0 } else { exit 1 } \
    } catch { exit 1 }

# Start all services
CMD powershell -NoProfile -ExecutionPolicy Bypass -Command \
    $env:ORCH_MCP_TOKEN = $env:ORCH_MCP_TOKEN; \
    Start-Job -ScriptBlock { & ./scripts/Start-GmAgentOrchestrator.ps1 -Headless }; \
    Start-Job -ScriptBlock { & ./scripts/Start-OrchMcpServer.ps1 }; \
    Start-Job -ScriptBlock { & ./scripts/Start-Dashboard.ps1 }; \
    Get-Job | Wait-Job
```

---

## Step 5: Disaster Recovery Runbook

### If All Services Are Blocked (Complete Failure)

**Option A: Auto-Reset (Recommended)**
```powershell
# In health-check monitoring:
if (all services blocked) {
  1. Kill all containers
  2. Preserve volumes (tasks, status)
  3. Restart docker-compose
  4. Services read last-known state
  5. Auto-recover
}
```

**Option B: Manual Recovery**
```powershell
# User action needed:
1. Stop all services: docker-compose down
2. Check task state: ls tasks/
3. If corrupted: restore from backup
4. Start fresh: docker-compose up -d
5. Services resume from persisted state
```

---

## Implementation Priority

### Phase 1 (This Week) - Immediate Resilience
- [ ] Create docker-compose.yml with auto-restart
- [ ] Mount /tasks/ and /status/ as volumes
- [ ] Test: Kill a service, verify auto-restart
- [ ] Test: Simulate power loss, verify recovery

### Phase 2 (Next Week) - Full Containerization
- [ ] Create Dockerfile
- [ ] Build image
- [ ] Test: Run all 3 services in containers
- [ ] Verify they coordinate correctly

### Phase 3 (Week After) - Monitoring & DR
- [ ] Health check service
- [ ] Auto-recovery script for blocked state
- [ ] Backup strategy for volumes
- [ ] DR runbook documentation

---

## Benefits

✅ **Auto-recovery** from power loss  
✅ **No blocked state** after reset (services restart cleanly)  
✅ **Persistent state** survives container restarts  
✅ **Portable** - same image runs anywhere  
✅ **Monitorable** - health checks detect issues  
✅ **Scalable** - can run multiple orchestrator instances  

---

## Immediate Next Steps

1. **Create docker-compose.yml** with volumes mounted
2. **Test manual recovery** - stop/start services, verify state persists
3. **Test power-loss scenario** - kill -9 all services, restart
4. **Add health checks** - detect when services are blocked
5. **Document recovery procedures** - so humans know what to do

---

## Question for You

Which phase should we start with?
- Phase 1: Container orchestration with persistence (fastest path to resilience)
- All phases: Full containerization + DR (takes longer, most robust)
