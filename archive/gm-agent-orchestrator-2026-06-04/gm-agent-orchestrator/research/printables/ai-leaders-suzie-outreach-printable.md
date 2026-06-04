# AI Leaders and Suzie Outreach Shortlist

Status: printable draft  
Source: issue #274 and PR #282  
Freshness: watch  
Verification: contact paths, affiliations, and current links must be verified before outreach

## Purpose

Use this page as a print-ready networking guide for Suzie.

Suzie is a local-first AI orchestration workspace for human-supervised agent work. It uses GitHub issues and pull requests, worktrees, MCP-style tool boundaries, research/context ingestion, and validation logs as the control plane.

## Positioning line

> I am building Suzie, a local-first AI orchestration workspace that treats GitHub issues/PRs, worktrees, MCP-style tool boundaries, and validation logs as the control plane for human-supervised agent work.

## Tier 1 AI leaders

| Priority | Person / orbit | Why they matter for Suzie | Best ask |
| ---: | --- | --- | --- |
| 1 | Andrew Ng / DeepLearning.AI | Practical ML, MLOps, evaluation, RAG, AI education, productization. | Which courses best map to local agent orchestration, evals, RAG, and AI productization? |
| 2 | Andrej Karpathy | Video-first grounding for LLM fundamentals, nanoGPT, makemore, software 2.0. | What project proof separates a real LLM systems project from a toy demo? |
| 3 | Nicholas Carlini | Adversarial ML, prompt injection, privacy, model extraction, LLM security. | What are the highest-risk failure modes for MCP tools, sandboxes, and source ingestion? |
| 4 | Alex Tamkin | Model behavior, evaluation, agents, societal impact, governance. | What evidence would make Suzie legible to researchers reviewing reliability and limitations? |
| 5 | Dario Amodei / Anthropic orbit | Agent safety, Claude Code, context engineering, sandboxing, responsible deployment. | What operational evidence makes autonomous coding/research agents safe enough for real work? |
| 6 | Yann LeCun / FAIR orbit | World models, JEPA, planning, skepticism about LLM-only autonomy. | Where do LLM agents fail, and what should Suzie track to avoid overclaiming autonomy? |

## Practical networking targets

| Priority | Target type | Why it fits Suzie | Suggested ask |
| ---: | --- | --- | --- |
| 1 | MCP server/framework maintainers | Direct match to tool boundaries, schema validation, endpoint trust. | What are the most common MCP schema/tool-boundary mistakes? |
| 2 | LangChain / LangGraph builders | Agent graphs, tracing, orchestration, tool calls, evals. | What evidence would you expect before trusting a multi-agent workflow beyond a demo? |
| 3 | LlamaIndex / RAG builders | Source registries, claim ledgers, retrieval, ingestion quality. | How should Suzie track source freshness, claims, and retrieval quality without overbuilding? |
| 4 | LLM evals practitioners | Targeted evals, terminal states, regression checks, operator-readable evidence. | What is the smallest useful eval harness for a local agent orchestrator? |
| 5 | AI security / prompt-injection researchers | Tool misuse, prompt injection, secret leakage, remote endpoint trust. | How should I threat-model an MCP-connected local agent workspace? |
| 6 | Developer-education creators | Diagrams, demos, runbooks, printable checklists, and examples. | What artifact would make Suzie understandable to another builder in ten minutes? |
| 7 | Enterprise workflow automation leaders | Governance, integrations, AI ops, HCM/workflow automation. | Where do agent workflows create measurable value inside enterprise systems? |
| 8 | Coding-agent maintainers and power users | PRs, worktrees, CI, task queues, capacity handling. | What failure evidence should a coding-agent orchestrator capture before opening a PR? |

## Candidate named additions to verify

| Candidate | Why relevant | First ask |
| --- | --- | --- |
| Harrison Chase / LangChain orbit | Agent frameworks, LangGraph, tracing, tool use. | What patterns make agent orchestration observable and debuggable? |
| Jerry Liu / LlamaIndex orbit | RAG, indexing, data agents, knowledge systems. | How should a small system track sources and claims without overbuilding? |
| Simon Willison | Practical LLM tooling, prompt injection awareness, local-first experimentation. | What evidence should a local agent tool capture so skeptical engineers trust what happened? |
| Hamel Husain | Practical evals and LLM product-quality discipline. | What are the first three evals you would add to a small agent orchestrator? |
| Shreya Shankar | AI engineering, evals, data quality. | How should Suzie separate model failure, retrieval failure, tool failure, and policy failure? |
| Chip Huyen | AI engineering, production ML/LLM systems, career/project framing. | What portfolio artifact best proves AI engineering judgment? |
| Jason Liu | Structured extraction and schema-first LLM apps. | How should Suzie validate structured outputs before repo mutation? |
| swyx / Latent Space orbit | AI engineering community and builder positioning. | How should Suzie be explained so it resonates with AI engineers? |

## Outreach message

```text
Hi <name> — I am building Suzie, a local-first AI orchestration workspace for human-supervised agent work. It uses GitHub issues/PRs, worktrees, MCP-style tool boundaries, and validation logs as the control plane.

I am trying to make it reliable rather than flashy. The next decision is where to focus proof: evals, source/claim registries, MCP tool contracts, sandboxing, or a small public demo.

If you were reviewing this as an AI systems project, what one artifact would make it more credible?
```

## Outreach tracker fields

```yaml
id: outreach-YYYYMMDD-short-slug
person_or_group: "..."
category: ai-leader|framework-maintainer|evals|security|developer-education|enterprise-ai|coding-agent
contact_path: "needs_live_verification"
message_sent_at: null
status: planned|sent|replied|follow_up|closed|not_fit
ask: "..."
response_summary: "..."
follow_up_action: "..."
evidence_link: "..."
freshness: watch
```

## First sequence

1. Verify contact paths from official or public sources.
2. Prepare a one-page Suzie brief with architecture, limitations, and evidence examples.
3. Start with practical builders and communities before celebrity researchers.
4. Send specific questions, not broad mentorship requests.
5. Record date, path, ask, response, next action, and confidence.
