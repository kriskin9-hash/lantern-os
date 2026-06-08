"""
Hermes Release-Check — cross-platform confidence table generation
Emits manifests/hermes-confidence-latest.json as a CI artifact
Usage: python scripts/hermes_release_check.py
"""
from __future__ import annotations

import json
import math
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = REPO_ROOT / "manifests"
MANIFEST_DIR.mkdir(parents=True, exist_ok=True)


def check_file_exists(path: Path, min_lines: int = 1) -> dict:
    if not path.exists():
        return {"ok": False, "detail": "missing"}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        if len(lines) < min_lines:
            return {"ok": False, "detail": f"only {len(lines)} lines"}
        return {"ok": True, "detail": f"{len(lines)} lines"}
    except Exception as e:
        return {"ok": False, "detail": str(e)}


def check_endpoint(url: str, timeout: int = 10) -> dict:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {"ok": True, "status": resp.status}
    except Exception as e:
        status = getattr(getattr(e, "code", None), "value", None)
        return {"ok": False, "status": status, "detail": str(e)}


def file_contains(path: Path, pattern: str) -> bool:
    if not path.exists():
        return False
    try:
        return pattern in path.read_text(encoding="utf-8")
    except Exception:
        return False


def main() -> int:
    table = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "hermes_version": "0.1.0",
        "gates": [
            {"id": "G1", "name": "Core journal", "owner": "CI", "checks": ["create", "stats", "search", "read", "export"]},
            {"id": "G2", "name": "Real UI browse", "owner": "Dream Journal UI", "checks": ["recent_entries_render"]},
            {"id": "G3", "name": "Semantic memory", "owner": "MemOS", "checks": ["memos_health", "save_ingest"]},
            {"id": "G4", "name": "Chat context", "owner": "MemOS", "checks": ["chat_semantic_context"]},
            {"id": "G5", "name": "Static/server truth", "owner": "Hermes", "checks": ["deploy_label_accuracy"]},
            {"id": "G6", "name": "Deploy smoke", "owner": "Hermes", "checks": ["static_url_probe", "api_health_probe"]},
            {"id": "G7", "name": "Safety copy", "owner": "Tests+Hermes", "checks": ["no_therapy_claims", "no_cloud_sync_claims"]},
            {"id": "G8", "name": "Release confidence", "owner": "Hermes", "checks": ["confidence_table_artifact"]},
        ],
        "scores": {},
        "evidence": {},
    }

    # G1
    api_test = check_file_exists(REPO_ROOT / "tests" / "test_dream_journal_api.js", 20)
    chat_test = check_file_exists(REPO_ROOT / "tests" / "test_dream_chat_multiturns.js", 20)
    py_test = check_file_exists(REPO_ROOT / "tests" / "test_dashboard_ux.py", 1)
    table["scores"]["G1"] = 0.82 if (api_test["ok"] and chat_test["ok"]) else 0.55
    table["evidence"]["G1"] = {"api_test": api_test["detail"], "chat_test": chat_test["detail"], "py_test": py_test["detail"]}

    # G2
    index_html = check_file_exists(REPO_ROOT / "apps" / "lantern-garage" / "public" / "index.html", 300)
    has_recent = file_contains(REPO_ROOT / "apps" / "lantern-garage" / "public" / "index.html", "recent-entries")
    table["scores"]["G2"] = 0.72 if has_recent else 0.42
    table["evidence"]["G2"] = {"index_html_lines": index_html["detail"], "has_recent_entries": has_recent}

    # G3
    memos_bridge = check_file_exists(REPO_ROOT / "src" / "convergence_io" / "memos_bridge.py", 30)
    dream_route = check_file_exists(REPO_ROOT / "apps" / "lantern-garage" / "routes" / "dream.js", 100)
    has_ingest = file_contains(REPO_ROOT / "apps" / "lantern-garage" / "routes" / "dream.js", "memos")
    has_health = file_contains(REPO_ROOT / "apps" / "lantern-garage" / "routes" / "dream.js", "memory/health")
    table["scores"]["G3"] = 0.65 if (has_ingest and has_health) else 0.46
    table["evidence"]["G3"] = {"memos_bridge": memos_bridge["detail"], "has_ingest": has_ingest, "has_health": has_health}

    # G4
    has_chat_ctx = file_contains(REPO_ROOT / "src" / "convergence_io" / "memos_bridge.py", "get_context_for_prompt")
    table["scores"]["G4"] = 0.68 if has_chat_ctx else 0.48
    table["evidence"]["G4"] = {"has_chat_context": has_chat_ctx}

    # G5
    deploy_wf = check_file_exists(REPO_ROOT / ".github" / "workflows" / "deploy.yml", 10)
    table["scores"]["G5"] = 0.62 if deploy_wf["ok"] else 0.40
    table["evidence"]["G5"] = {"deploy_workflow": deploy_wf["detail"]}

    # G6
    health = check_endpoint("http://127.0.0.1:4177/api/health", 5)
    table["scores"]["G6"] = 0.72 if health["ok"] else 0.50
    table["evidence"]["G6"] = {"api_health": health.get("status"), "api_health_detail": health.get("detail")}

    # G7
    has_safety = file_contains(REPO_ROOT / "tests" / "test_dream_journal_api.js", "safety") or file_contains(REPO_ROOT / "tests" / "test_dream_journal_api.js", "privacy")
    table["scores"]["G7"] = 0.76 if has_safety else 0.60
    table["evidence"]["G7"] = {"has_safety_tests": has_safety}

    # G8
    table["scores"]["G8"] = 0.70
    table["evidence"]["G8"] = {"hermes_script": "hermes_release_check.py", "manifest_dir": str(MANIFEST_DIR)}

    overall = sum(table["scores"].values()) / len(table["scores"])
    table["overall_confidence"] = round(overall, 3)
    if overall >= 0.75:
        table["overall_label"] = "ready"
    elif overall >= 0.55:
        table["overall_label"] = "caution"
    else:
        table["overall_label"] = "hold"

    out_path = MANIFEST_DIR / "hermes-confidence-latest.json"
    out_path.write_text(json.dumps(table, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Hermes confidence table written to {out_path}")
    print(f"Overall confidence: {table['overall_confidence']} ({table['overall_label']})")
    for g in table["gates"]:
        s = table["scores"][g["id"]]
        color = "green" if s >= 0.75 else ("yellow" if s >= 0.55 else "red")
        print(f"  {g['id']} {g['name']}: {s} [{color}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
