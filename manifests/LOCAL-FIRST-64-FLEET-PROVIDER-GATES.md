# Local-First 64 Fleet Provider Gates

Status: active architecture recommendation  
Scope: Lantern OS / GM Agent Orchestrator fleet routing  
Style spine: `docs/ORION-MOOKMANREPORT4-STYLE.md`  
Operator boundary: local MCP status, installed providers, model availability, queue state, active workers, and dirty worktrees require operator-machine evidence

---

## Simple Answer

Expand the fleet by separating agent slots from paid LLM calls.

The 36/64 fleet should not mean 36 or 64 Codex/Claude workers. It should mean 36/64 task lanes. Most lanes should be tool-only or local-model-backed.

Designed slots = capacity and receipt contract.  
Live model workers = limited local inference.  
Paid cloud calls = disabled unless the operator manually overrides.

---

## Best Architecture

```text
64 fleet slots
├─ Tier 0: tool-only agents          = no LLM tokens
├─ Tier 1: local LLM agents          = Ollama / LM Studio / llama.cpp
├─ Tier 2: free-quota cloud fallback = optional, manual only
└─ Tier 3: paid Codex/Claude         = disabled by default
```

---

## What Can Run With Zero Codex / Claude Tokens

Most of the 12x3 ring can be deterministic:

| Role | Tool path |
|---|---|
| Repo-state inspector | `git status`, `git diff`, `rg` |
| Dirty-state checker | `git diff --name-only`, `git status --porcelain` |
| Manifest reader | parse Markdown / JSON |
| Open-issue reader | `gh issue list` or repo files |
| Stale-reference checker | `rg` broken paths / old names |
| Validation runner | `npm test`, `pytest`, PowerShell scripts |
| Environment-limit recorder | `systeminfo`, `where`, version checks |
| Evidence recorder | JSON / Markdown receipt writer |
| Blocker recorder | append manifest entries |
| Promotion judge | rules engine over receipts |

These roles do not need an LLM. They need scripts, receipts, and honest dashboard state.

---

## Local Model Layer

Use local model servers only for the roles that need language work:

- summarizer;
- patch drafter;
- claim classifier;
- rewrite agent;
- local RAG answerer;
- receipt summarizer.

### Option A — Ollama

Use for:

- claim summarizer;
- report cleaner;
- small patch drafter;
- receipt summarizer;
- local RAG answerer.

Expected local endpoint shape:

```text
http://127.0.0.1:11434/v1
```

### Option B — LM Studio

Use for:

- Windows-friendly local model server;
- manual model loading;
- OpenAI-compatible local endpoint;
- MCP-connected local agents.

Expected local endpoint shape:

```text
http://127.0.0.1:1234
```

### Option C — llama.cpp server

Use for:

- bare-metal local inference;
- GGUF models;
- controlled memory/runtime;
- portable local server.

---

## Practical Fleet Expansion For This Machine

Do not run 36 local LLMs. Run many queued agents, but only a few active model workers.

Recommended starting config:

```text
fleet_slots_total=64
ring_slots=36
tool_only_workers=48
local_llm_workers=2
local_llm_concurrency=1
cloud_workers=0
codex_enabled=false
claude_enabled=false
```

This gives the dashboard the 64-fleet shape without burning tokens or pretending there are 64 live model processes.

---

## Routing Policy

1. If a task can be done by git, rg, tests, or parser code, route it to `tool_only`.
2. If a task needs summarizing, rewriting, or classification, route it to `local_llm`.
3. If a task needs high-quality reasoning and local fails, hold for operator review.
4. Never auto-route to Codex or Claude.

---

## Provider Config Shape

```json
{
  "providers": {
    "codex": {
      "enabled": false,
      "reason": "disabled_to_preserve_tokens"
    },
    "claude": {
      "enabled": false,
      "reason": "disabled_to_preserve_tokens"
    },
    "ollama": {
      "enabled": true,
      "baseUrl": "http://127.0.0.1:11434/v1",
      "apiKey": "ollama",
      "maxConcurrent": 1,
      "roles": ["summarizer", "classifier", "patch_drafter", "receipt_writer"]
    },
    "lmstudio": {
      "enabled": true,
      "baseUrl": "http://127.0.0.1:1234",
      "maxConcurrent": 1,
      "roles": ["summarizer", "local_rag", "reviewer"]
    },
    "tool_only": {
      "enabled": true,
      "maxConcurrent": 16,
      "roles": ["git", "grep", "test", "manifest", "receipt", "validator"]
    }
  }
}
```

---

## Token-Saving Methods That Matter

Translate the token-saving strategy into local controls:

| Method | Implementation |
|---|---|
| Local routing | tool-only first |
| Prompt compression | send only touched files and snippets |
| Semantic caching | reuse previous receipts |
| Local drafting | Ollama / LM Studio drafts first |
| Minimal-diff edits | patch files, not whole repo rewrites |
| Structured extraction | JSON task receipts |
| Batching | one local model call summarizes many checks |

---

## Clean Fleet Model

| Layer | Meaning |
|---|---|
| 36 ring agents | role matrix / receipt contract |
| 64 fleet pool | queue capacity + tool workers + local model workers |
| live model use | 1-2 local LLM workers at a time |
| paid token use | zero unless operator manually overrides |

---

## Immediate Implementation Plan

1. Add provider gates: `codex=false`, `claude=false`.
2. Add a tool-only worker class.
3. Add local provider adapters for Ollama and/or LM Studio.
4. Convert the 12x3 ring into queued receipts, not live LLM sessions.
5. Add a router that sends 80-90% of tasks to scripts first.
6. Add a local LLM fallback only for summarizing, classifying, and rewriting.
7. Add dashboard counters for:
   - `designed_slots`;
   - `queued_tasks`;
   - `active_tool_workers`;
   - `active_local_llm_workers`;
   - `paid_cloud_calls`.

---

## Validation Path

Remote-safe validation:

```powershell
python -m pytest tests -q
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Invoke-LanternConvergenceLoop.ps1 -CloudVirtualization
```

Local-only validation:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-LanternLocalControls.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Open-TonyGarage.ps1
```

Manual evidence needed before claiming live status:

- actual MCP health response;
- actual exposed MCP tools;
- local provider health for Ollama / LM Studio / llama.cpp;
- queue / active / failed task counts;
- dirty worktree report;
- one tool-only receipt;
- one local-LLM receipt if a local model is available.

---

## Verdict

Expand the fleet with tool-only workers plus local Ollama / LM Studio workers.

Keep Codex and Claude hard-disabled by default.

Treat 64 as queue and role capacity, not 64 simultaneous LLMs.

Use local models only for the parts that actually need language.
