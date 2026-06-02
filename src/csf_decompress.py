#!/usr/bin/env python3
"""CSF decompress CLI — extract a .csf archive."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from csf import CsfArchive


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Decompress a CSF archive")
    p.add_argument("input", help="Input .csf file")
    p.add_argument("-o", "--output", required=True, help="Output directory")
    args = p.parse_args(argv)

    archive = CsfArchive.open(args.input)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    for i, seg in enumerate(archive._segments):
        out_path = out_dir / f"segment_{i:04d}.bin"
        out_path.write_bytes(seg)

    print(f"Extracted {archive.segment_count} segments to {out_dir}")
    print(f"  Total bytes: {archive.uncompressed_size:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
