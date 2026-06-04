# Regulatory Primitive Stack for AI Agent Systems

Status: research draft v0.1
Date: 2026-05-06
Audience: standards authors, AI safety researchers, compliance engineers, policy reviewers
Disclaimer: this document is enforcement substrate research, not legal advice; deployments still require qualified counsel

---

## Abstract

Modern AI compliance is built backwards. Vendors ship per-regulation point solutions ("HIPAA-eligible Claude," "FERPA-safe ChatGPT," "FedRAMP-authorized Bedrock") and treat each regime as a distinct moat. We argue that every regulation that touches AI agent systems decomposes into the same small set of runtime primitives, executed in one of three modes. We formalize a **10 × 3 matrix** (ten primitives × three execution modes) plus two execution modifiers (dynamic externally-maintained predicates, temporal obligations), demonstrate the framework on US federal and US payments regulations, and argue that the agent system itself — not the model, not the wrapper, not external monitoring — is the correct enforcement layer because it is where data classification, authority resolution, capability selection, and provenance generation converge at action time. We sketch four derived specifications (Capability Claim Format, Agent Action Provenance Format, Negative Authority Profiles, Provider Capacity State Format) plus a fifth (Data Classification Format) that together instantiate the framework.

---

## 1. Motivation

The current state of AI compliance has three structural problems.

**Vendor incentives push toward point solutions.** Each major lab markets per-regulation compliance ("HIPAA," "FedRAMP," "SOC 2") because it sells better than "we have decomposed compliance into eleven shared primitives." This produces apparent coverage of named regulations while leaving the underlying primitive surface unstandardized.

**Compliance teams and AI engineers do not share vocabulary.** Compliance teams know implicitly that GDPR, FERPA, and HIPAA share most underlying mechanics. AI engineers do not see the shared structure because they work from vendor-provided checklists. The decomposition exists in lawyers' heads but is not encoded in the runtime.

**The primitives have only become operational with capability honesty.** Until the AI agent system itself can prove, at action time, what models, tools, providers, and data classes are authorized for the current actor in the current context, "this provider is approved for this data class" has been a contract clause, not an enforcement point. Capability honesty as a runtime doctrine ([Anthropic 2026 internal; this repo's `docs/product/capability-honesty-model.md`]) makes per-action enforcement possible for the first time.

The combination — vendor incentives, vocabulary gap, and recently-arrived enforcement substrate — explains why the primitive observation in this paper is "obvious in hindsight" yet has not been formalized.

---

## 2. The ten primitives

When approximately one hundred fifty regulations and frameworks that touch AI agent systems are decomposed into their runtime requirements, ten primitives emerge as common substrate. Each primitive is described with its requirement, an existing regulation example, and the substrate already present in the reference repo.

### Primitive 1 — Data classification

**Requirement.** Every datum the agent processes carries a class label (`pii.email`, `phi.diagnosis`, `ferpa.educational_record`, `pci.pan`, `cui.basic`, `coppa.under_13_identifier`, etc.). Labels propagate through transformations: a summary of a FERPA record is still a FERPA record; a hash of a SSN is still subject to access controls under most state privacy laws.

**Example.** HIPAA's "minimum necessary" standard requires that PHI use is limited; this is enforceable only if PHI is identifiable as such in the data flow.

**Substrate.** Currently absent in the repo as an explicit primitive; implicit in some preflight gates. Derived spec: **DCF (Data Classification Format)**.

### Primitive 2 — Authority and consent gates

**Requirement.** Every action that requires authorization (operator approval, user consent, role grant, scope authorization) must resolve that authorization at action time, against a record that is independently verifiable.

**Example.** GDPR Art. 6 lawful bases; FERPA's school official exception; OAuth scope grants.

**Substrate.** `CLAUDE.md`'s prohibited and explicit-permission action lists are an instance of this primitive scoped to a single agent. Derived specs: **NAP (Negative Authority Profiles)** for hard denials, plus positive grants in **CCF**.

### Primitive 3 — Provenance and audit

**Requirement.** Every action produces a record that ties the artifact (commit, edit, message, transaction) to the actor (model + version + prompt + tools + capability claims + operator + tenant), with sufficient detail to reproduce the decision.

**Example.** SR 11-7 model risk management requires reproducible model decisions; SOX requires audit trails for financial reporting; OMB M-24-10 requires AI inventories.

**Substrate.** `logs/control-actions/*.json`, `reports/queue-movements/*.jsonl`. Derived spec: **AAPF (Agent Action Provenance Format)**.

### Primitive 4 — Capability constraints

**Requirement.** The agent must prove, at action time, that it has the capability it claims: a working model, a verified tool surface, a fresh provider authorization, an authorized MCP endpoint. Hallucinated capability is a compliance failure, not a usability bug.

**Example.** EU AI Act Art. 14 (human oversight) requires that operators understand actual system capabilities; FDA SaMD guidance requires that medical device claims match validated capability.

**Substrate.** `Test-GeminiCliPreflight.ps1`, `status/gemini-preflight.json`, `schemas/capability-map.schema.json`. Derived spec: **CCF (Capability Claim Format)**.

### Primitive 5 — Boundary enforcement

**Requirement.** Data and capability flows respect explicit boundaries: local-only profiles do not call cloud providers; non-BAA paths do not transmit PHI; region-locked tenants do not egress data to non-approved jurisdictions.

**Example.** EO 14117 / 28 CFR 202 (bulk US person data to countries of concern); HIPAA BAA scope; FedRAMP authorization boundaries.

**Substrate.** Capability honesty doctrine implies this primitive; current implementation is partial.

### Primitive 6 — Subject rights

**Requirement.** Data subjects have rights (access, correction, erasure, portability, opt-out, objection) that the system must serve, often within statutory time windows.

**Example.** GDPR Art. 15-22; CCPA/CPRA Title 1.81.5; FERPA 34 CFR 99.10 (45-day access); HIPAA Privacy Rule §164.524.

**Substrate.** Not present in the repo. Always operates in the temporal mode (Mode C below).

### Primitive 7 — Incident response

**Requirement.** Detection, containment, evidence preservation, and notification follow defined procedures with statutory timelines.

**Example.** GDPR Art. 33 (72-hour breach notification to supervisory authority); HIPAA Breach Notification Rule (60-day individual notification); state breach laws (varies, 30-90 days typical); EU NIS2 (significant incident reporting).

**Substrate.** `tasks/failed/` directory and audit log are partial substrate. Always operates in modes B and C.

### Primitive 8 — Vendor chain and flow-down

**Requirement.** Obligations propagate through the supply chain: a covered entity's BAA with a vendor must flow down to the vendor's sub-processors; FedRAMP boundary obligations flow to subcontractors; PCI-DSS scope flows to processors.

**Example.** HIPAA §164.308(b) (BAA); GDPR Art. 28 (processor); OCC Third-Party Risk Management; Bank Service Company Act.

**Substrate.** Not present in the repo as an explicit primitive.

### Primitive 9 — Threshold-based reporting obligations

**Requirement.** When a defined pattern or threshold is met, the system must inform a regulator, trusted contact, or audit log — independent of any allow/deny decision on the action itself.

**Example.** FinCEN BSA SAR (suspicious activity ≥$5K), CTR (cash ≥$10K); OMB M-24-10 high-impact AI inventory; state Adult Protective Services mandatory reporting; FERPA disclosure tracking under §99.32; GDPR Art. 35 DPIA threshold.

**Substrate.** Not present in the repo as an explicit primitive. Reveals a gap: most compliance tooling assumes synchronous gating only.

### Primitive 10 — Supply chain attestation

**Requirement.** The provenance of the agent's own software, models, tools, and connections is attested: SBOM for software dependencies, signed model identifiers, hashed prompt templates, verified MCP endpoints, sanctioned-vendor screening.

**Example.** EO 14028 + NIST SP 800-218 (SSDF); Section 889 NDAA 2019 (banned vendors); CMMC 2.0 evidence requirements; ISO/IEC 5230 (OpenChain).

**Substrate.** Partial — Gemini CLI hooks resolved to `C:\hooks\sessionstart.mjs` (a non-existent path) without detection, illustrating the gap.

---

## 3. The three execution modes

The primitive set above is necessary but not sufficient. Federal and payments regulations demonstrate that primitives execute in three distinct modes. Compliance tooling that supports only one mode (typically Mode A) fails the moment it touches federal benefits or financial services.

### Mode A — Synchronous gating

The action is allowed, denied, or routed for approval at the moment it is requested. Most policy engines, RBAC systems, OAuth scope checks, and content-safety filters operate exclusively in Mode A.

*Examples.* OFAC SDN screen before wire origination; PHI → non-BAA capability denied; CUI → unauthorized capability denied.

### Mode B — Asynchronous reporting obligation

The action is allowed (or already happened), and a downstream obligation is triggered: inform a regulator, generate a SAR, log to a tenant-aware audit, alert a trusted contact. The obligation has its own deadline and consequences for non-fulfillment.

*Examples.* FinCEN SAR within 30 days of detection; state APS report when an AI assistant detects suspected elder financial exploitation; OMB M-24-10 high-impact AI inventory entry; GDPR Art. 33 supervisory authority notification within 72 hours.

### Mode C — Temporal contract

An action starts a clock; the system must produce a defined outcome within a statutory window, regardless of the agent's other state.

*Examples.* Reg E §1005.11 ten-day provisional credit; FERPA 45-day records access; Privacy Act access response; HIPAA §164.524 30-day records access; Reg Z §1026.13 60-day billing error window; GDPR Art. 12 one-month subject access response.

The asymmetry matters operationally: Mode A failures look like errors; Mode B and C failures look like nothing happened until a regulator asks. Most compliance tooling cannot detect Mode B or C failures because they do not occur at action time.

---

## 4. The two execution modifiers

Two cross-cutting modifiers apply across primitives and modes. They are not new primitives because they do not introduce new compliance requirements; they describe how primitives must behave under realistic conditions.

### Modifier 1 — Dynamic externally-maintained predicates

Some authorization predicates reference lists maintained by external authorities and updated frequently: OFAC SDN lists, BIS Entity List, Section 889 covered list, FedRAMP Marketplace, CMS exclusion list, FATF high-risk jurisdictions. The runtime must refresh these lists, prove the freshness of the data used in any decision, and degrade safely when the source is unreachable.

*Implication.* CCF and NAP claims must be parameterized over a `predicate_source` and a `freshness_proof`. A claim derived from an OFAC list refreshed five seconds ago is not the same artifact as one from a six-month-old snapshot.

### Modifier 2 — Temporal obligations as first-class state

Mode C requires that deadlines be tracked as first-class state in the audit substrate, not as implicit follow-ups. AAPF must include start, deadline, completion, and overdue states. Subject rights and incident response always carry temporal obligations.

*Implication.* The provenance ledger is not a log; it is a state machine over actions, with transitions tied to wall-clock time.

---

## 5. The 10 × 3 matrix

| Primitive | Mode A (sync gate) | Mode B (async report) | Mode C (temporal) |
|---|---|---|---|
| 1. Data classification | Label propagation gate | Mislabel detection report | Class change retention |
| 2. Authority and consent | Approval check | Consent revocation log | Consent expiration |
| 3. Provenance and audit | Action signing | Audit anomaly report | Retention windows |
| 4. Capability constraints | Capability claim verify | Capability drift detection | Claim freshness deadline |
| 5. Boundary enforcement | Egress check | Cross-boundary attempt log | Re-attestation cycle |
| 6. Subject rights | Access decision | Rights request escalation | Statutory response window |
| 7. Incident response | Containment action | Regulator notification | Notification deadline |
| 8. Vendor chain and flow-down | Sub-processor approval | Sub-processor change notice | DPA refresh cycle |
| 9. Threshold reporting | Pattern match | Generated report | Reporting deadline |
| 10. Supply chain attestation | Component verification | SBOM update notification | Re-attestation cycle |

Observation: every primitive has at least one mode, most have all three. No regulation analyzed touches only one cell. A primitive stack that supports only Mode A is structurally unable to encode FinCEN, EU AI Act, FERPA, HIPAA, or any federal regulation.

---

## 6. Worked example — US federal regulations

The federal regulatory surface is where the framework's three execution modes become essential. Synchronous gating alone is insufficient.

### Cloud authorization layer

**FedRAMP** (Low / Moderate / High / JAB-P-ATO) authorizes a cloud service for federal data use. Maps to primitive 4 (capability constraints) — only services with current authorization at the required tier qualify — and primitive 5 (boundary enforcement) — federal data does not flow to non-authorized capabilities. Mode A gating, with Modifier 1 (FedRAMP Marketplace as dynamic predicate) and Mode C (authorization expiry).

### Federal security baseline

**FISMA** + **FIPS 199** + **NIST SP 800-53** assigns categorization (Low/Moderate/High) and a control baseline (~1000 controls across 20 families). Every primitive has 800-53 controls behind it. SP 800-53 is essentially the master union of the framework's primitives expressed as federal control language.

### Federal data outside federal systems

**NIST SP 800-171** (Controlled Unclassified Information / CUI) governs contractors handling federal data. Maps to primitive 1 (DCF: `cui.*` classes), primitive 4 (CCF gating: only authorized capabilities), primitive 3 (AAPF: audit logs).

### DoD contractors

**CMMC 2.0** (Levels 1-3) certifies cyber maturity. Maps to primitive 4 (capability tier) and primitive 10 (supply chain attestation: certification artifacts). Mode C (re-attestation cycle).

### Export-controlled technology

**ITAR** (defense articles) and **EAR** (dual-use technology) restrict who can access controlled tech. Maps to primitive 2 (authority over person classes — US persons, foreign nationals) and primitive 5 (boundary: no transmission to unauthorized recipients). Modifier 1 (BIS Entity List as dynamic predicate).

### Criminal justice

**CJIS Security Policy** governs systems handling criminal justice information. Maps to primitive 1 (DCF: `cjis.*`), primitive 2 (authority gates: NCIC certification), and primitive 3 (AAPF: audit retention).

### Tax data

**IRS Publication 1075** governs Federal Tax Information (FTI) handling by state agencies and contractors. Maps to primitive 1 (DCF: `fti.*`), primitive 4 (CCF: no FTI to unauthorized capability), primitive 8 (flow-down to subcontractors).

### Software supply chain

**EO 14028** + **NIST SP 800-218** (SSDF) requires SBOM and secure development practices for federal software. Maps directly to primitive 10. **Section 889 NDAA 2019** prohibits specified vendors in federal supply chain — primitive 10 with Modifier 1 (covered list as dynamic predicate).

### AI use by federal agencies

**OMB M-24-10** + **EO 14110** require AI inventories, impact assessments, and rights/safety determinations. Maps to primitive 3 (AAPF: inventory entries), primitive 9 (threshold reporting: high-impact AI determination triggers reporting), primitive 7 (incident response: rights/safety adverse outcomes).

### Bulk sensitive personal data

**EO 14117** + **28 CFR 202** restrict bulk US-person data flowing to "countries of concern" via specified data brokers and transactions. Maps to primitive 1 (DCF), primitive 2 (NAP: jurisdiction-aware denylists), primitive 5 (boundary). Modifier 1 (DOJ-maintained restricted-transaction list).

### Federal records

**Privacy Act of 1974** governs federal agency record systems. Maps to primitive 6 (subject rights: access, correction) and primitive 3 (AAPF: System of Records Notices). Mode C (statutory response windows).

### Zero trust

**OMB M-22-09** + **M-24-04** require federal zero-trust architecture: per-action authorization, no implicit trust. This is precisely what CCF (primitive 4) operationalizes — every action verified at the time it is requested, against fresh evidence.

---

## 7. Worked example — US payments regulations

The payments regulatory surface adds dynamic external lists (sanctions screening) and threshold-based reporting at high frequency. Mode B is dominant in this domain.

### Card data

**PCI-DSS v4.0.1** governs cardholder data storage and transmission. Maps to primitive 1 (DCF: `pci.pan`, `pci.cvv`, etc.), primitive 4 (CCF: PCI-scoped capabilities only), primitive 5 (boundary).

### Electronic funds transfers

**Reg E** (Electronic Fund Transfer Act) sets consumer protections, error resolution windows, and unauthorized transaction liability tiers. Mode C is dominant: 60-day error window, 10 business days to provisional credit, 45 days to investigation completion.

### Privacy of financial information

**Reg P** (GLBA implementation) governs sharing of nonpublic personal financial information. Maps to primitive 2 (NAP per profile), primitive 1 (DCF: `nppi.*`).

### ACH

**NACHA Operating Rules** govern Automated Clearing House origination. Maps to primitive 4 (CCF: origination eligibility tier), primitive 3 (AAPF: complete audit chain — return codes, prenotes, authorization records).

### Anti-money laundering

**FinCEN BSA** + **31 CFR 1020** requires suspicious activity reporting, currency transaction reporting, customer identification, and AML programs. Mode B is dominant: SAR within 30 days of detection (>$5K), CTR for cash transactions ≥$10K. Primitive 9 (threshold reporting) with primitive 3 (AAPF) as substrate.

### Sanctions screening

**OFAC SDN list** + sectoral lists must be screened before any financial transmission. Maps to primitive 2 (NAP) with Modifier 1 (externally-maintained dynamic denylist with freshness proof). Failure to screen is a strict-liability OFAC violation regardless of intent.

### Wire originator information

**Travel Rule** (31 CFR 1010.410) requires originator information to accompany wires ≥$3,000. Maps to primitive 1 (DCF labeling propagation) and primitive 3 (AAPF: chain integrity).

### Money movement licensing

**State money transmitter licensing** (49 states + DC) is required for non-bank money movement. CSBS NMLS registration is the meta-process. Maps to primitive 4 (CCF: capability tier — entity-level authorization) and primitive 8 (flow-down where agents/sub-agents are involved).

### Cross-border remittance

**Dodd-Frank §1073** + **Reg E Subpart B** require disclosures for international transfers ≥$15. Mode C: 30-minute cancellation window, 35-day error notice period.

### Open banking

**CFPB §1033** (Personal Financial Data Rights) governs consumer access and portability of financial data. Maps to primitive 6 (subject rights).

### Larger digital wallet supervision

**CFPB Larger Participant Rule** (2024) brings major nonbank digital wallet providers under CFPB supervision. Implies that AI assistants integrated with such wallets inherit the supervised entity's primitive obligations.

### Fair lending

**ECOA** + **Reg B** prohibit discrimination in credit decisions and require adverse action notices. The primitive surface here is unusual: it requires *post-hoc statistical testing* of agent decisions for disparate impact — an extension of primitive 3 (AAPF) toward population-level audit.

### Elder financial exploitation

**FINRA Rule 2165**, **Senior Safe Act** (2018), and state mandatory reporter laws permit (and in many states require) reporting of suspected elder financial exploitation. Mode B with tenant-aware obligation: a financial advisor's AI assistant inherits the advisor's reporting obligation; a consumer's AI assistant generally does not, but the "trusted contact" pattern is a Mode B obligation regardless.

### Cryptocurrency

**FATF Travel Rule** for VASPs and **GENIUS Act** (stablecoins, July 2025) extend payments primitives to crypto rails with new DCF data classes (`crypto.*`).

### European strong customer authentication

**PSD2 SCA** requires two-factor authentication for most online payments. Maps to primitive 2 (consent gates) with Mode C (authentication freshness window).

### Bank vendor management

**OCC Third-Party Risk Management** + **Bank Service Company Act** propagate the bank's regulatory obligations to AI vendors. Direct application of primitive 8 (flow-down).

### Consumer protection (catch-all)

**UDAAP** (Dodd-Frank §1031, FTC §5) prohibits unfair, deceptive, or abusive acts. Operates primarily in Mode B (post-hoc enforcement) but produces Mode A obligations once interpreted into specific guidance (CFPB consent orders, settlement terms).

---

## 8. The convergence demonstration — federal benefits navigation

Federal and payments converge most usefully in **AI-assisted federal benefits navigation**, a use case nobody serves safely today:

- A caregiver helping an elderly relative apply for Social Security retirement
- A teacher helping families apply for federal free or reduced-price lunch
- A social worker assisting with Medicaid renewal
- A veteran navigating VA benefits with AI assistance

A single transaction in this space touches:

- **Privacy Act of 1974** (federal records — primitives 6, 3, 7)
- **HIPAA Privacy Rule** (Medicaid touches PHI — primitives 1, 4, 5, 8)
- **Reg E** (benefits paid via EBT or direct deposit — primitive 9 + Mode C)
- **State Adult Protective Services mandatory reporting** (suspected exploitation — primitive 9 with tenant-aware obligation)
- **FERPA** (school-administered programs like NSLP — primitive 1, 4)
- **COPPA** (children involved — primitive 2)
- **Section 504 / ADA Title II** (disability accommodation — primitive 5)
- **§508 / WCAG 2.2 AA** (accessibility of federal communications — primitive 5)
- **OMB M-24-10** (when used by a federal agency — primitive 9, 10)
- **Dodd-Frank §1073** (international family remittances — primitive 9 + Mode C)
- **OFAC SDN screening** (any payment context — primitive 2 + Modifier 1)
- **FinCEN BSA** (large or unusual benefit-related cash patterns — primitive 9 + Mode B)
- **Senior Safe Act** + FINRA 2165 (when assistance is provided through a financial professional — primitive 9, tenant-aware)
- **CFPB UDAAP** (consumer protection — primitive 9 mode B post-hoc)

Today, every commercially-available AI assistant either (a) refuses such tasks via blanket disclaimers, (b) handles them while disclaiming legal responsibility (transferring risk to the operator), or (c) handles them with risk that the operator absorbs unknowingly. None offer **verifiable enforcement** that survives regulator inspection.

A primitive stack that operates correctly across all ten primitives in all three modes can serve this use case safely. The demonstration is not a feature; it is a falsifiable prediction: if the framework is correct, then a properly-instantiated agent system can serve federal benefits navigation in a way that survives a CMS, IRS, or state APS audit. If it cannot, the framework needs revision.

---

## 9. Spec derivations

The following five specifications are derived from the framework. Each instantiates a subset of the primitives × modes matrix. They are independent (each is publishable on its own) but composable (each consumes outputs of the others).

### CCF — Capability Claim Format

Operationalizes primitive 4. A signed, timestamped, freshness-proven claim that an agent has a specific capability (a working model, a verified MCP endpoint, an authorized provider key, a tool surface). Modes A (gating), B (drift detection), C (claim expiry). Modifier 1 (dynamic predicates) and Modifier 2 (temporal claims) are first-class.

### AAPF — Agent Action Provenance Format

Operationalizes primitive 3. A signed, reproducible record tying an artifact to (model + version + prompt + tools + capability claims + operator + tenant + git state). All three modes. Modifier 2 (temporal obligations) is first-class because audit retention windows differ by primitive.

### NAP — Negative Authority Profiles

Operationalizes primitive 2 in its denial form. A profile schema for action classes that are denied regardless of approval flow. Operates primarily in Mode A but composes with Mode B (denied-action notification) and Modifier 1 (dynamic external lists like OFAC SDN, BIS Entity List).

### DCF — Data Classification Format

Operationalizes primitive 1. A labeling schema that propagates through agent transformations and gates capability claims (CCF) by data class. Mode A primary, with Mode B for misclassification detection.

### PCSF — Provider Capacity State Format

A canonical taxonomy and schema for "what is the current state of this provider," subsuming the messy provider-specific state vocabulary (OpenAI `insufficient_quota`, Anthropic banner text, Gemini HTTP 429, Codex CLI labels, ChatGPT-Web DOM scraping). Substrate already exists in `docs/suzie-provider-capacity-limits.md`. PCSF feeds CCF (provider-capability claims depend on provider state) and is the easiest of the five to publish for ecosystem adoption.

The five together form the operational substrate for the framework. **Crucially: none of them, alone, change the world.** The primitive framework is the joining layer that makes the specs cohere as a unified theory rather than as disconnected standards.

---

## 10. Limitations and open questions

This framework is enforcement substrate, not a complete compliance solution. Specifically out of scope:

- **Model alignment and content-policy harms.** The framework gates *what action* the agent takes; it does not gate *what content* a model generates. Prompt-injection-class harms, alignment failures, and content-policy harms require separate substrate.
- **Novel statutes and jurisdictional conflict resolution.** When two regulations conflict (e.g., GDPR right to erasure vs. SEC retention), the framework can detect the conflict but cannot resolve it. Resolution remains a human legal judgment.
- **Legal advice.** A regulator's interpretation of how a primitive maps to a specific obligation is the regulator's prerogative. The framework provides substrate for compliance posture; it does not substitute for counsel.
- **Audit certification.** Implementing the primitives correctly is necessary but not sufficient for SOC 2, HIPAA OCR review, FedRAMP ATO, or any other certification. Auditors examine evidence, not architecture.
- **Adversarial robustness of the primitives themselves.** A signed CCF claim is only as trustworthy as the runner's signing key; a NAP denylist is only as trustworthy as the list maintainer; AAPF retention is only as trustworthy as the storage system. The framework assumes a threat model that itself requires separate analysis.

Open questions for v0.2:

- Can the framework express compliance with regulations not yet decomposed (Brazilian LGPD, Chinese PIPL, Indian DPDP Act 2023)? Initial inspection suggests yes; formal verification is pending.
- Does the framework apply to non-AI agent systems (RPA, deterministic workflow engines)? Probably yes for primitives 1-8; the specifically-AI primitives (4 capability claims, 10 supply chain) become weaker in non-AI contexts but remain meaningful.
- What is the right canonical signing infrastructure for CCF and AAPF? Sigstore, x.509, DID/VC, or a new format? This decision affects ecosystem adoption.
- How should the framework relate to ISO/IEC 42001 (AI management system standard) and NIST AI RMF? The relationship is complementary, but a formal mapping is needed.

---

## 11. Related work

**NIST AI RMF (NIST AI 100-1).** Voluntary risk management framework for AI. Operates at the program level (govern, map, measure, manage). The primitive stack operates one layer below — at the runtime substrate level. Complementary, not competing.

**ISO/IEC 42001:2023.** AI management system standard. Audit framework for an organization's AI practices. Complements the primitive stack the way ISO/IEC 27001 complements technical security controls.

**OPA / Rego (Open Policy Agent).** Policy-as-code engine. Operates in Mode A only and is regulation-agnostic. The primitive stack could be expressed as a Rego policy library; this would be a useful integration project.

**OpenAI / Anthropic enterprise compliance posture.** Per-vendor, per-regulation point solutions (HIPAA-eligible API, FedRAMP authorization, BAA availability). The primitive stack treats these as inputs to CCF claims rather than as the compliance answer.

**W3C Verifiable Credentials.** A credential format standard. CCF could be expressed as a VC profile; AAPF claims could be VCs about agent actions. Integration is possible but unstudied.

**OAuth 2.0 + OIDC.** Authorization protocol. Operates in Mode A only, with no awareness of execution modes B or C. NAP could be expressed as an OAuth-adjacent denial layer.

**MCP (Model Context Protocol).** Tool exposure protocol. The primitive stack layers on top of MCP — MCP describes which tools exist; CCF describes whether those tools are *currently authorized* for the requesting actor.

**Sigstore.** Software supply chain signing. Useful infrastructure for primitive 10 (supply chain attestation) and for CCF/AAPF signing.

**Cryptographic provenance research (e.g., C2PA).** Content provenance for media. The primitive stack and AAPF address a different problem (action provenance for agents) but the cryptographic substrate is similar.

The novel claim of this paper is not any individual primitive — most of them have been observed before in compliance literature. The novel claim is that **ten primitives × three execution modes is the minimal sufficient set for AI agent compliance, that the agent system is the right enforcement layer for them, and that this set generalizes across at least US federal, US payments, US education (FERPA / COPPA), US healthcare (HIPAA), EU privacy and AI (GDPR / EU AI Act), and accessibility regimes**.

---

## 12. References

Statutes and regulations are cited by official name and citation. Vendor compliance pages and marketing materials are not cited as authoritative.

**United States — federal**
- Privacy Act of 1974, 5 U.S.C. §552a
- Family Educational Rights and Privacy Act (FERPA), 20 U.S.C. §1232g; 34 CFR Part 99
- Children's Online Privacy Protection Act (COPPA), 15 U.S.C. §§6501-6506; 16 CFR Part 312
- Health Insurance Portability and Accountability Act (HIPAA) Privacy Rule, 45 CFR Parts 160 and 164
- Federal Information Security Modernization Act (FISMA), 44 U.S.C. §3551 et seq.
- NIST SP 800-53 Rev. 5; NIST SP 800-171 Rev. 3; NIST SP 800-218 (SSDF)
- Executive Order 14028, "Improving the Nation's Cybersecurity" (2021)
- Executive Order 14117, "Preventing Access to Americans' Bulk Sensitive Personal Data" (2024); 28 CFR Part 202
- OMB M-22-09 (Zero Trust); OMB M-24-04; OMB M-24-10 (AI use)
- Section 889 of the John S. McCain National Defense Authorization Act for FY 2019
- 26 U.S.C. §6103; IRS Publication 1075
- FBI CJIS Security Policy

**United States — payments**
- Electronic Fund Transfer Act, 15 U.S.C. §§1693-1693r; 12 CFR Part 1005 (Reg E)
- Truth in Lending Act, 15 U.S.C. §§1601-1667f; 12 CFR Part 1026 (Reg Z)
- Gramm-Leach-Bliley Act, 15 U.S.C. §§6801-6809; 12 CFR Part 1016 (Reg P)
- Bank Secrecy Act, 31 U.S.C. §§5311-5336; 31 CFR Chapter X
- Office of Foreign Assets Control sanctions programs, 31 CFR Chapter V
- Travel Rule, 31 CFR §1010.410
- Dodd-Frank Wall Street Reform and Consumer Protection Act, Pub. L. 111-203
- Equal Credit Opportunity Act, 15 U.S.C. §§1691-1691f; 12 CFR Part 1002 (Reg B)
- FINRA Rule 2165 (Financial Exploitation of Specified Adults)
- Senior Safe Act, 12 U.S.C. §3423
- Consumer Financial Protection Bureau Larger Participant Rule for Digital Wallets (2024)
- NACHA Operating Rules (annual)

**European Union**
- Regulation (EU) 2016/679 (GDPR)
- Regulation (EU) 2024/1689 (EU AI Act)
- Directive (EU) 2015/2366 (PSD2)
- Directive (EU) 2022/2555 (NIS2)

**International**
- ISO/IEC 42001:2023; ISO/IEC 23894:2023; ISO/IEC 27001:2022
- FATF Recommendations (40+9), particularly Recommendation 16 (Travel Rule)

**Standards bodies**
- NIST AI Risk Management Framework (NIST AI 100-1)
- NIST Cybersecurity Framework 2.0
- W3C Verifiable Credentials Data Model 2.0

---

## Acknowledgements

This framework emerged from operating an AI agent orchestration system that was forced to confront capability honesty as a runtime requirement, then required to reason about regulatory constraints across multiple deployment scenarios. The decomposition is unoriginal in compliance circles — what is original is the formalization at the agent-system runtime layer.
