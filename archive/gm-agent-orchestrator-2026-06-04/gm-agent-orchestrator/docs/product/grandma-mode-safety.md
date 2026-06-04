# Grandma Mode Safety

Status: required guardrail  
Related issue: #308  
Priority: P0

## Scope

Grandma mode is a high-protection profile for users at elevated risk of social
engineering and financial coercion.

This profile is denylist-first. Voice or text approval alone cannot override the
denylist.

## Hard Denylist (Cannot Be Unlocked by Prompt Approval)

1. Outbound payments to recipients not on a pre-approved allowlist.
2. Password reset/account recovery for financial, health, or government accounts.
3. Responding to urgent money/legal/family-crisis solicitation patterns.
4. Sending sensitive identity data (SSN, DOB, full address, account numbers).
5. Installing software/browser extensions.
6. Changing recovery email/phone/2FA/contact information on protected accounts.

## Trusted Contact Escalation

When a denylisted action is requested:

1. Refuse the action.
2. Record a safety event in audit logs.
3. Notify configured trusted contact workflow.
4. Provide non-destructive alternatives (draft-only, information-only).

## Approval Model

- Standard actions: explicit approval may allow execution.
- Denylisted actions: explicit approval is ignored; escalation path only.

## Logging Requirements

For every denylisted request:

- profile id
- action category
- refusal reason
- trusted-contact escalation state
- timestamp and request id

Do not log secrets or full credential content.

## Contract Requirement

Representative denylisted actions must be refused in grandma mode by contract
tests.

See: `tests/Test-GrandmaModeSafety.ps1`.
