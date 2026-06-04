# LM Studio Preflight Lane

## Purpose

`lm-studio` is the user-facing local preflight lane for token reduction. It is not a coding executor and must not be routed autonomous shell, edit, deploy, secret, commit, or filesystem mutation work.

The lane is for cheap read-only preflight work before a premium or implementation agent is used.

## Naming

- User-facing slot / agent name: `lm-studio`
- Product display name: `LM Studio`
- Internal provider key: `lmstudio`
- Default base URL: `http://localhost:1234/v1`
- Default model: `lfm2-24b-a2b`
- Default mode: `read_only`

Keep `lmstudio` as the provider key for `scripts/Setup-LocalAgent.ps1`; use `lm-studio` in status, dashboard, task packets, and operator-facing docs.

## Allowed local preflight tasks

- classification
- summarization
- routing
- code explanation
- log summary
- task packet compression
- fake or stall response classification

## Blocked task classes

`lm-studio` must deny or escalate tasks that ask for:

- PowerShell, shell, or command execution
- code edits or file writes
- commits, pushes, merges, rebases, or branch mutation
- deploys, releases, rollbacks, migrations, or production access
- secrets, credentials, tokens, passwords, or private keys
- destructive filesystem operations

Denied tasks should route to `human_review`, `codex-main`, or `claude-main` depending on risk and current availability.

## Local setup

```powershell
cd C:\Users\alexp\Documents\gm-agent-orchestrator

Test-NetConnection localhost -Port 1234

.\scripts\Setup-LocalAgent.ps1 -Provider lmstudio -Model lfm2-24b-a2b
```

The provider setup command intentionally uses `lmstudio`, not `lm-studio`, because `lmstudio` is the internal provider key.

## Policy-only validation

This validation does not require a running LM Studio server:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tests\Test-LocalRouterPolicy.ps1
```

It must prove that read-only summarization can stay local, while edit, command, and high-risk tasks are denied or escalated.

## Live validation

Only after LM Studio is running locally:

```powershell
.\scripts\Invoke-LocalRouter.ps1 -Task 'Classify this task: summarize logs from a failed MCP connector validation run.'

.\scripts\Invoke-LocalRouter.ps1 -Task 'Run PowerShell to restart MCP on port 8787.'
```

Expected behavior:

- The first command may route to `local` if the model is available and returns valid policy JSON.
- The second command must deny local execution because it asks to run PowerShell.

## Evidence boundary

GitHub CI can prove the policy-only routing contract and documentation/config naming. It cannot prove the workstation LM Studio server is running. Live server connectivity remains a local-machine validation step.