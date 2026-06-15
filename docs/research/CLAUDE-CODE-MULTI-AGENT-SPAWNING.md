# Claude Code Multi-Agent Spawning — Validation (#519)

**Claim under test:** *"Claude Code can autonomously spawn and coordinate multiple
sub-agents that work on different parts of a task simultaneously."*

**Verdict: VERIFIED — real and generally available in Claude Code (the agent
harness), not a future capability.** It is a *harness/SDK* capability, not an
intrinsic property of the Claude model or the raw Claude API. Confidence: high
(direct, in-environment evidence — this repo's own session ran it).

---

## What was checked (each row: claim · evidence · confidence)

| Sub-claim | Evidence | Confidence |
|---|---|---|
| 1. Create multiple sub-agents for parallel work | The **`Agent` tool** spawns a subagent (`subagent_type`, `run_in_background`). The **`Workflow` tool** orchestrates many subagents via `parallel(thunks)` (barrier) and `pipeline(items, …stages)` (no barrier). Concurrency is capped at `min(16, cores−2)` running at once; up to **1000 agents per workflow** lifetime; ≤4096 items per fan-out call. | High |
| 2. Assign subtasks automatically | The orchestrator (lead) authors per-agent prompts in a deterministic script; each `agent(prompt, {schema})` call can force structured output. Subtasks are assigned by the script's control flow (loops/conditionals/fan-out). | High |
| 3. Merge results back to the lead | A subagent's **final message is returned to the orchestrator** as the tool result (`Agent` result text, or `Workflow` `agent()` return — raw text or schema-validated object). The lead synthesizes. | High |
| 4. Maturity: PoC / beta / GA? | **GA in Claude Code.** Subagent types ship today (`general-purpose`, `Explore`, `Plan`, `statusline-setup`, custom `.claude/agents/*`). Background agents (`run_in_background`) and worktree isolation (`isolation: "worktree"`) are live. | High |

### Direct in-repo evidence (ground truth, not docs)
This session executed it on this repository:
- A **17-agent `Workflow`** (verify → adversarial-refute → synthesize → rewrite) validated the Σ₀ certificate — see `project_sigma0_certificate` history / PR #473. Recorded cost: **~975k output tokens across 17 agents**.
- An autonomous delegation loop spawned/operated per-lane work serially.

That measured cost is *why* this repo's token-reduction strategy prefers direct
local tools over fan-out: multi-agent spawning is real **and expensive** — each
subagent re-loads context cold. Use it for genuine parallel decomposition or
adversarial verification, not for work one context can do directly.

## Scope / honest boundaries
- **Claude Code (harness/CLI/SDK): YES, GA.** Spawning + coordination + result merge are first-class.
- **Raw Claude API (messages endpoint): NO auto-spawn.** The API returns one assistant turn; multi-agent orchestration is something you *build on top* using the **Claude Agent SDK** (the same machinery Claude Code uses).
- "Autonomous" = the lead agent decides when to fan out and how to recombine; it is deterministic orchestration authored by the lead, not emergent swarm behavior.

## Acceptance criteria (#519)
- [x] Independent verification of Claude Code capabilities (in-environment, 2026-06).
- [x] Capability maturity stated: **GA** (harness), **build-it-yourself via SDK** (raw API).
- [x] Examples/tests: the `Agent` and `Workflow` tools; this session's 17-agent workflow (PR #473).
- [x] Result: claim **VERIFIED** — posted to EPIC #509 via this issue's closure.

> Citation note: exact public-doc URLs (Claude Code "subagents", Agent SDK) should
> be confirmed before external publication; the evidence above is grounded in the
> live tool surface of this environment and this session's measured runs, not on
> fetched URLs.
