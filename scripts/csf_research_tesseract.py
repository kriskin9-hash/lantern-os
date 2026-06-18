"""
CSF Research Tesseract — pack / unpack all ingest PDFs into one CSF archive.

Usage:
  python scripts/csf_research_tesseract.py pack
  python scripts/csf_research_tesseract.py unpack

Pack:
  - Scans data/ingest/**/*.pdf (deduplicates by filename)
  - Extracts text via PyMuPDF
  - Writes data/tesseract/research-pool.csf using src/csf CSFWriter
  - Writes data/tesseract/manifest.json (fast JS-side index)

Unpack:
  - Reads the CSF archive
  - Re-emits manifest.json (regenerates index from archive)
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import struct
import sys
import time
from pathlib import Path

# Repo root = two levels up from scripts/
REPO = Path(__file__).resolve().parent.parent
INGEST_BASE = REPO / "data" / "ingest"
TESSERACT_DIR = REPO / "data" / "tesseract"
CSF_OUT = TESSERACT_DIR / "research-pool.csf"
MANIFEST_OUT = TESSERACT_DIR / "manifest.json"

sys.path.insert(0, str(REPO / "apps"))
sys.path.insert(0, str(REPO / "src"))

try:
    from csf.csf_file import CSFWriter, CSFReader, SymbolicDictionary
    from csf.delta_stream import DeltaType
    _CSF_NATIVE = True
except Exception as e:
    _CSF_NATIVE = False
    print(f"[warn] Native CSF not available ({e}), using fallback format", flush=True)

try:
    import fitz  # PyMuPDF
    _FITZ = True
except ImportError:
    _FITZ = False
    print("[warn] PyMuPDF not available — storing filenames only (no text extraction)", flush=True)


# ── Helpers ──────────────────────────────────────────────────────────────────

def scan_pdfs() -> list[dict]:
    """Deduplicated list of all PDFs under data/ingest/."""
    seen: set[str] = set()
    pdfs = []
    for p in sorted(INGEST_BASE.rglob("*.pdf")):
        key = p.name.lower()
        if key in seen:
            continue
        seen.add(key)
        stat = p.stat()
        pdfs.append({
            "filename": p.name,
            "name": p.stem,
            "path": str(p),
            "folder": str(p.parent.relative_to(INGEST_BASE)),
            "size": stat.st_size,
            "modifiedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(stat.st_mtime)),
        })
    return pdfs


def extract_text(pdf_path: str) -> str:
    if not _FITZ:
        return ""
    try:
        doc = fitz.open(pdf_path)
        pages = []
        for page in doc:
            pages.append(page.get_text())
        doc.close()
        return "\n".join(pages)[:50_000]  # cap at 50 KB of text per doc
    except Exception as e:
        return f"[extraction error: {e}]"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


# ── Pack ─────────────────────────────────────────────────────────────────────

def pack():
    TESSERACT_DIR.mkdir(parents=True, exist_ok=True)
    pdfs = scan_pdfs()
    print(f"[pack] Found {len(pdfs)} unique PDFs in {INGEST_BASE}", flush=True)

    records = []
    for i, meta in enumerate(pdfs):
        text = extract_text(meta["path"])
        sha = sha256_file(meta["path"])
        record = {**meta, "sha256": sha, "textLength": len(text), "text": text}
        records.append(record)
        print(f"[pack] {i+1}/{len(pdfs)} {meta['filename']} ({meta['size']} B, {len(text)} chars)", flush=True)

    # Native CSF delta writer uses a single-byte length field (max 255 B payload).
    # Text extraction payloads are always larger — use fallback container format.
    _pack_csf_fallback(records)

    # Always write the manifest for fast JS queries
    manifest = {
        "packedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "count": len(records),
        "totalSize": sum(r["size"] for r in records),
        "totalTextChars": sum(r["textLength"] for r in records),
        "format": "csf-fallback",
        "csfPath": str(CSF_OUT),
        "docs": [{k: v for k, v in r.items() if k != "text"} for r in records],
    }
    MANIFEST_OUT.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[pack] Manifest written: {MANIFEST_OUT}", flush=True)
    print(f"[pack] Tesseract: {CSF_OUT} ({CSF_OUT.stat().st_size} B)", flush=True)
    print(f"[pack] Done. {len(records)} documents packed.", flush=True)


def _pack_csf_native(records: list[dict]):
    """Use the Lantern CSF writer to produce a proper CSF archive."""
    writer = CSFWriter()

    # Baseline = collection stats as a sparse scalar map (index → doc count)
    writer.set_baseline({0: len(records), 1: sum(r["size"] for r in records)})

    # Register each PDF name in the symbolic dictionary
    for r in records:
        writer.dictionary.encode_name(r["name"])

    # One ANCHOR_ACTIVATION delta per document
    for i, r in enumerate(records):
        payload_obj = {
            "filename": r["filename"],
            "folder": r["folder"],
            "size": r["size"],
            "sha256": r["sha256"],
            "modifiedAt": r["modifiedAt"],
            "textLength": r["textLength"],
            "text": r["text"],
        }
        payload_bytes = gzip.compress(json.dumps(payload_obj, separators=(",", ":")).encode())
        # position = (doc_index, 0, 0, ...) in 12-dim space
        position = tuple([i % 3] * 12)
        writer.add_delta(level=4, dtype=DeltaType.ANCHOR_ACTIVATION,
                         position=position, payload=payload_bytes)

    meta = writer.write(CSF_OUT)
    print(f"[pack] CSF native: {meta.delta_count} deltas, {meta.total_bytes} B", flush=True)


def _pack_csf_fallback(records: list[dict]):
    """Minimal CSF-compatible container when the native lib is unavailable."""
    MAGIC = b"CSF\x00"
    VERSION = b"\x00\x03"
    FLAGS = b"\x00\x00"

    entries = []
    for r in records:
        payload = gzip.compress(json.dumps(
            {k: v for k, v in r.items()}, separators=(",", ":"
        )).encode())
        entries.append(payload)

    body = bytearray()
    body.extend(MAGIC)
    body.extend(VERSION)
    body.extend(FLAGS)
    body.extend(struct.pack(">I", len(entries)))
    for e in entries:
        body.extend(struct.pack(">I", len(e)))
        body.extend(e)

    checksum = hashlib.sha256(bytes(body)).hexdigest()[:16]
    body.extend(checksum.encode())
    CSF_OUT.write_bytes(bytes(body))


# ── Unpack ───────────────────────────────────────────────────────────────────

def unpack():
    if not CSF_OUT.exists():
        print(f"[unpack] No tesseract found at {CSF_OUT} — run pack first", flush=True)
        sys.exit(1)

    stat = CSF_OUT.stat()
    print(f"[unpack] Reading {CSF_OUT} ({stat.st_size} B)", flush=True)

    raw = CSF_OUT.read_bytes()
    magic = raw[:4]

    if magic != b"CSF\x00":
        print(f"[unpack] Bad magic: {magic!r}", flush=True)
        sys.exit(1)

    # Check if manifest already exists and is up to date
    if MANIFEST_OUT.exists():
        manifest = json.loads(MANIFEST_OUT.read_text(encoding="utf-8"))
        print(f"[unpack] Manifest already present: {manifest['count']} docs packed {manifest['packedAt']}", flush=True)
        print(f"[unpack] Total text: {manifest['totalTextChars']:,} chars", flush=True)
        for doc in manifest["docs"]:
            print(f"  • {doc['filename']} ({doc['size']} B, {doc['textLength']} chars text)", flush=True)
        return

    # Re-extract from the fallback format
    offset = 8  # magic + version + flags
    count = struct.unpack_from(">I", raw, offset)[0]
    offset += 4
    print(f"[unpack] {count} records in archive", flush=True)
    docs = []
    for i in range(count):
        size = struct.unpack_from(">I", raw, offset)[0]
        offset += 4
        payload = gzip.decompress(raw[offset:offset + size])
        offset += size
        obj = json.loads(payload)
        docs.append({k: v for k, v in obj.items() if k != "text"})
        print(f"  [{i+1}] {obj.get('filename', '?')} — {obj.get('textLength', 0)} chars", flush=True)

    manifest = {
        "packedAt": "unknown",
        "count": len(docs),
        "totalSize": sum(d.get("size", 0) for d in docs),
        "totalTextChars": sum(d.get("textLength", 0) for d in docs),
        "format": "csf-fallback",
        "csfPath": str(CSF_OUT),
        "docs": docs,
    }
    MANIFEST_OUT.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[unpack] Manifest written: {MANIFEST_OUT}", flush=True)


# ── Entry ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "pack"
    if action == "pack":
        pack()
    elif action == "unpack":
        unpack()
    else:
        print(f"Unknown action: {action}. Use 'pack' or 'unpack'.", flush=True)
        sys.exit(1)
