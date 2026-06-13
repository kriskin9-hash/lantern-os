# -*- coding: utf-8 -*-
"""
Lantern Discord server setup script.
- Lists all channels with IDs
- Reads existing messages from kickazzkenji
- Creates missing channels
- Posts rewritten messages as the Lantern bot
- Renames channels
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
KICKAZZ_ID = None  # discovered from messages


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
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body_txt = e.read().decode("utf-8", errors="replace")
        if e.code == 429 and retry:
            data = json.loads(body_txt)
            wait = data.get("retry_after", 1) + 0.2
            print(f"  [rate-limit] waiting {wait:.1f}s...")
            time.sleep(wait)
            return api(path, method, body, retry=False)
        return {"error": e.code, "msg": body_txt}


def get_channels():
    chs = api(f"/guilds/{GUILD}/channels")
    cats = {c["id"]: c for c in chs if c["type"] == 4}
    return chs, cats


def get_messages(channel_id, limit=50):
    return api(f"/channels/{channel_id}/messages?limit={limit}")


def send_message(channel_id, content=None, embeds=None):
    body = {}
    if content:
        body["content"] = content
    if embeds:
        body["embeds"] = embeds
    return api(f"/channels/{channel_id}/messages", method="POST", body=body)


def delete_message(channel_id, message_id):
    return api(f"/channels/{channel_id}/messages/{message_id}", method="DELETE")


def create_channel(guild_id, name, channel_type=0, parent_id=None, topic=None, position=None):
    body = {"name": name, "type": channel_type}
    if parent_id:
        body["parent_id"] = parent_id
    if topic:
        body["topic"] = topic
    if position is not None:
        body["position"] = position
    return api(f"/guilds/{guild_id}/channels", method="POST", body=body)


def create_category(guild_id, name, position=None):
    return create_channel(guild_id, name, channel_type=4, position=position)


def rename_channel(channel_id, new_name, new_topic=None):
    body = {"name": new_name}
    if new_topic is not None:
        body["topic"] = new_topic
    return api(f"/channels/{channel_id}", method="PATCH", body=body)


def rename_category(category_id, new_name):
    return api(f"/channels/{category_id}", method="PATCH", body={"name": new_name})


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Lantern Discord Setup ===\n")

    chs, cats = get_channels()

    # Print current structure
    print("--- Current channel structure ---")
    by_parent = {}
    for c in chs:
        pid = c.get("parent_id") or "ROOT"
        by_parent.setdefault(pid, []).append(c)

    def print_category(cat_id, prefix=""):
        cat = next((c for c in chs if c["id"] == cat_id), None)
        if cat:
            print(f"{prefix}[CATEGORY] {cat['name']}  (id={cat['id']})")
        for ch in sorted(by_parent.get(cat_id, []), key=lambda x: x.get("position", 0)):
            t = {0: "text", 2: "voice"}.get(ch["type"], "?")
            print(f"{prefix}  [{t}] {ch['name']}  (id={ch['id']})")

    for cat in sorted(by_parent.get("ROOT", []), key=lambda x: x.get("position", 0)):
        if cat["type"] == 4:
            print_category(cat["id"])
    print()

    # Build lookup by name (lowercase)
    ch_by_name = {c["name"].lower(): c for c in chs}
    cat_by_name = {c["name"].lower(): c for c in chs if c["type"] == 4}

    # ── Step 1: Read existing kickazzkenji messages in #rules ─────────────────
    rules_ch = ch_by_name.get("rules") or ch_by_name.get("📃rules")
    if rules_ch:
        print(f"--- Reading #rules (id={rules_ch['id']}) ---")
        msgs = get_messages(rules_ch["id"], limit=100)
        for m in reversed(msgs):
            author = m.get("author", {})
            print(f"  [{author.get('username')}] {m['id']}: {m['content'][:120]!r}")
            if author.get("username", "").lower() not in ("lantern", "lantern os"):
                KICKAZZ_ID = author.get("id")
        print()

    print("Setup script loaded. Call specific functions to make changes.")
    print("Channel IDs saved — ready for create/rename operations.")
