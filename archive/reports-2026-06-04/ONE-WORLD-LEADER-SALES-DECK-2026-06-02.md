# Lantern OS / One World Leader — Productized Local Intelligence

**Date:** 2026-06-02
**Classification:** Public-safe operator pitch deck
**Evidence class:** operator_asserted + source_repo_evidence | projection clearly labeled
**Version:** v1.0

---

## 1. Vision Scene

> Two years from now — summer 2028.

Three founders and operators stand at the van door looking out over the Garraf coast near Sitges, Spain. Alex, Courtney, and Shelby. The sun is dropping behind the ridge. Someone's Orion Watch MK1 buzzes with a memory pulse. The villa Wi-Fi is local-first. The stack running on the patio edge node is the same stack that ran in the garage.

This is a product-vision frame — a target destination, not a present-day proof claim.

The path from here to that door is built one paid packet at a time. This deck is about those packets.

---

## 2. Problem

Personal data, AI tools, wearables, memories, and workflows are fragmented across:

| Pain point | Where it lives today |
|---|---|
| Wearable health data | Siloed apps, cloud-only sync, no local ownership |
| AI assistants | Cloud endpoints, no memory continuity, no local RAG |
| Founder notes / meeting records | Scattered documents, no retrieval layer |
| Learning content | Separate platforms, no personal knowledge graph |
| Revenue tracking | Manual spreadsheets, no invoice-to-cleared-cash ledger |
| Reimbursement and cost splits | Informal, untracked, dispute-prone |
| Personal research | No local vector index, no citation chain |

The gap: there is no single local-first stack that owns memory, wearables, AI output, and a clean cash ledger — without requiring a cloud subscription or giving away private data.

---

## 3. Product Stack

### Hardware Layer

| Product | Function | Status |
|---|---|---|
| **Orion Watch MK1** | Wrist-mounted edge sensor; local pulse capture, memory trigger | Prototype concept / design phase |
| **Orion Charge Scarf** | Textile charging surface; passive device top-up | Concept |
| **Memory Puck** | Portable local RAG node; stores personal memory chunks offline | Concept |
| **Lantern Ring Audio Gate MK1** | Wearable audio capture gate; voice-to-local-memory pipeline | Concept |

### Software Layer

| Product | Function | Status |
|---|---|---|
| **RAG Dollhouse + Lantern OS** | Local vector memory, flat file RAG, citation-safe personal AI | Active development — see `skills/lantern-rag-dollhouse/` |
| **Wallet-safe Revenue Route** | Invoice draft → sent → paid → cleared cash ledger; no fake revenue | Active — see `data/wallet/` |
| **Public Bounty Radar** | Scans public bounties, grant signals, and pilot-ready buyer profiles | Planned |

> All hardware items are design-phase concepts. No manufactured inventory claimed. No revenue from hardware claimed.

---

## 4. Trust Layer

Lantern OS is built on four non-negotiable trust principles:

1. **Local-first.** Personal memory and data stay on your device by default. Cloud sync is opt-in, not default.

2. **Cited evidence.** Every report, claim, or recommendation carries an evidence class and confidence level. No invented facts.

3. **Human approval gate.** AI output is a draft. The operator approves before any send, invoice, or publish action.

4. **No fake revenue.** The wallet ledger uses a strict state machine:

```
invoice_draft → invoice_sent → invoice_paid → cash_cleared
```

Only `cash_cleared` events count as revenue. No projection is presented as cleared cash.

---

## 5. First Paid Slice

The fastest path to one dollar of cleared cash:

### Step 1: Product Atlas
- Publish a single public offer page from `reports/LANTERN-PRODUCT-UNIVERSE-ATLAS.md`
- One clear price. One clear deliverable. No ambiguity.

### Step 2: 11-Day Cash Sprint
- Run the sprint defined in `reports/COMET-LEAP-11-DAY-CASH-SPRINT.md`
- Manual outreach queue: 3–5 named contacts per day, logged in ledger
- No mass email. No spam. One human message at a time.

### Step 3: Local Wallet
- Record every cost, every invoice state, every cleared payment in `data/wallet/ledger.jsonl`
- Courtney reimbursement costs tracked in `data/wallet/courtney-reimbursement-ledger.jsonl`

### Step 4: One Paid Packet
- Close one transaction. Log the cleared payment. That is the proof event.

---

## 6. Buyer Use Cases

| Buyer | What they get | Price shape |
|---|---|---|
| **Founder / solo operator** | Report pack: personal AI context, RAG index, founder state summary | One-time flat fee |
| **Technical team** | RAG cleanup sprint: ingest, deduplicate, retrieval test, handoff | Sprint-based invoice |
| **Non-technical professional** | Local AI setup + training session: install, configure, one-hour walkthrough | Session fee |
| **Learner / researcher** | Learning packet: curated sources, local index, retrieval-ready study set | Per-packet fee |

Pricing is manual and negotiated for the pilot phase. No published price sheet until pilot data confirms willingness-to-pay.

---

## 7. Revenue Path

The only valid revenue path recognized by this stack:

```
manual_pilot → invoice_draft → invoice_sent → invoice_paid → cash_cleared
```

| State | Meaning | Can be claimed as revenue? |
|---|---|---|
| `manual_pilot` | Offer made, interest expressed | No |
| `invoice_draft` | Invoice created, not sent | No |
| `invoice_sent` | Invoice delivered to buyer | No |
| `invoice_paid` | Payment received by processor | No — pending clearing |
| `cash_cleared` | Funds confirmed cleared in account | **Yes** |

Evidence class for revenue claims: `local_verified` after bank/processor confirmation.

---

## 8. Roadmap

### Now (June 2026)

- [ ] Publish Product Atlas offer page
- [ ] Launch manual outreach queue (3–5 contacts, logged)
- [ ] First invoice drafted
- [ ] Courtney reimbursement ledger active
- [ ] RAG Dollhouse ingestion running locally

### 90 Days (September 2026)

- [ ] First cash-cleared pilot transaction recorded
- [ ] Orion Watch MK1 prototype design finalized
- [ ] Memory Puck local node tested
- [ ] Learning packet v1 delivered to first buyer
- [ ] Invoice-to-cleared pipeline validated end-to-end

### Two-Year Vision (Summer 2028 — Sitges/Garraf Coast)

> **Projection — not cleared cash, not present-day fact.**

The Sitges/Garraf coast villa scenario is a directional target: a distributed, location-independent operation running on local-first infrastructure, with multiple product lines delivering recurring revenue, and a three-person founding team operating from a van and a terrace with full stack continuity.

Getting there requires:
- Repeatable paid pilot transactions
- At least one hardware prototype validated with users
- RAG Dollhouse running as a self-hosted product, not just an internal tool
- A clean reimbursement ledger with zero disputed costs

This roadmap item is classified as `projection` (evidence class) and requires cash-cleared milestones before confidence can be raised above candidate.

---

## 9. The Ask

We are looking for:

| Ask type | What we need | What you get |
|---|---|---|
| **Pilot buyer** | Pay for one of the buyer-use-case packets above | Direct access to the stack + feedback loop with founders |
| **Partner** | Introductions to founders, operators, or technical teams who need local AI | Revenue share on closed introductions (terms TBD in writing) |
| **Paid packet order** | Pre-order a learning packet or report pack | First-mover pricing + priority delivery |

No equity offered at this stage. No projections guaranteed. One clean transaction at a time.

---

## Appendix: Source Paths

| Artifact | Path | Evidence class |
|---|---|---|
| Product Atlas | `reports/LANTERN-PRODUCT-UNIVERSE-ATLAS.md` | source_repo_evidence |
| 11-Day Cash Sprint | `reports/COMET-LEAP-11-DAY-CASH-SPRINT.md` | source_repo_evidence |
| Wallet ledger | `data/wallet/ledger.jsonl` | local_verified |
| Courtney reimbursement | `data/wallet/courtney-reimbursement-ledger.jsonl` | local_verified |
| RAG Dollhouse skill | `skills/lantern-rag-dollhouse/` | source_repo_evidence |
| Trust principles | `data/wallet/SATOSHI-STYLE-WALLET-PRINCIPLES.md` | source_repo_evidence |
| This deck | `reports/ONE-WORLD-LEADER-SALES-DECK-2026-06-02.md` | source_repo_evidence |

---

*Lantern OS / One World Leader — local intelligence, cited evidence, cleared cash only.*
*Public-safe document. No private health, legal, or financial data included.*
