# Architecture

## Components

### Orchestrator

`Start-GmAgentOrchestrator.ps1`

Loads project and agent configs, prepares worktrees, and starts one slot process per enabled agent.

### Slot runner

`Start-AgentSlot.ps1`

Claims one task, injects the agent contract into the assigned worktree, runs the configured agent command, watches output, and handles resume loops.

Slot metadata from `config/agents.json`, including `agent` and optional `role`, is passed into the runner. The runner records the role in `status/<slot>.json` and includes it in the agent prompt as execution-style guidance. Role metadata does not expand task scope, priority, or delegation authority; `TASK_QUEUE.md` remains the only source of assigned work.

The slot runner must treat source-control closure as part of successful completion. A task can move to done only after the agent has committed the scoped work, pushed the feature branch, opened a pull request, and recorded the PR reference in the handoff. Push or pull-request failures leave the task blocked or failed rather than done.

### Worktree manager

`New-AgentWorktree.ps1`

Creates one branch/worktree per agent slot so multiple agents do not stomp the same files.

## Runtime flow

```text
queue task exists
  -> slot claims task into active/
  -> worktree receives AGENT_RESUME.md + TASK_QUEUE.md
  -> agent starts with slot role metadata in prompt
  -> output streamed to logs/
  -> status/<slot>.json updated with slot, agent, role, state, reason, and next action
  -> if token/rate limited, sleep then resume
  -> agent commits scoped changes on its feature branch
  -> agent pushes the feature branch and opens a pull request
  -> agent records branch, commits, push state, PR, working tree, and validation in AGENT_LOG.md
  -> if source-control closure and validation succeed, move task to done/
  -> if push, PR creation, or validation fails, move task to blocked or failed/
```
