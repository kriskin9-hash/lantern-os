---
author: Sigma0 training run
created: 2026-06-22
---

# Σ₀ Ouro Coder — training results (before / after)

Empirical results from training the [Σ₀ Ouro Coder](SIGMA0-OURO-CODER.md) on this
project's own Claude Code sessions, on an RTX 4070 SUPER (12 GB). All numbers below
are **observed**, not estimated — per the Σ₀ External Reality Rule (claim + evidence
+ confidence + source).

## Two adapters

| | v1 (text pairs) | v2 (tool-call traces) |
|---|---|---|
| **Base** | `ByteDance/Ouro-1.4B` | `ByteDance/Ouro-1.4B` |
| **Data** | 243 text Q&A pairs (`training-data.jsonl`) | **10,507** agentic traces (`tool-call-traces.jsonl`), 8,044 with a real tool call |
| **Source** | assistant *text* turns only | full **context → action** traces incl. `tool_use`+`tool_result` |
| **Config** | 3 epochs, seq 1024, batch 1 | 1 epoch, seq 768, batch 4 |
| **Precision** | bf16 (auto; avoids fp16 grad NaN on this LM) | bf16 |
| **Trainable** | 15.2M LoRA params (1.05%) | 15.2M LoRA params (1.05%) |
| **Loss** | 0.975 → 0.21 | (see run log) |
| **Runtime** | ~22 min | ~4.75 h (657 steps) |
| **Adapter** | `ouro-sigma0-adapters/final` | `ouro-sigma0-v2-toolcalls/final` |

The v2 jump (243 → 10,507 examples, **43×**) is the "more extensive, like Claude
Code does" training: instead of only assistant prose, it learns the actual agentic
decision — *given the conversation so far, what tool do I call with what arguments*.

## Data ceiling — the "20k" question, grounded

```
CLAIM:      20k tool-call training examples are available locally
EVIDENCE:   direct scan of all 22 ~/.claude/projects/*/*.jsonl (35,171 records):
              8,021 tool_use blocks | 8,018 tool_result | 2,670 asst text turns
SOURCE:     live measurement, 2026-06-22
RESULT:     REFUTED. Real ceiling today ≈ 8k tool calls (10,507 windowed examples).
CONFIDENCE: 0.95 (measured, not estimated)
```

20k is reachable only by **accumulating more sessions over time** (or synthetic
augmentation). That's wired up: see [Continual growth](#continual-growth).

## Before / after — base vs. v1 (qualitative probe)

Same prompts, same decoding (`do_sample=False, rep_penalty=1.3, no_repeat_ngram=3`).
A 2-prompt probe, not a benchmark.

**Test 1 — generic code `is_palindrome(s)`**
- **Base:** buggy logic, spilled into 3 unrelated functions + malformed `print` — ignored the requested signature.
- **v1:** `def is_palindrome(s): return s.lower() == s[::-1].lower()` — correct first line, right signature, concise.

**Test 2 — repo knowledge (entrypoint file + port)**
- **Base:** "Lantern *Gardener* … *index.js* … port *3001*" — 0/3, fully hallucinated.
- **v1:** "*server.py* … *localhost* … port 8091" — 2/3 (correct file + host; port wrong, real is 4177).

**Verdict:** training moved the model from *generic + hallucinated* → *repo-aware +
format-correct + correct on simple code*, with a clean ~78% loss drop. Still in the
doc's honest scope: 1.4B, modest fine-tune; exact specifics (e.g. ports) not yet
trustworthy. Both base and v1 ramble (no trained stop) — the serving `stop_strings`
in `ouro_serve.py` enforce termination in production.

## Continual growth

[`scripts/extract-tool-call-traces.py`](../scripts/extract-tool-call-traces.py)
re-scans **all** Claude sessions each run, so the corpus grows automatically as you
keep using Claude Code.
[`scripts/continual-train-ouro.ps1`](../scripts/continual-train-ouro.ps1) refreshes
the dataset and trains the next adapter version (`ouro-sigma0-vN-toolcalls`).
Schedule it weekly to climb toward 20k:

```
schtasks /Create /TN "Sigma0OuroContinualTrain" /SC WEEKLY /D SUN /ST 03:00 /F `
  /TR "powershell -ExecutionPolicy Bypass -File C:\Users\krisk\Desktop\lanternOS\scripts\continual-train-ouro.ps1"
```

## Reproduce

```bash
# 1. extract agentic traces from your Claude sessions (raw set is gitignored — privacy)
python scripts/extract-tool-call-traces.py --out models/lantern-sigma0-coder/tool-call-traces.jsonl

# 2. train (CUDA GPU; HF_HOME on C: since there's no D: drive here)
HF_HOME=C:\hf-cache .venv-train/Scripts/python scripts/train-qlora-ouro.py \
  --base ByteDance/Ouro-1.4B --data models/lantern-sigma0-coder/tool-call-traces.jsonl \
  --out C:/lantern-train/ouro-sigma0-v2-toolcalls --epochs 1 --seq 768 --batch 4 --grad-accum 4

# 3. serve (pin OURO_MODEL to the SAME base the adapter trained on)
OURO_MODEL=ByteDance/Ouro-1.4B OURO_ADAPTER=C:/lantern-train/ouro-sigma0-v2-toolcalls/final \
  .venv-train/Scripts/python scripts/ouro_serve.py
```

## Honest scope
- v1 before/after is a **2-prompt qualitative probe**, not HumanEval. A firmer eval
  (`scripts/eval-sigma-coder.py`) is the next step.
- v2 trains on tool-call *text serialization* (`[tool: NAME] {json}`); the Ollama
  serving shim does not yet parse those into real tool invocations — it improves the
  model's agentic *fluency*, not end-to-end tool execution.
- Raw `tool-call-traces.jsonl` is **gitignored** (verbatim session content).
