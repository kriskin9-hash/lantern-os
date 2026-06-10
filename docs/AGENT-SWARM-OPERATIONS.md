# Agent Swarm Operations — Convergence IO + Dream Journal

**Status:** operational doctrine (candidate)
**Date:** 2026-06-09
**Goal:** keep the agent swarm deterministically producing work on the two priority streams — **Convergence IO** and **Dream Journal** — with human oversight at every promotion point.

This builds on what already exists: agent lanes (AGENTS.md), `.claude/agent-slots.json`, monoworkstream hooks, the Convergence Loop (docs/CONVERGENCE-LOOP.md), and the Dream Journal roadmap (docs/DREAM-JOURNAL-ROADMAP.md). Nothing here replaces those — this is the scheduling layer on top.

---

## Core principle: deterministic means queue-driven, not prompt-driven

Agents drift when they pick their own work. They stay on-target when work arrives as a queue they cannot reorder. The entire strategy is three rules:

1. **All work enters as a GitHub issue** labeled `convergence-io` or `dream-journal`, with a priority label (`p0`/`p1`/`p2`). No issue, no work. (This matches the existing rule: design contracts in CSF require issues before implementation.)
2. **Each agent lane pulls the top issue from its assigned stream** — never browses, never invents. Lane assignment is fixed in the table below and only a human edits it.
3. **Nothing merges without a human.** The monoworkstream hooks already enforce one open PR per lane and block direct master pushes — the human review of that single PR per lane *is* the oversight gate.

## Lane assignment (deterministic routing)

| Lane | Stream | Work type |
|---|---|---|
| `claude/` | Dream Journal | features, lore/game systems, docs |
| `gemini/` | Convergence IO | routing, batching, loop mechanics (matches gemini-first slots config) |
| `codex/` | Convergence IO | tests, validation, bug fixes |
| `devin/` / `grok/` / `openai/` | flex pool | overflow from either stream, human-assigned only |

One lane = one stream = one open PR. An agent that finishes its issue takes the next top issue *in its own stream*. Cross-stream moves require a human relabeling the issue.

## The daily loop (time-efficient human oversight: ~15 min/day)

**Morning (human, 10 min):**
1. Review open PRs — one per lane, so at most 6. Merge, request changes, or close.
2. Triage new issues: add stream + priority labels. Unlabeled issues are invisible to agents.
3. Glance at `queue_status` (MCP server) for stuck lanes.

**During the day (agents, autonomous):**
- Pull top issue in stream → branch on own lane → implement → run the safe pytest subset + `make check-node` → open PR → ingest a CSF session note to `csf/ingest/` → stop. No second PR until the first is closed.

**Evening (human, 5 min, optional):**
- Skim CSF ingest notes from the day's sessions; quarantine anything that promoted symbol → doctrine without passing the LORE.md gate.

## Determinism guards

- **Issue templates** for both streams with required sections (acceptance criteria, files touched, test command). Agents implement the criteria, nothing more.
- **Definition of done is mechanical:** tests pass, `node --check` passes, PR references issue number, CSF note ingested. The slop-commit hook already rejects junk messages.
- **Timeboxing:** if an issue isn't PR-ready in one session, the agent posts a checkpoint comment on the issue and stops — no sprawling multi-day branches.
- **No self-promotion:** agents never label issues, never edit this file, never edit `.claude/agent-slots.json`, never merge.

## Oversight escalation (when to interrupt the human)

Agents tag a PR `needs-founder` when work touches: security (SECURITY.md items), provider keys/config, lore canon (lore/ directory, per the LORE.md promotion gate), money/pricing, or anything destructive to `data/`.

## One reversible next action

Create the two issue labels and one issue template, then route this week's existing open issues (#292–#301 are already a natural Dream Journal queue). Everything else above activates lane by lane as PRs cycle — and this doc can be deleted to revert.
