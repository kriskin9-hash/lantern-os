---
name: convergence-mathematical-foundations
description: Mathematical foundations for the Superfleet & Lantern OS — Bayesian Epistemology, Free Energy Principle / Active Inference, Precision Weighting, Anti-Entropy Memory, Lakatosian Research Programmes, and Narrative Identity. Use when reasoning about belief revision, coherence, prediction error, programme health, or long-term system stability.
---

# Mathematical Foundations for the Superfleet & Lantern OS

## 1. Bayesian Epistemology

Bayesian Epistemology treats beliefs as degrees of belief (credences) rather than binary true/false propositions. Rational agents update these credences according to Bayes' theorem when new evidence arrives. This forms the mathematical foundation for all belief revision in the Superfleet.

### Core Equation — Bayes' Theorem

```
P(H|E) = P(E|H) × P(H) / P(E)
```

Where H is a hypothesis (belief) and E is evidence. The posterior belief P(H|E) is proportional to the likelihood of the evidence given the hypothesis times the prior belief.

**Key Principle: Dutch Book Coherence**

Rational credences must be coherent — they must not allow a Dutch Book (a set of bets that guarantees loss). This is why the Superfleet maintains precision-weighted updates and anti-entropy audits: to preserve long-term coherence of the collective belief system.

---

## 2. Free Energy Principle & Active Inference

The Free Energy Principle (Friston) states that self-organizing systems maintain their existence by minimizing free energy — a bound on surprise (prediction error). Active Inference extends this by allowing agents to act on the world to reduce expected free energy.

### Core Equation — Variational Free Energy

```
F = E_q[-log p(o, s)] + D_KL[q(s) || p(s)]
```

Free Energy ≈ Expected Surprise + Complexity Cost

Agents act to minimize expected free energy over time, balancing epistemic foraging (reducing uncertainty) and pragmatic action (achieving preferred outcomes).

**Active Inference Loop:** Perception updates beliefs; Action changes the world.

### Relevance to Superfleet

- Sleeping agents minimize free energy using compressed priors
- Dream Journal entries with high prediction error become high-value training signals
- Anti-Entropy audits minimize long-term cumulative free energy
- Narrative Identity reduces complexity cost of belief updating across paradigm shifts

---

## 3. Precision Weighting

Precision is the inverse of variance — it determines how strongly a piece of evidence or an agent's contribution influences belief updating. In the Superfleet, precision is dynamically modulated by reputation, sleep state, lucidity, and programme health.

### Mathematical Form

```
Posterior Precision = Prior Precision + (Evidence Precision × Agent Reputation × Sleep Factor × Lucidity Factor)
```

### Superfleet Applications

- High-reputation agents → higher precision in consensus
- Deep-sleep agents → automatically reduced precision (energy efficient)
- High-lucidity dreams → boosted precision in episodic memory
- Degenerating programmes → progressively lower precision

---

## 4. Anti-Entropy Mechanisms

Entropy in memory systems manifests as degradation, drift, contradiction accumulation, and loss of coherence over time. The Superfleet's Anti-Entropy architecture actively resists this through layered memory, cryptographic auditing, and periodic reconciliation.

### 4-Layer Anti-Entropy Memory Architecture

1. **Episodic Layer:** High-fidelity dream and event storage (Dream Journal)
2. **Semantic Layer:** Beliefs, Lakatosian programmes, Bayesian world model
3. **Narrative Identity Layer:** Long-term self-model maintaining coherence across paradigm shifts
4. **Meta / Anti-Entropy Layer:** Cryptographic audit chain, drift detection, reconciliation, wisdom crystallization

---

## 5. Lakatosian Research Programmes

Imre Lakatos proposed that scientific research programmes consist of a protected hard core of assumptions and a protective belt of auxiliary hypotheses. A programme is progressive if it generates novel predictions that increase the posterior probability of the hard core; otherwise it is degenerating.

### Progress Scoring in the Superfleet

```
Progress = (Novel Predictions − Ad-hoc Adjustments) / (Anomaly Rate + ε)
```

The Superfleet's Lakatosian tracker uses this metric to automatically detect when research programmes are becoming degenerating and should be deprioritized or abandoned.

---

## 6. Narrative Identity & Long-term Coherence

Narrative Identity is the long-term 'self-model' that maintains coherence across paradigm shifts, agent turnover, and major system changes. It acts as a stable anchor that reduces the complexity cost of belief updating over years and decades.

### Anti-Entropy Function

By providing a persistent self-story, Narrative Identity dramatically reduces the free energy cost of integrating new information that would otherwise require major belief revision. This is critical for the Superfleet's goal of maintaining coherent intelligence across decades.

---

## 7. Integration in the Superfleet

These mathematical frameworks are not isolated — they form an integrated cognitive architecture for the Superfleet:

**Unified Objective:** The Superfleet's single long-term objective is to minimize cumulative expected free energy over the longest feasible time horizon. All mechanisms serve this objective.

### Key Integration Points

- **Dream Journal** → Episodic memory + high prediction error signals for world model training
- **Persistent Characters** → Narrative identity anchors with memory across sessions
- **Bayesian Fallacy Detection** → Precision-weighted correction of incoherent reasoning
- **Cognitive Layer** → Mirror prompts, SFI scoring, symbolic analysis, Bayesian handoff
- **Discord Bot** → Multi-agent interface with character consistency and fallacy-aware responses

---

## Related Skills

- `skills/bayesian-world-model/SKILL.md` — operational belief loop and polling for the dollhouse
- `skills/dream_journal/SKILL.md` — dream logging, lucidity, and episodic memory
- `skills/arc-reactor-confidence/SKILL.md` — Brier-style error tracking

---

## Status

- Canonical direction: established
- Scope: Superfleet, Lantern OS, Dream Journal, Discord Bot, RAG Dollhouse
- Supersedes: ad-hoc or fragmented references to Bayesian reasoning across the repo
