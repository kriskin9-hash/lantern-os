# Local Agent Routing Policy

## Primary local model

Use LFM2-24B-A2B local for repeated low-risk agent steps when a local OpenAI-compatible endpoint is available.

## Purpose

Local inference is the preferred path for tasks that are read-only, repetitive, and low risk. The goal is to reduce paid-token burn while keeping high-risk work gated by review.

## Allowed task classes

- classify request type
- summarize logs
- summarize retrieved files
- choose the next tool from an allowlist
- rewrite prompts
- extract structured fields
- generate short implementation plans
- explain low-risk code

## Disallowed task classes

- production code edits
- security-sensitive changes
- dependency upgrades
- deployment
- deleting files
- modifying credentials
- financial, legal, or medical decisions
- autonomous multi-step execution without an external orchestrator budget

## Execution limits

Initial defaults:

- max input tokens: 8192
- max output tokens: 1024
- temperature: 0.1
- max local retries: 1
- mode: read-only
- shell execution: disabled
- file writes: disabled unless a separate reviewed implementation path performs them

## Routing order

1. Route low-risk read-only work to local LFM2.
2. Retry once only if the local model returns invalid JSON.
3. Escalate medium-risk work to premium review or a human.
4. Keep Amp in initializing status until its Windows/WSL path is intentionally enabled.
5. Do not route high-risk work to a local autonomous path.

## Required output contract

Local routing responses should be valid JSON using this shape:

```json
{
  "task_type": "classification|summarization|routing|code_explanation|code_edit|security|deployment|unknown",
  "risk": "low|medium|high",
  "route": "local|amp_initializing|premium|human_review",
  "reason": "short reason",
  "allowed": true
}
```

## RC2 Agentic Routing Contract

All RC2 queue tasks must carry routing metadata:

- `role_owner`: `gpt|codex|claude|gemini|human`
- `fallback_owner`: `gpt|codex|claude|gemini|human`
- `risk_class`: `low|medium|high|blocked`
- `budget_class`: `light|medium|heavy|restricted`
- `terminal_rule`: `done|failed|requeued|blocked`

If metadata is missing, the task must not be dispatched and should be routed to `human_review`.

### Assignment policy

- GPT: orchestration setup, policy/runbook work, queue shaping, status and evidence workflows.
- Codex: narrow patch and validation fixes only, medium-light scope.
- Claude: fallback fixes and final conformance pass only when wake/preflight is safe.

### Codex sticky approval policy

Codex dispatch requires an auditable approval record, with:

- scope (repo + task class),
- TTL expiry time,
- approval reference id.

Codex tasks without a valid approval record must not start and must be requeued or blocked with evidence.

### Pre-dispatch gates

Before claiming a task:

1. `tasks/active` count must be `0`.
2. selected slot worktree must have no unexpected tracked diffs.
3. task metadata and validation commands must be present.
4. Codex task must have valid sticky approval record.
5. Claude task must pass wake-safe preflight, else requeue/blocked with reason.
