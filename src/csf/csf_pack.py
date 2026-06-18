"""
CSF-Pack (CSF v0.8) — general-purpose archive: pack & unpack ARBITRARY files.

Unlike the symbolic CSF formats (v0.3 `csf_file.py`, v0.7 engine) which encode
world-model memory, CSF-Pack is a plain container for any bytes — the Σ₀ release
that can wrap arbitrary files (code, data, models) with per-file hashing,
optional zlib compression, and an integrity footer.

Binary layout
-------------
    [Magic        4 bytes : b"CSF\\x00"]
    [Version      2 bytes : major, minor = 0, 8]
    [Flags        2 bytes : bit0 = blobs zlib-compressed]
    [ManifestLen  4 bytes : uint32 BE]
    [Manifest     N bytes : UTF-8 JSON]
    [Blob region  M bytes : concatenated (optionally compressed) file bytes]
    [Footer      40 bytes : sha256(everything before footer) (32) + total size uint64 BE (8)]

Manifest JSON
-------------
    {
      "format": "csf-pack", "version": "0.8", "created_at": <epoch>,
      "compressed": bool, "file_count": int,
      "files": [{"path", "size", "csize", "sha256", "offset", "compressed"}]
    }

CLI
---
    python -m csf.csf_pack pack <paths...> -o out.csf [--no-compress]
    python -m csf.csf_pack unpack out.csf -d <dest_dir>
    python -m csf.csf_pack list out.csf
"""
from __future__ import annotations

import hashlib
import json
import os
import struct
import time
import zlib
from pathlib import Path
from typing import Iterable

MAGIC = b"CSF\x00"
VERSION = (0, 8)
FLAG_COMPRESSED = 0x0001
FOOTER_FMT = ">Q"  # total size; preceded by 32-byte sha256


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iter_files(paths: Iterable[str]):
    """Yield (abs_path, arc_path) for each file; directories are walked."""
    for p in paths:
        path = Path(p)
        if path.is_dir():
            base = path.parent
            for f in sorted(path.rglob("*")):
                if f.is_file():
                    yield f, f.relative_to(base).as_posix()
        elif path.is_file():
            yield path, path.name
        else:
            raise FileNotFoundError(p)


def _safe_join(dest: Path, arc_path: str) -> Path:
    """Resolve arc_path under dest, refusing path traversal (.. / absolute)."""
    target = (dest / arc_path).resolve()
    if not str(target).startswith(str(dest.resolve())):
        raise ValueError(f"unsafe path in archive: {arc_path}")
    return target


# ---------------------------------------------------------------------------
# Pack
# ---------------------------------------------------------------------------

def _write_archive(items, out_path: str, compress: bool, extra_meta: dict | None) -> dict:
    """Core writer. items = iterable of (arc_path, raw_bytes)."""
    files, blob = [], bytearray()
    for arc, raw in items:
        sha = hashlib.sha256(raw).hexdigest()
        stored = zlib.compress(raw, 9) if compress else raw
        files.append({
            "path": arc, "size": len(raw), "csize": len(stored),
            "sha256": sha, "offset": len(blob), "compressed": bool(compress),
        })
        blob.extend(stored)

    manifest = {
        "format": "csf-pack", "version": "0.8", "created_at": time.time(),
        "compressed": bool(compress), "file_count": len(files), "files": files,
    }
    if extra_meta:
        manifest.update(extra_meta)
    manifest_bytes = json.dumps(manifest, separators=(",", ":")).encode("utf-8")

    body = bytearray()
    body += MAGIC
    body += struct.pack(">BB", *VERSION)
    body += struct.pack(">H", FLAG_COMPRESSED if compress else 0)
    body += struct.pack(">I", len(manifest_bytes))
    body += manifest_bytes
    body += blob
    body += hashlib.sha256(bytes(body)).digest()
    body += struct.pack(FOOTER_FMT, len(body) + 8)

    Path(out_path).write_bytes(bytes(body))
    return manifest


def pack(paths: Iterable[str], out_path: str, compress: bool = True) -> dict:
    """Pack arbitrary files/dirs into a CSF-Pack archive. Returns the manifest."""
    items = ((arc, Path(abs_path).read_bytes()) for abs_path, arc in _iter_files(paths))
    return _write_archive(items, out_path, compress, None)


def pack_blobs(blobs: dict, out_path: str, compress: bool = True, extra_meta: dict | None = None) -> dict:
    """Pack in-memory {arc_path: bytes} blobs (e.g. generated manifests). Returns manifest."""
    return _write_archive(blobs.items(), out_path, compress, extra_meta)


# ---------------------------------------------------------------------------
# Read / verify / unpack
# ---------------------------------------------------------------------------

def _read_container(archive: str):
    data = Path(archive).read_bytes()
    if data[:4] != MAGIC:
        raise ValueError(f"not a CSF file (magic={data[:4]!r})")
    major, minor = struct.unpack(">BB", data[4:6])
    if (major, minor) != VERSION:
        raise ValueError(f"unsupported CSF-Pack version {major}.{minor} (need {VERSION[0]}.{VERSION[1]})")
    flags = struct.unpack(">H", data[6:8])[0]
    # Footer integrity FIRST — catch any tampering with a clean error before parsing.
    if len(data) < 52:
        raise ValueError("CSF-Pack too small / truncated")
    stored_digest = data[-40:-8]
    if hashlib.sha256(data[:-40]).digest() != stored_digest:
        raise ValueError("CSF-Pack integrity check failed (footer digest mismatch)")
    mlen = struct.unpack(">I", data[8:12])[0]
    manifest = json.loads(data[12:12 + mlen].decode("utf-8"))
    blob_start = 12 + mlen
    blob_end = len(data) - 40
    return data, manifest, flags, blob_start, blob_end


def list_archive(archive: str) -> dict:
    """Return the manifest without extracting."""
    _, manifest, _, _, _ = _read_container(archive)
    return manifest


def unpack(archive: str, dest: str) -> list[str]:
    """Extract all files to dest, verifying per-file sha256. Returns written paths."""
    data, manifest, _flags, blob_start, blob_end = _read_container(archive)
    dest_path = Path(dest)
    dest_path.mkdir(parents=True, exist_ok=True)
    written = []
    for fe in manifest["files"]:
        start = blob_start + fe["offset"]
        chunk = data[start:start + fe["csize"]]
        raw = zlib.decompress(chunk) if fe.get("compressed") else chunk
        if hashlib.sha256(raw).hexdigest() != fe["sha256"]:
            raise ValueError(f"checksum mismatch for {fe['path']}")
        target = _safe_join(dest_path, fe["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        written.append(str(target))
    return written


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="csf-pack", description="CSF v0.8 — pack/unpack arbitrary files")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pack", help="pack files/dirs into a .csf archive")
    p.add_argument("paths", nargs="+")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--no-compress", action="store_true")
    u = sub.add_parser("unpack", help="extract a .csf archive")
    u.add_argument("archive")
    u.add_argument("-d", "--dest", default=".")
    l = sub.add_parser("list", help="list archive contents")
    l.add_argument("archive")
    args = ap.parse_args(argv)

    if args.cmd == "pack":
        m = pack(args.paths, args.out, compress=not args.no_compress)
        total = sum(f["size"] for f in m["files"])
        stored = sum(f["csize"] for f in m["files"])
        print(f"packed {m['file_count']} file(s) -> {args.out}  ({total} -> {stored} bytes)")
    elif args.cmd == "unpack":
        w = unpack(args.archive, args.dest)
        print(f"extracted {len(w)} file(s) -> {args.dest}")
    elif args.cmd == "list":
        m = list_archive(args.archive)
        print(f"CSF-Pack v{m['version']} — {m['file_count']} file(s), compressed={m['compressed']}")
        for f in m["files"]:
            print(f"  {f['path']}  {f['size']}B  sha256={f['sha256'][:12]}…")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
