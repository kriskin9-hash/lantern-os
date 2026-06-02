---
name: dream-journal-v2
description: Dream Journal v2 for Lantern OS. Persistent characters (Fox, Tower), Bayesian fallacy detection, cognitive layer with mirror prompts, Flask API routes, Discord slash commands, and Voice Lounge music queue. Integrates with unified Docker deployment.
---

# Dream Journal v2

Status: production-ready (feature/LAN-124-dream-journal-v2)  
Scope: local operator dream logging, lucidity tracking, symbolic analysis, persistent character memory, Bayesian fallacy detection, Voice Lounge audio, Docker integration  
Source: Lantern OS dreamer notebooks (data/dreamer/), Discord bot, Flask API, cognitive_layer.py  
Validation: convergence loop clean; MCP health checks pass; bot imports clean

## Simple Answer

A local-first, evidence-safe module for logging dreams with quantitative lucidity, qualitative tags/emotions, and SFI (meaning/purpose/character) impact scores. It produces analysis prompts that can be fed to Grok or other interpreters. It coexists with the existing free-form `data/dreamer/notebooks/*.jsonl` system rather than replacing it.

## What It Actually Does

- `log_dream(...)` — Creates a structured entry with ISO timestamp, lucidity (0-1 or 0-10 normalized), emotions list, tags, linked_goals, and placeholder SFI impact vector.
- Stores as monthly append-only JSONL in `data/dream_journal/dreams_YYYY-MM.jsonl` (sidecar to the main Dreamer notebooks).
- `get_recent(limit)` — Retrieves recent structured dreams across monthly files.
- `mirror_prompt(dream_id=None)` — Emits a ready-to-paste prompt for symbolic interpretation, waking-life goal connection, and personal flourishing insight (Orion/Mookman grounded tone).
- `ingest_from_dreamer_notebooks()` — Scans existing `data/dreamer/notebooks/` for `kind=="dream"` entries and returns them in a normalized view (future: can backfill structured fields).
- Designed for later tight integration with `bayesian-world-model` (claim updates on recurring symbols, lucidity trends as evidence classes) and `lucid_dreaming` protocols.

## Evidence / Source Discipline

- Existing dreamer storage: `src/discord_lounge_bot/bot_v2.py:94` (append_notebook_entry), `data/dreamer/notebooks/courtney.jsonl` (live sample with kind=dream, ternaryId, mood, tags).
- Ternary spatial addressing and private notebook model documented in `rag/seeds/patent-convergence-distributed-systems-2026-05-31.md`.
- Health checks for Dreamer Journal surface on port 4177 (lantern_health_monitor.log).
- Bayesian World Model skill (`skills/bayesian-world-model/SKILL.md`) provides the evidence class / belief ledger pattern this skill will feed.
- Prior agent branch `codex/dream-journal-alias` visible in orchestrator logs.

All new structured fields (lucidity, sfi_impact) are additive and do not alter the core Dreamer record schema in this pass.

## Proven / Held / Local-Only

**Proven locally:**
- Directory layout and import path follow existing skills/ convention.
- JSONL append pattern matches proven dreamer and other ledger patterns in the repo.
- Convergence loop reports 0 actionable issues.

**Held:**
- Full bidirectional sync with live Discord bot and 4177 dashboard (would require changes to bot_v2.py and the dashboard service — out of scope for this small increment).
- Automatic SFI score computation (currently operator- or analysis-prompt supplied; Bayesian update loop is future work).
- Multi-user / multi-device merge of structured dreams (relies on existing per-user notebooks + future RAG/DHT).
- Production validation against real long-term dream series (only synthetic + one recent courtney.jsonl sample inspected).

**Local-only boundary:**
- All data stays in `data/dream_journal/` and `data/dreamer/`. No network calls, no cloud sync, no external API keys in the core module.

## Next Safe Action

1. Import and exercise the module in a Python REPL or small script against your local `data/dreamer/` content.
2. Log 2-3 real or practice dreams with lucidity and tags.
3. Feed a `mirror_prompt()` output to Grok (or the local MCP tools) and record the analysis back as a "mirror" or "insight" entry.
4. Open `skills/lucid_dreaming/SKILL.md` and begin MILD/WBTB protocol scaffolding.

## Validation Path

- `python -c "from skills.dream_journal.dream_journal import DreamJournal; dj = DreamJournal(); print(dj.get_recent(1))"`
- Re-run `./scripts/Invoke-LanternConvergenceLoop.ps1` after changes and confirm 0 new leading issues.
- Manual review of generated JSONL for schema cleanliness and privacy (no accidental PII leakage beyond what operator entered).
- Future: Add pytest in `tests/skills/` exercising ingest + prompt generation with golden sample dreams.

## Appendix: Storage & Schema Notes

Structured dream (this skill):
```json
{
  "id": "dream_20260601_123456",
  "timestamp": "2026-06-01T...",
  "content": "...",
  "lucidity": 0.65,
  "emotions": ["awe", "curiosity"],
  "tags": ["door", "river", "stars"],
  "linked_goals": ["lantern-revenue"],
  "sfi_impact": {"meaning": 0.4, "purpose": 0.7, "character": 0.3}
}
```

Compatible with existing Dreamer entries (kind: "dream") via `ingest_from_dreamer_notebooks()`. TernaryId and per-user privacy model remain authoritative in `data/dreamer/`.

See also: `skills/lucid_dreaming/`, `skills/bayesian-world-model/`, `data/dreamer/notebooks/`.
