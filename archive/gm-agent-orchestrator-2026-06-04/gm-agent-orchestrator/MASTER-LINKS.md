# Lantern + Suzie Foundry — Master Links & Portfolio
**2026-05-25 | Comet Leap v0.2-infinite-cube | Ready for Print**

---

## PRIMARY ENTRY POINTS

### Portfolio Overview (Start Here)
- **OVERVIEW.md** — One-page founder summary
  - Org model (1 founder + 20 operators + 20 PCs)
  - 22 product streams with TRL assessment
  - Revenue model Y1–Y3 ($900k → $4.3M)
  - Architecture & deployment checklist
  - URL: https://github.com/alex-place/gm-agent-orchestrator/blob/master/OVERVIEW.md

### Master Strategy Documents
1. **COMET-LEAP-MASTER-PORTFOLIO.md** — 8-hour roadmap snapshot
   - Audio narration system, PBFT consensus, Family A deployment
   - Foundry resource pool (consent-bounded sharing)
   - 22 product streams (Tier 1–3)
   - Deployment verification checklist
   - URL: https://github.com/alex-place/gm-agent-orchestrator/blob/master/COMET-LEAP-MASTER-PORTFOLIO.md

2. **FOUNDRY-PLAN.md** — Master org document
   - Org model & capacity planning (40 effective units)
   - Revenue lines to $4M ARR
   - Foundry resource pool architecture
   - Patent filing strategy (M1 + M4)
   - Stream → Owner mapping
   - URL: https://github.com/alex-place/gm-agent-orchestrator/blob/master/FOUNDRY-PLAN.md

3. **STRATEGY-REVISION-2026-05-25.md** — Year 1–3 execution plan
   - 3 parallel workstreams
   - Family A approval (2026-05-24)
   - Revenue roadmap with confidence bands
   - Accessibility layer
   - URL: https://github.com/alex-place/gm-agent-orchestrator/blob/master/STRATEGY-REVISION-2026-05-25.md

---

## DEPLOYMENT & SETUP

### Family A (Off-Grid Families)
- **FAMILY-A-DEPLOYMENT.md** — Complete setup guide
  - Prerequisites (Windows 10+, Python 3.9+, 4GB RAM)
  - 5-minute installation walkthrough
  - API key configuration (Claude, Gemini)
  - Starlink troubleshooting
  - Privacy model & billing ($20/mo)
  - FAQ & support contact
  - URL: https://github.com/alex-place/gm-agent-orchestrator/blob/master/docs/FAMILY-A-DEPLOYMENT.md

### Product Documentation

**Lantern Chat**
- **LANTERN-CHAT-GUIDE.md** — Quick start guide
  - How to run (option 1: launcher, option 2: Python)
  - Real-time chat features (streaming, threading, dark theme)
  - Provider switching & troubleshooting
  - Performance notes (latency, memory)
  - URL: https://github.com/alex-place/gm-agent-orchestrator/blob/master/LANTERN-CHAT-GUIDE.md

- **LANTERN-DEPLOYMENT-CHECKLIST.md** — Step-by-step deployment
  - Pre-deployment verification (29 tests passing)
  - Family A installation steps (6 phases)
  - Post-deployment verification
  - Troubleshooting guide (11 scenarios)
  - Success criteria & milestones
  - URL: https://github.com/alex-place/gm-agent-orchestrator/blob/master/LANTERN-DEPLOYMENT-CHECKLIST.md

**Suzie Orchestrator**
- **README.md** — Suzie quick start
  - What it does (multi-agent coordination)
  - Quick start (Start-Dashboard.ps1)
  - Architecture diagram
  - License & status
  - URL: https://github.com/alex-place/gm-agent-orchestrator/blob/master/README.md

---

## CODEBASE & IMPLEMENTATION

### Scripts (Ready to Deploy)
| File | Purpose | Status |
|------|---------|--------|
| `scripts/start-lantern-chat.bat` | Quick launcher | ✅ Shipping |
| `scripts/lantern-desktop-auth-ui.py` | Auth UI + provider config | ✅ Shipping |
| `scripts/lantern-chat-ui.py` | Real-time chat interface | ✅ Shipping |
| `scripts/lantern-audio-narrator.py` | Frank Sinatra narration | ✅ Shipping |
| `scripts/pbft-consensus.ps1` | Byzantine consensus network | ✅ Ready |

### Tests
- `tests/test_lantern_desktop.py` — Auth UI + startup (19 tests)
- `tests/test_lantern_startup.py` — Port detection, config (10 tests)
- **Status:** 29/29 passing (100% pass rate)
- URL: https://github.com/alex-place/gm-agent-orchestrator/tree/master/tests

### Configuration
- `~/.lantern/llm-configurations.json` — 5 LLM providers configured
- `~/.lantern/narrator.json` — Frank Sinatra narration script + audio files
- `~/.lantern/providers.json` — Primary/fallback provider selection
- `~/.lantern/credentials/` — Securely stored API keys

---

## SISTER REPOSITORY: HUMAN FLOURISHING FRAMEWORKS (HFF)

**Lantern Chat** lives in both repos:
- **gm-agent-orchestrator**: Suzie orchestrator + Family A deployment
- **human-flourishing-frameworks**: Lantern Desktop + Lantern Kids + Bumblebee curator

### Key HFF Files
- `apps/lantern-desktop/lantern_desktop.py` — Main application
- `apps/lantern-desktop/sounds/` — Voice curator library (CC-licensed)
- `scripts/lantern-chat-ui.py` — Chat interface (synced from gm-agent-orchestrator)

URL: https://github.com/alex-place/human-flourishing-frameworks

---

## REVENUE & BUSINESS MODEL

### 22 Product Streams (Quick Reference)
**Tier 1 Shipping (TRL 4):**
1. Lantern Desktop ($20/mo, 10 families Y1)
2. Lantern Kids ($30/mo per child, 20 children Y1)
3. Suzie Orchestrator ($0 open-source, 5 operators Y1)
4. Suzie SaaS ($50/mo, 20 teams Y1)
5. MCP Distribution ($30/mo Pro, 3 servers Y1)
6–19. GameMaker, Longevity, Vosk STT, PBFT, Foundry Pool, others

**Full catalog with TRL:** See FOUNDRY-PLAN.md § "22 Product Streams"

### Year 1–3 Revenue Model
| Line | Y1 | Y2 | Y3 |
|---|---:|---:|---:|
| Services + Suzie SaaS | $840k | $1.9M | $2.6M |
| Lantern Kids | $20k | $250k | $700k |
| MCP + GameMaker + Longevity | $25k | $250k | $600k |
| Consulting | $20k | $200k | $400k |
| **Total** | **$900k** | **$2.6M** | **$4.3M** |

**Confidence Bands:**
- Y1 ($900k+): 55%
- Y2 ($2.6M+): 45%
- Y3 ($4.3M+): 30%

Full model with drivers: See FOUNDRY-PLAN.md § "Revenue lines to $4M ARR"

---

## PATENT & IP STRATEGY

### Filing Plan
**M1: Capability Honesty Model**
- Automated self-assessment of AI agent capability constraints at runtime
- Design patent + provisional utility
- Status: Ready for attorney review (72-hour mark)

**M4: Regulatory Primitive Stack**
- Decomposable compliance primitives (govern/map/measure/manage)
- Provisional utility + trade secret
- Status: Patent novelty search pending

See FOUNDRY-PLAN.md § "Patent Filing Strategy" for full details.

---

## GLOSSARY & KEY TERMS

| Term | Definition |
|------|-----------|
| **Lantern** | Local-first AI chat platform for off-grid families |
| **Suzie** | Multi-agent orchestrator (PowerShell + Python) |
| **Foundry** | 1 Founder + 20 operators × 20 PCs × 20 agent slots = 40 units |
| **PBFT** | Practical Byzantine Fault Tolerant consensus (20 operators, no single-operator failure) |
| **Family A** | First deployment target (van-life family, Starlink, approved 2026-05-24) |
| **Comet Leap** | Development milestones (1hr → 8hr → 24hr → 72hr → 7day) |
| **TRL** | Technology Readiness Level (1–9 scale, 4 = lab-validated) |
| **MCP** | Model Context Protocol (safe-tool boundary for agents) |

---

## CONTACT & SUPPORT

**Founder:** Autonomous Operator  
**Email:** alex.place.7@gmail.com  

**Issue Tracking:** https://github.com/alex-place/gm-agent-orchestrator/issues

**Primary Repos:**
- Suzie Orchestrator: https://github.com/alex-place/gm-agent-orchestrator
- Lantern + HFF: https://github.com/alex-place/human-flourishing-frameworks

**Deployment Support:**
- Family A setup: support@lantern.local
- Response time: Critical (2hr), High (4hr), Normal (24hr)

---

## MILESTONES & TIMELINE

| Date | Milestone | Status |
|------|-----------|--------|
| **2026-05-25** | 8-hour comet leap (audio, PBFT, Family A packet) | 🟢 Complete |
| **2026-05-26** | Family A onboarding + first $20/mo payment | 🟡 Pending |
| **2026-05-28** | Lantern Kids alpha + hff_distributed + patent review | 🟡 Pending |
| **2026-06-01** | v0.2 full deployment + foundry coordinator + $20/mo MRR | 🟡 Pending |

---

## QUICK LINKS SUMMARY (Paste into Browser)

**GitHub Repos:**
- https://github.com/alex-place/gm-agent-orchestrator (Suzie)
- https://github.com/alex-place/human-flourishing-frameworks (Lantern + HFF)

**Master Documents:**
- OVERVIEW.md: https://github.com/alex-place/gm-agent-orchestrator/blob/master/OVERVIEW.md
- COMET-LEAP-MASTER-PORTFOLIO.md: https://github.com/alex-place/gm-agent-orchestrator/blob/master/COMET-LEAP-MASTER-PORTFOLIO.md
- FOUNDRY-PLAN.md: https://github.com/alex-place/gm-agent-orchestrator/blob/master/FOUNDRY-PLAN.md
- STRATEGY-REVISION-2026-05-25.md: https://github.com/alex-place/gm-agent-orchestrator/blob/master/STRATEGY-REVISION-2026-05-25.md

**Deployment:**
- FAMILY-A-DEPLOYMENT.md: https://github.com/alex-place/gm-agent-orchestrator/blob/master/docs/FAMILY-A-DEPLOYMENT.md
- LANTERN-CHAT-GUIDE.md: https://github.com/alex-place/gm-agent-orchestrator/blob/master/LANTERN-CHAT-GUIDE.md
- LANTERN-DEPLOYMENT-CHECKLIST.md: https://github.com/alex-place/gm-agent-orchestrator/blob/master/LANTERN-DEPLOYMENT-CHECKLIST.md

**Code:**
- Scripts directory: https://github.com/alex-place/gm-agent-orchestrator/tree/master/scripts
- Tests directory: https://github.com/alex-place/gm-agent-orchestrator/tree/master/tests

---

**This document is print-ready. Print 1–3 copies, keep at desk, share with stakeholders.**

**Version:** 1.0 | **Date:** 2026-05-25 | **Status:** Master Links Complete
