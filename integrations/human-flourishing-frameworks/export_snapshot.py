#!/usr/bin/env python3
"""
Export HFF world-model state to a JSON snapshot for the Node.js dashboard.

Usage:
    cd integrations/human-flourishing-frameworks
    python export_snapshot.py

Writes: data/snapshot.json
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

DATA_DIR = Path(__file__).parent / "data"
SNAPSHOT_PATH = DATA_DIR / "snapshot.json"


def build_snapshot():
    try:
        from world_model import WorldModel
        from seed_data import ALL_SEED_MEASUREMENTS
    except ImportError as e:
        print(f"[hff] Import error: {e} — writing empty snapshot.")
        return _empty_snapshot()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db_path = str(DATA_DIR / "world_model.db")
    wm = WorldModel(db_path=db_path)

    # Seed if fresh
    if len(wm.beliefs) == 0:
        print(f"[hff] Seeding with {len(ALL_SEED_MEASUREMENTS)} measurements…")
        try:
            wm.update(ALL_SEED_MEASUREMENTS)
        except Exception as ex:
            print(f"[hff] Seed error: {ex}")

    stat = wm.status()
    belief_count = stat.get("belief_count", 0)
    flourishing_scores = stat.get("flourishing_scores", {})

    # Build by_scope for the dashboard table
    by_scope = {
        scope: {
            "score": data.get("score", 0),
            "belief_count": belief_count,
            "population": "—",
        }
        for scope, data in flourishing_scores.items()
    }

    # Top beliefs
    beliefs = [
        {
            "entity": b.entity,
            "domain": b.domain,
            "scope": b.scope,
            "flourishing": round(b.posterior, 4),
            "confidence": round(1.0 - b.uncertainty, 4),
            "last_update": b.last_updated.isoformat() if hasattr(b.last_updated, "isoformat") else str(b.last_updated),
        }
        for b in sorted(wm.beliefs.values(), key=lambda x: 1.0 - x.uncertainty)[:50]
    ]

    avg_flourishing = (
        sum(d.get("score", 0) for d in flourishing_scores.values()) / max(len(flourishing_scores), 1)
        if flourishing_scores else None
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "world": {
            "belief_count": belief_count,
            "sensor_count": stat.get("sensor_count", 0),
            "flourishing": round(avg_flourishing, 4) if avg_flourishing is not None else None,
            "domains": stat.get("domains", []),
            "avg_uncertainty": stat.get("avg_uncertainty"),
            "last_update": stat.get("last_update"),
        },
        "beliefs": beliefs,
        "flourishing": {"by_scope": by_scope},
        "violations": [],
        "agents": [],
        "immutable_rules": 0,
        "adoption": {"verified_nodes": 0, "active_nodes": 0, "total_nodes": 0},
    }


def _empty_snapshot():
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "world": {"belief_count": 0, "sensor_count": 0, "flourishing": None},
        "beliefs": [],
        "flourishing": {"by_scope": {}},
        "violations": [],
        "agents": [],
        "immutable_rules": 0,
        "adoption": {"verified_nodes": 0, "active_nodes": 0, "total_nodes": 0},
    }


if __name__ == "__main__":
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    snap = build_snapshot()
    SNAPSHOT_PATH.write_text(json.dumps(snap, indent=2, default=str), encoding="utf-8")
    bc = snap.get("world", {}).get("belief_count", 0)
    print(f"[hff] Snapshot → {SNAPSHOT_PATH} ({bc} beliefs)")
