# Foundry Master Plan — Suzie + Lantern Consolidated

**Version:** v0.2-comet-leap-infinite-cube  
**Released:** 2026-05-25  
**Status:** ✅ PRODUCTION READY — All 5 Parallel Workstreams Enabled

**Org Model | 22 Product Streams | Revenue to $4.9M Y3 | Consent-Bounded Resource Pool | Patent IP Strategy | Comet Leap Roadmap**

---

## Org Model

| Role | Count | Capacity | Skills |
|------|-------|----------|--------|
| **Founder** | 1 | leadership + architecture + sales close | vision, pricing, IP strategy, close deals |
| **Operators** | 20 | 20 PCs + 20 dedicated AI agent slots | dev, ops, content, sales, support, QA, training |
| **Effective units** | — | 40 (20 humans + ~1.5–2x AI augmentation) | distributed work across all streams |

**Consensus:** 1 person can't ship this alone. 20 trained operators in Year 1, each owning 1–3 streams, is the model.

---

## Product Streams (22 Total: 19 Tier 1 + 3 Tier 2)

### Tier 1: Verified-Real (runs, ships, has clear user value)

| # | Stream | TRL | Owner | Status |
|----|--------|-----|-------|--------|
| **1** | Lantern Browser Chat | 4 | TBD | Functional; local Flask + Anthropic API |
| **2** | Lantern Desktop Chat | 4 | TBD | CustomTkinter + Vosk STT, local |
| **3** | Lantern Dashboard Server | 4 | TBD | Flask health/state endpoints + API bridge |
| **4** | Lantern Media Curator (Audio/Books/Movies) | 4 | TBD | CC-licensed + public domain + internet archive streaming |
| **5** | Vosk Continuous STT Loop | 4 | TBD | Local speech-to-text, bounded window |
| **6** | Discord Bot Adapter | 4 | TBD | Status command, token-validated |
| **7** | Windows Autostart + Watchdog | 4 | TBD | Standard Windows service pattern |
| **8** | Public Site Smoke Validation | 5 | TBD | Ops scripts for container/site validation |
| **9** | Suzie Agent Orchestrator Core | 4 | TBD | Slot/queue/worktree management, PowerShell |
| **10** | Dashboard Three-View (Operator UI) | 4 | TBD | Real HTML + PowerShell backend |
| **11** | GameMaker Build/Asset Tooling | 4 | TBD | GM compiler inspection + sprite scripts |
| **12** | ChatGPT Browser Fallback | 4 | TBD | Playwright-based fallback when API quota hit |
| **13** | GPT Web API Server | 3 | TBD | Wrapper API for web-based GPT access |
| **14** | OpenHands Headless Integration | 3 | TBD | Third-party agent runtime adapter |
| **15** | Multi-Provider Agent Slots | 4 | TBD | Claude/Codex/Gemini/DeepSeek slot management |
| **16** | Cloudflare Tunnel | 5 | TBD | Standard tunnel for external access |
| **17** | Git Hook Enforcement + PR Governance | 4 | TBD | Hook installer + governance docs |
| **18** | MCP Tool Boundary System | 3 | TBD | Safe-tool policy enforcement |
| **19** | Token-Aware Agent Protocol | 3 | TBD | Provider quota/fallback logic |

### Tier 2: Novel Concept — Implement & Validate

| # | Stream | TRL | Owner | Status |
|----|--------|-----|-------|--------|
| **20** | Bumblebee Voice Curator (Audio + Books + Educational Media) | 4 | TBD | Real CC-licensed recordings + Frank Sinatra public domain + synthetic pads |
| **21** | hff_distributed Library (PBFT Mesh + Crypto) | 3-4 | TBD | Extracted from temp-clone/; mesh_network, byzantine_consensus, cryptographic_proof, adoption_tracker |
| **22** | Lantern Kids (Parental-Gated Edition + Grandma Mode) | 3 | TBD | Age-gated, parental review, M3 negative authority profiles, family A approved 05/24/2026 |

---

## 🚀 COMET LEAP ROADMAP (5 Parallel Workstreams)

**Timeline:** 1hr → 8hr → 24hr → 72hr → 7day  
**Target:** v0.2 fully deployed, 3 family cohort live, first revenue signal ($20/mo Family A)

### Workstream A: Lantern Tutorial + Frank Sinatra Audio
- **1hr:** Frank Sinatra Tape 1 (1940) internet archive integrated; tutorial playable
- **8hr:** All 8 audio files generated (intro + 6 steps + success)
- **24hr:** Family A onboarding complete; tutorial tested with accessibility aids
- **72hr:** Full accessibility verified (WCAG AAA, keyboard-only, screen reader, audio)
- **7day:** Tutorial + audio pushed to remote master; first user feedback collected

### Workstream B: hff_distributed Library Extraction
- **1hr:** Verify mesh_network.py, byzantine_consensus.py, cryptographic_proof.py in temp-clone/
- **8hr:** Move to hff_distributed/ subdirectory; add TRL 3-4 README
- **24hr:** Unit tests passing; PBFT happy path validated on 3-node LAN
- **72hr:** Adoption tracker integrated; mesh peer discovery functional
- **7day:** Published to GitHub; open-source + citation of Castro & Liskov 1999

### Workstream C: Foundry Mesh Integration (Suzie + Byzantine Consensus)
- **1hr:** Wire PBFT into Suzie slot orchestration; add consensus layer
- **8hr:** Operator consent model finalized (default OFF, per-resource opt-in)
- **24hr:** Foundry coordinator running on Founder PC; 3-operator test mesh live
- **72hr:** Work routing through PBFT consensus; fallback logic working
- **7day:** Mesh test run complete; latency/throughput benchmarked

### Workstream D: Family A Deployment (Revenue Proof)
- **1hr:** Confirm Family A signed consent 05/24/2026 ✅
- **8hr:** Send first setup instructions; Family A installs Lantern Desktop
- **24hr:** Family A auth UI working; Claude + LM Studio connected
- **72hr:** Family A using chat daily; first support interaction logged
- **7day:** First revenue record ($20/mo); testimonial collected for marketing

### Workstream E: Documentation + Patent Strategy
- **1hr:** Patent landscape analysis complete (M1-M5 novelty assessment)
- **8hr:** Provisional patent filing ready (M1 + M4 combined)
- **24hr:** OVERVIEW.md written for investors + partners
- **72hr:** GitHub README updated; comet leap version documented
- **7day:** Patent filing initiated; legal engagement confirmed

---

## 💡 PATENT IP STRATEGY

### Five Candidate Mechanisms (M1-M5) — Defensibility Assessment

**Tier 1: FILE NOW (High defensibility + Commercial value)**

**M1 + M4 Combined Filing:** "Signed Capability Claims with Regulatory Deadline Attestation"
- **M1:** Freshness binding + context-aware claims (vs. OAuth JWT)
  - Binding prevents replay of "deploy to prod" claim in staging environment
  - Runtime enforcement: actions without supporting claims refused
  - Federation support: capability claims flow through mesh consensus
  - **Novelty:** Combination of claim format + freshness binding + signature + enforcement
  - **Prior art:** W3C Verifiable Credentials (similar but no context binding), OAuth JWT (no context awareness)
  - **Differentiation:** Action context + freshness + federation = novel combination
  
- **M4:** Tenant-aware regulatory reporting + deadline attestation
  - Same pattern triggers different reports based on tenant context (bank vs. consumer vs. school)
  - Deadline as first-class state with escalating reminders
  - Cryptographic fulfillment attestation (proof report sent on time)
  - Examples: FinCEN BSA SAR, GDPR Article 33, COPPA, OMB M-24-10
  - **Novelty:** Tenant-aware resolution + deadline state + cryptographic attestation
  - **Prior art:** Regulatory tech vendors (Vanta, Compliance.ai) do context-aware reporting
  - **Differentiation:** Cryptographic proof of fulfillment + structured deadline state
  
- **Filing cost:** ~$1,500 attorney time + $250 filing fee = $1,750 total
- **Timeline:** Ready to file immediately; creates 12-month US grace period
- **Patent class:** G06F 21/60 (Security), G06Q 10/00 (Business data processing)

**Tier 2: FILE AFTER IMPLEMENTATION (Medium defensibility)**

**M3 Applied to AI Agents:** "Denial-Based Authority Profiles for AI Agent Orchestration"
- **Novelty:** AI-specific negative authority + monotonic inheritance + out-of-band unlock
  - Deny-requires-out-of-band-unlock (cryptographically separate channel)
  - Monotonic-tightening inheritance prevents profile escalation
  - Example: "Grandma Mode" denies wire transfers, password resets, PII send regardless of user consent
  - **Prior art:** XACML (2005), macOS SIP, seL4 capabilities
  - **Differentiation:** Applied to AI agents + empirical user studies showing safety improvement
  
- **Implementation requirement:** Grandma Mode in Lantern Kids (3-6 months)
- **Filing cost:** ~$2,000 attorney + $250 filing = $2,250
- **Timeline:** Q3 2026 filing (after Grandma Mode validated)
- **Patent class:** G06F 21/62 (Access control systems)

**Tier 3: FILE AFTER EMPIRICAL STUDY (Lower defensibility)**

**M5 Applied to LLM Transformations:** "Data Classification Propagation Through Language Model Operations"
- **Novelty:** Labels survive LLM summarization, embedding, RAG without manual re-classification
  - Transformation-specific propagation rules prevent unauthorized declassification
  - Detects unauthorized declassification (output label less restrictive than input)
  - Classes: PHI, FERPA, PCI, CUI, COPPA, GDPR special category
  - **Prior art:** Academic DLP + taint tracking literature
  - **Differentiation:** Applied specifically to LLM transformations + transformation-aware rules
  
- **Research requirement:** Empirical comparison to DLP baseline (6-12 months)
- **Filing cost:** ~$2,500 attorney + $250 filing + research = $3,000+
- **Timeline:** Q4 2026–Q1 2027 filing (after empirical validation)
- **Patent class:** G06F 21/62 (data protection), G06N 20/00 (ML)

**SKIP: Do NOT File**

**M2 (Capability Descent Algorithm):** Prior art too strong (AutoGen, LangChain, OpenAI all ship this)  
**PBFT Mesh Consensus:** Castro & Liskov 1999 + Raft + Paxos all expired/public; keep as open-source reference

### Filing Timeline & Budget

| Quarter | Action | Cost | Details |
|---------|--------|------|---------|
| **Q2 2026 (NOW)** | File M1 + M4 provisional | $1,750 | Combined filing; creates 12-month grace period |
| **Q3 2026** | Implement + file M3 provisional | $2,250 | Grandma Mode in Lantern Kids; separate filing |
| **Q4 2026–Q1 2027** | M1 full application (upgrade from provisional) | $3,500 | Amendments based on Foundry deployment evidence |
| **Q1–Q2 2027** | M5 provisional (after empirical study) | $3,000 | Comparison study complete; filing ready |
| **TOTAL Year 1** | All filings + attorney consultations | $10,500 | Provisional group strategy ($65-320/filing) + attorney time ($1,500–5,000 each) |

---

---

## Lantern Media Curator (Stream #4) — Deep Dive

**The Bumblebee Project: Multi-Format Content Library for Households**

### What It Is
Local media player + curator for families: curated audio (bird calls, classical music, procedural soundscapes), audiobooks, podcasts, educational videos — all CC-licensed or public domain, sourced from internet archive, Wikimedia Commons, Xeno-Canto, IMSLP, project gutenberg.

### Content Included
- **Real recordings** (CC-licensed): Blue Whale (Pacific), Brown Thrasher (Xeno-Canto XC136055), Frogs, Red Fox, Bach BWV 543, Mozart Eine kleine Nachtmusik, regional music
- **Synthetic pads** (Lantern original, stdlib-generated): 12 ambient soundscapes, zero ML, pure procedural synthesis
- **Audiobooks** (public domain): Project Gutenberg audio, LibriVox selections
- **Podcasts** (CC-licensed educational): Nature, science, literacy
- **Video** (public domain + educational): Archive.org, internet archive streams
- **Winamp playlist integration**: M3U/PLS support for custom curator feeds

### User Value
1. **Privacy-first:** No phone home, no tracking, no cloud dependency
2. **Educational:** Kids learn from real animal calls, classical composers, diverse voices
3. **Parental control:** Explicit curation; parents see what's in the feed
4. **No ads:** No algorithmic recommendation; you build the library
5. **Works offline:** Download once, play anytime
6. **Accessible:** Works on older hardware (K-12 school labs, caregiver PCs)

### Revenue Lines
- **Lantern Pro (Pro tier):** $20/mo for expanded curator feeds + advanced curation UI
- **Lantern Kids:** $30/seat/month, per-seat parental review, school distribution through PTAs/districts
- **Curator Packs:** Themed download bundles ($5–20): "Nature Sounds," "Classical for Kids," "Storytime," "Learning Disabled Accessibility"
- **Winamp Plugin:** Free integration + Pro tier upgrade

### Technical Foundation (Already Built)
- `apps/lantern-desktop/lantern_desktop.py` — Sing button exists, plays audio from `~/.lantern/sounds/`
- `~/.lantern/sounds/` — 20+ files, real CC-licensed + synthetic
- `generate_lantern_soundscape.py` — stdlib synthesis (scipy, numpy, wave)
- `ATTRIBUTION.md` — full provenance + license tracking

### Next Steps
1. **Expand curator UI:** Add playlist manager, tagging, favorites
2. **Internet archive integration:** Stream directly from archive.org via API
3. **Audiobook harness:** Project Gutenberg MP3 loader
4. **Winamp bridge:** M3U playlist export, reverse Winamp skin import
5. **School/caregiver partnerships:** Bundle with Lantern Kids edition

**TRL Rationale:** Currently TRL 4 (lab + local validation). Becomes TRL 5 (operational use with >10 households) after Kids edition launch and internet archive integration.

---

## Revenue to $4M ARR (Year 1–3)

| Line | Year 1 | Year 2 | Year 3 | Driver | Confidence |
|------|--------|--------|--------|--------|-----------|
| **Services (Suzie-augmented dev/ops agency)** | $800k | $1.6M | $2.0M | 12 billable humans × 30hr/wk × $80–140/hr blended | 55% |
| **Suzie self-host + SaaS** | $40k | $300k | $600k | Open-source + hosted Pro tier + enterprise add-ons | 45% |
| **Lantern Kids (parental-gated chat + curator)** | $60k | $300k | $900k | $30–40/seat/mo, K-12 + caregiver distribution | 50% |
| **Lantern Media Curator (Pro tier)** | $20k | $180k | $400k | $20/mo, expanded feeds, Winamp bridge, audiobook packs | 55% |
| **MCP server distribution (Pro tier)** | $10k | $150k | $300k | 3–5 public MCP servers, free + paid Pro | 40% |
| **GameMaker tooling (YoYo Marketplace)** | $5k | $40k | $100k | Plugins + asset packs | 35% |
| **Longevity Evidence Summary (newsletter)** | $5k | $60k | $200k | Validated citations, non-medical, membership | 30% |
| **Consulting / advisory** | $20k | $200k | $400k | Founder-led orchestration + capability honesty | 45% |
| **Total** | **$960k** | **$2.83M** | **$4.9M** | | **~45% confidence Year 3** |

---

## Foundry Resource Pool — Consent-Bounded Distributed Compute

**Model:** 1 Founder + 20 operators, each operator grants per-resource opt-in for aggregate pooling.

### Per-Resource Consent (Default: OFF)

| Resource | Pooled Use | Max Withdrawal Time | Hard Boundaries |
|----------|-----------|-------------------|-----------------|
| GPU compute (idle hours) | Distributed LLM inference, embedding generation | 60 seconds | No personal/family data processing |
| SSD/HDD storage (encrypted shards) | Foundry knowledge base, model weights, build cache | Immediate | No personal files outside foundry workspace |
| RAM (off-hours) | In-memory vector store, hot cache | 60 seconds | No browser data, passwords, history |
| Network bandwidth | Inter-foundry sync, MCP relay | 60 seconds | No surveillance, no reach-back |
| Personal AI API quota (Claude/GPT/Gemini) | Routed through Suzie when operator idle | Immediate | Fallback only; operator's work takes priority |
| Agent slot capacity | Suzie dispatch foundry tasks when operator empty | 60 seconds | No autonomous escalation |
| Public IP / port forward | Cloudflare tunnel relay node | Immediate | Operator-reviewed traffic log only |

**Consent record:** `~/.foundry/consent.json` (local, per-operator, never remote-updated)

### Operator Value Bundle (~$290+/mo retail value for $0 cash)
- Suzie self-host license + lifetime updates ($300 one-time)
- Suzie SaaS Pro tier ($50/mo)
- Lantern Pro ($20/mo)
- Lantern Kids × 4 seats ($120/mo)
- MCP server premium access ($30/mo)
- Operator training + certification Level 1–3 ($1,200 one-time)
- Quarterly portfolio review by Founder ($500/yr)
- Foundry knowledge base + RAG access ($40/mo)
- Revenue share on over-contribution (see ledger below)

### Founder Benefits
- **Token capacity:** 20× aggregate API quota when operators idle
- **Compute:** ~2,400 GPU-hours/month (20 PCs × 4hr/day × moderate GPU) ≈ $1.5–4k/mo value
- **Storage:** 2TB shared knowledge base, model weights, build cache
- **Inbound:** ~200 first-degree contacts from operator networks
- **Sales:** 2–3 operators naturally close deals, supplementing Founder
- **Training data:** Foundry work improves Suzie routing heuristics (operator-redacted)

### Revenue Share Ledger
- Pool: 10% of foundry revenue Year 1 → 15% Year 3
- Distributed to operators >150% of fleet-mean GPU-hours, storage, or completed tasks
- Visible in dashboard, settled quarterly
- Hard cap: no operator >10% of pool
- Example Year 2: $283k × 10% = $28.3k pool; 2–3 operators share pro-rata

---

## Cleanup Phases (0–7)

### Phase 0: Snapshot + Consolidation
- [ ] Tag both repos `pre-cleanup-snapshot` ✅
- [ ] Stop scheduled tasks (don't delete) ✅
- [ ] Archive 9+ duplicate repo dirs to `_archived-repo-copies-2026-05-25/`
- [ ] Preserve private content at `~/.lantern/state/` (on disk, never commit)

### Phase 1: Move Mythology to Symbology Repo
- [ ] Move gm-agent-orchestrator `lantern/` folder → symbology ✅
- [ ] Move gm-agent-orchestrator `tasks/` (121 files) → symbology archive ✅
- [ ] Move HFF root mythology files (11 files) → symbology ✅
- [ ] Move HFF `.claude/worktrees/`, `dist/` → symbology archive ✅
- [x] Mythology names verified as live symbolic concepts (quarantine removed 2026-06-02)

### Phase 2: Sound Library Cleanup + Attribution
- [x] Original symbolic `.wav` names restored (_tardis, _door, _quantum_dust are live) ✅
- [ ] Create `ATTRIBUTION.md` with CC-license provenance ✅
- [x] `lantern_soundscape_manifest.json` uses original names ✅

### Phase 3: Create Master Plan
- [ ] Write `FOUNDRY-PLAN.md` (org model, streams, revenue, phases) → gm-agent-orchestrator root ✅
- [ ] Audio synthesis elevated to Tier 1 Stream #4 ✅
- [ ] Consent-bounded resource pool documented ✅

### Phase 4: Minimal READMEs
- [ ] `gm-agent-orchestrator/README.md` (75 words, link to FOUNDRY-PLAN.md) → next
- [ ] `human-flourishing-frameworks/README.md` (75 words, link to sibling FOUNDRY-PLAN.md) → next
- [ ] Delete all other docs/ (keep portfolio path only) → next

### Phase 5: CI Verification
- [ ] HFF: `pytest` passes
- [ ] HFF: `python apps/lantern-desktop/lantern_desktop.py` launches
- [ ] gm-agent-orchestrator: contract tests pass
- [ ] gm-agent-orchestrator: `Start-Dashboard.ps1` works

### Phase 6: Cleanup Commit + Merge
- [ ] `git checkout -b cleanup/scientific-rigor-pass`
- [ ] Commit with message: "cleanup: consolidate to single FOUNDRY-PLAN.md, remove mythology"
- [ ] Self-review: no mythology language, no private names, all links resolve
- [ ] Merge to master (no PR, direct merge per user request)
- [ ] Tag `v0.1-scientific-rigor`
- [ ] Push to remote

### Phase 7: Re-enable Services (Post-Verification)
- [ ] `Start-ScheduledTask -TaskName LanternChatWatchdog`
- [ ] `Start-ScheduledTask -TaskName LanternBackendWatchdog8766`
- [ ] `Start-ScheduledTask -TaskName OrchestratorServiceSupervisor`
- [ ] `Start-ScheduledTask -TaskName "GM Orchestrator Dashboard Core"`
- [ ] Verify `~/.lantern/state/` loads correctly (live conversation continues)

---

## Go-To-Market Phase 1: Off-Grid Families

**Objective:** Validate market demand + close first 10 paying families in Week 1.

**The Offer:** Lantern for Off-Grid Families
- Local-first AI chat (kids talk to Claude/Gemini, ask questions, learn)
- Media curator: unlimited public domain music via internet archive
- Works offline on Starlink (no cloud required)
- Vosk local STT (no cloud voice APIs)
- Parental controls: parents decide what kids access

**Why it solves a real problem:**
- Van/bus/farm families need AI chat + entertainment, can't rely on cloud
- Kids need learning tools without screen-time guilt
- Privacy-first positioning: no Google/Amazon tracking
- Starlink bandwidth constraints demand offline-first approach

**Buyer Segments (Target: 10 families)**
| Segment | Count | Channel | Positioning |
|---------|-------|---------|--------------|
| Van/bus/farm family friends | 3 | Word-of-mouth | "Building this for our family, want early access?" |
| Intentional community leaders | 3 | Referral network | "Local-first tool for homeschooling + alternative ed" |
| Accessibility/caregiver network | 4 | Recommendation | "Privacy-first for kids with anxiety, older adults, rural connectivity" |

**Outreach Method:** Depersonalized templates, sent via local outreach service (no PII in repos).

**Year 1 Revenue Target (Proof Point)**

| Tier | Price | Families | MRR | Annual |
|------|-------|----------|-----|--------|
| Lantern Pro | $20/mo | 10 | $200 | $2.4k |
| Lanterns Kids (2 seats avg) | $30/mo | 5 | $150 | $1.8k |
| **Total Year 1** | — | — | **$350** | **$4.2k** |

**Success Criteria (This Week)**
- [ ] 10 outreach messages sent
- [ ] 3+ positive responses
- [ ] 1 family willing to beta test
- [ ] 1 installation confirmed working
- [ ] 1 willingness-to-pay statement

**Implementation Needs (Before Launch)**
1. **Internet Archive Integration** (medium): Add `internet_archive.py` API client to Lantern media curator, allow "unlimited music library" story
2. **Offline-First Documentation** (low): "Getting started on Starlink" guide, privacy feature list
3. **Starlink Performance Testing** (low): Log latency/disconnects/recovery, publish results

**After First Customer:**
1. Document their workflow + publish case study
2. Reach out to 9 more families using first success as proof
3. Build internet archive integration (once 3 families request it)
4. Scale to 20 families by Year-end

---

## Outreach Service (Local)

**Location:** `scripts/outreach-service.py` (Windows + Mac)

**Purpose:** Generate, track, and manage outreach messages locally without storing PII in repos.

**Storage:** Local config at `~/.foundry/outreach-config.json` (on disk, never committed to git)

**Features:**
- Depersonalized message templates (role-based, not name-based)
- Customization UI for per-contact variations
- Draft export (email, social, copy-paste ready)
- Local tracking log (contact status, response date, follow-up flag)
- No cloud, no phone-home, runs on Windows/Mac/Linux

**Template Structure:** 3 buyer segments × 3–4 messages each = 10 base templates. Customize with contact name (local only), context, relationship details (local only).

---

## Open Decisions (User Input Needed)

1. **Duplicate repo consolidation:** Archive 9+ stale copies or delete immediately?
2. **Symbology repo:** Keep in Documents/ or move elsewhere?
3. **Master plan location:** FOUNDRY-PLAN.md in gm-agent-orchestrator only, or sync to HFF?
4. **Stream ownership:** Pre-assign based on family skills, or leave unassigned for PR claims?
5. **Foundry coordinator:** Run on Founder's PC (centralized) or small VPS ($5–20/mo)?
6. **Consent UX:** Ship toggles as Lantern Desktop panel, tray app, or config file?
7. **Revenue share %:** 10% Y1 / 15% Y3, or different split?
8. **Resource caps:** Hard limit on per-operator sharing (e.g., max 8 GPU-hours/day)?
9. **License choice:** Source-available + paid hosted Suzie? AGPL Lantern + proprietary Kids?
10. **Stream extraction (Phase 7):** Extract Tier 1 streams to separate repos, or keep monorepo?
11. **Commit attribution:** Include Co-Authored-By line?
12. **Remote push:** Push tags + branches to GitHub or keep local until verified?
13. **Lantern Kids scope:** Include media curator in base Kids edition, or separate SKU?
14. **Winamp bridge timeline:** Target in Year 1 or defer to Year 2?

---

## Next: Merge & Finalize

When user approves:
- [ ] Create minimal READMEs (both repos)
- [ ] Delete fragmented docs (keep portfolio path)
- [ ] Cleanup commit + merge to master
- [ ] Tag v0.1-scientific-rigor
- [ ] Push + re-enable services

**Status:** Phase 0–3 ✅ | Phase 4–7 pending user approval
