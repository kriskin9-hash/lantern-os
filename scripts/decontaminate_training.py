"""
Decontaminate a training JSONL against HumanEval + MBPP (Issue #1292, Phase 0).

A training example is CONTAMINATED if it shares a long literal span with any
benchmark problem's prompt OR canonical solution. We use normalized n-gram
overlap (the standard decontamination recipe: StarCoder/Phi/BigCode use
13-gram exact match on whitespace-normalized text).

    .venv-train/Scripts/python scripts/decontaminate_training.py \
        --in  data/training/opencode-completion.jsonl \
        --out data/training/opencode-completion.clean.jsonl

Reports how many rows were dropped and a sample of what matched, so the
cleaning is auditable (no silent data loss).
"""
import argparse, json, os, re, sys
sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("HF_HOME", "D:/hf-cache")

NGRAM = 13  # tokens; BigCode/StarCoder decontamination standard


def normalize(text: str) -> list[str]:
    """Lowercase, collapse whitespace, split to tokens (the n-gram unit)."""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.split(" ")


def ngrams(tokens: list[str], n: int) -> set[str]:
    return {" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)} if len(tokens) >= n else set()


def build_contamination_index() -> set[str]:
    """All n-grams from HumanEval (164) + MBPP prompts AND canonical solutions."""
    from datasets import load_dataset
    bad = set()
    n_problems = 0

    print("Loading HumanEval ...", flush=True)
    he = load_dataset("openai_humaneval", split="test")
    for ex in he:
        for field in ("prompt", "canonical_solution"):
            bad |= ngrams(normalize(ex.get(field, "")), NGRAM)
        n_problems += 1

    print("Loading MBPP ...", flush=True)
    try:
        mbpp = load_dataset("google-research-datasets/mbpp", "sanitized")
        for split in ("train", "validation", "test", "prompt"):
            if split in mbpp:
                for ex in mbpp[split]:
                    for field in ("code", "source_code", "prompt", "text"):
                        if ex.get(field):
                            bad |= ngrams(normalize(ex[field]), NGRAM)
                    n_problems += 1
    except Exception as e:
        print(f"  MBPP load skipped: {e}", flush=True)

    print(f"contamination index: {len(bad):,} {NGRAM}-grams from {n_problems} benchmark problems", flush=True)
    return bad


def row_text(rec: dict) -> str:
    """Concatenate the trainable text of a row (handles both formats)."""
    parts = [str(rec.get(k, "")) for k in ("instruction", "input", "output", "text", "prompt", "completion")]
    return "\n".join(p for p in parts if p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="out", required=True)
    ap.add_argument("--drop-self-study", action="store_true",
                    help="also drop rows whose source=='humaneval-selfstudy'")
    ap.add_argument("--min-overlap", type=int, default=1,
                    help="drop a row if it shares >= this many benchmark n-grams")
    a = ap.parse_args()

    bad = build_contamination_index()

    rows = [json.loads(l) for l in open(a.inp, encoding="utf-8") if l.strip()]
    kept, dropped, samples = [], 0, []
    for rec in rows:
        if a.drop_self_study and rec.get("source") == "humaneval-selfstudy":
            dropped += 1
            continue
        grams = ngrams(normalize(row_text(rec)), NGRAM)
        hits = len(grams & bad)
        if hits >= a.min_overlap:
            dropped += 1
            if len(samples) < 5:
                samples.append((rec.get("source", "?"), hits, row_text(rec)[:80]))
        else:
            kept.append(rec)

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        for rec in kept:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"\nIN  {len(rows)} rows -> KEPT {len(kept)}  DROPPED {dropped} "
          f"({dropped / max(1, len(rows)) * 100:.1f}% contaminated/self-study)", flush=True)
    print(f"OUT {a.out}", flush=True)
    if samples:
        print("sample dropped rows (source, ngram-hits, text):", flush=True)
        for s in samples:
            print(f"  [{s[0]}] hits={s[1]}: {s[2]!r}", flush=True)


if __name__ == "__main__":
    main()
