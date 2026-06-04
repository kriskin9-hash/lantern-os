# Dashboard / Status Snapshot 001

Status: template, awaiting fresh redacted snapshot  
Purpose: answer "What did the system show while running?"

---

## Snapshot metadata

| Field | Value |
|---|---|
| Date/time | TODO |
| Branch | TODO |
| Commit | TODO |
| Capture type | dashboard screenshot / status JSON / both |
| Redactions | TODO |

---

## Candidate command

```powershell
cd "C:\Users\alexp\Documents\gm-agent-orchestrator"
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Get-OrchestratorStatus.ps1 -Root .
```

If using dashboard UI, attach or reference a redacted screenshot path and describe what is visible.

---

## Snapshot excerpt

```json
{
  "TODO": "paste redacted status JSON or screenshot notes"
}
```

---

## What to verify

| Signal | Expected evidence | Result |
|---|---|---|
| Queue counts | queued/active/done/failed counts or equivalent | TODO |
| Agent slots | enabled/disabled/asleep/blocked state | TODO |
| Provider capacity | rate-limit/quota/preflight state if available | TODO |
| MCP/control plane | local status or exposed tool status | TODO |
| Dashboard/service health | healthy/degraded/error with reason | TODO |
| Failure context | errors include actionable context | TODO |

---

## What this proves

TODO after snapshot is captured.

---

## What this does not prove

- long-running uptime;
- production-grade monitoring;
- complete alerting;
- multi-user or remote observability.
