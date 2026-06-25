---
adr: 0008
title: End product is a personal AI wrapper — capabilities as Tools + Skills in the one loop
status: Accepted
date: 2026-06-24
author: Alex Place
---

## Context

After establishing the Convergence Core (ADR-0002) and the core loop
(`Observe → Remember → Reason → Act → Verify → Converge`), the question
arose: *what does the user actually do with this system?* The system had:

- A dream-journal chat interface
- Four live skills (dream_journal, lucid_dreaming, archive_curator, voice_curator)
- Thirteen skills listed in `skills/*/SKILL.md` that were design-contracts only
- No general-purpose tool-calling for user tasks (web lookup, document creation, etc.)

The system was optimised for one persona (journaling / convergence) but the
operator's real day-to-day needs include: looking up information, producing
documents (resumes, cover letters), assisting with job applications, and
driving general tasks. Cloud LLMs (Claude, GPT-4) handle these today, but the
local Ouro model cannot because it was trained only on coding sessions.

## Decision

**The end product is a personal AI wrapper** — a thin, private interface over
the one loop that gives the operator general-purpose AI capabilities without
leaking data to external services:

1. **Capabilities are Tools** (`lib/tool-runner.js`) — atomic, consent-gated,
   auditable. New capabilities register in the canonical REGISTRY so that
   advertised == executable == trainable (train/serve parity rule). New tools in
   scope: `web_search`, `web_fetch`, `create_document`.

2. **Workflows are Skills** (`skills/*/`) — chains of Tools that implement a
   user-facing scenario (e.g. "job-application assistant"). A Skill is live when
   it is wired to real Tools and has an acceptance test. Docs must not claim a
   skill is live until it is.

3. **User artifacts live in a user workspace** (`~/.keystone/workspace/` by
   default, configurable via `KEYSTONE_WORKSPACE`), not in the repo. The repo
   sandbox (`_safe()` in tool-runner.js) is correct for coding tools; user
   documents (resumes, exports) need a separate, consent-gated root.

4. **The local model (Ouro) needs capability trajectories** — a training corpus
   of `{instruction, input, output}` + `<tool_call>` format for general tasks
   (web lookup, document generation, form-filling), kept separate from the coding
   corpus.

5. **No autonomous submission** — the human must confirm any action that
   affects external state (sending email, submitting a form, publishing content).
   The `web_fetch` tool reads; it does not post.

## Status

**Accepted** — follow-on issues #1095 (web tools), #1096 (user workspace),
#1097 (document generation), #1098 (job-application skill), #1099 (live
skills audit), #1100 (capability training data).

## Consequences

### Positive
- General-purpose AI capability without external data leakage
- Capabilities are auditable (every tool call is logged; consent-gated)
- Skills layer makes the one loop extensible without architectural sprawl
- Train/serve parity means the local model learns from real operator sessions

### Negative / trade-offs
- Tool implementations must be kept narrow (no shell injection, no unconstrained
  web fetch); each one is a new attack surface
- User workspace requires its own safe-path guard distinct from the repo sandbox
- Capability corpus must be built/curated; won't improve the local model overnight
- Operator must confirm external actions — intentionally slows some flows

## Alternatives considered

**Embed a full agent framework (LangChain / CrewAI):** Rejected — violates
ADR-0002 (single convergence core; no independent agent ecosystems).

**Only ever use cloud models for user tasks:** Rejected — data privacy; operator
wants local-first capability even at reduced quality.

**Hard-code workflows in server routes:** Rejected — not reusable, not trainable,
creates the architectural sprawl that ADR-0002 forbids.
