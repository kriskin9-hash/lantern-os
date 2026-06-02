"""Sparse Matrix Layer (L2) — Compressed Sparse Row (CSR) encoding.

Structural compression for repeated/default values.
"""

from __future__ import annotations

import io
import struct
import zlib
from dataclasses import dataclass
from typing import BinaryIO


@dataclass(frozen=True, slots=True)
class SparseMatrixMeta:
    row_count: int
    col_count: int
    nonzero_count: int
    default_value: int
    original_length: int


# ------------------------------------------------------------------
# Encode / Decode
# ------------------------------------------------------------------

def encode_csr(data: bytes, default_value: int = 0, block_size: int = 256) -> tuple[SparseMatrixMeta, bytes]:
    """Encode byte sequence as CSR-like sparse representation.

    Data is chunked into blocks. Blocks that are all default_value are omitted.
    Non-default blocks are stored with (block_index, block_data) pairs.
    """
    rows: list[int] = []
    cols: list[int] = []
    values: list[int] = []

    for i, b in enumerate(data):
        if b != default_value:
            rows.append(i // block_size)
            cols.append(i % block_size)
            values.append(b)

    meta = SparseMatrixMeta(
        row_count=(len(data) + block_size - 1) // block_size,
        col_count=block_size,
        nonzero_count=len(values),
        default_value=default_value,
        original_length=len(data),
    )

    # Pack: row_ptrs (varint-delta), col_indices (varint), values (raw bytes)
    buf = io.BytesIO()
    _write_varints(buf, _delta_encode(rows))
    _write_varints(buf, cols)
    buf.write(bytes(values))
    compressed = zlib.compress(buf.getvalue(), level=3)
    return meta, compressed


def decode_csr(compressed: bytes, meta: SparseMatrixMeta) -> bytes:
    """Decode CSR-like representation back to raw bytes."""
    raw = zlib.decompress(compressed)
    buf = io.BytesIO(raw)

    delta_rows = _read_varints(buf, meta.nonzero_count)
    rows = _delta_decode(delta_rows)
    cols = _read_varints(buf, meta.nonzero_count)
    values = list(buf.read(meta.nonzero_count))

    output = bytearray(meta.row_count * meta.col_count)
    output[:] = bytes([meta.default_value]) * len(output)
    for r, c, v in zip(rows, cols, values):
        idx = r * meta.col_count + c
        if idx < len(output):
            output[idx] = v

    # Trim to actual original data length
    trimmed = output[:meta.original_length]
    return bytes(trimmed)


# ------------------------------------------------------------------
# Binary serialization
# ------------------------------------------------------------------

def write_sparse_meta(fh: BinaryIO, meta: SparseMatrixMeta) -> None:
    fh.write(struct.pack("<Q", meta.row_count))
    fh.write(struct.pack("<I", meta.col_count))
    fh.write(struct.pack("<Q", meta.nonzero_count))
    fh.write(struct.pack("<B", meta.default_value))
    fh.write(struct.pack("<Q", meta.original_length))


def read_sparse_meta(data: bytes, offset: int) -> tuple[SparseMatrixMeta, int]:
    row_count = struct.unpack_from("<Q", data, offset)[0]
    col_count = struct.unpack_from("<I", data, offset + 8)[0]
    nonzero_count = struct.unpack_from("<Q", data, offset + 12)[0]
    default_value = struct.unpack_from("<B", data, offset + 20)[0]
    original_length = struct.unpack_from("<Q", data, offset + 21)[0]
    meta = SparseMatrixMeta(row_count, col_count, nonzero_count, default_value, original_length)
    return meta, offset + 29


# ------------------------------------------------------------------
# Varint helpers (simple LEB128-ish)
# ------------------------------------------------------------------

def _write_varints(fh: io.BytesIO, values: list[int]) -> None:
    for v in values:
        # Write as unsigned varint
        while v >= 128:
            fh.write(bytes([(v & 0x7F) | 0x80]))
            v >>= 7
        fh.write(bytes([v]))


def _read_varints(buf: io.BytesIO, count: int) -> list[int]:
    out = []
    for _ in range(count):
        v = 0
        shift = 0
        while True:
            b = ord(buf.read(1))
            v |= (b & 0x7F) << shift
            if (b & 0x80) == 0:
                break
            shift += 7
        out.append(v)
    return out


def _delta_encode(values: list[int]) -> list[int]:
    out = []
    prev = 0
    for v in values:
        out.append(v - prev)
        prev = v
    return out


def _delta_decode(deltas: list[int]) -> list[int]:
    out = []
    prev = 0
    for d in deltas:
        prev += d
        out.append(prev)
    return out
