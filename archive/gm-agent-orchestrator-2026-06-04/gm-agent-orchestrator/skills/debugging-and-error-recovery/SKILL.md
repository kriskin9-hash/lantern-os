---
name: debugging-and-error-recovery
description: Use when an agent, MCP tool, or PowerShell script returns an error — identifies the failure class and safe recovery path without destructive retries.
---

# Skill: Debugging and Error Recovery

Status: active
Scope: MCP JSON pipeline errors, PowerShell encoding failures, agent authentication errors, and queue state recovery in this orchestrator.

## Purpose

Most failures in this repo fall into one of six known classes. Identifying the class before
acting prevents cascading failures. This skill documents the classes, their signatures,
and the safe recovery path for each.

## Known failure classes

### 1. MCP JSON parse error (-32000)

Signature: `Invoke-JsonScript` returns `-32000` or `ConvertFrom-Json` throws at a specific character position.

Root cause: Non-ASCII character in a task title, agent log line, or file path — corrupted by PowerShell 5.1's
Windows-1252 default encoding when read via `Get-Content` without `-Encoding UTF8`.

Fix path:
1. Identify the offending file — check `Get-OrchestratorStatus.ps1 Get-TaskTitle` and any `Get-Content` call missing `-Encoding UTF8`.
2. Confirm the character: `[System.IO.File]::ReadAllBytes($path) | Where-Object { $_ -gt 127 }`.
3. Replace the non-ASCII character in the source file (em dashes `—` → ` - `, smart quotes → straight quotes).
4. Verify `Invoke-JsonScript` output parses cleanly before restarting the MCP server.

Defense in depth already applied:
- `Get-OrchestratorStatus.ps1`: `-Encoding UTF8` on all `Get-Content` calls.
- `Start-OrchMcpServer.ps1` `Invoke-JsonScript`: pre-JSON prefix stripper + ASCII sanitizer layer.

### 2. Stderr prefix contamination

Signature: `ConvertFrom-Json` fails on a string starting with a warning or progress line before the `{` or `[`.

Root cause: PowerShell subscripts write warnings or debug lines to stdout mixed with JSON output.

Fix: `Invoke-JsonScript` now strips everything before the first `{` or `[`. If output still fails,
check the subscript for `Write-Host` or `Write-Output` calls that emit non-JSON before the payload.

### 3. Agent authentication failure (401 / invalid API key)

Signature: Agent slot exits with `401 Unauthorized` or `invalid x-api-key`.

Root cause: `ANTHROPIC_API_KEY` is not set, is expired, or the slot-specific key env var
(`CLAUDE_<SLOT>_API_KEY`) has not been mapped.

Fix path:
1. Check `$env:ANTHROPIC_API_KEY` in the slot's launch environment.
2. Verify the system env var `CLAUDE_<SLOT_NAME_UPPER>_API_KEY` is set and current.
3. `Start-AgentSlot.ps1` maps slot-specific keys at launch — confirm it ran the mapping block.
4. Rotate the key at the provider console if expired.

### 4. Dirty worktree dispatch block

Signature: Orchestrator refuses to route a task; logs show "dirty worktree" or "uncommitted changes."

Root cause: Previous agent left uncommitted changes in the worktree branch.

Fix path (human only — do not auto-resolve):
1. Inspect the worktree: `git -C <worktree-path> status`.
2. If changes are recoverable: commit or stash them on the branch.
3. If changes are junk: `git -C <worktree-path> checkout -- .` (destructive — human confirms).
4. Re-route the task only after the worktree is clean.

Rule: Never dispatch to a slot with uncommitted changes. This is a hard blocker per `AGENTS.md`.

### 5. MCP server unreachable

Signature: `http://127.0.0.1:8787/api/status` returns connection refused or times out.

Fix path:
1. Check if `Start-OrchMcpServer.ps1` is running: `Get-Process | Where-Object { $_.Name -like '*pwsh*' -or $_.Name -like '*powershell*' }`.
2. Restart via the MCP tool `restart_mcp_server` or manually: `Start-Process pwsh -ArgumentList "-NoProfile -File scripts\Start-OrchMcpServer.ps1 -NoAuth"`.
3. Confirm `/health` returns `{"status":"ok"}` before routing tasks.

### 6. Queue state corruption

Signature: Task file appears in multiple state folders (`queue/`, `active/`, `done/`), or a task
that should be active is missing from `active/`.

Fix path:
1. Do not run multiple agents simultaneously against the same queue without isolation.
2. Identify where the task file actually is: `Get-ChildItem tasks/ -Recurse -Filter <task-id>*`.
3. Move it to the correct folder based on actual agent outcome (not assumed state).
4. Update `reports/queue-movements/` with a manual correction note.

## Reference docs

- `docs/mcp-connector-config.md` — MCP connector shape and auth
- `docs/mcp-connector-health.md` — Health check patterns
- `docs/operator-runbook.md` — Full recovery runbook
- `docs/safe-powershell-runner.md` — Safe PowerShell execution rules
- `scripts/Start-OrchMcpServer.ps1` — `Invoke-JsonScript` implementation
- `scripts/Get-OrchestratorStatus.ps1` — Task title extraction
