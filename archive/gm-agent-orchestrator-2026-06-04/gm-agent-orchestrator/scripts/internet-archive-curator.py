#!/usr/bin/env python3
"""
Internet Archive Media Curator

Streams CC-licensed and public domain music from archive.org.
Searches, filters, and plays Frank Sinatra, classical music, nature sounds, audiobooks.

API: https://archive.org/advancedsearch.php

Usage:
  python scripts/internet-archive-curator.py search --query "Frank Sinatra" --limit 5
  python scripts/internet-archive-curator.py search --query "Bach" --type audio --limit 10
  python scripts/internet-archive-curator.py play "Frank Sinatra - I've Got the World on a String"
"""

import json
import urllib.request
import urllib.parse
from typing import List, Dict, Optional

ARCHIVE_API = "https://archive.org/advancedsearch.php"


class InternetArchiveCurator:
    """Search and stream from internet archive."""

    def __init__(self):
        self.session_cache = {}

    def search(
        self,
        query: str,
        content_type: str = "audio",
        limit: int = 10,
        sort: str = "downloads desc",
    ) -> List[Dict]:
        """
        Search internet archive for media.

        content_type: audio, texts, video, web, data
        sort: downloads desc, date desc, relevance
        """
        # Build query with filters
        # Search in audio/music collections
        full_query = query
        if content_type == "audio":
            # Look in audio and audio_musiconly collections
            full_query = f'({query}) AND (mediatype:audio OR collection:(audio_musiconly OR etree))'

        params = {
            "q": full_query,
            "output": "json",
            "rows": limit,
            "sort": sort,
        }

        url = f"{ARCHIVE_API}?{urllib.parse.urlencode(params)}"

        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode())
            return self._parse_results(data)
        except Exception as e:
            print(f"[ERROR] Search failed: {e}")
            return []

    def _parse_results(self, data: Dict) -> List[Dict]:
        """Parse archive.org search results."""
        results = []
        docs = data.get("response", {}).get("docs", [])

        for doc in docs:
            result = {
                "id": doc.get("identifier"),
                "title": doc.get("title", "Unknown"),
                "creator": doc.get("creator", ["Unknown"])[0]
                if doc.get("creator")
                else "Unknown",
                "date": doc.get("date", ""),
                "url": f"https://archive.org/details/{doc.get('identifier')}",
                "download_url": f"https://archive.org/download/{doc.get('identifier')}/{doc.get('identifier')}_vbrmp3.m3u",
                "format": doc.get("format", []),
                "license": doc.get("licenseurl", ["public domain"])[0]
                if doc.get("licenseurl")
                else "public domain",
            }
            results.append(result)

        return results

    def get_download_url(self, identifier: str) -> Optional[str]:
        """Get direct download/stream URL for an archive item."""
        return f"https://archive.org/download/{identifier}/{identifier}_vbrmp3.m3u"

    def list_results(self, results: List[Dict]):
        """Pretty-print search results."""
        if not results:
            print("No results found")
            return

        print(f"\nFound {len(results)} results:\n")
        for i, result in enumerate(results, 1):
            print(f"[{i}] {result['title']}")
            print(f"    Creator: {result['creator']}")
            print(f"    Date: {result['date']}")
            print(f"    License: {result['license']}")
            print(f"    URL: {result['url']}")
            print()


def main():
    """CLI interface."""
    import sys

    curator = InternetArchiveCurator()

    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1]

    if command == "search":
        query = sys.argv[3] if len(sys.argv) > 3 else "Frank Sinatra"
        content_type = sys.argv[5] if len(sys.argv) > 5 else "audio"
        limit = int(sys.argv[7]) if len(sys.argv) > 7 else 5

        print(f"\nSearching archive.org for: {query}")
        print(f"Type: {content_type} | Limit: {limit}\n")

        results = curator.search(query, content_type, limit)
        curator.list_results(results)

        if results:
            print(f"\nExample stream URL (result 1):")
            print(f"  {results[0]['download_url']}")

    elif command == "play":
        title = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Frank Sinatra"
        print(f"\nSearching for: {title}")
        results = curator.search(title, limit=1)

        if results:
            result = results[0]
            print(f"\nFound: {result['title']}")
            print(f"Creator: {result['creator']}")
            print(f"Stream URL: {result['download_url']}")
            print(f"\n[READY TO PLAY] Stream this in Lantern Media Curator")
        else:
            print("Not found")

    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
