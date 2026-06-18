#!/usr/bin/env python3
"""
Gaming Shorts Filter — Separate gaming from general Shorts

Reads raw_shorts_dataset.jsonl and outputs gaming_shorts.jsonl
Uses keyword matching, category hints, and heuristics.

Usage:
    python scripts/filter_gaming_shorts.py
"""

import json
from pathlib import Path
from typing import Dict
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class GamingShortsFilter:
    """Filter and classify gaming Shorts."""

    def __init__(self, input_dir: str = "data/youtube"):
        self.input_dir = Path(input_dir)
        self.input_file = self.input_dir / "raw_shorts_dataset.jsonl"
        self.output_file = self.input_dir / "gaming_shorts.jsonl"

        # Gaming keywords
        self.gaming_keywords = {
            # Game titles
            "minecraft", "fortnite", "cod", "valorant", "roblox", "gta",
            "cs2", "league", "warzone", "apex", "rust", "elden ring",
            "baldurs gate", "starfield", "palworld", "helldivers", "helldivers 2",
            "tarkov", "escape from tarkov", "rust", "dayz", "ark", "survival",
            "overwatch", "destiny", "diablo", "path of exile", "mmorpg",

            # Gaming actions
            "gameplay", "gaming", "esports", "clip", "montage", "reaction",
            "skill", "clutch", "kill", "elimination", "raid", "boss", "speedrun",
            "walkthrough", "tutorial", "lets play", "playthrough", "stream",
            "tournament", "competitive", "ranked", "multiplayer", "coop",
            "boss fight", "boss battle", "pvp", "pve", "achievement",

            # Emotional/intensity markers (correlate with gaming content)
            "insane", "crazy", "epic", "unbelievable", "impossible", "sick",
            "clutch", "fail", "funny", "moment", "best", "ultimate",

            # Streamer/content creator culture
            "streamer", "youtuber", "content creator", "gamer",
        }

        # Gaming category IDs (YouTube API)
        self.gaming_category_ids = {"20", "1"}  # 20=Gaming, 1=Film & Animation (some gaming vids)

    def is_gaming(self, record: Dict) -> bool:
        """Determine if a video is gaming-related."""

        # Check category first (most reliable)
        if record.get('category_id') in self.gaming_category_ids:
            return True

        # Check title
        title = record.get('title', '').lower()
        if any(keyword in title for keyword in self.gaming_keywords):
            return True

        # Check description
        description = record.get('description', '').lower()
        if any(keyword in description for keyword in self.gaming_keywords):
            return True

        # Check tags
        tags = record.get('tags', [])
        if isinstance(tags, list):
            tags_lower = [tag.lower() for tag in tags]
            if any(keyword in ' '.join(tags_lower) for keyword in self.gaming_keywords):
                return True

        # Check channel name
        channel = record.get('channel_name', '').lower()
        if any(keyword in channel for keyword in ['gamer', 'gaming', 'streamer', 'esports']):
            return True

        return False

    def filter_and_save(self) -> Dict[str, int]:
        """
        Read raw dataset, filter gaming, output separately.

        Returns:
            {"total": int, "gaming": int, "general": int}
        """

        if not self.input_file.exists():
            logger.error(f"Input file not found: {self.input_file}")
            return {"total": 0, "gaming": 0, "general": 0}

        gaming_records = []
        general_records = []

        with open(self.input_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue

                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning(f"Line {line_num}: invalid JSON, skipping")
                    continue

                if self.is_gaming(record):
                    record['is_gaming'] = True
                    gaming_records.append(record)
                else:
                    record['is_gaming'] = False
                    general_records.append(record)

        # Save gaming subset
        gaming_file = self.input_dir / "gaming_shorts.jsonl"
        with open(gaming_file, 'w') as f:
            for record in gaming_records:
                f.write(json.dumps(record) + '\n')

        logger.info(f"Saved {len(gaming_records)} gaming records to {gaming_file}")

        # Save general subset (optional, for comparison)
        general_file = self.input_dir / "general_shorts.jsonl"
        with open(general_file, 'w') as f:
            for record in general_records:
                f.write(json.dumps(record) + '\n')

        logger.info(f"Saved {len(general_records)} general records to {general_file}")

        # Stats
        total = len(gaming_records) + len(general_records)
        gaming_pct = 100.0 * len(gaming_records) / max(1, total)

        logger.info(f"Total: {total} | Gaming: {len(gaming_records)} ({gaming_pct:.1f}%) | General: {len(general_records)}")

        return {
            "total": total,
            "gaming": len(gaming_records),
            "general": len(general_records),
            "gaming_pct": gaming_pct
        }


def main():
    logger.info("Starting gaming shorts filter...")
    filter = GamingShortsFilter()
    stats = filter.filter_and_save()

    if stats["total"] > 0:
        logger.info(f"✅ Filtering complete: {stats['gaming']} gaming / {stats['total']} total")
    else:
        logger.error("❌ No records processed")


if __name__ == "__main__":
    main()
