#!/usr/bin/env python3
"""Reannotate a v2 CSF-Pack archive: add per-file ``description`` + ``metadata``.

The v2 CSF-Pack manifest now carries an optional per-file ``description`` and
``metadata`` (see ``src/csf/csf_pack.py``). Archives written before that — or
any archive whose members lack a self-describing gloss — can be *regenerated*
in place with this tool so the CSF store says *what* each archived file/script
is, not just its bytes.

It reads the archive (verifying every member's SHA-256 on the way in), attaches
descriptions/metadata from a JSON map or auto-derives a description from each
member's path, and rewrites the archive with the **same codec**, so the output
round-trips byte-for-byte identical content with a richer manifest.

Only v2 CSF-Pack archives (magic ``CSF\\x00``) are supported. Legacy formats
(``CSF\\x06`` v0.7, ``CSFv1`` web caches) are read-only by design and are
skipped with a clear message rather than silently.

Usage
-----
  # dry-run: show what descriptions would be attached
  python scripts/annotate_csf_archive.py ARCHIVE --auto
  # apply, auto-derived descriptions, in place (with .bak backup)
  python scripts/annotate_csf_archive.py ARCHIVE --auto --apply
  # apply descriptions/metadata from a JSON map {arc_path: {description, metadata}}
  python scripts/annotate_csf_archive.py ARCHIVE --map notes.json --apply --out OUT.csf
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from csf import csf_pack  # noqa: E402

_V2_MAGIC = b"CSF\x00"


def _auto_description(arc_path: str) -> str:
    """Best-effort human gloss from an arc path (no content decode needed)."""
    name = arc_path.rsplit("/", 1)[-1]
    stem, ext = os.path.splitext(name)
    ext = ext.lstrip(".").lower() or "file"
    # Strip long hex/hash prefixes that carry no meaning (ingested downloads).
    cleaned = re.sub(r"^[0-9a-f]{6,}[_-]?", "", stem)
    cleaned = re.sub(r"[_-]+", " ", cleaned).strip()
    if not cleaned or re.fullmatch(r"[0-9a-f ]+", cleaned):
        return f"Ingested {ext.upper()} document ({name})"
    parent = arc_path.rsplit("/", 2)[0] if "/" in arc_path else ""
    where = f" - {parent}" if parent and parent != arc_path else ""
    return f"{cleaned} ({ext}){where}"


def _load_map(path: str | None) -> dict:
    if not path:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("--map must be a JSON object keyed by arc_path")
    return data


def annotate(archive: str, out: str, apply: bool, ann_map: dict, auto: bool,
             base_meta: dict | None = None) -> dict:
    magic = Path(archive).read_bytes()[:4]
    if magic != _V2_MAGIC:
        raise SystemExit(
            f"{archive}: not a v2 CSF-Pack archive (magic={magic!r}). "
            "Legacy CSF formats are read-only; regenerate from source instead."
        )

    manifest = csf_pack.list_archive(archive)
    codec = manifest.get("codec", "zlib")
    blobs = csf_pack.unpack_blobs(archive)  # verifies per-file sha256

    annotations = {}
    changed = 0
    for arc in blobs:
        entry = ann_map.get(arc)
        desc = None
        md = None
        if isinstance(entry, dict):
            desc = entry.get("description")
            md = entry.get("metadata")
        elif isinstance(entry, str):
            desc = entry
        if desc is None and auto:
            desc = _auto_description(arc)
        if md is None and base_meta is not None:
            md = dict(base_meta, source_archive=os.path.basename(archive))
        if desc or md:
            annotations[arc] = {"description": desc, "metadata": md}
            changed += 1

    print(f"{archive}: {len(blobs)} member(s), codec={codec}, "
          f"{changed} to annotate -> {out}")
    for arc in list(annotations)[:8]:
        print(f"    {arc}\n      -> {annotations[arc]['description']}")
    if len(annotations) > 8:
        print(f"    … +{len(annotations) - 8} more")

    if apply:
        if os.path.abspath(out) == os.path.abspath(archive):
            backup = f"{archive}.bak-{int(time.time())}"
            Path(backup).write_bytes(Path(archive).read_bytes())
            print(f"  backup: {backup}")
        # use_dict=True recovers cross-file redundancy for text corpora; harmless for others.
        csf_pack.pack_blobs(blobs, out, codec=codec, use_dict=(codec == "zstd"),
                            annotations=annotations)
        # Verify the rewrite round-trips.
        re_blobs = csf_pack.unpack_blobs(out)
        assert re_blobs == blobs, "round-trip mismatch after annotate"
        print(f"  -> wrote {out} ({sum(1 for _ in annotations)} annotated, content verified)")
    else:
        print("  (dry-run; pass --apply to write)")
    return {"members": len(blobs), "annotated": changed}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Reannotate a v2 CSF-Pack archive with description+metadata")
    ap.add_argument("archive")
    ap.add_argument("--map", help="JSON {arc_path: {description, metadata} | \"description\"}")
    ap.add_argument("--auto", action="store_true", help="auto-derive a description from each member's path")
    ap.add_argument("--out", help="output path (default: in place)")
    ap.add_argument("--apply", action="store_true", help="write (default: dry-run)")
    ap.add_argument("--meta", help="JSON object merged into every member's metadata (e.g. loop_stage)")
    args = ap.parse_args(argv)

    out = args.out or args.archive
    base_meta = json.loads(args.meta) if args.meta else None
    annotate(args.archive, out, args.apply, _load_map(args.map), args.auto, base_meta)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
