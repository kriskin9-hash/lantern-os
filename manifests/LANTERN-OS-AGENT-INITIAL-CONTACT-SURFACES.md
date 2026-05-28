# Lantern OS Agent Initial Contact Surfaces

**Status:** candidate remote contract  
**Date:** 2026-05-28  
**Purpose:** make every agent contact start from the same Lantern OS control surface: tools declared, connectors checked, repo context loaded, local-only gaps reported, and next validation path stated.

## Rule

Every agent the operator speaks with should begin by loading the Lantern OS initial-contact surface before taking action.

The surface is not a claim that tools are live. It is a required checklist that separates:

- observed tools and connectors;
- advertised but unverified capabilities;
- repo context available from remote sources;
- local-only state that requires operator-machine proof;
- held issues, blockers, and missing validation.

## Initial-contact packet

Each agent should receive or reconstruct this packet at session start:

1. **Identity / role**
   - Agent name or platform.
   - Intended lane: repo, MCP, Canva/art, PDF/report, dashboard, RAG/memory, shipping/lead-process, or validation.
   - Current authority level: read-only, candidate write, local execution, or held.

2. **Repo anchors**
   - Remote repo: `alex-place/lantern-os`.
   - Primary branch: `master` unless the live repo says otherwise.
   - Core loop: `docs/CONVERGENCE-LOOP.md`.
   - MCP split: `manifests/MCP-WORK-SPLIT.md`.
   - Fleet contract: `manifests/CONVERGENCE-LOOP-AGENT-FLEET.md`.
   - Current surface list: `README.md` initial surfaces.

3. **Tool / connector declaration**
   The agent must list what it can actually access in the current session, grouped as:
   - repo tools;
   - local shell / local MCP tools;
   - browser / web tools;
   - Canva / design tools;
   - file read/write tools;
   - PDF / document tools;
   - calendar, mail, contact, or other personal connectors;
   - unavailable or unverified tools.

4. **MCP and local-state boundary**
   The agent must not claim live local MCP health, dirty worktree status, Windows process state, private folders, or worker counts unless it has fresh local operator-machine evidence.

5. **First report shape**
   The first response should include:
   - loaded surface version;
   - tools observed;
   - connectors observed;
   - repo anchors read;
   - local-only checks that are held;
   - safest next objective;
   - validation path;
   - blockers / issues.

## Surface types by agent lane

| Lane | Optimal first surface | Required checks | Issue report if missing |
|---|---|---|---|
| Repo agent | Repo control surface | Read `README.md`, convergence loop, MCP split, fleet contract | missing repo read, stale branch, no write permission |
| MCP agent | Local-first MCP surface | Probe local MCP health, tool descriptors, tunnel status, dirty worktrees | remote-only view, missing local probe, advertised-only tools |
| Canva/art agent | Design surface | Source artifact, editable/import path, quota/status, public-safe boundary | quota exceeded, prompt block, flat-only import, missing source file |
| PDF/report agent | Report surface | Source manifest, page render check, no path spam, human-readable layout | render failed, raw path spam, missing validation JSON |
| Dashboard agent | Operator UI surface | Current surface file, health panels, status/action separation, mobile/1080p fit | stale cache, broken links, placeholder-only UI |
| RAG/memory agent | RAG receipt surface | Durable artifact pointer, summary, tags, boundary, hash/manifest | private data leak risk, no pointer, no validation state |
| Lead-process agent | Public-safe lead surface | Non-binding lane, dependency list, human approval gate | shipment/production claim, supplier spend without approval |
| Validation agent | Evidence surface | Cheapest checks, receipt, pass/fail/held, rollback | no evidence, no rollback, no rerun path |

## Required first message template

```text
Lantern OS initial-contact surface loaded.

Observed tools/connectors:
- Repo:
- Local shell/MCP:
- Web/browser:
- Canva/design:
- Files/PDF/docs:
- Personal connectors:
- Unavailable/unverified:

Repo anchors checked:
- README.md:
- docs/CONVERGENCE-LOOP.md:
- manifests/MCP-WORK-SPLIT.md:
- manifests/CONVERGENCE-LOOP-AGENT-FLEET.md:

Held local-only evidence:
- local MCP health:
- dirty worktrees:
- Windows process state:
- live worker count:
- private folders/secrets:

Safest next objective:
Validation path:
Issues/blockers:
Rollback:
```

## Tool completeness rule

An agent is **fully loaded** only when it can name the tools/connectors it actually sees and distinguish them from desired tools.

States:

- `ready`: tool is observed and usable in this session.
- `partial`: tool exists but has limits, quota, auth, missing file access, or import limits.
- `held`: requires local machine, account login, secret, hardware, payment, or operator action.
- `missing`: not visible to the agent.
- `mismatch`: advertised in docs but not actually exposed.

## Connector issue receipt

When a tool or connector is missing, the agent should emit this compact receipt:

```json
{
  "surface": "agent-initial-contact",
  "toolOrConnector": "name",
  "expected": "what the lane needs",
  "observed": "what is actually visible",
  "state": "ready | partial | held | missing | mismatch",
  "impact": "what cannot be validated",
  "safeFallback": "smallest useful fallback",
  "nextAction": "operator or repo action"
}
```

## Validation hooks

Remote validation:

- Confirm this manifest exists.
- Confirm `README.md` points to the convergence loop and initial surfaces.
- Confirm the MCP split keeps local-only evidence held.
- Confirm the fleet contract does not claim live worker proof.

Local validation, when available:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Invoke-LanternConvergenceLoop.ps1
python .\scripts\Test-ConvergenceAgentFleet.py --write-json .\manifests\validation\CONVERGENCE-FLEET-LATEST.json
```

## Current remote evidence

- The repo is pre-v1 staging and promotes surfaces through the convergence loop.
- The README says local MCP health, dirty worktrees, private folders, and live worker counts require operator-machine evidence.
- The MCP split requires actual exposed tool descriptors, not advertised-only tools.
- The fleet contract is a design and receipt contract, not live-worker proof.

## Next integration

Promote this manifest into the agent intake path by referencing it from `README.md` or the relevant dashboard surface after the operator reviews it. Do not claim automatic loading for every external agent until each platform has a tested intake method.
