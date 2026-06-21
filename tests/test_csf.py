#!/usr/bin/env python3
"""Canonical CSF core tests (post-v2 consolidation).

Exercises the single public API in :mod:`csf`: lossless byte-stream
compression, the file/blob archive container with per-file integrity, and the
read-only legacy decoder. The pre-v2 ``CsfArchive`` segmented format and the
``csf_compress/decompress/merge/search`` CLIs were removed; their tests went
with them.
"""

from __future__ import annotations

import sys
import zlib
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import csf  # noqa: E402

_CODECS = ["zlib", "store"] + (["zstd"] if csf.csf_pack._zstd is not None else [])


# --------------------------------------------------------------------------
# Single-blob stream helpers
# --------------------------------------------------------------------------

@pytest.mark.parametrize("codec", _CODECS)
@pytest.mark.parametrize("data", [
    pytest.param(b"", id="empty"),
    pytest.param(b"Garden Table Lantern Convergence", id="short"),
    pytest.param(b"Garden Table Lantern " * 500, id="redundant"),
    pytest.param(bytes(range(256)) * 64, id="binary"),
])
def test_compress_bytes_roundtrip(codec, data):
    blob = csf.compress(data, codec=codec)
    assert csf.decompress(blob) == data


def test_default_compress_roundtrip_and_shrinks():
    data = b'{"k":1,"v":[1,2,3]}\n' * 2000
    blob = csf.compress(data)
    assert csf.decompress(blob) == data
    assert len(blob) < len(data)  # redundant JSON must shrink


# --------------------------------------------------------------------------
# Archive container (files + integrity)
# --------------------------------------------------------------------------

def test_pack_blobs_roundtrip_and_read_file():
    blobs = {"a.txt": b"alpha\n" * 100, "sub/b.json": b'{"x":1}', "empty": b""}
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        out = str(Path(d) / "out.csf")
        m = csf.pack_blobs(blobs, out)
        assert m["file_count"] == 3
        # whole-archive extract
        csf.unpack(out, str(Path(d) / "x"))
        for arc, raw in blobs.items():
            assert (Path(d) / "x" / arc).read_bytes() == raw
        # verified single-member read
        assert csf.read_file(out, "a.txt") == blobs["a.txt"]
        with pytest.raises(KeyError):
            csf.read_file(out, "missing")


def test_archive_tamper_detected():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "out.csf"
        csf.pack_blobs({"f": b"payload" * 50}, str(out))
        b = bytearray(out.read_bytes())
        b[len(b) // 2] ^= 0xFF
        bad = Path(d) / "bad.csf"
        bad.write_bytes(bytes(b))
        with pytest.raises(ValueError):
            csf.unpack(str(bad), str(Path(d) / "out"))


# --------------------------------------------------------------------------
# Legacy read-only decoder
# --------------------------------------------------------------------------

def test_legacy_decodes_zlib_blob():
    raw = b"dream preview text " * 20
    blob = zlib.compress(raw, 9)            # the on-disk dream-preview form
    assert csf.legacy.is_zlib_blob(blob)
    assert csf.legacy.decode_bytes(blob) == raw


def test_legacy_open_modern_archive(tmp_path):
    out = tmp_path / "a.csf"
    csf.pack_blobs({"only.txt": b"hello legacy bridge"}, str(out))
    assert csf.legacy.open(str(out)) == b"hello legacy bridge"


def test_legacy_rejects_unknown():
    with pytest.raises(csf.legacy.CsfLegacyError):
        csf.legacy.decode_bytes(b"\x00\x01not a known format")
