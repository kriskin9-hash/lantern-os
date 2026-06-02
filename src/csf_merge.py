#!/usr/bin/env python3
"""CSF merge CLI — converge two .csf archives into one."""

from __future__ import annotations

import argparse
import sys

from csf import CsfArchive


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Merge two CSF archives (convergence)")
    p.add_argument("--base", required=True, help="Base .csf archive")
    p.add_argument("--delta", required=True, help="Delta .csf archive to merge")
    p.add_argument("-o", "--output", required=True, help="Output merged .csf file")
    args = p.parse_args(argv)

    base = CsfArchive.open(args.base)
    delta = CsfArchive.open(args.delta)
    merged = base.converge(delta)
    merged.write(args.output)

    print(f"Merged {args.base} + {args.delta} → {args.output}")
    print(f"  Base segments:   {base.segment_count}")
    print(f"  Delta segments:  {delta.segment_count}")
    print(f"  Merged segments: {merged.segment_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
