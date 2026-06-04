# Lantern OS All-Repos Code Master Plan

Date: 2026-05-26  
Control repo: `alex-place/lantern-os`  
Branch written: `master`  
Mode: connector inventory, code-first, all accessible repositories  
Scope correction: this supersedes the earlier Lantern-only RAG-house plan.

## Correction

The previous report was too narrow. It treated `alex-place/lantern-os` as the whole universe. That is wrong for an all-code master plan.

This report treats Lantern OS as the control plane and covers every repository currently visible through the GitHub connector inventory.

Connector inventory returned 43 accessible repositories and a second page returned no additional repositories.

## Operating Goal

Build one master control plane for all code without destroying working repo history.

The desired state is:

1. Every repo is represented in a Lantern OS inventory.
2. Every code surface is classified by runtime, language, risk, and promotion path.
3. Active repos are pulled into RAG as indexed metadata first, not blindly copied source.
4. Code stays executable in its source repo unless explicitly promoted.
5. Lantern OS stores the map, receipts, launch paths, validation status, and migration decisions.
6. All future moves happen as small commits with validation receipts.

## Repo Inventory Summary

Total accessible repositories: 43

Visibility split from connector metadata:

- Public: 31
- Private: 12

Default branch split:

- `master`: 36
- `main`: 7

Search index status from connector metadata:

- Indexed: 16
- Not indexed: 27

## All Repositories

| # | Repository | Visibility | Default branch | Size KB | Search indexed | Primary code lane |
|---:|---|---|---|---:|---|---|
| 1 | `alex-place/Mr.Nom` | public | master | 680 | no | game/app legacy |
| 2 | `alex-place/KeepSafe` | public | master | 9900 | no | app/security legacy |
| 3 | `alex-place/The_Josephus_Problem` | public | master | 212 | no | algorithm/sample |
| 4 | `alex-place/OpenTray` | public | master | 180 | no | desktop utility |
| 5 | `alex-place/Returners` | public | master | 146656 | no | game/app legacy |
| 6 | `alex-place/Quest` | public | master | 38944 | no | game/app legacy |
| 7 | `alex-place/LoL-Chat` | public | master | 4507 | no | chat/API client |
| 8 | `alex-place/jriot` | public | master | 324 | no | Riot API/library |
| 9 | `alex-place/GDungeon` | public | master | 1508 | no | game/app legacy |
| 10 | `alex-place/libgdx` | public | master | 835619 | no | framework/vendor-sized fork |
| 11 | `alex-place/GDXJam` | public | master | 92090 | no | game jam/app |
| 12 | `alex-place/GdxJam2` | public | master | 18156 | no | game jam/app |
| 13 | `alex-place/Orion` | public | master | 1264 | no | game/app legacy |
| 14 | `alex-place/corporate_crawler` | public | master | 776 | no | crawler/data tool |
| 15 | `alex-place/Porkopolis` | public | master | 30504 | no | game/app legacy |
| 16 | `alex-place/Cloudbot` | public | master | 2564 | no | bot/service |
| 17 | `alex-place/clouddataissexy` | public | master | 4133 | no | web/data app |
| 18 | `alex-place/riot-api-java` | public | master | 3894 | no | Java API library |
| 19 | `alex-place/Dungeon` | public | master | 781 | no | game/app legacy |
| 20 | `alex-place/VisionPark` | public | master | 0 | no | empty/placeholder |
| 21 | `alex-place/dnd_homebrew` | public | master | 33 | no | content/site |
| 22 | `alex-place/alex-place..github.io` | public | master | 2 | no | site placeholder |
| 23 | `alex-place/alex-place.github.io` | public | master | 44 | no | personal site |
| 24 | `alex-place/moneybags` | public | master | 61228 | yes | app/business code |
| 25 | `alex-place/TheGiddyLimit.github.io` | public | master | 1456094 | no | large site/content app |
| 26 | `alex-place/tradiest` | public | master | 2 | no | placeholder |
| 27 | `alex-place/badslothserver` | private | master | 10 | yes | server/service |
| 28 | `alex-place/server-debugclient` | public | master | 6 | yes | debug client |
| 29 | `alex-place/slothapi` | public | master | 17 | yes | API/service |
| 30 | `alex-place/BadSloth` | public | master | 300 | yes | app/game/service client |
| 31 | `alex-place/MysticGarden` | public | master | 16672 | no | game/app legacy |
| 32 | `alex-place/intspeedcheck` | private | main | 4 | yes | utility/service |
| 33 | `alex-place/statusmonitor` | private | main | 11 | yes | monitoring service |
| 34 | `alex-place/smartmealplanning` | private | main | 10 | yes | app/service |
| 35 | `alex-place/SmartBid` | private | master | 63 | yes | bidding/business app |
| 36 | `alex-place/ChildOfLevistus` | private | master | 183750 | yes | game/content app |
| 37 | `alex-place/gamemaker-room-editor` | private | main | 377 | yes | GameMaker tooling |
| 38 | `alex-place/gm-agent-orchestrator` | private | master | 6126 | yes | orchestrator/MCP/agents |
| 39 | `alex-place/place_co` | private | main | 143 | yes | company/site app |
| 40 | `alex-place/lantern-symbolic-sandbox` | private | master | 16243 | yes | symbolic/RAG sandbox |
| 41 | `alex-place/lantern-os` | private | master | 5330 | yes | control plane |
| 42 | `human-flourishing-frameworks/human-flourishing-frameworks` | private | master | 8721 | yes | framework/content/code |
| 43 | `human-flourishing-frameworks/.github` | public | main | 0 | no | org profile/config |

## Code-First Repo Lanes

### Lane A - Active control and agent runtime

Repos:

- `alex-place/lantern-os`
- `alex-place/gm-agent-orchestrator`
- `alex-place/gamemaker-room-editor`
- `alex-place/lantern-symbolic-sandbox`

Purpose:

- These are the current operating spine.
- Treat these as the first repos to inspect locally before any automation or mass refactor.
- They likely control MCP, orchestration, GameMaker workflows, RAG intake, and Lantern control-plane behavior.

Promotion path:

1. Inspect local dirty state first.
2. Map commands, scripts, configs, and agent queues.
3. Add validation receipts to `lantern-os/manifests/validation/`.
4. Only then index code into `references/LANTERN-OS-RAG-DOLLHOUSE.flat.md`.

### Lane B - Business/service apps

Repos:

- `alex-place/moneybags`
- `alex-place/SmartBid`
- `alex-place/place_co`
- `alex-place/smartmealplanning`
- `alex-place/statusmonitor`
- `alex-place/intspeedcheck`
- `alex-place/badslothserver`
- `alex-place/slothapi`
- `alex-place/server-debugclient`
- `alex-place/Cloudbot`
- `alex-place/corporate_crawler`
- `alex-place/clouddataissexy`

Purpose:

- Revenue, service, automation, monitoring, crawler, and API surfaces.
- These need dependency, secrets, env, endpoint, and test mapping before migration.

Promotion path:

1. Build `manifests/ALL-REPOS-CODE-SURFACES.md` entries.
2. For each repo, capture run command, build command, test command, deploy target, and secrets state.
3. Mark repos with unknown secrets as `held` until reviewed.
4. Do not combine services until ports, env files, and database assumptions are known.

### Lane C - Game/app legacy code

Repos:

- `alex-place/Mr.Nom`
- `alex-place/Returners`
- `alex-place/Quest`
- `alex-place/GDungeon`
- `alex-place/GDXJam`
- `alex-place/GdxJam2`
- `alex-place/Orion`
- `alex-place/Porkopolis`
- `alex-place/Dungeon`
- `alex-place/MysticGarden`
- `alex-place/ChildOfLevistus`
- `alex-place/BadSloth`

Purpose:

- Legacy games, experiments, app/game clients, and large art/content projects.
- Treat these as preservation plus selective modernization, not blanket rewrite.

Promotion path:

1. Identify engine/runtime per repo.
2. Capture build toolchain and asset requirements.
3. Preserve binary/art assets separately from source summaries.
4. Index source architecture and key loops into RAG; do not dump all assets into Lantern OS.

### Lane D - Java/API/library code

Repos:

- `alex-place/jriot`
- `alex-place/riot-api-java`
- `alex-place/LoL-Chat`
- `alex-place/libgdx`

Purpose:

- Java/API/library ecosystem.
- `libgdx` is very large and likely should not be absorbed directly into Lantern OS.

Promotion path:

1. Treat `libgdx` as external/vendor-sized unless a specific fork delta is needed.
2. Index only local modifications and dependency role.
3. For Riot API repos, inspect whether API contracts are current before any rebuild.

### Lane E - Sites/content/frameworks

Repos:

- `alex-place/TheGiddyLimit.github.io`
- `alex-place/alex-place.github.io`
- `alex-place/alex-place..github.io`
- `alex-place/dnd_homebrew`
- `human-flourishing-frameworks/human-flourishing-frameworks`
- `human-flourishing-frameworks/.github`

Purpose:

- Sites, content systems, framework documents, and org-level config.

Promotion path:

1. Separate copyright/content assets from source code.
2. Index metadata and local authored docs first.
3. Copy only operator-owned or approved assets into Lantern OS.
4. Use summaries and manifests for large public-content repos.

### Lane F - Empty/placeholders

Repos:

- `alex-place/VisionPark`
- `alex-place/tradiest`
- `human-flourishing-frameworks/.github`

Purpose:

- Placeholder or nearly-empty control points.

Promotion path:

- Mark as `held` or `archive_candidate` until the operator assigns purpose.

## Required Lantern OS Files

Add or update these files in `alex-place/lantern-os`:

```text
manifests/ALL-REPOS-INVENTORY.md
manifests/ALL-REPOS-CODE-SURFACES.md
manifests/ALL-REPOS-RAG-INTAKE.md
manifests/ALL-REPOS-VALIDATION-MATRIX.md
references/LANTERN-ALL-REPOS-CODE-RAG.flat.md
reports/LANTERN-OS-ALL-REPOS-CODE-MASTER-PLAN-2026-05-26.md
```

## Per-Repo Intake Record

Every repo needs this record before code is moved, rewritten, or promoted:

```text
repo:
visibility:
default_branch:
local_path:
local_status:
remote_status:
primary_language:
runtime:
entrypoints:
build_command:
test_command:
validation_receipt:
secrets_or_env:
asset_weight:
rag_state:
promotion_decision:
next_action:
```

## Validation Rules

Do not push mass rewrites across all repos. Use staged validation:

1. Inventory only.
2. Read-only local clone/status check.
3. Build/test command discovery.
4. One repo, one small change, one commit.
5. Push only after validation evidence is captured.
6. Update Lantern OS manifests after each repo pass.

## Priority Order

Recommended first pass:

1. `alex-place/gm-agent-orchestrator` - controls agents and MCP workflow.
2. `alex-place/gamemaker-room-editor` - current GameMaker tooling.
3. `alex-place/lantern-symbolic-sandbox` - RAG/symbolic experiments.
4. `alex-place/moneybags` - indexed, large public app/business code.
5. `alex-place/place_co` - company/site surface.
6. `human-flourishing-frameworks/human-flourishing-frameworks` - framework/control content.
7. `alex-place/ChildOfLevistus` - large private game/content project.
8. `alex-place/TheGiddyLimit.github.io` - very large content/site repo; metadata-first only.
9. Legacy game repos as preservation lane.
10. Placeholder repos last.

## Risks

1. Some repos are very large and should not be copied into Lantern OS.
2. Some repos are not search indexed, so connector metadata is incomplete.
3. Private service repos may contain environment assumptions or secrets paths; inspect before action.
4. Game repos may have binary assets that should be manifested, not embedded.
5. `libgdx` and `TheGiddyLimit.github.io` are large enough to require metadata-first handling.
6. The connector cannot validate local dirty worktrees; local status must override remote assumptions.

## Done Definition

This corrected all-repos plan is complete when:

- This report exists on `master` in `alex-place/lantern-os`.
- The PDF report is generated from this content.
- `manifests/ALL-REPOS-INVENTORY.md` exists.
- `manifests/ALL-REPOS-CODE-SURFACES.md` exists.
- Every repo has an intake state.
- Active code repos have build/test/launch commands captured.
- No repo is rewritten or moved without validation evidence.

## Next Safe Commit

Create `manifests/ALL-REPOS-INVENTORY.md` from this connector inventory, then begin read-only local inspections for the active control lane.
