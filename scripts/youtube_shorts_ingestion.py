#!/usr/bin/env python3
"""
YouTube Shorts Data Ingestion Pipeline
Continuously builds training dataset from YouTube API for Σ₀ V10 scoring model

Usage:
    python youtube_shorts_ingestion.py --api-key YOUR_KEY [--gaming-only] [--limit 1000]

Output:
    data/shorts_global.jsonl
    data/shorts_gaming.jsonl
"""

import json
import sys
import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

# Optional: would use googleapiclient.discovery in production
# from googleapiclient.discovery import build

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class YouTubeShortsIngestor:
    """
    Ingests YouTube Shorts data via YouTube Data API v3
    Stores engagement signals for model training
    """

    def __init__(self, api_key: str, output_dir: str = "data"):
        self.api_key = api_key
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.global_file = self.output_dir / "shorts_global.jsonl"
        self.gaming_file = self.output_dir / "shorts_gaming.jsonl"

    def ingest_shorts(
        self,
        query: str = "shorts",
        gaming_only: bool = False,
        max_results: int = 50,
        categories: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query YouTube Shorts via API

        Args:
            query: Search term
            gaming_only: Filter to gaming category
            max_results: Results per query
            categories: Category filters (gaming, gameplay, clip, montage, etc.)

        Returns:
            List of video records
        """
        if categories is None:
            categories = ["gaming", "gameplay", "clip", "montage"] if gaming_only else []

        logger.info(f"Ingesting YouTube Shorts: query='{query}', gaming_only={gaming_only}, limit={max_results}")

        # In production: use googleapiclient to query YouTube API v3
        # youtube = build('youtube', 'v3', developerKey=self.api_key)
        # request = youtube.search().list(
        #     q=query,
        #     part='snippet',
        #     type='video',
        #     videoDuration='short',
        #     order='viewCount',
        #     maxResults=max_results,
        #     publishedAfter='2024-01-01T00:00:00Z'
        # )
        # response = request.execute()

        # For now, return template with instructions
        logger.warning("YouTube API key required. Set up googleapiclient.discovery for live ingestion.")

        return []

    def extract_record(self, video_snippet: Dict, video_stats: Dict) -> Dict[str, Any]:
        """
        Transform API response into training record

        Record schema:
        {
            "video_id": str,
            "title": str,
            "channel": str,
            "views": int,
            "likes": int,
            "comments": int,
            "duration": int (seconds),
            "publish_date": ISO8601,
            "transcript": str (if available),
            "category": "gaming" | "general",
            "url": str,
            "ingest_date": ISO8601,
        }
        """
        return {
            "video_id": video_snippet.get("videoId", ""),
            "title": video_snippet.get("title", ""),
            "channel": video_snippet.get("channelTitle", ""),
            "views": int(video_stats.get("viewCount", 0)),
            "likes": int(video_stats.get("likeCount", 0)),
            "comments": int(video_stats.get("commentCount", 0)),
            "duration": int(video_stats.get("duration", 0)),
            "publish_date": video_snippet.get("publishedAt", ""),
            "transcript": "",  # Would fetch via YouTube Captions API
            "category": "gaming",  # Would detect via tags/category
            "url": f"https://www.youtube.com/shorts/{video_snippet.get('videoId', '')}",
            "ingest_date": datetime.utcnow().isoformat(),
        }

    def save_records(self, records: List[Dict], is_gaming: bool = False):
        """
        Append records to JSONL file

        Gaming and global datasets stored separately for model flexibility
        """
        target_file = self.gaming_file if is_gaming else self.global_file

        with open(target_file, 'a') as f:
            for record in records:
                f.write(json.dumps(record) + '\n')

        logger.info(f"Saved {len(records)} records to {target_file}")

    def ingest_curated_dataset(self, curated_path: str):
        """
        Fallback: ingest from local curated dataset (CSV/JSON)
        For development when API quota exhausted
        """
        path = Path(curated_path)
        if not path.exists():
            logger.error(f"Curated dataset not found: {curated_path}")
            return

        logger.info(f"Ingesting curated dataset from {curated_path}")
        # Implementation: parse CSV/JSON, normalize to record schema


def main():
    parser = argparse.ArgumentParser(
        description="YouTube Shorts Data Ingestion for Σ₀ V10 Model"
    )
    parser.add_argument("--api-key", required=False, help="YouTube Data API key")
    parser.add_argument("--gaming-only", action="store_true", help="Gaming Shorts only")
    parser.add_argument("--limit", type=int, default=100, help="Records to ingest")
    parser.add_argument("--output-dir", default="data", help="Output directory")
    parser.add_argument("--curated-path", help="Path to curated dataset (fallback)")

    args = parser.parse_args()

    if not args.api_key and not args.curated_path:
        logger.error("Either --api-key or --curated-path required")
        sys.exit(1)

    ingestor = YouTubeShortsIngestor(args.api_key or "", args.output_dir)

    if args.api_key:
        records = ingestor.ingest_shorts(
            gaming_only=args.gaming_only,
            max_results=args.limit
        )
        if records:
            ingestor.save_records(records, is_gaming=args.gaming_only)
    elif args.curated_path:
        ingestor.ingest_curated_dataset(args.curated_path)

    logger.info("Ingestion complete")


if __name__ == "__main__":
    main()
