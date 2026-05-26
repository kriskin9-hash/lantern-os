# External LLM / Web RAG Cache

Generated: 2026-05-26.

## Decision

Yes: Lantern can cache Googled information from other LLMs, but only as a
filtered compressed RAG record.

## What To Store

- compressed claims;
- source URLs;
- source titles;
- capture dates;
- source type;
- rights state;
- evidence class;
- confidence;
- decision;
- brief summary.

## What Not To Store

- full articles;
- long copyrighted quotes;
- private data;
- copied forum dumps without source context;
- model hallucinations as facts;
- credentials or secrets.

## Paths

```text
data/rag-intake/external-llm-web-cache/inbox.md
data/rag-intake/external-llm-web-cache/cache.jsonl
scripts/Add-ExternalRagCacheItem.ps1
```

## Promotion Rule

`external_llm` and `operator_asserted` items stay candidate/hold until verified
against a URL, local artifact, or accepted operator decision.
