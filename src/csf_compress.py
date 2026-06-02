#!/usr/bin/env python3
"""CSF compress CLI — create a .csf archive from files or directories."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from csf import CsfArchive


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Compress files into a CSF archive")
    p.add_argument("inputs", nargs="+", help="Files or directories to archive")
    p.add_argument("-o", "--output", required=True, help="Output .csf file path")
    p.add_argument("--streaming", action="store_true", help="Enable streaming mode flag")
    args = p.parse_args(argv)

    archive = CsfArchive()
    if args.streaming:
        archive._flags |= 0x00000008  # CSF_FLAG_STREAMING

    for inp in args.inputs:
        path = Path(inp)
        if path.is_dir():
            for child in path.rglob("*"):
                if child.is_file():
                    archive.add_file(child)
        elif path.is_file():
            archive.add_file(path)
        else:
            print(f"Warning: skipping {path}", file=sys.stderr)

    archive.write(args.output)
    ratio = archive.ratio
    print(f"Created {args.output}")
    print(f"  Segments: {archive.segment_count}")
    print(f"  Uncompressed: {archive.uncompressed_size:,} bytes")
    print(f"  Approx ratio: {ratio:.2%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
