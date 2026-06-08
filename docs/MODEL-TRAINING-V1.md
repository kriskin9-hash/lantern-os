# Model Training v1 — Convergance OS

Fine-tune the three Convergance OS profiles using LoRA adapters on sanitized instruction datasets.

## Overview

**Goal:** Train in-house models that understand Lantern OS behavior (style, memory safety, receipt emission, Three Doors, etc.) without memorizing private data.

**Approach:**
- v0: Router + Modelfiles + prompt contracts (current)
- v1: LoRA adapters on qwen2.5-coder base
- v2: Merged weights into local Ollama
- v3: Full model family deployment

**Profiles:**
1. **lantern-csf-dream** — DreamChat, warmth, Three Doors (3B model)
2. **lantern-pcsf** — PCSF receipts, capacity state (1.5B model)
3. **lantern-convergance** — Convergence receipts, actions (3B model)

---

## Step 1: Prepare Training Environment

### Install dependencies

```bash
pip install -r training-requirements.txt
```

### Generate dataset

```bash
python scripts/generate-training-dataset.py
```

This creates `training_data/lantern-v1-dataset.jsonl` with 500–2,000 sanitized examples:
- Dream journal entries (anonymized)
- RAG seed ingest examples
- Three Doors patterns
- PCSF receipt examples
- Convergence loop examples

**Output:** `training_data/lantern-v1-dataset.jsonl`

---

## Step 2: Train LoRA Adapters

Train each profile separately. Each takes ~30-60 minutes on a GPU.

### lantern-csf-dream

```bash
python scripts/train-lora.py --profile lantern-csf-dream --epochs 3 --batch-size 4
```

- **Base:** Qwen 3B Instruct
- **LoRA rank:** 16
- **Training time:** ~45 min (V100/A100)
- **Output:** `models/lantern-csf-dream-lora/`

### lantern-pcsf

```bash
python scripts/train-lora.py --profile lantern-pcsf --epochs 3 --batch-size 8
```

- **Base:** Qwen 1.5B Instruct (smaller for receipt generation)
- **LoRA rank:** 8
- **Training time:** ~30 min
- **Output:** `models/lantern-pcsf-lora/`

### lantern-convergance

```bash
python scripts/train-lora.py --profile lantern-convergance --epochs 3 --batch-size 4
```

- **Base:** Qwen 3B Instruct
- **LoRA rank:** 16
- **Training time:** ~45 min
- **Output:** `models/lantern-convergance-lora/`

---

## Step 3: Merge Adapters

Merge LoRA weights into base model and create Ollama Modelfiles.

```bash
python scripts/merge-lora-ollama.py --profile lantern-csf-dream
python scripts/merge-lora-ollama.py --profile lantern-pcsf
python scripts/merge-lora-ollama.py --profile lantern-convergance
```

**Output:** `models/lantern-*-merged/` with Modelfile ready for Ollama.

---

## Step 4: Create Local Ollama Models

Register the merged models with Ollama:

```bash
ollama create lantern-csf-dream -f models/lantern-csf-dream-merged/Modelfile
ollama create lantern-pcsf -f models/lantern-pcsf-merged/Modelfile
ollama create lantern-convergance -f models/lantern-convergance-merged/Modelfile
```

Verify they're available:

```bash
ollama list
```

---

## Step 5: Test in Lantern OS

### Start the server

```bash
npm run dev --prefix apps/lantern-garage
```

### Test Dream Chat routing

The Convergance OS router should now:
1. Detect intent (dream_chat, capacity_query, etc.)
2. Select profile (lantern-csf-dream, lantern-pcsf, etc.)
3. Route to local Ollama model first
4. Verify model responds with correct behavior

### Verify outputs

Check logs for:
- `[Convergance] intent=dream_chat profile=lantern-csf-dream provider=ollama`
- `[Stream] Ollama local-first OK`
- Receipt written to `data/pcsf/convergance-receipts.jsonl`

---

## Training Dataset Format

Each line in `lantern-v1-dataset.jsonl`:

```json
{
  "instruction": "User asks to resume Raven Door.",
  "input": "lets go back to the bathhouse",
  "output": "We resume at the Raven villa Bathhouse Mosaic Door...",
  "type": "dream_chat",
  "source": "dream_journal"
}
```

**Types:**
- `dream_chat` — DreamChat responses with doors
- `three_doors` — Door branching patterns
- `pcsf_receipt` — PCSF capacity receipts (JSON)
- `convergance_action` — Convergence loop receipts
- `rag_ingest` — Data ingestion patterns

**Key properties:**
- **No PII:** All names, emails, paths anonymized
- **Sanitized:** Personal context removed
- **Opt-in only:** Real examples from consenting testers
- **Finite size:** 500–2,000 examples per training run

---

## Monitoring Training

### With Weights & Biases (optional)

```bash
# Login first
wandb login

# Training logs will upload to W&B dashboard
python scripts/train-lora.py --profile lantern-csf-dream --epochs 3
```

### Local monitoring

```bash
# Watch loss metrics in TensorBoard
tensorboard --logdir models/lantern-csf-dream-lora/runs/
```

---

## Troubleshooting

### Out of memory

Reduce batch size:

```bash
python scripts/train-lora.py --profile lantern-csf-dream --batch-size 2
```

### Model not found

Ensure base model is downloaded:

```bash
# Pre-download base model
from transformers import AutoModel
AutoModel.from_pretrained("Qwen/Qwen2.5-Coder-3B-Instruct")
```

### LoRA adapter not found

Verify training completed and adapter saved:

```bash
ls models/lantern-csf-dream-lora/
# Should show: adapter_config.json, adapter_model.bin, etc.
```

---

## Next Steps (v2+)

1. **Evaluate trained models** — Compare quality vs Ollama base
2. **Integrate PEFT quantization** — Further compress adapters
3. **Fine-tune hyperparameters** — Optimize for specific profiles
4. **Merge full weights** — v3 deployment as standalone models
5. **A/B test** — Compare v0 (base + prompt) vs v1 (trained) in production

---

## References

- **LoRA paper:** Hu et al., "LoRA: Low-Rank Adaptation of Large Language Models"
- **QLoRA:** Dettmers et al., "QLoRA: Efficient Finetuning of Quantized LLMs"
- **Qwen models:** https://github.com/QwenLM/Qwen2
- **PEFT:** https://github.com/huggingface/peft
- **TRL:** https://github.com/huggingface/trl
