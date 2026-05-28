# Valid Ideas Promotion List

Status: list-first promotion gate.

Generated: 2026-05-27.

## Rule

Make the list before promotion.

Promote only ideas that have:

1. a clear Lantern OS surface;
2. a dependency/provider path;
3. evidence or a prior manifest;
4. no unresolved held boundary blocking the claim;
5. a fallback/degraded path;
6. a validation receipt path or validation command;
7. a safe claim that does not overstate runtime, revenue, route, device, or agent capacity.

Ideas can be promoted as architecture, manifest, adapter, RAG index, fallback-first task, or implementation task. Promotion does not mean public readiness unless validation and fallback receipts exist.

## Promotion Vocabulary

| Decision | Meaning | Can Promote? |
|---|---|---|
| `promote` | valid now as architecture/manifest/control-plane rule | yes |
| `adapter_first` | valid idea, but wrap dependency before moving code | partially |
| `index_only` | valid for RAG/storage/metadata, not runtime | partially |
| `fallback_first` | valid, but needs fallback before feature/public claim | not yet public-ready |
| `hold` | blocked by proof, dirty state, secrets, rights, physical action, or missing validation | no |
| `reject` | unsafe, unsupported, or outside boundary | no |

## Promoted Now

| Idea | Surface | Evidence | Promotion Type | Safe Claim |
|---|---|---|---|---|
| Lantern OS is top-down control plane | architecture/control plane | `manifests/TOP-DOWN-DEPENDENCY-GRAPH.md` | `promote` | Lantern OS owns project spine; old repos are dependencies. |
| Old repos are dependencies, not roots | all-repos/dependency intake | `manifests/ALL-REPOS-INVENTORY.md` | `promote` | Old repos feed Lantern through adapters/manifests/RAG, not blind merges. |
| Full matrix use rule | operating method | `manifests/FULL-BLOWN-MATRIX-USE-RULE.md` | `promote` | Use full matrix for non-trivial runtime/public/MCP/dependency/release work. |
| SPOF redundancy gate | resilience/release gate | `manifests/SINGLE-POINTS-OF-FAILURE.md` | `promote` | Critical surfaces need primary, local fallback, static/read-only fallback, recovery, validation, and degraded claim. |
| RAG matrix transform model | RAG/storage architecture | `manifests/RAG-MATRIX-TRANSFORM-MODEL.md` | `promote` | Large sparse matrices are valid for storage/transform, not as blind task queues. |
| Continuous `[-1,1]` latent matrix values | RAG/view architecture | `manifests/RAG-MATRIX-TRANSFORM-MODEL.md` | `promote` | Store latent values; render dynamic views through transforms. |
| RAG dollhouse truth states | RAG/source control | `skills/lantern-rag-dollhouse/SKILL.md` | `promote` | Separate local-inspected, copied assets, metadata-only, not-yet-cloned, held, and external-cache states. |
| Bayesian evidence loop | confidence/decision system | `skills/bayesian-world-model/SKILL.md` | `promote` | Claims move by evidence class, likelihood, posterior, and boundary checks. |
| Blocker fix record | validation/control-plane history | `manifests/BLOCKER-FIX-2026-05-26.md` | `promote` | Dual boot, cash send, orchestrator dirty, and archive rights blockers have recorded fix states and hard boundaries. |

## Valid But Not Yet Public-Ready

| Idea | Surface | Decision | Blocker | Next Smallest Promotion Step |
|---|---|---|---|---|
| HFF Render `/os` route | public HFF surface | `fallback_first` | live route returns Not Found / lacks HTTP 200 receipt | patch HFF `safe_app.py`, add smoke test, push, verify Render HTTP 200 |
| Public/static Lantern fallback bundle | public/static fallback | `fallback_first` | static bundle not built/validated | export non-secret rights-cleared HTML/PDF/manifest bundle and hash it |
| MCP/orchestrator live capability | execution plane | `adapter_first` | local MCP/tool exposure must be verified, connector mismatch observed | run local read-only MCP status and save validation JSON |
| Agent fleet capacity / 600 agents | execution capacity | `hold` | slots/queues/active/failed not verified locally | inspect local config, queue, active, failed, dry-run supervisor; save receipt |
| Dependency repo mass intake | all-repos intake | `adapter_first` | many repos are metadata-only / not locally inspected | clone missing repos only into explicit intake path; record branch/remote/status/fallback |
| GameMaker/game lane modernization | game/runtime lane | `index_only` then `adapter_first` | old build chains/assets/toolchains unknown | capture engine, build/test command, asset manifest, and fallback per repo |
| Wallet/payment surface | money/cash lane | `hold` for cleared-cash claims | no external cleared payment truth | keep local ledger; do not mark cleared cash until funds clear |
| Archive/Wayback/media download lane | media/archive lane | `hold` for downloads | rights/storage/operator review required | keep metadata-only and `downloadAllowed=false` until reviewed |
| Dual boot install | device/OS lane | `hold` | physical disk action and rollback boundary | prep-only readiness and operator-controlled Disk Management step |
| Render deployment dependency | public deployment | `fallback_first` | Render route/deploy can fail or stale | keep local Flask/static fallback and live HTTP smoke checks |

## Rejected / Not Promoted As Stated

| Idea | Decision | Reason | Safer Version |
|---|---|---|---|
| Treat `3^12 - 1` matrix as 531,440 tasks | `reject` | confuses RAG storage state space with execution queue | sparse latent vectors with dynamic view transforms |
| Use large matrix count as proof of agent capacity | `reject` | storage states do not prove slots, workers, queues, or uptime | verify local orchestrator counts and health receipts |
| Public readiness from architecture alone | `reject` | readiness needs live validation and fallback receipts | release gate through SPOF and validation matrix |
| Clone/import all old repos into Lantern OS root | `reject` | violates dependency boundary and risks dirty state/import noise | explicit intake directory and dependency profiles |

## Promotion Queue

### Next 1: HFF `/os` fallback-first repair

Target decision: `fallback_first` -> `promote` after HTTP 200.

Validation receipt target:

```text
manifests/validation/HFF-OS-ROUTE-LATEST.json
```

### Next 2: static/public fallback bundle

Target decision: `fallback_first` -> `degraded_ready`.

Validation receipt target:

```text
manifests/validation/STATIC-FALLBACK-BUNDLE-LATEST.json
```

### Next 3: orchestrator/MCP local truth snapshot

Target decision: `adapter_first` -> `promote` for capability map; `hold` remains for 600-agent claim until counts pass.

Validation receipt target:

```text
manifests/validation/ORCHESTRATOR-MCP-LATEST.json
```

### Next 4: RAG matrix implementation skeleton

Target decision: `promote` architecture -> `adapter_first` implementation.

Files:

```text
data/rag-matrix/matrix-records.jsonl
scripts/Convert-RagChunkToMatrixRecord.ps1
scripts/Test-RagMatrixRecords.ps1
manifests/validation/RAG-MATRIX-LATEST.json
```

## End-To-Beginning Loop

Each promoted idea must feed actual result back into the next beginning:

```text
idea -> list -> decision -> smallest action -> validation receipt -> updated matrix/RAG state -> next prior
```

No idea leaves this list as public-ready unless its validation receipt and fallback state support that view.
