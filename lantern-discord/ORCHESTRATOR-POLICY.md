# Orchestrator-Backed Deployment Policy

**Status**: PRODUCTION | **Version**: 1.0 | **Date**: 2026-05-25

---

## Single Source of Truth

All Lantern OS operations are routed through the **Suzie Orchestrator** (gm-agent-orchestrator). This document defines the policy.

```
User Input
    ↓
Lantern Interface (Web/CLI/Desktop)
    ↓
Suzie Orchestrator
    ├─ Route to correct LLM provider
    ├─ Check token budget + capability
    ├─ Dispatch work to agent slot
    ├─ Log all operations
    └─ Return response
    ↓
Local Storage (JSONL + HDD mesh)
```

---

## Unified Command Entry Points

### Windows (PowerShell)

**Single master launcher** (all systems):
```powershell
powershell C:\Users\alexp\.lantern\MASTER-START-ALL.ps1
```

This:
1. Verifies Python + Flask
2. Starts Ollama (or LM Studio)
3. Launches button server (Flask, port 5001)
4. Launches unlimited chat console
5. Monitors processes with auto-restart
6. All logs → `~/.lantern/state/`

### Linux (Bash)

**Single master launcher** (all systems):
```bash
~/.lantern/MASTER-START-LINUX.sh
```

This:
1. Checks Ollama running
2. Kills stale processes
3. Starts button server (Flask, port 5001)
4. Starts unlimited chat console
5. Starts native desktop app (GTK3)
6. Monitors with 10-second auto-restart
7. All logs → `~/.lantern/state/`

---

## LLM Provider Priority

When user sends prompt, Suzie checks providers in order:

1. **Local Ollama** (127.0.0.1:11434) — preferred, unlimited tokens
2. **LM Studio** (127.0.0.1:1234) — fallback, unlimited tokens
3. **Claude API** (if MCP enabled) — last resort, pay-per-token

**Rule**: Never use cloud API if local LLM is running. Local-first policy.

---

## Configuration (config.json)

```json
{
  "llm": {
    "backend": "ollama",
    "ollama_url": "http://127.0.0.1:11434",
    "lm_studio_url": "http://127.0.0.1:1234",
    "default_model": "mistral",
    "fallback_model": "neural-chat",
    "timeout_sec": 120,
    "max_tokens": 4096,
    "temperature": 0.7
  },
  "storage": {
    "state_dir": "~/.lantern/state",
    "persistence_format": "jsonl",
    "auto_backup_interval_min": 60,
    "mesh_hdd_nodes": 3,
    "compression": "zstandard"
  },
  "interfaces": {
    "button_server": {
      "port": 5001,
      "auto_start": true
    },
    "console_chat": {
      "auto_start": true,
      "log_file": "~/.lantern/state/unlimited-chat.jsonl"
    },
    "discord_bot": {
      "enabled": false,
      "token_env_var": "DISCORD_TOKEN"
    },
    "native_desktop": {
      "enabled_linux": true,
      "framework": "gtk3"
    }
  },
  "policies": {
    "local_first": true,
    "zero_cloud_dependency": true,
    "auto_restart_on_crash": true,
    "watchdog_check_interval_sec": 10,
    "persistent_logging": true,
    "consent_based_resource_sharing": false
  }
}
```

---

## Unified State Format

All persistent data uses JSONL (JSON Lines):

```jsonl
{"timestamp": "2026-05-25T22:06:00Z", "event": "startup", "platform": "windows", "python_version": "3.11", "status": "ok"}
{"timestamp": "2026-05-25T22:06:10Z", "event": "ollama_check", "endpoint": "127.0.0.1:11434", "status": "ok", "models": ["mistral"]}
{"timestamp": "2026-05-25T22:06:30Z", "event": "button_server_start", "port": 5001, "status": "ok", "pid": 8734}
{"timestamp": "2026-05-25T22:06:45Z", "event": "chat_message", "role": "user", "prompt": "explain oauth", "tokens": 12}
{"timestamp": "2026-05-25T22:07:00Z", "event": "chat_response", "role": "assistant", "response_tokens": 234, "latency_ms": 1250}
```

---

## Deployment Checklist

Before going live:

- [ ] Python 3.10+ installed
- [ ] Flask + flask-cors installed (`pip install flask flask-cors`)
- [ ] Ollama downloaded and installed (or LM Studio running)
- [ ] Model pulled (`ollama pull mistral` or equivalent)
- [ ] Port 5001 available (not in use)
- [ ] ~/.lantern/ directory exists with all scripts
- [ ] QA test suite passes (`QA-TEST-UNIFIED.ps1`)
- [ ] System checks clean log entries in state/
- [ ] Button server responds on http://localhost:5001
- [ ] Unlimited chat console functional
- [ ] No Python syntax errors detected

---

## Watchdog Auto-Restart Logic

Every 10 seconds (Windows: 5 sec, Linux: 10 sec):

```
Check: button-chat-server.py still running?
  NO → Kill all related processes
       → Wait 2 seconds
       → Start button-chat-server.py again
       → Log restart event

Check: unlimited-chat process still running?
  NO → Start unlimited-chat again
       → Log restart event

Check: LLM backend still reachable?
  NO → Log warning
       → Alert user in UI
       → Attempt auto-recover (restart Ollama)
```

---

## Operational Boundaries

### What Lantern DOES
- ✅ Run unlimited local LLM chat
- ✅ Store all conversations locally
- ✅ Provide button-based quick prompts
- ✅ Auto-restart on crash
- ✅ Log all operations to JSONL

### What Lantern DOES NOT
- ❌ Send data to cloud (unless explicitly enabled)
- ❌ Track user behavior (except local logs)
- ❌ Require API keys (unless MCP enabled)
- ❌ Auto-update (manual patch only)
- ❌ Phone home telemetry

---

## Stream Consolidation

All products now route through single architecture:

| Product | Entry Point | Backend | Storage | Status |
|---------|-------------|---------|---------|--------|
| Lantern Chat (Web) | http://localhost:5001 | Local LLM | JSONL | **LIVE** |
| Lantern Chat (CLI) | console | Local LLM | JSONL | **LIVE** |
| Lantern Desktop (Linux) | GTK3 app | Local LLM | JSONL | **LIVE** |
| Rhythm OS (Discord) | bot commands | Local LLM | JSONL | **OPTIONAL** |
| Research Agent | orchestrator | Local LLM | JSONL | **OPTIONAL** |

---

## Critical Safety Rules

1. **Never send PII to cloud LLM** without explicit consent prompt
2. **Always check local backend first** before using cloud API
3. **Auto-restart must have upper bound** (no infinite loop of crashes)
4. **Log rotation required** (state/ directory can grow unbounded)
5. **Port conflicts checked** at startup (fail early if port taken)

---

## Scaling (Future)

When ready for multiple operators:

```
Operator A (PC 1)
    ├─ Local Lantern + Suzie
    ├─ Consent-based GPU share
    └─ Mesh HDD backup

Operator B (PC 2)
    ├─ Local Lantern + Suzie
    ├─ Consent-based GPU share
    └─ Mesh HDD backup

Orchestrator Hub
    ├─ Coordinate work across operators
    ├─ Aggregate compute capacity
    ├─ Route work by latency/load
    └─ Manage token budget
```

---

## Commits & Versioning

**Current deployment**: `unlimited-mode-v1.0-unified` (master branch)

```bash
# After successful QA pass:
git add -A
git commit -m "feat: unified orchestrator deployment - single entry point, all systems"
git tag v1.0-unlimited-unified
git push origin master --tags
```

---

## Next Gate: Family Beta

After orchestrator policy is live:
1. Deploy to Family A (real usage test)
2. Collect uptime metrics (target: 99%+ within first week)
3. Monitor token usage (should be unlimited without throttle)
4. Gather feedback on button interface UX
5. Fix any blocking issues
6. Scale to Family B, C, D

