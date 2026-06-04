#!/usr/bin/env python3
"""
Family Setup Manager — Local Configuration for Lantern Testing

Manages family profiles (A, B, C) with local PII storage (never in repos).
Generates per-family setup scripts and tracking.

Storage: ~/.foundry/families.json (on disk, never committed)

Usage:
  python scripts/family-setup.py init-family A --dwelling "van" --kids 2
  python scripts/family-setup.py setup A
  python scripts/family-setup.py list
  python scripts/family-setup.py status A
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

CONFIG_DIR = Path.home() / ".foundry"
FAMILIES_FILE = CONFIG_DIR / "families.json"


class FamilyManager:
    """Manage family profiles for Lantern testing."""

    def __init__(self):
        self.families = self._load_families()

    def _load_families(self) -> Dict:
        """Load family data from disk."""
        if FAMILIES_FILE.exists():
            with open(FAMILIES_FILE) as f:
                return json.load(f)
        return {"families": {}}

    def _save_families(self):
        """Save family data to disk."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(FAMILIES_FILE, "w") as f:
            json.dump(self.families, f, indent=2)

    def init_family(
        self,
        family_id: str,
        dwelling_type: str = "van",
        kids_count: int = 0,
        internet_type: str = "starlink",
    ):
        """Initialize a new family profile."""
        if family_id in self.families.get("families", {}):
            print(f"Family {family_id} already exists")
            return

        self.families.setdefault("families", {})[family_id] = {
            "id": family_id,
            "dwelling_type": dwelling_type,  # van, bus, farm, house
            "kids_count": kids_count,
            "internet_type": internet_type,
            "status": "initialized",
            "created_at": datetime.now().isoformat(),
            "lantern_installed": False,
            "first_run_date": None,
            "usage_hours": 0,
            "feedback": [],
            "media_curator_enabled": False,
            "local_models": [],
        }
        self._save_families()
        print(f"[OK] Family {family_id} initialized")
        print(f"  Dwelling: {dwelling_type}")
        print(f"  Kids: {kids_count}")
        print(f"  Internet: {internet_type}")

    def generate_setup_script(self, family_id: str) -> str:
        """Generate per-family setup script."""
        if family_id not in self.families.get("families", {}):
            return f"Family {family_id} not found"

        family = self.families["families"][family_id]
        script = f"""#!/bin/bash
# Lantern Setup for Family {family_id}
# Dwelling: {family['dwelling_type']}
# Kids: {family['kids_count']}
# Internet: {family['internet_type']}

echo "=== Lantern Setup for Family {family_id} ==="
echo ""
echo "Step 1: Installing Lantern..."
cd ~/Documents/human-flourishing-frameworks
pip install -r requirements.txt

echo ""
echo "Step 2: Starting Lantern Desktop..."
python apps/lantern-desktop/lantern_desktop.py

echo ""
echo "Setup complete! Lantern is running."
echo "Configuration saved to ~/.foundry/families.json"
"""
        return script

    def record_installation(self, family_id: str):
        """Record that Lantern was installed for a family."""
        if family_id not in self.families.get("families", {}):
            print(f"Family {family_id} not found")
            return

        family = self.families["families"][family_id]
        family["lantern_installed"] = True
        family["first_run_date"] = datetime.now().isoformat()
        family["status"] = "active"
        self._save_families()
        print(f"[OK] Recorded installation for Family {family_id}")

    def add_feedback(self, family_id: str, feedback: str):
        """Add feedback from a family."""
        if family_id not in self.families.get("families", {}):
            print(f"Family {family_id} not found")
            return

        family = self.families["families"][family_id]
        family["feedback"].append(
            {"timestamp": datetime.now().isoformat(), "text": feedback}
        )
        self._save_families()
        print(f"[OK] Recorded feedback for Family {family_id}")

    def update_usage(self, family_id: str, hours: float):
        """Update usage hours for a family."""
        if family_id not in self.families.get("families", {}):
            print(f"Family {family_id} not found")
            return

        family = self.families["families"][family_id]
        family["usage_hours"] += hours
        self._save_families()
        print(f"[OK] Updated usage for Family {family_id}: +{hours} hours")

    def list_families(self) -> Dict:
        """List all families."""
        return self.families.get("families", {})

    def get_family_status(self, family_id: str) -> Dict:
        """Get detailed status for a family."""
        if family_id not in self.families.get("families", {}):
            return {"error": f"Family {family_id} not found"}

        family = self.families["families"][family_id]
        return {
            "id": family_id,
            "dwelling": family.get("dwelling_type"),
            "kids": family.get("kids_count"),
            "internet": family.get("internet_type"),
            "status": family.get("status"),
            "installed": family.get("lantern_installed"),
            "first_run": family.get("first_run_date"),
            "usage_hours": family.get("usage_hours"),
            "feedback_count": len(family.get("feedback", [])),
            "media_curator": family.get("media_curator_enabled"),
        }

    def get_summary(self) -> Dict:
        """Get summary statistics across all families."""
        families = self.families.get("families", {})
        active = len([f for f in families.values() if f.get("status") == "active"])
        installed = len([f for f in families.values() if f.get("lantern_installed")])
        total_usage = sum(f.get("usage_hours", 0) for f in families.values())

        return {
            "total_families": len(families),
            "active_families": active,
            "installed_count": installed,
            "total_usage_hours": total_usage,
            "average_kids": (
                sum(f.get("kids_count", 0) for f in families.values()) / len(families)
                if families
                else 0
            ),
        }


def main():
    """CLI interface."""
    mgr = FamilyManager()

    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1]

    if command == "init-family":
        family_id = sys.argv[2] if len(sys.argv) > 2 else "A"
        dwelling = sys.argv[4] if len(sys.argv) > 4 else "van"
        kids = int(sys.argv[6]) if len(sys.argv) > 6 else 0
        internet = sys.argv[8] if len(sys.argv) > 8 else "starlink"
        mgr.init_family(family_id, dwelling, kids, internet)

    elif command == "setup":
        family_id = sys.argv[2] if len(sys.argv) > 2 else "A"
        script = mgr.generate_setup_script(family_id)
        print(script)

    elif command == "installed":
        family_id = sys.argv[2] if len(sys.argv) > 2 else "A"
        mgr.record_installation(family_id)

    elif command == "feedback":
        family_id = sys.argv[2] if len(sys.argv) > 2 else "A"
        feedback = " ".join(sys.argv[4:]) if len(sys.argv) > 4 else "No feedback"
        mgr.add_feedback(family_id, feedback)

    elif command == "usage":
        family_id = sys.argv[2] if len(sys.argv) > 2 else "A"
        hours = float(sys.argv[4]) if len(sys.argv) > 4 else 0
        mgr.update_usage(family_id, hours)

    elif command == "list":
        families = mgr.list_families()
        if not families:
            print("No families configured yet")
            return
        for fid, fdata in families.items():
            status = "[X]" if fdata.get("lantern_installed") else "[ ]"
            print(
                f"  {status} Family {fid:<3} | {fdata.get('dwelling_type'):<8} | {fdata.get('kids_count')} kids | {fdata.get('usage_hours')} hours"
            )

    elif command == "status":
        family_id = sys.argv[2] if len(sys.argv) > 2 else "A"
        status = mgr.get_family_status(family_id)
        print(f"\nFamily {family_id} Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")

    elif command == "summary":
        summary = mgr.get_summary()
        print(f"\nFamily Testing Summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")

    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
