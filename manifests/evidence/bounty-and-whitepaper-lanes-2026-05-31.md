# Lantern Fleet Bounty And Whitepaper Lanes

Date: 2026-05-31
Status: research radar, not a prize claim or submission
Evidence class: public-source only; no prize collection without official acceptance

## Simple Answer

These are the public science and math bounty lanes the Lantern fleet can
attack right now using local solvers, RAG compression, proof gates, and
human review. Each lane has a whitepaper angle that produces publishable
output independent of winning the prize.

---

## Bounty Lanes By Readiness

### Tier 1 - Build Now (Fleet-fit, clear workbench path)

| Lane | Prize | Deadline | Why fleet fits |
|---|---|---|---|
| ARC-AGI-3 interactive agent | $850K | 2026-11-02 | Local agent loop: explore, model, plan, act. No internet at eval. Fleet = parallel task search + failure compression. |
| ARC-AGI-2 static puzzle solver | $700K | 2026-11-02 | RAG-compressed visual transform DSL. Offline notebook. Fleet = hypothesis search over program space. |
| ARC Paper Prize | $450K | 2026-11-08 | Whitepaper lane tied to a real Kaggle submission. Fleet generates evidence receipts per run. |
| ICML 2026 AI for Math / TCS Proving | $8K | 2026-06-15 | Lean 4 theorem proving. Fast feedback loop. Deadline is close - urgent if pursued. |

### Tier 2 - Long Horizon (Formal research, not a cash sprint)

| Lane | Prize | Why it matters |
|---|---|---|
| Beal Prize | $1M | Symbolic search + Lean formalization sandbox. Prize requires published proof in refereed journal. |
| Clay Millennium Problems | $1M each | Six remain unsolved. Fleet builds verifier benchmarks, not prize claims. |
| Open Problems in Machine Learning (OPML) | Varies | NeurIPS/ICML style open challenges posted publicly. Fleet contributes experiments and receipts. |
| Polymath Project collaborative problems | Recognition | Public math collaboration. Fleet contributes partial results with provenance receipts. |

### Tier 3 - Science Bounties (Non-math, empirical)

| Lane | Prize | Notes |
|---|---|---|
| Kaggle competitions (active) | Varies | Data science + ML. Fleet runs local experiments offline. |
| AlphaFold / protein structure challenges | Research credit | Bioinformatics lanes. Fleet runs local structure search if data is public-domain. |
| DARPA / NSF public challenge grants | Varies | Check grants.gov. Fleet produces whitepaper artifacts. |

---

## Fleet Attack Shape Per Lane

### ARC-AGI-3

```
Fleet role:
  Worker A: task loader + visual transform DSL
  Worker B: curiosity policy + map memory
  Worker C: hypothesis search + self-play perturbations
  Worker D: receipt writer + submission packager
  
Gate: no internet, deterministic seed, receipt before submit
```

### ARC-AGI-2

```
Fleet role:
  Worker A: grid pattern extractor
  Worker B: program synthesis search
  Worker C: two-output submission validator
  Worker D: offline accuracy tracker
  
Gate: 85% private accuracy target, Kaggle limits only
```

### Lean / ICML Math Proving

```
Fleet role:
  Worker A: conjecture card writer (natural language → formal statement)
  Worker B: Lean 4 proof scratch
  Worker C: verifier log
  Worker D: expert-review hold gate
  
Gate: proof must pass Lean checker before human review
```

### Beal / Clay (Long horizon)

```
Fleet role:
  Worker A: literature scan + known result map
  Worker B: counterexample search (symbolic)
  Worker C: Lean formalization attempt
  Worker D: prior-art gate (no claim without novelty search)
  
Gate: no prize claim; no publication claim without attorney + journal review
```

---

## Whitepaper Lanes

Each bounty lane produces a whitepaper artifact independent of winning:

| Paper | Target venue | Core claim | Evidence needed |
|---|---|---|---|
| Lantern ARC Solver Architecture | ARC Paper Prize / arXiv | Novel local-first agent loop for ARC tasks using RAG-compressed transforms and deterministic receipts | Real Kaggle submission + accuracy receipts |
| Local-First Proof Assistance with Fleet Orchestration | ICML AI for Math | Fleet-orchestrated Lean 4 proof search with verifiable receipts and human review gates | At least one verified Lean theorem |
| Evidence-Gated Confidence Models for AI Systems | NeurIPS / ICML | Brier-calibrated confidence tracking for multi-agent systems using local evidence ledgers | Arc Reactor metrics + Brier score receipts |
| HotSwapVM: Live Block Replacement with Identity Continuity | Patent candidate / arXiv | Running system that replaces functional blocks while preserving operator trust via continuity receipts | Simulated swap receipt + block ledger |
| 4D-GMS: A Family-Safe Local Game System Architecture | Game/HCI venue | Family-first game launcher with legal catalog, parent controls, and local-first ownership map | Working alpha + three legal capsules |

---

## Minimum Next Commits

Priority order:

1. **ARC workbench** - already started; add `visual_transform.py` and `agent_stack.py` stubs
2. **Lean scratch** - add `arc-bounty-workbench/lean_scratch/` with one trivial verified theorem
3. **ICML deadline check** - 2026-06-15 is close; decide pursue or hold by 2026-06-01
4. **Whitepaper draft** - start ARC paper outline in `arc-bounty-workbench/paper_template.md`
5. **Receipt loop** - every experiment run saves a receipt before next run

---

## Boundaries

- No prize claim without official contest submission and acceptance.
- No publication claim without real results and human expert review.
- Clay / Beal work is a long-horizon research sandbox, not a revenue plan.
- No copied benchmark data, book text, or private solutions.
- All work reproducible, public-safe, and receipt-gated.
- ICML deadline is 2026-06-15 AoE - do not commit to submission without a working Lean proof.
