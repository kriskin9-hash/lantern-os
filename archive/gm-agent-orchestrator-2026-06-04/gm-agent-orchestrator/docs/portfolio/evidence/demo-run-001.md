# Demo Run 001

Status: template, awaiting fresh local dry-run transcript  
Purpose: answer "Did it actually run?" without mutating queue state or starting agents.

---

## Run metadata

| Field | Value |
|---|---|
| Date/time | TODO |
| Machine | TODO, redacted |
| Branch | TODO |
| Commit | TODO |
| Operator | TODO |
| Mode | Dry-run / read-only |

---

## Safety constraints for capture

The demo run must not:

- start agents;
- move queue files;
- write to `active`, `done`, or `failed`;
- trust remote MCP/tunnel state without local verification;
- print secrets or full environment dumps.

---

## Candidate command sequence

Use exact commands after local inspection confirms they are safe on the current branch.

```powershell
cd "C:\Users\alexp\Documents\gm-agent-orchestrator"
git status --short
git branch --show-current
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Get-OrchestratorStatus.ps1 -Root . | ConvertFrom-Json | Out-Null
powershell -NoProfile -ExecutionPolicy Bypass -File .\tests\Test-PowerShellSyntax.ps1 -Root .
```

Optional only if confirmed read-only:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tests\Test-OrchMcpServerContracts.ps1 -Root .
powershell -NoProfile -ExecutionPolicy Bypass -File .\tests\Test-OrchestratorStatusJson.ps1 -Root .
```

---

## Transcript

Paste redacted command output here.

```text
TODO: paste output
```

---

## Result

| Check | Result | Evidence |
|---|---|---|
| Repo inspected before run | TODO | TODO |
| Status command completed | TODO | TODO |
| Syntax test completed | TODO | TODO |
| MCP route contract completed | TODO | TODO |
| Queue state unchanged | TODO | TODO |
| No agent startup | TODO | TODO |

---

## What this proves

TODO after transcript is captured.

Possible proof points:

- local repo path and branch were inspected;
- status JSON path works;
- contract tests execute on Windows/PowerShell;
- demo stayed read-only.

---

## What this does not prove

- production auth;
- concurrent queue locking;
- multi-agent dispatch reliability;
- remote tunnel safety;
- long-running uptime.

---

## Follow-up evidence needed

- dashboard screenshot or JSON snapshot;
- queue transition example;
- failure/recovery example;
- latest CI run link/output.
