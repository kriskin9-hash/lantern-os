#!/usr/bin/env python3
"""
YouTube Shorts Data Collector v2 — Real engagement data for Σ₀ V10 training

Usage:
    python scripts/youtube_shorts_collector_v2.py --real --search-calls 2

Output (real data, append-only, never overwrites mock files):
    data/youtube/real_raw_shorts.jsonl — raw metadata
    data/youtube/real_gaming_shorts.jsonl — gaming subset
    data/youtube/api_quota_state.json — daily quota tracker

Output (--use-mock, default — synthetic data for testing/CI only):
    data/youtube/raw_shorts_dataset.jsonl
    data/youtube/gaming_shorts.jsonl
"""

import json
import os
import re
import sys
import argparse
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Will be imported in production:
# from googleapiclient.discovery import build
# from googleapiclient.errors import HttpError


class YouTubeShortsCollectorV2:
    """
    Collects real YouTube Shorts data with engagement metrics.
    Designed for Σ₀ V10 model training.
    """

    def __init__(self, api_key: str, output_dir: str = "data/youtube"):
        self.api_key = api_key
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.raw_file = self.output_dir / "raw_shorts_dataset.jsonl"
        self.gaming_file = self.output_dir / "gaming_shorts.jsonl"

        # Real API output — separate from mock files, never overwritten in place
        self.real_raw_file = self.output_dir / "real_raw_shorts.jsonl"
        self.real_gaming_file = self.output_dir / "real_gaming_shorts.jsonl"
        self.quota_state_file = self.output_dir / "api_quota_state.json"

        # Queries rotated daily for diversity
        self.search_queries = [
            "shorts gaming",
            "viral shorts",
            "minecraft shorts",
            "fortnite shorts",
            "tiktok style shorts",
            "gaming highlights shorts",
            "call of duty shorts",
            "valorant shorts",
            "roblox shorts",
            "gta shorts",
            "shorts gameplay",
            "shorts montage",
            "shorts funny",
            "shorts epic",
            "shorts clutch",
        ]

        # Gaming keywords for filtering
        self.gaming_keywords = {
            "minecraft", "fortnite", "cod", "valorant", "roblox", "gta",
            "cs2", "league", "warzone", "apex", "rust", "elden ring",
            "baldurs gate", "starfield", "palworld", "helldivers",
            "gameplay", "gaming", "esports", "clip", "montage", "reaction",
            "skill", "clutch", "kill", "elimination", "raid", "boss"
        }

        self.gaming_category_ids = {
            "20"  # Gaming category
        }

    def collect_shorts(
        self,
        max_results: int = 5000,
        use_cached_api: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Collect YouTube Shorts via API.

        Args:
            max_results: Target number of videos to collect
            use_cached_api: If True, use mock data (testing). Set False for production.

        Returns:
            List of video records
        """

        if use_cached_api:
            logger.warning("⚠️  Using MOCK API data (for testing/CI)")
            logger.warning("For production: set use_cached_api=False and provide YouTube API key")
            return self._mock_api_data(max_results)

        if not self.api_key:
            logger.error("No YouTube API key provided — cannot run real collection")
            return []

        return []

    # ------------------------------------------------------------------
    # Real YouTube Data API v3 integration (stdlib urllib, no extra deps)
    # ------------------------------------------------------------------

    QUOTA_DAILY_BUDGET = 8000  # stay under the 10,000 unit default daily cap
    QUOTA_COST_SEARCH = 100
    QUOTA_COST_VIDEOS = 1

    def _load_quota_state(self) -> Dict[str, Any]:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        if self.quota_state_file.exists():
            try:
                state = json.loads(self.quota_state_file.read_text())
            except (json.JSONDecodeError, OSError):
                state = {}
        else:
            state = {}

        if state.get("date") != today:
            state = {"date": today, "units_used": 0, "query_index": 0, "seen_video_ids": []}

        state.setdefault("units_used", 0)
        state.setdefault("query_index", 0)
        state.setdefault("seen_video_ids", [])
        return state

    def _save_quota_state(self, state: Dict[str, Any]) -> None:
        self.quota_state_file.write_text(json.dumps(state, indent=2))

    @staticmethod
    def _parse_iso8601_duration(duration: str) -> int:
        """Convert ISO 8601 duration (e.g. 'PT1M5S') to total seconds."""
        match = re.match(
            r"^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$", duration or ""
        )
        if not match:
            return 0
        hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
        return hours * 3600 + minutes * 60 + seconds

    def _api_get(self, base_url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        query = urllib.parse.urlencode(params)
        url = f"{base_url}?{query}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            logger.error(f"YouTube API HTTP {e.code}: {body[:300]}")
            raise

    def _search_video_ids(self, query: str, max_results: int = 50) -> List[str]:
        data = self._api_get(
            "https://www.googleapis.com/youtube/v3/search",
            {
                "key": self.api_key,
                "q": query,
                "part": "snippet",
                "type": "video",
                "videoDuration": "short",
                "order": "viewCount",
                "maxResults": max_results,
            },
        )
        return [item["id"]["videoId"] for item in data.get("items", []) if "videoId" in item.get("id", {})]

    def _fetch_video_details(self, video_ids: List[str]) -> List[Dict[str, Any]]:
        if not video_ids:
            return []
        data = self._api_get(
            "https://www.googleapis.com/youtube/v3/videos",
            {
                "key": self.api_key,
                "id": ",".join(video_ids),
                "part": "snippet,statistics,contentDetails",
            },
        )

        records = []
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            content = item.get("contentDetails", {})
            duration_sec = self._parse_iso8601_duration(content.get("duration", ""))

            if duration_sec == 0 or duration_sec > 60:
                continue  # not a true Short

            category_id = snippet.get("categoryId", "")
            title_lower = snippet.get("title", "").lower()
            is_gaming = (
                category_id in self.gaming_category_ids
                or any(kw in title_lower for kw in self.gaming_keywords)
            )

            records.append({
                "video_id": item.get("id"),
                "title": snippet.get("title", ""),
                "channel_id": snippet.get("channelId", ""),
                "channel_name": snippet.get("channelTitle", ""),
                "publish_date": snippet.get("publishedAt", ""),
                "duration": duration_sec,
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "tags": snippet.get("tags", []),
                "category_id": category_id,
                "description": snippet.get("description", ""),
                "is_gaming": is_gaming,
                "source": "youtube_api_real",
                "timestamp": datetime.utcnow().isoformat(),
            })
        return records

    def collect_shorts_real(self, search_calls: int = 1) -> List[Dict[str, Any]]:
        """
        Collect real Shorts metadata via the YouTube Data API v3.

        Quota-aware (round-robins self.search_queries, persists daily usage in
        api_quota_state.json) and deduplicated across runs by video_id.
        Each search call costs 100 units; each videos.list batch costs 1 unit.
        """
        if not self.api_key:
            logger.error("No YouTube API key provided — cannot run real collection")
            return []

        state = self._load_quota_state()
        seen_ids = set(state["seen_video_ids"])
        new_records: List[Dict[str, Any]] = []

        for _ in range(search_calls):
            cost_estimate = self.QUOTA_COST_SEARCH + self.QUOTA_COST_VIDEOS
            if state["units_used"] + cost_estimate > self.QUOTA_DAILY_BUDGET:
                logger.warning(
                    f"Daily quota budget reached ({state['units_used']}/{self.QUOTA_DAILY_BUDGET} units) — stopping"
                )
                break

            query = self.search_queries[state["query_index"] % len(self.search_queries)]
            state["query_index"] += 1

            try:
                video_ids = self._search_video_ids(query)
                state["units_used"] += self.QUOTA_COST_SEARCH
            except urllib.error.HTTPError:
                self._save_quota_state(state)
                raise

            new_ids = [vid for vid in video_ids if vid not in seen_ids]
            if not new_ids:
                logger.info(f"Query '{query}': no new videos (all {len(video_ids)} already seen)")
                continue

            try:
                details = self._fetch_video_details(new_ids)
                state["units_used"] += self.QUOTA_COST_VIDEOS
            except urllib.error.HTTPError:
                self._save_quota_state(state)
                raise

            for record in details:
                record["query_source"] = query
                seen_ids.add(record["video_id"])
                new_records.append(record)

            logger.info(f"Query '{query}': {len(details)} new real Shorts collected")

        state["seen_video_ids"] = list(seen_ids)
        self._save_quota_state(state)
        logger.info(
            f"Real collection done: {len(new_records)} new records, "
            f"{state['units_used']}/{self.QUOTA_DAILY_BUDGET} quota units used today"
        )
        return new_records

    def save_real_records(self, records: List[Dict[str, Any]]) -> None:
        """Append real records to real_*.jsonl files (never overwrites mock data)."""
        if not records:
            logger.info("No new real records to save")
            return

        with open(self.real_raw_file, "a") as f:
            for record in records:
                f.write(json.dumps(record) + "\n")
        logger.info(f"Appended {len(records)} real records to {self.real_raw_file}")

        gaming_records = [r for r in records if r.get("is_gaming")]
        with open(self.real_gaming_file, "a") as f:
            for record in gaming_records:
                f.write(json.dumps(record) + "\n")
        logger.info(f"Appended {len(gaming_records)} real gaming records to {self.real_gaming_file}")

    def _mock_api_data(self, count: int = 100) -> List[Dict[str, Any]]:
        """
        Generate realistic mock data for testing/CI.
        In production, replace with real API calls above.
        """
        import random

        videos = []
        base_date = datetime.utcnow() - timedelta(days=30)

        gaming_channels = [
            "PewDiePie", "Sykkuno", "Valkyrae", "Pokimane", "CouRageJD",
            "Myth", "Tfue", "Shroud", "Ninja", "Summit1g", "xQcOW"
        ]

        titles_gaming = [
            "Insane Minecraft Clutch",
            "Fortnite 1v5 Wipe",
            "Valorant Ace Round",
            "CS2 Headshot Montage",
            "Elden Ring Boss Fail",
            "GTA 5 Epic Moment",
            "Roblox Funny Glitch",
            "Call of Duty Killstreak",
            "League Mechanical Outplay",
            "Warzone Sniper Flick",
        ]

        for i in range(count):
            is_gaming = random.random() < 0.6  # 60% gaming

            video = {
                "video_id": f"vid_{i:06d}",
                "title": random.choice(titles_gaming) if is_gaming else f"Shorts Clip #{i}",
                "channel_id": f"UCchannel_{i % 20}",
                "channel_name": random.choice(gaming_channels) if is_gaming else f"Creator {i % 50}",
                "publish_date": (base_date + timedelta(hours=i)).isoformat() + 'Z',
                "duration": random.randint(15, 59),  # 15-59 seconds
                "views": int(random.lognormvariate(10.5, 2.0)),  # Log-normal distribution
                "likes": int(random.lognormvariate(8.0, 1.8)),
                "comments": int(random.lognormvariate(6.5, 1.5)),
                "tags": ["gaming", "shorts", "viral"] if is_gaming else ["shorts"],
                "category_id": "20" if is_gaming else "24",  # 20=Gaming, 24=Entertainment
                "description": f"Epic moment #{i}",
                "is_gaming": is_gaming,
                "query_source": random.choice(self.search_queries),
                "timestamp": datetime.utcnow().isoformat(),
            }
            videos.append(video)

        logger.info(f"Generated {count} mock videos ({int(count*0.6)} gaming, {int(count*0.4)} general)")
        return videos

    def save_records(self, records: List[Dict[str, Any]]):
        """Save records to JSONL files."""

        with open(self.raw_file, 'w') as f:
            for record in records:
                f.write(json.dumps(record) + '\n')

        logger.info(f"Saved {len(records)} raw records to {self.raw_file}")

        # Split gaming subset
        gaming_records = [r for r in records if r.get('is_gaming', False)]

        with open(self.gaming_file, 'w') as f:
            for record in gaming_records:
                f.write(json.dumps(record) + '\n')

        logger.info(f"Saved {len(gaming_records)} gaming records to {self.gaming_file}")

    def validate_records(self, records: List[Dict[str, Any]]) -> bool:
        """Sanity check on collected data."""

        if not records:
            logger.error("No records collected!")
            return False

        # Check required fields
        required = ['video_id', 'views', 'likes', 'comments', 'duration']
        for record in records[:5]:  # Check first 5
            for field in required:
                if field not in record:
                    logger.error(f"Missing field: {field}")
                    return False

        # Stats
        views = [r['views'] for r in records]
        logger.info(f"Views: min={min(views)}, max={max(views)}, median={sorted(views)[len(views)//2]}")

        likes = [r['likes'] for r in records]
        engagement_rate = [r['likes'] / max(1, r['views']) for r in records]
        logger.info(f"Engagement rate: min={min(engagement_rate):.4f}, max={max(engagement_rate):.4f}")

        return True


def _load_env_local(path: Path) -> None:
    """Minimal .env.local loader (KEY=VALUE lines, no quoting support needed here)."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def main():
    parser = argparse.ArgumentParser(
        description="YouTube Shorts Collector v2 for Σ₀ V10 Training"
    )
    parser.add_argument("--api-key", help="YouTube Data API key (defaults to YOUTUBE_API_KEY env / .env.local)")
    parser.add_argument("--limit", type=int, default=5000, help="Target number of mock videos (--use-mock only)")
    parser.add_argument("--output-dir", default="data/youtube", help="Output directory")
    parser.add_argument("--use-mock", action="store_true", help="Use mock/synthetic data instead of the real API")
    parser.add_argument("--real", action="store_true", help="Run a real YouTube Data API collection")
    parser.add_argument("--search-calls", type=int, default=1, help="Number of search.list calls to make (100 quota units each)")

    args = parser.parse_args()

    if not args.use_mock and not args.real:
        parser.error("Specify either --use-mock (synthetic test data) or --real (live YouTube API)")

    _load_env_local(Path(__file__).resolve().parent.parent / ".env.local")
    api_key = args.api_key or os.environ.get("YOUTUBE_API_KEY", "")

    collector = YouTubeShortsCollectorV2(api_key, args.output_dir)

    if args.real:
        logger.info(f"Running real YouTube API collection ({args.search_calls} search call(s))...")
        records = collector.collect_shorts_real(search_calls=args.search_calls)
        collector.save_real_records(records)
        logger.info("✅ Real collection complete" if records else "⚠️  Real collection returned no new records")
        return

    logger.info(f"Collecting ~{args.limit} mock YouTube Shorts...")
    records = collector.collect_shorts(max_results=args.limit, use_cached_api=True)

    if collector.validate_records(records):
        collector.save_records(records)
        logger.info("✅ Mock collection complete")
    else:
        logger.error("❌ Validation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
