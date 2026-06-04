# Regulatory Primitive Stack — Glossary

Companion to `docs/research/regulatory-primitive-stack.md` v0.1.

This glossary is a standalone reference for implementers who need the framework definitions without the worked examples or motivation. Cite as `RPS-Glossary v0.1`.

## Primitives

Numbering matches the framework note. Each primitive is the minimal substrate required by at least one of the regulations analyzed in v0.1.

| ID | Name | One-line definition |
|---|---|---|
| P1 | Data classification | Every datum carries a class label; labels propagate through transformations. |
| P2 | Authority and consent gates | Authorization for an action is resolved at action time against an independently-verifiable record. |
| P3 | Provenance and audit | Every action produces a reproducible record tying the artifact to the actor. |
| P4 | Capability constraints | The agent must prove, at action time, that it has the capability it claims. |
| P5 | Boundary enforcement | Data and capability flows respect explicit deployment, jurisdictional, and contractual boundaries. |
| P6 | Subject rights | Data subjects' rights (access, correction, erasure, portability, opt-out, objection) are served within statutory windows. |
| P7 | Incident response | Detection, containment, evidence preservation, and notification follow defined procedures with statutory timelines. |
| P8 | Vendor chain and flow-down | Obligations propagate through the supply chain: BAAs, DPAs, FedRAMP boundaries, sub-processors. |
| P9 | Threshold-based reporting | When a defined pattern or threshold is met, a report is generated to a regulator, trusted contact, or audit log. |
| P10 | Supply chain attestation | The provenance of the agent's own software, models, tools, and connections is attested. |

## Execution modes

| ID | Name | Definition | Examples |
|---|---|---|---|
| MA | Synchronous gating | The action is allowed, denied, or routed for approval at the moment it is requested. | OFAC SDN screen before wire; PHI to non-BAA blocked; CUI to unauthorized capability blocked. |
| MB | Asynchronous reporting | The action is allowed (or already happened); a downstream obligation is triggered. | FinCEN SAR within 30 days; OMB M-24-10 inventory entry; state APS report; GDPR Art. 33 breach notification. |
| MC | Temporal contract | The action starts a clock; a defined outcome must occur within a statutory window. | Reg E 10-day provisional credit; FERPA 45-day records access; HIPAA 60-day individual breach notification; GDPR 30-day subject access response. |

A primitive may operate in any non-empty subset of the three modes for a given regulation.

## Modifiers

Modifiers describe how primitives behave under realistic conditions. They are cross-cutting; they do not introduce new compliance requirements.

| ID | Name | Definition |
|---|---|---|
| M1 | Dynamic externally-maintained predicate | An authorization predicate references a list maintained by an external authority and updated frequently (OFAC SDN, BIS Entity List, Section 889 covered list, FedRAMP Marketplace, CMS exclusion list, FATF jurisdiction list). The runtime must refresh, prove freshness, and degrade safely when the source is unreachable. |
| M2 | Temporal obligation as first-class state | Mode C requires that deadlines be tracked as first-class state (start, deadline, completion, overdue), not implicit follow-ups. The provenance ledger becomes a state machine with wall-clock transitions. |

## Composition rules

A regulation is expressed in the framework as a tuple:

```
RegulationBinding = {
  regulation_id: string,             // e.g., "us.fincen.bsa.sar"
  primitives: set<PrimitiveID>,       // {P3, P9}
  modes: map<PrimitiveID, set<Mode>>, // {P3: {MA, MB}, P9: {MB, MC}}
  modifiers: set<ModifierID>,         // {M1, M2}
  predicate_sources: map,             // {OFAC_SDN: "https://..."}
  temporal_obligations: list,         // [{start: "transaction", deadline: "30d", action: "file_SAR"}]
  source_citation: string,            // "31 U.S.C. §5318(g); 31 CFR §1020.320"
  last_verified_at: ISO8601 date
}
```

A **policy bundle** (e.g., "k12-school," "hipaa-covered-entity," "federal-benefits-navigator") is a composition of regulation bindings plus a runtime-resolution strategy when bindings conflict.

## Derived specs

The framework does not, by itself, dictate concrete schemas. Five spec proposals derive from it:

| Spec | Operationalizes | Status |
|---|---|---|
| CCF (Capability Claim Format) | P4 primarily; consumed by P5, P8, P10 | proposed |
| AAPF (Agent Action Provenance Format) | P3 primarily; consumed by P6, P7, P9 | proposed |
| NAP (Negative Authority Profiles) | P2 (denial form); composes M1 | proposed |
| DCF (Data Classification Format) | P1; gates CCF | proposed |
| PCSF (Provider Capacity State Format) | feeds P4 / CCF; standalone useful | proposed; substrate exists in `docs/suzie-provider-capacity-limits.md` |

The framework note (§9) discusses publication ordering. PCSF is the recommended first spec to ship because it has the lowest political resistance and the most existing substrate.

## Terms used elsewhere in the framework

| Term | Definition |
|---|---|
| Capability honesty | The doctrine that a system must not act on a capability it cannot prove it has at action time. Established in `docs/product/capability-honesty-model.md`. |
| Tenant | A boundary of authorization, audit, and data sharing (household, business, classroom, school, district, organization). |
| Profile | A user-facing mode that composes regulatory and product policy (e.g., k12-school, grandma, developer-agent-ops, hipaa-covered-entity). |
| Bundle | A composition of regulation bindings plus a conflict-resolution strategy, applied to a profile or tenant. |
| Predicate freshness proof | Cryptographic or attested evidence that an externally-maintained list was refreshed within a stated window. |
| Mode-A/B/C failure | A primitive failure in the named execution mode. Mode A failures are visible at action time; Mode B and C failures often only surface during regulator inspection. |

## Versioning

This glossary is versioned with the framework note. Breaking changes to primitive numbering, mode definitions, or modifier semantics increment the major version. Additions are minor versions. Editorial changes are unversioned.

Current: **RPS v0.1** (draft).
