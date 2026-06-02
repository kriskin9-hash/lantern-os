"""Search Index Layer — Bloom filters + inverted index for symbol IDs.

Enables fast negative checks and confirmed positive searches
without full decompression.
"""

from __future__ import annotations

import io
import struct
import hashlib
import math
from typing import BinaryIO


class BloomFilter:
    """Simple Bloom filter for fast negative membership tests."""

    def __init__(self, size: int = 1024, hash_count: int = 3):
        self.size = size
        self.hash_count = hash_count
        self.bits = bytearray(size)

    def _hashes(self, item: str) -> list[int]:
        """Generate k hash positions for an item (bit positions)."""
        h1 = int(hashlib.md5(item.encode("utf-8")).hexdigest(), 16)
        h2 = int(hashlib.sha256(item.encode("utf-8")).hexdigest(), 16)
        total_bits = self.size * 8
        out = []
        for i in range(self.hash_count):
            idx = (h1 + i * h2) % total_bits
            out.append(idx)
        return out

    def add(self, item: str) -> None:
        for idx in self._hashes(item):
            byte_idx = idx // 8
            bit_idx = idx % 8
            self.bits[byte_idx] |= (1 << bit_idx)

    def might_contain(self, item: str) -> bool:
        for idx in self._hashes(item):
            byte_idx = idx // 8
            bit_idx = idx % 8
            if byte_idx >= len(self.bits):
                continue
            if not (self.bits[byte_idx] & (1 << bit_idx)):
                return False
        return True


class SearchIndex:
    """Per-segment bloom filters + inverted index for tokens."""

    def __init__(self):
        self._filters: list[BloomFilter] = []
        self._inverted: dict[str, list[int]] = {}  # token -> segment indices

    def add_segment(self, seg_idx: int, data: bytes) -> None:
        """Index a segment's content."""
        bf = BloomFilter(size=512, hash_count=2)
        # Tokenize on words; strip punctuation
        import re
        text = data.decode("utf-8", errors="replace")
        tokens = set(re.findall(r"[a-z0-9_]+", text.lower()))
        for token in tokens:
            bf.add(token)
            self._inverted.setdefault(token, []).append(seg_idx)
        # Ensure list length matches segment count
        while len(self._filters) <= seg_idx:
            self._filters.append(BloomFilter(size=512, hash_count=2))
        self._filters[seg_idx] = bf

    def might_contain(self, seg_idx: int, query: str) -> bool:
        if seg_idx >= len(self._filters):
            return True  # err on side of caution
        bf = self._filters[seg_idx]
        import re
        tokens = re.findall(r"[a-z0-9_]+", query.lower())
        if not tokens:
            return True
        return all(bf.might_contain(t) for t in tokens)

    def segments_with_token(self, token: str) -> list[int]:
        return self._inverted.get(token.lower(), [])


# ------------------------------------------------------------------
# Binary serialization
# ------------------------------------------------------------------

def write_index(fh: BinaryIO, index: SearchIndex) -> None:
    """Write search index to binary stream."""
    fh.write(struct.pack("<I", len(index._filters)))
    for bf in index._filters:
        fh.write(struct.pack("<I", bf.size))
        fh.write(struct.pack("<I", bf.hash_count))
        fh.write(bytes(bf.bits))
    # Inverted index
    fh.write(struct.pack("<I", len(index._inverted)))
    for token, seg_indices in index._inverted.items():
        token_bytes = token.encode("utf-8")
        fh.write(struct.pack("<H", len(token_bytes)))
        fh.write(token_bytes)
        fh.write(struct.pack("<I", len(seg_indices)))
        for sid in seg_indices:
            fh.write(struct.pack("<I", sid))


def read_index(data: bytes, offset: int) -> tuple[SearchIndex, int]:
    """Parse search index from raw bytes; return (SearchIndex, next_offset)."""
    idx = SearchIndex()
    filter_count = struct.unpack_from("<I", data, offset)[0]
    offset += 4
    for _ in range(filter_count):
        size = struct.unpack_from("<I", data, offset)[0]
        hash_count = struct.unpack_from("<I", data, offset + 4)[0]
        bit_bytes = data[offset + 8:offset + 8 + size]
        bf = BloomFilter(size=size, hash_count=hash_count)
        bf.bits = bytearray(bit_bytes)
        idx._filters.append(bf)
        offset += 8 + size

    inv_count = struct.unpack_from("<I", data, offset)[0]
    offset += 4
    for _ in range(inv_count):
        token_len = struct.unpack_from("<H", data, offset)[0]
        token = data[offset + 2:offset + 2 + token_len].decode("utf-8")
        offset += 2 + token_len
        seg_count = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        seg_indices = []
        for _ in range(seg_count):
            seg_indices.append(struct.unpack_from("<I", data, offset)[0])
            offset += 4
        idx._inverted[token] = seg_indices

    return idx, offset
