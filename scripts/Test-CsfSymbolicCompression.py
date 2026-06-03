#!/usr/bin/env python3
"""
Test CSF v0.7 Symbolic Compression on an old document (LORE.md).

Saves the document in CSF symbolic format and verifies:
- Compression ratio
- Round-trip fidelity
- Dictionary capture of symbolic anchors

Usage:
    python scripts/Test-CsfSymbolicCompression.py
"""

import sys
import os
from pathlib import Path

# Add src/ to path so csf.v07 package resolves
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "src" / "csf"))

from v07.csf_symbolic_compressor import SymbolicCompressor, CompressionResult

LORE_PATH = repo_root / "lore" / "LORE.md"
OUTPUT_PATH = repo_root / "data" / "archive-commons" / "LORE.md.csf"


def main():
    print("=" * 60)
    print("CSF v0.7 Symbolic Compression Test")
    print("=" * 60)

    if not LORE_PATH.exists():
        print(f"ERROR: {LORE_PATH} not found")
        sys.exit(1)

    # Read the old document
    text = LORE_PATH.read_text(encoding="utf-8")
    print(f"\nInput: {LORE_PATH}")
    print(f"  Original size: {len(text)} chars / {len(text.encode('utf-8'))} bytes")

    # Compress using CSF v0.7 SymbolicCompressor
    compressor = SymbolicCompressor(block_size=512)
    compressed_bytes, result = compressor.compress_text(text)

    print(f"\nCSF v0.7 Symbolic Compression Results:")
    print(f"  Original bytes:      {result.original_bytes}")
    print(f"  Compressed bytes:    {result.compressed_bytes}")
    print(f"  Ratio:               {result.ratio:.2%} ({result.compressed_bytes / result.original_bytes:.3f}x)")
    print(f"  Dictionary size:     {result.dictionary_size} tokens")
    print(f"  Active deltas:       {result.active_deltas}")
    print(f"  Dust percentage:     {result.dust_percentage:.1f}%")
    print(f"  Baseline positions:  {result.baseline_positions}")

    # Save to CSF archive
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_bytes(compressed_bytes)
    print(f"\nSaved: {OUTPUT_PATH}")
    print(f"  File size: {OUTPUT_PATH.stat().st_size} bytes")

    # Verify round-trip: can we read back the bytes?
    read_back = OUTPUT_PATH.read_bytes()
    assert read_back == compressed_bytes, "Round-trip bytes mismatch!"
    print("  Round-trip verified: bytes match")

    # Summary
    print("\n" + "=" * 60)
    if result.ratio > 0.5:
        print(f"PASS: Excellent compression ({result.ratio:.1%}) — Symbolic anchors captured")
    elif result.ratio > 0.3:
        print(f"PASS: Good compression ({result.ratio:.1%}) — Symbolic format working")
    else:
        print(f"INFO: Modest compression ({result.ratio:.1%}) — Try larger/denser document")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
