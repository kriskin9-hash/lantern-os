# RC2 Message Ingress Contract

Status: active RC2 contract  
Owner surface: GPT/MCP control plane  
Route scope: `/dashboard` operator intake and MCP message ingestion

## Goal

Turn each operator message into an auditable orchestration decision with dry-run-first mutation safety.

## Ingress Schema

```json
{
  "messageId": "string",
  "createdAt": "ISO-8601",
  "source": "dashboard|mcp|chat",
  "actor": "alex|system|agent:<slot>",
  "body": "string",
  "classification": {
    "intent": "status_question|task_request|approval|rejection|hold_request|agent_control_request|gitops_request|validation_result|fallback_handoff|unsafe_command|unknown",
    "requiresMutation": false,
    "requiresDryRun": true,
    "riskClass": "low|medium|high|blocked",
    "confidence": 0.0
  },
  "result": {
    "state": "received|classified|dry_run_ready|queued|blocked|refused|completed",
    "summary": "string",
    "nextAction": "string",
    "auditPath": "string"
  }
}
```

## Classification Rules

- `status_question`: read-only status or evidence lookup.
- `task_request`: request to create/shape/move work.
- `approval` / `rejection` / `hold_request`: policy decision response.
- `agent_control_request`: start/rerun/lock/unlock slot operations.
- `gitops_request`: Git workflow mutation path.
- `validation_result`: test/verification result intake.
- `fallback_handoff`: handoff path when a primary lane is blocked.
- `unsafe_command`: destructive or policy-violating request.
- `unknown`: ambiguous intent requiring clarification or hold.

## Inline vs Queue Execution

Inline-allowed (read-only):

- status questions,
- capability summaries,
- queue and slot visibility reads,
- audit trail queries.

Queue-required:

- any mutation-capable task request,
- agent start/rerun action requests,
- gitops requests,
- multi-step or uncertain work units.

## Dry-Run Gate Contract

For mutation-capable intents, system must return a dry-run card before any mutation:

- understood intent,
- proposed action,
- affected task/paths,
- risk level,
- policy decision (`allowed|blocked|needs_approval|refused`),
- next action,
- audit path.

No direct raw prompt mutation is allowed.

## Audit Requirements

Each ingress stage emits an audit event:

1. `message_received`
2. `message_classified`
3. `dry_run_prepared` (for mutation intents)
4. `action_approved|action_rejected|action_held`
5. `mutation_executed|mutation_refused|mutation_blocked`

Each event must include:

- timestamp,
- actor,
- surface,
- messageId,
- policy decision,
- summary,
- details path.
