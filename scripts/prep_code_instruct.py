"""
Phase 2 (Issue #1292): build a large raw-completion code dataset from proven
open-source instruction sets — Magicoder OSS-Instruct (75K) + evol-codealpaca-v1
(~110K Evol-Instruct). These boosted 7B models past ChatGPT on HumanEval
(arXiv:2312.02120); here we adapt them to Ouro's winning format.

Prior finding (docs/research/2026-06-26-ouro-humaneval-training.md): instruction
format makes Ouro emit `assistant\\n<chain-of-thought>` instead of code, so we
extract the first Python FUNCTION from each solution and store it as a raw
completion (signature+docstring as `instruction`, body as `output`) — the same
format that scored 50% on the peak run.

    .venv-train/Scripts/python scripts/prep_code_instruct.py \
        --out data/training/code-instruct-raw.jsonl

Then decontaminate before training:
    .venv-train/Scripts/python scripts/decontaminate_training.py \
        --in data/training/code-instruct-raw.jsonl \
        --out data/training/code-instruct-raw.clean.jsonl
"""
import argparse, json, os, re, sys
sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("HF_HOME", "D:/hf-cache")


def first_function(code: str) -> str | None:
    """Extract the first top-level `def ...` block (signature + indented body)."""
    if "def " not in code:
        return None
    m = re.search(r"```(?:python)?\s*(.*?)```", code, re.S)
    if m:
        code = m.group(1)
    lines = code.splitlines()
    start = next((i for i, l in enumerate(lines) if re.match(r"^def ", l)), None)
    if start is None:
        return None
    block = [lines[start]]
    for l in lines[start + 1:]:
        if l.strip() and not l[0].isspace() and not l.startswith("#"):
            break
        block.append(l)
    fn = "\n".join(block).rstrip().replace("\t", "    ")
    return fn if len(fn.splitlines()) >= 3 else None


def to_completion_record(fn: str, source: str) -> dict | None:
    """Split a function into (signature+docstring) prompt and body output."""
    lines = fn.split("\n")
    # find end of signature+docstring block
    in_doc, split_at = False, 1
    for i, l in enumerate(lines):
        s = l.strip()
        if s.startswith('"""') or s.startswith("'''"):
            if in_doc:
                split_at = i + 1
                break
            in_doc = True
            if s.count('"""') >= 2 or s.count("'''") >= 2:
                split_at = i + 1
                break
    prompt = "\n".join(lines[:split_at])
    body = "\n".join(lines[split_at:])
    if not body.strip():
        return None
    return {"instruction": prompt, "output": body, "source": source}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "data/training/code-instruct-raw.jsonl"))
    ap.add_argument("--max-ossinstruct", type=int, default=75000)
    ap.add_argument("--max-evol", type=int, default=110000)
    a = ap.parse_args()

    from datasets import load_dataset
    rows = []

    # ── Magicoder OSS-Instruct (problem -> solution) ─────────────────────────
    print("Loading Magicoder OSS-Instruct-75K ...", flush=True)
    try:
        ds = load_dataset("ise-uiuc/Magicoder-OSS-Instruct-75K", split="train")
        n0 = len(rows)
        for ex in ds:
            if len(rows) - n0 >= a.max_ossinstruct:
                break
            fn = first_function(ex.get("solution", "") or ex.get("output", ""))
            if fn:
                rec = to_completion_record(fn, "oss-instruct")
                if rec:
                    rows.append(rec)
        print(f"  OSS-Instruct completions: {len(rows) - n0}", flush=True)
    except Exception as e:
        print(f"  OSS-Instruct skipped: {e}", flush=True)

    # ── evol-codealpaca-v1 (instruction -> output) ───────────────────────────
    print("Loading evol-codealpaca-v1 ...", flush=True)
    try:
        ds = load_dataset("theblackcat102/evol-codealpaca-v1", split="train")
        n0 = len(rows)
        for ex in ds:
            if len(rows) - n0 >= a.max_evol:
                break
            fn = first_function(ex.get("output", "") or ex.get("response", ""))
            if fn:
                rec = to_completion_record(fn, "evol-codealpaca")
                if rec:
                    rows.append(rec)
        print(f"  evol-codealpaca completions: {len(rows) - n0}", flush=True)
    except Exception as e:
        print(f"  evol-codealpaca skipped: {e}", flush=True)

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        for rec in rows:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"\nWrote {len(rows)} raw-completion rows -> {a.out}", flush=True)
    print("Next: run scripts/decontaminate_training.py on this file before training.", flush=True)


if __name__ == "__main__":
    main()
