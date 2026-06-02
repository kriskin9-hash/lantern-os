"""Symbolic Dictionary Layer (L1) — frequency-sorted symbol table.

Recurring strings are mapped to compact 2-byte IDs.
"""

from __future__ import annotations

import io
import struct
import re
from collections import Counter
from typing import BinaryIO


class SymbolicDictionary:
    """Builds a frequency dictionary from raw bytes, then encodes/decodes."""

    # Tokenization: split on non-alphanumeric, keep words ≥ 2 chars
    _TOKEN_RE = re.compile(rb"[A-Za-z0-9_]{2,}")

    def __init__(self):
        self._freq: Counter[bytes] = Counter()
        self._id_to_symbol: list[bytes] = []
        self._symbol_to_id: dict[bytes, int] = {}
        self._finalized: bool = False
        self._max_symbols: int = 65535

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def ingest(self, data: bytes) -> None:
        """Scan raw bytes and count token frequencies."""
        if self._finalized:
            raise RuntimeError("Dictionary already finalized")
        for token in self._TOKEN_RE.findall(data):
            self._freq[token] += 1

    def finalize(self) -> None:
        """Sort by frequency descending, assign IDs, cap at 65535 symbols."""
        if self._finalized:
            return
        most_common = self._freq.most_common(self._max_symbols)
        self._id_to_symbol = [token for token, _ in most_common]
        self._symbol_to_id = {token: idx for idx, token in enumerate(self._id_to_symbol)}
        self._finalized = True

    # ------------------------------------------------------------------
    # Encode / Decode
    # ------------------------------------------------------------------

    def encode(self, data: bytes) -> bytes:
        """Replace frequent tokens with 2-byte escape sequences (0xFF + ID)."""
        if not self._finalized:
            self.finalize()
        out = bytearray()
        pos = 0
        while pos < len(data):
            # Try to match longest known symbol at this position
            best_token: bytes | None = None
            best_id = -1
            best_len = 0
            # Scan forward up to max reasonable token length (64)
            for end in range(min(pos + 2, len(data)), min(pos + 64, len(data)) + 1):
                substr = data[pos:end]
                if substr in self._symbol_to_id:
                    best_token = substr
                    best_id = self._symbol_to_id[substr]
                    best_len = len(substr)
            if best_token is not None:
                out.append(0xFF)
                out.extend(struct.pack("<H", best_id))
                pos += best_len
            else:
                # Escape literal 0xFF as 0xFF 0xFF
                b = data[pos]
                if b == 0xFF:
                    out.append(0xFF)
                    out.append(0xFF)
                else:
                    out.append(b)
                pos += 1
        return bytes(out)

    def decode(self, data: bytes) -> bytes:
        """Expand escape sequences back to original tokens."""
        out = bytearray()
        pos = 0
        while pos < len(data):
            if data[pos] == 0xFF:
                if pos + 1 < len(data) and data[pos + 1] == 0xFF:
                    out.append(0xFF)
                    pos += 2
                elif pos + 2 < len(data):
                    sid = struct.unpack_from("<H", data, pos + 1)[0]
                    if sid < len(self._id_to_symbol):
                        out.extend(self._id_to_symbol[sid])
                    pos += 3
                else:
                    # Trailing escape, treat as literal
                    out.append(data[pos])
                    pos += 1
            else:
                out.append(data[pos])
                pos += 1
        return bytes(out)

    @property
    def symbol_count(self) -> int:
        return len(self._id_to_symbol)


# ------------------------------------------------------------------
# Binary serialization
# ------------------------------------------------------------------

def write_dictionary(fh: BinaryIO, sym_dict: SymbolicDictionary) -> None:
    """Write dictionary to binary stream."""
    symbols = sym_dict._id_to_symbol
    fh.write(struct.pack("<I", len(symbols)))
    for sid, token in enumerate(symbols):
        fh.write(struct.pack("<H", sid))
        fh.write(struct.pack("<H", len(token)))
        fh.write(token)


def read_dictionary(data: bytes, offset: int) -> tuple[SymbolicDictionary, int]:
    """Parse dictionary from raw bytes; return (SymbolicDictionary, next_offset)."""
    count = struct.unpack_from("<I", data, offset)[0]
    offset += 4
    sym_dict = SymbolicDictionary()
    sym_dict._id_to_symbol = []
    for _ in range(count):
        sid = struct.unpack_from("<H", data, offset)[0]
        length = struct.unpack_from("<H", data, offset + 2)[0]
        token = data[offset + 4:offset + 4 + length]
        sym_dict._id_to_symbol.append(token)
        offset += 4 + length
    sym_dict._symbol_to_id = {token: idx for idx, token in enumerate(sym_dict._id_to_symbol)}
    sym_dict._finalized = True
    return sym_dict, offset
