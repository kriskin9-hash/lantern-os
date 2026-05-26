# External LLM / Web Cache Intake

Generated: 2026-05-26.

Purpose: cache research from other LLMs, search snippets, and operator-pasted
web findings in a filtered, compressed, RAG-safe format.

## Rule

Store compressed claims and citations, not raw web dumps.

Do not paste whole articles, long copyrighted passages, private data, secrets,
or unverifiable claims as facts.

## Intake State

Use one of:

- `external_llm_summary`: summary from another model, not verified yet;
- `external_search_snippet`: search result snippet or brief result;
- `official_source_summary`: summary grounded in official docs;
- `operator_asserted`: user-provided claim;
- `needs_verification`: useful but not yet source-checked;
- `rejected`: not useful, unsafe, or unsupported.

## Minimal Record

Each row should preserve:

- topic;
- claim;
- source URL if available;
- source title if available;
- captured date;
- source type;
- rights state;
- evidence class;
- confidence;
- decision;
- compressed summary.

## Files

Inbox:

```text
data/rag-intake/external-llm-web-cache/inbox.md
```

JSONL cache:

```text
data/rag-intake/external-llm-web-cache/cache.jsonl
```
