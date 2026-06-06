"""Dream Journal Delta Compressor (CSF Bridge)

Builds on CSF v0.7 infrastructure to compress dream journal JSONL entries.

Pipeline:
  1. Delta: consecutive entries → only changed fields
  2. Dictionary: recurring symbols/tags/emotions → integer codes
  3. Sparse: 3^12 ternary matrices → non-zero positions only
  4. Zstd: final byte-level pass

Safety: last 30 days kept as full JSONL fallback.
"""

from __future__ import annotations

import hashlib
import io
import json
import struct
import time
import zlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Reuse v07 symbolic dictionary
try:
    from .v07.symbolic_dictionary import SymbolicDictionary
except ImportError:
    import sys
    from pathlib import Path
    _repo = Path(__file__).resolve().parents[2]
    if str(_repo) not in sys.path:
        sys.path.insert(0, str(_repo))
    from src.csf.v07.symbolic_dictionary import SymbolicDictionary

# ------------------------------------------------------------------
#  Configuration
# ------------------------------------------------------------------

KEEP_FULL_DAYS = 30
MAX_DELTA_CHAIN = 7  # force a full snapshot every N deltas
BLOCK_SIZE = 512

# Fields that benefit from dictionary compression (symbolic / low cardinality)
DICT_FIELDS = {"emotions", "tags", "symbols", "ctf_glyphs", "mood", "technique"}

# Fields that are numeric / structural (skip dictionary)
NUMERIC_FIELDS = {"lucidity", "clarity", "recurring", "dreamsign"}

# Fields that form the stable identity of an entry
IDENTITY_FIELDS = {"id", "timestamp", "kind"}


# ------------------------------------------------------------------
#  Delta helpers
# ------------------------------------------------------------------

def _hash_entry(entry: Dict[str, Any]) -> str:
    """Stable hash for delta base referencing."""
    payload = json.dumps(entry, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def compute_delta(prev: Dict[str, Any], curr: Dict[str, Any]) -> Dict[str, Any]:
    """Return only fields that changed between prev and curr."""
    delta: Dict[str, Any] = {}
    for key, curr_val in curr.items():
        if key in IDENTITY_FIELDS:
            continue  # never delta identity fields
        prev_val = prev.get(key)
        if prev_val != curr_val:
            delta[key] = curr_val
    return delta


def apply_delta(base: Dict[str, Any], delta: Dict[str, Any]) -> Dict[str, Any]:
    """Reconstruct an entry by applying a delta to its base."""
    result = dict(base)
    for key, value in delta.items():
        result[key] = value
    return result


# ------------------------------------------------------------------
#  Dictionary Compression
# ------------------------------------------------------------------

class DreamDictionary:
    """Dictionary compressor tuned for dream journal fields.

    Maps recurring symbols, tags, emotions, and mood strings to small integers.
    """

    def __init__(self):
        self._dict = SymbolicDictionary(min_freq=1)
        # Seed with common emotional/symbolic vocabulary
        self._extra = {
            "joy": 1001, "fear": 1002, "sadness": 1003, "anger": 1004,
            "love": 1005, "peace": 1006, "anxiety": 1007, "wonder": 1008,
            "flying": 1009, "falling": 1010, "chasing": 1011, "water": 1012,
            "fire": 1013, "forest": 1014, "door": 1015, "light": 1016,
            "darkness": 1017, "mirror": 1018, "lucid": 1019, "vivid": 1020,
        }

    def encode_value(self, value: Any) -> Any:
        """Compress a single value through the dictionary."""
        if isinstance(value, str):
            low = value.lower()
            if low in self._extra:
                return {"__d": self._extra[low]}
            token_id = self._dict.encode(low)
            if token_id != 0:
                return {"__d": token_id}
        if isinstance(value, list):
            return [self.encode_value(v) for v in value]
        return value

    def decode_value(self, value: Any) -> Any:
        """Decompress a single value."""
        if isinstance(value, dict) and "__d" in value:
            code = value["__d"]
            # Try extra dict first
            for text, cid in self._extra.items():
                if cid == code:
                    return text
            # Fall back to symbolic dictionary
            token = self._dict.decode(code)
            return token if token else value
        if isinstance(value, list):
            return [self.decode_value(v) for v in value]
        return value

    def compress_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Compress symbolic fields in an entry."""
        out = {}
        for key, value in entry.items():
            if key in DICT_FIELDS and value is not None:
                out[key] = self.encode_value(value)
            else:
                out[key] = value
        return out

    def decompress_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Decompress symbolic fields."""
        out = {}
        for key, value in entry.items():
            if key in DICT_FIELDS and value is not None:
                out[key] = self.decode_value(value)
            else:
                out[key] = value
        return out


# ------------------------------------------------------------------
#  Sparse Ternary Encoder for 3^12 matrices
# ------------------------------------------------------------------

class SparseTernaryEncoder:
    """Encode 3^12 symbolic positions as sparse non-zero entries."""

    def __init__(self, dimensions: int = 12):
        self.dimensions = dimensions
        self.total_positions = 3 ** dimensions

    def encode_matrix(self, positions: Dict[int, int]) -> Dict[str, Any]:
        """Store only non-zero positions in 3^12 space.

        positions: {int_position -> ternary_value (0,1,2)}
        """
        sparse = {str(k): v for k, v in positions.items() if v != 0}
        return {
            "format": "sparse_ternary_v1",
            "dims": self.dimensions,
            "non_zero_count": len(sparse),
            "positions": sparse,
        }

    def decode_matrix(self, packed: Dict[str, Any]) -> Dict[int, int]:
        """Restore full position map (returns sparse dict)."""
        if packed.get("format") != "sparse_ternary_v1":
            raise ValueError("unknown sparse format")
        return {int(k): v for k, v in packed.get("positions", {}).items()}

    def entry_to_positions(self, entry: Dict[str, Any]) -> Dict[int, int]:
        """Map a dream entry's symbolic fields into 3^12 positions.

        This is a heuristic: each unique symbol/tag gets a hashed position.
        Most positions will be zero → sparse encoding wins big.
        """
        positions: Dict[int, int] = {}
        all_symbols = []
        for field in ("symbols", "tags", "ctf_glyphs"):
            all_symbols.extend(entry.get(field) or [])
        # Also hash mood/technique if present
        for field in ("mood", "technique"):
            val = entry.get(field)
            if val:
                all_symbols.append(str(val))

        for sym in all_symbols:
            h = hashlib.sha256(sym.lower().encode()).hexdigest()
            # Use first 12 base-3 digits as coordinates
            coords = []
            for ch in h:
                digit = int(ch, 16) % 3
                coords.append(digit)
                if len(coords) >= self.dimensions:
                    break
            while len(coords) < self.dimensions:
                coords.append(0)
            # Scalar position
            scalar = 0
            for d in coords:
                scalar = scalar * 3 + d
            positions[scalar] = 1  # mark as occupied

        return positions


# ------------------------------------------------------------------
#  Main Compressor / Decompressor
# ------------------------------------------------------------------

@dataclass
class CompressionStats:
    original_bytes: int = 0
    compressed_bytes: int = 0
    entries_total: int = 0
    full_entries: int = 0
    delta_entries: int = 0
    dictionary_hits: int = 0
    ratio: float = 0.0


class DreamCompressor:
    """End-to-end dream journal compressor."""

    def __init__(self, keep_full_days: int = KEEP_FULL_DAYS):
        self.keep_full_days = keep_full_days
        self.dictionary = DreamDictionary()
        self.ternary = SparseTernaryEncoder()
        self.stats = CompressionStats()

    def compress_journal(self, entries: List[Dict[str, Any]]) -> Tuple[bytes, CompressionStats]:
        """Compress a list of dream entries into a CSF-like stream."""
        if not entries:
            return b"", self.stats

        out = io.BytesIO()
        # Header
        header = {
            "format": "dream_csf_v1",
            "count": len(entries),
            "keep_full_days": self.keep_full_days,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        header_bytes = json.dumps(header, ensure_ascii=True).encode("utf-8")
        out.write(struct.pack(">I", len(header_bytes)))
        out.write(header_bytes)

        original_total = 0
        compressed_total = out.tell()
        last_full: Optional[Dict[str, Any]] = None
        last_hash = ""
        delta_count = 0

        now = datetime.now(timezone.utc)

        for idx, entry in enumerate(entries):
            entry_bytes = json.dumps(entry, ensure_ascii=True).encode("utf-8")
            original_total += len(entry_bytes)

            # Determine if this should be a full entry or a delta
            entry_time = None
            try:
                ts = entry.get("timestamp", "")
                if ts:
                    entry_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                pass

            age_days = (now - entry_time).total_seconds() / 86400 if entry_time else 999
            force_full = age_days <= self.keep_full_days
            chain_broken = delta_count >= MAX_DELTA_CHAIN

            if force_full or chain_broken or last_full is None:
                # Full entry
                compressed = self.dictionary.compress_entry(entry)
                record = {
                    "type": "full",
                    "seq": idx,
                    "hash": _hash_entry(entry),
                    "data": compressed,
                }
                # Embed sparse ternary matrix for symbolic analysis
                positions = self.ternary.entry_to_positions(entry)
                if positions:
                    record["ternary"] = self.ternary.encode_matrix(positions)

                last_full = dict(entry)
                last_hash = record["hash"]
                delta_count = 0
                self.stats.full_entries += 1
            else:
                # Delta entry
                delta = compute_delta(last_full, entry)
                if not delta:
                    # Identical entry — store minimal marker
                    record = {
                        "type": "delta",
                        "seq": idx,
                        "base_hash": last_hash,
                        "delta": {},
                        "identical": True,
                    }
                else:
                    compressed_delta = self.dictionary.compress_entry(delta)
                    record = {
                        "type": "delta",
                        "seq": idx,
                        "base_hash": last_hash,
                        "delta": compressed_delta,
                    }
                delta_count += 1
                self.stats.delta_entries += 1
                # Update last_full so next delta is chained correctly
                last_full = apply_delta(last_full, delta)
                last_hash = _hash_entry(last_full)

            record_bytes = json.dumps(record, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
            out.write(struct.pack(">I", len(record_bytes)))
            out.write(record_bytes)
            compressed_total += 4 + len(record_bytes)

        # Final zstd pass
        raw = out.getvalue()
        final = zlib.compress(raw, level=3)

        self.stats.original_bytes = original_total
        self.stats.compressed_bytes = len(final)
        self.stats.entries_total = len(entries)
        self.stats.ratio = (
            1.0 - (len(final) / original_total) if original_total else 0.0
        )

        return final, self.stats

    def decompress_journal(self, data: bytes) -> Tuple[List[Dict[str, Any]], CompressionStats]:
        """Decompress a dream journal CSF stream back to entries."""
        raw = zlib.decompress(data)
        stream = io.BytesIO(raw)

        # Header
        header_len = struct.unpack(">I", stream.read(4))[0]
        header = json.loads(stream.read(header_len).decode("utf-8"))
        if header.get("format") != "dream_csf_v1":
            raise ValueError("unsupported format")

        entries: List[Dict[str, Any]] = []
        last_full: Optional[Dict[str, Any]] = None

        while True:
            size_bytes = stream.read(4)
            if len(size_bytes) < 4:
                break
            record_len = struct.unpack(">I", size_bytes)[0]
            record = json.loads(stream.read(record_len).decode("utf-8"))

            if record["type"] == "full":
                entry = self.dictionary.decompress_entry(record["data"])
                last_full = dict(entry)
                entries.append(entry)
            elif record["type"] == "delta":
                if last_full is None:
                    raise ValueError("delta record with no base")
                delta = self.dictionary.decompress_entry(record.get("delta", {}))
                entry = apply_delta(last_full, delta)
                last_full = entry
                entries.append(entry)
            else:
                raise ValueError(f"unknown record type: {record['type']}")

        return entries, self.stats


# ------------------------------------------------------------------
#  CLI / Direct invocation
# ------------------------------------------------------------------

def compress_dream_file(input_path: Path, output_path: Optional[Path] = None) -> CompressionStats:
    """Compress a single dream journal JSONL file."""
    entries = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    comp = DreamCompressor()
    data, stats = comp.compress_journal(entries)

    out_path = output_path or input_path.with_suffix(".csf")
    with open(out_path, "wb") as f:
        f.write(data)

    print(f"Compressed {stats.entries_total} entries → {out_path}")
    print(f"  Original: {stats.original_bytes:,} bytes")
    print(f"  Compressed: {stats.compressed_bytes:,} bytes")
    print(f"  Ratio: {stats.ratio:.2%}")
    print(f"  Full entries: {stats.full_entries}, Delta entries: {stats.delta_entries}")
    return stats


def decompress_dream_file(input_path: Path, output_path: Path) -> List[Dict[str, Any]]:
    """Decompress a .csf dream journal back to JSONL."""
    with open(input_path, "rb") as f:
        data = f.read()

    comp = DreamCompressor()
    entries, _stats = comp.decompress_journal(data)

    with open(output_path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"Decompressed {len(entries)} entries → {output_path}")
    return entries


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Dream Journal CSF Compressor")
    sub = parser.add_subparsers(dest="command")

    p_compress = sub.add_parser("compress")
    p_compress.add_argument("input", type=Path)
    p_compress.add_argument("--output", type=Path, default=None)

    p_decompress = sub.add_parser("decompress")
    p_decompress.add_argument("input", type=Path)
    p_decompress.add_argument("output", type=Path)

    p_benchmark = sub.add_parser("benchmark")
    p_benchmark.add_argument("input", type=Path)

    args = parser.parse_args()

    if args.command == "compress":
        compress_dream_file(args.input, args.output)
    elif args.command == "decompress":
        decompress_dream_file(args.input, args.output)
    elif args.command == "benchmark":
        entries = []
        with open(args.input, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        comp = DreamCompressor()
        start = time.time()
        data, stats = comp.compress_journal(entries)
        compress_ms = round((time.time() - start) * 1000, 2)

        start = time.time()
        restored, _ = comp.decompress_journal(data)
        decompress_ms = round((time.time() - start) * 1000, 2)

        # Verify roundtrip
        ok = len(entries) == len(restored)
        if ok:
            for a, b in zip(entries, restored):
                if a != b:
                    ok = False
                    break

        print(f"Benchmark: {stats.entries_total} entries")
        print(f"  Compress:   {compress_ms} ms")
        print(f"  Decompress: {decompress_ms} ms")
        print(f"  Original:   {stats.original_bytes:,} bytes")
        print(f"  Compressed: {stats.compressed_bytes:,} bytes")
        print(f"  Ratio:      {stats.ratio:.2%}")
        print(f"  Full: {stats.full_entries}, Delta: {stats.delta_entries}")
        print(f"  Roundtrip:  {'PASS' if ok else 'FAIL'}")
    else:
        parser.print_help()
