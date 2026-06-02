#!/usr/bin/env python3
"""CSF search CLI — search inside a .csf archive without full decompression."""

from __future__ import annotations

import argparse
import sys

from csf import CsfArchive


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Search inside a CSF archive")
    p.add_argument("archive", help="Input .csf file")
    p.add_argument("query", help="Search string")
    args = p.parse_args(argv)

    archive = CsfArchive.open(args.archive)
    results = archive.search(args.query)

    if not results:
        print("No matches found.")
        return 1

    print(f"Found {len(results)} match(es):")
    for seg_idx, offset, context in results:
        print(f"  segment {seg_idx} @ byte {offset}: ...{context}...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
