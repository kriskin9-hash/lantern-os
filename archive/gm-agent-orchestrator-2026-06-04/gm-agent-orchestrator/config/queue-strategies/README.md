# Queue strategies

Queue strategies are human-editable policy files for tuning how the orchestrator prioritizes, routes, and moves tasks.

They are intentionally data files rather than hardcoded logic so Alex can optimize behavior without editing runner scripts.

## Default strategy

`default.cost-optimized.json` is the default queue strategy.

Its goals are:

- minimize paid-token usage
- prefer local/free read-only routing for classification, summarization, routing, status, and log review
- use free-tier agents for low-risk docs/status/queue maintenance when safe
- reserve paid/high-context agents for implementation, complex debugging, and high-context review
- stop repeated same-cause retries that burn tokens without progress
- make routing and movement reasons visible in status/dashboard output

## Editing rules

Keep strategy files conservative:

1. Do not route secrets, credentials, billing, production, or deployment work automatically.
2. Do not route code-edit tasks to local read-only models.
3. Keep repeated same-cause failures in `human_review` until the blocker is fixed.
4. Prefer adding a new rule over changing the meaning of an existing rule ID.
5. Treat `movementPolicy.forbidOverwrite` and `movementPolicy.forbidPathTraversal` as required safety defaults.

## Runtime shape

A strategy should expose:

- `name`
- `version`
- `costMode`
- `preferredOrder`
- `rules[]`
- `movementPolicy`
- `statusFields`

Future dashboard/status integrations should show:

- active strategy name
- cost mode
- routing reason
- queue movement reason

## Runtime flags

The default strategy now documents two operator flags used by runtime scripts:

- `ORCH_URGENT_ONLY=1`: claim/recommend only urgent/P0 queue items.
- `ORCH_CODEX_TOKEN_SAVER=1`: use compact prompt style for `codex-main` to reduce token burn.
