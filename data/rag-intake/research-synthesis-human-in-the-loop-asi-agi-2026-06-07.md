# Research Synthesis: Human-in-the-Loop Self-Improvement for ASI/AGI

**Synthesized:** 2026-06-07  
**Topic:** Self-improving AI with human-in-the-loop frameworks — from recursive self-improvement to co-superintelligence  
**Sources:** 2 primary (read), 3 secondary (identified)  
**Confidence:** high for Anthropic internal data; medium for theoretical frameworks (pre-peer-review)  
**Status:** active synthesis, ready for citation

---

## Executive Summary

The dominant narrative in frontier AI labs has shifted from "self-improving AI" to **"co-improvement"** — humans and AI collaborating on research, with humans retaining judgment and direction-setting roles. Two landmark documents define this shift:

1. **Anthropic Institute (May 2026)** — Internal data showing Claude now writes >80% of Anthropic's merged code, achieves 52x code speedups (vs. human 4x), and beats human researchers on next-step judgment 64% of the time. Anthropic calls for verifiable slowdown/pause mechanisms before full recursive self-improvement.

2. **Weston & Foerster (Dec 2025, arXiv)** — Proposes replacing "self-improving AI" with **"co-improvement"** as the safer, faster path to superintelligence. Humans remain in the loop for steerability, safety, and societal alignment.

---

## Source Registry

| ID | Source | Type | Read Status | Freshness | Authority |
|---|---|---|---|---|---|
| SRC-001 | Anthropic Institute, "When AI builds itself" (May 2026) | Primary — internal operational data | complete | current | primary |
| SRC-002 | Weston & Foerster, arXiv:2512.05356 (Dec 2025) | Primary — preprint | complete | current | primary |
| SRC-003 | ICLR 2026 Workshop on AI with Recursive Self-Improvement | Secondary — CFP/workshop | partial | current | secondary |
| SRC-004 | Taylor & Francis, DOI:10.1080/17517575.2026.2653244 (Apr 2026) | Secondary — peer-reviewed article | inaccessible | current | primary |
| SRC-005 | IEEE Spectrum, "Recursive Self-Improvement" (2026) | Secondary — journalism | inaccessible | current | secondary |

---

## Key Claims

### Claim 1: Frontier AI already writes most of its own training infrastructure
- **Source:** SRC-001
- **Status:** verified
- **Evidence:** As of May 2026, >80% of code merged into Anthropic's codebase was authored by Claude (up from low single digits before Claude Code launched in Feb 2025). Engineers merge 8x as much code per day as in 2024.
- **Caveat:** Lines of code is an imperfect measure; true productivity gain is likely lower than 8x.

### Claim 2: AI now exceeds skilled humans at optimizing within defined experiments
- **Source:** SRC-001
- **Status:** verified
- **Evidence:** Claude achieved ~52x speedup on training code optimization (Apr 2026, Mythos Preview) vs. skilled human baseline of ~4x. Success rate on open-ended tasks reached 76% (up 50 percentage points in 6 months).

### Claim 3: AI next-step judgment is approaching human parity on research decisions
- **Source:** SRC-001
- **Status:** verified
- **Evidence:** On 129 challenging research session detours, Claude beat the human researcher's next step 64% of the time (Apr 2026, Mythos Preview) vs. 51% (Nov 2025, Opus 4.5).

### Claim 4: Co-improvement is safer and potentially faster than pure self-improvement
- **Source:** SRC-002
- **Status:** inferred (theoretical argument)
- **Evidence:** Weston & Foerster argue that including humans in the research loop provides (i) faster paradigm shift discovery, (ii) more transparency/steerability, (iii) more focus on human-centered safe AI. Pure self-improvement risks goal misspecification.

### Claim 5: The human role is narrowing toward judgment and direction-setting only
- **Source:** SRC-001
- **Status:** verified
- **Evidence:** Anthropic describes a progression: execution → goal+design → problem selection. "The doing now costs almost nothing in human time." Human comparative advantage is now "research taste and judgment."

### Claim 6: Full recursive self-improvement has not yet been demonstrated
- **Source:** SRC-001, SRC-002
- **Status:** verified
- **Evidence:** Anthropic notes Claude still requires humans to choose problems and create scoring rubrics. Weston & Foerster note AI cannot yet fully self-improve and is susceptible to misalignment.

---

## Gaps & Requests

| Gap | Severity | Action |
|---|---|---|
| SRC-004 (Taylor & Francis) inaccessible — paywalled | medium | Request library access or author preprint |
| SRC-005 (IEEE Spectrum) inaccessible — blocked | low | Find mirror or read via textise dot iitty |
| No empirical benchmark for "co-improvement" vs. "self-improvement" speed | high | Weston & Foerster call for new benchmarks; this is a research opportunity |
| Long-term safety of human-in-the-loop at superhuman capability levels | high | Open question; Anthropic calls for societal deliberation |

---

## Implications for Lantern OS

1. **Agent design:** Lantern's multi-agent personas (Keystone, Lantern, Xenon, Blinkbug, Waterfall, Founder) map naturally onto the "co-improvement" paradigm — each agent represents a different human value/judgment axis.

2. **Chat grounding:** Gemini's `google_search_retrieval` grounding (recently added to `dream-chat.js`) aligns with the co-improvement principle of "AI collaborates with humans using external knowledge" rather than "AI hallucinates in isolation."

3. **Convergence loop:** The convergence loop's human-in-the-loop validation (operator reviews before commit) is an instance of co-improvement at the infrastructure level.

4. **Research workflow:** Lantern OS could adopt the co-improvement research pipeline: human proposes → AI explores → human judges → AI implements → human validates.

---

## Citations

- [1] Anthropic Institute. "When AI builds itself." May 2026. https://www.anthropic.com/institute/recursive-self-improvement
- [2] Weston, J. & Foerster, J. "AI & Human Co-Improvement for Safer Co-Superintelligence." arXiv:2512.05356 [cs.AI], December 2025. https://arxiv.org/abs/2512.05356
- [3] ICLR 2026 Workshop on AI with Recursive Self-Improvement. Call for Papers. https://recursive-workshop.github.io/
- [4] Taylor & Francis. "From AI to AGI: a human-in-the-loop framework." *AI & Society*, DOI:10.1080/17517575.2026.2653244, April 2026.
- [5] IEEE Spectrum. "Recursive Self-Improvement Edges Closer In AI Labs." 2026. https://spectrum.ieee.org/recursive-self-improvement

---

*This synthesis follows the Lantern OS Research Evidence Contract. Claims are traceable to source IDs. Inferences are marked. Gaps are listed. Promotion to canonical docs requires audit pass.*
