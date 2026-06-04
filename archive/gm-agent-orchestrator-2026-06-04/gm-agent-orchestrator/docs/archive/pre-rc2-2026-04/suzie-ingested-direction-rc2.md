# Suzie Ingested Direction (RC2)

Date: 2026-05-02  
Source brief: `C:\Users\alexp\Downloads\suzie_research_ingestion_brief.md`  
Status: authoritative for RC2 planning and queue shaping

## Accepted Doctrine

- Suzie is a local-first orchestration work engine.
- The control plane is queue-backed, worktree-aware, and audit-driven.
- MCP is the primary GPT orchestration surface.
- Risky mutations require policy gate, dry-run evidence, and explicit approval.
- Every work unit must end in an explicit terminal state with evidence.

## Product Direction

- One operator dashboard route: `/dashboard`.
- Panel-first growth model; no tabs and no multi-page dashboard expansion for now.
- Queue lifecycle safety and status clarity are higher priority than agent expansion.
- External agent frameworks are adapters behind Suzie contracts, not control-plane replacements.

## Explicit Non-Goals (Current RC Window)

- No framework-core migration (no OpenAI Agents SDK rewrite, no LangGraph rewrite).
- No dashboard route expansion (`/dashboard/public`, `/dashboard/project`, `/dashboard/operator`, `/dashboard/stream`).
- No destructive Git controls in operator flow (`reset`, `clean`, `force push`, `stage all`).
- No bypass of queue and dry-run policy for risky actions.

## RC2 Validation Objective

Prove RC1 reliability by advancing to RC2 through controlled, auditable work units:

1. codify message ingress and routing contract,
2. enforce role-based dispatch gates,
3. run one queue lifecycle smoke with no stale active task,
4. align dashboard next-action truth with queue and slot reality,
5. capture an end-of-cycle RC2 validation packet with blockers and readiness verdict.

## Routing and Task Authoring Requirement

All new RC2 queue tasks must include:

- `role_owner`
- `fallback_owner`
- `risk_class`
- `budget_class`
- `terminal_rule`

This document is the baseline reference for task routing and acceptance in the current cycle.
