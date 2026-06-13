#!/usr/bin/env python3
"""CSF search — stdin-piped JSON interface for the /api/csf/search route.

Input (stdin):
    {"query": "lantern door", "archives": ["/abs/path/a.csf", ...], "top_n": 3}

Output (stdout):
    {"segments": [{"text": "...", "score": 1.0, "segment_id": 0, "archive": "a.csf"}]}

Errors (non-zero exit):
    {"error": "reason"}

No command-line arguments are accepted to prevent injection. All input comes
through stdin. Archives default to data/dream_journal/csf/ + data/all-docs.csf
when the archives list is empty or omitted.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _default_archives() -> list[Path]:
    """Paths to search when caller provides no explicit archive list."""
    found: list[Path] = []
    journal_dir = REPO_ROOT / "data" / "dream_journal" / "csf"
    if journal_dir.is_dir():
        found.extend(sorted(journal_dir.glob("*.csf")))
    all_docs = REPO_ROOT / "data" / "all-docs.csf"
    if all_docs.is_file():
        found.append(all_docs)
    return found


def _score(query: str, text: str) -> float:
    """Simple TF-style score: fraction of query tokens found in text."""
    tokens = re.findall(r"[a-z0-9_]+", query.lower())
    if not tokens:
        return 0.0
    text_lower = text.lower()
    hits = sum(1 for t in tokens if t in text_lower)
    return hits / len(tokens)


def search(query: str, archive_paths: list[Path], top_n: int = 3) -> list[dict]:
    """Open each archive, search segments, return top-N scored results."""
    from csf import CsfArchive  # import here so errors surface cleanly

    results: list[dict] = []
    for path in archive_paths:
        try:
            archive = CsfArchive.open(path)
        except Exception:
            continue
        for seg_idx, _byte_offset, context in archive.search(query):
            score = _score(query, context)
            results.append({
                "text": context.strip(),
                "score": round(score, 4),
                "segment_id": seg_idx,
                "archive": path.name,
            })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top_n]


def main(argv: list[str] | None = None) -> int:
    if argv:
        # CLI form: csf_search.py <archive.csf> [<archive.csf> ...] <query>
        if len(argv) < 2:
            print(json.dumps({"error": "usage: csf_search <archive.csf>... <query>"}))
            return 1
        req = {"archives": argv[:-1], "query": argv[-1]}
    else:
        try:
            req = json.loads(sys.stdin.read())
        except json.JSONDecodeError as e:
            print(json.dumps({"error": f"invalid JSON input: {e}"}))
            return 1

    query = str(req.get("query", "")).strip()
    if not query:
        print(json.dumps({"error": "query must not be empty"}))
        return 1

    raw_archives = req.get("archives") or []
    if raw_archives:
        archive_paths = [Path(p) for p in raw_archives if Path(p).is_file()]
    else:
        archive_paths = _default_archives()

    top_n = int(req.get("top_n", 3))

    segments = search(query, archive_paths, top_n)
    print(json.dumps({"segments": segments}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
