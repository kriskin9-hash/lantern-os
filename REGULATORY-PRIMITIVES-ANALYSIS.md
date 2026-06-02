# Regulatory Primitives Analysis — Your Stack vs. NIST AI RMF

**Status:** Research | Analysis only, not implemented as formal "stack"  
**Date:** 2026-06-01  
**Scope:** Compare your agent_system.py + audit approach to NIST AI RMF framework

---

## What You Have

### Core Components (agent_system.py + cryptographic_proof.py)

| Component | Implementation | Purpose |
|-----------|---|---------|
| **Byzantine Consensus (PBFT)** | 7-agent quorum-based decision | Prevent single-agent bias; require supermajority (e.g., 5/7) to escalate |
| **Append-Only Audit Log** | Ed25519 signed records in SQLite | Immutable proof of when escalations occurred |
| **Time-Locking (24-hour hold)** | Escalation lock table | Delay between consensus → execution for human review |
| **Immutable Rules** | accuracy_gap_threshold=5%, escalation_is_irreversible=True | Rules enforced in code, not database |
| **Public Disclaimer** | "Research advisory software, not regulatory action" | Clear boundary: software is advisory, not enforcing |

### What It Actually Does

1. **Detects** alleged violations (e.g., 5%+ accuracy gap between subgroups)
2. **Proposes** via 7-agent consensus (PBFT quorum required)
3. **Records** in append-only log with signatures
4. **Locks** for 24 hours before execution
5. **Escalates** (currently: appends to log for human review, not actual regulatory notification)

### What It Explicitly Doesn't Do

- ❌ Notify regulators (would require partnerships)
- ❌ Override human decision-making
- ❌ Self-propagate (runs only on your deployed nodes)
- ❌ Enforce against database admins (SQLite can be directly modified)
- ❌ Make legal determinations (courts, not software, decide admissibility)

---

## NIST AI RMF Framework (Quick Reference)

NIST AI Risk Management Framework has 4 core functions:

### 1. GOVERN
**Purpose:** Establish AI governance structure, risk tolerance, oversight  
**Your coverage:** ✅ Partial
- ✅ You have a PBFT-based decision system
- ✅ You have immutable rules + audit log
- ❌ Missing: formal governance structure (board, appeals process, policy registry)

### 2. MAP
**Purpose:** Identify AI systems, risks, and stakeholders  
**Your coverage:** ❌ Minimal
- ✅ You log violations
- ❌ Missing: system inventory, threat modeling, stakeholder mapping, risk categorization
- ❌ Missing: which specific AI models/features are in scope?

### 3. MEASURE
**Purpose:** Measure AI risk and performance (benchmarks, tests, metrics)  
**Your coverage:** ✅ Partial
- ✅ You have accuracy_gap_threshold (a metric)
- ❌ Missing: comprehensive metrics (fairness, robustness, explainability, security)
- ❌ Missing: benchmarking against baselines
- ❌ Missing: evaluation protocols

### 4. MANAGE
**Purpose:** Mitigate identified risks through controls and monitoring  
**Your coverage:** ✅ Partial
- ✅ You have escalation (a control response)
- ✅ You have 24-hour lock (cooling-off control)
- ❌ Missing: other mitigation strategies (model retraining, data cleanup, feature removal, etc.)
- ❌ Missing: ongoing monitoring plan

---

## Side-by-Side Comparison

| NIST AI RMF | Your System | Gap |
|---|---|---|
| **GOVERN: Risk tolerance policy** | Hardcoded in `IMMUTABLE_RULES` | Need formal policy document + governance board |
| **GOVERN: Audit trail** | ✅ Ed25519 signed audit log | ✅ Good match |
| **GOVERN: Escalation procedure** | 24-hour lock → human review | Partial; no defined "who reviews" or "what next" |
| **MAP: AI system inventory** | Not applicable; single system focus | Need registry if multi-system |
| **MAP: Risk categorization** | Only accuracy gaps; what about other risks? | Need threat model |
| **MEASURE: Fairness metrics** | accuracy_gap threshold only | Need: demographic parity, equalized odds, calibration, etc. |
| **MEASURE: Benchmarks** | None documented | Need: baseline model + comparison |
| **MEASURE: Evaluation protocol** | Not formalized | Need: when/how often to test, who validates results |
| **MANAGE: Mitigation controls** | Escalation + cooling-off only | Need: remediation playbook (retrain, pause, rollback, etc.) |
| **MANAGE: Monitoring** | Real-time detection via 7-agent system | ✅ Good; but need SLA for response time |

---

## Honest Assessment

### Strengths

1. **Excellent consensus mechanism** — PBFT 7-agent quorum is novel + solid
2. **Immutable audit log** — Ed25519 signing + append-only = good for accountability
3. **Time-locking** — thoughtful cooling-off period
4. **Clear disclaimer** — explicitly not claiming regulatory authority

### Weaknesses vs. NIST AI RMF

1. **No governance structure** — NIST expects board, policy, appeal process; you have code
2. **Single metric** — accuracy gap; NIST RMF covers fairness, robustness, security, explainability
3. **No threat model** — NIST expects structured risk identification
4. **Incomplete mitigation** — you have escalation; missing: retrain, rollback, pause, feature removal
5. **No formal evaluation protocol** — NIST expects documented testing + benchmarking

### Positioning Options

#### Option A: "Research Advisory System"
- **Honest position:** This is a proof-of-concept that *demonstrates* some NIST AI RMF principles
- **Key statement:** "We implement audit log + consensus + time-locking, which map to NIST GOVERN and MANAGE. We do not implement the full RMF."
- **Risk:** Undersells the solid technical work
- **Honesty:** High

#### Option B: "NIST AI RMF Prototype"
- **Claim:** We're building toward full NIST compliance
- **Key additions needed:** governance policy, threat model, full metrics set, remediation playbook
- **Estimated effort:** 4-6 weeks to close gaps
- **Risk:** Implies more coverage than you have; needs follow-through
- **Honesty:** Medium (if you commit to roadmap)

#### Option C: "Regulatory Primitives v0"
- **Positioning:** We've implemented 3 primitives (audit, consensus, time-lock) that are foundational to any AI governance system
- **Key statement:** "These are the technical building blocks regulators and risk frameworks expect. We've validated them; we're not claiming full compliance."
- **Risk:** "Primitives" sounds authoritative but isn't a standard term
- **Honesty:** Medium-high

---

## Recommendation

**Go with Option A** (with roadmap to B):

```markdown
## Status: Research Advisory System

Lantern implements three core regulatory primitives:

1. **Immutable Audit Log** (Ed25519 signing, append-only)
2. **Byzantine Consensus** (PBFT 7-agent quorum for proposals)
3. **Time-Locking** (24-hour hold before escalation)

These map to NIST AI RMF GOVERN and MANAGE functions. We do NOT implement:
- Full governance structure (board, policy, appeals)
- Complete metrics suite (fairness, robustness, explainability)
- Threat modeling or risk categorization
- Remediation playbook beyond escalation

**Roadmap:** In Q3 2026, we will add:
- Formal governance policy document
- NIST-aligned fairness metrics (demographic parity, equalized odds, calibration)
- Threat model + risk registry
- Remediation playbook (retrain, pause, rollback strategies)

This positions us as honest but ambitious — we have real tech, we know what's missing, and we have a plan.
```

---

## What NOT to Say

❌ "Court-admissible proofs" — courts, not software, decide admissibility  
❌ "Regulatory compliance" — you don't have full NIST RMF coverage  
❌ "Impossible engine that regulators can't override" — misleading + false  
❌ "Autonomous enforcement system" — you explicitly require human review  

---

## Files to Update

Once you decide on positioning:

1. **agent_system.py docstring** — update to match chosen option
2. **README.md** — clarify regulatory position (research vs. toward-compliance)
3. **docs/REGULATORY-APPROACH.md** — new doc explaining stance + roadmap
4. **OVERVIEW.md** — mention regulatory primitives as foundation, not full system

---

## TL;DR

| Aspect | Truth |
|--------|-------|
| Do you have PBFT consensus? | ✅ Yes, real implementation |
| Do you have audit log? | ✅ Yes, Ed25519 signed |
| Do you have time-locking? | ✅ Yes, 24-hour hold |
| Are these novel? | ❌ Not really (blockchain + audit log patterns) but solid execution |
| Do you have full NIST AI RMF? | ❌ No, only 2/4 functions partially covered |
| Should you claim "regulatory primitives stack"? | ✅ Yes, as research foundation + roadmap, not final solution |
| Is this production-ready? | ⚠️ For research/audit; not for actual regulatory notification |

**Bottom line:** You have solid technical building blocks. Position them honestly as *foundation* for compliance, not *compliance itself*.
