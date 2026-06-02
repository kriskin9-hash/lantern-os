# Dream Journal — User Guide

**Status:** Active (TRL 4)
**Last Updated:** 2026-06-02
**Skill path:** `skills/dream_journal/`
**Data path:** `data/dream_journal/` and `data/dreamer/notebooks/`

---

## What the Dream Journal Is

The Dream Journal is a local-first, privacy-safe module for logging dreams with quantitative lucidity scores, emotional tags, symbolic analysis, and SFI (meaning/purpose/character) impact vectors. It runs entirely on your machine — no cloud calls, no external API keys in the core module.

It has two layers:

- **`dream_journal.py`** — Structured entry storage, retrieval, and mirror-prompt generation
- **`cognitive_layer.py`** — Bayesian fallacy detection on dream text + persistent symbolic dream characters (The Fox, The Old Tower)

Both coexist with the existing free-form Dreamer notebook system (`data/dreamer/notebooks/*.jsonl`) rather than replacing it.

---

## Prerequisites

### Python

Python 3.12 is required (matches the unified Docker container).

```bash
python --version   # should show 3.12.x
```

### Install dependencies

The Dream Journal core has no external dependencies beyond the Python standard library. For the Discord bot integration and Docker deployment, install the full stack:

```bash
pip install discord.py aiohttp flask
# or use the unified requirements file:
pip install -r requirements.txt
```

### For Docker / cloud deployment

The unified container (`Dockerfile.unified`) includes everything needed. It exposes ports `5000`, `4177`, `8765`, `4178`, `9000`. The Dream Journal skill is copied in via:

```dockerfile
COPY src/ src/
COPY apps/ apps/
COPY skills/ skills/   # dream_journal lives here
COPY data/ data/       # notebooks and structured dreams land here
```

No additional Docker config is needed for the journal itself.

---

## Setup

### 1. Verify the skill loads

From the repo root:

```bash
python -c "from skills.dream_journal.dream_journal import DreamJournal; dj = DreamJournal(); print('OK:', dj.get_recent(1))"
```

Expected output:

```
OK: []
```

(Empty on first run — no dreams logged yet.)

### 2. Verify the cognitive layer loads

```bash
python -c "from skills.dream_journal.cognitive_layer import get_cognitive_journal; cj = get_cognitive_journal(); print(cj.character_status())"
```

Expected output:

```
Dream Characters:
- The Fox: 0 memories | wise, cautious, symbolic guide
- The Old Tower: 0 memories | ancient, watchful, mysterious
```

### 3. Data directories

On first use, the journal auto-creates its directories:

```
data/
  dream_journal/          # structured monthly JSONL files
    dreams_2026-06.jsonl  # created on first log_dream() call
  dreamer/
    notebooks/            # existing free-form dreamer entries (Discord bot)
    character_fox.json    # character memory (created by cognitive layer)
    character_the_old_tower.json
```

---

## Usage — Python API

### Log a dream

```python
from skills.dream_journal.dream_journal import DreamJournal

dj = DreamJournal()

entry = dj.log_dream(
    content="I was standing at a glowing door in a forest. The Fox appeared and led me through.",
    lucidity=0.7,                          # 0.0 (non-lucid) to 1.0 (fully lucid)
    emotions=["awe", "curiosity"],
    tags=["door", "forest", "fox", "guide"],
    linked_goals=["lantern-revenue", "creative-output"],
    sfi_impact={"meaning": 0.6, "purpose": 0.8, "character": 0.4}
)

print(entry["id"])   # e.g. dream_20260602_143022
```

**Schema of a stored entry:**

```json
{
  "id": "dream_20260602_143022",
  "timestamp": "2026-06-02T14:30:22+00:00",
  "content": "I was standing at a glowing door...",
  "lucidity": 0.7,
  "emotions": ["awe", "curiosity"],
  "tags": ["door", "forest", "fox", "guide"],
  "linked_goals": ["lantern-revenue"],
  "sfi_impact": {"meaning": 0.6, "purpose": 0.8, "character": 0.4}
}
```

### Retrieve recent dreams

```python
recent = dj.get_recent(limit=5)
for r in recent:
    print(r["timestamp"], r["content"][:60])
```

### Generate a mirror prompt

The mirror prompt is a ready-to-paste analysis request for Grok or another interpreter:

```python
prompt = dj.mirror_prompt()   # uses most recent dream
print(prompt)

# Or target a specific dream by ID:
prompt = dj.mirror_prompt(dream_id="dream_20260602_143022")
```

Feed the output into `/mcp call` in Discord or paste directly into Grok.

### Ingest existing Dreamer notebook entries

Pulls `kind == "dream"` entries from `data/dreamer/notebooks/*.jsonl` into a normalized view:

```python
legacy = dj.ingest_from_dreamer_notebooks()
for entry in legacy:
    print(entry)
```

---

## Usage — Discord Bot Commands

The Dream Journal integrates into the Lantern OS Discord bot (`src/discord_lounge_bot/bot_v2.py`). The following slash commands interact with journal features:

| Command | Tier required | What it does |
|---|---|---|
| `/dream <text>` | Public | Logs a new dream entry to your personal notebook and replies with a confirmation |
| `/recall` | Public | Retrieves your last 3 notebook entries |
| `/note <text>` | Public | Saves a free-form note to your dreamer notebook |
| `/talk fox <message>` | Supporter+ | Talks to The Fox character; it remembers and responds |
| `/talk tower <message>` | Supporter+ | Talks to The Old Tower character |
| `/character` | Supporter+ | Shows all characters and memory counts |
| `/converge` | Pilot+ | Runs the Bayesian fallacy detector on your most recent dream |
| `/mirror` | Pilot+ | Generates a mirror prompt for your most recent dream |

### Bot environment variables required

Copy `.env.example` to `.env` (or `.lantern/discord.env`) and fill in your values:

```bash
DISCORD_BOT_TOKEN=your-bot-token-here
LANTERN_DISCORD_GUILD_ID=your-guild-id-here

# Optional (defaults shown)
MCP_SERVER_URL=http://127.0.0.1:8787
LANTERN_STATUS_URL=http://127.0.0.1:4177/api/status
```

### Start the bot (Windows)

```powershell
cd $REPO_ROOT
pwsh -NoExit -Command { & .\scripts\Start-DiscordBotWatchdog.ps1 }
```

### Start the bot (Linux / Mac)

```bash
export DISCORD_BOT_TOKEN="your-token"
export LANTERN_DISCORD_GUILD_ID="your-guild-id"
cd src/discord_lounge_bot
python bot_v2.py
```

Expected console output on start:

```
[READY] Logged in as LanternBot#1234 at 2026-06-02T...
[SYNC] Synced 27 slash commands globally
```

### Role tiers

Discord roles control access to journal features. Create these roles in your server (case-insensitive):

| Role | Access |
|---|---|
| `@everyone` (Public) | `/dream`, `/recall`, `/note`, `/help`, `/status`, `/subscribe` |
| `supporter` | All public commands + `/talk`, `/character`, `/wish`, `/wallet` |
| `pilot` | All supporter commands + `/converge`, `/mirror`, `/orchestrator`, `/queue` |
| `founder` | All commands + admin/release gate commands |

---

## Usage — Docker (Unified Container)

The unified container runs the full Lantern OS stack including the journal skill.

### Build

```bash
docker build -f Dockerfile.unified -t lantern-os:latest .
```

### Run locally

```bash
docker run -d \
  -p 4177:4177 \
  -p 5000:5000 \
  -e DISCORD_BOT_TOKEN=your-token \
  -e LANTERN_DISCORD_GUILD_ID=your-guild-id \
  -v $(pwd)/data:/app/data \
  lantern-os:latest
```

Mounting `data/` as a volume preserves your dream journal entries and character memories between container restarts.

### Health check

```bash
curl http://localhost:9000/health
```

The container also exposes the primary dashboard at `http://localhost:4177`.

### Exposed ports

| Port | Service |
|---|---|
| 4177 | Primary Lantern dashboard (local front door) |
| 5000 | Flask app / API |
| 8765 | WebSocket / secondary service |
| 4178 | Secondary dashboard surface |
| 9000 | Health check endpoint |

### Cloud mirrors

| Surface | URL | Status |
|---|---|---|
| Local dashboard | `http://127.0.0.1:4177` | Verified — primary front door |
| Netlify cloud mirror | `https://lantern-os-cloud.netlify.app` | Configured (health check pending) |
| AWS ECS Fargate | Service URL pending operator deploy | Candidate |
| Render | Retired 2026-05-29 (returned 404) | Retired |

The local dashboard is always canonical. Cloud mirrors serve the same surface — not separate products. Mirror status is tracked in `manifests/cloud-mirrors.json`.

---

## Usage — Cognitive Layer (Fallacy Detection + Characters)

### Analyze a dream for reasoning fallacies

```python
from skills.dream_journal.cognitive_layer import get_cognitive_journal

cj = get_cognitive_journal()

results = cj.analyze("I always feel afraid because I always feel afraid. Everyone in the dream was against me.")
for r in results:
    print(r["fallacy"], r["probability"], r["note"])
```

Example output:

```
Circular Reasoning 0.857 Conclusion assumed in the premise.
Hasty Generalization 0.631 Broad conclusion from limited examples.
Appeal To Emotion 0.583 Heavy reliance on emotion rather than evidence.
```

**Fallacy detection reference:**

| Fallacy | Trigger keywords | Prior probability |
|---|---|---|
| False Dichotomy | "either", "only" | 0.28 |
| Appeal to Emotion | "scary", "feel", "afraid", "beautiful", "terrifying", "wonderful" | 0.32 |
| Hasty Generalization | "always", "never", "everyone" | 0.35 |
| Circular Reasoning | "because" appearing more than once | 0.18 |

Detection threshold: Bayesian posterior `>= 0.30`.

### Talk to dream characters

```python
# The Fox — wise, cautious, symbolic guide
response = cj.talk("fox", "What does the glowing door mean?", user_id="alex")
print(response)
# -> The Fox tilts its head, eyes glinting. (I carry 1 memories.) "What does the glowing door mean?"

# The Old Tower — ancient, watchful, mysterious
response = cj.talk("tower", "Why do you keep appearing?", user_id="alex")
print(response)
```

Character memories persist in `data/dreams/character_fox.json` and `data/dreams/character_the_old_tower.json`.

### Check character status

```python
print(cj.character_status())
# Dream Characters:
# - The Fox: 3 memories | wise, cautious, symbolic guide
# - The Old Tower: 1 memories | ancient, watchful, mysterious
```

---

## Testing

### Run the passing Discord bot tests (includes /dream coverage)

```bash
pip install pytest pytest-asyncio "discord.py>=2.3.2" dpytest
python -m pytest tests/test_discord_bot.py -v
```

All 15 tests should pass.

### Run the full suite

```bash
python -m pytest tests/ -q
```

Note: `tests/test_fallacy_detector.py` has 4 pre-existing failures because `apps/superfleet_memory/bayesian_fallacy_detector.py` does not yet exist. The working fallacy detector is in `skills/dream_journal/cognitive_layer.py`.

### Validate the skill directly

```bash
python -c "
from skills.dream_journal.dream_journal import DreamJournal
dj = DreamJournal()
e = dj.log_dream('Test dream', lucidity=0.5, emotions=['calm'], tags=['test'])
print('Logged:', e['id'])
print('Recent:', dj.get_recent(1)[0]['content'])
print('Prompt preview:', dj.mirror_prompt()[:120])
"
```

---

## Data Storage and Privacy

All dream data stays local — nothing is sent to any external service by this module.

| Path | Contents |
|---|---|
| `data/dream_journal/dreams_YYYY-MM.jsonl` | Structured dreams — one file per month, append-only |
| `data/dreamer/notebooks/<username>.jsonl` | Free-form dreamer notebook (Discord bot entries) |
| `data/dreams/character_fox.json` | The Fox's persistent memory |
| `data/dreams/character_the_old_tower.json` | The Old Tower's persistent memory |

Notebook files are excluded from version control via `.gitignore`. Do not commit personal dream content to the repo.

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'skills'`**
Run all Python commands from the repo root, not from inside a subdirectory.

**`/dream` command not appearing in Discord**
Confirm the bot synced: look for `[SYNC] Synced N slash commands` in the log. If missing, restart the bot and verify `LANTERN_DISCORD_GUILD_ID` is set.

**Character memories not persisting between runs**
The `data/dreams/` directory must be writable. Check: `ls -la data/dreams/`.

**Docker: dream entries lost on container restart**
Mount the data volume: `-v $(pwd)/data:/app/data`. Without this flag, data written inside the container is discarded when it stops.

**Netlify mirror not responding**
The Netlify mirror (`https://lantern-os-cloud.netlify.app`) is configured but health-check verification is pending operator confirmation. Use `http://127.0.0.1:4177` as the reliable front door.

**Bot starts but cognitive layer unavailable**
The import path for the cognitive layer requires the repo root on `sys.path`. The bot handles this automatically when started via the watchdog script. If running manually, set: `export PYTHONPATH=.`

---

## Related Docs

- `skills/dream_journal/SKILL.md` — Technical spec, evidence discipline, and validation path
- `skills/lucid_dreaming/` — MILD/WBTB protocol scaffolding (planned)
- `skills/bayesian-world-model/SKILL.md` — Belief ledger that Dream Journal feeds into
- `DISCORD-BOT-QUICKSTART.md` — Full bot setup and watchdog configuration
- `docs/LANTERN-LOCAL-LAUNCH-RUNBOOK.md` — Starting the full local stack
- `manifests/cloud-mirrors.json` — Cloud URL status and mirror policy
- `BOT-SETUP-GUIDE.md` — Discord server voice channel and command setup

---

*Last Updated: 2026-06-02 | Author: Founder | Status: Production Ready*
