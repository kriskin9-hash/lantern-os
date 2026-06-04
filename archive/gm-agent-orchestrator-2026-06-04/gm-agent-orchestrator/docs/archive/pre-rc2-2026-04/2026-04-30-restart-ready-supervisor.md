# Restart-Ready Service Supervisor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a stable local restart path for the orchestrator after Windows reboot/login, ensuring dashboard, MCP, and ngrok services are managed and monitored without waking agents.

**Architecture:** An idempotent service supervisor (`Start-OrchestratorServices.ps1`) manages services based on a registry (`local-services.json`). A Windows Startup Task triggers the supervisor. Service health is integrated into existing health monitoring and status JSON.

**Tech Stack:** PowerShell, Windows Task Scheduler, JSON.

---

### Task 1: Service Registry and Idempotent Supervisor

**Files:**
- Create: `config/local-services.example.json`
- Create: `scripts/Start-OrchestratorServices.ps1`
- Create: `tests/Test-OrchestratorServicesSupervisor.ps1`

- [ ] **Step 1: Create `config/local-services.example.json`**
```json
{
  "services": [
    {
      "name": "dashboard",
      "enabled": true,
      "required": true,
      "command": "powershell.exe",
      "args": ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "scripts/Start-Dashboard.ps1"],
      "healthUrl": "http://localhost:8765/api/status",
      "port": 8765
    },
    {
      "name": "mcp",
      "enabled": true,
      "required": true,
      "command": "powershell.exe",
      "args": ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "scripts/Start-OrchMcpServer.ps1", "-NoAuth"],
      "healthUrl": "http://127.0.0.1:8787/health",
      "port": 8787
    },
    {
      "name": "ngrok",
      "enabled": true,
      "required": false,
      "command": "ngrok.exe",
      "args": ["http", "8787", "--url", "crinkle-utmost-debit.ngrok-free.dev"],
      "healthUrl": null,
      "port": null,
      "processName": "ngrok"
    }
  ]
}
```

- [ ] **Step 2: Create `scripts/Start-OrchestratorServices.ps1`**
Implement the supervisor logic:
- Load `config/local-services.json` (fallback to example).
- Support `-DryRun` and `-Once`.
- For each enabled service:
    - Check if port is in use or process is running.
    - If healthy, skip.
    - If unhealthy/missing and not `-DryRun`, start it (using `Start-Process -WindowStyle Hidden` or similar to reduce noise).
- Write `status/services.json` with current state.

- [ ] **Step 3: Create `tests/Test-OrchestratorServicesSupervisor.ps1`**
- Test loading config.
- Test `-DryRun` behavior (should not start processes).
- Test state reporting in `status/services.json`.
- Mock health checks to verify idempotent behavior.

- [ ] **Step 4: Commit**
```bash
git add config/local-services.example.json scripts/Start-OrchestratorServices.ps1 tests/Test-OrchestratorServicesSupervisor.ps1
git commit -m "feat: add service registry and idempotent supervisor"
```

### Task 2: Startup Task Registration

**Files:**
- Create: `scripts/Register-OrchestratorStartupTask.ps1`
- Create: `tests/Test-OrchestratorStartupTask.ps1`

- [ ] **Step 1: Create `scripts/Register-OrchestratorStartupTask.ps1`**
- Use `Register-ScheduledTask` (or `schtasks.exe` if needed for better compatibility).
- Defaults to dry-run. Needs `-Apply` to mutate.
- Logic:
    - Task Name: `OrchestratorServiceSupervisor`
    - Trigger: At logon.
    - Delay: 60 seconds.
    - Action: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/Start-OrchestratorServices.ps1 -Once`
    - Settings: Stop if runs longer than 1 hour, don't allow multiple instances.
- Support `-Status` and `-Unregister`.

- [ ] **Step 2: Create `tests/Test-OrchestratorStartupTask.ps1`**
- Verify command line generation.
- Verify status reporting (mocking `Get-ScheduledTask`).
- Ensure no real task is created during tests.

- [ ] **Step 3: Commit**
```bash
git add scripts/Register-OrchestratorStartupTask.ps1 tests/Test-OrchestratorStartupTask.ps1
git commit -m "feat: add Windows startup task registration"
```

### Task 3: Health Pulse Integration

**Files:**
- Modify: `scripts/Monitor-ServerHealthPulse.ps1`
- Modify: `tests/Test-ServerHealthPulse.ps1`

- [ ] **Step 1: Extend `scripts/Monitor-ServerHealthPulse.ps1`**
- Load `status/services.json`.
- Include `ngrok` (checking process state if no health URL).
- Ensure MCP health uses `8787`.
- Mark Cloudflare as legacy/disabled unless config says otherwise.
- Update `status/server-health.json` to include these services.

- [ ] **Step 2: Update `tests/Test-ServerHealthPulse.ps1`**
- Add test cases for ngrok and services integration.
- Verify MCP port 8787 usage.

- [ ] **Step 3: Commit**
```bash
git add scripts/Monitor-ServerHealthPulse.ps1 tests/Test-ServerHealthPulse.ps1
git commit -m "feat: extend health pulse with service health and ngrok"
```

### Task 4: Ops Overview / Status Integration

**Files:**
- Modify: `scripts/Get-OrchestratorStatus.ps1`
- Create: `tests/Test-DashboardServiceHealthContract.ps1`

- [ ] **Step 1: Extend `scripts/Get-OrchestratorStatus.ps1`**
- Read `status/server-health.json`.
- Add `serviceHealth` field to `status/orchestrator.json`.
- Implement logic:
    - If MCP offline -> nextAction: "Start MCP server."
    - If ngrok offline -> nextAction: "External gateway unavailable. Inspect ngrok."
    - No agent wake allowed by default.

- [ ] **Step 2: Create `tests/Test-DashboardServiceHealthContract.ps1`**
- Verify the structure of `orchestrator.json` includes `serviceHealth`.
- Verify nextAction mapping for offline services.

- [ ] **Step 3: Commit**
```bash
git add scripts/Get-OrchestratorStatus.ps1 tests/Test-DashboardServiceHealthContract.ps1
git commit -m "feat: expose service health in orchestrator status"
```
