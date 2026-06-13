# -*- coding: utf-8 -*-
"""
Lantern Discord NA 1 — Full convergence script.
Runs all server setup: channel creates/renames, message rewrites.
"""
import urllib.request
import urllib.error
import json
import os
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[1]
for f in [".env", ".env.local"]:
    p = REPO_ROOT / f
    if p.exists():
        for line in p.read_text("utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() and k.strip() not in os.environ:
                os.environ[k.strip()] = v.strip()

TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
GUILD = "1503853513023950959"

# Known channel IDs
CH_RULES          = "1511683144913256581"
CH_ANNOUNCEMENTS  = "1503853513485058162"
CH_FOUNDER_AFTER  = "1509188995698131004"
CH_ARCHIVE_TEXT   = "1511131734123483277"
CH_CHAT           = "1511678337460863036"
CH_MEMES          = "1511681653741846668"
CH_ART            = "1511892721160163338"
CH_RESOURCES      = "1503853513485058163"
CH_QUEUE          = "1511134570035286038"
CH_KEYSTONE_DOORS = "1511890790127767712"

CAT_INFORMATION   = "1503853513485058160"
CAT_TEXT_CHANNELS = "1503853513485058164"
CAT_VOICE         = "1503853513485058168"

VC_FOUNDER_HOURS  = "1509188951804739675"


def api(path, method="GET", body=None, retry=True):
    url = f"https://discord.com/api/v10{path}"
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(
        url, data=data,
        headers={
            "Authorization": f"Bot {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "LanternBot/1.0",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        body_txt = e.read().decode("utf-8", errors="replace")
        if e.code == 429 and retry:
            try:
                wait = json.loads(body_txt).get("retry_after", 1) + 0.3
            except Exception:
                wait = 1.3
            print(f"  [rate-limit] {wait:.1f}s...")
            time.sleep(wait)
            return api(path, method, body, retry=False)
        return {"error": e.code, "msg": body_txt}


def post(channel_id, content=None, embeds=None):
    body = {}
    if content:
        body["content"] = content
    if embeds:
        body["embeds"] = embeds
    r = api(f"/channels/{channel_id}/messages", method="POST", body=body)
    if "error" in r:
        print(f"  ✗ post failed: {r}")
    else:
        print(f"  ✓ posted msg {r.get('id')}")
    time.sleep(0.6)
    return r


def delete_msg(channel_id, message_id):
    r = api(f"/channels/{channel_id}/messages/{message_id}", method="DELETE")
    if r and "error" in r:
        print(f"  ✗ delete {message_id} failed: {r.get('error')} {r.get('msg','')[:60]}")
        return False
    print(f"  ✓ deleted {message_id}")
    time.sleep(0.4)
    return True


def get_messages(channel_id, limit=100):
    r = api(f"/channels/{channel_id}/messages?limit={limit}")
    if isinstance(r, list):
        return r
    return []


def rename_channel(channel_id, name, topic=None):
    body = {"name": name}
    if topic is not None:
        body["topic"] = topic
    r = api(f"/channels/{channel_id}", method="PATCH", body=body)
    if "error" in r:
        print(f"  ✗ rename failed: {r.get('error')} — {r.get('msg','')[:80]}")
        return False
    print(f"  ✓ renamed → #{r.get('name')}")
    time.sleep(0.4)
    return True


def create_channel(name, parent_id, topic=None, position=None, ch_type=0):
    body = {"name": name, "type": ch_type, "parent_id": parent_id}
    if topic:
        body["topic"] = topic
    if position is not None:
        body["position"] = position
    r = api(f"/guilds/{GUILD}/channels", method="POST", body=body)
    if "error" in r:
        print(f"  ✗ create #{name} failed: {r.get('error')} — {r.get('msg','')[:80]}")
        return None
    print(f"  ✓ created #{r.get('name')} (id={r.get('id')})")
    time.sleep(0.6)
    return r


def create_category(name, position=None):
    body = {"name": name, "type": 4}
    if position is not None:
        body["position"] = position
    r = api(f"/guilds/{GUILD}/channels", method="POST", body=body)
    if "error" in r:
        print(f"  ✗ create category {name} failed: {r.get('error')}")
        return None
    print(f"  ✓ created category [{r.get('name')}] (id={r.get('id')})")
    time.sleep(0.6)
    return r


# ── Content ────────────────────────────────────────────────────────────────────

RULES_CONTENT = """@everyone

# 🌌 Lantern Dream Journal — Server Rules

Welcome. This is a space for dreamers, builders, and explorers. A few rules keep the room clear.

---

**1. Respect the room.**
Treat every member with care. No harassment, targeted cruelty, or bad-faith arguments. Disagreement is welcome — contempt isn't.

**2. Dreams are personal.**
Content shared here may include strange, symbolic, or emotionally raw material. That's normal and expected. Do not mock, diagnose, or exploit someone else's dream content. This is not therapy or medical advice.

**3. Use the right channels.**
→ `#🚀start-here` — orientation and quick-start guide
→ `#🤖bot-commands` — test `!help`, `!threedoors`, slash commands here
→ `#📝dream-journal` — share dream notes (Deep Dreamer+ tier)
→ `#🆘support` — access issues, tier questions, payment help
→ `#💬chat` — general conversation
→ `#🖼️art` — visual art, dream sketches, scene images
→ `#📰resources` — links, docs, research
→ `#📣announcements` — Lantern OS updates (read-only)

**4. Respect role access.**
Three tiers exist for a reason. Don't attempt to bypass role gates, flood commands into channels that aren't meant for bot use, or share gated content publicly.

**5. Don't spam the bot.**
Lantern runs on local hardware. Repeated command floods, automated scripts, or prompt injection attempts will result in a mute. If something fails, report it in `#🆘support` rather than retrying in a loop.

**6. Keep content legal and safe.**
No illegal material, sexual content involving minors, doxxing, malware, scams, or instructions for real-world harm. Violators are removed immediately without appeal.

**7. No financial advice.**
Lantern's wallet and status tools are for personal use only. Nothing here constitutes investment, financial, or legal advice.

---

*Rules may be updated. Major changes announced in `#📣announcements`. If something's unclear — ask in `#🆘support`.*"""

START_HERE_CONTENT = """# 🚀 Welcome to Lantern Discord NA 1

You've arrived at the **Lantern OS** community — a local-first AI dream journal, convergence cockpit, and creative workspace.

---

## What is Lantern OS?

Lantern OS is a personal AI system built around one core idea: **your inner world deserves the same infrastructure as the outer one.**

The flagship feature is the **Dream Journal** — a freeform RP chat interface where you can record dreams, explore symbolic patterns, and interact with AI agents that know your notebook.

---

## How to get started

**Step 1 — Pick a tier**
→ `/subscribe` to see membership options
→ Free tier (Wanderer) includes: `/status`, `/help`, `/threedoors`
→ Deep Dreamer ($20/mo): dream notebook, notes, wishes, recall
→ Synthesasia Guild ($200/mo): agent queue, workspace commands, dispatch

**Step 2 — Try the Three Doors**
The Three Doors is a short narrative dream-walk. Start it anywhere:
```
!threedoors
!choose A
```
Or use the slash commands `/threedoors` and `/threedoors-choose`.

**Step 3 — Save something**
```
!dream I stood at the edge of a city I didn't recognise
!note the lantern color was different this time
!wish I want to remember more clearly
```

**Step 4 — Recall it**
```
!recall
!recall lantern
```

---

## Channels

| Channel | Purpose |
|---|---|
| `#📣announcements` | Lantern OS release notes & updates |
| `#🤖bot-commands` | Safe space for bot testing |
| `#💬chat` | General conversation |
| `#📝dream-journal` | Share dream entries (Deep Dreamer+) |
| `#🖼️art` | Dream art, scene images |
| `#📰resources` | Links, documentation, research |
| `#🚪three-doors` | Three Doors game discussion & lore |
| `#👁️agent-status` | Live AI agent fleet visibility |
| `#🆘support` | Access issues & help |

---

*Built by Alex Place. Powered by local-first AI, Ollama, and a lot of dreams.*
*Bot: Lantern#2027 | System: lantern-garage@4177*"""

ANNOUNCEMENTS_INTRO = """📣 **Lantern OS — Announcements**

This channel carries official updates: releases, downtime notices, feature launches, and tier changes.

**Subscribe** to this channel (right-click → Notification Settings → All Messages) to stay current.

---

🌿 *Lantern OS v0.2-infinite-cube is live.*
Dream Journal, Three Doors, notebook system, and bot commands are all online.
Type `!help` or `/help` in any channel to get started."""

BOT_COMMANDS_INTRO = """🤖 **Bot Commands — Test Zone**

Use this channel to explore Lantern bot commands without cluttering other spaces.

**Text commands (prefix `!`)**
```
!help              — full command list
!status            — health check + your tier
!threedoors        — enter the Three Doors dream game
!choose A          — choose door A
!dream <text>      — save a dream
!note <text>       — save a note
!wish <text>       — save a wish
!recall            — your last 5 entries
!recall <keyword>  — search notebook
!wallet            — your tier info
!mirror            — mirror all notebook facets
!subscribe         — subscription info
```

**Slash commands (type `/` in chat)**
`/threedoors` `/threedoors-choose` `/dream` `/note` `/wish` `/recall` `/wallet` `/mirror` `/status` `/help` `/subscribe`

---

*Commands are gated by tier. See `#🚀start-here` for tier info.*"""

DREAM_JOURNAL_INTRO = """📝 **Dream Journal — Community Space**

Share dream entries, fragments, symbols, and sequences here. Deep Dreamer+ tier access.

---

**How to post**
Write freely — there's no required format. Dates, feelings, symbols, recurring themes — all welcome.

If you want to save privately to your notebook instead, use `/dream` or `!dream` — those entries are yours alone.

---

*Be gentle with what others share here. Dreams are personal.*"""

SUPPORT_INTRO = """🆘 **Support**

Use this channel for:
→ Tier access issues (role not applied after subscribing)
→ Bot not responding or wrong tier shown
→ Payment questions
→ Feature requests
→ Bug reports

**Quick checks first:**
```
!status    — is the bot online?
!wallet    — is your tier showing correctly?
```

If the bot shows the wrong tier after subscribing, ping **@admin** with your Patreon/Ko-fi receipt.

---

*Response time: best-effort, usually same day.*"""

KEYSTONE_LORE = """🚪 **Three Doors — Game & Lore**

This channel is for Three Doors game discussion, lore, door theories, and scene art.

**Play anywhere with:**
```
!threedoors
!choose A   (or B or C)
```
Or: `/threedoors` then `/threedoors-choose door:A`

---

**Current door map (spoilers)**
> The Moss Door leads to the Burrow, the Sunken Bell, and the Little Crown.
> Each door has a fox companion who remembers where you've been.
> The path is circular — there's no final room. Only the next door.

---

*Share your scenes, choices, and what you found on the other side.*"""

QUEUE_INTRO = """👁️ **Agent Status**

Live visibility into the Lantern OS AI agent fleet and task queue.

→ **36 designed ring slots** + 64 elastic pool target
→ Active agents post status here automatically
→ Use `/queue` (Synthesasia Guild+) for detailed intake

---

*Read-only for most members. Agent logs stream here in real time.*"""


# ── Runner ─────────────────────────────────────────────────────────────────────

def run():
    print("\n=== Lantern Discord Convergence ===\n")

    # ── Step 1: Rename channels ──────────────────────────────────────────────
    print("--- Step 1: Rename channels ---")
    rename_channel(CAT_TEXT_CHANNELS, "Community")
    rename_channel(CH_QUEUE, "👁️agent-status", topic="Live AI agent fleet queue and task visibility.")
    rename_channel(CH_KEYSTONE_DOORS, "🚪three-doors", topic="Three Doors game discussion, door lore, and scene art.")
    rename_channel(CH_FOUNDER_AFTER, "🔐founder-lounge", topic="Private space for Founder-tier members.")
    rename_channel(CH_RULES, "📋rules", topic="Server rules for Lantern Discord NA 1.")
    rename_channel(CH_ANNOUNCEMENTS, "📣announcements", topic="Official Lantern OS release notes and updates.")
    rename_channel(CH_RESOURCES, "📰resources", topic="Links, documentation, and research.")
    rename_channel(CH_ART, "🖼️art", topic="Dream art, scene images, and visual creativity.")
    rename_channel(VC_FOUNDER_HOURS, "🔐 Founder Hours")
    print()

    # ── Step 2: Create missing channels ─────────────────────────────────────
    print("--- Step 2: Create missing channels ---")

    start_here = create_channel(
        "🚀start-here", parent_id=CAT_INFORMATION,
        topic="Welcome to Lantern OS — start here for orientation.", position=0,
    )
    support_ch = create_channel(
        "🆘support", parent_id=CAT_INFORMATION,
        topic="Access issues, tier questions, bug reports.",
    )
    bot_commands_ch = create_channel(
        "🤖bot-commands", parent_id=CAT_TEXT_CHANNELS,
        topic="Safe space for testing bot commands. Use !help to get started.",
    )

    # Dream Space category + dream-journal channel
    dream_cat = create_category("Dream Space", position=10)
    dream_journal_ch = None
    if dream_cat and not dream_cat.get("error"):
        dream_journal_ch = create_channel(
            "📝dream-journal", parent_id=dream_cat["id"],
            topic="Share dream entries publicly (Deep Dreamer+ tier).",
        )
    print()

    # ── Step 3: Post new content as Lantern bot ──────────────────────────────
    print("--- Step 3: Post new content ---")

    print("  → #📋rules")
    post(CH_RULES, RULES_CONTENT)

    if start_here and not start_here.get("error"):
        print("  → #🚀start-here")
        post(start_here["id"], START_HERE_CONTENT)

    print("  → #📣announcements")
    msgs = get_messages(CH_ANNOUNCEMENTS, limit=5)
    if not any(m.get("author", {}).get("username") == "Lantern" for m in msgs):
        post(CH_ANNOUNCEMENTS, ANNOUNCEMENTS_INTRO)

    if bot_commands_ch and not bot_commands_ch.get("error"):
        print("  → #🤖bot-commands")
        post(bot_commands_ch["id"], BOT_COMMANDS_INTRO)

    if dream_journal_ch and not dream_journal_ch.get("error"):
        print("  → #📝dream-journal")
        post(dream_journal_ch["id"], DREAM_JOURNAL_INTRO)

    if support_ch and not support_ch.get("error"):
        print("  → #🆘support")
        post(support_ch["id"], SUPPORT_INTRO)

    print("  → #🚪three-doors")
    post(CH_KEYSTONE_DOORS, KEYSTONE_LORE)

    print("  → #👁️agent-status")
    post(CH_QUEUE, QUEUE_INTRO)
    print()

    # ── Step 4: Delete old kickazzkenji messages ─────────────────────────────
    print("--- Step 4: Clean up old messages ---")

    # Messages to delete from #rules
    old_rule_msgs = [
        "1511902252225396767",  # original kickazzkenji rules
        "1511903062736769215",  # empty kickazzkenji message
        "1513961945181720646",  # test guide text in rules
        "1513963896489246790",  # empty Lantern message
        "1513965602472202431",  # !help test
        "1513966575693201592",  # !help test
        "1513966583079239772",  # Lantern !help response (now replaced)
    ]
    print(f"  Attempting to delete {len(old_rule_msgs)} old messages from #rules...")
    deleted, failed = 0, []
    for mid in old_rule_msgs:
        if delete_msg(CH_RULES, mid):
            deleted += 1
        else:
            failed.append(mid)

    if failed:
        print(f"\n  ⚠ {len(failed)} messages need manual deletion (bot lacks Manage Messages).")
        print("  To grant permission, re-invite with:")
        new_perms = 85056 + 16 + 8192  # + Manage Channels + Manage Messages
        print(f"  https://discord.com/api/oauth2/authorize?client_id=1503872865366442205&permissions={new_perms}&scope=bot%20applications.commands")
        print("  IDs to delete manually:")
        for mid in failed:
            print(f"    {mid}")

    print("\n=== Convergence complete ===")


if __name__ == "__main__":
    run()
