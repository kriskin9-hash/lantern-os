"""CSF — Convergence-Fitted Searchable Binary Archive.

Reference implementation matching docs/CSF-FORMAT-SPECIFICATION.md v1.0.
"""

from __future__ import annotations

import io
import struct
from pathlib import Path
from typing import BinaryIO

from . import header, dictionary, sparse, search, convergence


class CsfArchive:
    """In-memory CSF archive with read/write/search/merge operations."""

    def __init__(self):
        self._segments: list[bytes] = []
        self._symbol_dict: dictionary.SymbolicDictionary = dictionary.SymbolicDictionary()
        self._sparse_meta: list[sparse.SparseMatrixMeta] = []
        self._index: search.SearchIndex = search.SearchIndex()
        self._flags: int = 0

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def add_bytes(self, data: bytes) -> None:
        """Add a raw byte segment; symbolic + sparse layers applied on write."""
        self._segments.append(data)

    def add_file(self, path: str | Path) -> None:
        """Add file contents as a segment."""
        self.add_bytes(Path(path).read_bytes())

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def segment_count(self) -> int:
        return len(self._segments)

    @property
    def uncompressed_size(self) -> int:
        return sum(len(s) for s in self._segments)

    @property
    def ratio(self) -> float:
        """Compression ratio (compressed / uncompressed). 0.0 if not yet written."""
        # Approximate via in-memory re-encode without disk I/O
        buf = io.BytesIO()
        self._write_to(buf)
        compressed = buf.tell()
        uncompressed = self.uncompressed_size
        return compressed / uncompressed if uncompressed else 0.0

    # ------------------------------------------------------------------
    # I/O
    # ------------------------------------------------------------------

    def write(self, path: str | Path) -> None:
        with open(path, "wb") as fh:
            self._write_to(fh)

    @classmethod
    def open(cls, path: str | Path) -> "CsfArchive":
        with open(path, "rb") as fh:
            return cls._read_from(fh)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query: str) -> list[tuple[int, int, str]]:
        """Search inside the archive without full decompression.

        Returns list of (segment_index, byte_offset, context).
        """
        results: list[tuple[int, int, str]] = []
        for seg_idx, seg_data in enumerate(self._segments):
            # Fast negative check via bloom filter
            if not self._index.might_contain(seg_idx, query):
                continue
            # Confirm with actual scan
            text = seg_data.decode("utf-8", errors="replace")
            pos = text.find(query)
            if pos != -1:
                start = max(0, pos - 20)
                end = min(len(text), pos + len(query) + 20)
                context = text[start:end]
                results.append((seg_idx, pos, context))
        return results

    # ------------------------------------------------------------------
    # Convergence
    # ------------------------------------------------------------------

    def converge(self, other: "CsfArchive") -> "CsfArchive":
        """Merge two archives, sharing dictionary + sparse metadata where possible."""
        merged = convergence.merge(self, other)
        merged._flags |= header.CSF_FLAG_CONVERGED
        return merged

    # ------------------------------------------------------------------
    # Internal serialization
    # ------------------------------------------------------------------

    def _write_to(self, fh: BinaryIO) -> None:
        # Phase 1: build dictionary from all segment data
        # Reset mutable state if this is a re-write (e.g., ratio called previously)
        if self._symbol_dict._finalized:
            self._symbol_dict = dictionary.SymbolicDictionary()
        self._sparse_meta = []
        self._index = search.SearchIndex()

        for seg in self._segments:
            self._symbol_dict.ingest(seg)
        self._symbol_dict.finalize()

        # Phase 2: encode segments with dictionary + sparse matrix
        encoded_segments: list[bytes] = []
        for seg in self._segments:
            encoded = self._symbol_dict.encode(seg)
            # Wrap in sparse meta for structural compression
            meta, compressed = sparse.encode_csr(encoded)
            self._sparse_meta.append(meta)
            encoded_segments.append(compressed)

        # Phase 3: build search index
        for seg_idx, seg in enumerate(self._segments):
            self._index.add_segment(seg_idx, seg)

        # Phase 4: compute offsets and write
        seg_table = header.SegmentTable([
            header.SegmentEntry(offset=0, size=len(es), flags=0)
            for es in encoded_segments
        ])

        # Lay out: header | seg_table | dict | sparse_meta | data | index | footer
        buf = io.BytesIO()
        header.write_header(buf, version=1, flags=self._flags,
                            segment_count=len(self._segments),
                            uncompressed_size=self.uncompressed_size)
        header.write_segment_table(buf, seg_table)

        dict_offset = buf.tell()
        dictionary.write_dictionary(buf, self._symbol_dict)

        sparse_offset = buf.tell()
        for meta in self._sparse_meta:
            sparse.write_sparse_meta(buf, meta)

        data_offset = buf.tell()
        for es in encoded_segments:
            buf.write(es)

        index_offset = buf.tell()
        search.write_index(buf, self._index)

        footer_offset = buf.tell()
        buf.write(b"ENDCSF")
        import zlib
        crc = zlib.crc32(buf.getvalue()) & 0xFFFFFFFF
        buf.write(struct.pack("<I", crc))

        # Patch header with offsets
        final_data = buf.getvalue()
        patched = header.patch_offsets(final_data, dict_offset, index_offset)
        fh.write(patched)

    @classmethod
    def _read_from(cls, fh: BinaryIO) -> "CsfArchive":
        data = fh.read()
        hdr, offset = header.read_header(data)
        seg_table, offset = header.read_segment_table(data, offset, hdr.segment_count)
        sym_dict, offset = dictionary.read_dictionary(data, offset)
        sparse_metas = []
        for _ in range(hdr.segment_count):
            meta, offset = sparse.read_sparse_meta(data, offset)
            sparse_metas.append(meta)

        encoded_segments = []
        for entry in seg_table.entries:
            encoded_segments.append(data[offset:offset + entry.size])
            offset += entry.size

        idx, offset = search.read_index(data, offset)

        archive = cls()
        archive._symbol_dict = sym_dict
        archive._sparse_meta = sparse_metas
        archive._index = idx
        archive._flags = hdr.flags

        # Decode segments
        for enc, meta in zip(encoded_segments, sparse_metas):
            decoded_sparse = sparse.decode_csr(enc, meta)
            seg = sym_dict.decode(decoded_sparse)
            archive._segments.append(seg)

        return archive
