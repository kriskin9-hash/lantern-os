# Lantern OS

Status: pre-v1.0.0 staging  
Scope: local-first operating repo, surfaces, reports, manifests, and release gates  
Style spine: `docs/ORION-MOOKMANREPORT4-STYLE.md`  
Operator boundary: local MCP status, dirty worktrees, private folders, boot mutation, and live worker counts require operator-machine evidence

---

## Simple Answer

Lantern OS is the clean control plane for the Windows/local-first Lantern line.

The repo is not a dump of every prior artifact. It is the place where promoted work becomes readable, validated, public-safe, and ready for the next operator step.

Repo = evidence store. Surface = fast access. Together they reduce confusion.

---

## What It Actually Does

| Lane | Purpose | Current state |
|---|---|---|
| Local cockpit | Open operator surfaces for app, garage, RAG, wallet, boot gates, and reports | present |
| RAG Dollhouse | Keep source-labeled flat memory and receipts | present |
| Release gates | Prevent v1 claims before proof and operator approval | active |
| MCP split | Separate remote docs from local-only health and worker proof | active |
| Agent contact | Tell agents what to inspect first and what to hold | active |
| Orion style | Convert flat docs and CSS into human-readable technical sheets | active style pass |

---

## Evidence / Source Discipline

Source repos remain authoritative until promoted:

```text
C:\tmp\human-flourishing-frameworks-scan
C:\Users\alexp\Documents\gm-agent-orchestrator
```

Remote control plane:

```text
https://github.com/alex-place/lantern-os
```

Core maps:

```text
manifests/foundry-shareholder-repos.md
docs/wiki/ALEX-PLACE.md
docs/ORION-MOOKMANREPORT4-STYLE.md
```

---

## Proven / Held / Local-Only

| State | Meaning |
|---|---|
| Proven in repo | File exists here and can be reviewed through GitHub or local checkout |
| Held local-only | Requires the operator machine: MCP health, dirty worktrees, private folders, local queue/active/failed state, live worker counts |
| Design contract | Describes intended system shape, not live proof |
| Public-safe | Avoids private identity, raw dumps, unsafe fabrication details, and fake live-state claims |

Nothing becomes v1.0.0 merely because it exists elsewhere. Promotion requires the convergence loop in `docs/CONVERGENCE-LOOP.md`.

---

## Initial Surfaces

| Surface | Path |
|---|---|
| Shareholder HTML index | `surfaces/shareholder-index/index.html` |
| Tony Garage operator cockpit | `surfaces/tony-garage/index.html` |
| Lantern Garage app | `apps/lantern-garage/` |
| Agent initial-contact surface | `manifests/LANTERN-OS-AGENT-INITIAL-CONTACT-SURFACES.md` |
| Arc Reactor status | `data/arc-reactor/status.json` |
| Flat Lantern RAG Dollhouse | `skills/lantern-rag-dollhouse/references/LANTERN-OS-RAG-DOLLHOUSE.flat.md` |
| Orion / Mookman Report 4 style | `docs/ORION-MOOKMANREPORT4-STYLE.md` |

---

## Release Rule

Before adding new surfaces, run the loop and fix the first 2-4 open issues it finds. Expansion is allowed only after the leading blockers are handled or explicitly marked held by the operator.

Fleet execution uses the 12x3 convergence-ring contract in `manifests/CONVERGENCE-LOOP-AGENT-FLEET.md`: 12 loop steps, 3 agent roles per step, 36 designed ring slots, and a 64-worker elastic pool target. This is a design and receipt contract, not live-worker proof.

MCP work is split by `manifests/MCP-WORK-SPLIT.md`. Remote docs can validate contracts and receipts, but local-only MCP health, dirty worktrees, private folders, and live worker counts still require operator-machine evidence.

---

## Receptionist Routing

Use `docs/LANTERN-OS-RECEPTIONIST-CALL-LIST.md` for public-safe call routing. It uses organization switchboards and public program contacts only. Do not add personal phone numbers, scraped direct dials, or unverified private numbers.

---

## Printable Reports

Quick front page:

```text
artifacts/SUPER-JARVIS-LANTERN-OS-FRONT-PAGE.pdf
```

Master convergence PDF:

```text
artifacts/COMET-LEAP-TOKEN-BURN-REVENUE-CONVERGENCE-v1.pdf
```

---

## Non-Goals For This Repo

- No unattended bootloader edits.
- No partition or disk mutation scripts.
- No unreviewed generated artifact dump.
- No claim that v1.0.0 is ready before the operator says so.
- No skeleton-only milestones.
- No treating offline/local/server-farm Foundry tokens as cloud-metered, "Lite", or per-token rated.
- No raw filepath spam above the first human-relevant explanation.

---

## First Command

Run the convergence loop:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Invoke-LanternConvergenceLoop.ps1
```

Validate the convergence fleet count contract:

```powershell
python .\scripts\Test-ConvergenceAgentFleet.py --write-json .\manifests\validation\CONVERGENCE-FLEET-LATEST.json
```

---

## Garage Command

Open the Movie 1 operator cockpit:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Open-TonyGarage.ps1
```

If the browser shows stale styling, reopen through the launcher or refresh with cache bypass. The garage surface cache-busts its CSS, image, and document links.

---

## Local Controls Command

Open the local control bridge and validate dashboard/MCP/Lantern health:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-LanternLocalControls.ps1
```

---

## Full-Stack App Command

Start the in-house Lantern Garage app:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-LanternGarageApp.ps1
```

Then open:

```text
http://127.0.0.1:4177
```
