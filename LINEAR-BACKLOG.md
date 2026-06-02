# Lantern OS Linear Backlog — 2026-06-01

**Status:** Ready to sync to Linear  
**Total Issues:** 28 (Phase A: 5 | Phase B: 12 | Phase C: 11)  
**Timeline:** Phase A (1 week) | Phase B (8 weeks) | Phase C (4 weeks)

---

## PHASE A: Discord Bot + Linear Setup (Jun 1-7)

### A-1: Discord Bot MCP Bridge
- **Type:** Feature  
- **Priority:** P0  
- **Owner:** Unassigned  
- **Status:** In Progress  
- **Description:**  
  Wire Discord bot slash commands to MCP server endpoints. Bot exposes task queue + orchestrator status to Discord users.
  - Create `src/discord_lounge_bot/mcp_bridge.py` (✅ done)
  - Update bot_v2.py with MCP calls (✅ done)
  - Health check responds on port 8770 (✅ done)
  - `/status` command shows MCP status (✅ done)
- **Acceptance Criteria:**
  - [ ] Bot responds to `/status` within 2s
  - [ ] `/queue` lists pending tasks
  - [ ] Structured logging to `~/.lantern/logs/discord-bot.log`
  - [ ] Bot survives restart + reconnects within 30s

### A-2: Archive Curator Implementation
- **Type:** Feature  
- **Priority:** P0  
- **Owner:** Unassigned  
- **Status:** In Progress  
- **Description:**  
  Generic Internet Archive media curator for Discord voice channels. Frank Sinatra is first collection; support multiple collections (classical, audiobooks, etc.)
  - Create `archive_curator.py` (✅ done)
  - 7 slash commands: `/archive-{join,list,play,next,loop,stop,leave}` (✅ done)
  - Voice channel: `archive` (not `Lounge`)
  - Support switching collections
- **Acceptance Criteria:**
  - [ ] Create voice channel `archive` in test server
  - [ ] `/archive-join` connects bot + starts streaming
  - [ ] `/archive-list` shows 6 Frank Sinatra songs
  - [ ] `/archive-play the_world_we_knew` plays song
  - [ ] FFmpeg audio streaming works (or graceful fallback)
  - [ ] `/archive-next`, `/archive-loop`, `/archive-stop` work

### A-3: Linear Workspace Setup
- **Type:** Infrastructure  
- **Priority:** P0  
- **Owner:** Unassigned  
- **Status:** Pending  
- **Description:**  
  Create Linear workspace + team + cycles for Lantern OS repo reset. Establish single source of truth for work tracking.
  - Create workspace: `Lantern OS`
  - Create team: `Repo Reset`
  - Create cycles:
    - Cycle 1: Jun 1-14 (Phase C: delete mythology)
    - Cycle 2: Jun 15-28 (Phase C: strip overengineering + validate)
    - Cycle 3: Jul 1-14 (Phase C: document + fresh READMEs)
- **Acceptance Criteria:**
  - [ ] Linear workspace created + team added
  - [ ] Phase C issues synced to Linear backlog
  - [ ] Workflow documented in CONTRIBUTING.md

### A-4: Handoff Documentation
- **Type:** Documentation  
- **Priority:** P1  
- **Owner:** Unassigned  
- **Status:** Pending  
- **Description:**  
  Prepare runbooks for 2-3 operators to take over repo cleanup execution.
  - Create `docs/LINEAR-WORKFLOW.md` (500 words)
  - Create `docs/REPO-RESET-ROADMAP.md` (1000 words)
  - Update `CONTRIBUTING.md`
- **Acceptance Criteria:**
  - [ ] Operators can read docs and understand role
  - [ ] 2+ operators willing to claim issues

### A-5: CI/Test Verification
- **Type:** Infrastructure  
- **Priority:** P1  
- **Owner:** Unassigned  
- **Status:** Pending  
- **Description:**  
  Ensure all tests pass and bot is production-ready.
  - Run `pytest` on HFF
  - Run contract tests on gm-agent-orchestrator
  - Verify Discord bot connects + syncs commands
- **Acceptance Criteria:**
  - [ ] All tests pass
  - [ ] Bot online + 27 commands synced globally
  - [ ] No import errors

---

## PHASE B: Suzie 2.0 — Rust + Kubernetes Modernization (Jun 8 - Jul 27)

### B-1: Phase 1 - Redis Queue + PostgreSQL State
- **Type:** Infrastructure  
- **Priority:** P0  
- **Owner:** Unassigned  
- **Status:** Pending  
- **Description:**  
  Replace filesystem task queue + JSON state files with Redis + PostgreSQL. Atomic operations, O(1) claim.
  - Deploy Redis (queue service)
  - Deploy PostgreSQL + TimescaleDB (state store)
  - Rewrite `Claim-OrchestratorQueueTask.ps1` → Redis client
  - Rewrite `Get-OrchestratorStatus.ps1` → Postgres queries
  - Create `config/database.json` (new)
- **Acceptance Criteria:**
  - [ ] Redis health check responds
  - [ ] PostgreSQL schema created + migrations run
  - [ ] O(1) task claim via LPOP
  - [ ] State queries fast (<50ms)

### B-2: Phase 2 - Dockerize Slot Runtime
- **Type:** Infrastructure  
- **Priority:** P0  
- **Owner:** Unassigned  
- **Status:** Pending  
- **Description:**  
  Create containerized agent slot runtime. Replace PowerShell slot scripts with Python containers.
  - Create `python/agent_runner.py` (~300 lines)
  - Build `docker/Dockerfile.slot` (Python 3.12)
  - Update `docker-compose-multiagent.yml` (20 slot containers + services)
  - Test local: 20 agent slots on 1 PC
- **Acceptance Criteria:**
  - [ ] `docker build` succeeds
  - [ ] `docker-compose up` starts 20 slots + Redis + Postgres
  - [ ] Each slot connects to orchestrator

### B-3: Phase 3 - Rust Orchestrator Controller
- **Type:** Feature  
- **Priority:** P0  
- **Owner:** Unassigned  
- **Status:** Pending  
- **Description:**  
  Write Rust orchestrator that replaces PowerShell scripts. Manages pod lifecycle via Kubernetes API.
  - Create `rust/suzie-controller/` (~3000 lines)
  - Capabilities:
    - Watch Kubernetes pod API
    - Manage slot lifecycle (create/update/delete)
    - Enforce per-operator token quotas
    - Work distribution via Redis queue
    - Prometheus metrics export
  - Libraries: `kube-rs`, `redis`, `sqlx`, `tokio`, `prometheus`
- **Acceptance Criteria:**
  - [ ] Rust binary compiles
  - [ ] Manages 20 pods on 1 PC
  - [ ] Metrics exposed on port 9090
  - [ ] Token quota enforced per-operator

### B-4: Phase 4 - Kubernetes Manifests
- **Type:** Infrastructure  
- **Priority:** P1  
- **Owner:** Unassigned  
- **Status:** Pending  
- **Description:**  
  Define K8s deployment for full fleet. Kustomize overlays per operator.
  - Create `k8s/*.yaml` (~15 manifests)
  - Namespaces: agent-slots, queue-service, state-service, storage
  - Services: Redis, Postgres, Rust controller
  - Kustomize: founder + operators 1-20
- **Acceptance Criteria:**
  - [ ] `kubectl apply -k k8s/` succeeds
  - [ ] All pods healthy
  - [ ] Services discoverable

### B-5: Phase 5 - Golden Image + Setup Script
- **Type:** Infrastructure  
- **Priority:** P1  
- **Owner:** Unassigned  
- **Status:** Pending  
- **Description:**  
  Create reusable operator onboarding script. One-click setup for new operators.
  - Create `scripts/Setup-OperatorPC.ps1` (~500 lines)
  - Create `docs/OPERATOR_ONBOARDING.md`
  - Automate: Docker/k3s install, repo clone, secrets config, manifest deploy
  - Target: <5 minutes per operator
- **Acceptance Criteria:**
  - [ ] Script runs on clean Windows PC
  - [ ] Operator PC boots 20 agent slots
  - [ ] Connects to founder's Redis/Postgres

### B-6: Phase 6 - 20-Operator Rollout
- **Type:** Feature  
- **Priority:** P0  
- **Owner:** Unassigned  
- **Status:** Pending  
- **Description:**  
  Roll out Suzie 2.0 across 20 operators. Verify fleet health.
  - Week 6: Founder runs full Suzie 2.0 locally (40 slots)
  - Week 7: Operators 1-5 set up via script
  - Week 8: Operators 6-20 onboard
  - Target: 400 slots operational
- **Acceptance Criteria:**
  - [ ] Founder: 40 slots, all green
  - [ ] Operators 1-5: 100 slots, all green
  - [ ] Operators 6-20: 300 slots, all green
  - [ ] Fleet health dashboard shows 400/400 online

### B-7: Revenue & Foundry Model
- **Type:** Feature  
- **Priority:** P1  
- **Owner:** Unassigned  
- **Status:** Pending  
- **Description:**  
  Implement foundry resource pooling + revenue share ledger. Operators grant compute capacity; get value back.
  - Create `foundry-consent.json` per operator (per-resource opt-in)
  - Redis: track idle compute, distribute work
  - Postgres: revenue share ledger
  - Dashboard: shows operator contribution + quarterly payout
- **Acceptance Criteria:**
  - [ ] Operators can toggle consent for: GPU, SSD, RAM, bandwidth, API quota, agent slot, port forward
  - [ ] Foundry work only runs when operator slot is idle (>5min)
  - [ ] Revenue share calculated + displayed quarterly
  - [ ] No operator >10% of pool (hard cap)

---

## PHASE C: Repo Reset — Scientific Rigor (Jun 8 - Jul 5)

### C-1: Phase 0 - Snapshot + Stop Services
- **Type:** Infrastructure  
- **Priority:** P0  
- **Owner:** Unassigned  
- **Status:** Pending  
- **Description:**  
  Safe pre-cleanup snapshot. Stop live services before destructive work.
  - `git tag pre-cleanup-snapshot` (both repos)
  - Push tags to remote
  - Stop scheduled tasks: LanternChatWatchdog, OrchestratorServiceSupervisor, etc.
  - Archive `~/.lantern/state/` privately (journal.jsonl, screenshots, etc.)
- **Acceptance Criteria:**
  - [ ] Tags created + pushed
  - [ ] Tasks stopped (not deleted)
  - [ ] Private state backed up locally

### C-2: Phase 0b - Consolidate Duplicate Repos
- **Type:** Infrastructure  
- **Priority:** P1  
- **Owner:** Unassigned  
- **Status:** Pending  
- **Description:**  
  Audit & archive 9+ duplicate repo copies. Prevent accidental work in stale clones.
  - `Documents/human-flourishing-frameworks/`
  - `Documents/hff-fresh/`
  - `Documents/hff-master-clean/`
  - `Documents/gm-agent-orchestrator-local-backup-*`
  - ... (9 total)
  - Move stale-only to `Documents/_archived-repo-copies-2026-05-24/`
  - Verify no unique commits lost
- **Acceptance Criteria:**
  - [ ] All duplicates audited for unique commits
  - [ ] Archive folder created + populated
  - [ ] Confirmed safe to delete archive after verification

### C-3: Phase 1 - Delete Mythology Docs
- **Type:** Cleanup  
- **Priority:** P0  
- **Owner:** Unassigned  
- **Status:** Pending  
- **Description:**  
  Delete ~85 HFF mythology docs + ~70 gm-agent-orchestrator mythology task files. Remove overengineering framing.
  - HFF: delete TARDIS, spine, anchor, convergence, door, echo, etc. docs
  - HFF: delete mythology apps (toy-robot-lantern, lake-of-helpers-painter, return-door-watch)
  - HFF: delete mythology scripts (Wake-Lantern.ps1, help_lantern_now.ps1, seven_surface_audit.py)
  - gm: delete `lantern/` folder
  - gm: delete ~70 mythology task queue files
- **Acceptance Criteria:**
  - [ ] `grep -r "TARDIS\|Keystone\|convergence doctrine"` returns 0 hits
  - [ ] PR diff shows only deletions (no rewrites)
  - [ ] Tests still pass

### C-4: Phase 2 - Strip Overengineering
- **Type:** Cleanup  
- **Priority:** P0  
- **Owner:** Unassigned  
- **Status:** Pending  
- **Description:**  
  Remove grandiose framing. Reframe BFT as TRL-2 optional library. Delete useless registries.
  - HFF: strip "Impossibility Engine" / "court-admissible" branding from app.py
  - HFF: validate `byzantine_consensus.py` as standalone lib (if sound → `hff_distributed/`; if broken → delete)
  - HFF: delete `bio_threat_source_registry.py`, `polymorphic_seed_registry.py`
  - HFF: reframe BetterSafe as skeletal placeholder (delete mythology, keep 3 stubs)
- **Acceptance Criteria:**
  - [ ] No "Impossibility Engine" language in code
  - [ ] BFT either in `hff_distributed/` or deleted
  - [ ] BetterSafe marked as TRL 1 (placeholder only)
  - [ ] Tests pass

### C-5: Phase 3 - Validate + Refactor Tier 3
- **Type:** Research  
- **Priority:** P1  
- **Owner:** Unassigned  
- **Status:** Pending  
- **Description:**  
  Validate scientific claims against public frameworks. Refactor as synthesis notes, not novel research.
  - 500-year-lab: validate citations against PubMed/DOI, refactor to "Longevity Evidence Summary" with GRADE quality
  - Regulatory Primitive Stack: cross-ref against NIST AI RMF / ISO 42001 / EU AI Act, build overlap table
  - Capability Honesty: file as design doc, mark "implementation pending"
  - Bumblebee audio: rename synthetic files (lantern_10_quantum_dust.wav → lantern_10_sparkle_pad.wav), create MANIFEST.md with source + license
- **Acceptance Criteria:**
  - [ ] All longevity citations resolve
  - [ ] Regulatory primitive overlap table created
  - [ ] Audio manifest complete with source URLs
  - [ ] No mythology language remains

### C-6: Phase 4 - Document + Fresh READMEs
- **Type:** Documentation  
- **Priority:** P0  
- **Owner:** Unassigned  
- **Status:** Pending  
- **Description:**  
  Create polished, industry-grade documentation. Document all Tier 1-2 streams. Replace README entirely.
  - Create `docs/STREAMS.md` (19 Tier-1 + 3 Tier-2 with TRL/CPC/owner)
  - Create `docs/OVERVIEW.md` (≤1200 words, no mythology, for reviewers)
  - Replace `README.md` with Suzie/Lantern product positioning
  - Create `CONTRIBUTING.md` linking to Linear
  - Add status headers to all research docs: "Tier N | TRL X | CPC NNN"
- **Acceptance Criteria:**
  - [ ] STREAMS.md complete with all 22 streams
  - [ ] OVERVIEW.md passes 1200-word check
  - [ ] README is industry-readable
  - [ ] CONTRIBUTING.md explains Linear workflow

### C-7: Phase 5 - CI Verification + Service Restart
- **Type:** QA  
- **Priority:** P0  
- **Owner:** Unassigned  
- **Status:** Pending  
- **Description:**  
  Run all tests. Restart services. Verify nothing broke.
  - HFF: `pytest` clean
  - gm: contract tests pass
  - Discord bot: starts + syncs commands
  - Re-enable: LanternChatWatchdog, OrchestratorServiceSupervisor, etc.
  - Verify `~/.lantern/state/` runtime files load correctly
- **Acceptance Criteria:**
  - [ ] All tests pass
  - [ ] Bot online + 27 commands synced
  - [ ] Services restart successfully
  - [ ] Runtime state loads without error

### C-8: Phase 6 - Merge to Master
- **Type:** Infrastructure  
- **Priority:** P0  
- **Owner:** Unassigned  
- **Status:** Pending  
- **Description:**  
  Create single cleanup commit. Merge to master. Tag release.
  - Branch: `cleanup/scientific-rigor-pass`
  - Single squash commit with full message
  - Self-review PR diff
  - Merge to master
  - Tag: `v0.1-scientific-rigor`
  - Push tags
- **Acceptance Criteria:**
  - [ ] PR merged to master
  - [ ] Tag created + pushed
  - [ ] Full history preserved beneath tag

### C-9: Cleanup Verification
- **Type:** QA  
- **Priority:** P1  
- **Owner:** Unassigned  
- **Status:** Pending  
- **Description:**  
  Post-cleanup verification checklist. Ensure no mythology remains.
- **Acceptance Criteria:**
  - [ ] `grep -ri "TARDIS\|Keystone\|convergence"` = 0 hits
  - [ ] `grep -ri "Courtney\|Gage\|kickazzkenji"` = 0 hits
  - [ ] `pytest` pass
  - [ ] `docs/STREAMS.md` exists with all 22 streams
  - [ ] Pre-cleanup snapshot tag exists
  - [ ] git log shows cleanup commit on master

### C-10: Operator Onboarding Documentation
- **Type:** Documentation  
- **Priority:** P1  
- **Owner:** Unassigned  
- **Status:** Pending  
- **Description:**  
  Document how new operators claim issues, update status, and sync with team.
  - `docs/LINEAR-WORKFLOW.md`
  - `docs/REPO-RESET-ROADMAP.md`
  - Update `CONTRIBUTING.md`
- **Acceptance Criteria:**
  - [ ] Operators understand role + workflow
  - [ ] 2+ operators ready to claim issues

### C-11: Stream Extraction (Optional Phase 7)
- **Type:** Feature  
- **Priority:** P2  
- **Owner:** Unassigned  
- **Status:** Pending  
- **Description:**  
  Extract Tier 1 streams to separate repos if desired. Keep monorepo for now; decide post-cleanup.
  - For Tier 1 streams (PBFT, mesh, crypto, agent coordination)
  - Option: extract to `lantern-pbft/`, `lantern-mesh/`, etc.
  - Defer decision until Phase C complete
- **Acceptance Criteria:**
  - [ ] Decision made + documented
  - [ ] If extracted: repos created + CI passes

---

## Open Decisions (blocking launch)

| Question | Status | Owner |
|----------|--------|-------|
| Snapshot tag push to remote? | Decision needed | User |
| Duplicate repo consolidation safe? | Pending audit | User |
| Rust rewrite start: after Phase A or parallel? | Decision needed | User |
| Single repo (lantern-os/) or separate? | Decided: Single repo | User |
| License choice (AGPL/proprietary)? | Decision needed | Legal counsel |
| Foundry resource consent UX (panel/tray/config)? | Decision needed | UX |
| Revenue share % (10% Y1 / 15% Y3)? | Decision needed | Finance |

---

## Summary

- **Phase A (1 week):** Discord bot ready ✓ | Archive curator ready ✓ | Linear setup pending
- **Phase B (8 weeks):** Suzie 2.0 Rust/K8s rewrite (not started)
- **Phase C (4 weeks):** Repo cleanup (not started)
- **Total Issues:** 28
- **Est. capacity:** 20 humans + 20 agents (Foundry model)

Ready to import to Linear or start Phase A cleanup now?
