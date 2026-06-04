# ORCH MVP Stopgap

## Goal

Get the orchestrator running well enough to unblock game MVP work. Defer broad cleanup, old PR mining, connector polish, dashboard polish, and non-critical enforcement until an agent can take a game task from queue to clean handoff.

## Temporary policy

Agents should proceed without manual approval unless they hit one of these blockers:

- Credentials or login are missing.
- A destructive operation is required.
- A local tool is missing or broken.
- The task requires a product/design decision.
- The worktree contains unexpected user or unrelated agent edits.

If blocked, stop with a concise blocked handoff and one concrete recovery step. Do not repeatedly ask for permission or expand scope.

## MVP checklist

- Dashboard starts locally and shows queue, active task, agent status, and changed files.
- At least one enabled slot can claim a queued task.
- The slot writes logs and `AGENT_LOG.md`.
- The slot runs the cheapest configured validation or clearly reports why validation cannot run.
- The task ends as done, failed, or blocked with a clear next action.
- Game MVP tasks can be added by dropping one Markdown file into `tasks/queue`.

## Run order

1. Pull latest `master` locally.
2. Start the dashboard.
3. Run one enabled slot with `-RunOnce`.
4. Inspect dashboard and latest slot log.
5. Fix only the first blocker that prevents a game task from running.

## Local commands

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-Dashboard.ps1
```

In another terminal, run one available slot:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-GmAgentOrchestrator.ps1 -SlotName claude-main -RunOnce
```

If Gemini is the available slot:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-GmAgentOrchestrator.ps1 -SlotName gemini-main -RunOnce
```

## Deprioritized until unblocked

- Old conflicted PRs unless they directly fix the first runtime blocker.
- Read-only MCP connector polish.
- Dashboard redesign beyond showing current task, slot state, logs, and changed files.
- Strict process enforcement that prevents a useful blocked handoff.
