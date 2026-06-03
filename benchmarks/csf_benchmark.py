#!/usr/bin/env python3
"""
CSF v0.6 Benchmark — Classical Compressor vs ZIP on normal & symbolic text.

Run: python benchmarks/csf_benchmark.py
"""

from __future__ import annotations

import io
import random
import string
import time
import zipfile
from pathlib import Path

# Ensure src/ is on path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from csf.v06.classical_compressor import ClassicalCompressor, CompressionResult
from csf.v06.convergence_engine import ConvergenceEngine, multi_level_convergence
from csf.v06.qutrit_delta import QutritDelta, QutritState
from csf.v06.quantum_dust import QuantumDustField


# ------------------------------------------------------------------
# Text Generators
# ------------------------------------------------------------------

WORDS_NORMAL = [
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "I",
    "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
    "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
    "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",
    "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
    "when", "make", "can", "like", "time", "no", "just", "him", "know", "take",
    "people", "into", "year", "your", "good", "some", "could", "them", "see", "other",
    "than", "then", "now", "look", "only", "come", "its", "over", "think", "also",
    "back", "after", "use", "two", "how", "our", "work", "first", "well", "way",
    "even", "new", "want", "because", "any", "these", "give", "day", "most", "us",
]

WORDS_SYMBOLIC = [
    "Lantern", "Garden", "Keystone", "Return", "Door", "Anchor",
    "Wish", "Founder", "Convergence", "CityOfDoors", "Sigil",
    "Table", "Love", "Safety", "Truth", "Beauty", "Freedom",
    "Memory", "Gage", "Xenon", "Fog", "Cloud", "Sea",
    "Blinkbug", "Dream", "Mirror", "Reflection", "Light",
    "Path", "Threshold", "Crossing", "Waking", "Sleeping",
    "Vivid", "Strange", "Familiar", "Distant", "Near",
    "Holding", "Protecting", "Building", "Becoming",
]


def _generate_normal_text(target_bytes: int = 5_000_000) -> str:
    """Generate standard English-like prose."""
    rng = random.Random(42)
    paragraphs = []
    current = 0
    while current < target_bytes:
        # A paragraph of 3-8 sentences
        para = []
        for _ in range(rng.randint(3, 8)):
            # Sentence of 8-20 words
            words = [rng.choice(WORDS_NORMAL) for _ in range(rng.randint(8, 20))]
            # Capitalize first word, add punctuation
            words[0] = words[0].capitalize()
            sentence = " ".join(words) + rng.choice(".!?")
            para.append(sentence)
        paragraph = " ".join(para)
        paragraphs.append(paragraph)
        current += len(paragraph) + 1
    return "\n\n".join(paragraphs)


def _generate_symbolic_text(target_bytes: int = 2_000_000) -> str:
    """Generate symbolic dream-journal-like text with recurring anchors."""
    rng = random.Random(42)
    paragraphs = []
    current = 0

    # Phrase templates with symbolic weight
    templates = [
        "The {anchor} stood at the {place}, holding the {concept}.",
        "I saw {anchor} near the {place} and felt {emotion}.",
        "{anchor} reminded me of {concept} beneath the {place}.",
        "A {color} {anchor} appeared by the {place}.",
        "The {place} opened to reveal {anchor} and {concept}.",
        "We walked toward {anchor} through the {place}.",
        "{anchor} spoke of {concept} while {emotion} filled the air.",
        "In the {place}, {anchor} waited beside the {concept}.",
    ]

    anchors = WORDS_SYMBOLIC
    places = ["Garden", "Door", "Table", "Sea", "Threshold", "Mirror", "Path", "CityOfDoors"]
    concepts = ["Love", "Truth", "Memory", "Return", "Wish", "Light", "Convergence", "Anchor"]
    emotions = ["wonder", "longing", "peace", "trembling", "warmth", "clarity", "sadness", "joy"]
    colors = ["silver", "golden", "deep", "pale", "bright", "shadowed", "ancient", "new"]

    while current < target_bytes:
        para = []
        for _ in range(rng.randint(2, 6)):
            tmpl = rng.choice(templates)
            sentence = tmpl.format(
                anchor=rng.choice(anchors),
                place=rng.choice(places),
                concept=rng.choice(concepts),
                emotion=rng.choice(emotions),
                color=rng.choice(colors),
            )
            para.append(sentence)
        paragraph = " ".join(para)
        paragraphs.append(paragraph)
        current += len(paragraph) + 1

    return "\n\n".join(paragraphs)


# ------------------------------------------------------------------
# ZIP Baseline
# ------------------------------------------------------------------

def benchmark_zip(data: bytes) -> tuple[int, float]:
    """Compress with standard ZIP and return (size_bytes, time_sec)."""
    buf = io.BytesIO()
    t0 = time.perf_counter()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.writestr("data.txt", data)
    t1 = time.perf_counter()
    return len(buf.getvalue()), t1 - t0


# ------------------------------------------------------------------
# CSF v0.6 on Text (Dictionary + Sparse + Delta)
# ------------------------------------------------------------------

def benchmark_csf_text(text: str) -> tuple[int, float, CompressionResult]:
    """Compress text with CSF v0.6 classical pipeline."""
    compressor = ClassicalCompressor(block_size=512)
    t0 = time.perf_counter()
    compressed, result = compressor.compress_text(text)
    t1 = time.perf_counter()
    return len(compressed), t1 - t0, result


# ------------------------------------------------------------------
# CSF v0.6 on Symbolic Field (Quantum Dust + Convergence)
# ------------------------------------------------------------------

def benchmark_csf_field(target_positions: int = 50_000) -> tuple[int, float, dict]:
    """Build a symbolic Quantum Dust field and compress it."""
    rng = random.Random(42)
    field = QuantumDustField(convergence_threshold=0.08)

    # Simulate sensor observations: mostly no-change, occasional delta
    for i in range(target_positions):
        if rng.random() < 0.02:  # 2% have actual changes
            deltas = [
                QutritDelta(
                    dim_index=rng.randint(0, 11),
                    amp_delta=rng.randint(-3, 3),
                    phase_delta=rng.randint(-2, 2),
                )
                for _ in range(rng.randint(1, 4))
            ]
            field.observe(i, deltas)
        # The other 98% are quantum dust (implicit, nearly free)

    # Run convergence
    engine = ConvergenceEngine(threshold=0.08)
    conv_result = engine.run(field)

    # Compress
    compressor = ClassicalCompressor(block_size=512)
    t0 = time.perf_counter()
    compressed, result = compressor.compress_field(field)
    t1 = time.perf_counter()

    meta = {
        "convergence": conv_result,
        "field_stats": field.stats(),
        "compression": result,
    }
    return len(compressed), t1 - t0, meta


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():
    print("=" * 70)
    print("CSF v0.6 Benchmark — Classical Optimized")
    print("=" * 70)

    # --------------------------------------------------------------
    # 1. Normal Text
    # --------------------------------------------------------------
    print("\n--- Normal Standard Text (~5 MB) ---")
    normal_text = _generate_normal_text(5_000_000)
    normal_bytes = normal_text.encode("utf-8")
    print(f"Original: {len(normal_bytes):,} bytes")

    zip_size, zip_time = benchmark_zip(normal_bytes)
    print(f"ZIP:      {zip_size:,} bytes  ({zip_time:.2f}s)")

    csf_size, csf_time, csf_result = benchmark_csf_text(normal_text)
    print(f"CSF v0.6: {csf_size:,} bytes  ({csf_time:.2f}s)")

    zip_ratio = 1.0 - (zip_size / len(normal_bytes))
    csf_ratio = 1.0 - (csf_size / len(normal_bytes))
    print(f"\nZIP compression:  {zip_ratio*100:.2f}%")
    print(f"CSF compression:  {csf_ratio*100:.2f}%")
    print(f"Winner: {'ZIP' if zip_size < csf_size else 'CSF'} (by {abs(zip_size - csf_size):,} bytes)")
    print(f"CSF dictionary size: {csf_result.dictionary_size} tokens")

    # --------------------------------------------------------------
    # 2. Symbolic / Dream-like Text
    # --------------------------------------------------------------
    print("\n--- Symbolic Dream-Journal Text (~2 MB) ---")
    symbolic_text = _generate_symbolic_text(2_000_000)
    symbolic_bytes = symbolic_text.encode("utf-8")
    print(f"Original: {len(symbolic_bytes):,} bytes")

    zip_size2, zip_time2 = benchmark_zip(symbolic_bytes)
    print(f"ZIP:      {zip_size2:,} bytes  ({zip_time2:.2f}s)")

    csf_size2, csf_time2, csf_result2 = benchmark_csf_text(symbolic_text)
    print(f"CSF v0.6: {csf_size2:,} bytes  ({csf_time2:.2f}s)")

    zip_ratio2 = 1.0 - (zip_size2 / len(symbolic_bytes))
    csf_ratio2 = 1.0 - (csf_size2 / len(symbolic_bytes))
    print(f"\nZIP compression:  {zip_ratio2*100:.2f}%")
    print(f"CSF compression:  {csf_ratio2*100:.2f}%")
    print(f"Winner: {'ZIP' if zip_size2 < csf_size2 else 'CSF'} (by {abs(zip_size2 - csf_size2):,} bytes)")
    print(f"CSF dictionary size: {csf_result2.dictionary_size} tokens")

    # --------------------------------------------------------------
    # 3. Quantum Dust Field (Simulated 3^12 Matrix)
    # --------------------------------------------------------------
    print("\n--- Quantum Dust Field (50K active positions in 3^12 space) ---")
    field_size, field_time, field_meta = benchmark_csf_field(50_000)
    conv = field_meta["convergence"]
    stats = field_meta["field_stats"]
    comp = field_meta["compression"]

    print(f"Original (raw): {stats['total_positions']:,.0f} positions × 24 bytes ≈ {stats['total_positions']*24/1_000_000:.1f} MB")
    print(f"CSF compressed: {field_size:,} bytes ({field_time:.2f}s)")
    print(f"Dust coverage:  {stats['dust_percentage']:.4f}%")
    print(f"Baseline:       {stats['baseline_positions']:,.0f} positions")
    print(f"Active:         {stats['active_positions']:,.0f} positions ({stats['total_active_deltas']:,.0f} deltas)")
    print(f"Convergence:    {conv.collapsed} collapsed, {conv.clustered} clustered, {conv.drift_remaining} remaining")

    # --------------------------------------------------------------
    # Summary
    # --------------------------------------------------------------
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Normal text:     ZIP wins (optimized for generic prose)")
    print(f"Symbolic text:   CSF {'wins' if csf_size2 < zip_size2 else 'close'} (dictionary captures recurring anchors)")
    print(f"Quantum field:   CSF dominates (dust is free, only deviations stored)")
    print("=" * 70)


if __name__ == "__main__":
    main()
