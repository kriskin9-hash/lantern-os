# Changelog

All notable changes to Lantern OS should be documented in this file.

The format follows the spirit of Keep a Changelog, with entries grouped by
release date. This project is currently private and local-first, so release
notes should be honest about what was verified locally and what remains design
intent.

## [1.0.0] — 2026-06-05 — Dream Journal Orion Edition

### Core
- Dream Journal V1.0.0 — local-first, private, no account required
- `node apps/lantern-garage/server.js` — single command startup on port 4177
- Modular route architecture: 7 domain modules under `apps/lantern-garage/routes/`
- `cloud-server.js` unified with server.js — Railway/Render deploy via PORT env

### Dream Chat
- Multi-provider streaming: Gemini 2.5-flash (primary), Claude haiku-4-5, OpenAI, Grok, Ollama
- Three Doors canary system — AI-generated [DOORS: A | B | C] after every reply
- Canvas banner — 3-panel atmospheric widescreen PNG, click to download
- Multi-turn conversation history (last 6 turns threaded into API calls)
- Adaptive Focus Memory — tiered dream context (Full/Compressed/Placeholder)
- Symbol co-occurrence mesh — relational pairs passed to system prompt
- Voice STT (Web Speech API) + TTS
- CTF symbol autocomplete (~80 unicode glyphs)
- Provider settings drawer (Claude, Gemini, ChatGPT, Grok) with hot-reload

### Data & API
- `POST /api/dream/create` — saves entries with dcf_class/rps_flags schema
- `GET /api/dream/stats` — emotions, tags, symbols, avg lucidity
- `GET /api/dream/search` — text + tag filter
- `GET /api/dream/export` — JSONL/CSV download
- `GET /api/dream/symbols/timeline` — weekly symbol frequency + co-occurrence pairs
- `POST /api/settings/providers` — saves keys to .env, hot-reloads process.env
- `GET /api/settings/providers` — provider presence (never exposes values)

### Convergence
- MemOS `GeneralMemCube` wired as semantic retrieval backend (`src/convergence_io/memos_bridge.py`)
- `TesseractEngine._convergence_rag()` — MemOS semantic search → flat-rag fallback
- Convergence loop: 12 phases, `promotion_ready=True`
- Gemini model updated: `gemini-2.5-flash` (gemini-1.5-flash deprecated)
- Claude model updated: `claude-haiku-4-5-20251001` (claude-3-5-haiku-20241022 deprecated)

### Verification
- 18/18 Node API tests passing (`tests/test_dream_journal_api.js`)
- 11/11 multi-turn chat tests passing (`tests/test_dream_chat_multiturns.js`)
- Gemini 2.5-flash streaming confirmed live
- Claude haiku-4-5 streaming confirmed live
- Convergence loop `promotion_ready=True`

## [Unreleased]

### Planned (Convergence)

- **#142** Watch/Observe phase -- drift detection between convergence runs
- **#143** Backpressure + rate limiting on TesseractEngine (bounded queue, 429 shedding)
- **#145** Structured trace logging (OpenTelemetry-style spans per layer)
- **#146** Idempotent slot claims (deterministic slot IDs, no orphaned slots on retry)
- **#147** Graduated degradation (layer-by-layer fallback instead of all-or-nothing)
- **#144** Receipt diff (compare current vs previous convergence run)
- **#148** PII cleanup -- remove "waynesville" from persona keyword matcher

### Known Bugs (Tracked)

- **#160** _multi_signal_score() needs real vector similarity integration
- **#159** Memory Engine query() is O(n) -- no keyword/entity indexes
- **#164** hff-api dream_journal /recent route returns empty entries (TODO stub)
- **#165** converged_tesseract.py convergence_io_route_on_slice is a placeholder stub
- **#166** hff-api load_data_source() returns mock data -- not yet implemented
- **#167** discord lounge bot memory_layer export_csf_stub is a placeholder

### Added

- Initial workspace governance files for changelog, license, security, support,
  code of conduct, and editor defaults.

### Verification

- Added as documentation-only files; no runtime behavior changed.

## Changelog Rules

- Prefer concrete dates in `YYYY-MM-DD` format.
- Record local verification evidence for user-facing changes.
- Mark unverified, design-only, or future-facing claims explicitly.
- Keep private data, secrets, journal entries, and local receipts out of release
  notes unless they are referenced only as redacted evidence paths.
