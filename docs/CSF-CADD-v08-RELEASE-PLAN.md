# CSF v0.8 + CADD v0.2 Release Plan

Date: 2026-06-03  
Target release: 2026-07-01  
Status: Planning

---

## Executive Summary

This release ships two complementary systems:

- **CSF v0.8** — The compression/archive format matures from prototype to production candidate. Rust native implementation, real-world benchmarks, honest positioning.
- **CADD v0.2** — The brand/asset intake pipeline (Capture, Assess, Distill, Dock) gets automation, validation, and integration with the RAG dollhouse.

Both systems are infrastructure. Neither is user-facing directly. Both must be reliable enough that upstream products (Dream Journal, Lantern Garage, ImaginVerse) can depend on them without thinking about them.

---

## Part 1: CSF v0.8 — Convergence-Fitted Searchable Archive

### 1.1 Honest Positioning (already done)

CSF is **not** a universal compression replacement for gzip/zstd.

- **It IS** a searchable archive format for structured data (logs, JSON, configs, code).
- **It IS NOT** for media (mp4, mp3, jpg, png) or already-compressed streams.
- **Unique value**: search-without-decompress + convergence merging for log aggregation.
- **Best at**: repetitive symbolic structure (JSON keys, CSV headers, SQL schemas, code keywords).

### 1.2 What's In v0.8

#### ✅ Already Complete (from v0.7 work)

| Feature | Status | File |
|---------|--------|------|
| Rust crate structure | Done | `src/csf_rust/Cargo.toml` |
| Safe header parser/serializer | Done | `src/csf_rust/src/header.rs` |
| Symbolic dictionary with bounds | Done | `src/csf_rust/src/dictionary.rs` |
| Sparse CSR encode/decode | Done | `src/csf_rust/src/sparse.rs` |
| Compression pipeline (dict→sparse→zstd) | Done | `src/csf_rust/src/compress.rs` |
| Compression modes (Full/Fast/Static) | Done | `src/csf_rust/src/compress.rs` |
| Streaming I/O skeleton | Done | `src/csf_rust/src/streaming.rs` |
| Search index (Bloom + inverted) | Done | `src/csf_rust/src/search.rs` |
| Convergence merge with depth limits | Done | `src/csf_rust/src/convergence.rs` |
| CLI tool (compress/decompress/search/merge) | Done | `src/csf_rust/src/cli.rs` |
| Security policy (anti-zip-bomb) | Done | `src/csf_rust/src/security.rs` |
| Real-world benchmarks (logs, JSON, code) | Done | `benchmarks/csf_realworld_benchmark.py` |
| Media/file-type benchmarks | Done | `benchmarks/csf_media_benchmark.py` |

#### 🚧 Required for v0.8 Release

| Feature | Priority | Owner | Acceptance Criteria |
|---------|----------|-------|---------------------|
| Rust build passes on Windows/Linux/macOS | High | Alex | `cargo build --release` succeeds on all three |
| Criterion benchmarks run without errors | High | Alex | `cargo bench` produces report.html |
| Python bindings (PyO3) for existing v0.7 consumers | High | — | `import csf_rust` works; API matches v0.7 surface |
| Memory-mapped streaming >RAM tested on 10 GB file | High | — | Process RSS stays < 500 MB during 10 GB compress |
| Fast mode (skip dictionary) default for < 1 MB | Medium | — | Auto-detects small input; falls back to raw zstd L1 |
| AES-256-GCM encryption (`--features encrypt`) | Medium | — | Encrypted archives decrypt correctly; key from env var |
| Parallel segment compression (`rayon`) | Medium | — | 4-core machine shows >2x speedup on 4+ segments |
| CLI binary signed + distributed (GitHub Releases) | Low | — | `csf-v0.8-windows-x64.exe` available for download |

#### 🎯 v0.9 Future (not this release)

- WASM target for browser-side decompression
- Pre-built static dictionaries for known schemas (K8s YAML, nginx logs)
- Incremental compression (append to existing archive without full rewrite)
- Delta compression between versions of same file

### 1.3 Benchmark Commitments for v0.8

| Scenario | Target | Measured By |
|----------|--------|-------------|
| Application logs (1 MB) | < 15 ms compress | `cargo bench` |
| Search-without-decompress (10 MB) | < 1 ms query | `cargo bench` |
| Streaming 10 GB logs | < 2 min, RSS < 500 MB | Manual test |
| Agent JSON (1 MB) | > 94% ratio | `cargo bench` |
| Convergence merge (2 archives) | > 30% smaller than gzip-combined | `cargo bench` |

### 1.4 File Map

```
src/csf_rust/
├── Cargo.toml              # Manifest (add PyO3, fix versions)
├── README.md               # Updated with real benchmarks
├── src/
│   ├── lib.rs              # Public API (stable for v0.8)
│   ├── header.rs           # Binary format (frozen for v0.8)
│   ├── dictionary.rs       # Symbolic layer (frozen)
│   ├── sparse.rs           # CSR layer (frozen)
│   ├── compress.rs         # Pipeline + modes (frozen)
│   ├── streaming.rs        # >RAM (needs mmap test)
│   ├── search.rs           # Index + query (frozen)
│   ├── convergence.rs      # Merge (frozen)
│   ├── security.rs         # Policy (frozen)
│   └── cli.rs              # Command-line (add encrypt flag)
├── benches/
│   └── benchmark.rs        # Criterion suite (needs PyO3 benches)
└── tests/
    └── integration.rs      # NEW: roundtrip, search, merge tests

benchmarks/
├── csf_competitor_benchmark.py    # Updated projections
├── csf_realworld_benchmark.py   # Real log data
└── csf_media_benchmark.py        # File-type comparison

docs/
├── CSF-FORMAT-SPECIFICATION.md  # Update §6 with real numbers
└── CSF-CADD-v08-RELEASE-PLAN.md # This file
```

---

## Part 2: CADD v0.2 — Capture, Assess, Distill, Dock

### 2.1 What CADD Is

CADD is the brand/asset intake pipeline for Dream Journal by Lantern OS. It ensures every image, prompt, card, and visual asset passes through a consistent workflow before entering the RAG dollhouse or public channels.

- **Capture** — Record the asset, its source, date, purpose, tier role.
- **Assess** — Classify against brand rules (source-of-truth, candidate, rejected).
- **Distill** — Write a markdown note: what it is, what rules it follows, what must not change.
- **Dock** — Pass to `lantern-rag-dollhouse` for copy, hash, manifest, flat RAG reference.

### 2.2 What's In v0.2

#### ✅ Already Complete (from v0.1 work)

| Feature | Status | File |
|---------|--------|------|
| Brand rule documentation | Done | `skills/dream-journal-brand-cadd/SKILL.md` |
| Tier structure (FREE/NORMAL/PRO) | Done | SKILL.md §Consolidated Tier Roles |
| Source-of-truth card descriptions | Done | SKILL.md §Source-of-Truth Reference Cards |
| Prompt templates for all tiers | Done | SKILL.md §Prompt Templates |
| Asset file naming convention | Done | SKILL.md §Asset File Naming |
| Acceptance criteria checklist | Done | SKILL.md §Acceptance Criteria |

#### 🚧 Required for v0.2 Release

| Feature | Priority | Owner | Acceptance Criteria |
|---------|----------|-------|---------------------|
| Automated CADD validation script | High | — | Python script reads image + prompt; checks against 8 checklist items |
| Dashboard-style rejection detector | High | — | Script flags images with: dense widgets, left nav bars, analytics cards, admin grids |
| Text-in-image detector (OCR heuristic) | High | — | Flags images with embedded text/pseudo-letters |
| Lower-panel emptiness checker | Medium | — | Analyzes bottom 35-45% of card; warns if > 20% detail |
| Brand palette validator | Medium | — | Extracts dominant colors; warns if neon/corporate gray/harsh black detected |
| CADD manifest JSON schema | Medium | — | Every asset gets a `.cadd.json` sidecar with capture/assess/distill fields |
| Integration with RAG dollhouse intake | Medium | — | `cadd dock` command auto-calls `lantern-rag-dollhouse` ingest |
| CLI tool: `cadd capture <file>` | Low | — | Interactive prompt for purpose, tier, date |
| CLI tool: `cadd assess <file>` | Low | — | Runs validation script; outputs classification |
| CLI tool: `cadd distill <file>` | Low | — | Generates markdown note from template |
| CLI tool: `cadd dock <file>` | Low | — | Copies to `assets/brand/`, writes manifest, calls RAG ingest |

### 2.3 CADD Validation Script (v0.2 MVP)

```python
cadd validate <image.png> \
  --prompt <prompt.md> \
  --tier {free,normal,pro} \
  --purpose "patreon-card"
```

Checks:
1. File naming matches `assets/brand/dream-journal/cards/{tier}-*.png`
2. Image is vertical if tier card
3. No embedded text detected (OCR or pseudo-letter heuristics)
4. Lower panel emptiness score > 60%
5. Palette contains no neon/corporate gray/harsh black
6. Prompt matches approved template for tier
7. Not dashboard-like (no grid patterns, no sidebar shapes)
8. Has source prompt file alongside

Output:
```json
{
  "asset": "pro-imaginverse-builder-villa.png",
  "classification": "brand_ready_for_use",
  "checks_passed": 8,
  "checks_failed": 0,
  "warnings": ["lower_panel_detail: 22% (threshold 20%)"],
  "distilled_note": "pro-imaginverse-builder-villa.distill.md",
  "manifest": "pro-imaginverse-builder-villa.cadd.json"
}
```

### 2.4 File Map

```
skills/dream-journal-brand-cadd/
├── SKILL.md                    # Brand rules (frozen for v0.2)
├── cadd.py                     # NEW: CLI + validation script
├── validators/
│   ├── __init__.py
│   ├── text_detector.py        # OCR / heuristics for embedded words
│   ├── palette_checker.py      # Color analysis against brand palette
│   ├── layout_analyzer.py      # Dashboard / grid / sidebar detection
│   └── panel_emptiness.py      # Lower-panel detail analysis
├── templates/
│   ├── capture-template.json   # CADD sidecar schema
│   ├── distill-template.md     # Markdown note template
│   └── assess-rubric.json      # Classification rules
└── tests/
    ├── test_text_detector.py   # Unit tests
    ├── test_palette_checker.py
    └── test_layout_analyzer.py

assets/brand/dream-journal/
├── cards/                      # Approved cards (frozen)
│   ├── free-ya-k12-org.png
│   ├── normal-dream-journal.png
│   ├── pro-imaginverse-builder-villa.png
│   └── pro-beach-energy-companion.png
├── prompts/                    # Source prompts (frozen)
│   ├── free-ya-k12-org.md
│   ├── normal-dream-journal.md
│   ├── pro-imaginverse-builder-villa.md
│   └── pro-beach-energy-companion.md
└── cadd/                       # NEW: CADD sidecars for every card
    ├── free-ya-k12-org.cadd.json
    ├── free-ya-k12-org.distill.md
    └── ...
```

---

## Part 3: Integration Between CSF and CADD

Both systems share a common need: **asset provenance and integrity**.

### 3.1 Shared Infrastructure

| Feature | CSF Use | CADD Use |
|---------|---------|----------|
| Checksum/integrity | Archive footer checksum validates compressed data | Image hash validates asset hasn't changed |
| Manifest schema | Archive header describes segments, dictionary, index | CADD sidecar describes capture, assess, distill |
| Versioning | Header version field for format evolution | CADD schema version for validation rules |
| Security policy | Max size, depth limits prevent attacks | Max resolution, file size limits prevent abuse |

### 3.2 Cross-Cutting Concerns

- **GitHub Actions**: Both CSF (`cargo test`) and CADD (`python -m pytest`) get CI.
- **Release packaging**: Both ship via GitHub Releases with signed checksums.
- **Documentation**: Both share `docs/` directory; release notes combined.

---

## Part 4: Timeline

| Week | CSF Task | CADD Task |
|------|----------|-----------|
| Week 1 (Jun 3–9) | Rust build on all platforms; fix compile errors | CADD validation script MVP (text + palette) |
| Week 2 (Jun 10–16) | Criterion benchmarks + integration tests | Layout analyzer + panel emptiness checker |
| Week 3 (Jun 17–23) | PyO3 Python bindings; test against v0.7 API | CADD CLI (`capture`, `assess`, `distill`, `dock`) |
| Week 4 (Jun 24–30) | >RAM streaming test on 10 GB; release notes | Integration with RAG dollhouse; generate sidecars |
| Release Day (Jul 1) | Tag `csf-v0.8.0`; publish GitHub Release | Tag `cadd-v0.2.0`; publish validation script |

---

## Part 5: Acceptance Criteria for Release

### CSF v0.8 is ready when:

- [ ] `cargo build --release` passes on Windows, Linux, macOS
- [ ] `cargo test` passes with 0 failures
- [ ] `cargo bench` produces report with all targets met
- [ ] Python bindings import successfully: `import csf_rust`
- [ ] 10 GB streaming test completes with RSS < 500 MB
- [ ] README.md reflects real benchmarks (not projections)
- [ ] No references to "quantum dust" or "200 TB theoretical" in docs
- [ ] Honest positioning: "searchable archive, not universal compressor"

### CADD v0.2 is ready when:

- [ ] `cadd validate` runs against all 4 approved cards with 0 failures
- [ ] Dashboard detector correctly rejects 3+ synthetic dashboard images
- [ ] Text detector flags images with embedded words
- [ ] All approved cards have `.cadd.json` sidecars
- [ ] All approved cards have `.distill.md` notes
- [ ] RAG dollhouse ingests CADD-docked assets successfully
- [ ] SKILL.md updated with v0.2 CLI usage

---

## Appendix: Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Rust not installed on target machine | High | Blocks build | Document install steps; provide pre-built binaries |
| PyO3 bindings break v0.7 API | Medium | Breaks existing users | Write adapter layer; test against `tests/test_csf.py` |
| CADD validation false-positives | Medium | Rejects good assets | Tunable thresholds; human override flag |
| Real benchmarks worse than projections | Low | Damages credibility | Already using real data; projections removed |
| Scope creep (add more features) | High | Delays release | Strict freeze on Week 3; only bug fixes after |
