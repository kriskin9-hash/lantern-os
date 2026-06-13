# CSF Image Generation Training

Train local image generation models on Lantern OS dream data using **LoRA fine-tuning** of Stable Diffusion XL.

## Overview

This pipeline:
- **Extracts** dream scenes and descriptions from CSF ingest files
- **Prepares** training data with artistic prompts and negative prompts
- **Fine-tunes** Stable Diffusion XL with LoRA (Low-Rank Adaptation)
- **Deploys** to Ollama as `lantern-csf-dream-image` model
- **Generates** dreamlike, symbolic images on-device (no cloud)

## Quick Start

### 1. Install Dependencies

```bash
pip install diffusers accelerate peft safetensors
pip install torch torchvision  # or torch with CUDA/ROCm for GPU
```

**GPU Support:**
- NVIDIA: `pip install torch --index-url https://download.pytorch.org/whl/cu118`
- AMD: Use ROCm 5.5+
- Apple Silicon: MPS automatic
- CPU: Works but slower

### 2. Prepare Training Data

```bash
python scripts/train-csf-image-models.py
```

This creates:
- `models/csf-image/training-config.json` — training samples from CSF ingest
- `models/csf-image/lora-training-config.json` — LoRA hyperparameters
- `models/csf-image/Modelfile.image` — Ollama model definition

### 3. Start Ollama Service

```bash
ollama serve
# In another terminal:
ollama pull stabilityai/stable-diffusion-xl-base-1.0
```

### 4. Run LoRA Fine-tuning

```bash
python scripts/train-lora-diffusion.py
```

This:
- Loads base Stable Diffusion XL model (~7GB first run)
- Fine-tunes with LoRA on dream scenes (3 epochs, ~30 min on NVIDIA A100)
- Saves checkpoints to `models/csf-image/checkpoints/`

### 5. Export & Deploy

```bash
# Merge LoRA weights with base model
python scripts/export-lora-model.py

# Create Ollama model
ollama create lantern-csf-dream-image -f models/csf-image/Modelfile.image

# Test
ollama run lantern-csf-dream-image "a dreamlike elephant oasis with moonlight reflecting in water"
```

## Training Data Sources

Dream scenes extracted from:
- `data/csf-ingest/CSF-INGEST-LORE-DREAMS-DOORS-2026-06-07.md` — Core dream lore
- `csf/ingest/three-doors/2026-06-08-elephant-oasis-local-model-session.md` — Three Doors game state

Each scene generates:
- **Text prompt** — Enhanced description with artistic modifiers
- **Image prompt** — Focused visual generation instruction
- **Negative prompt** — What to avoid (blurry, distorted, etc.)
- **Hyperparameters** — Guidance scale (7.5), steps (20), seed

## Model Architecture

**Base:** `stabilityai/stable-diffusion-xl-base-1.0`
- 7B parameters
- 1024×1024 image generation
- Supports LoRA fine-tuning

**LoRA Config:**
```json
{
  "r": 16,
  "lora_alpha": 32,
  "target_modules": ["to_q", "to_v"],
  "lora_dropout": 0.05
}
```

- **r=16** — Rank 16 factorization (~0.5% additional parameters)
- **target_modules** — Fine-tune attention layers only
- **lora_alpha=32** — Scaling factor for LoRA contribution

## Training Hyperparameters

| Parameter | Value | Reason |
|-----------|-------|--------|
| Epochs | 3 | Avoid overfitting on small dataset |
| Batch size | 4 | Fit in 8GB VRAM |
| Learning rate | 1e-4 | Stable fine-tuning |
| Warmup steps | 100 | Smooth training start |
| Guidance scale | 7.5 | Balance creativity & adherence |
| Inference steps | 20 | Speed vs. quality trade-off |

## Integration with Dream Journal

Once deployed, the UI will:

1. **Image Generation Button** — Generate image from dream description
   ```
   User: "I dreamed of an elephant door with moonlight"
   → Generate image with lantern-csf-dream-image
   → Display in dream entry
   ```

2. **Three Doors Game** — Generate door imagery dynamically
   ```
   Game state: "The Reflecting Water Door"
   → Generate scene image (local, no cloud)
   → Render in game UI
   ```

3. **Dream Archive** — Illustrate past dreams
   ```
   Archive: Browse 100+ dreams
   → Re-generate images on demand
   → Build visual memory palace
   ```

## Performance Notes

**Hardware Requirements:**
- **GPU (Recommended):** 8GB+ VRAM, 5-10 min/epoch
- **CPU:** 16GB+ RAM, 30-60 min/epoch
- **Ollama:** Runs inference on any hardware

**Model Size:**
- Base model: 7GB
- LoRA weights: ~50MB
- Ollama quantized: ~3-4GB

## Extending Training

### Add New Dream Data

1. Create CSF ingest file in `data/csf-ingest/`
2. Format: Dream descriptions with clear "DOOR" or "SCENE" markers
3. Run training pipeline again — automatically included

### Custom Prompt Engineering

Edit `train-csf-image-models.py`:

```python
def _enhance_prompt(self, text):
    """Customize artistic style"""
    modifiers = [
        'your style here',
        'your aesthetic',
    ]
    return f"{text}, {', '.join(modifiers)}"
```

### Multi-GPU Training

```bash
accelerate config  # Select multi-GPU
accelerate launch scripts/train-lora-diffusion.py
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| CUDA out of memory | Reduce batch size (4→2), use gradient checkpointing |
| Slow generation | Use CPU inference for dev, GPU for prod |
| Poor image quality | Increase inference steps (20→30), guidance (7.5→10) |
| Model not found | Run `ollama pull stabilityai/stable-diffusion-xl-base-1.0` |

## References

- [Diffusers Documentation](https://huggingface.co/docs/diffusers)
- [PEFT LoRA Guide](https://huggingface.co/docs/peft)
- [Stable Diffusion XL](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0)
- [Ollama](https://ollama.ai)

## Status

- ✅ Training pipeline scripted
- ✅ CSF data extraction configured
- ✅ LoRA fine-tuning ready
- ⏳ GPU training (pending hardware/time)
- ⏳ Ollama integration (pending fine-tuning)
- ⏳ Dream Journal UI integration

## Next Steps

1. **Execute training** on GPU (3-5 hours)
2. **Export LoRA weights** to `.safetensors`
3. **Merge with base model** for Ollama
4. **Deploy** as `lantern-csf-dream-image`
5. **Integrate** image generation into Dream Journal UI
6. **Test** with Three Doors game state rendering

---

**Training Date:** 2026-06-08  
**Model Version:** lantern-csf-dream-image v1.0
