#!/usr/bin/env python3
"""
Lantern Off-Grid Families — Outreach Service

Generates, tracks, and manages outreach messages locally without storing PII in repos.
Configuration stored at ~/.foundry/outreach-config.json (on disk, never committed to git).

Usage:
  python scripts/outreach-service.py generate --segment van-family --count 3
  python scripts/outreach-service.py track --contact "John Doe" --status positive
  python scripts/outreach-service.py list --status pending
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Configuration
CONFIG_DIR = Path.home() / ".foundry"
CONFIG_FILE = CONFIG_DIR / "outreach-config.json"


class OutreachService:
    """Local outreach message generator and tracker."""

    # Message templates by segment (depersonalized, role-based)
    TEMPLATES = {
        "van-family": [
            "Hi {name} — quick question. You're doing the van/bus life with kids, right? "
            "We're building something called Lantern: local-first AI chat + music for families. "
            "Kids can talk to Claude or Gemini offline, ask homework questions, listen to unlimited free music. "
            "Works on Starlink (no cloud required). We're testing with families like yours. "
            "Want early access? Honest feedback only, no pressure.",

            "Hey {name} — remember when we talked about needing privacy-first tools for the kids? "
            "Built a local-first AI chat (Lantern) that works on Starlink, no cloud, no tracking. "
            "We're testing it with van/farm families. Want to be one of the first?",

            "{name} — we've been working on something for families traveling in vans/buses: Lantern. "
            "Keeps kids entertained + learning when you're off-grid. Local chat with AI, parent controls, works on Starlink. "
            "We'd love feedback from someone actually living this. Interested in trying it?",
        ],
        "community": [
            "Hi {name} — we're developing Lantern for homeschooling and alternative education communities. "
            "It's a local-first AI chat + media curator designed for kids with zero tracking, zero ads, full parental curation. "
            "Works offline on Starlink. Interested in piloting with {community_name}?",

            "{name} — Lantern is built for communities like yours: families wanting privacy-first tools for kids' learning + entertainment. "
            "Local AI chat (Claude, Gemini, etc.), unlimited public domain music, offline-first design. No cloud dependency. "
            "Pilot opportunity?",

            "Hi {name} — you've been thoughtful about tech for kids in your space. "
            "We're building Lantern specifically for communities wanting local-first, parent-controlled AI chat + learning. "
            "Works on Starlink, no surveillance. Interested in trying it with your group?",
        ],
        "accessibility": [
            "{name} — Lantern is designed for families in remote areas or with connectivity limits. "
            "Local AI chat for kids with anxiety (no cloud tracking), older adults learning tech, people with disabled connectivity. "
            "Privacy-first, offline-first. Want to test it?",

            "Hi {name} — we're building accessibility-first tools. "
            "Lantern is local-first AI chat designed for people with limited internet, privacy concerns, or accessibility needs. "
            "Works offline, runs on modest hardware, full parent/caregiver control. Interested in feedback?",

            "{name} — parents and caregivers often ask: 'How do I give my kid AI tools without Google/Amazon tracking them?' "
            "Lantern solves it: local chat, offline media library, works on Starlink, parents control everything. "
            "Testing with accessibility-focused families. Join us?",

            "Hi {name} — Lantern is purpose-built for families needing privacy, reliability, and offline capability. "
            "Local AI chat, no surveillance, no cloud dependency. Works for kids with anxiety, older adults, rural families, people with limited connectivity. "
            "Beta access?",
        ],
    }

    def __init__(self):
        """Initialize outreach service."""
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load outreach configuration from disk."""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                return json.load(f)
        return {"outreach": []}

    def _save_config(self):
        """Save outreach configuration to disk."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=2)

    def generate_messages(self, segment: str, count: int = 3) -> List[str]:
        """Generate message templates for a segment."""
        if segment not in self.TEMPLATES:
            print(f"Unknown segment: {segment}")
            print(f"Available: {', '.join(self.TEMPLATES.keys())}")
            return []

        templates = self.TEMPLATES[segment][:count]
        messages = []

        for i, template in enumerate(templates, 1):
            msg = f"--- Message {i} ({segment}) ---\n\n{template}\n\n"
            msg += "(Customize [name], [community_name] with actual contact details before sending)\n"
            messages.append(msg)

        return messages

    def track_outreach(
        self,
        contact_name: str,
        segment: str,
        status: str,
        message_preview: Optional[str] = None,
    ):
        """Track outreach attempt locally."""
        record = {
            "name": contact_name,
            "segment": segment,
            "status": status,  # pending, sent, positive, negative, no-response
            "timestamp": datetime.now().isoformat(),
            "message_preview": message_preview[:100] if message_preview else None,
        }
        self.config["outreach"].append(record)
        self._save_config()
        print(f"✓ Tracked: {contact_name} ({status})")

    def list_outreach(self, status: Optional[str] = None) -> List[Dict]:
        """List tracked outreach attempts."""
        outreach = self.config["outreach"]
        if status:
            outreach = [o for o in outreach if o["status"] == status]
        return outreach

    def stats(self) -> Dict:
        """Get outreach statistics."""
        all_outreach = self.config["outreach"]
        return {
            "total": len(all_outreach),
            "by_status": {
                s: len([o for o in all_outreach if o["status"] == s])
                for s in ["pending", "sent", "positive", "negative", "no-response"]
            },
            "by_segment": {
                s: len([o for o in all_outreach if o["segment"] == s])
                for s in ["van-family", "community", "accessibility"]
            },
        }


def main():
    """Command-line interface."""
    service = OutreachService()

    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1]

    if command == "generate":
        segment = sys.argv[3] if len(sys.argv) > 3 else "van-family"
        count = int(sys.argv[5]) if len(sys.argv) > 5 else 3
        messages = service.generate_messages(segment, count)
        for msg in messages:
            print(msg)

    elif command == "track":
        name = sys.argv[3] if len(sys.argv) > 3 else "Unknown"
        segment = sys.argv[5] if len(sys.argv) > 5 else "van-family"
        status = sys.argv[7] if len(sys.argv) > 7 else "sent"
        service.track_outreach(name, segment, status)

    elif command == "list":
        status = sys.argv[3] if len(sys.argv) > 3 else None
        outreach = service.list_outreach(status)
        for record in outreach:
            print(f"  {record['name']:<20} | {record['segment']:<14} | {record['status']:<12}")

    elif command == "stats":
        stats = service.stats()
        print(f"\nTotal outreach attempts: {stats['total']}")
        print("\nBy status:")
        for s, count in stats["by_status"].items():
            print(f"  {s}: {count}")
        print("\nBy segment:")
        for s, count in stats["by_segment"].items():
            print(f"  {s}: {count}")

    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
