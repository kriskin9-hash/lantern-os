# Capability Honesty Model

Status: architecture requirement
Audience: product, agents, operators, reviewers

## Product requirement

Suzie must not assume that every installed model, agent slot, tool, or extension can perform every task.

At runtime, Suzie should discover and track what is actually serviceable, then adapt task strategy accordingly. If a required capability is missing, degraded, quota-limited, disabled, policy-blocked, or unverified, Suzie must say so and either downgrade the plan or decline the task.

The product promise is:

> Suzie is useful because it is honest about what it can and cannot safely do right now.

## Capability sources

Effective capability should be computed from multiple sources:

| Source | Examples | Role |
|---|---|---|
| Static profile | `k12-school`, `grandma-mode`, `developer-agent-ops` | baseline policy |
| Configured slots | Claude, Codex, Gemini, GPT Web, local model lane | candidate capability |
| Live discovery | MCP tool list, shell access, browser access, file edit support | runtime truth |
| Provider state | quota, auth, billing, rate limit, model availability | runtime truth |
| Hardware profile | CPU, RAM, GPU, disk, Windows version, offline mode | runtime constraint |
| Policy gates | local-only mode, approval requirements, data boundaries | hard constraint |
| Recent evidence | preflight output, tests, service health, dashboard state | runtime truth |

Static config is never enough. Live discovery and recent evidence override advertised capability.

## Capability states

Every capability should resolve to one of these states:

| State | Meaning | Product behavior |
|---|---|---|
| `available` | configured, verified, and serviceable | use normally |
| `degraded` | usable with lower quality, quota, latency, missing tools, or constraints | warn and adjust strategy |
| `blocked` | present but policy forbids use | decline or request authorized policy change |
| `unverified` | may exist but has not been checked recently | run preflight or avoid high-risk use |
| `unavailable` | missing or failed preflight | do not plan around it |
| `unsafe` | would create an unacceptable mutation, privacy, or evidence risk | decline and explain |

## Strategy adaptation examples

| Situation | Strategy change |
|---|---|
| Gemini has read/search tools but no edit or shell tools. | Assign research/review only; decline implementation tasks for that slot. |
| Claude can edit files but quota is exhausted. | Queue work, route to a verified fallback, or ask the user to wait. |
| Cloud models are disabled in a K-12 profile. | Use local templates/local models; do not upload protected data. |
| Old school tower has low RAM and no GPU. | Prefer templates, retrieval, and small local models; avoid heavy inference. |
| MCP tools are advertised but route contracts fail. | Mark MCP actions unavailable and block dispatch. |
| Evidence capture is unavailable. | Do not claim completion for work requiring audit evidence. |

## Honest decline pattern

Suzie should use direct language:

```text
I cannot safely do that right now because [capability] is [state].
I can still help by [safe alternative].
To enable the original task, [specific remediation].
```

Examples:

```text
I cannot edit files with the selected Gemini slot because this slot only exposes read/search tools. I can review the code and propose a patch, or route the task to a slot with file-edit capability.
```

```text
I cannot send this message automatically because the active profile requires user approval before outbound communication. I can draft it for review.
```

```text
I cannot use a cloud model for this document because the active profile is local-only. I can use local templates or ask an administrator to change the policy.
```

## User-facing capability summary

Simple profiles should expose a plain-language summary:

```text
Current mode: K-12 local-first
Cloud AI: off by policy
Local model: available, low-capacity
Document summaries: available
Outbound messages: draft-only
Evidence log: available
```

Operator/developer mode can expose the full machine-readable map.

## Agent-slot behavior contract

Agent slots must:

1. declare intended capability;
2. prove live capability through preflight or tool discovery;
3. update status when capability changes;
4. decline tasks outside effective capability;
5. choose a safer strategy when degraded;
6. record evidence for routing and denial decisions;
7. avoid claiming completion when required tools, tests, or evidence were unavailable.

## Implementation outline

Initial implementation should add:

1. `schemas/capability-map.schema.json` for machine-readable capability state.
2. `status/capability-map.example.json` for example output.
3. A preflight collector that builds effective capability from config, profile, tools, provider status, hardware, policy, and recent tests.
4. A strategy resolver that maps work requirements to available/degraded/blocked capabilities.
5. A decline/degradation message generator.
6. CI tests that prevent agents from claiming unsupported slot capabilities.

## Non-goals

- Do not hardcode one best model.
- Do not assume cloud access.
- Do not assume agents can edit files unless tool discovery proves it.
- Do not hide degradation from the user.
- Do not claim completion when evidence capture or validation was unavailable.
- Do not silently route sensitive data to cloud models.

## CTO product implication

Profiles, modules, and extensions are valuable only if they are backed by capability honesty.

The core product must answer:

```text
Given this user, hardware, profile, tools, model access, and policy, what can Suzie safely do right now?
```

If the answer is not enough, Suzie should say so clearly and offer the best safe alternative.
