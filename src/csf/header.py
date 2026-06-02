"""CSF header and segment table serialization.

Binary layout per CSF-FORMAT-SPECIFICATION.md §4.
"""

from __future__ import annotations

import io
import struct
from dataclasses import dataclass
from typing import BinaryIO


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CSF_MAGIC = b"CSFv1\0\0\0"
CSF_HEADER_SIZE = 72
CSF_FOOTER_SIZE = 10  # "ENDCSF" + CRC-32C

CSF_FLAG_HAS_INDEX = 0x00000001
CSF_FLAG_CONVERGED = 0x00000002
CSF_FLAG_ENCRYPTED = 0x00000004
CSF_FLAG_STREAMING = 0x00000008


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Header:
    version: int
    flags: int
    segment_count: int
    uncompressed_size: int
    dictionary_offset: int
    index_offset: int
    header_checksum: int


@dataclass(frozen=True, slots=True)
class SegmentEntry:
    offset: int
    size: int
    flags: int


@dataclass(frozen=True, slots=True)
class SegmentTable:
    entries: list[SegmentEntry]


# ---------------------------------------------------------------------------
# Write helpers
# ---------------------------------------------------------------------------

def write_header(fh: BinaryIO, *, version: int, flags: int, segment_count: int,
                 uncompressed_size: int) -> None:
    """Write a 64-byte header with placeholder offsets (patched later)."""
    fh.write(CSF_MAGIC)
    fh.write(struct.pack("<H", version))
    fh.write(struct.pack("<I", flags))
    fh.write(struct.pack("<I", segment_count))
    fh.write(struct.pack("<Q", uncompressed_size))
    fh.write(struct.pack("<Q", 0))   # dictionary_offset placeholder
    fh.write(struct.pack("<Q", 0))   # index_offset placeholder
    fh.write(struct.pack("<Q", 0))   # header_checksum placeholder
    fh.write(b"\0" * 22)             # reserved


def write_segment_table(fh: BinaryIO, table: SegmentTable) -> None:
    fh.write(struct.pack("<I", len(table.entries)))
    for entry in table.entries:
        fh.write(struct.pack("<Q", entry.offset))
        fh.write(struct.pack("<Q", entry.size))
        fh.write(struct.pack("<I", entry.flags))


def patch_offsets(data: bytes, dictionary_offset: int, index_offset: int) -> bytes:
    """Patch placeholder offsets into an already-serialized header."""
    bytearray_data = bytearray(data)
    # Magic (8) + Version (2) + Flags (4) + SegmentCount (4) + UncompressedSize (8)
    # = 26 bytes; next is DictionaryOffset at byte 26
    struct.pack_into("<Q", bytearray_data, 26, dictionary_offset)
    struct.pack_into("<Q", bytearray_data, 34, index_offset)
    # Compute header checksum (xxHash64 of bytes 0–41)
    try:
        import xxhash
        checksum = xxhash.xxh64(bytes(bytearray_data[:42])).intdigest()
    except Exception:
        import hashlib
        checksum = int(hashlib.sha256(bytes(bytearray_data[:42])).hexdigest()[:16], 16)
    struct.pack_into("<Q", bytearray_data, 42, checksum)
    return bytes(bytearray_data)


# ---------------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------------

def read_header(data: bytes) -> tuple[Header, int]:
    """Parse header from raw bytes; return (Header, next_offset)."""
    if data[:8] != CSF_MAGIC:
        raise ValueError("Invalid CSF magic number")
    version = struct.unpack_from("<H", data, 8)[0]
    flags = struct.unpack_from("<I", data, 10)[0]
    segment_count = struct.unpack_from("<I", data, 14)[0]
    uncompressed_size = struct.unpack_from("<Q", data, 18)[0]
    dictionary_offset = struct.unpack_from("<Q", data, 26)[0]
    index_offset = struct.unpack_from("<Q", data, 34)[0]
    header_checksum = struct.unpack_from("<Q", data, 42)[0]
    return Header(
        version=version, flags=flags, segment_count=segment_count,
        uncompressed_size=uncompressed_size,
        dictionary_offset=dictionary_offset, index_offset=index_offset,
        header_checksum=header_checksum,
    ), CSF_HEADER_SIZE


def read_segment_table(data: bytes, offset: int, count: int) -> tuple[SegmentTable, int]:
    """Parse segment table; return (SegmentTable, next_offset)."""
    stored_count = struct.unpack_from("<I", data, offset)[0]
    offset += 4
    entries = []
    for _ in range(stored_count):
        off = struct.unpack_from("<Q", data, offset)[0]
        size = struct.unpack_from("<Q", data, offset + 8)[0]
        flags = struct.unpack_from("<I", data, offset + 16)[0]
        entries.append(SegmentEntry(offset=off, size=size, flags=flags))
        offset += 20
    return SegmentTable(entries=entries), offset
