---
name: planning-and-task-breakdown
description: Use when decomposing a large request into queue tasks — produces correctly formatted task files with priority scoring, agent slot assignment, and acceptance criteria.
---

# Skill: Planning and Task Breakdown

Status: active
Scope: Creating and prioritizing task files for the `tasks/queue/` system in this orchestrator.

## Purpose

The orchestrator routes tasks by reading files from `tasks/queue/`. Tasks that are vague,
oversized, or missing acceptance criteria block dispatch and produce partial or wrong outputs.
This skill describes how to break a request into correctly scoped task files.

## Task file format

```markdown
# <Title — plain ASCII, under 80 chars, no em dashes>

Priority: P0|P1|P2
Slot: <agent-slot-name from config/agents.json>
Scope: <one sentence>

## Acceptance criteria

- [ ] <observable, specific, pass/fail criterion>
- [ ] <observable, specific, pass/fail criterion>

## Context

<Minimal context the agent needs. File paths, not summaries. Link to relevant docs.>

## Out of scope

<Explicit list of what this task must NOT touch.>
```

## Priority scoring

| Priority | Meaning | Examples |
| --- | --- | --- |
| P0 | Blocks all other work | MCP server down, encoding failure breaking status API, broken agent dispatch |
| P1 | High value, does not block | New feature in approved backlog, reliability improvement, doc cleanup |
| P2 | Nice-to-have, can wait | Research tasks, exploratory analysis, optional improvements |

Assign P0 only when the orchestrator or a critical path is genuinely blocked.

## Slot assignment

Consult `config/agents.json` for valid slot names. Current slots:

| Slot | Agent | Best for |
| --- | --- | --- |
| `claude-main` | Claude | Implementation, refactoring, doc writing, MCP work |
| `codex-main` | Codex | Code review, patch application, test writing |
| `gemini-main` | Gemini | Research, validation, synthesis, external data |
| `gemini-flash` | Gemini Flash | Fast research tasks, agent reliability ledger |
| `gpt-web` | GPT (browser) | Dashboard UX tasks, web-based validation, visual review |

## Breakdown rules

1. One task file = one slot assignment. Tasks that need two agents need two files.
2. Acceptance criteria must be observable, not inferred. "Code is cleaner" is not an observable criterion.
3. Keep context minimal — link to docs, do not copy them into the task file.
4. "Out of scope" is required for any task that touches shared infrastructure (MCP, orchestrator scripts, config).
5. Task titles must be plain ASCII. No em dashes, smart quotes, or special characters (encoding failure risk).
6. Task files use `.md` extension, `kebab-case` filenames.

## Breakdown smell check

Before writing a task file, confirm:
- Is this one agent, one slot, one coherent output?
- Can I write 2-4 specific pass/fail acceptance criteria?
- Is the scope small enough to complete in one agent session?
- Does it touch fewer than 5 files?

If any answer is no, split into smaller tasks.

## Reference docs

- `tasks/queue/` — live task queue
- `config/agents.json` — slot definitions
- `docs/agent-contract.md` — acceptance criteria and evidence standard
- `docs/dispatch-determinism-map.md` — dispatch routing logic and color-coded safety zones
- `docs/connector-queue-actions.md` — queue action contract
