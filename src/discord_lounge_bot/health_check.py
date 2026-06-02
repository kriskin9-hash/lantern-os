"""
Lantern Discord Bot — External Health Checker

Can be run standalone or imported. Reports:
- Process existence (via PID file)
- Discord API gateway latency ( lightweight GET to /gateway/bot )
- Environment variable completeness
- Notebook directory accessibility

Usage:
    python src/discord_lounge_bot/health_check.py
    python src/discord_lounge_bot/health_check.py --json
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

import urllib.request
import urllib.error


LOG_DIR = Path.home() / ".lantern" / "logs"
PID_FILE = LOG_DIR / "discord-bot.pid"
NOTEBOOK_DIR = Path("data/dreamer/notebooks")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _check_env() -> List[Dict[str, str]]:
    checks = []
    required = [
        ("DISCORD_BOT_TOKEN", "Discord bot token"),
        ("LANTERN_DISCORD_GUILD_ID", "Guild ID"),
        ("LANTERN_DISCORD_CHANNEL_ID", "Channel ID"),
    ]
    for var, desc in required:
        val = os.getenv(var, "").strip()
        if val:
            checks.append({"name": var, "status": "pass", "message": f"{desc} is set"})
        else:
            checks.append({"name": var, "status": "fail", "message": f"{desc} is missing"})
    return checks


def _check_process() -> Dict[str, Any]:
    if not PID_FILE.exists():
        return {"name": "bot_process", "status": "fail", "message": f"PID file missing: {PID_FILE}"}
    try:
        pid = int(PID_FILE.read_text().strip())
    except (ValueError, OSError) as exc:
        return {"name": "bot_process", "status": "fail", "message": f"Cannot read PID file: {exc}"}

    # Cross-platform process check
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(1, False, pid)
            if handle:
                kernel32.CloseHandle(handle)
                return {"name": "bot_process", "status": "pass", "message": f"Process {pid} is running"}
            else:
                return {"name": "bot_process", "status": "fail", "message": f"Process {pid} not found"}
        except Exception as exc:
            return {"name": "bot_process", "status": "warn", "message": f"Could not verify process {pid}: {exc}"}
    else:
        try:
            os.kill(pid, 0)
            return {"name": "bot_process", "status": "pass", "message": f"Process {pid} is running"}
        except OSError:
            return {"name": "bot_process", "status": "fail", "message": f"Process {pid} not running"}


def _check_discord_latency() -> Dict[str, Any]:
    token = os.getenv("DISCORD_BOT_TOKEN", "").strip()
    if not token:
        return {"name": "discord_latency", "status": "skip", "message": "No token — skipping Discord API check"}

    req = urllib.request.Request(
        "https://discord.com/api/v10/gateway/bot",
        headers={"Authorization": f"Bot {token}"},
    )
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            latency_ms = round((time.time() - start) * 1000, 1)
            shards = body.get("shards", "?")
            return {
                "name": "discord_latency",
                "status": "pass",
                "message": f"Discord API OK ({latency_ms}ms) | shards: {shards}",
                "latency_ms": latency_ms,
            }
    except urllib.error.HTTPError as exc:
        return {"name": "discord_latency", "status": "fail", "message": f"Discord API error: HTTP {exc.code}"}
    except Exception as exc:
        return {"name": "discord_latency", "status": "fail", "message": f"Discord API unreachable: {exc}"}


def _check_notebook_dir() -> Dict[str, Any]:
    try:
        NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
        return {"name": "notebook_dir", "status": "pass", "message": f"Notebook dir ready: {NOTEBOOK_DIR}"}
    except OSError as exc:
        return {"name": "notebook_dir", "status": "fail", "message": f"Notebook dir error: {exc}"}


def run_checks() -> Dict[str, Any]:
    checks: List[Dict[str, Any]] = []
    checks.extend(_check_env())
    checks.append(_check_process())
    checks.append(_check_discord_latency())
    checks.append(_check_notebook_dir())

    pass_count = sum(1 for c in checks if c.get("status") == "pass")
    warn_count = sum(1 for c in checks if c.get("status") == "warn")
    fail_count = sum(1 for c in checks if c.get("status") in ("fail",))

    return {
        "generatedAt": _now(),
        "checks": checks,
        "summary": {"pass": pass_count, "warn": warn_count, "fail": fail_count},
        "healthy": fail_count == 0,
    }


if __name__ == "__main__":
    output_json = "--json" in sys.argv
    result = run_checks()
    if output_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Lantern Discord Bot Health Check — {_now()}")
        print(f"Pass: {result['summary']['pass']} | Warn: {result['summary']['warn']} | Fail: {result['summary']['fail']}")
        for check in result["checks"]:
            status = check["status"].upper()
            print(f"[{status}] {check['name']} — {check['message']}")
        print(f"\nOverall: {'HEALTHY' if result['healthy'] else 'UNHEALTHY'}")

    sys.exit(0 if result["healthy"] else 1)
