# Dream Journal === ORION === Roadmap (Canonical)

**Updated:** June 4, 2026

---

## 0. Agent Contract — Integration Hooks

This section documents how the Dream Journal, Convergence IO, and CSF are wired together.

### Integration Map

```
Dream Journal Orchestrator
    → DCF: classify new dreams (dream_content, symbolic_data, user_identity)
    → CCF: verify bot capabilities before response generation
    → NAP: check tier-based restrictions (art limits, content policy)
    → AAPF: record provenance for every dream_processed action
    → CSF: export dreams + DCF labels + CIO snapshot as delta records
```

### Hook Points

| Hook | File | Description |
|---|---|---|
| `add_dream()` DCF classification | `src/dream_journal/orchestrator.py:217` | Every new dream gets DCF labels auto-assigned |
| `process_dream()` AAPF provenance | `src/dream_journal/orchestrator.py:285` | ActionRecord with integrity hash written to ledger |
| `export_csf()` CIO embedding | `src/dream_journal/orchestrator.py:376` | CSF delta payload includes DCF + CIO health snapshot |
| `ConvergenceIO` init | `src/dream_journal/orchestrator.py:147` | CIO engine instantiated with repo_root for full RPS |

### Data Flow

1. **Dream Entry** → DCF classified (`dream_content`, `symbolic_data`)
2. **Bot Selection** → CCF check (do bots claim `dream_process` capability?)
3. **Response** → NAP check (tier enforcement: Wanderer vs DeepDreamer vs Guild)
4. **Archive** → CSF export with embedded DCF + CIO metadata
5. **Audit** → AAPF ledger with SHA-256 integrity proof

---

## 1. What Changed from CSF to Convergence IO

**CSF (Convergence Symbolic Format)** was the data storage and compression format — focused on symbolic memory, sparse matrices, qutrit-inspired encoding, and efficient storage of dreams and lore.

**Convergence IO** is the evolution — the active runtime intelligence system built on top of CSF. It adds real-time provider monitoring, intelligent fallback routing, regulatory-grade primitives, and tier-aware behavior.

| Aspect | CSF (Old) | Convergence IO (New) |
|---|---|---|
| Scope | Data format + storage | Full runtime execution engine |
| Main Focus | Symbolic compression & memory | Intelligent routing + decision making |
| Fallback System | Basic offline fallback | Full multi-provider chain: Claude → Gemini → OpenAI → Ollama → Offline |
| Regulatory Stack | Not integrated | All 5 RPS primitives (PCSF, CCF, AAPF, NAP, DCF) |
| Tier Integration | Not tied to tiers | Directly powers Wanderer / DeepDreamer / Guild behavior |

**CSF = The Archive** (how we store dreams and symbols efficiently).
**Convergence IO = The Brain** (how we decide which model to use, when to fallback, what we're allowed to do, and how we prove it).

---

## 1. Convergence IO — Regulatory Primitive Stack (RPS)

### All 5 Primitives — Side-by-Side

| Primitive | Full Name | Core Question | Main Focus | Example in ORION |
|---|---|---|---|---|
| **PCSF** | Provider Capacity State Format | "Is the backend healthy?" | Availability & Health | Tracks Claude, Gemini, Ollama health, quota, latency |
| **CCF** | Capability Claim Format | "What can the agent do?" | Positive Claims | "I can generate Gage art" (DeepDreamer+ only) |
| **NAP** | Negative Authority Profiles | "What is forbidden?" | Restrictions & Safety | Blocks NSFW, limits free users to 15 art/month |
| **DCF** | Data Classification Format | "How sensitive is this?" | Privacy & Data Handling | Marks dreams as Private, Symbolic, or Shared |
| **AAPF** | Agent Action Provenance Format | "What exactly happened?" | Audit & Traceability | Logs which model answered, which tier, which NAP triggered |

### How They Work Together

```
Incoming Request
    → DCF (classify data sensitivity)
    → CCF (does agent claim capability?)
    → NAP (is action forbidden?)
    → PCSF (which provider is available?)
    → EXECUTE
    → AAPF (record everything)
```

### Primitive Details

#### PCSF — Provider Capacity State Format

Tracks real-time health of every AI provider. Includes:

| Primitive | What It Tracks | Example |
|---|---|---|
| P1 Provider Identity | Unique identifier | `claude-3.5-sonnet`, `ollama-llama3.1` |
| P2 Capacity State | Operational status | `healthy`, `degraded`, `rate-limited`, `offline` |
| P3 Quota Tracking | Remaining tokens/requests | `"12,450 / 50,000 tokens left"` |
| P4 Latency & Performance | Response time & reliability | `1.2s avg, 98.7% success` |
| P5 Priority Level | Tier-based priority | Guild > DeepDreamer > Wanderer |
| P6 Fallback Order | Routing sequence | Claude → Gemini → OpenAI → Ollama → Offline |
| P7 Health Timestamp | Last check time | `2026-06-04T09:08:22Z` |
| P8 Recovery Strategy | What to do on failure | Auto-retry, switch provider, cached persona |
| P9 Provenance Tag | Which provider answered | `{ "source": "claude", "model": "claude-3.5-sonnet" }` |

#### CCF — Capability Claim Format

The "ID Card + License" system for AI agents. Includes:

| Primitive | What It Does | Example |
|---|---|---|
| C1 Capability Declaration | What agent says it can do | "I can generate Gage doodles" |
| C2 Proof of Capability | Evidence claim is true | "Art model available + quota OK" |
| C3 Scope & Limitations | Where/when it applies | "Unlimited for DeepDreamer, 15/month for Wanderer" |
| C4 Temporal Validity | How long claim is valid | `60` seconds (auto-expires) |
| C5 Dependency Chain | What capability depends on | "Art depends on PCSF showing healthy provider" |
| C6 Revocation Trigger | When to withdraw | "If rate limit hit → revoke immediately" |
| C7 Honesty Score | Historical truthfulness | `0.95` (95% of claims were valid) |

#### NAP — Negative Authority Profiles

The restriction and denial system. Includes:

| Primitive | What It Does | Example |
|---|---|---|
| N1 Negative Authority | List of forbidden actions | "No NSFW, no medical advice" |
| N2 Condition Triggers | When restriction activates | "If user is Wanderer tier" |
| N3 Denial Response | How to respond | Graceful message + suggestion + offline fallback |
| N4 Scope | Where restriction applies | "Only applies to art generation" |
| N5 Dynamic External Lists | Real-time restrictions | Safety classifiers, block lists |
| N6 Audit Logging | Record every denial | AAPF log: "Denied — NAP N1 triggered for Wanderer" |
| N7 Override & Escalation | When restrictions bypass | "Synthesasia Guild can override certain NAPs" |

#### DCF — Data Classification Format

Classifies data sensitivity. Includes:

| Primitive | What It Does | Example |
|---|---|---|
| D1 Classification Label | Sensitivity level | `Private`, `Symbolic`, `Shared`, `Public` |
| D2 Propagation Rules | Classification travels | Private dream → private art (inheritance) |
| D3 Handling Policies | Allowed actions per class | Private dreams cannot be used for public generation |
| D4 User Consent | User can change classification | Mark dream as "Shareable" after review |
| D5 Retention Rules | When data must be deleted | "Auto-delete Private dreams after 90 days" |
| D6 Audit Tagging | Record classification decisions | Every dream gets DCF tag in AAPF logs |
| D7 Cross-Boundary Controls | Moving data between systems | Prevent sending Private to external providers |

#### AAPF — Agent Action Provenance Format

The "black box / flight recorder" for every action. Includes:

| Primitive | What It Does | Example |
|---|---|---|
| A1 Action ID | Unique identifier | `aapf_20260604_091234_dream_78491` |
| A2 Timestamp & Sequence | Precise time and ordering | `2026-06-04T09:12:34.567Z` |
| A3 Actor Identity | Who performed action | `user:alex_place`, `tier:DeepDreamer` |
| A4 Action Type | Category | `dream_entry_create`, `art_generate_gage` |
| A5 Input Context | What was submitted | Dream text, user prompt |
| A6 Output Result | What was produced | Reply text, image ID |
| A7 CCF Reference | Which capability claimed | `ccf:art_generation_v1` |
| A8 PCSF Provider Used | Which provider handled it | `claude-3.5-sonnet`, `ollama-llama3.1:8b` |
| A9 NAP Rules Triggered | Any restrictions applied | `nap:rate_limit_wanderer` |
| A10 DCF Classification | Data sensitivity at time | `Private`, `Symbolic` |
| A11 User Tier & Consent | Tier and consent state | `DeepDreamer`, `consent:explicit` |
| A12 Integrity Proof | Cryptographic hash | `SHA-256` hash of entire record |

---

## 2. Vision

ORION is a local-first, symbolic, artistic dream journal that treats dreams as sacred territory. It combines raw hand-drawn expression (Gage style), intelligent AI (Convergence IO), and evolving symbolic gameplay (3 Door Game).

### Tier Structure (Locked)

| Tier | Price | Position |
|---|---|---|
| **Wanderer** | Free (7-day DeepDreamer trial) | Entry point |
| **DeepDreamer** | $20/month | Core paid tier |
| **Synthesasia Guild** | $200/month | Premium / team tier |

---

## 3. Phased Roadmap

### Phase 1: v1.0.0 — Foundation (Target: Mid-to-Late June 2026)

**Focus:** Solid, usable core with strong artistic identity and local-first architecture.

**Key Deliverables:**

- Fast dream logging (text + voice)
- Raw Gage hand-drawn doodle art generation pipeline
- Convergence IO v1.1.0 with full RPS (PCSF, CCF, AAPF, NAP, DCF)
- Symbolic tagging + DCF classification
- AAPF provenance logging with integrity hashes
- Local Docker + Ollama setup (fully offline capable)
- Tier system foundation with Convergence IO enforcement
- Full 3 Door Game Design Document (ships v1.0.1)
- Welcome marketing assets (pastel banner, first Patreon post)

**Current Confidence:**

| Milestone | Status |
|---|---|
| By June 4 | 76% |
| By June 6 | 91% |

**Completed (June 4):**
- Convergence IO v1.1.0 implemented (`src/convergence_io/`)
- PCSF: tier-aware routing, last_checked timestamps, quota tracking
- CCF: temporal validity (expiring claims), honesty scores, tier enforcement
- NAP: tier overrides (Guild bypasses certain restrictions)
- DCF: retention policies, derive() propagation (private dream → private art)
- AAPF: SHA-256 integrity hashes, cross-references to CCF/NAP/DCF, tier + consent fields
- MCP server fixed (restarted from new path, `-NoLogo` fix)
- `.env.local` dotenv loading across all MCP/orchestration scripts

---

### Phase 2: v1.0.1 — The 3 Door Game (Target: Late June / Early July 2026)

**Focus:** Make the journal alive and interactive.

**Key Deliverables:**

- Full interactive 3 Door Game with Information Cards
- Comment-driven door evolution using CSF + Convergence IO
- Enhanced AAPF with blockchain hash anchoring (optional for Guild)
- Advanced symbolic tools (void/light balance, mystery tracking)
- Improved Convergence IO with full NAP + CCF enforcement
- Tier-specific experiences fully activated

---

### Phase 3: v1.0.2 — Depth & Polish (July 2026)

- Dream pattern analysis dashboard
- Lucid dreaming tools (MILD/WBTB tracking, reality checks)
- Enhanced Discord bot integration
- Full DCF privacy controls + export tools
- Mobile-friendly web UI improvements

---

### Phase 4: v1.1 — Convergence & Guild Features (August 2026)

- Team / multi-user support for Synthesasia Guild
- Shared symbolic archives
- Advanced blockchain audit trails (full AAPF on-chain)
- Custom art style training
- API access for Guild members

---

## 4. Feature Requirements by Tier (v1.0.0+)

| Feature Area | Wanderer (Free) | DeepDreamer ($20) | Synthesasia Guild ($200) | Notes |
|---|---|---|---|---|
| **Dream Logging** | Basic text + voice | Full features + emotion/symbol tagging | Full + team/shared logging | Core for all tiers |
| **Raw Gage Art Generation** | Limited (10–15/month) | Unlimited | Unlimited + priority queue | Major differentiator |
| **3 Door Game** | Basic / limited plays | Full access + Information Cards | Full + team/custom instances | Plan documented in v1.0.0 |
| **CSF Memory** | Basic export | Advanced (delta, search, merging) | Advanced + team/shared archives | Foundation in v1.0.0 |
| **Convergence IO** | Basic fallback | Full CCF/NAP/DCF enforcement | Full + blockchain AAPF | v1.1.0 implemented |
| **Symbolic Tools** | Basic tagging | Advanced (void/light, mystery tracking) | Advanced + custom symbols | Strong in v1.0.0 |
| **Local-First / Offline** | Yes | Yes | Yes + team deployment support | Core requirement |
| **Discord Integration** | Read-only + limited channels | Full role + private channels | Dedicated / private server options | Tied to tiers |
| **Support** | Community | Priority | Direct + custom | — |
| **Team / Multi-user** | No | No | Yes | Guild only |
| **Custom / White-label** | No | No | On request | Guild only |

---

## 5. Feature Maturity by Version

| Feature | v1.0.0 | v1.0.1 | v1.0.2 | v1.1 |
|---|---|---|---|---|
| Dream Logging + Voice | Full | Full | Full | Full |
| Raw Gage Art Generation | Strong | Unlimited | Unlimited | Unlimited |
| Convergence IO + RPS | Full (v1.1.0) | Strong | Strong | Advanced |
| 3 Door Game | Design | Full | Enhanced | Team/Custom |
| Symbolic Tools & Mystery | Basic | Strong | Advanced | Advanced |
| AAPF Provenance | Full + integrity | Full | Full | Blockchain |
| Tier System Enforcement | Full (Convergence IO) | Full | Full | Advanced |

---

## 6. Confidence Table – v1.0.0 Features

| Feature | Confidence by June 4 | Confidence by June 6 | Priority | Notes |
|---|---|---|---|---|
| Basic dream logging (text + voice) | 95% | 100% | High | Very strong |
| Emotion + symbol tagging | 72% | 88% | High | Needs work |
| Raw Gage doodle art generation | 78% | 93% | High | Good progress |
| Unlimited art for DeepDreamer tier | 65% | 85% | High | Main remaining task |
| CSF basic storage + export | 70% | 88% | High | Core foundation |
| Advanced CSF (delta + search) | 60% | 82% | High | Biggest gap |
| Local Docker + offline mode | 85% | 95% | High | Strong |
| 3 Door Game Design Plan | 100% | 100% | High | Already complete |
| Symbolic tagging system | 68% | 85% | Medium | Needs refinement |
| Discord role + channel setup | 75% | 90% | Medium | Straightforward |
| **Convergence IO v1.1.0** | **100%** | **100%** | **High** | **Implemented June 4** |
| **Overall v1.0.0 Readiness** | **74%** | **89%** | — | Realistic target |

---

## 7. Key Deliverables for v1.0.0

### Must Have (High Confidence)

- Core dream logging with voice support
- Raw Gage doodle art generation pipeline
- Local-first Docker + Ollama setup
- Basic CSF storage and export
- Symbolic tagging foundation
- **Convergence IO v1.1.0 with full RPS (DONE)**
- Full documentation of the 3 Door Game plan
- Patreon tier structure (Wanderer / DeepDreamer / Synthesasia Guild)
- Marketing assets (welcome banner in pastel style)

### Should Have (Target for June 6)

- Unlimited art generation for paid tiers
- Advanced CSF features (delta compression + search)
- Refined symbolic tools (void/light balance, mystery tracking)
- Discord integration with proper roles

### Nice to Have (Lower Priority for v1.0.0)

- Full interactive 3 Door Game (moved to v1.0.1)
- Team features for Synthesasia Guild
- Advanced analytics

---

## 8. Implementation Notes

### Convergence IO File Map

| File | Purpose |
|---|---|
| `src/convergence_io/__init__.py` | Package exports, v1.1.0 |
| `src/convergence_io/pcsf.py` | Provider health, tier priority, quota tracking |
| `src/convergence_io/ccf.py` | Capability claims, temporal validity, honesty scores |
| `src/convergence_io/nap.py` | Denial rules, tier overrides |
| `src/convergence_io/dcf.py` | Data classification, retention, propagation |
| `src/convergence_io/aapf.py` | Audit trail, integrity hashes, cross-references |
| `src/convergence_io/engine.py` | Unified orchestration engine |

### MCP/Orchestration Fixes (June 4)

- MCP server killed at old path (`C:\Users\alexp\Documents\gm-agent-orchestrator`)
- Restarted from new path (`C:\Users\alexp\OneDrive\Documents\GitHub\gm-agent-orchestrator`)
- Added `-NoLogo` to all PowerShell subprocess invocations to prevent banner pollution of JSON
- `.env.local` dotenv loading added to all MCP scripts:
  - `scripts/mcp_stdio_bridge.py`
  - `src/mcp_server/server.py`
  - `src/discord_lounge_bot/mcp_bridge.py`
  - `src/dream_journal/orchestrator.py`

---

## Summary

v1.0.0 is positioned as a strong foundation release focused on logging, artistic expression, local ownership, and now — full regulatory-grade AI decision-making via Convergence IO.

The biggest gap closed on June 4 is the complete RPS implementation. The system now has real-time provider monitoring, tier-aware routing, expiring capability claims, honesty tracking, tier override on denials, data classification with retention and propagation, and tamper-evident audit trails.

The 3 Door Game is fully planned and documented in v1.0.0 but will launch as a major feature in v1.0.1.

Overall confidence for a solid v1.0.0 release by mid-to-late June is strong (89% by June 6) with Convergence IO now fully implemented.

---

## 9. Convergence Refinements — 2026-06-05

Source: 2026 State of AI Agent Memory (Mem0, ECAI 2025/2026 arXiv:2504.19413) and MemOS architecture analysis.

These refinements extend the CSF Memory Engine and Convergence IO based on production patterns emerging across the agent memory ecosystem.

### 9.1 Multi-Signal Retrieval (CSF Engine)

**Problem:** CSF retrieval uses vector similarity alone. Production systems in 2026 fuse semantic + keyword + entity scoring.

**Plan:**
- Add `keywords: list[str]` to `MemoryRecord` (extracted at ingestion)
- Add `{collection}_entities` parallel collection (extracted nouns/proper nouns)
- Implement three-pass retrieval:
  1. Vector similarity (existing)
  2. BM25 keyword matching on `keywords`
  3. Entity overlap scoring against query entities
- Fuse: `score = 0.5*semantic + 0.3*keyword + 0.2*entity`

**Target:** `src/csf/memory_engine.py`, `caad/schema/memory.schema.json`
**Priority:** P0

### 9.2 Procedural Memory Tier

**Problem:** No explicit "how" tier. Agents need to remember workflows, tool-use habits, review conventions.

**Plan:**
- Add `PROCEDURAL` to `Tier` enum
- Factory `create_procedure()` with:
  - `steps: list[str]`
  - `tool_invocations: list[str]`
  - `success_rate: float`
  - `last_applied: ISO8601`
- Promote to `SKILL` on crystallization, keep `PROCEDURAL` trace

**Target:** `src/csf/memory_engine.py`, `caad/schema/memory.schema.json`
**Priority:** P1

### 9.3 Async Memory Writes

**Problem:** Synchronous writes block response pipeline. Mem0 fixed this by making `async_mode=True` default.

**Plan:**
- Add `write_async()` to `MemoryEngine` using `asyncio.create_task()`
- Track pending write queue depth
- Expose queue depth in debug panel analytics

**Target:** `src/csf/memory_engine.py`, `apps/lantern-garage/public/dream-chat.html`
**Priority:** P0

### 9.4 Actor-Aware Provenance

**Problem:** "User needs help with deployment" is ambiguous. Was it stated, inferred, or created by an agent?

**Plan:**
- Expand `source_surface` → `actor_id`, `actor_type` (`user | agent | system | inferred`)
- Add `confidence_reasoning: str` explaining why memory exists
- Show provenance column in debug panel for recent memories

**Target:** `caad/schema/memory.schema.json`, `src/csf/memory_engine.py`
**Priority:** P1

### 9.5 Memory Staleness Detection

**Problem:** High-confidence memory becomes confidently wrong (e.g., user changes jobs). Decay handles low-relevance; staleness handles high-relevance contradictions.

**Plan:**
- Add `staleness_signals: list[str]` to `MemoryRecord`
- On ingestion, run lightweight contradiction check against same-entity memories
- If contradiction > threshold, mark old memory `confidence *= 0.5`
- Track stale corrections in debug panel

**Target:** `src/csf/memory_engine.py`
**Priority:** P2

### 9.6 Temporal Abstraction in Lineage

**Problem:** Moving NY → SF should be stored as evolution, not replacement.

**Plan:**
- Extend `promotion_lineage` with:
  - `lineage_event: { type: "creation" | "promotion" | "correction" | "evolution", from_memory_id: str | null, reason: str }`
- On entity update, create `EVOLUTION` entry linking old → new
- Keep both in `REFINED` cube with temporal validity flags

**Target:** `src/csf/memory_engine.py`, `caad/schema/memory.schema.json`
**Priority:** P2

### 9.7 Metadata Filtering API

**Problem:** Retrieval is purely semantic. Scoped queries need structured filtering.

**Plan:**
- Add `metadata: dict[str, Any]` to `MemoryRecord`
- Extend `query()` with `metadata_filter: dict`
- Example: `engine.query("deployment", metadata_filter={"project": "lantern-garage", "privacy_scope": "local"})`

**Target:** `src/csf/memory_engine.py`
**Priority:** P3

### Implementation Priority

| Priority | Feature | Effort | Impact |
|----------|---------|--------|--------|
| **P0** | Async writes | 1 file | Immediate UX |
| **P0** | Multi-signal retrieval | 2 files | +29% recall |
| **P1** | Procedural tier | 3 files | Agent capability |
| **P1** | Actor provenance | 2 files | Multi-agent reliability |
| **P2** | Staleness detection | 2 files | Long-term accuracy |
| **P2** | Temporal lineage | 2 files | Memory evolution |
| **P3** | Metadata filtering | 2 files | Query precision |


---

## Appendix: Convergence Engine Improvements (Planned)

Tracked in GitHub issues. These refine the Convergence IO runtime without changing user-facing behavior.

| Issue | Title | Priority | File |
|---|---|---|---|
| #142 | Add Watch/Observe phase for drift detection | Medium | `src/convergence_io_engine.py` |
| #143 | Backpressure + rate limiting on TesseractEngine | High | `src/convergence_io_engine.py` |
| #145 | Structured trace logging (OpenTelemetry-style spans) | Medium | `src/convergence_io_engine.py` |
| #146 | Idempotent slot claims (deterministic slot IDs) | Medium | `src/convergence_io_engine.py` |
| #147 | Graduated degradation (layer-by-layer fallback) | High | `src/convergence_io_engine.py` |
| #144 | Receipt diff (compare current vs previous run) | Low | `src/convergence_io_engine.py` |
| #148 | PII cleanup -- remove "waynesville" from persona matcher | High | `src/convergence_io_engine.py` |

**Design principles:**
- No infinite loops; explicit triggers only
- Local-first; cloud mirrors validate but don't own state
- Receipts are read-only evidence; never self-modify without operator approval
