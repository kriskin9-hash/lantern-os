# Research Hook Policy

This is the target policy for hook-backed research hygiene. This PR documents the policy only; enforcement hooks should be added in a later PR after local validation.

## SessionStart

Inject compact research state from `status/research-context.json`:

- best synthesis,
- latest audit,
- known gaps,
- source registry path,
- claim registry path,
- how to request missing research.

## UserPromptSubmit

When a prompt asks for research, verification, similar sources, freshness, citations, or vendor comparisons:

1. Check `status/research-context.json`.
2. If current data exists, point the agent to the best synthesis and audit.
3. If data is stale or missing, require a research request.
4. Warn if the prompt asks to treat partial data as complete.

## PreToolUse

Before editing research docs, warn or block if the edit changes a synthesis or canonical research doc without also updating the research status artifacts.

Protected paths:

```text
research/syntheses/**
docs/research/**
```

Expected companion paths:

```text
research/index/source-registry.yml
research/index/claim-registry.jsonl
research/audits/latest.md
status/research-context.json
```

## PostToolUse

After research writes, run the lightweight research ingestion validation script once it exists:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Test-ResearchIngestion.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Update-ResearchContext.ps1
```

## Stop

Block or require recovery if a research task tries to finish while:

- source registry changed but `status/research-context.json` did not,
- synthesis changed but latest audit did not,
- a claim says fully read while the source is partial or skimmed,
- speculative language appears outside `research/hypotheses/`,
- a missing-source gap was found but no research request was created.

## Non-Claude fallback

Codex, Gemini, manual commits, and other agents should get the same checks through future script or pre-commit validation. Hooks are a convenience surface, not the only enforcement layer.
