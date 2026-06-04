# K-12 Compliance Posture

Status: explicit scope statement  
Related issue: #307  
Current posture: pre-certification

## Scope statement

This system is not represented as FERPA-certified, COPPA-certified, or audited
for district-wide production deployment at this time.

It can support compliance-oriented controls, but those controls are not the same
as legal certification or institutional approval.

## FERPA/COPPA posture

### FERPA

- The platform can enforce data classification, access controls, and audit logs.
- Schools still require local legal/compliance review, contracts, and policy
  mapping before student-record processing at scale.
- District deployment requires documented school-official workflow and records
  governance.

### COPPA

- COPPA obligations depend on whether the service is school-authorized or direct
  to children under 13.
- For direct-to-child use, verifiable parental consent requirements apply.
- Current default posture is school/caregiver-supervised use with strict profile
  controls.

## What schools would still need

1. DPA / legal agreements.
2. District-approved deployment architecture.
3. Documented incident response workflow.
4. Data retention and deletion policy sign-off.
5. Role-based access control mapping by school/tenant.

## Product positioning rule

Until a formal compliance program is completed, position this as:

- small classroom / homeschool / caregiver-support tooling,
- not as a fully certified district platform.

## Primary references

- FERPA overview: https://studentprivacy.ed.gov
- FERPA regulations: 34 CFR Part 99
- COPPA statute/regulations: 15 U.S.C. 6501-6506 and 16 CFR Part 312
