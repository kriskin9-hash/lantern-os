---
name: context-engineering
description: Use when loading or preparing an agent session — ensures the right docs are read in the right order before any work begins.
---

# Skill: Context Engineering

Status: active
Scope: Agent session initialization and context loading for all agent types in this repo.

## Purpose

This repo has a defined context hierarchy. Agents that skip it produce hallucinated file paths,
duplicate work, and broken patches. This skill describes the correct load order and what each
layer provides.

## Context hierarchy

```
CLAUDE.md                          — P0 gate; Claude Code reads this at session start
  -> AGENTS.md                     — Root behavioral contract for all agents; read every session
    -> docs/README.md              — Hub map; routes to correct first-read by work type
      -> docs/agent-start-here.md  — Single canonical agent entry point
        -> docs/model-guides/<model>.md  — Model-specific behavior and safe operation rules
          -> assigned task file          — Concrete task scope and acceptance criteria
            -> docs/agent-contract.md   — Evidence, validation, handoff standards (on demand)
```

Each layer narrows scope. Do not skip ahead.

## Rules

1. Read `AGENTS.md` at the start of every session, including after context compaction.
2. Read only the model guide for your agent type. Do not read all model guides.
3. Read the task file before reading any source files.
4. Read source files narrowly — only what the task requires. Do not broad-scan.
5. Do not re-read layers you have already loaded unless the session was compacted.

## What each layer provides

| Layer | Provides |
| --- | --- |
| `CLAUDE.md` | Claude Code tool limits, repo root, MCP server URL, worktree isolation rules |
| `AGENTS.md` | Anti-redundancy rule, dispatch protocol, evidence standard, stop-after-one-task |
| `docs/README.md` | Fast-path table by work type; canonical doc list |
| `docs/agent-start-here.md` | Ordered read path, constraint list, what NOT to do |
| `docs/model-guides/<model>.md` | Per-model safe ops, known failure modes, output format |
| Task file | Scope, acceptance criteria, priority, agent slot |
| `docs/agent-contract.md` | Evidence format, validation requirements, handoff checklist |

## Common violations

- Reading the whole `docs/` directory instead of following the fast path
- Starting work before reading `AGENTS.md`
- Reading the wrong model guide
- Skipping the task file and guessing scope from context
- Re-loading context that was already loaded (wastes tokens, risks drift)

## Reference docs

- `AGENTS.md` — root behavioral contract
- `docs/agent-start-here.md` — canonical read order
- `docs/model-guides/` — per-model guides
- `docs/token-aware-agent-protocol.md` — token budget and context management rules
