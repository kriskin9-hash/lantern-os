#!/usr/bin/env python3
"""Build dream-journal instruction-tuning dataset for Lantern fine-tuning.

REQUIRES: ANTHROPIC_API_KEY in environment (or .env in repo root).

Input:  data/dream_journal/*.jsonl
Output: data/training/dream-instruct.jsonl

Format (Alpaca-style, compatible with Unsloth QLoRA):
  {
    "instruction": "...",   <- role prompt + dream text
    "input":        "...",   <- symbol mesh + co-occurrence context
    "output":       "..."    <- ideal Lantern response + [DOORS: A | B | C]
  }

Usage:
  python scripts/build-dream-dataset.py
  python scripts/build-dream-dataset.py --dry-run            # skip Claude calls, emit fixture rows
  python scripts/build-dream-dataset.py --limit 20           # only first 20 entries
  python scripts/build-dream-dataset.py --model claude-opus-4
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DREAM_DIR = REPO_ROOT / "data" / "dream_journal"
TRAINING_DIR = REPO_ROOT / "data" / "training"
OUTPUT_PATH = TRAINING_DIR / "dream-instruct.jsonl"

FIXTURE_PAIRS: list[dict] = [
    {
        "instruction": (
            "You are Lantern, a symbolic dream companion. "
            "The dreamer writes: 'I stood at the edge of a silver lake under a full moon. "
            "Three doors appeared on the opposite shore.'"
        ),
        "input": (
            "Symbol mesh: moon, lake, door, silver, reflection. "
            "Co-occurrence: (moon, lake), (door, silver), (lake, reflection)."
        ),
        "output": (
            "The moon illuminates what you are ready to see. "
            "The silver lake is stillness — your mind calm enough to reflect. "
            "Three doors wait because you are ready to choose, not because you must. "
            "Which resonance calls you: the warmth of familiarity, the pull of the unknown, "
            "or the quiet that asks nothing of you?\n"
            "[DOORS: warm familiarity | cool unknown | quiet rest]"
        ),
    },
    {
        "instruction": (
            "You are Lantern, a symbolic dream companion. "
            "The dreamer writes: 'I was chased through a forest by something I couldn't see. "
            "I found a door in the middle of the trees.'"
        ),
        "input": (
            "Symbol mesh: forest, chase, door, fear, hidden. "
            "Co-occurrence: (forest, chase), (chase, fear), (door, forest)."
        ),
        "output": (
            "The forest is the unknown parts of yourself — dense, alive, unevaluated. "
            "What chases you has no form because you haven't given it one yet. "
            "The door is remarkable: it appeared in the middle of the wilderness. "
            "That is not an escape — that is an invitation to face forward. "
            "Fear becomes curiosity the moment you name it.\n"
            "[DOORS: face the pursuer | step through the door | rest in the forest]"
        ),
    },
]


def load_dreams(dream_dir: Path, limit: int | None = None) -> list[dict]:
    """Load all JSONL entries from dream_journal directory."""
    entries: list[dict] = []
    jsonl_files = sorted(dream_dir.glob("*.jsonl"))
    for f in jsonl_files:
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                entries.append(obj)
            except json.JSONDecodeError:
                continue
    if limit:
        entries = entries[:limit]
    return entries


def filter_entries(entries: list[dict]) -> list[dict]:
    """Keep only dream/vision entries with meaningful text."""
    out = []
    for e in entries:
        text = str(e.get("text") or "").strip()
        if len(text) < 30:
            continue
        kind = str(e.get("kind") or "dream")
        if kind in ("test", "note") and "test" in text.lower():
            continue
        out.append(e)
    return out


def top_symbols(entry: dict, n: int = 8) -> list[str]:
    """Extract top-N symbols from entry symbol field."""
    syms = entry.get("symbols") or []
    if isinstance(syms, str):
        syms = [s.strip() for s in syms.split(",")]
    return [str(s) for s in syms[:n] if s]


def co_occurrence_pairs(symbols: list[str], n: int = 4) -> list[tuple[str, str]]:
    """Return up to n co-occurring symbol pairs."""
    pairs = list(combinations(symbols, 2))
    return pairs[:n]


def build_instruction(entry: dict) -> str:
    text = str(entry.get("text") or "").strip()
    text = text[:800]  # truncate very long entries
    return (
        "You are Lantern, a symbolic dream companion who responds to dreams with "
        "warmth, depth, and symbolic insight. Always end your response with "
        "[DOORS: door_a | door_b | door_c] — three short resonance options. "
        f"The dreamer writes: '{text}'"
    )


def build_input_context(entry: dict) -> str:
    syms = top_symbols(entry)
    pairs = co_occurrence_pairs(syms)
    sym_str = ", ".join(syms) if syms else "none noted"
    pair_str = ", ".join(f"({a}, {b})" for a, b in pairs) if pairs else "none"
    mood = str(entry.get("mood") or "").strip()
    lucidity = entry.get("lucidity", 0)
    parts = [f"Symbol mesh: {sym_str}.", f"Co-occurrence: {pair_str}."]
    if mood:
        parts.append(f"Mood: {mood}.")
    if lucidity:
        parts.append(f"Lucidity: {lucidity:.0%}.")
    return " ".join(parts)


def generate_response_claude(
    instruction: str,
    context: str,
    model: str,
    client: Any,
) -> str:
    """Call Claude to generate ideal Lantern response."""
    prompt = (
        f"{instruction}\n\n"
        f"Context: {context}\n\n"
        "Respond as Lantern: warm, symbolic, 3–6 sentences, end with [DOORS: A | B | C]."
    )
    message = client.messages.create(
        model=model,
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def generate_response_dry(entry: dict) -> str:
    """Deterministic stub output for --dry-run mode."""
    syms = top_symbols(entry, n=3)
    sym_str = ", ".join(syms) if syms else "the unknown"
    name = str(entry.get("name") or "this dream").strip() or "this experience"
    return (
        f"The imagery of {sym_str} carries meaning worth exploring. "
        f"{name.capitalize()} invites you to look inward with curiosity. "
        "Three paths open before you, each a reflection of where you already are.\n"
        "[DOORS: familiar warmth | curious depth | quiet stillness]"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Lantern dream instruction dataset")
    parser.add_argument("--dry-run", action="store_true", help="Skip Claude API calls")
    parser.add_argument("--limit", type=int, default=None, help="Max entries to process")
    parser.add_argument("--model", default="claude-opus-4-5", help="Anthropic model ID")
    parser.add_argument("--output", default=str(OUTPUT_PATH), help="Output JSONL path")
    parser.add_argument("--delay", type=float, default=0.5, help="Seconds between API calls")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # ── Load & filter dreams ─────────────────────────────────────────────────
    if not DREAM_DIR.exists():
        print(f"ERROR: dream_journal directory not found: {DREAM_DIR}", file=sys.stderr)
        return 1

    all_entries = load_dreams(DREAM_DIR, limit=args.limit)
    entries = filter_entries(all_entries)
    print(f"Loaded {len(all_entries)} entries, {len(entries)} pass filter.", flush=True)

    if not entries and not args.dry_run:
        print("No usable entries found. Use --dry-run to emit fixture rows only.")
        return 1

    # ── Anthropic client ─────────────────────────────────────────────────────
    client = None
    if not args.dry_run:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            dotenv = REPO_ROOT / ".env"
            if dotenv.exists():
                for line in dotenv.read_text().splitlines():
                    if line.startswith("ANTHROPIC_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"')
                        break
        if not api_key:
            print("ERROR: ANTHROPIC_API_KEY not set. Use --dry-run or export the key.", file=sys.stderr)
            return 1
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            print("ERROR: anthropic package not installed. pip install anthropic", file=sys.stderr)
            return 1

    # ── Write output ─────────────────────────────────────────────────────────
    written = 0
    errors = 0

    with output_path.open("w", encoding="utf-8") as fout:
        # Always write fixtures first
        for pair in FIXTURE_PAIRS:
            fout.write(json.dumps(pair, ensure_ascii=False) + "\n")
            written += 1

        for i, entry in enumerate(entries):
            instruction = build_instruction(entry)
            context = build_input_context(entry)

            if args.dry_run:
                output_text = generate_response_dry(entry)
            else:
                try:
                    output_text = generate_response_claude(instruction, context, args.model, client)
                    if args.delay > 0:
                        time.sleep(args.delay)
                except Exception as e:
                    print(f"  [warn] entry {i} ({entry.get('id', '?')}): {e}", file=sys.stderr)
                    errors += 1
                    continue

            pair = {"instruction": instruction, "input": context, "output": output_text}
            fout.write(json.dumps(pair, ensure_ascii=False) + "\n")
            written += 1

            if (i + 1) % 10 == 0:
                print(f"  [{i+1}/{len(entries)}] written={written} errors={errors}", flush=True)

    print(f"\nDone. {written} pairs written to {output_path}")
    if errors:
        print(f"  {errors} entries skipped due to API errors.")

    # ── Stats ─────────────────────────────────────────────────────────────────
    all_symbols: list[str] = []
    for e in entries:
        all_symbols.extend(top_symbols(e))
    top10 = Counter(all_symbols).most_common(10)
    print(f"\nTop symbols across dataset: {', '.join(f'{s}({n})' for s, n in top10)}")
    print(f"Average text length: {sum(len(e.get('text','')) for e in entries) // max(1,len(entries))} chars")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
