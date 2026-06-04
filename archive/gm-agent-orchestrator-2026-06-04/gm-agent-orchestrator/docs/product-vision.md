# Product Vision: General Work Orchestration

Status: outline  
Audience: operators, agents, reviewers, and future implementers

---

## One-line product definition

Suzie is a local-first AI work orchestration control plane for safely coordinating human-supervised work across agents, tools, repositories, evidence, and validation gates.

Suzie is not a sprint-management system. A sprint can be one workflow template, but the product core must remain workflow-agnostic.

---

## Product goal

Make agent-assisted work reliable enough that an operator can answer four questions at any time:

1. What work is allowed right now?
2. Which actor or agent owns each work item?
3. What evidence proves the state is true?
4. What validation must pass before the work can be called done?

---

## Core primitives

| Primitive | Purpose |
| --- | --- |
| `WorkItem` | A unit of work with goal, scope, owner, status, and validation requirements. |
| `CurrentObjective` | The active operating objective, such as stabilization, research, release, cleanup, or demo. |
| `Workflow` | A named sequence or policy bundle that shapes how work moves from requested to complete. |
| `Policy` | Allowed and forbidden actions, tool permissions, file scopes, and escalation rules. |
| `Evidence` | Durable proof from logs, PRs, status files, tests, screenshots, or commands. |
| `Validation` | Deterministic checks or review gates required before completion. |
| `AgentSlot` | A local or remote agent lane with capabilities, constraints, and health state. |
| `ToolBoundary` | A typed, inspectable action surface such as MCP tools or safe PowerShell commands. |
| `Handoff` | A structured transfer request preserving current state, risks, and next action. |
| `StatusSnapshot` | A compact machine-readable summary of current objective, risks, and blockers. |

---

## Product boundaries

The core product should not assume Scrum, sprints, story points, or any one planning method.

The core product can support these as optional workflow templates:

- stabilization sprint;
- release gate;
- research ingestion;
- code-review queue;
- incident response;
- repo cleanup;
- portfolio demo;
- GameMaker build lane.

---

## Agent-facing design principle

Agents should not infer operating rules from chat history. They should read stable instructions, a current objective/status file, and enforceable policy checks.

```text
AGENTS.md / model guides       -> stable behavior rules
current objective/status files -> current operating context
policy files                   -> allowed and forbidden actions
MCP/tool contracts             -> actual callable surface
CI/tests/hooks                 -> enforcement and validation
GitHub issues/PRs              -> human-auditable planning and change history
```

---

## Near-term implementation outline

Initial implementation should stay lightweight and avoid runtime lock-in:

1. Document the workflow-agnostic model.
2. Add a machine-readable current-objective schema.
3. Add an RC3 Convergence example as data, not as product behavior.
4. Add a deterministic contract test for the schema and example.
5. Later, wire hooks to generic policy violations, not sprint-specific wording.

---

## Non-goals for this outline

- No new agent lanes.
- No provider expansion.
- No queue movement.
- No agent dispatch.
- No hardcoded sprint runtime.
- No hook escalation from advisory to blocking until false positives are understood.

---

## Honest portfolio framing

Use language like:

```text
Windows-first local AI work orchestration prototype with MCP-style tool boundaries, GitHub issue/PR audit trails, deterministic PowerShell validation, evidence tracking, and configurable policy gates for human-supervised agents.
```

Do not claim production-grade reliability, compliance certification, clean-machine deployability, or autonomous completion without current evidence.
