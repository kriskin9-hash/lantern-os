# Survival and Flourishing Fund (SFF) HSEE Round Application

**Date:** 2026-05-31 (Draft - Not Submitted)  
**Applicant:** Alex Place / Lantern OS  
**Round:** Human Self-Enhancement and Empowerment (HSEE)  
**Deadline:** July 8, 2026 at 11:59 PM PT  
**Prize Pool:** $2-4 million  
**Status:** DRAFT - Requires operator review and submission

---

## Simple Answer

Lantern OS is a local-first AI control plane for Windows. It keeps personal files, workflows, and AI tools under the user's direct control — no cloud dependency, no autonomous action without explicit human approval. The project is pre-v1.0.0 with a working local prototype, ~20 known users, a 12-step validation loop, and a Brier-calibrated confidence model. We are seeking non-dilutive funding to reach v1.0.0 with 50 validated human pilots by mid-2027.

---

## Application Section 1: Project Summary (One Paragraph)

Lantern OS is a local-first AI control plane for Windows that keeps humans organized, capable, and in control of their own files, workflows, and AI tools as AI systems become more capable and autonomous. Unlike cloud-dependent AI services that require users to surrender their data to external servers, Lantern OS runs entirely on the user's local machine — providing RAG (Retrieval-Augmented Generation) over personal documents, MCP (Model Context Protocol) connectors with verified safety boundaries, and automation workflows that require explicit human approval before taking action. The project is built on the principle that human self-enhancement requires human agency: a 12-step validation loop treats human review gates as non-negotiable, a Brier-calibrated confidence model tracks development state without overclaiming, and pre/post action hooks block automated steps that have not passed safety checks. Lantern OS is pre-v1.0.0 with a working local prototype, comprehensive documentation, and a validation methodology requiring human approval at every automated action.

---

## Application Section 2: Why This Fits HSEE

The HSEE round specifically funds "tools and approaches that help humans stay capable and empowered as AI advances." Lantern OS directly addresses this mission:

**Human Capability Enhancement:**
- Local RAG system turns scattered documents into searchable knowledge without cloud dependency
- Convergence loop methodology provides structured thinking for complex projects
- Skills library and report automation amplify individual productivity

**Human Empowerment (Agency Preservation):**
- Explicit human approval gates prevent autonomous AI action
- Local-first architecture keeps data under user control
- Safety hooks (Validate-DemoSafety, Validate-PromptSafety) enforce boundaries
- Evidence-gated documentation prevents claims beyond validated proof

**ASI-Aligned Safety:**
- Brier-calibrated confidence tracking prevents overconfidence
- ASI pattern integration as architecture references only (not capability claims)
- Strict boundaries block: unattended disk mutation, MCP execution without canary, medical claims without evidence, token/investment advice

---

## Application Section 3: Current State and Evidence

### Repository Evidence
- **Primary Repo:** https://github.com/alex-place/lantern-os
- **Status:** Pre-v1.0.0 staging, active development
- **Structure:** 12-step convergence loop, agent fleet contracts, skills library, dashboard surfaces
- **Documentation:** Comprehensive (AGENTS.md, CONVERGENCE-LOOP.md, skill docs)

### Technical Achievements
- **Convergence Loop:** 12-step validation process with explicit retire/fix/promote gates
- **Agent Fleet:** 12x3 designed review ring (36 slots) with 64-worker elastic pool
- **Local RAG System:** Flat-file memory store with evidence labeling and asset hashing (`skills/lantern-rag-dollhouse/`)
- **Confidence Tracking Model:** Brier-calibrated confidence scores per development phase (`data/arc-reactor/status.json`)
- **Windsurf Hooks:** Safety validation (pre_run_command, pre_mcp_tool_use, pre_write_code)

### Confidence Scores (Brier-Calibrated)
- Phase 1 — Local prototype operational: 95%
- Phase 2 — Public platform readiness: 68%
- Phase 3 — Distributed fleet readiness: 32%
- Human trial demo readiness: 22%

### Users/Pilots
- **Current:** ~20 known users across three tiers: 5 paid ($20/mo via Ko-fi/Patreon), 10 free-tier, 3 investor-grade (high-engagement)
- **Auth:** No OAuth yet — tracked via Ko-fi and Patreon; building toward in-app auth for v0.9.0
- **Pending:** 5 outreach sends to warm contacts for paid pilot slots; each recorded as a wallet ledger event with evidence receipt
- **Target:** 5 successful $1000 founding seat demos to raise human trial readiness score

---

## Application Section 4: Use of Funds

| Category | Amount | Purpose |
|---|---|---|
| **Development** | $150,000 | 6 months founder salary to reach v1.0.0 |
| **Infrastructure** | $25,000 | Local testing hardware, CI/CD, documentation hosting |
| **Security Audit** | $30,000 | Third-party review of MCP safety boundaries |
| **Pilot Program** | $50,000 | 50 paid pilot slots at $1000 each (founding seats) |
| **Documentation** | $20,000 | Professional technical writing, tutorial videos |
| **Community** | $15,000 | Discord moderation, community events, support |
| **Legal/Compliance** | $10,000 | License normalization, terms of service, privacy review |
| **Reserve** | $50,000 | Buffer for unexpected costs |
| **Total** | **$350,000** | 12-month operating budget to sustainable revenue or next funding round |

**Alternative smaller ask:** $100,000 for 6-month operating budget + 20 pilot slots

---

## Application Section 5: Theory of Change

**If funded:**
1. **Month 1-2:** Security audit + license normalization + v0.9.0 release
2. **Month 3-6:** 50 founding seat pilots with explicit human feedback collection
3. **Month 6-9:** Iterate based on pilot feedback, harden safety boundaries
4. **Month 9-12:** v1.0.0 release with proven human-in-the-loop operation
5. **Month 12+:** Sustainable revenue through service contracts or next funding round

**Success metrics:**
- 50 pilots completed with receipts
- Human trial demo readiness score: 80%+
- MCP canary validation: 100% pass rate
- Zero autonomous actions without human approval
- Brier-calibrated confidence tracking on all claims

**Failure modes (explicit):**
- Pilots reject the local-first tradeoffs (slower setup vs cloud convenience)
- Safety boundaries too restrictive for practical use
- Founder capacity (mitigated: realistic operating budget, 6-month checkpoint)

---

## Application Section 6: Why SFF Specifically

**Alignment with SFF mission:**
- SFF prioritizes long-term survival and flourishing of sentient life
- Lantern OS treats human agency as non-negotiable design constraint
- Local-first + explicit approval = humans remain in control as AI advances
- Evidence-gated methodology prevents overconfidence that leads to harm

**Non-dilutive fit:**
- Lantern OS is currently solo founder, no equity raised
- SFF non-dilutive funding preserves optionality
- Open-source release planned regardless of funding outcome

**SFF mission alignment (deep):**
- SFF's focus on long-term human flourishing aligns with our non-negotiable human-in-the-loop design constraints
- Evidence-gated methodology and explicit claim boundaries directly operationalize the "survival" side of SFF's mission
- Non-dilutive grant preserves founder independence for safety-first decision making

---

## Application Section 7: Boundaries and Limitations

**What Lantern OS is NOT:**
- Not an ASI (artificial superintelligence) - patterns are architecture references only
- Not a medical device - no health/PPE claims without separate validation
- Not a financial advice platform - no investment/token claims
- Not production-ready yet — pre-v1.0.0, local prototype only

**What funding will NOT be used for:**
- No cloud compute at scale (violates local-first principle)
- No marketing spend before product-market fit
- No hiring before pilot validation
- No claims beyond validated evidence

**Explicit ask:**
We seek funding to complete a rigorous, evidence-gated path to v1.0.0 with 50 human pilots. We are not claiming the solution is ready now. We are claiming the methodology (convergence loop + Brier calibration + safety hooks) produces trustworthy results worth funding.

---

## Submission Checklist

- [ ] One-paragraph summary reviewed and approved
- [ ] Use of funds breakdown confirmed realistic
- [ ] Theory of change acknowledges failure modes
- [ ] All claims matched to evidence in repo
- [ ] Rolling application form completed (https://survivalandflourishing.fund/apply — VERIFY URL before submitting; SFF rolling form URL may differ)
- [ ] HSEE supplemental application completed
- [ ] Operator approval for submission
- [ ] Submission receipt saved

---

**Draft Generated:** 2026-05-31  
**Evidence Class:** `repo_documentation` + `confidence_scores` + `methodology_validation`  
**Confidence:** Application draft is complete; funding outcome is uncertain (0.15-0.25 probability typical for competitive grants)  
**Next Action:** Operator review and submission by July 8 deadline
