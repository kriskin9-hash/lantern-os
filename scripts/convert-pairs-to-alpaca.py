#!/usr/bin/env python3
"""
Convert {system, messages} fine-tuning pairs (Anthropic format, from
extract-session-pairs.py) into alpaca {instruction, input, output} records that
scripts/fine-tune-ollama-model.py consumes for QLoRA training.

Usage:
    python scripts/convert-pairs-to-alpaca.py \
        --in data/training/haiku-ft-pairs.jsonl \
        --out models/lantern-sigma0-coder/training-data.jsonl
"""
import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="data/training/haiku-ft-pairs.jsonl")
    ap.add_argument("--out", dest="out", default="models/lantern-sigma0-coder/training-data.jsonl")
    args = ap.parse_args()

    src = Path(args.inp)
    dst = Path(args.out)
    dst.parent.mkdir(parents=True, exist_ok=True)

    n_in = n_out = 0
    with open(src, encoding="utf-8") as f, open(dst, "w", encoding="utf-8") as o:
        for line in f:
            line = line.strip()
            if not line:
                continue
            n_in += 1
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            msgs = rec.get("messages", [])
            user = next((m.get("content", "") for m in msgs if m.get("role") == "user"), "")
            asst = next((m.get("content", "") for m in msgs if m.get("role") == "assistant"), "")
            if not user or not asst:
                continue
            alpaca = {"instruction": user.strip(), "input": "", "output": asst.strip()}
            o.write(json.dumps(alpaca, ensure_ascii=False) + "\n")
            n_out += 1

    print(f"Converted {n_out}/{n_in} records -> {dst} ({dst.stat().st_size // 1024} KB)")
    print("Next (needs GPU + unsloth): python scripts/fine-tune-ollama-model.py "
          f"--model lantern-sigma0-coder --data {dst} --epochs 3")


if __name__ == "__main__":
    main()
