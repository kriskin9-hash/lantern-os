# Lantern OS + Suzie Orchestrator

**Status:** TRL 4 (Field Validation)  
**Last Updated:** 2026-06-01  
**Repo Contract:** See `docs/REPO-CONTRACT.md`

---

## What This Repo Contains

### Lantern OS — Local-First AI Chat for Families
Privacy-first AI chat stack: desktop, browser, and dashboard surfaces.
- **Desktop:** Offline-first app with Vosk STT (no cloud speech-to-text)
- **Browser:** Same chat experience without install
- **Dashboard:** Local Flask service + Claude/Gemini/Codex routing
- **Voice Curator:** Public domain music library (CC-licensed + synthetic)
- **Kids Edition:** Age-gated, parental review, no external bridges

**Not included:** Cloud-hosted deployment, medical/legal advice surfaces, autonomous escalation.

### Suzie Orchestrator — AI Agent Management
Windows-first control plane for supervising 1–40 AI agents across local worktrees, GitHub, and MCP tool surfaces.
- **Slot Management:** Manage 8+ concurrent agent slots (Claude, Codex, Gemini, GPT, Ollama)
- **Task Queue:** Filesystem-based queue (being modernized to Redis for 400-agent scalability)
- **Token Quota:** Per-agent fallback routing when primary provider quota exhausted
- **MCP Boundary:** Safe tool allowlist — agents cannot escape sandbox

**Modernization:** Suzie 2.0 (Rust + Redis + PostgreSQL + Kubernetes) targets 400 agents across 20 operators. See `SUZIE-2.0-PLAN.md`.

---

## Quick Start

### 1. Install Dependencies

```bash
# Python packages
pip install discord.py aiohttp flask vosk pydub

# System packages (macOS/Linux)
brew install portaudio openssl

# Windows: install ffmpeg, portaudio from binaries
```

### 2. Start Lantern

```bash
cd apps/lantern-desktop
python lantern_desktop.py
```

### 3. Start Suzie (Agent Orchestrator)

```bash
cd gm-agent-orchestrator
pwsh -NoExit -Command { & .\Start-GmAgentOrchestrator.ps1 }
```

### 4. Start Discord Bot (Optional)

```bash
export DISCORD_BOT_TOKEN="your-token-here"
export LANTERN_DISCORD_GUILD_ID="your-guild-id"
cd src/discord_lounge_bot
pwsh -NoExit -Command { & ..\..\scripts\Start-DiscordBotWatchdog.ps1 }
```

---

## Repository Structure

```
├── apps/
│   ├── lantern-desktop/          # Tkinter desktop app + Vosk STT
│   ├── lantern-browser/          # Flask + HTML/JS web UI
│   └── lantern-kids/             # Age-gated variant (parental review)
├── services/
│   ├── lantern-dashboard/        # Flask control plane
│   ├── audit-verification-api/   # Cryptographic audit chain
│   └── discord-lounge-bot/       # Discord integration
├── gm-agent-orchestrator/        # Suzie: slot/queue/token management
├── src/
│   ├── hff-api/                  # Shared Flask utilities
│   └── voice_curator/            # Public domain music library
├── scripts/
│   ├── Start-DiscordBotWatchdog.ps1     # 24/7 bot monitoring
│   ├── Start-GmAgentOrchestrator.ps1    # Orchestrator supervisor
│   └── ... (135+ support scripts)
├── docs/
│   ├── REPO-CONTRACT.md          # What belongs in this repo
│   ├── LINEAR-WORKFLOW.md        # Operator training for sprints
│   └── ARCHITECTURE.md           # System design
├── tests/
│   ├── test_lantern_desktop.py
│   ├── test_suzie_orchestrator.py
│   └── ...
└── docker/
    ├── Dockerfile.lantern        # Lantern container
    └── Dockerfile.suzie          # Orchestrator container
```

---

## Active Product Streams

| Stream | TRL | Status | Owner |
|--------|-----|--------|-------|
| Lantern Desktop Chat | 4 | Shipped | (unassigned) |
| Lantern Browser Chat | 4 | Shipped | (unassigned) |
| Vosk STT Integration | 4 | Active | (unassigned) |
| Discord Bot + MCP | 4 | Just shipped | Founder |
| Suzie Orchestrator Core | 4 | Active (Phase 1 modernization) | Founder |
| Dashboard Three-View | 4 | Active | (unassigned) |

For complete stream list, see `docs/STREAMS.md`.

---

## Contributor Guide

### For Operators

1. **Read this README** — understand Lanterns + Suzie roles
2. **Check `CONTRIBUTING.md`** — git workflow, commit message style
3. **Join Linear workspace** — backlog lives there, not GitHub issues
4. **Claim a task** — see `docs/LINEAR-WORKFLOW.md` for how
5. **Work locally** on `cleanup/*` or `feature/*` branch
6. **Push and open PR** — Founder reviews Friday
7. **Merge once approved** — Linear status → Done

### For Founders

- Architecture decisions: see `docs/ARCHITECTURE.md`
- IP strategy: see memory file `/MEMORY.md`
- Roadmap: Suzie 2.0 plan, Lantern Kids scale-up, 20-operator foundry model

---

## Known Limitations (v1.0)

| Limitation | Impact | Roadmap |
|-----------|--------|---------|
| Filesystem task queue | O(N) claim ops, race conditions | Suzie 2.0: Redis (Q3 2026) |
| JSON state files | No indexing, bottleneck at 40+ agents | Suzie 2.0: PostgreSQL (Q3 2026) |
| Single-node deployment | No distributed consensus | Suzie 2.0: Kubernetes (Q3 2026) |
| Parental review in Kids mode | Manual, not automated | Lantern Kids v2 (Q3 2026) |
| Vosk STT latency | ~500ms on Starlink | Accept trade-off: offline-first |

---

## Support & Resources

- **Getting started:** Run `python apps/lantern-desktop/lantern_desktop.py`
- **Troubleshooting:** Check `~/.lantern/logs/` for error logs
- **Operator onboarding:** See `docs/LINEAR-WORKFLOW.md`
- **Architecture questions:** See `docs/ARCHITECTURE.md`
- **Issues & backlog:** Linear workspace (not GitHub)

---

## License

- **Lantern OS core** — AGPL (source-available)
- **Lantern Kids** — Proprietary (parental consent gating)
- **Suzie Orchestrator** — AGPL (source-available, self-host tier)
- **Third-party dependencies** — See `LICENSE.md` for full attribution

---

**Last Updated:** 2026-06-01  
**Reviewed:** Phase A (Discord + Linear setup), Phase C Phase 0 (top-level cleanup)  
**Next Review:** 2026-06-07 (end of Cycle 1 cleanup)
