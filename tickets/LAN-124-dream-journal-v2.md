# LAN-124: Dream Journal v2 — Persistent Characters, Cognitive Layer, Voice Lounge

**Type:** Feature  
**Priority:** P0  
**Status:** In Progress  
**Branch:** `feature/LAN-124-dream-journal-v2`  
**Created:** 2026-06-02  

---

## Description

Integrate Dream Journal v2 into Lantern OS unified Docker deployment. Includes:
- Persistent dream characters (The Fox, The Old Tower) with cross-session memory
- Bayesian fallacy detection on dream/reflection text
- Cognitive layer with mirror prompts, symbolic analysis, SFI scoring
- Robust music queue using yt-dlp for Voice Lounge audio streaming
- Flask API routes for Browser + Discord bot access
- Docker volume persistence for dream data

## Acceptance Criteria

- [ ] `/dream` slash command logs dreams + runs fallacy detection
- [ ] `@Fox` / `@Tower` character commands with persistent memory
- [ ] `/mirror` generates deep mirror prompts
- [ ] Voice lounge: `!play`, `!skip`, `!queue`, `!sing` with yt-dlp
- [ ] Flask API: `POST /api/dreams`, `GET /api/dreams/recent`, `GET /api/dreams/mirror/<id>`
- [ ] Docker: `docker-compose up` mounts dream journal data volume
- [ ] Dockerfile.unified copies `skills/dream_journal/` + installs deps
- [ ] No import errors, bot starts cleanly

## Files Changed

- `skills/dream_journal/cognitive_layer.py` (exists — Bayesian detector + characters)
- `skills/dream_journal/dream_journal.py` (exists — core journal)
- `src/discord_lounge_bot/bot_v2.py` (update — add music queue + voice fixes)
- `src/hff-api/routes/dream_journal.py` (new — Flask blueprint)
- `src/hff-api/app.py` (update — register blueprint)
- `Dockerfile.unified` (update — copy skills + install voice deps)
- `docker-compose.yml` (update — add dream journal volume)
- `requirements.txt` (update — add yt-dlp, pydub)
- `.env.example` (update — add dream journal env vars)
- `scripts/Start-MCPServer.ps1` (fix — `$Host` → `$BindHost`)

## Notes

- Port 8771 for MCP server (changed from 8770 to avoid conflict with gm-agent-orchestrator)
- Music queue uses yt-dlp for reliable audio extraction from URLs
- Character memory persisted to `data/dreams/character_*.json`
