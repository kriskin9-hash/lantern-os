#!/usr/bin/env python3
"""Build dream instruction-tuning dataset from dream journal entries.

Reads data/dream_journal/*.jsonl, formats entries into training pairs,
and optionally uses Claude API to generate ideal Lantern responses.

Output: data/training/dream-instruct.jsonl
Format: {"instruction": "...", "input": "...", "output": "..."}

Usage:
    # Build dataset without AI generation (uses existing text)
    python scripts/build-dream-dataset.py

    # Build with AI generation (requires ANTHROPIC_API_KEY)
    python scripts/build-dream-dataset.py --generate
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
JOURNAL_DIR = REPO_ROOT / "data" / "dream_journal"
TRAINING_DIR = REPO_ROOT / "data" / "training"
OUTPUT_FILE = TRAINING_DIR / "dream-instruct.jsonl"


def _extract_symbols_cooccurrence(entries: list[dict]) -> tuple[list[str], list[str]]:
    """Extract top 8 symbols and top 3 co-occurrence pairs from all entries."""
    symbol_counts: dict[str, int] = {}
    cooccur: dict[str, int] = {}

    for entry in entries:
        symbols = entry.get("symbols", [])[:8]
        for s in symbols:
            symbol_counts[s] = symbol_counts.get(s, 0) + 1

        # Co-occurrence pairs
        for i in range(len(symbols)):
            for j in range(i + 1, len(symbols)):
                pair = tuple(sorted([symbols[i], symbols[j]]))
                key = f"{pair[0]}⟶{pair[1]}"
                cooccur[key] = cooccur.get(key, 0) + 1

    top_symbols = sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)[:8]
    top_pairs = sorted(cooccur.items(), key=lambda x: x[1], reverse=True)[:3]

    return [s[0] for s in top_symbols], [p[0] for p in top_pairs]


def _generate_with_claude(dream_text: str, symbols: str, cooccur: str) -> Optional[str]:
    """Generate ideal Lantern response using Claude API."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        system_prompt = """You are Lantern — a dream companion for the Three Doors Game.
Respond to dream entries with:
1. 2-4 sentences of warm, symbolic reflection
2. Exactly THREE followable doors in format: [DOORS: A <name> | B <name> | C <name>]
3. Use liminal, dreamlike imagery (thresholds, light, water, doors)
4. Never explain game mechanics
5. Keep it brief and poetic"""

        user_message = f"""Dream entry: "{dream_text}"

Symbol mesh: {symbols}
Co-occurrence: {cooccur}

Respond as Lantern with reflection + three doors."""

        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=300,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        return response.content[0].text
    except Exception as e:
        print(f"  Claude API error: {e}", file=sys.stderr)
        return None


def build_dataset(use_ai: bool = False) -> list[dict]:
    """Build training dataset from dream journal entries."""
    # Load all dream entries
    entries: list[dict] = []
    for jsonl_file in JOURNAL_DIR.glob("*.jsonl"):
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if entry.get("kind") in ["dream", "csf_ingest"] and entry.get("text"):
                        entries.append(entry)
                except json.JSONDecodeError:
                    continue

    print(f"Loaded {len(entries)} dream entries")

    # Extract symbol mesh
    top_symbols, top_pairs = _extract_symbols_cooccurrence(entries)
    symbols_str = ", ".join(top_symbols)
    cooccur_str = ", ".join(top_pairs)

    print(f"Top symbols: {symbols_str}")
    print(f"Top co-occurrences: {cooccur_str}")

    # Build training pairs
    training_pairs: list[dict] = []
    for entry in entries:
        dream_text = entry.get("text", "")[:500]  # Truncate long dreams

        if use_ai:
            print(f"Generating response for: {dream_text[:50]}...", file=sys.stderr)
            output = _generate_with_claude(dream_text, symbols_str, cooccur_str)
            if not output:
                # Fallback to simple template
                output = f"The dream speaks of {dream_text[:30]}... A light shines through.\n[DOORS: A Follow the Light | B Open the Door | C Return to Sleep]"
        else:
            # Use existing text as simple training pair
            output = f"Reflection on: {dream_text[:100]}...\n[DOORS: A Remember | B Explore | C Let Go]"

        training_pairs.append({
            "instruction": f"The dreamer says: '{dream_text}'. Respond as Lantern with CTF doors.",
            "input": f"Symbol mesh: {symbols_str}. Co-occurrence: {cooccur_str}.",
            "output": output,
        })

    return training_pairs


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Build dream instruction-tuning dataset")
    parser.add_argument("--generate", action="store_true", help="Use Claude API to generate responses")
    args = parser.parse_args()

    # Create training directory
    TRAINING_DIR.mkdir(parents=True, exist_ok=True)

    # Build dataset
    pairs = build_dataset(use_ai=args.generate)

    # Write output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for pair in pairs:
            f.write(json.dumps(pair) + "\n")

    print(f"Wrote {len(pairs)} training pairs to {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
