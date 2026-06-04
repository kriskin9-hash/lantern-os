# Documentation Hub

This is the canonical map for humans and agents working in `gm-agent-orchestrator`.

Start here instead of scanning the repo.

## Single agent path

All agents should follow one path through the docs:

```text
README.md
  -> docs/README.md
    -> docs/agent-start-here.md
      -> model guide
        -> assigned task
          -> relevant sections of docs/agent-contract.md
```

Do not bounce between the hub, start page, and model guide. Use the hub as the map, then continue forward.

## Fast paths

| Reader | First file after this hub | Purpose |
| --- | --- | --- |
| GPT / ChatGPT | [`docs/agent-start-here.md`](agent-start-here.md) | Routes to the GPT guide, then to connector-safe planning, GitHub work, reporting, and false-claim avoidance. |
| Claude | [`docs/agent-start-here.md`](agent-start-here.md) | Routes to the Claude guide, then to local implementation flow, PowerShell-safe execution, evidence, and handoff. |
| Codex | [`docs/agent-start-here.md`](agent-start-here.md) | Routes to the Codex guide, then to code-change review, patch discipline, tests, and PR feedback. |
| Any worker agent | [`docs/agent-start-here.md`](agent-start-here.md) | Minimal required read order before claiming or changing work. |
| Human/operator | [`docs/operator-runbook.md`](operator-runbook.md) | Safe repo, queue, MCP, dashboard, and recovery operations. |
| Security/policy reviewers | [`docs/cto-successor-handoff.md`](cto-successor-handoff.md) | Current threat model, grandma safety, key lifecycle, and K-12 posture boundaries. |
| Career/profile agents | [`docs/operator-profile.md`](operator-profile.md) | Redacted capability profile for resumes, role fit, portfolio planning, and advocacy without private contact data. |
| Dispatch/capacity planners | [`docs/agent-model-capabilities.md`](agent-model-capabilities.md) | Deterministic model routing, tool availability, and task compatibility. |
| Control-plane reviewers | [`docs/dispatch-determinism-map.md`](dispatch-determinism-map.md) | Color-coded dispatch determinism map for identifying green/yellow/red/blue control-plane safety zones. |
| Standards / compliance / research | [`docs/research/regulatory-primitive-stack.md`](research/regulatory-primitive-stack.md) | Research framework: 10 primitives × 3 execution modes for AI agent regulatory compliance. Federal and payments worked examples. |

## Canonical docs

1. [`README.md`](../README.md) - repo purpose, boundaries, and setup entry point.
2. [`AGENTS.md`](../AGENTS.md) - root-level instructions for all agents in this repo.
3. [`docs/agent-start-here.md`](agent-start-here.md) - single canonical agent entry point.
4. [`docs/model-guides/gpt.md`](model-guides/gpt.md) - GPT / ChatGPT connector-safe behavior.
5. [`docs/model-guides/claude.md`](model-guides/claude.md) - Claude local implementation behavior.
6. [`docs/model-guides/codex.md`](model-guides/codex.md) - Codex review, patch, and test behavior.
7. [`docs/agent-contract.md`](agent-contract.md) - complete execution, evidence, validation, and handoff contract.
8. [`docs/operator-runbook.md`](operator-runbook.md) - human/operator control flow.
9. [`docs/meta-orchestrator.md`](meta-orchestrator.md) - meta-orchestrator action-item pattern.
10. [`docs/alternative-to-powershell-prompts.md`](alternative-to-powershell-prompts.md) - strategy for reducing shell-prompt friction.
11. [`docs/operator-profile.md`](operator-profile.md) - redacted operator capability profile and evidence boundaries for career/profile work.
12. [`docs/agent-model-capabilities.md`](agent-model-capabilities.md) - deterministic model routing, tool surfaces, restrictions, and task compatibility.
13. [`docs/dispatch-determinism-map.md`](dispatch-determinism-map.md) - color-coded dispatch determinism map and hardening gaps.
14. [`docs/research/regulatory-primitive-stack.md`](research/regulatory-primitive-stack.md) - research framework note: 10 primitives × 3 execution modes for AI agent compliance.
15. [`docs/research/regulatory-primitive-stack-glossary.md`](research/regulatory-primitive-stack-glossary.md) - standalone glossary for the framework primitives, modes, and modifiers.
16. [`docs/research/regulation-to-primitive-map.csv`](research/regulation-to-primitive-map.csv) - machine-readable matrix of regulations to primitives.
17. [`docs/cto-successor-handoff.md`](cto-successor-handoff.md) - active map to current security and product safety guardrails.
18. [`docs/security/threat-model.md`](security/threat-model.md) - prompt-injection, MCP impersonation, supply-chain, and tenant-lateral movement threat controls.
19. [`docs/product/grandma-mode-safety.md`](product/grandma-mode-safety.md) - denylist-first elder-safety profile contract.
20. [`docs/product/user-identity-and-api-keys.md`](product/user-identity-and-api-keys.md) - per-user key lifecycle, revocation closed loop, and spend controls.
21. [`docs/product/k12-compliance-posture.md`](product/k12-compliance-posture.md) - explicit FERPA/COPPA posture and deployment boundaries.

## Agent rule of thumb

Read less, but read the right things:

1. Read `docs/agent-start-here.md`.
2. Read only your model guide.
3. Read the assigned task.
4. Read only the relevant section of `docs/agent-contract.md`.
5. Inspect the smallest set of task and source files needed for the assigned work.

Do not start agents, move queue files, mark work done, or claim dispatch success unless observable evidence proves the state transition.

## Documentation ownership

- Root docs explain orientation and entry points.
- `docs/agent-start-here.md` owns agent read order.
- `docs/model-guides/` explains model-specific behavior.
- `docs/agent-contract.md` owns the detailed worker contract.
- `docs/operator-runbook.md` owns human/operator control and recovery steps.
- `docs/operator-profile.md` owns redacted career/profile capability positioning and evidence boundaries.
- `docs/agent-model-capabilities.md` owns deterministic agent model routing and observed tool restrictions.
- `docs/dispatch-determinism-map.md` owns the color-coded dispatch determinism map and related safety hardening gaps.
- Topic docs stay in `docs/` until they are promoted, merged, or archived as decision records.
