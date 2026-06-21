"""Read-only decoders for retired CSF byte formats.

The v2 consolidation (2026-06) removed the legacy CSF *writers* (the segmented
``CsfArchive`` v1, the v0.3 ``csf_file`` symbolic writer, and the lossy v0.7
text compressors) so they can't be called by mistake. This module preserves the
ability to *read* archives that already exist on disk — nothing writes here.

Coverage (verified against every ``.csf`` present in the repo at consolidation
time):

* **Modern CSF-Pack** (``b"CSF\\x00"``) → delegated to :mod:`csf.csf_pack`.
* **Raw DEFLATE blobs** (``0x78`` zlib header) → e.g. the dream-journal CSF
  previews and ``archive-commons/*.csf`` → inflated directly.
* Formats still owned by a *live* module are read by that module, not here:
  the ``CSFv1`` agent cache (``csf_cache_manager``), the ``CSF\\x06`` v0.7
  container (``csf.v07.csf_file``), and the tesseract ``CSF\\x00 v0.3`` pool
  (``scripts/csf_research_tesseract.py``).

The segmented ``CsfArchive`` v1 and root ``csf_file`` v0.3 had **no** archives on
disk; their decoders were retired rather than carried as dead code (recoverable
from git history if ever needed).
"""

from __future__ import annotations

import zlib
from pathlib import Path


class CsfLegacyError(ValueError):
    """Raised when a byte string is not a recognised legacy CSF format."""


def is_zlib_blob(data: bytes) -> bool:
    """Heuristic: a raw DEFLATE/zlib stream (0x78 0x01/0x5e/0x9c/0xda)."""
    return len(data) >= 2 and data[0] == 0x78 and data[1] in (0x01, 0x5E, 0x9C, 0xDA)


def decode_bytes(data: bytes) -> bytes:
    """Best-effort decode of a single legacy blob to its original bytes.

    Handles raw DEFLATE blobs (the only headerless legacy byte form with files
    on disk). Raises :class:`CsfLegacyError` for anything unrecognised.
    """
    if is_zlib_blob(data):
        return zlib.decompress(data)
    raise CsfLegacyError(
        "unrecognised legacy blob (not a raw DEFLATE stream); "
        "modern archives are read via csf.csf_pack / csf.read_file"
    )


def open(path: str | Path) -> bytes:
    """Open a legacy archive/blob file and return decoded bytes.

    * ``b"CSF\\x00"`` modern CSF-Pack → returns the first member's bytes
      (use :func:`csf.csf_pack.unpack` for multi-file archives).
    * raw DEFLATE blob → inflated bytes.
    """
    data = Path(path).read_bytes()
    from . import csf_pack  # local import to avoid a cycle

    if data[:4] == csf_pack.MAGIC:
        manifest = csf_pack.list_archive(str(path))
        files = manifest.get("files", [])
        if not files:
            return b""
        return csf_pack.read_file(str(path), files[0]["path"])
    return decode_bytes(data)
