"""
Agent Inspector & Self-Monitoring Daemon for Lantern OS

Runs periodic health checks across all configured providers, slots, and dollhouse
segments. Reports to local JSONL log and can trigger agent check-ins.

Usage:
    python scripts/agent_inspector.py --interval 300 --daemon
    python scripts/agent_inspector.py --once --report data/agent-fleet/inspector-latest.json

Environment:
- Reads config/agent-slots.json, config/agent-profiles.json
- Writes data/agent-fleet/inspector-log.jsonl
- Checks data/dollhouse/csf/manifest.json for segment health
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO_ROOT / "config"
DATA_DIR = REPO_ROOT / "data"
LOG_PATH = DATA_DIR / "agent-fleet" / "inspector-log.jsonl"
CHECKIN_MANIFEST_PATH = DATA_DIR / "dollhouse" / "agent-checkin-manifest.json"
CSF_MANIFEST_PATH = DATA_DIR / "dollhouse" / "csf" / "manifest.json"
LISTENER_LOCK_PATH = DATA_DIR / "agent-fleet" / "tesseract-listener.lock.json"


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def append_log(record: Dict[str, Any]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def check_slots() -> List[Dict[str, Any]]:
    slots_path = CONFIG_DIR / "agent-slots.json"
    data = load_json(slots_path)
    slots = data.get("agents", []) if data else []
    results = []
    for slot in slots:
        results.append({
            "id": slot.get("id"),
            "name": slot.get("name"),
            "type": slot.get("type"),
            "status": slot.get("status", "unknown"),
            "port": slot.get("port"),
            "healthcheck_endpoint": slot.get("healthcheck", {}).get("endpoint", "").replace("{port}", str(slot.get("port", "0"))),
        })
    return results


def check_profiles() -> List[Dict[str, Any]]:
    profiles_path = CONFIG_DIR / "agent-profiles.json"
    data = load_json(profiles_path)
    profiles = data.get("profiles", []) if data else []
    results = []
    for prof in profiles:
        missing = [v for v in prof.get("requiredEnvVars", []) if not os.environ.get(v)]
        results.append({
            "id": prof.get("id"),
            "provider": prof.get("provider"),
            "model": prof.get("model"),
            "env_ready": len(missing) == 0,
            "missing_env": missing,
            "capabilities": prof.get("capabilities", []),
        })
    return results


def check_dollhouse() -> Dict[str, Any]:
    manifest_path = DATA_DIR / "dollhouse" / "csf" / "manifest.json"
    manifest = load_json(manifest_path)
    if not manifest:
        return {"status": "no_csf_manifest", "segments": 0}
    return {
        "status": "ok",
        "segments": manifest.get("segments_built", 0),
        "inspectors": len(manifest.get("inspectors", [])),
        "checkin_slots": len(manifest.get("checkin_slots", [])),
        "self_monitoring": manifest.get("self_monitoring", {}),
    }


def inspect_all() -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    slot_report = check_slots()
    profile_report = check_profiles()
    dollhouse_report = check_dollhouse()
    summary = {
        "timestamp": now,
        "run_id": f"inspection-{int(time.time())}",
        "slots": {
            "total": len(slot_report),
            "sleeping": sum(1 for s in slot_report if s["status"] == "sleeping"),
            "active": sum(1 for s in slot_report if s["status"] == "active"),
            "error": sum(1 for s in slot_report if s["status"] == "error"),
        },
        "profiles": {
            "total": len(profile_report),
            "env_ready": sum(1 for p in profile_report if p["env_ready"]),
            "env_missing": sum(1 for p in profile_report if not p["env_ready"]),
        },
        "dollhouse": dollhouse_report,
        "details": {
            "slots": slot_report,
            "profiles": profile_report,
        },
    }
    append_log(summary)
    return summary


def _pid_running(pid: int) -> bool:
    """Return True if the given PID is still running (cross-platform)."""
    if sys.platform == "win32":
        import ctypes
        kernel = ctypes.windll.kernel32
        handle = kernel.OpenProcess(1, False, pid)
        if handle:
            kernel.CloseHandle(handle)
            return True
        return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False


def acquire_listener_lock(interval_seconds: int) -> bool:
    """Try to acquire the listener lock. Returns True if acquired, False if already owned by a running process."""
    LISTENER_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    if LISTENER_LOCK_PATH.exists():
        try:
            with open(LISTENER_LOCK_PATH, "r", encoding="utf-8") as f:
                lock = json.load(f)
            if _pid_running(lock.get("pid", -1)):
                return False
        except Exception:
            pass
    lock = {
        "pid": os.getpid(),
        "acquired_at": datetime.now(timezone.utc).isoformat(),
        "interval_seconds": interval_seconds,
    }
    with open(LISTENER_LOCK_PATH, "w", encoding="utf-8") as f:
        json.dump(lock, f, indent=2)
    return True


def refresh_checkin_manifest(interval_seconds: int) -> Dict[str, Any]:
    """Refresh the agent-checkin-manifest with current listener heartbeat and CSF slots."""
    CHECKIN_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    csf = load_json(CSF_MANIFEST_PATH) or {}
    slots = csf.get("checkin_slots", [])
    if not slots:
        slots = csf.get("paths", [])
        slots = [
            {
                "slot_id": f"checkin-{i}",
                "segment_id": str(s),
                "interval_minutes": 30,
                "agent_type": "dollhouse_monitor",
                "status": "active",
            }
            for i, s in enumerate(slots)
        ]
    manifest = {
        "generated_at": now.isoformat(),
        "listener": {
            "agent": "agent_inspector",
            "status": "active",
            "interval_seconds": interval_seconds,
            "heartbeat_at": now.isoformat(),
            "pid": os.getpid(),
        },
        "slots": slots,
    }
    with open(CHECKIN_MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return manifest


def listener_mode(interval_seconds: int) -> None:
    """Run as the Tesseract listener: acquire lock, refresh manifest, and sleep."""
    if not acquire_listener_lock(interval_seconds):
        print("[Listener] Lock already held by another process. Exiting.")
        sys.exit(1)
    print(f"[Listener] Lock acquired. PID: {os.getpid()}. Interval: {interval_seconds}s")
    while True:
        refresh_checkin_manifest(interval_seconds)
        print(f"[Listener] Heartbeat written. Sleeping {interval_seconds}s...")
        time.sleep(interval_seconds)


def daemon_mode(interval_seconds: int) -> None:
    print(f"[Agent Inspector] Daemon started. Interval: {interval_seconds}s")
    while True:
        summary = inspect_all()
        print(f"[{summary['timestamp']}] Slots: {summary['slots']['total']} | Profiles ready: {summary['profiles']['env_ready']} | Dollhouse: {summary['dollhouse']['status']}")
        time.sleep(interval_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent Inspector & Self-Monitoring")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--daemon", action="store_true", help="Run continuously")
    parser.add_argument("--listener", action="store_true", help="Run as Tesseract listener daemon")
    parser.add_argument("--refresh-checkins", action="store_true", help="Refresh checkin manifest and exit")
    parser.add_argument("--interval", type=int, default=300, help="Daemon interval in seconds")
    parser.add_argument("--report", type=Path, help="Write latest report to JSON file")
    args = parser.parse_args()

    if args.listener:
        listener_mode(args.interval)
    elif args.daemon:
        daemon_mode(args.interval)
    elif args.refresh_checkins:
        manifest = refresh_checkin_manifest(args.interval)
        print(json.dumps(manifest, indent=2))
    else:
        summary = inspect_all()
        print(json.dumps(summary, indent=2))
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            with open(args.report, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)
            print(f"[OK] Report written to {args.report}")


if __name__ == "__main__":
    main()
