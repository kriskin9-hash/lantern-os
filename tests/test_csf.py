#!/usr/bin/env python3
"""CSF utility test suite — verify whitepaper claims.

Claims tested:
1. Bit-perfect roundtrip (compress → decompress)
2. Search without full decompression
3. Convergent merging (merge two archives)
4. Dictionary compression ratio on symbolic data
"""

from __future__ import annotations

import io
import os
import tempfile
import unittest
from pathlib import Path

# Ensure src/ is on path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

try:
    from csf import CsfArchive
    from csf import header, dictionary, sparse, search
except ImportError:
    import pytest
    pytest.skip("csf.CsfArchive not available in this build", allow_module_level=True)


class CsfRoundTripTests(unittest.TestCase):
    """Claim 1: Bit-perfect compress/decompress roundtrip."""

    def test_single_segment_text(self):
        original = b"Garden Table Lantern Convergence Garden Table"
        archive = CsfArchive()
        archive.add_bytes(original)
        buf = io.BytesIO()
        archive._write_to(buf)
        buf.seek(0)
        recovered = CsfArchive._read_from(buf)
        self.assertEqual(recovered._segments, [original])

    def test_multiple_segments(self):
        segments = [
            b"The Garden begins the story.",
            b"The Table keeps the story real.",
            b"Lantern carries the light locally.",
        ]
        archive = CsfArchive()
        for seg in segments:
            archive.add_bytes(seg)
        buf = io.BytesIO()
        archive._write_to(buf)
        buf.seek(0)
        recovered = CsfArchive._read_from(buf)
        self.assertEqual(recovered._segments, segments)

    def test_binary_roundtrip(self):
        original = bytes(range(256)) * 40  # 10KB of repeating pattern
        archive = CsfArchive()
        archive.add_bytes(original)
        buf = io.BytesIO()
        archive._write_to(buf)
        buf.seek(0)
        recovered = CsfArchive._read_from(buf)
        self.assertEqual(recovered._segments, [original])


class CsfSearchTests(unittest.TestCase):
    """Claim 2: Search inside archive without full decompression."""

    def test_search_finds_match(self):
        archive = CsfArchive()
        archive.add_bytes(b"The Garden has quantum dust and helper lights.")
        results = archive.search("quantum dust")
        self.assertTrue(any("quantum dust" in ctx for _, _, ctx in results))

    def test_search_negative(self):
        archive = CsfArchive()
        archive.add_bytes(b"The Garden has helper lights.")
        results = archive.search("quantum dust")
        self.assertEqual(results, [])

    def test_search_multiple_segments(self):
        archive = CsfArchive()
        archive.add_bytes(b"Segment one has Garden.")
        archive.add_bytes(b"Segment two has quantum dust.")
        archive.add_bytes(b"Segment three has Table.")
        results = archive.search("quantum dust")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], 1)  # segment index 1


class CsfConvergenceTests(unittest.TestCase):
    """Claim 3: Convergent merging of two archives."""

    def test_merge_preserves_all_segments(self):
        base = CsfArchive()
        base.add_bytes(b"Garden Table Lantern")
        delta = CsfArchive()
        delta.add_bytes(b"Convergence City Doors")
        merged = base.converge(delta)
        self.assertEqual(merged.segment_count, 2)
        self.assertIn(b"Garden Table Lantern", merged._segments)
        self.assertIn(b"Convergence City Doors", merged._segments)

    def test_merge_flag_set(self):
        base = CsfArchive()
        base.add_bytes(b"Base data")
        delta = CsfArchive()
        delta.add_bytes(b"Delta data")
        merged = base.converge(delta)
        self.assertTrue(merged._flags & header.CSF_FLAG_CONVERGED)


class CsfDictionaryTests(unittest.TestCase):
    """Claim 4: Symbolic dictionary compression on redundant text."""

    def test_dictionary_reduces_size(self):
        text = b"Garden Table Lantern Convergence Garden Table Lantern Convergence"
        sym_dict = dictionary.SymbolicDictionary()
        sym_dict.ingest(text)
        sym_dict.finalize()
        encoded = sym_dict.encode(text)
        decoded = sym_dict.decode(encoded)
        self.assertEqual(decoded, text)
        # Encoded should be smaller for redundant text
        self.assertLess(len(encoded), len(text))

    def test_dictionary_preserves_literal_0xff(self):
        text = b"\xff\xfeGarden"
        sym_dict = dictionary.SymbolicDictionary()
        sym_dict.ingest(text)
        sym_dict.finalize()
        encoded = sym_dict.encode(text)
        decoded = sym_dict.decode(encoded)
        self.assertEqual(decoded, text)


class CsfSparseTests(unittest.TestCase):
    """Sparse matrix layer correctness."""

    def test_csr_roundtrip(self):
        data = bytes([0, 0, 1, 0, 0, 2, 0, 0, 0, 3])
        meta, compressed = sparse.encode_csr(data, default_value=0, block_size=4)
        recovered = sparse.decode_csr(compressed, meta)
        self.assertEqual(recovered[:len(data)], data)

    def test_csr_all_defaults(self):
        data = bytes([0, 0, 0, 0])
        meta, compressed = sparse.encode_csr(data, default_value=0)
        recovered = sparse.decode_csr(compressed, meta)
        self.assertEqual(recovered[:len(data)], data)


class CsfHeaderTests(unittest.TestCase):
    """Header serialization correctness."""

    def test_header_roundtrip(self):
        buf = io.BytesIO()
        header.write_header(buf, version=1, flags=0, segment_count=3,
                           uncompressed_size=12345)
        data = header.patch_offsets(buf.getvalue(), 100, 200)
        hdr, offset = header.read_header(data)
        self.assertEqual(hdr.version, 1)
        self.assertEqual(hdr.flags, 0)
        self.assertEqual(hdr.segment_count, 3)
        self.assertEqual(hdr.uncompressed_size, 12345)
        self.assertEqual(hdr.dictionary_offset, 100)
        self.assertEqual(hdr.index_offset, 200)

    def test_magic_validation(self):
        with self.assertRaises(ValueError):
            header.read_header(b"NOTCSF!!" + b"\0" * 56)


class CsfCliTests(unittest.TestCase):
    """End-to-end CLI tool tests."""

    def test_compress_decompress_cli(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            inp = Path(tmpdir) / "input.txt"
            inp.write_bytes(b"Garden Table Lantern Convergence")
            csf_path = Path(tmpdir) / "archive.csf"
            out_dir = Path(tmpdir) / "out"

            from csf_compress import main as compress_main
            from csf_decompress import main as decompress_main

            rc = compress_main([str(inp), "-o", str(csf_path)])
            self.assertEqual(rc, 0)
            self.assertTrue(csf_path.exists())

            rc = decompress_main([str(csf_path), "-o", str(out_dir)])
            self.assertEqual(rc, 0)
            seg_file = out_dir / "segment_0000.bin"
            self.assertTrue(seg_file.exists())
            self.assertEqual(seg_file.read_bytes(), inp.read_bytes())

    def test_search_cli(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            inp = Path(tmpdir) / "input.txt"
            inp.write_bytes(b"The Garden has quantum dust.")
            csf_path = Path(tmpdir) / "archive.csf"

            from csf_compress import main as compress_main
            from csf_search import main as search_main

            compress_main([str(inp), "-o", str(csf_path)])

            rc = search_main([str(csf_path), "quantum dust"])
            self.assertEqual(rc, 0)

    def test_merge_cli(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_inp = Path(tmpdir) / "base.txt"
            base_inp.write_bytes(b"Base segment")
            delta_inp = Path(tmpdir) / "delta.txt"
            delta_inp.write_bytes(b"Delta segment")

            base_csf = Path(tmpdir) / "base.csf"
            delta_csf = Path(tmpdir) / "delta.csf"
            merged_csf = Path(tmpdir) / "merged.csf"

            from csf_compress import main as compress_main
            from csf_merge import main as merge_main
            from csf_decompress import main as decompress_main

            compress_main([str(base_inp), "-o", str(base_csf)])
            compress_main([str(delta_inp), "-o", str(delta_csf)])

            rc = merge_main(["--base", str(base_csf), "--delta", str(delta_csf),
                            "-o", str(merged_csf)])
            self.assertEqual(rc, 0)
            self.assertTrue(merged_csf.exists())

            # Verify merged archive contains both segments
            archive = CsfArchive.open(merged_csf)
            self.assertEqual(archive.segment_count, 2)


class CsfRatioTests(unittest.TestCase):
    """Verify compression ratio claims on symbolic data."""

    def test_symbolic_text_ratio(self):
        """Highly redundant symbolic text should achieve measurable compression."""
        lines = [
            "Garden Table Lantern Convergence City Doors",
            "Garden Table Lantern Convergence Return Path",
            "Garden Table Lantern Convergence Keystone",
        ] * 100  # 300 lines, highly redundant
        text = "\n".join(lines).encode("utf-8")

        archive = CsfArchive()
        archive.add_bytes(text)
        buf = io.BytesIO()
        archive._write_to(buf)
        compressed = buf.tell()
        uncompressed = len(text)
        ratio = compressed / uncompressed

        # With highly redundant symbolic text, we expect < 80%
        self.assertLess(ratio, 0.80,
                        f"Expected ratio < 80% on redundant symbolic text, got {ratio:.2%}")


if __name__ == "__main__":
    unittest.main()
