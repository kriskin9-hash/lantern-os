# Research Control Plane

This directory is the canonical entry point for research used by humans and agents in `gm-agent-orchestrator`.

The goal is to make the best available research visible, citeable, auditable, and requestable without relying on chat history.

## Read order

1. `status/research-context.json` — current best synthesis, audit, and known gaps.
2. `research/index/source-registry.yml` — source inventory and read/freshness status.
3. `research/index/claim-registry.jsonl` — machine-readable claim ledger.
4. `research/audits/latest.md` — latest source coverage and risk audit.
5. Relevant synthesis under `research/syntheses/`.

## Rules for agents

- Do not treat a synthesis as primary source truth. Trace important claims to the source registry or claim registry.
- Do not claim a source was fully read unless `read_status: complete` exists in the registry.
- Keep speculation in `research/hypotheses/`, not in promoted docs or syntheses.
- If needed data is stale, missing, partial, or contradictory, create a research request in `research/requests/open/` or route it through the orchestrator MCP queue.
- When research docs change, update the source registry, claim registry, latest audit, and `status/research-context.json` together.

## Vendor pattern adopted

Use a hybrid research system:

- Claude / Anthropic pattern: lead researcher, parallel subagents, citation/audit pass.
- OpenAI pattern: explicit data-source contract, background-capable research, citations, tool budget awareness.
- Gemini pattern: collaborative plan first, then async/background execution with status polling.

## Requesting more research

Create a request file under `research/requests/open/` using the template in `research/requests/README.md`.

A valid request must state:

- the question,
- why it matters now,
- existing data checked,
- required source types,
- acceptance criteria,
- requested owner.

## Promotion rule

Research may be promoted into canonical docs only after the latest audit says the relevant claims are verified or explicitly marked as inferred with source support.

## Validation scripts

Use these scripts before claiming research ingestion is complete:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Test-ResearchIngestion.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Update-ResearchContext.ps1 -DryRun
```
