---
name: source-driven-development
description: Use before making any code change — ensures the agent reads actual source before acting, preventing hallucinated paths, duplicate work, and contract violations.
---

# Skill: Source-Driven Development

Status: active
Scope: All implementation, config, and doc changes by agents in this repo.

## Purpose

Agents that act on assumptions instead of actual source produce patches for functions that
do not exist, configs that have already been changed, and docs that duplicate active contracts.
This skill enforces the operating condition: read first, always.

## Operating condition check

Before writing any code, config, or doc:

1. Read the exact file you plan to change — not a summary, not a guess at its contents.
2. Confirm the function, variable, or section you intend to modify actually exists.
3. Confirm no other agent has already made the change (check recent commits on the branch).
4. Confirm the change does not duplicate an active contract in `docs/`.

If any check fails, stop and surface to the operator. Do not proceed on assumption.

## Anti-redundancy rule

Per `AGENTS.md`:

> Do not create a doc, contract, or script that already exists under a different name.
> Read the repo before writing anything new.

Before creating any new file, search for:
- The filename in `docs/`, `scripts/`, `config/`, `skills/`.
- The concept in `docs/README.md` (canonical doc list).
- The function or tool in the MCP server (`scripts/Start-OrchMcpServer.ps1`).

## Source read order

For implementation tasks:

1. Read the task file for scope and acceptance criteria.
2. Read the specific source files listed in the task context.
3. Read any contract docs the task references (do not read the whole `docs/` dir).
4. Read the diff of the current branch before adding new changes.

For doc tasks:

1. Read `docs/README.md` canonical doc list.
2. Read the specific doc to be updated.
3. Check `docs/repo-structure-contract.md` for placement rules.

## Evidence of reading

Per `docs/agent-contract.md`, completion evidence must include at least one observable fact
derived from reading actual source. Examples:

- "Confirmed `Get-TaskTitle` at line 56 uses `Get-Content` without `-Encoding UTF8`."
- "Read `config/agents.json` — `gpt-web` slot `command.start` still references `claude` CLI."
- "Read `docs/README.md` line 44 — link target is `META-ORCHESTRATOR.md` (stale, now `meta-orchestrator.md`)."

Vague assertions ("I checked the code") are not evidence.

## Common violations

- Writing a new helper function that already exists in `scripts/`.
- Creating a new doc that overlaps with an active contract.
- Patching a function signature that was already changed in a recent commit.
- Claiming a file "should be" a certain way without reading it first.

## Reference docs

- `AGENTS.md` — anti-redundancy rule (section: "Before writing anything new")
- `docs/agent-contract.md` — evidence standard
- `docs/agent-start-here.md` — minimum required read order
- `docs/drift-prevention-contract.md` — rules for preventing duplication and drift
