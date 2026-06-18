# Handoff: Σ₀ local coding agent + LoRA training

**Date:** 2026-06-18  
**Tracking issue:** [#690](https://github.com/alex-place/lantern-os/issues/690)  
**Repo:** `C:\dev\lantern-os` (never work from the OneDrive copy)

## Goal
"Ollama hooked to our own custom Σ₀ coding-agent LoRA, trained on past Claude sessions + external grounding, looped into the knowledge base and a central CSF store."

## Status: live + staged; one GPU step remains

### Done & verified
- **Ollama live** on `127.0.0.1:11434` (`ollama serve`). Models: `qwen2.5-coder`, `lantern-sigma0-coder`, `lantern-csf-dream`, `mistral`.
- **`lantern-sigma0-coder`** registered — repo-grounded Σ₀ system prompt over `qwen2.5-coder` (Stage 1: prompt-grounded, NOT yet a LoRA). Modelfile: `models/lantern-sigma0-coder/Modelfile`.
- **Wired**: `OLLAMA_MODEL=lantern-sigma0-coder` in `.env.local` (gitignored). autowork `callOllama` verified returning real coding output against live Ollama.
- **Training data**: `scripts/extract-session-pairs.py` → 365 high-quality pairs from 51 Claude sessions → `data/training/haiku-ft-pairs.jsonl`. Converted to alpaca via `scripts/convert-pairs-to-alpaca.py` → `models/lantern-sigma0-coder/training-data.jsonl`.
  - Both are **gitignored** (session-derived; privacy/split-data-model). Never commit weights or training data.

### Remaining: QLoRA fine-tune (needs GPU stack)
Blocker found: GPU is fine (RTX 3070, 8 GB) but **torch is CPU-only** (`2.10.0+cpu`) and `unsloth` not installed.

In progress: isolated venv `.venv-train` created (gitignored), pip upgraded. Next:
```
.venv-train\Scripts\python -m pip install torch --index-url https://download.pytorch.org/whl/cu121
.venv-train\Scripts\python -m pip install unsloth
.venv-train\Scripts\python scripts/fine-tune-ollama-model.py --model lantern-sigma0-coder --data models/lantern-sigma0-coder/training-data.jsonl --epochs 3
```
- `fine-tune-ollama-model.py` maps `lantern-sigma0-coder` → base `unsloth/Qwen2.5-Coder-7B` (added this pass). Loads 4-bit, LoRA r=16, SFTTrainer, saves adapter, merges 16-bit, and runs `ollama create lantern-sigma0-coder-v2`.
- 8 GB VRAM is tight for 7B QLoRA — keep `max_seq_length=2048`, `batch_size=1` if OOM. unsloth on native Windows is finicky; **WSL2 + CUDA is the reliable fallback**.

### After training succeeds
1. Confirm `ollama list` shows `lantern-sigma0-coder-v2`.
2. Update `models/lantern-sigma0-coder/Modelfile` Stage 2: `FROM` the merged GGUF; `ollama create lantern-sigma0-coder` again (or point `OLLAMA_MODEL` at `-v2`).
3. Run a real autowork issue end-to-end and confirm `source: ollama`.
4. **Push only code/config to master** (Modelfile, scripts, wiring). The GGUF/adapter + training JSONL stay local (large + session-derived).

## What lives where
- Code (committed): `scripts/extract-session-pairs.py`, `scripts/convert-pairs-to-alpaca.py`, `scripts/fine-tune-ollama-model.py`, `models/lantern-sigma0-coder/Modelfile`.
- Local-only (gitignored): `.venv-train/`, `data/training/`, `models/*/training-data.jsonl`, `models/*/adapters/`, the GGUF.
- Anti-fraud autowork fixes (separate work, PR #683 / branch `auto/issue-650`): apply-gate, scoped staging, SEARCH/REPLACE applier, git-apply, honest `[unverified]` tagging.

## Related issues
- #690 (this epic), #628 (local Ollama coding agent), #629 (Ollama agent failure diagnosis).
