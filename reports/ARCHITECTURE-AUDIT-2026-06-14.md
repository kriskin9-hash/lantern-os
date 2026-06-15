# Architecture Audit — ConvergenceIO, ESF, PCSF, and Related Runtime Systems

**Date:** 2026-06-14
**Scope:** GitHub issue [#395](https://github.com/kriskin9-hash/lanternOS/issues/395) — clean-room inspection, evidence over narrative.
**Method:** Direct code reading + grep across the full repo, plus live runs of `python src/convergence_io_engine.py health` and `inspect`. Every claim below cites a file (and line where useful). No documentation claim was accepted without checking the implementation.

---

## 0. Headline Finding

**"ConvergenceIO" / "Convergence IO" / "Convergence Loop" / "Tesseract" / "Converged Tesseract" / "Tesseract Convergence" / "PCSF" / "NAP" / "AAPF" / "StatusCube" each name TWO OR THREE different things in this repo.** The audit issue itself (#395) conflates at least two of them. This naming collision is the single biggest source of confusion for any future agent or human, and is responsible for most of the "is this real?" uncertainty documented below.

There are exactly **two systems that matter in practice**:

| | `src/convergence_io/` (package) | `src/convergence_io_engine.py` (2,144-line script) |
|---|---|---|
| Doc | `docs/CONVERGENCE-IO-v1.0.0.md` ("Convergence IO v1.0.0") | `docs/TESSERACT-CONVERGENCE-LOOP.md` + AGENTS.md "Tesseract Convergence Loop" |
| Core class | `ConvergenceIO.route_chat()` | `ConvergenceLoop`, `TesseractEngine` |
| Specs/phases | PCSF, CCF, AAPF, NAP, DCF | 20-phase loop (inspect, state_objective, retire_deprecated, map_and_classify, check_architecture, navigate_status_cube, project_future_states, update_beliefs, validate, fix_failures, record_evidence, promote_or_hold, ...) |
| **Status** | **DEAD CODE** — importable, unit-tested, never executed by the running app | **LIVE** — subprocess-called from Node, `health`/`inspect` run successfully today |
| Called from | Nothing in `apps/lantern-garage/` | `lib/stream-chat.js:279`, `routes/operator.js:47`, `routes/keystone.js:44` |

Everything else in this report is detail under that umbrella.

---

## 1. Architecture Map (text)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ LIVE RUNTIME (apps/lantern-garage — Node.js, port 4177)                    │
│                                                                             │
│  routes/dream.js, dreamer.js, status.js, claims.js, cubes.js, ...          │
│       │                                                                    │
│       ├─ lib/stream-chat.js  ── REAL provider chain:                       │
│       │     Ollama(local-first) → Gemini → Anthropic → OpenAI → Grok/xAI   │
│       │     → Ollama(retry) → offline error                               │
│       │     uses lib/provider-cache.js (60s in-mem env-key cache,          │
│       │     success/failure history, NO circuit breaker)                  │
│       │                                                                    │
│       ├─ lib/pcsf-refresh.js ── writes data/pcsf/{settings,provider,       │
│       │     health}.pcsf.json on startup (env-key presence, journal stats) │
│       │                                                                    │
│       ├─ routes/dream.js:810-839 ── hand-rolled "AAPF mirror": writes      │
│       │     data/provenance/actions.jsonl with authority_check HARDCODED   │
│       │     to "passed", capability_claim_id/nap_profile_id/dcf_ref=null   │
│       │                                                                    │
│       ├─ lib/cube-store.js, file-queue.js, conversation-store.js,          │
│       │     dreamer-store.js ── append-only JSONL, full-file reads         │
│       │                                                                    │
│       └─ subprocess → python src/convergence_io_engine.py {health|inspect│
│             |loop|converge}                                                │
│                  │                                                         │
│                  ▼                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ src/convergence_io_engine.py (LIVE, 2144 lines)                       │ │
│  │  ConvergenceLoop (20 phases) ── ValidationRing ── CircuitBreaker      │ │
│  │  ── SlotManager ── MetricsCollector ── NapSafety (3rd NAP impl!)      │ │
│  │  ── TesseractEngine ── WorkerPool ── HeadlessAgentDaemon              │ │
│  │       │                                                                │ │
│  │       ├─ imports src/convergence_io/status_cube.py (StatusCube #2:    │ │
│  │       │    4D x/y/z/t nav + BayesianBelief, Beta-Binomial, REAL math) │ │
│  │       │    → persists data/status-cube.json (62KB, growing)          │ │
│  │       │                                                                │ │
│  │       └─ writes data/agent-fleet/{validation-chain,tesseract-         │ │
│  │            convergence}.jsonl, data/agent-fleet/slots.json            │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ DEAD / ORPHANED CODE (importable, tested in isolation, never executed)     │
│                                                                             │
│  src/convergence_io/engine.py ── ConvergenceIO.route_chat()                │
│     ├─ pcsf.py    (ProviderRegistry, REAL circuit breaker, latent          │
│     │              AttributeError bug in record_success())                 │
│     ├─ ccf.py     (CapabilityGate — real logic, never gates anything)      │
│     ├─ nap.py     (AuthorityGate, NegativeAuthorityProfile — real logic,    │
│     │              local_only_nap() defined but never registered)          │
│     ├─ aapf.py    (ProvenanceLedger — real SHA-256 hashing, never writes)  │
│     └─ dcf.py     (DataClassification — real label propagation, unused)   │
│     _provider_handlers={} always empty → route_chat() ALWAYS falls         │
│     through to canned offline reply (engine.py:160,220-232)               │
│                                                                             │
│  src/converged_tesseract.py ── ConvergedTesseract (3^12 sparse ternary     │
│     matrix, active_wavefront, depends on csf.v07.QuantumDustField)         │
│     implements design doc manifests/CONVERGED-TESSERACT.md.                │
│     Zero references from convergence_io_engine.py's TesseractEngine.       │
│     Used only by tests/test_converged_tesseract.py and                     │
│     scripts/generate_convergence_csf_pdf.py.                               │
│                                                                             │
│  src/tesseract_convergence.py ── 39-line CLEAN backward-compat shim,        │
│     re-exports from convergence_io_engine.py. Not duplication — fine.      │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ PARALLEL "StatusCube #1": src/csf/status_cube.py                           │
│   Per-player Three Doors game state, CSF v0.7 binary (data/csf/<user>.csf)│
│   Used by src/three_doors_engine.py. Unrelated to StatusCube #2 above —    │
│   different classes, different files, different persistence formats,      │
│   filename collision only.                                                 │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ SCORING/RANKING SYSTEMS (4 distinct, 1 stub — no functional overlap)       │
│   1. integrations/human-flourishing-frameworks/world_model.py — real       │
│      Bayesian-ish wellbeing score; /api/flourishing reads a static         │
│      snapshot.json (NOT a live cross-language call)                       │
│   2. src/convergence_io/status_cube.py BayesianBelief — real Beta-Binomial │
│      posterior/confidence on repo-artifact boundary state                  │
│   3. src/converged_tesseract.py — information-density ranking for 3^12     │
│      matrix slice selection (caching concern, not a "wellbeing" score)     │
│   4. scripts/kalshi_odds.py — trading-volume ranking, fully isolated        │
│   5. apps/bettersafe/modules/{safety_monitor,social_services}.py — partial │
│      stub (threat score hardcoded to 0.3); contradicts BACKLOG's "no code  │
│      yet" claim — ~180 lines of real module code exist                     │
└─────────────────────────────────────────────────────────────────────────┘

  ESF ("Event Synchronization Framework"): DOES NOT EXIST anywhere in this
  repository — no code, doc, config, comment, or glossary entry, in any
  casing or abbreviation. Treat as a non-existent/never-built concept.
```

---

## 2. Dependency Map

```
apps/lantern-garage/server.js
 └─ routes/*.js
     ├─ dream.js ───────► lib/stream-chat.js ──► provider-cache.js (live PCSF #2)
     │                 └─► lib/dream-chat.js (retired offline path, 503)
     │                 └─► hand-rolled AAPF mirror → data/provenance/actions.jsonl
     │                 └─► convergence_io.memos_bridge (DIFFERENT submodule,
     │                       MemOS RAG bridge — not route_chat/CCF/NAP/AAPF/DCF)
     ├─ operator.js, keystone.js ─► subprocess ► src/convergence_io_engine.py
     ├─ status.js ──────► provider-cache.getRoutingSnapshot() (/api/pcsf/routing)
     └─ flourishing.js ─► reads integrations/human-flourishing-frameworks/data/
                            snapshot.json (static file, not live Python call)

src/convergence_io_engine.py (LIVE)
 ├─ src/convergence_io/status_cube.py  (StatusCube #2 — Bayesian beliefs)
 ├─ NapSafety (defined in-file, 3rd NAP implementation)
 ├─ ValidationRing → data/agent-fleet/validation-chain.jsonl (real SHA-256 chain,
 │     but "3-agent consensus" = 5 hardcoded validator names re-running the
 │     SAME check function — not independent agents)
 └─ SlotManager → data/agent-fleet/slots.json

src/convergence_io/engine.py (DEAD)
 ├─ pcsf.py  (ProviderRegistry — real circuit breaker, zero callers)
 ├─ ccf.py   (CapabilityGate — zero callers outside its own test)
 ├─ nap.py   (AuthorityGate — zero callers; local_only_nap unregistered)
 ├─ aapf.py  (ProvenanceLedger — zero callers; ProvenanceLedger.record()
 │             never fires — the actions.jsonl entries come from dream.js
 │             instead)
 └─ dcf.py   (DataClassification — zero callers)
   imported ONLY by tests/test_convergence_io.py

src/csf/status_cube.py (StatusCube #1 — unrelated to above)
 └─ used by src/three_doors_engine.py, tests/test_status_cube_game_loop.py,
            scripts/seed_alex_cubes.py
 └─ persists data/csf/<user>.csf (CSF v0.7 binary, via src/csf/v07/csf_file.py)

src/converged_tesseract.py (orphaned design impl)
 └─ src/csf/v07/quantum_dust.py (QuantumDustField)
 └─ used by tests/test_converged_tesseract.py, scripts/generate_convergence_csf_pdf.py

src/tesseract_convergence.py ─► re-exports everything from convergence_io_engine.py
   (clean shim, no independent logic)

src/csf/memory_engine.py (CSF memory engine)
 └─ Tier = TRACE/CORRECTION/ANCHOR/ENTITY/RELATION/RITUAL/SKILL/PROCEDURAL/EXPORT
 └─ CubePartition = RAW/REFINED/CANON/ARCHIVE
 └─ one JSON file per record under data/csf_memory/{partition}/{tier}/
 └─ NOTE: docs/CODEMAP.md §2.6 claims tiers "EPHEMERAL, WORKING, REFINED, SKILL,
        ARCHIVE" — these strings do not exist anywhere in memory_engine.py.
        Either doc drift, or describes a module that was never built.
```

---

## 3. Data-Flow Diagrams

### 3a. Dream chat message (the actual live path)

```
Browser ─POST /api/dream/chat/stream──► routes/dream.js
                                            │
                                            ▼
                                  lib/stream-chat.js: handleStreamChat()
                                            │
                  ┌─────────────────────────┴─────────────────────────┐
                  │ 1. Ollama (local-first, model chain)                │
                  │ 2. Gemini (GEMINI_API_KEY/GOOGLE_API_KEY)           │
                  │ 3. Anthropic (ANTHROPIC_API_KEY)                    │
                  │ 4. OpenAI (OPENAI_API_KEY)                          │
                  │ 5. Grok/xAI (XAI_API_KEY)                           │
                  │ 6. Ollama (retry)                                   │
                  │ 7. streamLocalFallback → "all_providers_failed"     │
                  └─────────────────────────┬─────────────────────────┘
                                            │ each attempt:
                                            ▼
                          provider-cache.recordProviderSuccess/Failure
                          (history only — NO circuit-open logic)
                                            │
                                            ▼
                          dream.js:810-839 "AAPF mirror"
                          → appends data/provenance/actions.jsonl
                            {authority_check: "passed" (HARDCODED),
                             nap_profile_id: null, dcf_ref: null,
                             capability_claim_id: null,
                             integrity_hash: sha256(...)}
```

**No DCF classification, no NAP authority check, no CCF capability check ever
runs on this path.** The provenance record claims `authority_check: "passed"`
unconditionally — this is the audit's most important correctness finding
(§6, risk R1).

### 3b. `python src/convergence_io_engine.py inspect` (verified live, 2026-06-14)

```
ConvergenceLoop.inspect()
  → reads data/agent-fleet/tesseract-convergence.jsonl (last log, 1 line/3KB)
  → src/convergence_io/status_cube.py StatusCube.report()
       → BayesianBelief.update() / .confidence()  [REAL Beta-Binomial math]
       → returns belief_report for 5 dimensions (health, animal, ecosystem,
         economy, culture) — overall_confidence=0.5568 (observed 2026-06-14)
       → projection_report: 143 accumulated projections, by_horizon (1w/...)
         — NO pruning/expiry observed; data/status-cube.json = 62,057 bytes
  → returns {cells:16, slots_active:0, circuits:{}, status_cube:{...}}
```

`circuits: {}` in live output — confirms the live loop's `CircuitBreaker`
class (convergence_io_engine.py) currently has nothing registered, separate
from (and not to be confused with) the dead `pcsf.py` circuit breaker.

---

## 4. Top 10 Technical Debt Items

1. **Two unrelated "ConvergenceIO" systems share a name and a doc prefix.** `src/convergence_io/` (dead, 5-spec library) vs `src/convergence_io_engine.py` (live, 20-phase loop). docs/CONVERGENCE-IO-v1.0.0.md describes the dead one as "Implemented" with zero caveats.
2. **`data/provenance/actions.jsonl` hardcodes `authority_check: "passed"`** for every record (dream.js:826) regardless of whether any authority check ran — the live NAP/CCF/DCF gates described in docs do not exist on this path (engine.py route_chat() is dead). This is compliance-theater: the audit trail looks like gates fired when they didn't.
3. **Three independent "NAP" implementations**: `src/convergence_io/nap.py` (`AuthorityGate`, dead), `convergence_io_engine.py`'s in-file `NapSafety` (live, used at line 714), and the hardcoded `"passed"` stamp in dream.js. None of the three talk to each other.
4. **`src/convergence_io/pcsf.py` has a latent `AttributeError`**: `record_success()` references `self.latency_p50_ms`, which is never declared as a dataclass field (only `latency_ema_ms`/`latency_p99_ms` exist). Currently masked because nothing calls this module.
5. **Real provider fallback chain matches none of the three documented chains.** Code: Ollama→Gemini→Anthropic→OpenAI→Grok/xAI→Ollama→offline. Docs variously claim Anthropic→OpenAI→Google→Groq→DeepSeek→Ollama→Offline (pcsf.py), Gemini→Claude→OpenAI→Ollama→503 (CLAUDE.md), and Gemini→Claude→OpenAI→Grok→Ollama (stream-chat.js's own inline comment).
6. **docs/CODEMAP.md §2.6 CSF memory tier names (EPHEMERAL/WORKING/REFINED/SKILL/ARCHIVE) don't match `src/csf/memory_engine.py`** (actual: TRACE/CORRECTION/ANCHOR/ENTITY/RELATION/RITUAL/SKILL/PROCEDURAL/EXPORT + RAW/REFINED/CANON/ARCHIVE partitions). Either stale docs or an undelivered module.
7. **"3-agent consensus" validation ring is actually 5 hardcoded validator names** (`alpha..epsilon`) each re-running the *same* local check function (`_simulate_validators`, convergence_io_engine.py:598-618) — the SHA-256 hash chain itself is real and unbroken (verified 10/10 records), but "consensus" provides no independent verification today.
8. **`write_async()` in memory_engine.py is not async I/O** — `_async_write` is `async def` but its body directly calls the synchronous `write()` (blocking `open()`/`json.dump()`); "queue depth tracking" is real, "async writes" as a concurrency claim is not.
9. **Stale v06 archival bookkeeping**: `src/csf/v06/` is already gone from `src/` (moved outside the repo to `D:\tmp\lantern-os-archive-2026-06-10`), but `BACKLOG-2026-06-10.md:60` still lists it as an unchecked TODO, and `docs/benchmarks/{csf_v07_benchmark,csf_benchmark}.py` still contain dead `from csf.v06...` imports that would now raise `ModuleNotFoundError`.
10. **`data/status-cube.json` grows unbounded** — 143 accumulated `projection_report` entries (62KB and climbing) with no observed pruning/expiry/TTL in Phase 13 (`project_future_states`).

---

## 5. Top 10 Simplification Opportunities

1. **Delete or explicitly archive `src/convergence_io/engine.py` + ccf.py/nap.py/aapf.py/dcf.py/pcsf.py** (the dead 5-spec library) — or, if the intent is real, wire `route_chat()` into `dream.js` and retire the hand-rolled AAPF mirror. Don't leave both. This single change resolves debt items #1–4.
2. **Rename one of the two "ConvergenceIO" things.** Even just renaming `src/convergence_io/` → `src/convergence_io_specs/` (or similar) and retitling docs/CONVERGENCE-IO-v1.0.0.md would eliminate most of the confusion issue #395 itself exhibits.
3. **Replace the hardcoded `authority_check: "passed"` / `null` fields in dream.js:820-826** with either (a) a real call into the live `NapSafety` class already in `convergence_io_engine.py`, or (b) explicit `"not_evaluated"` values so the audit trail doesn't overclaim.
4. **Pick ONE provider-chain definition** and make pcsf.py / CLAUDE.md / stream-chat.js's comment agree with it (or delete the two that aren't load-bearing).
5. **Fix or delete `src/convergence_io/pcsf.py`'s `record_success()`** — either add the missing `latency_p50_ms` field or remove the dead p50 tracking code.
6. **Either integrate `src/converged_tesseract.py`'s `ConvergedTesseract`/`active_wavefront` into `TesseractEngine`'s phases, or move it out of `src/` into an explicitly-experimental location** — right now it's a fully-implemented, tested, but disconnected design contract sitting alongside the live engine with overlapping vocabulary.
7. **Reconcile docs/CODEMAP.md §2.6's tier names with `src/csf/memory_engine.py`'s actual `Tier`/`CubePartition` enums** — pick the real names and fix the doc, or note the doc describes a planned-but-unbuilt variant.
8. **Either implement independent validators for the validation ring, or rename "3-agent consensus" to something accurate** (e.g. "repeated self-check with hash-chained receipts") — the hash chain itself is solid and worth keeping as-is.
9. **Add a TTL/cap to `projection_report` in `src/convergence_io/status_cube.py`** (Phase 13) — e.g. keep only the latest N projections per artifact/horizon, since nothing currently prunes it.
10. **Remove the two dead `from csf.v06...` imports** in `docs/benchmarks/csf_v07_benchmark.py` and `csf_benchmark.py`, and correct `BACKLOG-2026-06-10.md:60`'s stale checkbox (the archival already happened, just not to the path the backlog names).

---

## 6. Top 5 Convergence Risks

- **R1 — Compliance-theater provenance (highest).** `data/provenance/actions.jsonl` (14/14 live records) stamps `authority_check: "passed"` unconditionally via dream.js's hand-rolled mirror, while the actual NAP/CCF/DCF gates described in docs/CONVERGENCE-IO-v1.0.0.md are dead code that never executes. Any future audit, dashboard, or compliance report reading this file will believe authority checks are enforced when they are not.
- **R2 — Naming-collision-driven duplicate work.** With "ConvergenceIO," "StatusCube," "NAP," "PCSF," and "Tesseract" each referring to 2-3 different real or dead systems, future agents (including this audit's requester) will keep re-discovering, re-auditing, or re-implementing the same concepts under the same names. Issue #395 itself asked to audit "ESF" (doesn't exist) and treated "ConvergenceIO" as singular.
- **R3 — `_provider_handlers={}` makes `route_chat()` a silent no-op.** If anything ever DOES start calling `src/convergence_io/engine.py` (e.g. a future "let's use the documented Convergence IO" effort), `route_chat()` will silently return canned offline replies for every message until `register_provider_handler()` is called somewhere — there's no error, no warning, just always-offline.
- **R4 — Validation ring "consensus" is currently a single-point-of-failure dressed as redundancy.** `_simulate_validators` runs the same `job["check"]()` 5 times; if that one check function has a bug, all 5 "validators" agree on the wrong answer with `consensus_ratio: 1.0`, providing false confidence via a cryptographically-real-looking hash chain.
- **R5 — Unbounded `data/status-cube.json` growth feeds directly into `inspect`/`health`,** which AGENTS.md tells every agent to run *before* reading source. As this file grows (143 projections already), the "cheap pre-flight check" that's supposed to save tokens will itself become an increasingly large context cost.

---

## 7. Top 5 Performance Risks

- **P1 — Full-file JSONL reads with no pagination.** `cube-store.js`, `file-queue.js`, `conversation-store.js`, `dreamer-store.js` all do `readFileSync(...).split("\n")` then slice to a `limit`. Currently all files are <70KB (negligible), but the cost is O(total history) per read regardless of `limit`, with zero rotation/compaction anywhere in the codebase.
- **P2 — `data/status-cube.json` (62KB, 143 projections) is read/written on every `inspect`/`health` call** and has no pruning — this is the fastest-growing state file found and sits on the "run before exploring" hot path (AGENTS.md rule 2).
- **P3 — `src/csf/memory_engine.py` writes one JSON file per memory record** with no batching, plus fully-in-memory `defaultdict(set)` keyword/entity indexes serialized whole to `_index.json` on every write — this will degrade linearly with total memory count, with no tiering/eviction to bound it.
- **P4 — `write_async()` doesn't actually offload I/O** (synchronous `open()`/`json.dump()` inside an `async def` that's `create_task()`'d) — under concurrent load this blocks the event loop exactly like a sync call while *appearing* non-blocking to callers, which could mask contention until it's severe.
- **P5 — The live provider chain tries up to 6 providers sequentially with no circuit breaker** (Ollama→Gemini→Anthropic→OpenAI→Grok/xAI→Ollama→offline) — a single consistently-down provider (e.g. bad API key) adds its full timeout to every chat request indefinitely, since `provider-cache.js` tracks failure history but never short-circuits future attempts.

---

## 8. Recommended Roadmap (ordered by impact)

1. **Fix R1/debt#2 — stop overclaiming authority checks.** Smallest change, biggest integrity fix: change dream.js:820-826 to write `authority_check: "not_evaluated"` (or wire in the live `NapSafety` class from `convergence_io_engine.py`, which already runs in-process via subprocess and could be queried). This is a doc-and-data-honesty fix, not a redesign.
2. **Resolve the "two ConvergenceIO systems" naming collision (R2, debt#1/#3).** Decide: is `src/convergence_io/` (dead 5-spec library) worth finishing and wiring in, or should it be archived/deleted with docs/CONVERGENCE-IO-v1.0.0.md marked superseded-by `docs/TESSERACT-CONVERGENCE-LOOP.md`? Either answer is fine; the current "both exist, both claim 'Implemented'" state is not.
3. **Add a pruning/TTL policy to `status_cube.py`'s `projection_report`** (P2/R5) before it grows further — it's already the largest and fastest-growing piece of state on the agent pre-flight hot path.
4. **Decide the fate of `src/converged_tesseract.py`** (debt#6) — integrate into `TesseractEngine`'s phases or move out of `src/` with a note that it's an unconnected design-contract implementation. Low urgency but actively confusing given `manifests/CONVERGED-TESSERACT.md` reads as if it's part of the live loop.
5. **Pick and document ONE provider fallback chain** (debt#5) and delete/correct the other two written descriptions — low effort, removes a recurring "which chain is real?" question for every future agent.
6. **Decouple "validation ring consensus" claims from reality** (R4/debt#7) — either implement genuinely independent checks per validator or rename the field/docs so `consensus_ratio: 1.0` doesn't imply 3-5 independent agents agreed.
7. **Address JSONL growth (P1) proactively** — add simple rotation (e.g. monthly files, as `data/dream_journal/dreams_2026-06.jsonl` already does for one store) to `cube-store.js`/`conversation-store.js`/`dreamer-store.js` before any of them cross ~1MB.
8. **Small cleanups, batch together**: fix `pcsf.py`'s `latency_p50_ms` field (debt#4), remove dead `csf.v06` imports in benchmark scripts (debt#9 part 2), correct `BACKLOG-2026-06-10.md:60`'s stale checkbox (debt#9 part 1), and reconcile `docs/CODEMAP.md` §2.6 tier names with `memory_engine.py`'s actual enums (debt#6/simplification#7).
9. **Memory engine scaling (P3)**: if `data/csf_memory/` usage grows beyond hand-seeded samples, revisit the one-file-per-record + whole-index-in-memory design before it's exercised at scale — not urgent today (current data is small, hand-seeded).
10. **`write_async()` real-async fix (P4/debt#8)**: low priority unless/until concurrent write load becomes observable — the current queue-depth tracking already provides visibility into the problem if it emerges.

---

## Stable vs Unstable Modules (summary)

| Module | Status |
|---|---|
| `src/convergence_io_engine.py` (20-phase loop) | **Stable & live** — `health`/`inspect` verified working 2026-06-14 |
| `src/convergence_io/status_cube.py` (Bayesian StatusCube) | **Stable & live**, but unbounded growth (R5/P2) |
| `apps/lantern-garage/lib/stream-chat.js` provider chain | **Live**, functioning, but undocumented-accurately and no circuit breaker (P5) |
| `apps/lantern-garage/lib/{provider-cache,pcsf-refresh}.js` | **Live**, working as a cache/refresher — not a circuit breaker despite naming |
| `src/csf/status_cube.py` + `three_doors_engine.py` | **Stable & live** — separate system, no issues found |
| `src/tesseract_convergence.py` (shim) | **Stable** — clean, no action needed |
| `src/converged_tesseract.py` | **Implemented & tested, but orphaned** — not wired into anything live |
| `src/convergence_io/engine.py` + ccf/nap/aapf/dcf/pcsf.py | **Dead code** — implemented, unit-tested, never executed |
| `data/provenance/actions.jsonl` pipeline | **Live but misleading** (R1) — needs the fix in roadmap item 1 |
| `data/agent-fleet/validation-chain.jsonl` | **Live, hash chain sound, "consensus" semantics weak** (R4) |
| `apps/bettersafe/modules/*` | **Partial scaffold** — real code exists (contra BACKLOG), scoring is stubbed |
| ESF (Event Synchronization Framework) | **Does not exist** — no action possible or needed |

---

*This report synthesizes direct file reads, repo-wide greps, and two live `convergence_io_engine.py` invocations performed on 2026-06-14. No content was generated by running the system's own LLM-backed `converge` command (per operator instruction to avoid additional model calls during this audit).*
