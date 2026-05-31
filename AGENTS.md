# AGENTS

Status: active agent instruction file  
Repo: Lantern OS v1.0.0 staging  
Style spine: `docs/ORION-MOOKMANREPORT4-STYLE.md`

---

## Simple Answer

Agents working in this repo should make Lantern OS clearer, safer, and easier to validate.

Every change should move raw material toward an Orion-style technical sheet: clear purpose, real evidence, held boundaries, next action, and validation path.

---

## Operating Rules

- Inspect before editing.
- Keep changes small and reviewable.
- Do not import dirty worktree state blindly from source repos.
- Do not mutate boot configuration, partitions, firmware boot order, or disks.
- Do not claim v1.0.0 readiness without operator approval.
- Use the Innovator evidence method for promotion decisions.
- Do not stop at skeletons. If a loop finds actionable local issues, fix the first 2-4 before starting new expansion work.
- Retire deprecated surfaces as an explicit convergence step.
- Apply the Orion / Mookman Report 4 style to public-facing Markdown, flat text, and CSS.

---

## Source Repos

```text
C:\tmp\human-flourishing-frameworks-scan
C:\Users\alexp\Documents\gm-agent-orchestrator
```

Both may be dirty. Treat their working tree state as evidence, not as something to overwrite or reset.

---

## Promotion Criteria

An artifact can move into this repo when it has:

- source path;
- purpose;
- claim IDs or clear claim summary;
- validation status;
- blockers and rollback notes;
- operator approval status;
- human-readable first screen;
- no raw filepath spam above the first explanation.

---

## Flat Document Shape

Use this order for public-safe `.md` and `.txt` files unless the file has a stronger operational structure:

1. title;
2. short metadata block;
3. simple answer;
4. what it actually does;
5. evidence / source discipline;
6. proven / held / local-only;
7. next safe action;
8. validation path;
9. appendices, raw commands, paths, and receipts.

---

## CSS Surface Shape

For static surfaces, use the Orion style:

- limestone / warm white paper;
- thin blue grid lines;
- teal/cyan status accents;
- amber held-state accents;
- rounded technical panels;
- visible focus outlines;
- no fake active buttons;
- disabled controls clearly marked as local-only or held.

---

## Required Loop

Before meaningful work, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Invoke-LanternConvergenceLoop.ps1
```

Then handle the first 2-4 reported issues in priority order. If an issue cannot be fixed safely, mark it held in `manifests/open-issues.md` with the reason.

---

## Branching

Use `codex/` branch names for agent work unless the operator asks otherwise.

---

## Kalshi Connector — Agent Boundary

**App:** `apps/lantern-trade-chat/` — FastAPI, GitHub OAuth, RSA-PSS signing.
**Registry:** `data/automation/mcp-canary-results.json` → id `kalshi-public-markets`.

### What agents MAY do (operator-approved 2026-05-31 — EXPLICIT LIVE APPROVAL GIVEN)

- Read `apps/lantern-trade-chat/app/kalshi.py` and `app/main.py` to understand the client.
- Call read-only methods via the running app's `/api/status` endpoint (requires login):
  - `account_connectivity` — credentials present and reachable
  - `open_orders` — resting orders only
  - `open_positions` — current holdings
  - `recent_fills` — last 20 executed trades
  - `settlement_warnings` — voided, disputed, or pending settlements flagged automatically
- Run read-only balance checks against **demo** or **prod** environment (operator approval on file).
- Update `data/automation/mcp-canary-results.json` `checkedAt` field after a successful status check.

### Environment variables required to call the API

```text
KALSHI_API_KEY_ID       — API Key ID from Kalshi dashboard
KALSHI_PRIVATE_KEY      — RSA private key PEM (full text, newlines preserved)
KALSHI_ENVIRONMENT      — demo (default, safe) | prod (real money)
LANTERN_LIVE_ENABLED    — 0 (default) | 1 (arms live order submission)
```

### Platform-risk note

Public coverage as of March 2026 flags regulatory/settlement disputes on Kalshi
(Khamenei-related market payout). Before routing meaningful capital, check
`settlementWarnings` in `/api/status` and review the Kalshi terms for the
specific market. This is not investment advice.

---

## Dream Journal — Naming Convention

**Feature:** Local-first symbolic journal for reflection and pattern tracking.

### Names are equivalent

The following names refer to the same feature:

- **Dream Journal** — Dashboard panel name (`dashboard/index.html` → panel-journal)
- **Dreamer** — Internal system name (`apps/lantern-garage/public/dreamer-dashboard.html`)
- **Courtney's Well** — User-facing name (`apps/lantern-garage/public/courtney.html`)
- **data-analyst** — MCP service alias (in some contexts)
- **/sales** — MCP service route (in some contexts)

### Implementation location

- **Backend:** `apps/lantern-garage/server.js` — `/api/dreamer` endpoints
- **Storage:** `data/dreamer/notebooks/{user}.jsonl` — JSONL persistence per user
- **Tasks:** `data/dreamer/tasks/{user}.jsonl` — Task tracking
- **UI surfaces:**
  - `apps/lantern-garage/public/courtney.html` — Entry form and recall
  - `apps/lantern-garage/public/dreamer-dashboard.html` — Stats, matrix, timeline
  - `dashboard/index.html` — Launch panel with links

### Capabilities (already implemented)

- JSONL persistence for entries (dreams, notes, places, characters, events, lore, symbols, mirrors)
- Ternary matrix visualization (3^12 constellation)
- Task tracking with completion
- Search/query across entries
- Stats dashboard (counts, streak, heatmap, timeline)
- Mirror entry generation (average of selected entries)
- Local-only storage (no cloud sync)

### API endpoints

- `GET /api/dreamer?user={user}&limit={limit}&q={query}` — List entries
- `POST /api/dreamer` — Create entry
- `GET /api/dreamer/stats?user={user}` — Compute statistics
- `GET /api/dreamer/matrix?user={user}` — Matrix nodes for visualization
- `POST /api/dreamer/mirror` — Create mirror entry
- `GET /api/dreamer/tasks?user={user}` — List tasks
- `POST /api/dreamer/tasks` — Create task
- `PATCH /api/dreamer/tasks/{id}?user={user}` — Complete task
