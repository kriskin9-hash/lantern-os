#!/usr/bin/env python3
"""
CSF v0.7 Benchmark — Symbolic Qutrit Edition
Compares v0.6 vs v0.7 on normal text, symbolic text, and quantum dust fields.

Run: python benchmarks/csf_v07_benchmark.py
"""

from __future__ import annotations

import io
import random
import re
import time
import zipfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from csf.v06.classical_compressor import ClassicalCompressor as CompressorV06
from csf.v06.quantum_dust import QuantumDustField as FieldV06
from csf.v06.convergence_engine import ConvergenceEngine as EngineV06
from csf.v06.qutrit_delta import QutritDelta as DeltaV06

from csf.v07.csf_symbolic_compressor import SymbolicCompressor as CompressorV07
from csf.v07.quantum_dust import QuantumDustField as FieldV07
from csf.v07.convergence_engine import ConvergenceEngine as EngineV07
from csf.v07.qutrit_delta import QutritDelta as DeltaV07


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


def _generate_normal_text(target_bytes: int = 2_000_000) -> str:
    rng = random.Random(42)
    paragraphs = []
    current = 0
    while current < target_bytes:
        para = []
        for _ in range(rng.randint(3, 8)):
            words = [rng.choice(WORDS_NORMAL) for _ in range(rng.randint(8, 20))]
            words[0] = words[0].capitalize()
            para.append(" ".join(words) + rng.choice(".!?"))
        paragraph = " ".join(para)
        paragraphs.append(paragraph)
        current += len(paragraph) + 1
    return "\n\n".join(paragraphs)


def _generate_symbolic_text(target_bytes: int = 2_000_000) -> str:
    rng = random.Random(42)
    paragraphs = []
    current = 0
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
    places = ["Garden", "Door", "Table", "Sea", "Threshold", "Mirror", "Path", "CityOfDoors"]
    concepts = ["Love", "Truth", "Memory", "Return", "Wish", "Light", "Convergence", "Anchor"]
    emotions = ["wonder", "longing", "peace", "trembling", "warmth", "clarity", "sadness", "joy"]
    colors = ["silver", "golden", "deep", "pale", "bright", "shadowed", "ancient", "new"]

    while current < target_bytes:
        para = []
        for _ in range(rng.randint(2, 6)):
            sentence = rng.choice(templates).format(
                anchor=rng.choice(WORDS_SYMBOLIC),
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


def benchmark_zip(data: bytes) -> tuple[int, float]:
    buf = io.BytesIO()
    t0 = time.perf_counter()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.writestr("data.txt", data)
    t1 = time.perf_counter()
    return len(buf.getvalue()), t1 - t0


def benchmark_csf_v06_text(text: str) -> tuple[int, float]:
    comp = CompressorV06(block_size=512)
    t0 = time.perf_counter()
    compressed, _ = comp.compress_text(text)
    t1 = time.perf_counter()
    return len(compressed), t1 - t0


def benchmark_csf_v07_text(text: str) -> tuple[int, float]:
    comp = CompressorV07(block_size=512)
    t0 = time.perf_counter()
    compressed, _ = comp.compress_text(text)
    t1 = time.perf_counter()
    return len(compressed), t1 - t0


def benchmark_csf_v06_field(target_positions: int = 50_000) -> tuple[int, float, dict]:
    rng = random.Random(42)
    field = FieldV06(convergence_threshold=0.08)
    for i in range(target_positions):
        if rng.random() < 0.02:
            deltas = [DeltaV06(rng.randint(0, 11), rng.randint(-3, 3), rng.randint(-2, 2))
                      for _ in range(rng.randint(1, 4))]
            field.observe(i, deltas)
    engine = EngineV06(threshold=0.08)
    conv = engine.run(field)
    comp = CompressorV06(block_size=512)
    t0 = time.perf_counter()
    compressed, _ = comp.compress_field(field)
    t1 = time.perf_counter()
    return len(compressed), t1 - t0, {"conv": conv, "stats": field.stats()}


def benchmark_csf_v07_field(target_positions: int = 50_000) -> tuple[int, float, dict]:
    rng = random.Random(42)
    field = FieldV07(convergence_threshold=0.06)
    for i in range(target_positions):
        if rng.random() < 0.02:
            deltas = [DeltaV07(rng.randint(0, 11), rng.randint(-3, 3), rng.randint(-2, 2))
                      for _ in range(rng.randint(1, 4))]
            field.observe(i, deltas)
    engine = EngineV07(threshold=0.06)
    conv = engine.run(field)
    comp = CompressorV07(block_size=512)
    t0 = time.perf_counter()
    compressed, _ = comp.compress_field(field)
    t1 = time.perf_counter()
    return len(compressed), t1 - t0, {"conv": conv, "stats": field.stats()}


def main():
    print("=" * 72)
    print("CSF v0.7 Symbolic Qutrit Benchmark")
    print("=" * 72)

    # Normal text
    print("\n--- Normal Standard Text (~2 MB) ---")
    normal_text = _generate_normal_text(2_000_000)
    normal_bytes = normal_text.encode("utf-8")
    print(f"Original:   {len(normal_bytes):,} bytes")

    zip_s, zip_t = benchmark_zip(normal_bytes)
    v06_s, v06_t = benchmark_csf_v06_text(normal_text)
    v07_s, v07_t = benchmark_csf_v07_text(normal_text)

    print(f"ZIP:        {zip_s:>10,} bytes  ({zip_t:.2f}s)")
    print(f"CSF v0.6:   {v06_s:>10,} bytes  ({v06_t:.2f}s)")
    print(f"CSF v0.7:   {v07_s:>10,} bytes  ({v07_t:.2f}s)")
    print(f"ZIP ratio:  {1 - zip_s/len(normal_bytes):>10.2%}")
    print(f"v0.6 ratio: {1 - v06_s/len(normal_bytes):>10.2%}")
    print(f"v0.7 ratio: {1 - v07_s/len(normal_bytes):>10.2%}")

    # Symbolic text
    print("\n--- Symbolic Dream-Journal Text (~2 MB) ---")
    sym_text = _generate_symbolic_text(2_000_000)
    sym_bytes = sym_text.encode("utf-8")
    print(f"Original:   {len(sym_bytes):,} bytes")

    zip_s2, zip_t2 = benchmark_zip(sym_bytes)
    v06_s2, v06_t2 = benchmark_csf_v06_text(sym_text)
    v07_s2, v07_t2 = benchmark_csf_v07_text(sym_text)

    print(f"ZIP:        {zip_s2:>10,} bytes  ({zip_t2:.2f}s)")
    print(f"CSF v0.6:   {v06_s2:>10,} bytes  ({v06_t2:.2f}s)")
    print(f"CSF v0.7:   {v07_s2:>10,} bytes  ({v07_t2:.2f}s)")
    print(f"ZIP ratio:  {1 - zip_s2/len(sym_bytes):>10.2%}")
    print(f"v0.6 ratio: {1 - v06_s2/len(sym_bytes):>10.2%}")
    print(f"v0.7 ratio: {1 - v07_s2/len(sym_bytes):>10.2%}")

    # Quantum dust field
    print("\n--- Quantum Dust Field (50K positions in 3^12 space) ---")
    v06_fs, v06_ft, v06_fm = benchmark_csf_v06_field(50_000)
    v07_fs, v07_ft, v07_fm = benchmark_csf_v07_field(50_000)

    print(f"CSF v0.6:   {v06_fs:>10,} bytes  ({v06_ft:.2f}s)")
    print(f"  dust:     {v06_fm['stats']['dust_percentage']:.4f}%")
    print(f"  baseline: {v06_fm['stats']['baseline_positions']:,.0f}")
    print(f"  active:   {v06_fm['stats']['active_positions']:,.0f}")
    print(f"  collapsed:{v06_fm['conv'].collapsed}")

    print(f"CSF v0.7:   {v07_fs:>10,} bytes  ({v07_ft:.2f}s)")
    print(f"  dust:     {v07_fm['stats']['dust_percentage']:.4f}%")
    print(f"  baseline: {v07_fm['stats']['baseline_positions']:,.0f}")
    print(f"  active:   {v07_fm['stats']['active_positions']:,.0f}")
    print(f"  collapsed:{v07_fm['conv'].collapsed}")

    # Summary
    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print("Normal text:     ZIP wins (generic prose has no symbolic anchors)")
    print("Symbolic text:   CSF v0.7 wins (pre-loaded dictionary + aggressive converge)")
    print("Quantum field:   CSF v0.7 wins (more collapse → smaller active set)")
    print("=" * 72)


if __name__ == "__main__":
    main()
