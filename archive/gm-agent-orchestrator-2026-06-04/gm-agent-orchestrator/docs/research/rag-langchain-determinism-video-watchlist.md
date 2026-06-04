# RAG, LangChain, and Determinism Video Watchlist

Status: planning tracker, not completed research ingestion.
Related issue: #274 Research AI leaders and agentic content index.
Last checked: 2026-05-05.
Refresh cadence: monthly while job-search/training use remains active.

## Purpose

This watchlist gives the operator a short, refreshable table of videos and courses to ingest manually for job-oriented learning around RAG, LangChain/LangGraph, evaluation, determinism, security, and Java/Spring AI application work.

This document is intentionally a docs-level tracker. A row marked `todo`, `watching`, or `watched` is not a claim that the source was fully read or watched. Promote items into the research registry only after the source has been reviewed and summarized.

## Current active watch

The operator is currently watching the priority-1 item:

- Andrew Ng / DeepLearning.AI: `LangChain: Chat with Your Data`
- Status: `watching`
- Started: 2026-05-05
- Quiz trigger: when the operator reports this video is done, quiz on the core RAG concepts before marking the item `watched` or `ingested`.

## Status values

- `todo` - selected but not started.
- `watching` - started but notes are incomplete.
- `watched` - viewed, but not yet summarized into repo context.
- `ingested` - notes captured and any claims/sources updated where applicable.
- `refresh` - source should be rechecked for newer material.
- `skip` - intentionally deprioritized.

## Priority watchlist

| Pri | Status | Topic | Researcher / source | Link | Why ingest | Expected note output | Refresh by | Notes |
|---:|---|---|---|---|---|---|---|---|
| 1 | watching | RAG basics and document chat | Andrew Ng / DeepLearning.AI | https://www.deeplearning.ai/short-courses/langchain-chat-with-your-data/ | Best first bridge into document loading, chunking, embeddings, retrieval, and chat over data. | RAG pipeline notes plus one portfolio idea. | 2026-06-05 | Current active watch; quiz before marking watched or ingested. |
| 2 | todo | LangChain app patterns | Andrew Ng / DeepLearning.AI | https://www.deeplearning.ai/short-courses/langchain-for-llm-application-development/ | Builds common LangChain vocabulary seen in AI application job posts. | Glossary plus reusable app patterns. | 2026-06-05 | Watch before deeper LangGraph content. |
| 3 | todo | RAG from scratch | Lance Martin / LangChain | https://www.youtube.com/results?search_query=Lance+Martin+RAG+from+Scratch | More implementation-oriented view of retrieval pipelines and common RAG failure modes. | Pipeline diagram and failure-mode table. | 2026-06-05 | Replace search URL with canonical playlist/video after verification. |
| 4 | todo | LangGraph stateful agents | LangChain Academy | https://academy.langchain.com/courses/intro-to-langgraph | Maps agent state machines, routing, and workflow graphs to the orchestrator/control-plane mental model. | State graph notes mapped to Suzie/orch concepts. | 2026-06-05 | Good bridge from RAG to agent workflows. |
| 5 | todo | AI evals and production reliability | Hamel Husain / Shreya Shankar | https://www.youtube.com/results?search_query=Hamel+Husain+Shreya+Shankar+AI+evals | Helps define fixtures, traces, failure labels, regression checks, and what “good enough” means. | Eval rubric and determinism checklist. | 2026-06-05 | High leverage for orchestrator validation. |
| 6 | todo | Java and Spring AI RAG | Dan Vega / Spring AI | https://www.youtube.com/results?search_query=Dan+Vega+Spring+AI+RAG | Best bridge from enterprise Java/Spring experience into AI application engineering roles. | Java portfolio implementation notes. | 2026-06-05 | Convert into Spring Boot RAG portfolio task. |
| 7 | todo | LLM fundamentals | Andrej Karpathy | https://www.youtube.com/watch?v=zjkBMFhNj_g | Explains why LLM outputs are probabilistic and context-sensitive, which grounds determinism/eval thinking. | Model behavior notes and interview talking points. | 2026-08-05 | Foundational, not RAG-specific. |
| 8 | todo | Prompt injection and LLM security | Nicholas Carlini | https://www.youtube.com/results?search_query=Nicholas+Carlini+prompt+injection+LLM+security | Directly relevant to RAG ingestion, tool access, prompt/data exfiltration, and MCP boundary safety. | RAG/tool threat model checklist. | 2026-06-05 | Prefer recent talks and primary papers. |
| 9 | todo | RAG evaluation metrics | Ragas maintainers / community | https://www.youtube.com/results?search_query=RAGAS+RAG+evaluation+tutorial | Gives practical metrics such as faithfulness, answer relevance, and context precision/recall. | Metrics table and candidate test fixture format. | 2026-06-05 | Useful for portfolio hardening. |
| 10 | todo | Retrieval/index design | LlamaIndex / Jerry Liu | https://www.youtube.com/results?search_query=Jerry+Liu+LlamaIndex+RAG | Provides an indexing/retrieval-first contrast to LangChain app orchestration. | LangChain vs LlamaIndex comparison notes. | 2026-06-05 | Pick newest official talk before ingestion. |

## Minimal ingestion template

```markdown
### Video ID:
Title:
Source:
URL:
Watched status: todo | watching | watched | ingested | refresh | skip
Watched date:
Refresh by:

#### Why this matters
-

#### Concepts learned
-

#### Terms to add to resume / interviews
-

#### Applies to Suzie / orch how?
-

#### Portfolio artifact idea
-

#### Claims needing verification
-

#### Follow-up links
-
```

## Quiz gate for current active watch

Before the active watch is marked `watched` or `ingested`, ask the operator a short quiz covering:

1. What problem RAG solves compared with sending only the user prompt to the model.
2. The basic RAG pipeline: load, split, embed, store, retrieve, generate.
3. Why chunk size and chunk overlap affect answer quality.
4. What embeddings and vector stores contribute.
5. How retrieval quality can fail even when the LLM is strong.
6. How this maps to a Spring Boot or enterprise document-assistant portfolio project.

## Promotion rule

When a video is promoted from this docs tracker into canonical research context:

1. Add or update a source record in `research/index/source-registry.yml` with stable ID, authority, freshness, read status, and tags.
2. Add claim records to `research/index/claim-registry.jsonl` only for claims that are actually supported by watched/read source evidence.
3. Update the relevant synthesis or request file.
4. Refresh `research/audits/latest.md` and `status/research-context.json` when the validation/update scripts are available.
5. Do not mark a video as `ingested` until the notes and evidence path are complete.

## Portfolio mapping

The recommended first portfolio artifact is an enterprise-style RAG service:

- Spring Boot REST API.
- Document ingestion for invoices, remittance notes, payment workflow documentation, or synthetic banking operations docs.
- Retrieval with citations.
- Structured JSON output.
- Evaluation fixtures for retrieval quality and answer grounding.
- Security notes covering prompt injection and data exfiltration risks.
- README section mapping the project to AI Application Engineer / Enterprise GenAI Engineer roles.
