### Persisted, resumable research tasks — wired into chat, !convergance, and autowork

A single `wideSearch()` pass answers one question; a real research job needs to keep going
until it's actually done. Added `lib/research-task.js`: a persisted `Task` object
(`data/research-tasks/<id>.json`) that runs the Observe→Reason→Verify→Converge loop round
after round — each round targets the gaps the last one left open — until the gap-check comes
back empty or a round ceiling is hit (`RESEARCH_TASK_MAX_ROUNDS`, default 8). State survives
across chat turns and server restarts, so a long task doesn't have to finish in one HTTP request.

Three entry points now share this one engine instead of three separate ad-hoc searches:

- **Keystone chat**: `!research <topic>` / `!research continue <taskId>`, or plain language
  ("research X", "look into X", "investigate X") — `stream-chat.js` runs up to
  `RESEARCH_ROUNDS_PER_TURN` (default 3) rounds per turn, streams every stage live, and tells
  the user the resume command if the task isn't done.
- **`!convergance` grounding**: both the streaming council path (`stream-chat.js`) and the
  dream-synthesis path (`dream-chat.js`'s `handleConvergenceCommand`) now ground their claims
  in a bounded 1-2 round research task instead of one flat `webSearch()` call, falling back to
  the old single-search behavior on any error.
- **Autowork issue research**: `autowork-research.js`'s `researchIssue()` runs up to
  `AUTOWORK_RESEARCH_ROUNDS` (default 2) rounds instead of a single `wideSearch()` pass.

Every completed task emits a Convergence Record (`reasoner: "research-task"` /
`"convergance-council"` with a `grounding_task_id`) and a CSF memory entry. Documented as a real
implemented skill: `skills/research/SKILL.md`, registered in `SKILLS.md`.

Verified live in the dev preview: multi-round `!research` runs, cross-turn resume via
`!research continue <id>`, natural-language triggering, and grounded `!convergance` council
answers — all confirmed against real task-state files and `data/convergence/records.jsonl`.

`data/research-tasks/` is gitignored (runtime state, unbounded growth, same treatment as
`data/autowork-runs/`).
