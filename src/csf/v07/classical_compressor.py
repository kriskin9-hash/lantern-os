"""CSF v0.7 symbolic *primitives* (post-v2 consolidation).

This module once held a lossy ``ClassicalCompressor`` (a non-invertible
"symbolic" text/field compressor). That lossy compressor was **removed** in the
v2 CSF consolidation (2026-06) — use :mod:`csf` (zstd-backed, lossless) for real
compression. What remains here are the reusable, lossless primitives still
needed by the kept v0.7 binary container (:mod:`csf.v07.csf_file`) and the
Status-Cube store (:mod:`csf.status_cube`):

  * ``SymbolicDictionary`` — token ↔ id table (serialisable).
  * ``encode_sparse`` / ``decode_sparse`` — CSR-style sparse block coding.

No lossy or "ratio"-reporting code lives here anymore.
"""

from __future__ import annotations

import io
import struct
import zlib
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Tuple


# ------------------------------------------------------------------
# Dictionary Encoding (L1)
# ------------------------------------------------------------------

class SymbolicDictionary:
    """Adaptive dictionary for recurring tokens/anchors."""

    def __init__(self, min_freq: int = 3):
        self.min_freq = min_freq
        self._token_to_id: Dict[str, int] = {}
        self._id_to_token: Dict[int, str] = {}
        self._next_id = 1  # 0 reserved for unknown

    def train(self, tokens: List[str]) -> None:
        """Build dictionary from token frequency counts."""
        counts = Counter(tokens)
        for token, count in counts.most_common():
            if count < self.min_freq:
                break
            if token not in self._token_to_id:
                self._token_to_id[token] = self._next_id
                self._id_to_token[self._next_id] = token
                self._next_id += 1

    def encode(self, token: str) -> int:
        return self._token_to_id.get(token, 0)

    def decode(self, token_id: int) -> str:
        return self._id_to_token.get(token_id, f"?{token_id}")

    def to_bytes(self) -> bytes:
        """Serialize dictionary as: [count:2] then [id:2][len:1][token]."""
        buf = io.BytesIO()
        buf.write(struct.pack(">H", len(self._token_to_id)))
        for tid, token in sorted(self._id_to_token.items()):
            tok_bytes = token.encode("utf-8")
            buf.write(struct.pack(">HB", tid, len(tok_bytes)))
            buf.write(tok_bytes)
        return buf.getvalue()

    @classmethod
    def from_bytes(cls, data: bytes) -> "SymbolicDictionary":
        offset = 0
        count = struct.unpack_from(">H", data, offset)[0]
        offset += 2
        sd = cls()
        for _ in range(count):
            tid, tlen = struct.unpack_from(">HB", data, offset)
            offset += 3
            token = data[offset:offset + tlen].decode("utf-8")
            offset += tlen
            sd._token_to_id[token] = tid
            sd._id_to_token[tid] = token
            sd._next_id = max(sd._next_id, tid + 1)
        return sd


# ------------------------------------------------------------------
# Sparse CSR Encoding (L2)
# ------------------------------------------------------------------

@dataclass
class CSRBlock:
    """One sparse block: index + raw bytes."""
    block_index: int
    data: bytes


def encode_sparse(
    data: bytes,
    default_value: int = 0,
    block_size: int = 256,
) -> Tuple[bytes, bytes]:
    """Encode data as sparse blocks. Returns (meta_bytes, compressed_blocks)."""
    blocks: List[CSRBlock] = []
    for i in range(0, len(data), block_size):
        chunk = data[i:i + block_size]
        if any(b != default_value for b in chunk):
            blocks.append(CSRBlock(i // block_size, chunk))

    # Meta: original_length, block_size, default_value, num_blocks
    meta = struct.pack(">III", len(data), block_size, default_value)
    meta += struct.pack(">I", len(blocks))

    # Block data: [index:4][len:2][data] per block
    buf = io.BytesIO()
    for b in blocks:
        buf.write(struct.pack(">IH", b.block_index, len(b.data)))
        buf.write(b.data)

    compressed = zlib.compress(buf.getvalue(), level=3)
    return meta, compressed


def decode_sparse(meta: bytes, compressed: bytes) -> bytes:
    """Decode sparse blocks back to raw data."""
    orig_len, block_size, default_val = struct.unpack_from(">III", meta, 0)
    num_blocks = struct.unpack_from(">I", meta, 12)[0]

    raw = zlib.decompress(compressed)
    output = bytearray([default_val] * orig_len)

    offset = 0
    for _ in range(num_blocks):
        idx, blen = struct.unpack_from(">IH", raw, offset)
        offset += 6
        block_data = raw[offset:offset + blen]
        offset += blen
        start = idx * block_size
        end = min(start + blen, orig_len)
        output[start:end] = block_data[:end - start]

    return bytes(output)
