"""
T4 hybrid probe (Technique 4 / #1596) — neural pass over the CSF-Col RESIDUAL.

#1596's thesis: CSF-Col strips structural redundancy at zero compute, then a grounded
neural predictor drives only the high-L residual to the entropy floor. The faithful,
measurable form: replace the codec on the col-transposed stream with a neural
arithmetic coder, i.e. compare
    neural-CE( col_forward(data) )   vs   best-codec( col_forward(data) )   [= col-best]
both normalized to bits per ORIGINAL byte, so it's directly comparable to §1.1/§3.1.

Σ₀ + external grounding both predict a LOSS for an *ungrounded* model: the col-transposed
stream (varint header + skeletons + column blobs) is NOT natural language — it is maximally
out-of-distribution for gpt2 — and arithmetic coding pays the KL divergence between the
model's distribution and the data's (Revisiting Data Compression with LM, arXiv:2601.02875;
LLM-as-a-Compressor benchmark). This probe tests whether that penalty actually bites, and by
how much, BEFORE building the grounded coder.

    HF_HOME=D:\\hf-cache python experiments/t4_hybrid_probe.py [--model gpt2]
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))


def codec_bytes_on(stream: bytes) -> tuple[int, str]:
    """Smallest strong codec on an arbitrary byte stream (the col-best backend)."""
    import bz2, lzma, zlib
    cands = [("zlib-9", zlib.compress(stream, 9)),
             ("bz2-9", bz2.compress(stream, 9)),
             ("lzma-9e", lzma.compress(stream, preset=9 | lzma.PRESET_EXTREME))]
    try:
        import brotli
        cands.append(("brotli-11", brotli.compress(stream, quality=11)))
    except Exception:
        pass
    try:
        import zstandard as z
        cands.append(("zstd-19", z.ZstdCompressor(level=19).compress(stream)))
    except Exception:
        pass
    name, blob = min(cands, key=lambda c: len(c[1]))
    return len(blob), name


def neural_bits_on(stream: bytes, model, tok, ctx: int) -> float:
    """Teacher-forced CE of `model` over `stream` (bytes via latin-1), in BITS total.

    latin-1 is a byte-faithful 1:1 decode so every byte of the transposed stream is
    scored; gpt2's byte-level BPE handles the resulting code points."""
    import torch
    text = stream.decode("latin-1")
    ids = tok(text, return_tensors="pt").input_ids[0]
    n = ids.shape[0]
    total_nll = 0.0
    with torch.no_grad():
        i = 0
        while i < n - 1:
            window = ids[i:i + ctx].unsqueeze(0)
            out = model(window, labels=window)
            total_nll += out.loss.item() * (window.shape[1] - 1)
            i += ctx
    return total_nll / math.log(2)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gpt2")
    ap.add_argument("--slice", type=int, default=32768, help="bytes of the ORIGINAL file")
    args = ap.parse_args()
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except Exception as e:
        print(f"T4 probe skipped — needs torch+transformers ({e})")
        return 0
    from csf import col_transform as col

    print(f"loading {args.model} (cpu)...")
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.float32).eval()
    ctx = min(getattr(model.config, "max_position_embeddings", 1024) or 1024, 1024)

    print("bits/byte over the COL-TRANSPOSED stream (lower=better), per original byte.")
    print(f"{'log':<24}{'rawB':>8}{'codec-on-col':>14}{'neural-on-col':>15}  verdict (#1596)")
    print("-" * 78)
    for p in sorted(REPO.glob("data/csf_memory/*.jsonl")):
        full = p.read_bytes()[:args.slice]
        # slice must end on a line boundary or col.forward sees a truncated record
        nl = full.rfind(b"\n")
        if nl > 0:
            full = full[:nl + 1]
        if len(full) < 256:
            continue
        try:
            t = col.forward(full)
        except col.NotApplicable:
            print(f"{p.name[:23]:<24}{len(full):>8}  col N/A")
            continue
        cb, cname = codec_bytes_on(t)
        codec_bpb = cb * 8 / len(full)
        neural_bpb = neural_bits_on(t, model, tok, ctx) / len(full)
        verdict = "NEURAL WINS" if neural_bpb < codec_bpb else f"loses ({(neural_bpb/codec_bpb-1)*100:+.0f}%)"
        print(f"{p.name[:23]:<24}{len(full):>8}{codec_bpb:>12.3f}({cname[:4]}){neural_bpb:>14.3f}  {verdict}")
    print("\nIf ungrounded neural loses on the transposed stream, #1596 needs a model")
    print("conditioned on the column distribution (fine-tune / grounding), not stock gpt2.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
