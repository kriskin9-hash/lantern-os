---
name: research
description: Persisted, resumable long-running research tasks for Keystone chat, !convergance grounding, and autowork issue research. Fan-out web search + gap-driven multi-round refinement (Σ₀ Observe→Reason→Verify→Converge), state survives across chat turns and server restarts.
---

# Research

Status: production-ready
Scope: chat-triggered research tasks (`!research`, natural language), `!convergance` grounding, autowork issue research
Source: `apps/lantern-garage/lib/research-task.js`, `apps/lantern-garage/lib/wide-search.js`
Validation: exercised live in dev preview across multiple resumed turns (see PR history); `node --check` clean on all three call sites

## Simple Answer

One search answers one question. A research TASK keeps going — each round targets the gaps the last round left open — until either nothing's left to cover or a round ceiling is hit, and it survives across chat turns (and server restarts) because it's a plain JSON file, not in-memory state. This is the `Task` object (goal + status) CLAUDE.md's four-object model calls for, scoped to the research workload.

## What It Actually Does

- `createTask(topic, {sessionId})` — starts a task, persists `data/research-tasks/<id>.json` (`status: "running"`, empty `rounds`/`sources`/`gaps`).
- `runRound(task, onStep)` — one round: builds a query from the topic plus any open gaps, runs `wideSearch()` (fan out angled sub-queries → low-fidelity prune → high-fidelity cited synthesis), merges new sources into the task's deduped source pool, then asks a model what's still missing. Saves the task after every round.
- A task is `done` when the gap-check comes back empty or `MAX_TOTAL_ROUNDS` (default 8, env `RESEARCH_TASK_MAX_ROUNDS`) is hit.
- Three entry points share this one engine:
  - **Chat**: `!research <topic>` / `!research continue <taskId>`, or plain language ("research X", "look into X", "investigate X") — [stream-chat.js](../../apps/lantern-garage/lib/stream-chat.js) runs up to `RESEARCH_ROUNDS_PER_TURN` (default 3) rounds per HTTP turn, streams every stage live, and tells the user the resume command if the task isn't done yet.
  - **!convergance grounding**: [dream-chat.js](../../apps/lantern-garage/lib/dream-chat.js)'s `handleConvergenceCommand` runs up to 2 bounded rounds to ground its dream-synthesis claims, falling back to a single flat `webSearch()` on any error so a research-task problem never breaks convergence.
  - **Autowork issue research**: [autowork-research.js](../../apps/lantern-garage/lib/autowork-research.js)'s `researchIssue()` runs up to `AUTOWORK_RESEARCH_ROUNDS` (default 2) rounds instead of a single `wideSearch()` pass, so issues that need real investigation get more than a single-query skim.
- On completion, emits a Convergence Record (`reasoner: "research-task"` or `"wide-search"`) with full evidence (`evidence_ids` = source URLs, `verification_notes` = round/source counts) and ingests a CSF memory entry via `recordConvergance`.

## Evidence / Source Discipline

- Every claim in a task's final answer is expected to cite a numbered source `[n]`; `data/research-tasks/<id>.json` keeps the full source list (title, url, snippet, which sub-query found it) for audit.
- `data/convergence/records.jsonl` carries the terminal record once a task reaches `status: "done"` — `verified: confidence >= 0.5`, never asserted true by default.
- Confidence is NOT invented by the model: `wide-search`'s `_confidence()` derives it from pool coverage (kept/pooled ratio) and citation density (how many `[n]` refs actually appear in the answer), scaled down if the high-fidelity synthesis pass didn't run.

## Proven / Held / Local-Only

**Proven locally (dev preview, live requests):**
- `!research <topic>` and plain-language triggers both create and progress a task with live streamed stage progress.
- `!research continue <id>` resumes a task after the server restarted between turns; rounds and sources accumulate correctly across resumptions.
- A task correctly reaches `status: "done"` at the round ceiling and emits its Convergence Record.
- `!convergance` and autowork's `researchIssue()` both call into the same engine without introducing a circular require (lazy `require()` inside the calling function, same pattern `wide-search.js` already used for `autowork-research.js`).

**Held:**
- No UI surface lists in-progress/resumable tasks — resuming requires the user to have the exact task id from a prior reply. A `!research list` or sidebar affordance would close this gap.
- The gap-check model call is best-effort (`self-edit-engine`'s `callLlm`); if it's unavailable, a task always runs to `MAX_TOTAL_ROUNDS` rather than stopping early — this is intentional degradation, not a bug, but it means a misconfigured provider chain makes every task expensive.
- No de-duplication across DIFFERENT tasks on similar topics — two overlapping `!research` calls will re-search from scratch.

**Local-only boundary:**
- Task state lives entirely in `data/research-tasks/*.json` — no network calls beyond the existing `web-search-client.js` chain (MCP → DuckDuckGo → Wikipedia) and whatever LLM provider is selected for synthesis/gap-check.

## Next Safe Action

1. Try `!research <topic you actually want answered>` in dream-chat and watch the live round-by-round streaming.
2. If it stops with gaps still open, send `!research continue <taskId>` from the reply to keep it going.
3. Tune `RESEARCH_TASK_MAX_ROUNDS` / `RESEARCH_ROUNDS_PER_TURN` / `AUTOWORK_RESEARCH_ROUNDS` in `.env` if tasks are stopping too early or running too long for your use.
4. Check `data/convergence/records.jsonl` for `source: research-task/<id>` or `wide-search/research` entries to audit what a completed task actually grounded.

## Validation Path

- `node --check apps/lantern-garage/lib/research-task.js apps/lantern-garage/lib/stream-chat.js apps/lantern-garage/lib/dream-chat.js apps/lantern-garage/lib/autowork-research.js`
- Manual: dev preview, type `!research <topic>`, confirm staged progress streams and a `data/research-tasks/<id>.json` file appears; send `!research continue <id>` and confirm `rounds.length` grows.
- Manual: `!convergance <topic>` with dream entries present, confirm the record in `data/convergence/records.jsonl` carries `grounding_task_id`.
- Future: pytest/node:test coverage exercising `runRound()` with a mocked `wideSearch()` so the round-loop and gap-check-driven termination are covered without live network calls.

## Appendix: Task Schema

```json
{
  "id": "topic-slug-<base36-timestamp>",
  "topic": "the original topic string",
  "sessionId": "chat session id or autowork-issue-<n>",
  "status": "running | done",
  "rounds": [
    { "n": 1, "query": "...", "answerPreview": "...", "sourcesFound": 8, "confidence": 0.5, "gaps": ["..."], "at": "ISO timestamp" }
  ],
  "sources": [ { "n": 1, "title": "...", "url": "...", "snippet": "...", "via": ["..."] } ],
  "latestAnswer": "the most recent round's synthesized answer",
  "confidence": 0.61,
  "gaps": ["what the last round's gap-check flagged"],
  "createdAt": "ISO timestamp",
  "updatedAt": "ISO timestamp"
}
```

See also: `skills/convergence/SKILL.md` (the record-emission side this skill feeds), `apps/lantern-garage/lib/wide-search.js` (the per-round engine), `apps/lantern-garage/lib/autowork-research.js` (the autowork call site).
