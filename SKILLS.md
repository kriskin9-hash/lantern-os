# Lantern OS Skills & Capabilities

**⚠️ REQUIRED READING: Before working with any skill, all agents must review [SECURITY.md](SECURITY.md)**

## Core Skills

### dream_journal
Dream Journal entry creation, management, and RAG-backed search.
- Create dream entries with metadata (emotions, tags, symbols, lucidity)
- Search/filter across dream history
- Export to CSV/JSONL format
- CSF compression for efficient storage

### lucid_dreaming
Lucid dreaming coaching and reflection tools.
- Technique suggestions (WILD, DILD, WBTB)
- Dream sign tracking
- Reality checks and sleep window planning
- Integration with dream journal for pattern analysis

### archive_curator
Documentation, archival, and knowledge management.
- Markdown rendering and repo file serving
- RAG house building (flat document index)
- Knowledge base search and retrieval
- CSF/CADD memory exports

### voice_curator
Text-to-speech and audio generation via ElevenLabs/OpenAI.
- Voice selection and model control
- Streaming audio output
- Provider fallback (ElevenLabs → OpenAI)
- Caching and rate-limit handling

## Agent Personas

Each dream chat request is routed to one of six agent personas based on keyword matching:

| Agent | Strengths | Keywords |
|-------|-----------|----------|
| **Lantern** | Reflection, guidance, wisdom | dream, reflect, meaning, symbol |
| **Blinkbug** | Analysis, patterns, data | analyze, pattern, track, data |
| **Keystone** | Integration, connections, structure | connect, integrate, organize |
| **Waterfall** | Flow, emotion, narrative | feel, story, journey, flow |
| **Xenon** | Creativity, imagination, play | create, imagine, play, explore |
| **Founder** | Vision, goals, direction | goal, vision, plan, future |

Selection is automatic but can be overridden via `?agent=NAME` parameter.

## Provider Chain

LLM requests are routed through a swarm orchestrator supporting:

- **Anthropic** (Claude family) — chat, coding, reasoning, creative
- **OpenAI** (GPT-4 family) — chat, reasoning, vision, coding
- **Google** (Gemini) — chat, vision, fast inference
- **xAI** (Grok) — creative, vision, chat
- **Mistral** — coding, chat, creative
- **Cohere** — summarization, research
- **Perplexity** — research, retrieval-augmented
- **DeepSeek** — reasoning, coding
- **Ollama** (local) — fallback, privacy-preserving
- **OpenRouter** (unified gateway)

Default is "auto" (best available). Override with `?provider=NAME`.

## Integration Points

### MCP Server
`src/mcp_server/server.py` — FastAPI + SSE service exposing:
- `queue_status` — task queue snapshot
- `task_intake` — enqueue work for async processing
- `dispatch_work` — assign tasks to agents
- `boot_check` — system readiness verification
- `list_skills` — enumerate available capabilities
- `get_status` — unified system health

### Discord Bot
Optional `src/discord_lounge_bot/bot.py` — chat relay and notifications when:
- `DISCORD_BOT_TOKEN` and `LANTERN_DISCORD_GUILD_ID` set in `.env.local`

### Three Doors Game
Interactive narrative engine at `/api/dream/doors`:
- Action: `start` | `reset` | `choose` | `status`
- Door choice persistence via CSF memory
- Image suggestions (Stable Diffusion or AI prompts)

## Configuration

### Environment Variables
Copy `.env.example` to `.env` (or `.env.local` for secrets):

```bash
ANTHROPIC_API_KEY=sk-...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
XAI_API_KEY=...
OLLAMA_BASE_URL=http://127.0.0.1:11434
ELEVENLABS_API_KEY=...
DISCORD_BOT_TOKEN=...
LANTERN_DISCORD_GUILD_ID=...
```

### Python Tests
```bash
python -m pytest tests/ -q --tb=short \
  --ignore=tests/test_anti_entropy_memory.py \
  --ignore=tests/test_audit_chain.py \
  --ignore=tests/test_discord_bot.py \
  --ignore=tests/test_discord_voice_gate.py
```

### Node.js Tests
```bash
npm run test:api --prefix apps/lantern-garage
npm run test:chat --prefix apps/lantern-garage
npm run test:ui --prefix apps/lantern-garage
```

## Security Guidelines

**ALL AGENTS MUST READ:** [SECURITY.md](SECURITY.md)

Key points:
- Never interpolate user input into Python `-c` scripts (use stdin JSON)
- File serving uses path.relative() boundary checks + denylist for `.env*`, `data/private`, etc.
- All HTTP responses include security headers (CSP, X-Frame-Options, etc.)
- CORS is restricted to local-only (no wildcard `*`)

## Skill Development

To add a new skill:
1. Create a directory in `/skills/{skill-name}/`
2. Add a `SKILL.md` with description and API contract
3. Implement in appropriate service (Node.js or Python)
4. Register in MCP server (`src/mcp_server/server.py`)
5. Document in this file

---

**Last updated:** 2026-06-08  
**Branch:** master  
**Status:** All core skills operational
