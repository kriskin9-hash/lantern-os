#!/usr/bin/env python3
"""
Family-Specific Lantern Configuration

Generates Lantern config files per family (A, B, C) with local settings.
Stores in ~/.lantern/families/ — local on each operator's PC.

Creates family-specific:
- Parental controls (age gates, content filters)
- Media curator preferences (music, audiobooks, videos)
- Voice settings (local STT sensitivity, language)
- Dashboard appearance (kids' names, color scheme)

Usage:
  python scripts/family-lantern-config.py create-config A
  python scripts/family-lantern-config.py set-curator A --kids-age 8-12
  python scripts/family-lantern-config.py export A > family-a-config.json
"""

import json
from pathlib import Path
from datetime import datetime
import sys

LANTERN_CONFIG_DIR = Path.home() / ".lantern" / "families"


def create_family_config(family_id: str, kids_names: list = None):
    """Create default Lantern config for a family."""
    LANTERN_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    config = {
        "family_id": family_id,
        "created_at": datetime.now().isoformat(),
        "parental_controls": {
            "enabled": True,
            "kids_mode": True,
            "max_session_hours": 3,
            "daily_screen_time_limit": 4,
            "age_gate": 13,
        },
        "voice_settings": {
            "stt_engine": "vosk",
            "stt_sensitivity": "medium",
            "language": "en-US",
            "microphone_enabled": True,
            "output_voice": "system-default",
        },
        "media_curator": {
            "enabled": True,
            "content_types": ["audio", "audiobooks", "educational-video"],
            "sources": [
                "cc-licensed",
                "public-domain",
                "internet-archive",
                "wikimedia",
            ],
            "filter_explicit": True,
            "age_appropriate": True,
        },
        "dashboard": {
            "theme": "light",
            "text_size": "normal",
            "kids_names": kids_names or [f"Child {i+1}" for i in range(2)],
            "show_timer": True,
            "show_usage_stats": False,  # parents only
        },
        "ai_providers": {
            "primary": "claude",
            "fallback": "gemini",
            "offline_fallback": "local-lm-studio",
        },
        "privacy": {
            "no_cloud_by_default": True,
            "local_storage_only": True,
            "no_tracking": True,
            "no_analytics": True,
        },
    }

    config_file = LANTERN_CONFIG_DIR / f"family-{family_id}-config.json"
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

    print(f"[OK] Created config for Family {family_id}")
    print(f"     Path: {config_file}")
    return config


def set_curator_settings(family_id: str, kids_age: str = None):
    """Set media curator preferences based on kids' age."""
    config_file = LANTERN_CONFIG_DIR / f"family-{family_id}-config.json"

    if not config_file.exists():
        print(f"[ERROR] Config not found for Family {family_id}")
        return

    with open(config_file) as f:
        config = json.load(f)

    # Age-appropriate curator defaults
    age_settings = {
        "0-5": {
            "content_types": ["audio", "nature-sounds"],
            "sources": ["wikimedia", "public-domain"],
            "filter_explicit": True,
            "max_session_hours": 1,
        },
        "6-10": {
            "content_types": ["audio", "educational-audio", "audiobooks"],
            "sources": ["internet-archive", "wikimedia", "public-domain"],
            "filter_explicit": True,
            "max_session_hours": 2,
        },
        "11-16": {
            "content_types": ["audio", "audiobooks", "educational-video"],
            "sources": [
                "internet-archive",
                "wikimedia",
                "public-domain",
                "cc-licensed",
            ],
            "filter_explicit": True,
            "max_session_hours": 3,
        },
        "17+": {
            "content_types": ["audio", "audiobooks", "video", "podcasts"],
            "sources": ["internet-archive", "public-domain", "cc-licensed"],
            "filter_explicit": False,
            "max_session_hours": 8,
        },
    }

    if kids_age and kids_age in age_settings:
        settings = age_settings[kids_age]
        config["media_curator"].update(
            {
                "content_types": settings["content_types"],
                "sources": settings["sources"],
                "filter_explicit": settings["filter_explicit"],
            }
        )
        config["parental_controls"]["max_session_hours"] = settings[
            "max_session_hours"
        ]

    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

    print(f"[OK] Updated curator settings for Family {family_id} (age: {kids_age})")


def export_config(family_id: str):
    """Export family config as JSON."""
    config_file = LANTERN_CONFIG_DIR / f"family-{family_id}-config.json"

    if not config_file.exists():
        print(f"[ERROR] Config not found for Family {family_id}")
        return

    with open(config_file) as f:
        config = json.load(f)
    return json.dumps(config, indent=2)


def list_configs():
    """List all family configs."""
    LANTERN_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    configs = list(LANTERN_CONFIG_DIR.glob("family-*-config.json"))

    if not configs:
        print("No family configs found")
        return

    print("Family Lantern Configurations:")
    for config_file in sorted(configs):
        with open(config_file) as f:
            config = json.load(f)
        fid = config.get("family_id")
        provider = config.get("ai_providers", {}).get("primary")
        privacy = config.get("privacy", {}).get("no_cloud_by_default")
        print(
            f"  Family {fid:<3} | Provider: {provider:<8} | Cloud-free: {privacy}"
        )


def main():
    """CLI interface."""
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1]

    if command == "create-config":
        family_id = sys.argv[2] if len(sys.argv) > 2 else "A"
        create_family_config(family_id)

    elif command == "set-curator":
        family_id = sys.argv[2] if len(sys.argv) > 2 else "A"
        age = sys.argv[4] if len(sys.argv) > 4 else "6-10"
        set_curator_settings(family_id, age)

    elif command == "export":
        family_id = sys.argv[2] if len(sys.argv) > 2 else "A"
        print(export_config(family_id))

    elif command == "list":
        list_configs()

    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
